import asyncio
import logging
from typing import Callable, Any, List, Optional, Set, Coroutine

# 全局日志（可替换为项目自有logger）
logger = logging.getLogger("ConcurrentAsyncEventManager")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class ConcurrentAsyncEventManager:
    """
    全局异步并发事件管理类（单例）
    核心特性：
    1. 回调函数异步并发执行（基于asyncio.Task）
    2. 管理所有未完成的Task，支持取消/等待
    3. 完善的异常隔离与兜底
    4. 异步安全（锁保护）
    """
    # 单例实例
    _instance: Optional["ConcurrentAsyncEventManager"] = None
    # 单例创建锁（异步环境下保证唯一）
    _instance_lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        """同步单例创建（基础保证）"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 事件存储：{事件名: [回调函数列表]}
            cls._instance._events: dict[str, List[Callable]] = {}
            # 异步锁：保护_events的增删改查
            cls._instance._lock = asyncio.Lock()
            # 未完成的Task集合（用于管理/取消）
            cls._instance._pending_tasks: Set[asyncio.Task] = set()
        return cls._instance

    # -------------------------- 核心：事件注册/取消 --------------------------
    async def register_event(self, event_name: str, callback: Callable) -> None:
        """
        注册事件回调（支持同步/异步函数）
        :param event_name: 事件名（如"qq_message_received"）
        :param callback: 回调函数（async def/def 均可）
        """
        if not isinstance(event_name, str) or event_name.strip() == "":
            raise ValueError("事件名必须为非空字符串")
        if not callable(callback):
            raise ValueError("回调函数必须是可调用对象")

        async with self._lock:
            if event_name not in self._events:
                self._events[event_name] = []
            # 避免重复注册
            if callback not in self._events[event_name]:
                self._events[event_name].append(callback)
                logger.info(f"✅ 事件[{event_name}]注册回调成功：{callback.__name__}")
            else:
                logger.warning(f"⚠️ 事件[{event_name}]的回调[{callback.__name__}]已存在，无需重复注册")

    async def unregister_event(self, event_name: str, callback: Callable) -> bool:
        """
        取消指定事件的回调函数
        :return: 是否取消成功
        """
        async with self._lock:
            if event_name not in self._events:
                logger.warning(f"⚠️ 事件[{event_name}]不存在，无法取消回调")
                return False
            if callback not in self._events[event_name]:
                logger.warning(f"⚠️ 事件[{event_name}]未注册回调[{callback.__name__}]")
                return False

            self._events[event_name].remove(callback)
            # 无回调时删除事件（节省内存）
            if len(self._events[event_name]) == 0:
                del self._events[event_name]
            logger.info(f"❌ 事件[{event_name}]取消回调成功：{callback.__name__}")
            return True

    # -------------------------- 核心：并发触发事件 --------------------------
    async def trigger_event(
            self,
            event_name: str,
            *args,
            wait_all: bool = False,  # 是否等待所有回调完成
            return_exceptions: bool = True  # 是否捕获回调异常（不中断其他任务）
    ) -> List[Any]:
        """
        异步并发触发事件（核心）
        :param event_name: 事件名
        :param args/kwargs: 传递给回调的参数
        :param wait_all: 是否等待所有回调执行完成（默认False：非阻塞）
        :param return_exceptions: 是否捕获异常（True：异常返回，不中断）
        :return: 回调执行结果列表（wait_all=True时有效）
        """
        # 1. 加锁读取回调列表（避免并发修改）
        async with self._lock:
            callbacks = self._events.get(event_name, []).copy()

        if not callbacks:
            logger.debug(f"📌 事件[{event_name}]无注册回调，跳过触发")
            return []

        # 2. 封装所有回调为Task（并发执行）
        tasks: List[asyncio.Task] = []
        for callback in callbacks:
            try:
                # 区分同步/异步回调，统一封装为Coroutine
                if asyncio.iscoroutinefunction(callback):
                    # 异步回调：直接调用
                    coro: Coroutine = callback(*args)
                else:
                    # 同步回调：封装为异步函数（避免阻塞事件循环）
                    async def sync_callback_wrapper(cb=callback):
                        return cb(*args)

                    coro = sync_callback_wrapper()

                # 创建Task并添加异常兜底
                task = asyncio.create_task(coro)
                # 记录未完成的Task（便于管理）
                self._pending_tasks.add(task)
                # Task完成后自动从集合移除
                task.add_done_callback(lambda t: self._pending_tasks.discard(t))
                # 自定义异常处理（避免未捕获异常警告）
                task.add_done_callback(self._handle_task_exception)

                tasks.append(task)
                logger.debug(f"🚀 事件[{event_name}]的回调[{callback.__name__}]已创建Task")

            except Exception as e:
                logger.error(
                    f"❌ 事件[{event_name}]创建回调[{callback.__name__}]的Task失败：{str(e)}",
                    exc_info=True
                )

        # 3. 控制是否等待所有Task完成
        results = []
        if wait_all:
            # 等待所有Task完成，捕获异常（不中断）
            results = await asyncio.gather(*tasks, return_exceptions=return_exceptions)
            logger.info(f"✅ 事件[{event_name}]的{len(tasks)}个回调已全部执行完成")
        else:
            # 非阻塞模式：直接返回，Task后台执行
            logger.info(f"🚀 事件[{event_name}]的{len(tasks)}个回调已并发启动（非阻塞）")

        return results

    # -------------------------- Task管理工具 --------------------------
    def _handle_task_exception(self, task: asyncio.Task) -> None:
        """Task异常兜底（捕获未处理的异常）"""
        try:
            # 获取Task结果，触发潜在异常
            task.result()
        except asyncio.CancelledError:
            logger.debug(f"🔄 Task已被取消：{task}")
        except Exception as e:
            logger.error(
                f"❌ Task执行失败：{str(e)}",
                exc_info=True
            )

    async def cancel_all_pending_tasks(self) -> int:
        """
        取消所有未完成的Task
        :return: 取消的Task数量
        """
        if not self._pending_tasks:
            logger.info("📌 暂无未完成的Task")
            return 0

        cancel_count = 0
        # 遍历并取消所有未完成的Task
        for task in list(self._pending_tasks):  # 转列表避免迭代时修改集合
            if not task.done():
                task.cancel()
                cancel_count += 1
                logger.debug(f"🔄 已取消Task：{task}")

        logger.info(f"✅ 共取消{cancel_count}个未完成的Task")
        return cancel_count

    async def wait_all_pending_tasks(self) -> List[Any]:
        """等待所有未完成的Task执行完成"""
        if not self._pending_tasks:
            logger.info("📌 暂无未完成的Task")
            return []

        tasks = list(self._pending_tasks)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"✅ 所有{len(tasks)}个未完成的Task已执行完成")
        return results

    # -------------------------- 辅助方法 --------------------------
    async def clear_event(self, event_name: Optional[str] = None) -> None:
        """清空事件（可选清空指定事件/所有事件）"""
        async with self._lock:
            if event_name is None:
                self._events.clear()
                logger.info("🗑️ 所有事件已清空")
            else:
                if event_name in self._events:
                    del self._events[event_name]
                    logger.info(f"🗑️ 事件[{event_name}]已清空")
                else:
                    logger.warning(f"⚠️ 事件[{event_name}]不存在，无需清空")

    def get_event_callbacks(self, event_name: str) -> List[Callable]:
        """获取指定事件的所有回调（只读）"""
        return self._events.get(event_name, []).copy()

    def get_pending_task_count(self) -> int:
        """获取未完成的Task数量"""
        return len(self._pending_tasks)


# 全局唯一实例（所有模块直接导入使用）
global_event_manager = ConcurrentAsyncEventManager()
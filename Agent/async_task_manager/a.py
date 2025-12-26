import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Callable, Any
from asyncio import Task, Event, Lock

# 配置日志
logger = logging.getLogger(__name__)

# ------------------------------
# 抽象异步任务类（所有异步任务的基类）
# ------------------------------
class BaseAsyncTask(ABC):
    """
    异步任务抽象基类
    所有需要被AsyncTaskManager管理的异步任务，都必须继承此类并实现run方法
    """
    @property
    def task_name(self) -> str:
        """任务名称（默认使用类名，子类可重写）"""
        return self.__class__.__name__

    @abstractmethod
    async def run(self, abort_flag: Event):
        """
        任务核心执行逻辑
        :param abort_flag: 中止信号标志，任务内部可监听该标志提前退出
        """
        pass

# ------------------------------
# 异步任务管理器核心类
# ------------------------------
class AsyncTaskManager:
    """
    异步任务管理器
    负责统一管理所有异步任务的创建、状态跟踪、批量终止与资源回收
    """
    def __init__(self):
        # 存储任务：key=任务名称，value=asyncio.Task对象
        self.tasks: Dict[str, Task] = {}
        # 全局中止标志：用于通知所有任务停止执行
        self.abort_flag: Event = asyncio.Event()
        # 异步锁：保证对tasks字典的并发操作安全
        self._lock: Lock = asyncio.Lock()

    # ------------------------------
    # 核心方法：添加任务
    # ------------------------------
    async def add_task(
        self,
        task: BaseAsyncTask,
        finish_callback: Optional[Callable[[Task], None]] = None
    ) -> None:
        """
        添加异步任务到管理器
        :param task: 继承自BaseAsyncTask的任务实例
        :param finish_callback: 任务完成后的自定义回调函数
        """
        task_name = task.task_name
        async with self._lock:  # 加锁保证线程安全
            # 1. 若同名任务已存在，先取消旧任务
            if task_name in self.tasks:
                old_task = self.tasks[task_name]
                if not old_task.done():
                    logger.warning(f"同名任务[{task_name}]已存在，正在取消旧任务...")
                    old_task.cancel()
                    # 等待旧任务结束（超时5秒）
                    try:
                        await asyncio.wait_for(old_task, timeout=5.0)
                    except (asyncio.CancelledError, asyncio.TimeoutError):
                        logger.warning(f"旧任务[{task_name}]取消超时或已被取消")
                # 从任务列表中移除旧任务
                del self.tasks[task_name]

            # 2. 创建新任务并绑定回调
            new_task = asyncio.create_task(
                self._wrap_task_run(task)  # 包装任务执行逻辑
            )

            # 3. 绑定任务完成后的回调（先清理任务，再处理结果）
            new_task.add_done_callback(self._remove_task_call_back)
            if finish_callback:
                new_task.add_done_callback(finish_callback)
            else:
                new_task.add_done_callback(self._default_finish_call_back)

            # 4. 将新任务加入管理列表
            self.tasks[task_name] = new_task
            logger.info(f"任务[{task_name}]已成功添加到异步任务管理器")

    # ------------------------------
    # 辅助方法：包装任务执行
    # ------------------------------
    async def _wrap_task_run(self, task: BaseAsyncTask) -> None:
        """
        包装任务的run方法，统一处理异常
        :param task: 异步任务实例
        """
        try:
            await task.run(self.abort_flag)  # 执行任务核心逻辑
        except asyncio.CancelledError:
            logger.info(f"任务[{task.task_name}]被主动取消")
        except Exception as e:
            logger.error(f"任务[{task.task_name}]执行异常: {str(e)}", exc_info=True)

    # ------------------------------
    # 回调方法：任务完成后自动移除
    # ------------------------------
    def _remove_task_call_back(self, task: Task) -> None:
        """
        任务完成（成功/失败/取消）后，自动从任务列表中移除
        :param task: 已完成的任务对象
        """
        # 遍历任务列表，找到对应任务并删除（无需加锁，仅读取+删除）
        for task_name, task_obj in list(self.tasks.items()):
            if task_obj is task:
                del self.tasks[task_name]
                logger.debug(f"任务[{task_name}]已从管理器中移除")
                break

    # ------------------------------
    # 回调方法：默认任务结果处理
    # ------------------------------
    def _default_finish_call_back(self, task: Task) -> None:
        """
        默认的任务完成回调：处理任务结果与异常
        :param task: 已完成的任务对象
        """
        task_name = None
        # 先获取任务名称
        for name, obj in self.tasks.items():
            if obj is task:
                task_name = name
                break

        try:
            # 获取任务返回结果（若有异常会在此处抛出）
            task.result()
            logger.info(f"任务[{task_name or '未知任务'}]正常执行完成")
        except asyncio.CancelledError:
            logger.info(f"任务[{task_name or '未知任务'}]已被取消")
        except Exception as e:
            logger.error(f"任务[{task_name or '未知任务'}]执行失败: {str(e)}", exc_info=True)

    # ------------------------------
    # 核心方法：获取所有任务状态
    # ------------------------------
    async def get_tasks_status(self) -> Dict[str, str]:
        """
        获取所有任务的当前状态
        :return: 字典，key=任务名称，value=任务状态（running/done）
        """
        async with self._lock:
            status_dict = {}
            for task_name, task in self.tasks.items():
                status_dict[task_name] = "running" if not task.done() else "done"
            return status_dict

    # ------------------------------
    # 调试方法：打印详细任务状态
    # ------------------------------
    async def debug_task_status(self) -> None:
        """
        调试用：打印所有任务的详细状态（含事件循环中所有任务）
        """
        # 1. 打印管理器管理的任务
        async with self._lock:
            logger.info(f"===== 异步任务管理器当前状态 =====")
            logger.info(f"管理的任务总数: {len(self.tasks)}")
            for task_name, task in self.tasks.items():
                status = "running" if not task.done() else "done"
                cancelled = task.cancelled()
                exception = task.exception() if task.done() else None
                logger.info(f"任务[{task_name}]: 状态={status}, 已取消={cancelled}, 异常={exception}")
            logger.info(f"==================================")

        # 2. 打印事件循环中所有任务（含未被管理器管理的）
        all_tasks = asyncio.all_tasks()
        logger.info(f"当前事件循环总任务数: {len(all_tasks)}")
        for idx, task in enumerate(all_tasks):
            logger.debug(f"全局任务[{idx}]: 状态={'running' if not task.done() else 'done'}, 已取消={task.cancelled()}")

    # ------------------------------
    # 核心方法：停止并等待所有任务
    # ------------------------------
    async def stop_and_wait_all_tasks(self, timeout: float = 10.0) -> None:
        """
        停止所有异步任务并等待其结束
        :param timeout: 等待所有任务结束的超时时间
        """
        # 1. 设置全局中止标志，通知所有任务退出
        self.abort_flag.set()
        logger.info("已发送全局中止信号，正在停止所有异步任务...")

        # 2. 批量取消未完成的任务
        async with self._lock:
            pending_tasks = [task for task in self.tasks.values() if not task.done()]
            if not pending_tasks:
                logger.info("没有待停止的任务")
                return

            # 3. 取消所有待执行任务
            for task in pending_tasks:
                if not task.cancelled():
                    task.cancel()

            # 4. 等待所有任务结束
            try:
                await asyncio.wait_for(asyncio.gather(*pending_tasks, return_exceptions=True), timeout=timeout)
                logger.info("所有任务已成功停止")
            except asyncio.TimeoutError:
                logger.warning(f"等待任务停止超时（{timeout}秒），部分任务可能未正常结束")

        # 5. 清理状态
        await self._clear()

    # ------------------------------
    # 辅助方法：清理管理器状态
    # ------------------------------
    async def _clear(self) -> None:
        """清空任务列表并重置中止标志"""
        async with self._lock:
            self.tasks.clear()
        self.abort_flag.clear()
        logger.info("异步任务管理器已完成状态清理")

# ------------------------------
# 全局单例（项目中通常使用单例模式）
# ------------------------------
_async_task_manager: Optional[AsyncTaskManager] = None

def get_async_task_manager() -> AsyncTaskManager:
    """
    获取异步任务管理器单例
    :return: AsyncTaskManager实例
    """
    global _async_task_manager
    if _async_task_manager is None:
        _async_task_manager = AsyncTaskManager()
    return _async_task_manager


if __name__ == "__main__":
    async_task_manager = get_async_task_manager()

    async_task_manager.add_task()


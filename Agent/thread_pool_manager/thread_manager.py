import time
from concurrent.futures import ThreadPoolExecutor
import concurrent
import atexit

from utils import logger


class ThreadPoolManager:
    def __init__(
            self,
            front_max_workers: int = 4,
            back_max_workers: int = 6,
    ):
        """初始化线程池"""
        self.front_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=front_max_workers,
            thread_name_prefix='FrontThread-'
        )
        logger.info(f"前台线程初始化成功，最大线程数为：{front_max_workers}")

        self.back_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=back_max_workers,
            thread_name_prefix="BackThread-",
        )
        logger.info(f"后台线程初始化成功，最大线程数为：{back_max_workers}")

        self.future_map = {}
        # 保存future对象
        self.front_future = []
        # 保存前台线程池的future对象
        self.back_future = []
        # 保存后台线程池的future对象

        atexit.register(self.shutdown_all)
        #注册退出函数，关闭线程池释放资源

    def submit_front_executor(self, task_name: str, func, *args, **kwargs):
        """
        提交到前台线程池执行函数
        :param func: 任务函数
        :param args: 任务函数的参数名
        :param kwargs: 任务参数的键值对
        :return: 返回future对象
        """
        #定义线程名称
        if task_name is None:
            task_name = f"{func.__name__}:{int(time.time())}"
        else:
            task_name = f"{task_name}:{int(time.time())}"
        try:
            future = self.front_executor.submit(func, *args, **kwargs)
            future.add_done_callback(self.callback)
            #map保存future对象
            self.future_map[future] = task_name
            #front_future保存前台线程池的future对象
            self.front_future.append(future)
        except Exception as e:
            logger.error("任务提交失败", e)

    def submit_back_executor(self, task_name: str, func, *args, **kwargs):
        """
        提交到后台线程池执行函数
        :param func: 任务函数
        :param args: 任务函数的参数名
        :param kwargs: 任务参数的键值对
        :return: 返回future对象
        """
        if task_name is None:
            task_name = f"{func.__name__}:{int(time.time())}"
        else:
            task_name = f"{task_name}:{int(time.time())}"

        try:
            future = self.back_executor.submit(func, *args, **kwargs)
            future.add_done_callback(self.callback)
            #map保存future对象
            self.future_map[future] = task_name
            #front_future保存后台线程池的future对象
            self.back_future.append(future)
        except Exception as e:
            logger.error("任务提交失败", e)

    def get_front_executor_count(self) -> int:
        """
        获取前台线程池待执行任务数量
        :return: 任务数量
        """
        if hasattr(self.front_executor, '_work_queue'):
            return self.front_executor._work_queue.qsize()
        return 0

    def get_back_executor_count(self) -> int:
        """
        获取后台线程池待执行任务数量
        :return: 任务数量
        """
        if hasattr(self.back_executor, '_work_queue'):
            return self.back_executor._work_queue.qsize()
        return 0

    def callback(self, future):
        task_name = self.future_map[future]
        try:
            future.result()
            logger.info(f"{task_name}任务完成")
        except Exception as e:
            logger.error("任务出错", e)
        finally:
            if future in self.front_future:
                self.front_future.remove(future)
            if future in self.back_future:
                self.back_future.remove(future)
            self.future_map.pop(future)
            logger.info(f"任务{task_name}完成，剩余任务数量：{len(self.future_map)}")

    def get_back_task_detail(self) -> list:
        """
        获取后台所有任务的详细信息（名称/状态/线程名）
        :return 返回后台任务的详细信息列表
        """
        task_details = []
        for future in self.back_future:
            task_name = self.future_map.get(future, "未知")
            task_status = self.get_task_status(future)
            thread_name = None
            if future.running():
                thread_name = "运行中（需任务内部记录）"
            task_details.append({
                "task_name": task_name,
                "task_status": task_status,
                "thread_name": thread_name,
                "future": future
            })
        return task_details

    def get_front_task_detail(self) -> list:
        """
        获取前台所有任务的详细信息（名称/状态/线程名）
        :return 返回后台任务的详细信息列表
        """
        task_details = []
        for future in self.front_future:
            task_name = self.future_map.get(future, "未知")
            task_status = self.get_task_status(future)
            thread_name = None
            if future.running():
                thread_name = "运行中（需任务内部记录）"
            task_details.append({
                "task_name": task_name,
                "task_status": task_status,
                "thread_name": thread_name,
                "future": future
            })
        return task_details

    def get_task_status(self, future):
        if future.running():
            return "运行中"
        elif future.cancelled():
            return "已取消"
        elif future.done():
            if future.exception() is not None:
                return "出错"
            else:
                return "完成"

    def shutdown_all(self):
        """关闭所有线程池"""
        if hasattr(self, 'front_executor'):
            self.front_executor.shutdown()
            logger.info("前台线程池关闭成功")
        if hasattr(self, 'back_executor'):
            self.back_executor.shutdown()
            logger.info("后台线程池关闭成功")


thread_pool_manager = ThreadPoolManager()

if __name__ == '__main__':
    t = ThreadPoolManager()




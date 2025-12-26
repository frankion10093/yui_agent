import asyncio
from asyncio import Task, Lock, Event
from dataclasses import dataclass
import asyncio
from typing import Dict, Optional, Set


class AsyncTaskManager:

    _insance: Optional['AsyncTaskManager'] = None

    def __new__(cls):
        if cls._insance is None:
            cls._insance = AsyncTaskManager()
            cls._insance.lock = Lock()
            cls._insance.pending_tasks = Set[asyncio.Task] = set()

        return cls._insance


    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        print(self.tasks)

    async def add_task(self,task_name: str, event: Event):
        # 异步锁保证并发修改tasks字典的安全
        async with self._lock:

            print(f"任务[{task_name}]已添加到管理器")


async def aaa():
    print("任务aaa开始执行，休眠2秒...")
    await asyncio.sleep(2)
    print("任务aaa执行完成")

async def main(event: Event):
    event.set()

    print("wadadawd")
async def da():
    await asyncio.sleep(2)
    print("awwad")


if __name__ == '__main__':
    a = Event(da())
    asyncio.run(main())
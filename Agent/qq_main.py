import asyncio

from async_task_manager import get_async_task_manager
from qq import get_qq_manager
from llm import get_advent
from thread_pool_manager import thread_pool_manager
from utils import print_main_page_yui


async def main():
    async_task_manager = get_async_task_manager()

    advent = get_advent()

    qq_manager = get_qq_manager()

    print_main_page_yui()

    try:
        await async_task_manager.add_task(qq_manager)

        await async_task_manager.add_task(advent)

        await asyncio.Future()
    except Exception as e:
        print(e)


def qq_main():
    asyncio.run(main())

thread_pool_manager.submit_front_executor("qq",qq_main)

while True:
    pass
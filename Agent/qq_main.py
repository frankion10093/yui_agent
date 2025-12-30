import asyncio

from async_task_manager import get_async_task_manager
from qq import get_qq_manager
from llm import get_agent
from thread_pool_manager import thread_pool_manager
from utils import print_main_page_yui


async def main():
    try:
        async_task_manager = get_async_task_manager()

        agent = get_agent()

        qq_manager = get_qq_manager()

        await async_task_manager.add_task(qq_manager)

        await async_task_manager.add_task(agent)

        print_main_page_yui()

        await asyncio.Future()
    except Exception as e:
        print(e)


def qq_main():
    asyncio.run(main())

thread_pool_manager.submit_front_executor("qq",qq_main)

while True:
    pass
import asyncio

from async_task_manager import get_async_task_manager
from qq import get_qq_manager
from llm import get_async_agent
from thread_pool_manager import get_thread_pool_manager
from utils import print_main_page_yui



async_task_manager = get_async_task_manager()

agent = get_async_agent()

qq_manager = get_qq_manager()

thread_pool_manager = get_thread_pool_manager()

async def init_qq_server():
    try:
        await async_task_manager.add_task(qq_manager)

        await async_task_manager.add_task(agent)

        print_main_page_yui()

        await asyncio.Future()
    except Exception as e:
        print(e)


def start_qq_server():
    asyncio.run(init_qq_server())


thread_pool_manager.submit_front_executor("qq",start_qq_server)

while True:
    pass

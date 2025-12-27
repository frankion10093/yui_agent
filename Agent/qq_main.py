import asyncio

from async_task_manager import get_async_task_manager
from qq import get_qq_manager
from llm import get_advent
from thread_pool_manager import thread_pool_manager
from utils import logger


async def main():
    async_task_manager = get_async_task_manager()

    advent = get_advent()

    qq_manager = get_qq_manager()

    # 定义ANSI颜色代码
    COLORS = [
        "\033[91m",  # 亮红
        "\033[93m",  # 亮黄
        "\033[92m",  # 亮绿
        "\033[96m",  # 亮青
        "\033[94m",  # 亮蓝
        "\033[95m",  # 亮紫
        "\033[97m"  # 亮白
    ]
    RESET = "\033[0m"  # 重置颜色

    # 带颜色的文本输出
    print(f"{COLORS[0]}  ___    ___ ___  ___  ___  ________  ________  _______   ________   _________   {RESET}")
    print(
        f"{COLORS[1]} |\\  \\  /  /|\\  \\|\\  \\|\\  \\|\\   __  \\|\\   ____\\|\\  ___ \\ |\\   ___  \\|\\___   ___\\ {RESET}")
    print(
        f"{COLORS[2]} \\ \\  \\/  / | \\  \\\\\\  \\ \\  \\ \\  \\|\\  \\ \\  \\___|\\ \\   __/|\\ \\  \\\\ \\  \\|___ \\  \\_| {RESET}")
    print(
        f"{COLORS[3]}  \\ \\    / / \\ \\  \\\\\\  \\ \\  \\ \\   __  \\ \\  \\  __\\ \\  \\_|/_\\ \\  \\\\ \\  \\   \\ \\  \\  {RESET}")
    print(
        f"{COLORS[4]}   \\/  /  /   \\ \\  \\\\\\  \\ \\  \\ \\  \\ \\  \\ \\  \\|\\  \\ \\  \\_|\\ \\ \\  \\\\ \\  \\   \\ \\  \\ {RESET}")
    print(
        f"{COLORS[5]} __/  / /      \\ \\_______\\ \\__\\ \\__\\ \\__\\ \\_______\\ \\_______\\ \\__\\\\ \\__\\   \\ \\__\\{RESET}")
    print(
        f"{COLORS[6]}|\\___/ /        \\|_______|\\|__|\\|__|\\|__|\\|_______|\\|_______|\\|__| \\|__|    \\|__|{RESET}")
    print(f"{COLORS[0]}                                                                          {RESET}")
    print(f"{COLORS[1]}                                                                          {RESET}")

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
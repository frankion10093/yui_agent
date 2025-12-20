import time

from llm import Advent
import os
from utils import logger
import asyncio
#这个方法用于构建和启动聊天机器人，并提供聊天功能。
#需要根据传入值启动不同模式
async def agent_core(mode :str):
    #检查依赖项目是否存在
    if(not os.path.exists("./config/llm_config.yaml")):
        logger.error("构建失败，llm_config.yaml配置文件不存在！")
        return
    #初始化构架agent
    chatbot = Advent()
    while True:
        #获取用户输入
        time.sleep(1)
        print("test")

async def main():
    while True:
        print("test1")
        time.sleep(1)



if __name__ == '__main__':
    asyncio.run(agent_core("111"))
    asyncio.run(main())

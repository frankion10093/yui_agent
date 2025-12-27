from asyncio import Event
from typing import Optional

import yaml
import os

from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from utils import logger
from llm.tools import QQTools
from llm.build_llm import build_ollama

from async_task_manager import BaseAsyncTask
from message import get_message_manager


class Advent(BaseAsyncTask):

    @property
    def task_name(self) -> str:
        """任务名称（默认使用类名，子类可重写）"""
        return "Advent"

    def __init__(self):
        try:
            self.tools = QQTools
            self.llm = build_ollama()
            if self.llm is None:
                logger.log('llm创建失败')
                raise Exception('llm创建失败')
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config',
                                'llm_config.yaml')
            with open(path, 'r', encoding='utf-8') as f:
                #1 加载语言模型配置
                temp = yaml.safe_load(f)
                #2 初始化系统提示词
                system_prompt = temp['system_prompts']['猫娘']

                self.agent = create_agent(
                    model=self.llm,
                    tools=self.tools,
                    system_prompt=system_prompt,
                )

                logger.info("Agent机器人初始化成功")
        except FileNotFoundError:
            logger.error(f"Agent机器人初始化失败：未找到配置文llm_config.yaml")
        except Exception as e:
            logger.error(f"Agent机器人初始化失败：{e}")

        #3 初始化历史对话管理
        self.chat_history = []

    async def run(self, abort_flag: Event):
        _message_manager = get_message_manager()
        while True:
            try:
                msg = await _message_manager.message_queue.get()
                print("开始对话")
                await self.chat(msg)
                print("结束对话")
            except Exception as e:
                logger.error(e)

    async def chat(self, user_prompt: str):
        #构造消息流
        full_response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(user_prompt),
            ]
        })
        msg = full_response['messages'][-1].content
        print(msg)
        return msg



_advent: Optional['Advent'] = None  # 正确的类型注解 + 初始值

def get_advent():
    global _advent
    if _advent is None:
        _advent = Advent()
    return _advent

if __name__ == '__main__':
    ad = Advent()
    while True:
        input_str = input("请输入：")
        ad.chat(input_str)
        if input_str == 'exit':
            break

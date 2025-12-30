import asyncio
from asyncio import Event
from typing import Optional
import base64

import aiohttp
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langgraph.graph.state import CompiledStateGraph
from PIL import Image
from io import BytesIO

from utils import logger
from llm.tools import QQTools
from llm.build_llm import build_core_llm,build_vl_llm

from async_task_manager import BaseAsyncTask
from llm.prompt.system_prompt_template import system_prompt


from message import get_message_manager

message_manager = get_message_manager()


class Agent(BaseAsyncTask):

    @property
    def task_name(self) -> str:
        """
        任务名称（默认使用类名，子类可重写）
        :return: str
        """
        return "Advent"

    agent: Optional['CompiledStateGraph'] = None

    def __init__(self):
        try:
            self.tools = QQTools
            self.core_llm = build_core_llm('siliconflow')
            self.vl_llm,self.vl_llm_name = build_vl_llm('siliconflow')
            if self.core_llm is None:
                logger.log('llm创建失败')
                raise Exception('llm创建失败')
            #1 加载语言模型配置
            self.agent = create_agent(
                model=self.core_llm,
                tools=self.tools,
                system_prompt=system_prompt,
            )
            logger.info("Agent机器人初始化成功")
        except FileNotFoundError as e:
            logger.error(f"Agent机器人初始化失败：未找到配置文llm_config.yaml：{str(e)}")
        except Exception as e:
            logger.error(f"Agent机器人初始化失败：{str(e)}")

        #2 初始化历史对话管理
        self.chat_history = []

    async def run(self, abort_flag: Event):
        """
        重写BaseAsyncTask的方法，开启智能体处理消息队列，进行QQ对话
        :param abort_flag: asyncio.Event,Event事件，用于控制任务的开启和暂停
        :return: void
        """
        _message_manager = get_message_manager()
        while not abort_flag.is_set():
            try:
                msg = await _message_manager.get_message()
                print("开始对话")
                await self.async_chat(msg)
                print("结束对话")
            except Exception as e:
                logger.error("对话出现错误",str(e))

    async def async_chat(self, user_prompt: str) -> str:
        """
        异步的agent对话方法，用于提供给run方法
        :param user_prompt: str,接受用户传入一个字符串
        :return: str,返回ai回复内容
        """
        #构造消息流

        global text
        full_response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(user_prompt),
            ]
        })
        # tool_calls = full_response['messages'][1].tool_calls # 获取tool_calls对象
        # for tool_call in tool_calls:
        #     if tool_call.get("name") == "send_qq_message":
        #         args = tool_call.get("args",{})
        #         text = args.get("text",'')

        msg = full_response['messages'][-1].content
        print(msg)
        return msg

    async def async_vl(self, url: str) -> str:
        """
        :param url: 传入图片的url
        :return: 当存在视觉识别模型的时候返回解析内容，不存在直接打印没有配置视觉模型
        """
        # 为None说明模型初始化阶段失败
        if self.vl_llm is None:
            logger.log("没有可以使用的视觉模型，请检查llm_config.yaml文件中的配置")
            return ''
        async  with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    image_byte = await resp.content.read()
                else:
                    logger.error("请求视觉模型失败")
                    return ''
        with Image.open(BytesIO(image_byte)) as img:
            resized_img = img.resize((160,160))
            buffer = BytesIO()
            # 根据原图格式保存（这里假设为PNG，可根据实际情况调整）
            resized_img.save(buffer, format=img.format or 'JPG')

        image_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        try:
            response = self.vl_llm.chat.completions.create(
                model = self.vl_llm_name,
                messages =
                [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": "data:application/pdf;base64,"+ image_str,
                                    "detail": "low"
                                }
                            },
                            {
                                "type": "text",
                                "text": "非常简短的描述这一张表情包或者图片"
                            }
                        ]
                    }
                ],
            )

            print(response.choices[0].message.content)
            return response.choices[0].message.content
        except Exception as e:
            logger.error("请求失败",str(e))
            return ''

_agent: Optional['Agent'] = None  # 正确的类型注解 + 初始值

def get_agent():

    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent

if __name__ == '__main__':
    ad = Agent()

    asyncio.run( ad.async_vl("https://ts1.tc.mm.bing.net/th/id/R-C.b462f4f34a59260f49ec40a176468c0e?rik=b2hc1zyYFJYtLw&riu=http%3a%2f%2fseopic.699pic.com%2fphoto%2f50020%2f5325.jpg_wh1200.jpg&ehk=NSMaSPA3bpcWKSEcxGbAy%2fmr%2bAeOu5I1qgC6xAJIae8%3d&risl=&pid=ImgRaw&r=0"))
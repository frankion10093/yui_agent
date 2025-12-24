import yaml
import os

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain.agents import create_agent

from qq import qq_manager
from utils import logger
from tools import LocalTools,QQTools
from llm.build_llm import build_ollama
from llm.build_llm import build_siliconflow



class Advent:

    def __init__(self, tools=LocalTools,llm=build_ollama()):
        try:
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(parent_dir, 'config', 'llm_config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                #1 加载语言模型配置
                temp = yaml.safe_load(f)
                #2 初始化系统提示词
                system_prompt = temp['system_prompts']['猫娘']

                self.agent = create_agent(
                    model=llm,
                    tools=tools,
                    system_prompt=system_prompt,
                )

                print(system_prompt)
        except FileNotFoundError:
            logger.critical(f"初始化失败：未找到配置文llm_config.yaml")
        except Exception as e:
            logger.critical(f"初始化失败：{e}")

        #3 初始化历史对话管理
        self.chat_history = []



    def chat(self, user_prompt: str):
            #构造消息流
            full_response = ''
            full_response = self.agent.invoke({
                "messages": [
                    HumanMessage(user_prompt),
                ]
            })
            msg = full_response['messages'][-1].content
            print(msg)
            return msg

    def send_message(self):
        while True:
            try:
                msg = qq_manager.msg_queue.get()
                if msg != '' or None:
                    print("开始对话")
                    chatbot.chat(msg)
                    print("结束对话")
            except Exception as e:
                logger.error(e)


chatbot = Advent(tools=QQTools)


if __name__ == '__main__':
    ad = Advent()
    while True:
        input_str = input("请输入：")
        ad.chat(input_str)
        if input_str == 'exit':
            break
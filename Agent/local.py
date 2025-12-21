import json
from llm import Advent
import websocket
from llm import build_siliconflow

if __name__ == '__main__':
    chatbot = Advent(llm=build_siliconflow())
    wb = websocket.create_connection("ws://192.168.31.100:5788/")
    while True:
        user_input = input("请输入：")
        if user_input == "exit":
            break
        chatbot.chat(user_input)

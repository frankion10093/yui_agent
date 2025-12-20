import json
from llm import Advent
import websocket

if __name__ == '__main__':
    chatbot = Advent()
    wb = websocket.create_connection("ws://8.148.5.68:5788/")
    while True:
        user_input = input("请输入：")
        if user_input == "exit":
            break
        chatbot.chat(user_input)

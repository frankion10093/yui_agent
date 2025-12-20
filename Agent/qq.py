import json
from llm import Advent
from tools import QQTools
import websocket
from utils import parse_group_message_to_log
import asyncio

chatbot = Advent(QQTools)
wb = websocket.create_connection("ws://192.168.31.100:5788/")
huifu = 0
while True:


    msg = wb.recv()
    # msg :dict = json.loads(msg)
    # msg = msg.__str__()
    # chatbot.chat(msg)
    print(msg)
    msg = json.loads(msg)
    # parse_message(msg)
    msg = parse_group_message_to_log(msg)
    if(msg != ''):
        chatbot.chat(msg)


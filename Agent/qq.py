import concurrent
import json
from llm import Advent
from tools import QQTools
import websocket
from qq_operation import parse_group_message_to_log
from concurrent.futures import TimeoutError
from utils import logger
from llm import build_siliconflow
import queue

msg_queue = queue.Queue(maxsize=1000)

chatbot = Advent(tools=QQTools,llm=build_siliconflow())
#生产者消费者模型
def get_message():
    wb = websocket.create_connection("ws://192.168.31.100:5788/")
    while True:
        msg = wb.recv()
        msg = json.loads(msg)
        print(msg)
        # if msg.get("group_id") != 533350129:
        msg = parse_group_message_to_log(msg)
        if msg != '':
            msg_queue.put(msg)
            print(msg_queue.qsize())

def send_message():
    while True:
        try:
            msg = msg_queue.get()
            if msg != '' or None:
                print("开始对话")
                chatbot.chat(msg)
                print("结束对话")
        except Exception as e:
            logger.error(e)

with concurrent.futures.ThreadPoolExecutor(max_workers=13) as executor:
    executor.submit(get_message)
    executor.submit(send_message)






import json
from llm import Advent

from concurrent.futures import TimeoutError

import concurrent.futures

def task(n):
    agent = Advent()
    while True:
        res = agent.chat("你好,帮我写1000字作文，标题为穷人，直接开始写")
        print('线程池1回复:'+res)

def task1(n):
    agent = Advent()
    while True:
        res = agent.chat("你好,帮我写1000字作文，标题为穷人，直接开始写")
        print('线程池2回复:'+res)


def task2(n):

    agent = Advent()
    while True:
        res = agent.chat("你好,帮我写1000字作文，标题为穷人，直接开始写")
        print('线程池3回复:'+res)

def task3(n):

    agent = Advent()
    while True:
        res = agent.chat("你好,帮我写1000字作文，标题为穷人，直接开始写")
        print('线程池4回复:'+res)

def task4(n):

    agent = Advent()
    while True:
        res = agent.chat("你好,帮我用c语言实现链表")
        print('线程池5回复:'+res)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future1 = executor.submit(task, 5)
        future2 = executor.submit(task1, 6)
        future3 = executor.submit(task2, 6)
        future4 = executor.submit(task3, 6)
        future5 = executor.submit(task4, 6)

    # chatbot = Advent(QQTools)
    # wb = websocket.create_connection("ws://192.168.31.100:5788/")
    # huifu = 0
    # while True:
    #
    #     msg = wb.recv()
    #     msg = json.loads(msg)
    #     if msg.get('message_type') == 'group':
    #         print(msg)
    #         msg ="用户"+msg['sender']['nickname']+" "+"qq号"+str(msg['user_id'])+"在qq群号"+str(msg['group_id'])+"的群聊中说"+str(msg['message'][0]['data']['text'])
    #         chatbot.chat("请回复这条信息：" + msg)
    print(__file__)

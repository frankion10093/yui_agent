import os
import yaml
import random
import string
import hashlib
import hmac
import struct
import websocket
import time
import threading
import requests
import json
from utils import logger
'''
Operation
OP_HEARTBEAT	2	客户端发送的心跳包(30秒发送一次)
OP_HEARTBEAT_REPLY	3	服务器收到心跳包的回复
OP_SEND_SMS_REPLY	5	服务器推送的弹幕消息包
OP_AUTH	7	客户端发送的鉴权包(客户端发送的第一个包)
OP_AUTH_REPLY	8	服务器收到鉴权包后的回复
"P4c11P4115De7Glb4StkFTPs"
"cI4sn7MNW1FtgH5IV0ASpSGXTBtSep"
'''



class bilibili:
    #这个是获取的accesskeyid
    accesskeyidValue = ''
    #这个是获取的secret_key
    secret_key = ''
    #这是公共请求地址
    base_url = ''
    #这个是获取的鉴权信息
    auth_body = ""
    #这个是获取的wss链接，一般返回的是四个链接，这里只取第一个
    wss_url = ''
    #这个是获取的场次id,用于发送心跳包
    game_id = ''
    #这个是房间id
    room_id =''
    #这个b站是项目编号
    app_id =0

    ws =None

    #控制线程开启或者关闭
    is_listening = False

    def __init__(self):
        try:
            #初始化为文件夹的根路径
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.dirname(parent_dir)
            config_path = os.path.join(path, 'config', 'live_config.yaml')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f, Loader=yaml.FullLoader)
            self.base_url = config["bilibili"]['base_url']
            self.room_id = config["bilibili"]['room_id']
            self.app_id = config["bilibili"]['app_id']
            self.accesskeyidValue = config["bilibili"]['accesskeyidValue']
            self.secret_key = config["bilibili"]['secret_key']
        except Exception as e:
            logger.error(e)
            print(e)

    def init_bilibili(self):
        """
        这个函数用于初始化b站
        :return: 初始化b站，返回socket对象，t1线程，t2线程
        """

        # 开始初始化b站
        strat_success = self.start_bilibili()
        if not strat_success:
            logger.error("初始化b站失败,原因是获取鉴权信息失败，第一次api请求")
            return False

        logger.info("初始化b站成功")
        # 启动websocket连接
        self.ws = self.start_websocket(self.selfwss_url,self.selfauth_body)

        #创建线程，用于发送心跳包
        t1 = threading.Thread(target=self.send_ws_heartbeat, args=(self.ws,),daemon=True)

        # 启动api心跳包发送线程
        t2 = threading.Thread(target=self.send_api_heartbeat,daemon=True)

        self.is_listening = True

        #开启了多线程利用while不断循环配合sleep来实现定时发送心跳包
        t1.start()
        t2.start()

        #返回的第一个值是用于数据通信，第二三个值是用于线程的管理，分别对应websocket长连和发送API心跳包
        return True

    def start_websocket(self, wss_url, auth_body):
        """
        这个方法主要用于第一次建立服务器的连接
        :param wss_url:
        :param wss_url:
        :param auth_body:
        :return: 返回socket对象
        """

        # 传入这个body参数，进行构建数据包
        auth_packet = self.build_packet(7, auth_body)

        ws = None

        try:
            # 创建websocket连接
            ws = websocket.create_connection(wss_url)

            # 发送鉴权包
            ws.send(auth_packet)
            print("鉴权成功")
        except Exception as e:
            logger.error(e)

        return ws

    def send_ws_heartbeat(self, ws):
        """
        这个方法主要用于ws启动心跳包的发送
        :param ws:
        :return:
        """

        while self.is_listening:
            # 构建心跳包,根据开发的api手册operation2是心跳包，发送心跳包的时候不需要携带消息体为空即可
            heartbeat_packet = self.build_packet(2, '')
            ws.send(heartbeat_packet)
            # 延时30秒发送一次心跳包
            time.sleep(30)

    def send_api_heartbeat(self):
        """
        这个方法主要用于api启动心跳包的发送
        :return:
        """
        body_json = {
                "game_id":self.game_id
        }

        body_data = json.dumps(body_json, ensure_ascii=False)



        while self.is_listening:
            # 这里是发送心跳包的api接口，根据开发的api手册，这里是发送一个post请求，参数是game_id
            headers = self.get_request_headers(body_data)

            response = requests.post(self.base_url + "/v2/app/heartbeat", headers=headers, json=body_json)
            if response.json()['code'] == 0:
                time.sleep(30)
            else:
                print("api发送心跳包失败")
                return False


    def start_bilibili(self):
        """
        向api发送第一次请求获取到第一次返回的重要信息，报错game_id和wss_url
        :return: ture or false
        """
        # 构建基本请求信息
        body_json= {
            "code":self.room_id,
            "app_id": self.app_id,
        }

        # 转为字符串
        body_data = json.dumps(body_json, ensure_ascii=False)

        # 获取请求头,传入值为body的 json 字符串
        headers = self.get_request_headers(body_data)


        # 保存初始化后b站返回信息
        response = requests.post(self.base_url + "/v2/app/start", headers=headers, json=body_json)

        if response.status_code == 200:
            if response.json()['code'] == 0:
                response = response.json()
                # 这个是获取的鉴权信息
                self.selfauth_body = response['data']['websocket_info']['auth_body']

                # 这个是获取的wss链接，一般返回的是四个链接，这里只取第一个
                self.selfwss_url = response['data']['websocket_info']['wss_link'][0]

                # 这个是获取的场次id,用于发送心跳包
                self.game_id = response['data']['game_info']['game_id']
                logger.info("初始化b站成功")
                return True
            else:
                logger.error(response.json()['message'])
                return False
        else:
            logger.error(" 请求失败, 状态码: " + str(response.status_code))
            return False

    def build_packet(self, operation, body):
        """
        构造符合B站长链协议的数据包
        :param operation: 操作类型（如OP_AUTH=7、OP_HEARTBEAT=2）
        :param body: 消息体（JSON字符串或空字符串）
        :return: 完整二进制数据包
        """
        # 这一步是将json格式的消息体转换成字节数组，如果没有消息体则为空字节数组
        body_bytes = body.encode('utf-8') if body else b''

        body_len = len(body_bytes)
        total_len = 16 + body_len  # 包头16字节 + 消息体长度
        # 按大端对齐打包包头：Packet Length(4) + Header Length(2) + Version(2) + Operation(4) + Sequence ID(4)
        header = struct.pack(
            '>IhhiI',  # >大端对齐，IhhiI告诉struck如何将数据打包
            total_len,
            16,  # Header Length固定为16
            0,  # Version=0（Body为原始数据）
            operation,
            0  # Sequence ID为保留字段，填0即可
        ) + body_bytes  # 消息体追加到包头后面

        return header

    def generate_signature_nonce(self, length=32):
        """
        生成32位随机字符串，作为加密签名的随机数
        :param length:
        :return: 随机生成的32位字符串
        """
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def get_md5(self, body_data: str):
        """
        获取md5值，值是根据请求体生成的
        :param body_data:
        :return:  md5值
        """
        md5 = hashlib.md5()
        md5.update(body_data.encode('utf-8'))
        return md5.hexdigest()

    def get_request_headers(self,body_data: str):
        """
        获取请求头
        :param body_data: 传入post出去的json转化后的字符串
        :return: 构建好的请求头
        """
        signatureNonceValue = self.generate_signature_nonce()

        contentMd5Value = self.get_md5(body_data)

        timestamp = str(int(time.time()))

        body_data = f"""x-bili-accesskeyid:{self.accesskeyidValue}
x-bili-content-md5:{contentMd5Value}
x-bili-signature-method:HMAC-SHA256
x-bili-signature-nonce:{signatureNonceValue}
x-bili-signature-version:1.0
x-bili-timestamp:{timestamp}"""

        signature = hmac.new(self.secret_key.encode(), body_data.encode(), digestmod=hashlib.sha256).hexdigest()

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-bili-accesskeyid": self.accesskeyidValue,
            "x-bili-content-md5": contentMd5Value,
            "x-bili-signature-method": "HMAC-SHA256",
            "x-bili-signature-nonce": signatureNonceValue,
            "x-bili-signature-version": "1.0",
            "x-bili-timestamp": timestamp,
            "Authorization": signature
        }

        return headers

if __name__ == '__main__':
    pass


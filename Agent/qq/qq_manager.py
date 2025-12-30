import asyncio
import json
from asyncio import Event
from typing import Optional

import aiohttp

import websockets
import yaml
import os

from pydantic import BaseModel
from yaml import YAMLError

from utils import logger

from async_task_manager import get_async_task_manager,BaseAsyncTask
from message import get_message_manager


class QQBaseConfig(BaseModel):
    #发送请求的基本路径
    base_url: str
    #监听请求的基本路径
    base_ws_url: str
    # 请求超时设置
    timeout: int


class QQApiConfig(BaseModel):
    #基础私聊架构
    base_private_api: dict
    base_group_api: dict
    #记录不同功能的的path
    base_path: dict


class QQManager(BaseAsyncTask):
    """QQ消息构造器"""

    def __init__(self):
        """需要初始化写死的参数在这里进行初始化"""

        self.ws_conn: Optional["websockets"] = None


        # 读取配置文件
        try:
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'napcat_config.yaml'
            )

            with open(path, 'r', encoding='utf-8') as f:
                #初始化加载配置文件
                base: dict = yaml.safe_load(f)['napcat']
                config = base['config']
                api = base['qq_api']
                self.base_config = QQBaseConfig(**config)
                self.api_config = QQApiConfig(**api)
                logger.info("QQ管理器初始化成功")

        except FileNotFoundError as e:
            logger.error("napcat_config.yaml配置文件不存在: %s", str(e))
        except YAMLError as e:
            logger.error(f"配置文件解析失败（YAML格式错误）: {str(e)}")
        except KeyError as e:
            logger.error("配置文件格式错误，缺少关键节点[%s]: %s", str(e), str(e))
        except Exception as e:
            logger.error("读取配置文件失败: %s", str(e))

    async def _init_ws_conn(self):
        """初始化/重连全局WebSocket连接"""
        while True:
            try:
                # 创建全局WS连接
                self.ws_conn = await websockets.connect(self.base_config.base_ws_url)
                break  # 连接成功退出重连循环
            except Exception as e:
                logger.error(f"WebSocket连接失败，3秒后重试重试：{str(e)}")
                await asyncio.sleep(3)

    async def run(self, abort_flag: Event):
        """
        重写BaseAsyncTask的方法，开启qq消息监听
        :param abort_flag: asyncio.Event,Event事件，用于控制任务的开启和暂停
        :return: void
        """
        _async_task_manager = get_async_task_manager()
        _message_manager = get_message_manager()
        print("开启监听QQ消息")
        """启动监听"""
        #检查链接是否初始化
        if self.ws_conn is None:
            await self._init_ws_conn()

        while not abort_flag.is_set():
            msg = await self.ws_conn.recv()
            #拿到小新将消息转换成json格式
            msg = json.loads(msg)
            #存入消息队列
            await _message_manager.add_message(msg)

    @property
    def task_name(self) -> str:
        return "QQManager"  # 同名任务的唯一标识



    def build_message(self, message_type: str, qq_id: str, reply_strategy: str, target_id: str, text: str):
        """
        构架ai发送消息
        :param message_type: str，发送消息的类型可以取值 private | group
        :param qq_id: str，qq号或者群号，根据message_type来决定
        :param reply_strategy: str，回复的方式取值 direct | at | reply
        :param target_id: str，发送消息内@对方的qq号，或者具体回复哪条信息id号，如果回复方式是direct就直接回复
        :param text: str，需要发送的文本内容
        :return: dict，返回构建好的信息，用于发送qq信息
        """
        message_json: dict

        if message_type == 'group':
            message_json = self.api_config.base_group_api
            message_json['group_id'] = qq_id
        elif message_type == 'private':
            message_json = self.api_config.base_private_api
            message_json['user_id'] = qq_id
        else:
            logger.warning("请填写正确的message_type")
            return None

        text_segment = {
            "type": "text",
            "data": {"text": text}
        }

        strategy_prefix_map = {
            'at': {"type": "at", "data": {"id": target_id}},
            'reply': {"type": "reply", "data": {"id": target_id}}
        }

        if reply_strategy in strategy_prefix_map:
            message_json['message'] = [
                strategy_prefix_map[reply_strategy],
                text_segment
            ]
        elif reply_strategy == 'direct':
            message_json['message'] = [text_segment]
        else:
            logger.warning("请填写正确的reply_strategy（可选值：at/reply/no）")
            return None
        return message_json

    async def send_request(self, api_type: str, data: dict) -> str:
        """
        异步的发送qq信息的方法，可以发送各种定义好的qq操作，可以参考config/napcat_config.yaml内哪些api支持
        :param api_type: str，需要传入可以调用的api方法的参数名
        :param data: dict，传入构建好的消息体
        :return: str，返回消息发送后返回的内容
        """

        """这个方法用户判断获取的的消息类型，然后调用对应的api发送消息"""
        if api_type == '' or data is None:
            return "notice参数为空请重新构建"
        if data is None:
            return "data参数为空请重新构建"
        if self.api_config.base_path.get(api_type) is None:
            return f"没有{api_type}这个方法哦"
        try:
            url: str = self.base_config.base_url + self.api_config.base_path[api_type]
            timeout: int = self.base_config.timeout
            #发送消息，然后处理后的napcat返回的 message
            async with aiohttp.ClientSession() as seesion:
                async with seesion.post(url=url, json=data,timeout=timeout) as res:
                    if res.status == 200:
                        return "发送成功，无需重复进行操作"
                    else:
                        return "发送失败，请再次尝试"
        except Exception as e:
            logger.error("发送消息失败", e)


_qq_manager: Optional[QQManager] = None

def get_qq_manager() -> QQManager:
    """
    获取异步任务管理器单例
    :return: AsyncTaskManager实例
    """
    global _qq_manager
    if _qq_manager is None:
        _qq_manager = QQManager()
    return _qq_manager

if __name__ == '__main__':
    qq_message = QQManager()


import requests
import yaml
import os
from langchain.tools import tool,ToolRuntime
import requests as rq
from pydantic import Field
from qq_operation import QQMessage

qq_message = QQMessage()

@tool
def send_qq_message(organization: str,target_id : str, message_list: list[dict] ) -> str:
    """这个方法用于给qq回复信息，你需要提供参数
        organization: 消息的类型类型，private |  group,private表示私聊，group表示群聊。
        target_id: 目标id，如果发送类型是私聊，则为对方的qq号，如果发送类型是群聊，则为群号。
        message_list: 包含多个字典的列表，message_list列表中的每个字典的定义如下：
        第一个参数data: dict
        第二个参数type: str
        type字段是at时表示艾特，data就包含qq的键，值为艾特的qq号
        type字段是text时表示纯文本，data就包含text的键，值为要发送的文本内容
        回复样例:
        [{"type": "text", "data": {"text": "你好，我是机器人，很高兴为你服务！"}}]
        [{"type": "at", "data": {"qq": "123456789"}},{"type": "text" "data": {"text": "你好，我是机器人，很高兴为你服务！"}}]
        你可以根据不同的情景组合进行回复，每个字典表示一条消息，可以随意组合
        最外层是列表，内部是用逗号分割的字典
    """
    print("调用了发送qq消息")
    print(message_list)
    try:
        message = qq_message.build_message(organization=organization,message_data=message_list,target_id=target_id)
        print(message)
        # 发送消息
        requests.post(
            url=f'http://192.168.31.100:3000/send_{organization}_msg',
            json=message,
        )
        return f"qq信息发送成功,无需进行任何操作"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"


@tool
def qq_utils(notice: str, message_data: dict) -> str:
    """这个方法用于使用qq的一些功能
        notice: 功能的名称，类型为str，
        message_data: 功能所需的参数，类型为dict，
        根据你自己的判断来决定传入的参数
        功能列表：
        1. (当用户言论激烈时调用这个功能，可以进行一些限制)禁言：禁言功能，需要三个参数，第一个参数为"group_id": 群聊qq号，第二个参数为禁言的对象"user_id": 用户qq号，第三个参数为禁言时长"duration": 单位为秒，默认为10-30秒。
    """
    print(f"调用了{notice}功能")
    try:
        # 发送消息
        response = requests.post(
            url=f'http://192.168.31.100:3000/set_group_ban',
            json=message_data,
        )
        return f"{response}"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"

QQTools = [
    send_qq_message,
    qq_utils
]

if __name__ == '__main__':
    pass

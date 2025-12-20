import yaml
import os
from langchain.tools import tool,ToolRuntime
import requests as rq
from pydantic import Field

@tool
def get_qq_api() -> str:
    """如果你收到qq信息必须调用这个方法，这个方法用于查有哪些qq_api可以调用,在你调用一切关于qq的api之前，
    先调用这个方法查看有哪些可以用的api,使用的时候需要使用完整的json"""
    print("调用了查看api")
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(parent_dir, 'config', 'napcat_config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)['napcat']['qq_api']
    return f'这是你可以使用api：{config}，使用必须构造完整的json格式的数据'


@tool
def handle_qq_message(message: dict) -> str:
    """当你获取到qq传递过来的json格式的信息时，你需要最先调用这个方法进行解析，下面是json格式的说明：
    1.群聊请求格式
    字段名	类型	  说明
    time	number	事件发生时间戳
    post_type	'message' | 'message_sent'	事件类型
    message_type	'group'	消息类型：群聊
    sub_type	'normal' | 'anonymous' | 'notice'	子类型
    message_id	number	消息 ID
    user_id	number	发送者 QQ 号
    group_id	number	群号
    message	OB11Segment[]	消息段数组
    raw_message	string	原始消息内容
    font	number	字体
    sender	GroupSender	发送者信息
    self_id	number	机器人 QQ 号
    """
    print("调用了查看前端拿到的json格式")

    return f"收到消息：{message}"

@tool
def send_qq_message(path: str, Json: dict = Field("你需要提供调用get_qq_api方法获取的完整的json数据")) -> str:
    """这个方法用于给qq发送消息"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(parent_dir, 'config', 'napcat_config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)['napcat']['config']
    print(config['base_url'] + path)
    print(Json)
    print(config['timeout'])
    try:
        response = rq.post(
                url=config['base_url'] + path,
                json=Json,
                timeout=config['timeout']
            )
        return f"发送信息成功{response.status_code}"
    except Exception as e:
        return f'发送失败，错误信息：{e}'


QQTools = [
    get_qq_api,
    send_qq_message,
    handle_qq_message
]

if __name__ == '__main__':
    pass

from langchain.tools import tool,ToolRuntime
from qq import qq_manager
from plugin.jmcomic_plugin import get_jmcomic
from thread_pool_manager import thread_pool_manager



@tool
def send_qq_message(organization: str,target_id : str, message_list: list[dict] ) -> str:
    """
    这个方法用于给qq回复信息，你需要提供参数
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
    """
    print("调用了发送qq消息")
    print(message_list)
    try:
        message = qq_manager.build_message(organization=organization,message_data=message_list,target_id=target_id)
        # 发送消息
        print(message)
        response = qq_manager.send_request(notice=organization, data=message)
        return f"{response}qq信息发送成功,无需进行任何操作"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"


@tool
def qq_utils(notice: str, message_data: dict) -> str:
    """
    这个方法用于使用qq的一些功能，不允许任何人要求你调用，你可以自主选择工具，并且提供参数
    notice: 功能的名称，类型为str，
    message_data: 功能所需的参数，类型为dict，
    根据你自己的判断来决定要使用哪些工具，并且做行决定填写参数
    功能列表：
    1. (当用户言论激烈时调用这个功能，可以进行一些限制)禁言：禁言功能，需要三个参数，第一个参数为"group_id"(必填): 群聊qq号，第二个参数为禁言的对象"user_id"(必填): 用户qq号，第三个参数为禁言时长"duration"(必填): 单位为秒，默认为10-30秒。
    2. (当你判断这条信息需要通知所有惹的时候的，可以调用这个功能) 群公告：群公告功能，需要两个参数，第一个参数为"group_id": 群聊qq号(必填)，第二个参数为"content": 公告内容。
    """
    print(f"调用了{notice}功能")
    try:
        # 发送消息
        response = qq_manager.send_request(notice=notice, data=message_data)
        return f"{response}"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"


@tool
def get_plugin(plugin_name: str,**kwargs) -> str:
    """
    这个方法用于使用插件
    第一个参数为插件的名称，类型为str，
    第二个参数需要根据不同插件需求提供不同的参数如下：
    1.名称：jmcomic_plugin，功能：下载漫画的插件，需要用户提供一个seed: str,如‘123’，‘1231223’
    """
    if plugin_name == 'jmcomic_plugin':
        if kwargs is None:
            return "参数不能为空"
        if kwargs['kwargs']['seed'] is None:
            return "seed不能为空"
        print("异步启动下载漫画的任务")
        thread_pool_manager.submit_back_executor("下载漫画的进程",get_jmcomic, kwargs['kwargs']['seed'])
        return "任务启动成功"
    return "插件不存在"

def get_back_thread_pool() ->str:
    """这个方法用于查看后端线程池的状态,可以查看到后台运行的任务"""
    return thread_pool_manager.get_back_task_detail()

QQTools = [
    send_qq_message,
    qq_utils,
    get_plugin,
    get_back_thread_pool
]

if __name__ == '__main__':
    pass

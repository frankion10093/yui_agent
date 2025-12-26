from langchain.tools import tool,ToolRuntime


from plugin.jmcomic_plugin import get_jmcomic
from thread_pool_manager import thread_pool_manager

from qq import qq_manager
from utils import logger


@tool
def send_qq_message( message_type: str, qq_id: str, reply_strategy: str, target_id: str, text: str) -> str | None:
    """
    这个方法用于给qq回复信息，你需要提供参数
    message_type: group | private
    qq_id:群聊id或者私聊对象的id
    reply_strategy: 是否艾特回复，at (概率为10%) | reply (概率为10%) | no (概率为80%)当私聊时不能为at
    target_id: 目标id，当call为at时，target_id为艾特的qq号，当call为reply时，target_id为消息的id号，当reply_strategy的值为no时，target_id为None
    text: 要发送的文本内容
    """

    try:
        print(message_type, qq_id, reply_strategy, target_id, text)
        message_json = qq_manager.build_message(message_type,qq_id,reply_strategy, target_id,text)

        if message_json is not None:
            print(message_json)
            res = qq_manager.send_request(message_type, message_json)
            return f"{res} qq信息发送成功,无需进行任何操作"
        else:
            return f"消息构建失败无需再次尝试"
    except Exception as e:
        logger.error("向qq发送消息失败",e)




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
    后续参数根据不同插件提供
    1.名称：jmcomic_plugin，功能：下载漫画的插件，需要用户提供一个seed: str,如‘123’，‘1231223’
    """
    try:
        if plugin_name == 'jmcomic_plugin':
            thread_pool_manager.submit_back_executor("下载漫画的进程",get_jmcomic, kwargs['kwargs']['seed'])
            return "任务启动成功"
        return "插件不存在"
    except Exception as e:
        logger.error("发生报错",e)
        return f"发生报错"

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

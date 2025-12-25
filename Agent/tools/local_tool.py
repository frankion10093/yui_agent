import json
import threading
from datetime import datetime

from langchain.tools import tool
import pyautogui as pg
from plugin.live_plugin import bilibili

#初始化b站实例
b = bilibili()


@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气（占位版）：输入 city，返回固定友好提示，并非实时天气。"""
    return f"{city}总是阳光明媚！"


@tool
def mouse_move(x: int, y: int) -> str:
    """将鼠标移动到屏幕坐标 (x, y)，单位为像素，需提供整数坐标。"""
    pg.moveTo(x, y)
    return f"鼠标移动到屏幕坐标({x},{y})"


@tool
def open_app(app_name: str) -> str:
    """根据 app_name 生成已打开的提示文本；当前实现不真正启动应用。"""
    return f"{app_name}已经打开"


@tool
def bilibili_live(is_live: bool) -> str:
    """控制 B 站直播：is_live=True 开启并启动监听线程，False 置 is_listening=False 以关闭。"""
    try:
        if is_live:
            if (b.init_bilibili()):
                #开启线程监听信息
                t = threading.Thread(target=start_bilibili)

                t.start()

                return f"启动B站直播成功！"
            else:
                return f"启动B站直播失败！"
        else:
            #这里的逻辑是关闭守护线程，从而主线程会自动关闭
            b.is_listening = False
            return f"关闭B站直播成功！"
    except Exception as e:
        return f"启动B站直播失败：发生报错{e}"


def start_bilibili():
    """监听 B 站直播弹幕并打印 cmd 字段。"""
    while b.is_listening:
        row_data = b.ws.recv()
        if len(row_data) >= 21:
            #转换为json格式
            json_str = row_data[16:].decode("UTF-8")
            json_data = json.loads(json_str)
            if (json_data.get("cmd") != None):
                print(json_data["cmd"])


def get_time():
    """返回当前时间，格式 YYYY-MM-DD HH:MM:SS。"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

LocalTools = [
    get_weather_for_location,
    mouse_move,
    bilibili_live, open_app,
    get_time
]

if __name__ == '__main__':
    pass

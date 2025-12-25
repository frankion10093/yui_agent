from langchain.tools import tool
from qq import qq_manager
from plugin.jmcomic_plugin import get_jmcomic
from thread_pool_manager import thread_pool_manager



@tool
def send_qq_message(organization: str, target_id: str, message_list: list[dict]) -> str:
    """发送 QQ 消息（必用工具，严格填参）：
    - organization: "private"(私聊) 或 "group"(群聊)，大小写固定。
    - target_id: 私聊填对方 QQ 号，群聊填群号，不能为空，且必须为数字字符串。
    - message_list: 非空列表，每项结构 {"type": "text"|"at", "data": {...}}。
      * type="text" → data:{"text": "内容"}，内容为字符串。
      * type="at"   → data:{"qq": "要艾特的 QQ 号"}。
    - 示例（私聊）：[{"type": "text", "data": {"text": "你好"}}]
    - 示例（群聊艾特）：[{"type": "at", "data": {"qq": "123"}}, {"type": "text", "data": {"text": "欢迎"}}]
    返回发送结果；若参数缺失或格式错误，直接返回错误提示。"""
    if organization not in ("private", "group"):
        return "organization 必须是 'private' 或 'group'"
    if not target_id:
        return "target_id 不能为空"
    if not target_id.isdigit():
        return "target_id 必须为数字字符串"
    if not isinstance(message_list, list) or not message_list:
        return "message_list 必须是非空列表"

    # 轻量校验 message_list 结构，减少调用失败
    total_length = 0
    for idx, item in enumerate(message_list):
        if not isinstance(item, dict):
            return f"message_list 第 {idx} 项必须是字典"
        if item.get("type") not in ("text", "at"):
            return f"message_list 第 {idx} 项的 type 只能是 'text' 或 'at'"
        if item["type"] == "text" and not item.get("data", {}).get("text"):
            return f"message_list 第 {idx} 项 text 内容不能为空"
        if item["type"] == "at" and not item.get("data", {}).get("qq"):
            return f"message_list 第 {idx} 项 at 缺少 qq"
        # 累加长度（text 内容）
        if item["type"] == "text":
            total_length += len(item["data"]["text"])
        if item["type"] == "at":
            total_length += len(item["data"]["qq"]) + 5  # 估算 @ 长度

    # 裁剪长度（QQ 消息上限约 2000 字符）
    if total_length > 2000:
        # 简单裁剪：从最后一个 text 项开始截断
        excess = total_length - 2000
        for idx in reversed(range(len(message_list))):
            item = message_list[idx]
            if item["type"] == "text":
                text = item["data"]["text"]
                if len(text) > excess:
                    item["data"]["text"] = text[:len(text) - excess]
                    break
                else:
                    excess -= len(text)
                    message_list.pop(idx)
                    if excess <= 0:
                        break
        # 裁剪后继续发送，不返回错误

    try:
        message = qq_manager.build_message(organization=organization, message_data=message_list, target_id=str(target_id))
        response = qq_manager.send_request(notice=organization, data=message)
        if response is None:
            return "发送完成（无返回体）"
        return f"{response}"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"


@tool
def qq_utils(notice: str, message_data: dict) -> str:
    """QQ 管理功能（谨慎调用）：
    - notice: 只能是 "禁言" 或 "群公告"。
    - message_data: 按功能填参：
      * 禁言 → {"group_id": 群号(str/int), "user_id": QQ 号(str/int), "duration": 秒数(10-30 推荐)}
      * 群公告 → {"group_id": 群号(str/int), "content": 公告内容(str)}
    参数缺失或格式错误将直接返回提示，避免误操作。"""
    if notice not in ("禁言", "群公告"):
        return "notice 只能是 '禁言' 或 '群公告'"
    if not isinstance(message_data, dict):
        return "message_data 必须是字典"

    required = {
        "禁言": ("group_id", "user_id", "duration"),
        "群公告": ("group_id", "content"),
    }
    for key in required[notice]:
        if key not in message_data or message_data.get(key) in (None, ""):
            return f"缺少必填参数 {key}"

    # 额外校验 ID 为数字字符串
    if notice == "禁言":
        if not str(message_data["group_id"]).isdigit():
            return "group_id 必须为数字字符串"
        if not str(message_data["user_id"]).isdigit():
            return "user_id 必须为数字字符串"
        if not isinstance(message_data["duration"], (int, str)) or (isinstance(message_data["duration"], str) and not message_data["duration"].isdigit()):
            return "duration 必须为正整数"
    elif notice == "群公告":
        if not str(message_data["group_id"]).isdigit():
            return "group_id 必须为数字字符串"

    try:
        response = qq_manager.send_request(notice=notice, data=message_data)
        if response is None:
            return "操作完成（无返回体）"
        return f"{response}"
    except Exception as e:
        return f"{e}发送失败,尝试重新发送"


@tool
def get_plugin(plugin_name: str, seed: str | None = None, **kwargs) -> str:
    """调用插件：
    - 仅支持 plugin_name="jmcomic_plugin"。
    - seed 必填（字符串）。直接传 seed="123"，或兼容 seed 未命名传入的旧写法 kwargs={"seed": "123"}。
    - seed 缺失或其他插件名将返回提示，不执行任务。"""
    if plugin_name == 'jmcomic_plugin':
        # 兼容两种写法
        seed_val = seed or kwargs.get('seed') or kwargs.get('kwargs', {}).get('seed')
        if not seed_val:
            return "seed不能为空"
        print("异步启动下载漫画的任务")
        thread_pool_manager.submit_back_executor("下载漫画的进程", get_jmcomic, seed_val)
        return "任务启动成功"
    return "插件不存在"

def get_back_thread_pool() ->str:
    """查看后台线程池状态，返回后台任务列表及状态。"""
    return thread_pool_manager.get_back_task_detail()

QQTools = [
    send_qq_message,
    qq_utils,
    get_plugin,
    get_back_thread_pool
]

if __name__ == '__main__':
    pass

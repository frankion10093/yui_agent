import json

import websocket


#这个方法主要是用于实现通用的信息解析
def parse_group_message_to_log(msg_event: dict) -> str:
    """
    将OB11协议的消息事件（群聊/私聊）解析为标准化日志字符串
    :param msg_event: 消息事件字典（符合OB11 Message结构，支持group/private类型）
    :return: 格式化后的日志字符串；若不是消息事件，返回空字符串
    """
    # 1. 基础校验：必须是消息事件
    if msg_event.get("post_type") != "message":
        return ""

    # 2. 提取消息类型（群聊/group | 私聊/private）
    message_type = msg_event.get("message_type", "")
    if message_type not in ["group", "private"]:
        return ""

    # 3. 按消息类型提取核心字段（带严格默认值，防止字段缺失）
    scene_info = ""  # 场景信息（群聊/私聊标识）
    sender_info_str = ""  # 发送者信息
    user_id = msg_event.get("user_id", "未知QQ")

    # 3.1 群聊消息解析
    if message_type == "group":
        group_id = msg_event.get("group_id", "未知群号")
        group_name = msg_event.get("group_name", f"未知群名({group_id})")
        scene_info = f"群聊 [{group_name}({group_id}])"

        # 群聊发送者信息（优先群名片 > 昵称 > QQ号）
        sender_info = msg_event.get("sender", {})
        sender_card = sender_info.get("card", "")
        sender_nickname = sender_info.get("nickname", "")
        sender_display = sender_card or sender_nickname or user_id
        sender_info_str = f"{sender_display}({user_id})"

    # 3.2 私聊消息解析
    elif message_type == "private":
        target_id = msg_event.get("target_id")  # 私聊接收方QQ
        self_id = msg_event.get("self_id")  # 机器人QQ
        # 私聊发送者信息（优先备注 > 昵称 > QQ号）
        sender_info = msg_event.get("sender", {})
        sender_remark = sender_info.get("remark", "")
        sender_nickname = sender_info.get("nickname", "")
        sender_display = sender_remark or sender_nickname or user_id
        scene_info = f"私聊 [对方:{sender_display}({target_id}) | 我方:{self_id}]"
        sender_info_str = sender_display  # 私聊场景下简化发送者展示

    # 4. 完善消息内容解析（支持OB11常见消息类型）
    def parse_ob11_message_chain(message_chain: list) -> str:
        """解析OB11的message数组（消息链），还原完整消息内容"""
        content_parts = []
        for msg_segment in message_chain:
            seg_type = msg_segment.get("type", "")
            seg_data = msg_segment.get("data", {})

            if seg_type == "text":
                # 文本消息
                content_parts.append(seg_data.get("text", ""))
            elif seg_type == "face":
                # 表情消息（显示表情ID）
                content_parts.append(f"[表情:{seg_data.get('id', '未知')}]")
            elif seg_type == "image":
                # 图片消息（显示图片ID/URL标识）
                img_id = seg_data.get("image_id", seg_data.get("url", "未知图片"))
                content_parts.append(f"[图片:{img_id[:8]}...]")  # 截断ID避免过长
            elif seg_type == "at":
                # @消息
                at_qq = seg_data.get("qq", "未知")
                at_name = seg_data.get("name", "")
                content_parts.append(f"@[{at_name or at_qq}]")
            elif seg_type == "record":
                # 语音消息
                record_id = seg_data.get("file", "未知语音")
                content_parts.append(f"[语音:{record_id[:8]}...]")
            elif seg_type == "file":
                # 文件消息
                file_name = seg_data.get("name", "未知文件")
                file_size = seg_data.get("size", 0)
                content_parts.append(f"[文件:{file_name}({file_size / 1024:.1f}KB)]")
            else:
                # 其他未适配类型（如视频、分享等）
                content_parts.append(f"[{seg_type.upper()}消息]")

        return "".join(content_parts)

    # 优先解析message数组（消息链），raw_message兜底（兼容部分场景）
    message_chain = msg_event.get("message", [])
    if isinstance(message_chain, list) and message_chain:
        raw_message = parse_ob11_message_chain(message_chain)
    else:
        raw_message = msg_event.get("raw_message", "") or "[空消息]"

    # 5. 拼接标准化日志字符串（区分群聊/私聊）
    log_template = "[INFO] 接收到来自qq的消息（必须使用工具进行回复） <- {scene_info} [{sender_info}] {message}"
    formatted_log = log_template.format(
        scene_info=scene_info,
        sender_info=sender_info_str,
        message=raw_message.strip()
    )

    print(formatted_log)
    return formatted_log


# ------------------- 测试示例 -------------------
if __name__ == "__main__":
    wb = websocket.create_connection("ws://192.168.31.100:5788/")
    while True:


        msg = wb.recv()

        print(msg)
        msg = json.loads(msg)
        parse_group_message_to_log(msg)



    


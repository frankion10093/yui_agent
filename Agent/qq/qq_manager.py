import json
import queue

import requests as rq
import websocket
import yaml
import os

from utils import logger


class QQManager:
    """QQ消息构造器"""
    base_private_api = None
    base_group_api = None
    #发送请求的基本路径
    base_url = None
    #监听请求的基本路径
    base_ws_url = None
    #记录不同功能的的path
    base_path = None
    # 请求超时设置
    timeout = None

    msg_queue = queue.Queue(maxsize=1000)

    def __init__(self):
        """需要初始化写死的参数在这里进行初始化"""
        # 读取配置文件
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'napcat_config.yaml')
            with open(path, 'r', encoding='utf-8') as f:
                #初始化加载配置文件
                base: dict = yaml.safe_load(f)['napcat']
                config = base['config']
                api = base['qq_api']
                self.base_url = config['base_url']
                self.base_ws_url = config['base_ws_url']
                self.timeout = config['timeout']

                self.base_private_api = api['base_private_api']
                self.base_group_api = api['base_group_api']
                self.base_path = api['base_path']


        except FileNotFoundError as e:
            logger.error("napcat_config.yaml配置文件不存在", e)
        except Exception as e:
            logger.error("读取配置文件失败", e)

    def start_listen(self):
        """启动监听"""
        wb = websocket.create_connection(self.base_ws_url)
        while True:
            msg = wb.recv()
            msg = json.loads(msg)
            msg = self.parse_group_message_to_log(msg)
            if msg != '':
                self.msg_queue.put(msg)


    def build_message(self, message_type: str, qq_id: str, reply_strategy: str, target_id: str, text: str):
        message_json: dict

        if message_type == 'group':
            message_json = self.base_group_api
            message_json['group_id'] = qq_id
        elif message_type == 'private':
            message_json = self.base_private_api
            message_json['user_id'] = qq_id
        else:
            logger.error("请填写正确的message_type")
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
        elif reply_strategy == 'no':
            message_json['message'] = [text_segment]
        else:
            logger.error("请填写正确的reply_strategy（可选值：at/reply/no）")
            return None
        return message_json


    def send_request(self, notice: str, data: dict) -> str:
        """这个方法用户判断获取的的消息类型，然后调用对应的api发送消息"""
        if notice == '' or data is None:
            return "notice参数为空请重新构建"
        if data is None:
            return "data参数为空请重新构建"
        if self.base_path.get(notice) is None:
            return f"没有{notice}这个方法哦"
        try:
            #发送消息，然后处理后的napcat返回的 message
            response = rq.post(url=self.base_url + self.base_path[notice], json=data, timeout=self.timeout).json()
            return response.get('message', '')
        except Exception as e:
            logger.error("发送消息失败", e)

    def parse_group_message_to_log(self, msg_event: dict) -> str:
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
                    content_parts.append(f"[图片:{img_id}...]")  # 截断ID避免过长
                elif seg_type == "at":
                    # @消息
                    at_qq = seg_data.get("qq", "未知")
                    content_parts.append(f"@[{at_qq}]")
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

        message_id = msg_event.get("message_id", "未知消息id")

        # 5. 拼接标准化日志字符串（区分群聊/私聊）
        log_template = "[INFO] 接收到来自qq的消息 <- {scene_info} [{sender_info}] 消息内容: {message} (消息id:{message_id})"
        formatted_log = log_template.format(
            scene_info=scene_info,
            sender_info=sender_info_str,
            message=raw_message.strip(),
            message_id=message_id
        )

        print(formatted_log)
        return formatted_log


qq_manager = QQManager()

if __name__ == '__main__':
    qq_message = QQManager()
    qq_message.send_request("禁言", {
        "group_id": 533350129,
        "user_id": 2639045525,
        "duration": 10
    })

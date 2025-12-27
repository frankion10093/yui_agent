import os
import yaml
import asyncio
import random
from typing import List, Optional

from pydantic import BaseModel

from utils import logger
from async_task_manager import get_async_task_manager

"""
是否开启主动回复: 回复消息本身概率 三种回复的概率 ： @回复概率率10，消息回复概率10，直接回复概率80
依赖关键词或者被@之后回复概率100
"""


class MessageConfig(BaseModel):
    is_auto_reply: bool
    #自动回复概率
    auto_reply: float
    #1.@回复概率
    at_reply: float
    #2.选中消息回复概率
    message_reply: float
    #3.直接回复概率
    direct_reply: float
    #关键词回复，可是角色名称
    keyword_list: List[str]
    #屏蔽关键词
    block_keywords_list: List[str]


# 获取全局创建的异步管理器实例
_async_task_manager = get_async_task_manager()


class MessageManager:
    #信息管理器配置
    message_config: Optional['MessageConfig'] = None

    #统一存储的容器
    message_queue = asyncio.Queue(maxsize=200)

    row_message_queue = asyncio.Queue(maxsize=200)

    def __init__(self):
        try:
            #初始化消息管理器配置
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config",
                "message_config.yaml"
            )
            with open(path, "r", encoding='utf-8') as f:
                config = yaml.safe_load(f)["message"]["config"]
            self.message_config = MessageConfig(**config)
            logger.info("message信息管理器初始化成功")
        except FileNotFoundError as e:
            logger.error("未找到消息配置文件:message_config.yaml", {e})
        except Exception as e:
            logger.error("初始化配置文件错误:message_config.yaml", {e})

    async def add_message(self, row_message: dict):
        if row_message is None:
            logger.warning("收到空消息")
            return

        #判断是否存在文件或者图片，如果存在需要进行的操作（待实现）
        #---------------------------------------------------------

        #---------------------------------------------------------

        #将消息进行过滤
        not_filter, reply_mode = self.filter(row_message)

        if not_filter:
            #构建ai能看懂的信息
            message = self.parse_qq_message(row_message)
            message += reply_mode
            async with _async_task_manager.lock:
                print(message)
                await self.message_queue.put(message)

    async def get_message(self):
        async with _async_task_manager._lock:
            message = await self.message_queue.get()
        return message

    def filter(self, row_message: dict) -> bool and str:
        if row_message is None or row_message.get("post_type") == "meta_event":
            return False, ''
        if row_message.get("post_type") != "message":
            #不是message说明是群事件，解析后可以通知ai
            return True, ''
        message_type = row_message.get("message_type", "")
        if message_type not in ["group", "private"]:
            #既不是群聊信息又不是私聊信息，也不是群事件，拦截
            return False, ''

        if any(key in row_message.get("raw_message", '') for key in self.message_config.block_keywords_list):
            #接收的信息触发屏蔽词
            return False, ''

        if message_type == "private":
            #如果是私聊的话可以直接回复
            return True, ''

        has_keywords = any(key in row_message.get("raw_message", '') for key in self.message_config.keyword_list)

        #判断是否自动回复
        if not has_keywords:
            if self.message_config.is_auto_reply:
                #随机生成[0.0,1.0)之间的数
                rand_float = random.random()
                #如果没有触发自动回复False
                if rand_float >= self.message_config.auto_reply:
                    return False, ''
                else:
                    print(rand_float, self.message_config.auto_reply)
                    print("触发自动回复")
        else:
            print("触发关键词回复")

        #如果触发了回复
        rand_float = random.random()

        # print(self.message_config.direct_reply)
        # print(self.message_config.direct_reply,self.message_config.direct_reply+self.message_config.at_reply)
        # print(rand_float)
        reply_mode: str = '(这条信息回复方式:'
        if 0.0 <= rand_float < self.message_config.direct_reply:
            reply_mode += "直接回复)"
        elif self.message_config.direct_reply <= rand_float < self.message_config.at_reply + self.message_config.direct_reply:
            reply_mode += "这条信息需要@qq号)"
        else:
            reply_mode += "这条消息需要reply进行回复)"
        print(reply_mode)
        return True, reply_mode

    def parse_qq_message(self, msg_event: dict) -> str:
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
        return formatted_log


_message_manager: Optional['MessageManager'] = None


def get_message_manager() -> MessageManager:
    global _message_manager
    if _message_manager is None:
        _message_manager = MessageManager()
    return _message_manager


if __name__ == "__main__":
    row_message = "yui你好哦"
    keyword_list = ["yui", "Yui", "猫娘"]
    has_keywords = any(key in row_message for key in keyword_list)
    print(has_keywords)

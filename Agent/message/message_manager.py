import os
import queue

import yaml
import asyncio
import random
from typing import List, Optional, Dict

from pydantic import BaseModel
from yaml import YAMLError

from utils import logger


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
    #最大记忆历史消息
    max_list_size: int


class MessageManager:
    #信息管理器配置
    message_config: Optional['MessageConfig'] = None

    #异步存存储qq或者之后直播功能的信息
    __qq_message_queue = asyncio.Queue(maxsize=200)

    #同步存储用于存储本地对话信息
    __local_message_queue = queue.Queue(maxsize=200)

    #历史消息
    # __message_map: Dict[str,List[str]] = {}

    #最大能存储的历史消息数量
    __max_list_size: int = 0

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
            self.__max_list_size = self.message_config.max_list_size
            logger.info("message信息管理器初始化成功")
        except FileNotFoundError as e:
            logger.error("未找到消息配置文件:message_config.yaml", str(e))
        except YAMLError as e:
            logger.error(f"配置文件解析失败（YAML格式错误）: {str(e)}")
        except Exception as e:
            logger.error("初始化配置文件错误:message_config.yaml", str(e))

    async def add_message(self, row_message: dict):
        """
        向异步的消息队列内添加消息
        :param row_message: dict，没有经过解析的信息
        """
        if row_message is None:
            logger.warning("收到空消息")
            return

        #将消息进行过滤
        isfilter = self.filter(row_message)

        if isfilter:
            return

        #判断是否存在文件或者图片，如果存在需要进行的操作（待实现）
        #---------------------------------------------------------



        #---------------------------------------------------------

        #构建ai能看懂的信息
        message: str = await self.parse_qq_message(row_message)

        print(message)

        #将消息放入消息队列
        await self.__qq_message_queue.put(message)

    async def get_message(self):
        message = await self.__qq_message_queue.get()
        return message

    def filter(self, row_message: dict) -> bool:
        """
        过滤器，用于判断输入内容是否合法，是否触发ai回复
        :param row_message: dict，需要传入row_message没有经过处理的信息
        :return: bool，返回bool值判断是否过滤
        """
        if (
                row_message is None or row_message.get("post_type") == "meta_event" or
                row_message.get("post_type") == None or
                row_message.get("post_type") != "message"
        ):
            return True

        if row_message.get('message_type') not in ["group", "private"]:
            #既不是群聊信息又不是私聊信息，也不是群事件，拦截
            return True
        elif row_message.get("message_type") == "private":
            #私聊必回不拦截
            return False

        if any(key in row_message.get("raw_message", '') for key in self.message_config.block_keywords_list):
            #接收的信息触发屏蔽词
            return True

        has_keywords = any(key in row_message.get("raw_message", '') for key in self.message_config.keyword_list)

        #判断是否自动回复,最外层判断是否存在关键词100%回复，如果没有触发关键词就去判断自动回复有没打开，如果打开了就去进行判断是否命中
        if not has_keywords:
            if self.message_config.is_auto_reply:
                #随机生成[0.0,1.0)之间的数
                rand_float = random.random()
                #如果没有触发自动回复True
                if rand_float >= self.message_config.auto_reply:
                    return True
            else:
                return True

        # #如果触发了回复
        # rand_float = random.random()
        #
        # # print(self.message_config.direct_reply)
        # # print(self.message_config.direct_reply,self.message_config.direct_reply+self.message_config.at_reply)
        # # print(rand_float)
        # reply_mode: str = '(回复方式:'
        # if 0.0 <= rand_float < self.message_config.direct_reply:
        #     reply_mode += "direct)"
        # elif self.message_config.direct_reply <= rand_float < self.message_config.at_reply + self.message_config.direct_reply:
        #     reply_mode += "at)"
        # else:
        #     reply_mode += "reply)"
        # print(reply_mode)
        return False

    async def parse_qq_message(self, msg_event: dict) -> str:
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
        async def parse_ob11_message_chain(message_chain: list) -> str:
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
                    from llm import get_agent
                    agent = get_agent()
                    # 图片消息（显示图片ID/URL标识）

                    img = seg_data.get("url", "未知图片")
                    res = await agent.async_vl(img)
                    content_parts.append(f"[表情包:{res}]")
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
            raw_message = await parse_ob11_message_chain(message_chain)
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




    # def add_message_map(self,key: str, value: str):
    #     """
    #     这是用于向ai的记忆列表添加内容
    #     :param message: 消息内容
    #     """
    #     if key not in self.__message_map:
    #         self.__message_map[key] = []
    #
    #     if len(self.__message_map[key]) < self.__max_list_size:
    #         self.__message_map[key].append(value)
    #     else:
    #         self.__message_map[key].pop(0)
    #         self.__message_map[key].append(value)




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

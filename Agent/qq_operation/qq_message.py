from dataclasses import dataclass
import time
import yaml
import os

from utils import logger

# @dataclass
# class Seg:
#     type: str
#     data: dict

class QQMessage:
    """QQ消息构造器"""
    base_private_api = None
    base_group_api = None

    def __init__(self):
        """需要初始化写死的参数在这里进行初始化"""\
        # 读取配置文件
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'napcat_config.yaml')
            with open(path, 'r', encoding='utf-8') as f:
                config: dict = yaml.safe_load(f)['napcat']['qq_api']
                self.base_private_api = config['base_private_api']
                self.base_group_api = config['base_group_api']

        except FileNotFoundError as e:
            logger.error("napcat_config.yaml配置文件不存在",e)
        except Exception as e:
            logger.error("读取配置文件失败",e)


    def build_message(self,organization: str, message_data:list[dict],target_id: str) -> dict | None:
        """构建qq消息准则，传入的值必须是不写死的，需要根据传入的消息类型进行构建，比如群聊才能传入at类型的参数"""

        _api_ = None

        if organization == 'private':
            _api_ = self.base_private_api
            _api_['user_id'] = target_id
        elif organization == 'group':
            _api_ = self.base_group_api
            _api_['group_id'] = target_id
        else:
            logger.error("消息类型错误")
            return None

        _api_['message'] = message_data

        return _api_

if __name__ == '__main__':
    qq_message = QQMessage()
    qq_message.build_message()
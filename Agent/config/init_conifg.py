import os.path
from dataclasses import dataclass

import yaml
import sys
from yaml import YAMLError

from utils import logger


@dataclass
class CoreConfigClass():
    # 是否打开视觉识别
    isOpenVl: bool
    # 是否打开tts
    isOpenTTs: bool

    # 核心模型厂商
    core_llm: str

    # 视觉模型厂商
    vl_llm: str
    # 视觉模型选择
    vl_model: str

    # 语音识别厂商
    tts_llm: str


def get_core_config() -> CoreConfigClass:
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'llm_config.yaml'
    )
    try:
        with open(path, 'r',encoding='utf-8') as f:
            config = yaml.safe_load(f)['llm']['core_config']
            temp = CoreConfigClass(**config)
        return temp
    except FileNotFoundError as e:
        logger.error("未找到消息配置文件:llm_config.yaml", str(e))
        sys.exit(1)
    except YAMLError as e:
        logger.error(f"配置文件解析失败（YAML格式错误）: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error("初始化配置文件错误:llm_config.yaml", str(e))
        sys.exit(1)

core_config = get_core_config()





if __name__ == '__main__':
    core_config = get_core_config()
    print(core_config)

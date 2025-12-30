import yaml
import os
import sys
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from openai import OpenAI
from yaml import YAMLError

from utils import logger

path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'llm_config.yaml')

def build_core_llm(llm_name : str) -> ChatOllama | None:
    """
    构建agent的基础大模型的初始化
    :param str,传入使用大模型
    :return: ChatOllama | None
    """
    try:
        temp:dict
        with open(path, 'r',encoding='utf-8') as f:
            #在这里添加了根据提供商的名字来加载相应的配置文件从而初始化agent的核心模型
            if llm_name == 'ollama':
                temp = yaml.safe_load(f)['llm']['chat'][llm_name]
                return ChatOllama(**temp)
            if llm_name == 'siliconflow':
                temp = yaml.safe_load(f)['llm']['chat'][llm_name]
                return ChatOpenAI(**temp)
        raise("错误配置，请传入正确的大模型厂商姓名")
    except FileNotFoundError as e:
        logger.error("无法找到配置文件llm_config",str(e))
        sys.exit(1)
    except YAMLError as e:
        logger.error(f"配置文件解析失败（YAML格式错误）: {str(e)}")
    except Exception as e:
        logger.error("初始化核心语言大模型失败",str(e))
        sys.exit(1)

def build_vl_llm(llm_name : str):
    """
    用于获取视觉识别大模型
    :param llm_name: str,传入使用大模型
    :return:
    """
    try:

        with open(path, 'r',encoding='utf-8') as f:
            config = yaml.safe_load(f)
        #这里并没有提供本地功能，直接使用通用的openai接口
        if "llm" not in config:
            logger.error("配置文件缺少'llm'节点")
            return None
        if "vl" not in config["llm"]:
            logger.error("配置文件'llm'节点下缺少'vl'子节点")
            return None
        if llm_name not in config["llm"]["vl"]:
            logger.error(f"配置文件中未找到视觉模型'{llm_name}'的配置")
            return None
        if "model" not in config["llm"]["vl"][llm_name]:
            logger.error(f"配置文件中未找到视觉模型'model'的配置")

        config = config["llm"]["vl"][llm_name]
        return OpenAI(base_url=config['base_url'],api_key=config['api_key']), config['model']

    except FileNotFoundError as e:
        logger.error("无法找到配置文件llm_config",str(e))
        return None
    except YAMLError as e:
        logger.error(f"配置文件解析失败（YAML格式错误）: {str(e)}")
    except Exception as e:
        logger.error("初始化视觉语言大模型失败",str(e))
        return None





# def build_siliconflow() -> ChatOpenAI | None:
#     """
#     构建agent的基础大模型的初始化，硅基流动 siliconflow
#     :return: ChatOllama | None
#     """
#     path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'llm_config.yaml')
#     try:
#         with open(path, 'r',encoding='utf-8') as f:
#             temp = yaml.safe_load(f)['llm']['siliconflow']
#         llm = ChatOpenAI(**temp)
#         return llm
#     except FileNotFoundError as e:
#         logger.error("无法找到配置文件llm_config", {e})
#         sys.exit(1)
#     except Exception as e:
#         logger.error("初始化语言大模型失败", {e})
#         sys.exit(1)


if __name__ == '__main__':
    build_vl_llm("siliconflow")

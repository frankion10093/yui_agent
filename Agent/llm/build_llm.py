import yaml
import os
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from utils import logger

def build_ollama() -> ChatOllama | None:
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'llm_config.yaml')
    try:
        with open(path, 'r',encoding='utf-8') as f:
            temp = yaml.safe_load(f)['llm']['ollama']
        llm = ChatOllama(**temp)
        return llm
    except FileNotFoundError as e:
        print("未找到 ollama 配置文件")
        logger.error(e)
        return None
    except Exception as e:
        logger.error(e)
        return None

def build_siliconflow() -> ChatOpenAI | None:
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'llm_config.yaml')
    try:
        with open(path, 'r',encoding='utf-8') as f:
            temp = yaml.safe_load(f)['llm']['siliconflow']
        llm = ChatOpenAI(**temp)
        return llm
    except FileNotFoundError as e:
        logger.error(e)
        return None
    except Exception as e:
        logger.error(e)
        return None


if __name__ == '__main__':
    build_siliconflow()

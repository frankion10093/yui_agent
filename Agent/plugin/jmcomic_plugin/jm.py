import jmcomic
import os
from utils import logger


def get_jmcomic(seed: str):
    try:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jm_option.yml')
        option = jmcomic.create_option_by_file(path)
        logger.info("开始下载本子")
        jmcomic.download_album(seed, option)
        return "下载本子成功"
    except Exception as e:
        print(e)
        return "下载本子失败"


if __name__ == '__main__':
    get_jmcomic("123")

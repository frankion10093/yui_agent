import jmcomic
import os
import base64
import json
from utils import logger
import requests as rq
from requests.exceptions import RequestException, Timeout


def get_jmcomic(seed: str, message_type: str, target_id: str) -> str:
    """
    下载JMComic本子并通过Base64/DataUrl格式发送到QQ（私聊/群聊）
    :param seed: 本子编号（seed）
    :param message_type: 消息类型，仅支持 'private'（私聊）/ 'group'（群聊）
    :param target_id: 目标ID，私聊=QQ号，群聊=群号
    :return: 执行结果描述
    """
    if message_type not in ['private', 'group']:
        err_msg = f"消息类型错误，仅支持 'private'/'group'，当前传入：{message_type}"
        logger.error(err_msg)
        print(err_msg)
        return "下载失败：参数错误"

    # napcat API基础配置
    napcat_base_url = "http://192.168.31.100:3000"
    # 按消息类型拼接API路径 + 确定目标参数名（严格对齐文档格式）
    if message_type == 'group':
        api_path = "/send_group_msg"
        target_key = "group_id"  # 群消息必须用group_id（文档规范）
    else:
        api_path = "/send_private_msg"
        target_key = "user_id"  # 私聊用user_id（文档规范）
    full_api_url = f"{napcat_base_url}{api_path}"

    try:
        jm_option_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jm_option.yml')
        # 检查配置文件是否存在
        if not os.path.exists(jm_option_path):
            err_msg = f"JMComic配置文件不存在：{jm_option_path}"
            logger.error(err_msg)
            return f"下载失败：{err_msg}"

        option = jmcomic.create_option_by_file(jm_option_path)

        jmcomic.download_album(seed, option)


        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        pdf_file_path = os.path.join(project_root, 'output', 'pdf', f'{seed}.pdf')


        if not os.path.exists(pdf_file_path):
            err_msg = f"本子下载后PDF文件不存在：{pdf_file_path}"
            logger.error(err_msg)
            return f"下载失败：{err_msg}"


        with open(pdf_file_path, 'rb') as f:
            pdf_binary = f.read()


        pdf_base64 = base64.b64encode(pdf_binary).decode('utf-8')
        pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"

        send_data = {
            target_key: target_id,
            "message": [
                {
                    "type": "file",
                    "data": {
                        "file": pdf_data_url,
                        "name": f"{seed}.pdf"
                    }
                }
            ]
        }


        headers = {"Content-Type": "application/json"}
        res = rq.post(
            url=full_api_url,
            json=send_data,
            headers=headers,
            timeout=90
        )
        return res.text
    except FileNotFoundError as e:
        err_msg = f"文件操作失败：{str(e)}"
        logger.error(err_msg, exc_info=True)
        return err_msg
    except Timeout:
        err_msg = f"发送请求到Napcat超时（60秒），请检查网络或文件大小"
        logger.error(err_msg, exc_info=True)
        return err_msg
    except RequestException as e:
        err_msg = f"网络请求失败：{str(e)}"
        logger.error(err_msg, exc_info=True)
        return err_msg
    except Exception as e:
        err_msg = f"未知错误导致下载/发送失败：{str(e)}"
        logger.error(err_msg, exc_info=True)
        return err_msg


if __name__ == '__main__':
    # 测试调用：私聊发送 seed=123 到 QQ=2030236097
    result = get_jmcomic("350234", "private", "2030236097")
    print(f"最终执行结果：{result}")
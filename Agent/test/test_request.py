import os
import time
from io import BytesIO

import requests as req
import base64
from PIL import Image
from openai import OpenAI

# response = req.post("http://192.168.31.100:3000/send_group_msg",
#                     json=
# {
#     "user_id": "2030236097",
#     "message": [
#         {
#             "type": "music",
#             "data": {
#                 "type": "qq",
#                 "id": 11
#             }
#         }
#     ]
# }
#                     )
#
# print(response.text)

# import requests
#
# # 图片URL

def get_image() -> str:

    # response = req.get(url)
    #
    # # 检查请求是否成功（状态码200表示成功）
    # if response.status_code == 200:
    #     # 图片保存路径（根据实际图片格式修改扩展名，如.png、.jpg）
    #     save_path = "image.jpeg"
    #
    #     # 以二进制写入模式打开文件，写入图片数据
    #     with open(save_path, "wb") as f:
    #         f.write(response.content)  # content属性直接二进制内容
    #
    #     print(f"图片已保存至：{save_path}")
    # else:
    #     print(f"请求失败，状态码：{response.status_code}")
    file_path = "image/c.png"

    buffer = BytesIO()
    with Image.open(file_path) as f:
        img = f.resize((160,160))
        # img_format = img.format

        img.save(buffer, format="PNG")
    buffer.seek(0)
    buffer_str = base64.b64encode(buffer.read()).decode('utf-8')

    client = OpenAI(api_key="sk-apiakdsksjonkqeeilvubghnsqholuwhvdpfpccesjrirprd",
                    base_url="https://api.siliconflow.cn/v1")
    start = time.time()

    response = client.chat.completions.create(
        # model='Pro/deepseek-ai/DeepSeek-R1',
        model="Qwen/Qwen3-VL-32B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:application/pdf;base64,"+ buffer_str,
                            "detail": "low"
                        }
                    },
                    {
                        "type": "text",
                        "text": "非常简短描述图片"
                    }
                ]
            }
        ],
    )

    print(time.time() - start)
    print(response.choices[0].message.content)
    return response.choices[0].message.content

if __name__ == '__main__':
    get_image()

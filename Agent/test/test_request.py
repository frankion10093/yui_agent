import requests as req

response = req.post("http://192.168.31.100:3000/send_group_msg",
                    json=
                    {'group_id': '1035300253',
                     'message': [{'type': 'text', 'data': {'text': '喵~ 已经对用户2790817365执行了30秒禁言操作啦！'}}]}
                    )

print(response.text)

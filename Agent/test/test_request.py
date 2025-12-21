import requests as req

response = req.post("http://192.168.31.100:3000/set_group_ban",
                    json=
                    {
                        "group_id": 533350129,
                        "user_id": 2639045525,
                        "duration": 10
                    }
                    )

print(response.text)

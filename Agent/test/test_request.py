import requests as req

response = req.post("http://192.168.31.100:3000/send_group_msg",
                    json=
{
    "user_id": "2030236097",
    "message": [
        {
            "type": "music",
            "data": {
                "type": "qq",
                "id": 11
            }
        }
    ]
}
                    )

print(response.text)

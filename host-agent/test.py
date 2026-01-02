import uuid
import requests

url = "http://localhost:10022/"

payload = {
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",  # ✅ required method name
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),  # ✅ required
            "role": "user",                  # ✅ required
            "parts": [
                {
                    "text": "Analyze the AI adoption trend"
                }
            ]
        }
    }
}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())

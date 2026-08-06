import os
import requests
from dotenv import load_dotenv

load_dotenv()

DEVICE_ID = os.getenv("device-id")
API_KEY = os.getenv("api-key")

def send_sms(to: str, body: str) -> dict:
    resp = requests.post(
        f"https://api.textbee.dev/api/v1/gateway/devices/{DEVICE_ID}/send-sms",
        json={"recipients": [to], "message": body},
        headers={"x-api-key": API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    result = send_sms("8618011899", "Hello from Python")
    print(result)

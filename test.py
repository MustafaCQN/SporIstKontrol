import os
import sys
from playsound import playsound
import requests
from dotenv import load_dotenv

load_dotenv()
USERNAME = os.getenv("SPOR_USERNAME")
PASSWORD = os.getenv("SPOR_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print(f"tüm değişkenler: {USERNAME}, {PASSWORD}, {TELEGRAM_TOKEN}, {TELEGRAM_CHAT_ID}")


def send_telegram_message(message):
    """Telegram üzerinden mesaj gönder."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            print(f"❗ Telegram hata: {response.status_code} - {response.text}")
        else:
            print("📨 Telegram mesajı başarıyla gönderildi.")
    except Exception as e:
        print(f"Telegram mesajı gönderilemedi: {e}")

import winsound
winsound.Beep(1200, 500) 
winsound.Beep(1200, 500) 
winsound.Beep(1200, 500) 
send_telegram_message("🎉 Spor.istanbul sitesinde kontenjan açıldı! Hemen kontrol et!")


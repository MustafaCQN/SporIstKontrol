import os
import time
import requests
import threading
import keyboard
# from playsound import playsound
import winsound
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from datetime import datetime

# .env dosyasını yükle
load_dotenv()
USERNAME = os.getenv("SPOR_USERNAME")
PASSWORD = os.getenv("SPOR_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Global durdurma bayrağı
stop_flag = False

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

def login_and_check():
    """Siteye giriş yap, kontenjan kontrolü yap."""
    start_time = datetime.now()
    print(f"\n🕐 Kontrol başladı: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get("https://online.spor.istanbul/uyegiris")
        time.sleep(3)

        driver.find_element(By.ID, "txtTCPasaport").send_keys(USERNAME)
        driver.find_element(By.ID, "txtSifre").send_keys(PASSWORD)
        driver.find_element(By.ID, "btnGirisYap").click()
        time.sleep(3)
        
        driver.get("https://online.spor.istanbul/uyespor")
        time.sleep(3)

        driver.find_element(By.ID, "pageContent_rptListe_lbtnSeansSecim_1").click()
        time.sleep(3)

        driver.execute_script("""
            const sel = document.querySelectorAll("select")[0];
            sel.value = Array.from(sel.options).find(o => o.text.includes("TENİS")).value;
            sel.dispatchEvent(new Event("change"));
        """)

        spans = driver.find_elements(By.CSS_SELECTOR, 'span[title="Kalan Kontenjan"]')
        kontenjanlar = [int(span.text.strip()) for span in spans if span.text.strip().isdigit()]
        print(f"📊 Bulunan kontenjanlar: {kontenjanlar}")

        if any(k > 0 for k in kontenjanlar):
            print("✅ Kontenjan bulundu!")
            # playsound("ding.mp3")
            winsound.Beep(1200, 500)
            winsound.Beep(1200, 500)
            winsound.Beep(1200, 500)
            send_telegram_message("🎉 Spor.istanbul sitesinde kontenjan açıldı! Hemen kontrol et!")
        else:
            print("❌ Kontenjan yok.")
    except Exception as e:
        print(f"❗ Hata oluştu: {e}")
    finally:
        driver.quit()
        end_time = datetime.now()
        print(f"🏁 Kontrol bitti: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Süre: {(end_time - start_time).seconds} saniye")

def key_listener():
    """F tuşuna basıldığında durdurma işlemini tetikle."""
    global stop_flag
    print("🕹️ Programı durdurmak için 'F' tuşuna bas.")
    keyboard.wait('f')
    stop_flag = True
    print("\n🟥 Durdurma sinyali alındı, kontrol döngüsü sonlandırılacak...")

def main():
    listener_thread = threading.Thread(target=key_listener, daemon=True)
    listener_thread.start()

    while not stop_flag:
        login_and_check()
        for _ in range(180):  # 10 dakika = 600 saniye
            if stop_flag:
                break
            time.sleep(1)

    print("✅ Program güvenli şekilde sonlandırıldı.")

if __name__ == "__main__":
    main()

import os
import time
import threading
import keyboard
import msvcrt  # Windows terminal klavye dinleme
import requests
from playsound import playsound
import winsound
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from datetime import datetime

# === .env dosyasını yükle ===
load_dotenv()
USERNAME = os.getenv("SPOR_USERNAME")
PASSWORD = os.getenv("SPOR_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

stop_flag = False
LOG_FILE = "kontrol_log.txt"

# === Yardımcı fonksiyonlar ===
def log_yaz(mesaj):
    zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tam_mesaj = f"[{zaman}] {mesaj}"
    print(tam_mesaj)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(tam_mesaj + "\n")


def send_telegram_message(message):
    """Telegram mesaj gönderimi."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            log_yaz(f"❗ Telegram hata: {response.status_code} - {response.text}")
        else:
            log_yaz("📨 Telegram mesajı gönderildi.")
    except Exception as e:
        log_yaz(f"Telegram gönderim hatası: {e}")


def tenis_bransi_sec(driver): # sadece akşam saatleri olan seans için
    """TENİS seçimini JavaScript ile yapar."""
    js_code = """
        const sel = document.querySelectorAll("select")[0];
        sel.value = Array.from(sel.options).find(o => o.text.includes("TENİS")).value;
        sel.dispatchEvent(new Event("change"));
    """
    driver.execute_script(js_code)
    log_yaz("🎾 'TENİS' branşı seçildi.")
    # ASP.NET postback tamamlanmasını bekle
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//span[@title='Kalan Kontenjan']"))
    )

def old_kort_taramasi(driver):
    # çok uzun ve karmaşık olduğu için JavaScript ile tek seferde veri çekmeye karar verdim, bu fonksiyon artık kullanılmıyor.
    # Günler
    gunler = driver.find_elements(By.CSS_SELECTOR, "div.panel.panel-info")

    for gun in gunler:
        gun_title = gun.find_element(By.CSS_SELECTOR, "h3.panel-title").text.strip()
        seanslar = gun.find_elements(By.CSS_SELECTOR, "div.well")
        if len(seanslar) < 1:
            log_yaz(f"⚠️ {gun_title} günü için seans bulunamadı.")
            continue
        log_yaz(f"🔍 {gun_title} günü için {len(seanslar)} seans bulundu.")
        aktif_seanslar = []
        for seans in seanslar:
            try:
                seviye = seans.find_element(By.XPATH, ".//span[@title='Seans Seviyesi']").text.strip()
                salon = seans.find_element(By.XPATH, ".//label[@title='Salon Adı']").text.strip()
                saat = seans.find_element(By.XPATH, ".//span[contains(@id,'lblSeansSaat_')]").text.strip()
                kontenjan = int(seans.find_element(By.XPATH, ".//span[@title='Kalan Kontenjan']").text.strip())

                aktif_seanslar.append({
                    "gun": gun_title,
                    "seviye": seviye,
                    "salon": salon,
                    "saat": saat,
                    "kontenjan": kontenjan
                })
                return aktif_seanslar
            except Exception:
                continue

def kort_taramasi(driver):
    js_code = r"""
        const gunler = document.querySelectorAll('div.panel.panel-info');
        return Array.from(gunler).map(gun => ({
            gun_title: gun.querySelector('h3.panel-title')?.textContent.trim().replace(/\s+/g, ' '),
            seanslar: Array.from(gun.querySelectorAll('div.well')).map(seans => ({
                seviye: seans.querySelector("span[title='Seans Seviyesi']")?.textContent.trim(),
                salon: seans.querySelector("label[title='Salon Adı']")?.textContent.trim(),
                saat: seans.querySelector("span[id*='lblSeansSaat_']")?.textContent.trim(),
                kontenjan: parseInt(seans.querySelector("span[title='Kalan Kontenjan']")?.textContent.trim() || '0')
            }))
        }));
    """
    gunler_veri = driver.execute_script(js_code)

    aktif_seanslar = []
    for gun_data in gunler_veri:
        for seans in gun_data['seanslar']:
            aktif_seanslar.append({**seans, "gun": gun_data['gun_title']})
    return aktif_seanslar

def login_and_check():
    """Giriş yap, seansları kontrol et, uygun seans varsa bildir."""
    start_time = datetime.now()
    log_yaz("🕐 Kontrol başladı.")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")          # yeni headless
    options.add_argument("--window-size=1920,1080") # masaüstü boyutu gibi
    options.add_argument("--disable-gpu")          # alışkanlık, bazı ortamlarda faydalı
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Chrome'un sayfa yükleme ve script zaman aşımı limitlerini ayarla
    driver.set_page_load_timeout(60)   # 60 sn içinde sayfa yüklenmezse hata
    driver.set_script_timeout(60)      # JS işlemleri için 60 sn
    driver.implicitly_wait(10)         # element bekleme süresi

    try:
        # Giriş sayfasına git
        driver.get("https://online.spor.istanbul/uyegiris")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtTCPasaport")))

        driver.find_element(By.ID, "txtTCPasaport").send_keys(USERNAME)
        driver.find_element(By.ID, "txtSifre").send_keys(PASSWORD)
        driver.find_element(By.ID, "btnGirisYap").click()
        log_yaz("✅ Giriş yapıldı.")

        WebDriverWait(driver, 20).until(EC.url_contains("anasayfa"))

        driver.get("https://online.spor.istanbul/uyespor")
        time.sleep(3)

        driver.find_element(By.ID, "pageContent_rptListe_lbtnSeansSecim_1").click()
        time.sleep(3)

        # TENİS branşını seç
        # tenis_bransi_sec(driver)
        # time.sleep(2)

        aktif_seanslar = kort_taramasi(driver)

        log_yaz(f"📊 {len(aktif_seanslar)} seans bulundu.")

        # 🎯 İstediğin saatler
        istenen_saatler = {
            "12:00 - 13:00"
        }

        istenen_kortlar = {
            "KAPALI TENİS KORTU 3",
            "KAPALI TENİS KORTU 4"
        }

        uygun_seanslar = [
            s for s in aktif_seanslar
            if s["kontenjan"] > 0 and s["saat"] in istenen_saatler and s["salon"] in istenen_kortlar
        ]

        if uygun_seanslar:
            log_yaz("✅ Uygun saatlerde kontenjan bulundu!")
            winsound.Beep(1200, 500)
            winsound.Beep(1200, 500)
            winsound.Beep(1200, 500)
            mesaj = "🎾 Aşağıdaki seanslarda kontenjan var:\n\n"
            for s in uygun_seanslar:
                mesaj += f"{s['gun']} - {s['seviye']} | {s['salon']} | {s['saat']} | {s['kontenjan']} kişi\n"
            send_telegram_message(mesaj)
        else:
            log_yaz("❌ Uygun saatlerde kontenjan bulunamadı.")

    except Exception as e:
        log_yaz(f"❗ Hata: {e}")
    finally:
        driver.quit()
        end_time = datetime.now()
        log_yaz(f"🏁 Kontrol bitti. Süre: {(end_time - start_time).seconds} sn\n")


def key_listener():
    # """F tuşuna basıldığında programı durdur."""
    # global stop_flag
    # log_yaz("🕹️ Durdurmak için 'F' tuşuna bas.")
    # keyboard.wait("f")
    # stop_flag = True
    # log_yaz("🟥 Durdurma sinyali alındı.")
    """Yalnızca terminal penceresinde F tuşuna basıldığında durdur."""
    global stop_flag
    log_yaz("🕹️ Terminal penceresinde 'F' tuşuna basarak programı durdurabilirsin.")
    while not stop_flag:
        if msvcrt.kbhit():  # bir tuş basıldı mı?
            key = msvcrt.getch().decode('utf-8').lower()
            if key == 'f':
                stop_flag = True
                log_yaz("🟥 Durdurma sinyali alındı (terminalden).")
        time.sleep(0.2)

def main():
    listener_thread = threading.Thread(target=key_listener, daemon=True)
    listener_thread.start()

    while not stop_flag:
        login_and_check()
        for _ in range(180):  # 10 dakika = 600 sn
            if stop_flag:
                break
            time.sleep(1)

    log_yaz("✅ Program güvenli şekilde sonlandırıldı.")


if __name__ == "__main__":
    main()

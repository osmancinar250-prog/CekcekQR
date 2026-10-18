import time
import requests
from supabase import create_client

SUPABASE_URL = "SENIN_SUPABASE_URL"
SUPABASE_KEY = "SENIN_SUPABASE_KEY"
TELEGRAM_BOT_TOKEN = "SENIN_TELEGRAM_BOT_TOKEN"
APP_BASE_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})

def check_updates():
    offset = 0
    print("🤖 Bot dinlemede...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            res = requests.get(url, timeout=35).json()
            
            for result in res.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "").strip()

                if text.startswith("/start"):
                    send_message(chat_id, "👋 Hoş Geldiniz!\nKayıt için:\n`/kayit 34ABC123 05XXXXXXXXX`")

                elif text.startswith("/kayit"):
                    parts = text.split()
                    if len(parts) >= 3:
                        plate = parts[1].upper().replace(" ", "")
                        phone = parts[2].strip()
                        
                        data = {
                            "plate": plate,
                            "phone": phone,
                            "telegram_chat_id": str(chat_id)
                        }
                        res_db = supabase.table("vehicles").insert(data).execute()
                        if res_db.data:
                            v_id = res_db.data[0]["id"]
                            qr_link = f"{APP_BASE_URL}/?v={v_id}"
                            send_message(chat_id, f"✅ Kayıt Başarılı!\nPlaka: {plate}\n[QR Kod Bağlantınız]({qr_link})")
                        else:
                            send_message(chat_id, "❌ Kayıt yapılamadı.")
                    else:
                        send_message(chat_id, "⚠️ Hatalı format! Örnek:\n`/kayit 34ABC123 05XXXXXXXXX`")
        except Exception as e:
            print("Hata:", e)
            time.sleep(3)

if __name__ == "__main__":
    check_updates()

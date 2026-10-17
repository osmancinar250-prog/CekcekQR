import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Telegram Park Bildirimi", page_icon="🚗", layout="centered")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")

APP_BASE_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app"

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

supabase = init_supabase()

def send_telegram_message(chat_id, text):
    """Telegram API üzerinden kilit ekranı bildirimi gönderir."""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# ARAYÜZ BAŞLIĞI
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Telegram Entegrasyonlu Anlık Park İletişim Sistemi")

query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)

# ---------------------------------------------------------
# SENARYO A: QR KOD OKUTULDU (Bildiren Kişi)
# ---------------------------------------------------------
if qr_vehicle_id:
    st.subheader("📢 Araç Sahibine Bildirim Gönder")
    
    vehicle = None
    if supabase:
        try:
            res = supabase.table("vehicles").select("*").eq("id", qr_vehicle_id).execute()
            vehicle = res.data[0] if res.data else None
        except Exception as e:
            st.error(f"Veri çekme hatası: {e}")

    if vehicle:
        st.success(f"✅ Araç Doğrulandı: **{vehicle['plate']}**")
        
        sender_phone = st.text_input("Telefon Numaranız (Yasal doğrulama için saklanır, karşı tarafa gösterilmez):", placeholder="05XXXXXXXXX")
        
        preset_messages = [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ]
        selected_msg = st.radio("Durum seçiniz:", preset_messages)

        if st.button("🚨 Bildirimi Gönder"):
            if sender_phone.strip():
                try:
                    # 1. Veritabanına Kaydet
                    notif_data = {
                        "vehicle_id": qr_vehicle_id,
                        "incoming_preset": selected_msg,
                        "sender_phone": sender_phone.strip(),
                        "status": "BEKLIYOR",
                        "created_at": datetime.datetime.now().isoformat()
                    }
                    supabase.table("notifications").insert(notif_data).execute()
                    
                    # 2. Telegram Üzerinden Araç Sahibine Anında Kilit Ekranı Bildirimi Gönder
                    telegram_chat_id = vehicle.get("telegram_chat_id")
                    if telegram_chat_id:
                        msg_text = (
                            f"🚨 **CekCekQR BİLDİRİMİ!**\n\n"
                            f"🚗 **Plaka:** {vehicle['plate']}\n"
                            f"💬 **Mesaj:** {selected_msg}\n\n"
                            f"📱 *Bildirim kilit ekranınıza ulaştırıldı.*"
                        )
                        send_telegram_message(telegram_chat_id, msg_text)
                    
                    st.success("✅ Bildirim araç sahibinin Telegram'ına kilit ekranı uyarısı olarak gönderildi!")
                except Exception as e:
                    st.error(f"Bildirim hatası: {e}")
            else:
                st.warning("Lütfen telefon numaranızı giriniz.")

    else:
        st.error("Geçersiz veya veritabanında bulunmayan QR Kod.")

# ---------------------------------------------------------
# SENARYO B: ARAÇ SAHİBİ PANELİ (Kayıt & QR Üretme)
# ---------------------------------------------------------
else:
    st.subheader("📝 Araç Kaydı & QR Kod Oluştur")
    
    plate = st.text_input("Plakanız:", placeholder="34ABC123").upper().replace(" ", "")
    phone = st.text_input("Telefon Numaranız (Yasal Doğrulama):", placeholder="05XXXXXXXXX")
    
    st.markdown("---")
    st.markdown("### 📲 Kilit Ekranı Bildirimi İçin Telegram Eşleşmesi")
    st.info("Kilit ekranında bildirim alabilmek için Telegram Botumuza tıkla, `/start` de ve sana verilen Chat ID numarasını aşağıya yapıştır.")
    
    chat_id_input = st.text_input("Telegram Chat ID (Örn: 123456789):")

    if st.button("QR Kod Oluştur"):
        if plate and phone and chat_id_input:
            if supabase:
                try:
                    v_data = {
                        "plate": plate, 
                        "phone": phone.strip(),
                        "telegram_chat_id": chat_id_input.strip()
                    }
                    res = supabase.table("vehicles").insert(v_data).execute()
                    
                    if res.data:
                        new_id = res.data[0]["id"]
                        app_url = f"{APP_BASE_URL}/?v={new_id}"
                        
                        qr = qrcode.make(app_url)
                        buf = BytesIO()
                        qr.save(buf)
                        
                        st.success(f"✅ {plate} plakalı araç başarıyla kaydedildi!")
                        st.image(buf.getvalue(), caption=f"{plate} QR Kodu", width=250)
                        st.download_button("QR Kodu İndir", buf.getvalue(), file_name=f"{plate}_QR.png", mime="image/png")
                except Exception as e:
                    st.error(f"Kayıt Hatası (Supabase'e 'telegram_chat_id' sütununu eklediğinizden emin olun): {e}")
        else:
            st.warning("Lütfen plaka, telefon ve Telegram Chat ID alanlarının tamamını doldurunuz.")

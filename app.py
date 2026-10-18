import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime
import time
import json

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Canlı Park İletişimi", page_icon="🚗", layout="centered")

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
    """Telegram API üzerinden mesaj gönderir."""
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
# URL PARAMETRELERİ & TELEGRAM WEBHOOK DİNLEYİCİSİ
# ---------------------------------------------------------
query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)
reply_notif_id = query_params.get("reply", None)
reply_action = query_params.get("action", None)
is_webhook = query_params.get("webhook", None)

# TELEGRAM BOTUNDAN GELEN /kayit KOMUTLARINI OTOMATİK YAKALAMA
if is_webhook:
    try:
        # Telegram'dan gelen POST verisini oku
        raw_body = st.context.request.body.decode("utf-8")
        data = json.loads(raw_body)
        
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        if text.startswith("/start"):
            welcome_msg = (
                "👋 *CekCekQR'a Hoş Geldiniz!*\n\n"
                "Aracınızı kaydetmek için plaka ve telefon numaranızı şu formatta gönderin:\n\n"
                "`/kayit 34ABC123 05XXXXXXXXX`"
            )
            send_telegram_message(chat_id, welcome_msg)

        elif text.startswith("/kayit"):
            parts = text.split()
            if len(parts) >= 3:
                plate = parts[1].upper().replace(" ", "")
                phone = parts[2].strip()
                
                # Supabase'e Kaydet
                if supabase:
                    v_data = {
                        "plate": plate,
                        "phone": phone,
                        "telegram_chat_id": str(chat_id)
                    }
                    res = supabase.table("vehicles").insert(v_data).execute()
                    if res.data:
                        v_id = res.data[0]["id"]
                        qr_link = f"{APP_BASE_URL}/?v={v_id}"
                        send_telegram_message(
                            chat_id, 
                            f"✅ *Kayıt Başarılı!*\n\n"
                            f"🚗 *Plaka:* {plate}\n"
                            f"📱 *Telefon:* {phone}\n\n"
                            f"🔗 *QR Kod Bağlantınız:*\n{qr_link}"
                        )
                    else:
                        send_telegram_message(chat_id, "❌ Kayıt yapılırken bir hata oluştu.")
            else:
                send_telegram_message(chat_id, "⚠️ *Eksik bilgi!* Lütfen şu formatta yazın:\n`/kayit 34ABC123 05XXXXXXXXX`")
    except Exception:
        pass
    st.stop()

# ---------------------------------------------------------
# SENARYO C: ARAÇ SAHİBİ YANIT LİNKİNE TIKLADIYSA
# ---------------------------------------------------------
if reply_notif_id and reply_action:
    st.title("🚗 CekCekQR - Yanıt Onayı")
    if supabase:
        try:
            supabase.table("notifications").update({"status": reply_action}).eq("id", reply_notif_id).execute()
            if "Gelemiyorum" in reply_action:
                st.warning(f"⚠️ Yanıtınız iletildi: **{reply_action}**")
            else:
                st.success(f"✅ Yanıtınız başarıyla kaydedildi: **{reply_action}**")
            st.info("Bu pencereyi kapatabilirsiniz. Vatandaş bilgilendirildi.")
        except Exception as e:
            st.error(f"Güncelleme hatası: {e}")
    st.stop()

# ---------------------------------------------------------
# ARAYÜZ BAŞLIĞI
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Çift Yönlü Anlık Park İletişim Sistemi")

# ---------------------------------------------------------
# SENARYO A: QR KOD OKUTULDU (Bildiren Kişi + Canlı Takip)
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
        
        if "active_notif_id" not in st.session_state:
            st.session_state.active_notif_id = None

        if not st.session_state.active_notif_id:
            sender_phone = st.text_input("Telefon Numaranız (Yasal doğrulama için):", placeholder="05XXXXXXXXX")
            
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
                        notif_data = {
                            "vehicle_id": qr_vehicle_id,
                            "incoming_preset": selected_msg,
                            "sender_phone": sender_phone.strip(),
                            "status": "BEKLIYOR",
                            "created_at": datetime.datetime.now().isoformat()
                        }
                        insert_res = supabase.table("notifications").insert(notif_data).execute()
                        
                        if insert_res.data:
                            new_notif_id = insert_res.data[0]["id"]
                            st.session_state.active_notif_id = new_notif_id
                            
                            telegram_chat_id = vehicle.get("telegram_chat_id")
                            if telegram_chat_id:
                                link_geliyorum = f"{APP_BASE_URL}/?reply={new_notif_id}&action=🏃%20Geliyorum+(2+dk)"
                                link_cekiyorum = f"{APP_BASE_URL}/?reply={new_notif_id}&action=🚗%20Aracı%20Çekiyorum"
                                link_gelemiyorum = f"{APP_BASE_URL}/?reply={new_notif_id}&action=❌%20Gelemiyorum%20/%20Müsait%20Değilim"

                                msg_text = (
                                    f"🚨 *CekCekQR BİLDİRİMİ!*\n\n"
                                    f"🚗 *Plaka:* {vehicle['plate']}\n"
                                    f"💬 *Mesaj:* {selected_msg}\n\n"
                                    f"👇 *Durumunuzu bildirmek için tıklayın:*\n"
                                    f"[🏃 Geliyorum (2 dk)]({link_geliyorum})\n"
                                    f"[🚗 Aracı Çekiyorum]({link_cekiyorum})\n"
                                    f"[❌ Gelemiyorum / Müsait Değilim]({link_gelemiyorum})"
                                )
                                send_telegram_message(telegram_chat_id, msg_text)
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"Bildirim hatası: {e}")
                else:
                    st.warning("Lütfen telefon numaranızı giriniz.")
        
        else:
            # CANLI TAKİP EKRANI
            st.info("📡 Bildirim araç sahibine iletildi. Yanıtı bekleniyor...")
            status_placeholder = st.empty()
            
            for _ in range(60):
                try:
                    check_res = supabase.table("notifications").select("status").eq("id", st.session_state.active_notif_id).execute()
                    if check_res.data:
                        current_status = check_res.data[0]["status"]
                        if current_status != "BEKLIYOR":
                            if "Gelemiyorum" in current_status:
                                status_placeholder.error(f"❌ **Araç Sahibinin Yanıtı:** {current_status}")
                            else:
                                status_placeholder.success(f"✅ **Araç Sahibinin Yanıtı:** {current_status}")
                                
                            if st.button("Yeni Bildirim Gönder / Başa Dön"):
                                st.session_state.active_notif_id = None
                                st.rerun()
                            st.stop()
                except Exception:
                    pass
                
                time.sleep(3)
            
            st.warning("⏰ Araç sahibinden henüz yanıt alınamadı.")
            if st.button("Tekrar Dene / Başa Dön"):
                st.session_state.active_notif_id = None
                st.rerun()

    else:
        st.error("Geçersiz veya veritabanında bulunmayan QR Kod.")

# ---------------------------------------------------------
# SENARYO B: MANUEL KAYIT (YEDEK)
# ---------------------------------------------------------
else:
    st.subheader("📲 Kolay Kayıt Yöntemi (Telegram)")
    st.info("Sayısal ID kopyalamanıza gerek kalmadan kayıt olmak için Telegram botumuza gidin:\n\n**@cekcekqr_bot** hesabına şu mesajı atın:\n`/kayit 34ABC123 05XXXXXXXXX`")

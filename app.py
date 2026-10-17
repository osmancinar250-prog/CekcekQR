import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime
import time

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Canlı Park İletişimi", page_icon="🚗", layout="centered")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "")

# Kendi Streamlit uygulama adresiniz
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
# URL PARAMETRELERİ KONTROLÜ
# ---------------------------------------------------------
query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)
reply_notif_id = query_params.get("reply", None)
reply_action = query_params.get("action", None)

# ---------------------------------------------------------
# SENARYO C: ARAÇ SAHİBİ YANIT LİNKİNE TIKLADIYSA
# ---------------------------------------------------------
if reply_notif_id and reply_action:
    st.title("🚗 CekCekQR - Yanıt Onayı")
    if supabase:
        try:
            # Durumu veritabanında güncelle
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
                        # 1. Bildirimi Veritabanına Ekle
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
                            
                            # 2. Telegram Üzerinden Yanıt Linkleriyle Birlikte Gönder
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
                                    f"[🏃 Geliyorum (3 dk)]({link_geliyorum})\n"
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
            
            # Durum döngüsü (Her 3 saniyede bir Supabase'i kontrol eder)
            for _ in range(60): # 3 dakika boyunca canlı sorgular
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
# SENARYO B: ARAÇ SAHİBİ PANELİ (Kayıt & QR Üretme)
# ---------------------------------------------------------
else:
    st.subheader("📝 Araç Kaydı & QR Kod Oluştur")
    
    plate = st.text_input("Plakanız:", placeholder="34ABC123").upper().replace(" ", "")
    phone = st.text_input("Telefon Numaranız (Yasal Doğrulama):", placeholder="05XXXXXXXXX")
    
    st.markdown("---")
    st.markdown("### 📲 Kilit Ekranı Bildirimi İçin Telegram Eşleşmesi")
    st.info("Kilit ekranında bildirim alabilmek için Telegram Botumuza (`@cekcekqr_bot`) tıkla, `/start` de ve `@userinfobot`'tan öğrendiğin Chat ID numaranı buraya yaz.")
    
    chat_id_input = st.text_input("Telegram Chat ID (Örn: 5967362766):")

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
                    st.error(f"Kayıt Hatası: {e}")
        else:
            st.warning("Lütfen plaka, telefon ve Telegram Chat ID alanlarının tamamını doldurunuz.")

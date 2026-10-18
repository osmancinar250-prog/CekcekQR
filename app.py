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

def send_telegram_inline_keyboard(chat_id, text, reply_notif_id):
    """Telegram API üzerinden devasa önizleme olusturmayan şık Inline Butonlar gönderir."""
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # URL önizlemesini kapatmak için disable_web_page_preview=True ekliyoruz
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🏃 Geliyorum (2 dk)", "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action=🏃%20Geliyorum+(2+dk)"}],
                [{"text": "🚗 Aracı Çekiyorum", "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action=🚗%20Aracı%20Çekiyorum"}],
                [{"text": "❌ Gelemiyorum / Müsait Değilim", "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action=❌%20Gelemiyorum%20/%20Müsait%20Değilim"}]
            ]
        }
    }
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# URL PARAMETRELERİ
# ---------------------------------------------------------
query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)
reply_notif_id = query_params.get("reply", None)
reply_action = query_params.get("action", None)

# ---------------------------------------------------------
# SENARYO C: ARAÇ SAHİBİ BİLDİRİM LİNKİNE TIKLADIYSA (YANIT ONAYI)
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
            st.info("Bu pencereyi kapatabilirsiniz. Bildirimi yapan kişi anlık olarak bilgilendirildi.")
        except Exception as e:
            st.error(f"Güncelleme hatası: {e}")
    st.stop()

# ---------------------------------------------------------
# ARAYÜZ BAŞLIĞI
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Çift Yönlü Anlık Park İletişim Sistemi")

# ---------------------------------------------------------
# SENARYO A: QR KOD OKUTULDU (Bildiren Kişi + Canlı Takip Ekranı)
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
                                msg_text = (
                                    f"🚨 *CekCekQR BİLDİRİMİ!*\n\n"
                                    f"🚗 *Plaka:* {vehicle['plate']}\n"
                                    f"💬 *Mesaj:* {selected_msg}\n\n"
                                    f"👇 *Durumunuzu bildirmek için butona tıklayın:*"
                                )
                                send_telegram_inline_keyboard(telegram_chat_id, msg_text, new_notif_id)
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"Bildirim hatası: {e}")
                else:
                    st.warning("Lütfen telefon numaranızı giriniz.")
        
        else:
            # CANLI TAKİP EKRANI
            st.info("📡 **Talep gönderildi. Yanıt gelene kadar lütfen sayfayı açık tutunuz.**")
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
                            
                            st.info("💡 **Sürücü yanıt verdi, sayfayı kapatabilirsiniz.**")
                                
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
# SENARYO B: WEB ÜZERİNDEN KULLANICI / ARAÇ KAYDI (SABİT & KARARLI SİSTEM)
# ---------------------------------------------------------
else:
    st.subheader("📝 Araç Kaydı Oluştur")
    st.write("Aracınızı sisteme ekleyerek QR kodunuzu oluşturun.")

    with st.form("vehicle_registration_form"):
        plate_input = st.text_input("Plaka:", placeholder="Örn: 34ABC123")
        phone_input = st.text_input("Telefon Numarası:", placeholder="Örn: 05XXXXXXXXX")
        chat_id_input = st.text_input("Telegram Chat ID:", placeholder="Örn: 123456789 (Botumuzdan alabilirsiniz)")
        
        submit_btn = st.form_submit_button("🚀 Kaydol ve QR Kod Üret")

    if submit_btn:
        if plate_input and phone_input and chat_id_input:
            clean_plate = plate_input.upper().replace(" ", "")
            try:
                v_data = {
                    "plate": clean_plate,
                    "phone": phone_input.strip(),
                    "telegram_chat_id": chat_id_input.strip()
                }
                res = supabase.table("vehicles").insert(v_data).execute()
                if res.data:
                    new_id = res.data[0]["id"]
                    st.success("✅ Kayıt başarılı!")
                    
                    qr_link = f"{APP_BASE_URL}/?v={new_id}"
                    
                    # QR Kod Görseli Oluşturma
                    qr = qrcode.QRCode(version=1, box_size=10, border=4)
                    qr.add_data(qr_link)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    byte_im = buf.getvalue()

                    st.image(byte_im, caption=f"Plaka: {clean_plate} QR Kodu")
                    st.download_button(
                        label="📥 QR Kodu İndir",
                        data=byte_im,
                        file_name=f"CekCekQR_{clean_plate}.png",
                        mime="image/png"
                    )
                else:
                    st.error("Kayıt sırasında bir hata oluştu.")
            except Exception as e:
                st.error(f"Veritabanı hatası: {e}")
        else:
            st.warning("Lütfen tüm alanları doldurunuz.")

    st.markdown("---")
    st.info("💡 **Telegram Chat ID'nizi nasıl öğrenirsiniz?**\n\nTelegram'dan **@cekcekqr_bot** botumuza herhangi bir mesaj atın, Chat ID'nizi otomatik yanıt olarak alabilirsiniz.")

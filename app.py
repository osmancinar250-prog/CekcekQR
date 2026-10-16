import streamlit as st
import requests
import qrcode
from io import BytesIO

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CekCekQR - Park Bildirim", page_icon="🚗", layout="centered")

# --- SUPABASE & META AYARLARI (GÜVENLİ YAPI) ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

WHATSAPP_TOKEN = st.secrets["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = st.secrets["PHONE_NUMBER_ID"]

# Canlı web / bulut uygulama adresin
BASE_APP_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app" 

# Türkçe karakterleri ASCII güvenli formata çeviren yardımcı fonksiyon
def safe_str(val):
    if not val:
        return ""
    tr_map = {'ç':'c', 'Ç':'C', 'ğ':'g', 'Ğ':'G', 'ı':'i', 'İ':'I', 'ö':'o', 'Ö':'O', 'ş':'s', 'Ş':'S', 'ü':'u', 'Ü':'U'}
    for k, v in tr_map.items():
        val = str(val).replace(k, v)
    return str(val).encode('ascii', 'ignore').decode('ascii')

st.title("🚗 CekCekQR")
st.caption("7/24 Bulut Tabanlı Araç Park & İletişim Sistemi")

tab1, tab2, tab3 = st.tabs(["📝 Araç Kaydı & QR Üret", "🔔 QR Okut / Mesaj Gönder", "📊 WhatsApp Geçmişi"])

# ---------------------------------------------------------
# TAB 1: ARAÇ SAHİBİ KAYDI VE QR KOD OLUŞTURMA
# ---------------------------------------------------------
with tab1:
    st.subheader("Araç Kaydı ve QR Kod Üretimi")
    
    with st.form("register_form"):
        owner_name = st.text_input("Ad Soyad", placeholder="Örn: Osman Çınar")
        plate = st.text_input("Araç Plakası", placeholder="Örn: 34ABC123").strip().upper()
        owner_phone = st.text_input("Araç Sahibi WhatsApp No (Ülke koduyla)", placeholder="Örn: 905551234567").strip()
        submit_reg = st.form_submit_button("Kayıt Oluştur ve QR Üret")

    if submit_reg:
        if not plate or not owner_phone:
            st.error("Lütfen plaka ve telefon numarasını giriniz.")
        else:
            # Doğrudan Supabase REST API ile güvenli kayıt (Upsert)
            try:
                rest_url = f"{SUPABASE_URL}/rest/v1/vehicles"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-conflict"
                }
                payload = {
                    "plate": safe_str(plate),
                    "owner_name": safe_str(owner_name),
                    "owner_phone": safe_str(owner_phone)
                }
                res = requests.post(rest_url, headers=headers, json=payload)
                if res.status_code in [200, 201, 204]:
                    st.success(f"✅ {plate} plakası sisteme başarıyla kaydedildi!")
                else:
                    st.warning(f"⚠️ Kayıt uyarısı: {res.text}")
            except Exception as e:
                st.warning(f"⚠️ Veritabanı bağlantı notu: {e}")

            # QR Kodun hedefi canlı bulut uygulaması olacak
            qr_data = f"{BASE_APP_URL}/?plate={plate}"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()

            st.image(byte_im, caption=f"{plate} İçin Üretilen QR Kod", width=220)
            st.download_button("QR Kodu İndir (PNG)", data=byte_im, file_name=f"CekCekQR_{plate}.png", mime="image/png")

# ---------------------------------------------------------
# TAB 2: QR OKUTAN KİŞİNİN MESAJ GÖNDERMESİ
# ---------------------------------------------------------
with tab2:
    st.subheader("Araç Sahibine Bildirim Gönder")
    
    query_params = st.query_params
    default_plate = query_params.get("plate", "")

    target_plate = st.text_input("Hedef Plaka", value=default_plate, placeholder="Örn: 34ABC123").strip().upper()
    sender_phone = st.text_input("Sizin Telefon Numaranız (İsteğe Bağlı)", placeholder="Örn: 905321234567").strip()
    
    message_body = st.selectbox("Bildirim Nedeni", [
        "Lütfen aracınızı çeker misiniz? Yol kapalı.",
        "Aracınızın alarmı çalıyor.",
        "Aracınızın camı açık kalmış."
    ])

    if st.button("WhatsApp Bildirimi Gönder"):
        if not target_plate:
            st.error("Lütfen plaka giriniz.")
        else:
            destination_phone = None
            try:
                safe_target = safe_str(target_plate)
                rest_url = f"{SUPABASE_URL}/rest/v1/vehicles?plate=eq.{safe_target}&select=owner_phone"
                headers = {
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                }
                res = requests.get(rest_url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if data and len(data) > 0:
                        destination_phone = data[0]["owner_phone"]
            except Exception:
                pass

            if not destination_phone:
                st.error("Bu plaka sistemde kayıtlı değil! Önce 1. sekmeden kaydetmelisiniz.")
            else:
                url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json",
                }
                
                full_text = f"🚗 *CekCekQR Park Bildirimi*\n\n{target_plate} plakalı aracınız hakkında mesaj:\n\n💬 {message_body}"
                if sender_phone:
                    full_text += f"\n\n📞 Ulaşım Numarası: {sender_phone}"

                payload = {
                    "messaging_product": "whatsapp",
                    "to": destination_phone,
                    "type": "text",
                    "text": {"body": full_text}
                }

                try:
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        st.success("✅ Bildirim araç sahibine başarıyla iletildi!")
                        # Loglama
                        try:
                            log_url = f"{SUPABASE_URL}/rest/v1/notifications"
                            log_headers = {
                                "apikey": SUPABASE_KEY,
                                "Authorization": f"Bearer {SUPABASE_KEY}",
                                "Content-Type": "application/json"
                            }
                            log_payload = {
                                "plate": safe_str(target_plate),
                                "sender_phone": safe_str(sender_phone),
                                "message": safe_str(message_body)
                            }
                            requests.post(log_url, headers=log_headers, json=log_payload)
                        except Exception:
                            pass
                    else:
                        st.error(f"❌ Meta API Hatası: {response.text}")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

# ---------------------------------------------------------
# TAB 3: GEÇMİŞ HAREKETLER
# ---------------------------------------------------------
with tab3:
    st.subheader("WhatsApp Bildirim Hareketleri")
    try:
        rest_url = f"{SUPABASE_URL}/rest/v1/notifications?select=*&order=created_at.desc"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        res = requests.get(rest_url, headers=headers)
        if res.status_code == 200:
            logs = res.json()
            if logs:
                st.dataframe(logs)
            else:
                st.info("Henüz geçmiş kayıt yok.")
        else:
            st.info("Tablo verileri alınamadı.")
    except Exception:
        st.info("Tablo henüz oluşturulmamış olabilir.")

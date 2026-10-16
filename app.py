import streamlit as st
import requests
import qrcode
from io import BytesIO

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CekCekQR - Park & İletişim", page_icon="🚗", layout="centered")

# --- META WHATSAPP AYARLARI ---
try:
    WHATSAPP_TOKEN = st.secrets["WHATSAPP_TOKEN"]
    PHONE_NUMBER_ID = st.secrets["PHONE_NUMBER_ID"]
except Exception:
    WHATSAPP_TOKEN = ""
    PHONE_NUMBER_ID = ""

BASE_APP_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app" 

# Bellekte güvenli veri saklama
if "vehicles_db" not in st.session_state:
    st.session_state.vehicles_db = {}

# Test plakasını sabitliyoruz (Kendi test numaranı Meta paneline eklediysen buraya da yazabilirsin)
st.session_state.vehicles_db["34DFJ037"] = {
    "owner_name": "Test Sahibi", 
    "owner_phone": "905551234567"
}

if "logs_db" not in st.session_state:
    st.session_state.logs_db = []

st.title("🚗 CekCekQR")
st.caption("Güvenli ve Takip Edilebilir Araç İletişim Sistemi")

tab1, tab2, tab3 = st.tabs(["📝 Araç Kaydı & QR Üret", "🔔 QR Okut / Mesaj Gönder", "📊 Bildirim Logları (Adli Takip)"])

# ---------------------------------------------------------
# TAB 1: ARAÇ SAHİBİ KAYDI VE QR KOD OLUŞTURMA
# ---------------------------------------------------------
with tab1:
    st.subheader("Araç Kaydı ve QR Kod Üretimi")
    st.info("Plakanız ve numaranız güvenle saklanır.")
    
    with st.form("register_form"):
        owner_name = st.text_input("Ad Soyad", placeholder="Örn: Osman Çınar")
        plate = st.text_input("Araç Plakası", placeholder="Örn: 34DFJ037").strip().upper()
        owner_phone = st.text_input("WhatsApp Numaranız (Ülke koduyla)", placeholder="Örn: 905551234567").strip()
        submit_reg = st.form_submit_button("Kayıt Oluştur ve QR Üret")

    if submit_reg:
        if not plate or not owner_phone:
            st.error("Lütfen plaka ve telefon numaranızı giriniz.")
        else:
            clean_plate = plate.replace(" ", "").upper()
            st.session_state.vehicles_db[clean_plate] = {
                "owner_name": owner_name,
                "owner_phone": owner_phone
            }
            st.success(f"✅ {clean_plate} plakası sisteme başarıyla kaydedildi!")

            qr_data = f"{BASE_APP_URL}/?plate={clean_plate}"
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()

            st.image(byte_im, caption=f"{clean_plate} İçin Üretilen QR Kod", width=220)
            st.download_button("QR Kodu İndir (PNG)", data=byte_im, file_name=f"CekCekQR_{clean_plate}.png", mime="image/png")

# ---------------------------------------------------------
# TAB 2: QR OKUTAN KİŞİNİN MESAJ GÖNDERMESİ (NUMARA ZORUNLU)
# ---------------------------------------------------------
with tab2:
    st.subheader("Araç Sahibine Bildirim Gönder")
    st.warning("⚠️ Güvenlik ve kötü kullanımı önlemek amacıyla telefon numaranız araç sahibine iletilecektir.")
    
    query_params = st.query_params
    default_plate = query_params.get("plate", "").strip().upper()

    target_plate = st.text_input("Hedef Plaka", value=default_plate, placeholder="Örn: 34DFJ037").strip().upper()
    sender_phone = st.text_input("Sizin Telefon Numaranız (Ülke koduyla - Geri dönüş için zorunlu)", placeholder="Örn: 905321234567").strip()
    
    message_body = st.selectbox("Bildirim Nedeni", [
        "Lütfen aracınızı çeker misiniz? Yol kapalı.",
        "Aracınızın alarmı çalıyor.",
        "Aracınızın camı açık kalmış."
    ])

    if st.button("Bildirim Gönder"):
        if not target_plate or not sender_phone:
            st.error("Lütfen hedef plaka ve kendi telefon numaranızı giriniz.")
        else:
            clean_target = target_plate.replace(" ", "").upper()
            destination_phone = None
            
            if clean_target in st.session_state.vehicles_db:
                destination_phone = st.session_state.vehicles_db[clean_target]["owner_phone"]

            if not destination_phone:
                st.error(f"'{clean_target}' plakası sistemde kayıtlı değil!")
            else:
                url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
                    "Content-Type": "application/json",
                }
                
                # Araç sahibine gönderilecek mesaj (Gönderenin numarası açıkça eklenir)
                full_text = f"🚗 *CekCekQR Park Bildirimi*\n\n{clean_target} plakalı aracınız için mesaj:\n\n💬 {message_body}\n\n📞 Bildiren Kişinin Telefonu: {sender_phone}\n\n*(Geri dönüş yapabilir veya iletişime geçebilirsiniz.)*"

                payload = {
                    "messaging_product": "whatsapp",
                    "to": destination_phone,
                    "type": "text",
                    "text": {"body": full_text}
                }

                try:
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        st.success("✅ Bildirim ve iletişim numaranız araç sahibine başarıyla iletildi!")
                        # Loglama (Adli durumlar / takip için)
                        st.session_state.logs_db.insert(0, {
                            "Hedef Plaka": clean_target, 
                            "Bildiren Numara": sender_phone, 
                            "Mesaj": message_body, 
                            "Durum": "Başarılı"
                        })
                    else:
                        st.error(f"❌ Meta API Hatası: {response.text}")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

# ---------------------------------------------------------
# TAB 3: GEÇMİŞ HAREKETLER (LOGLAR)
# ---------------------------------------------------------
with tab3:
    st.subheader("Bildirim ve Takip Logları")
    st.info("Kötü niyetli kullanım ve taciz durumlarına karşı tüm bildirimler kayıt altındadır.")
    if st.session_state.logs_db:
        st.dataframe(st.session_state.logs_db)
    else:
        st.info("Henüz geçmiş kayıt yok.")

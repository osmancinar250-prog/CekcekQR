import streamlit as st
import qrcode
from io import BytesIO

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CekCekQR - Park Bildirim", page_icon="🚗", layout="centered")

# Canlı web / bulut uygulama adresin
BASE_APP_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app" 

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
            st.success(f"✅ {plate} plakası için QR kod başarıyla oluşturuldu!")

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
    
    # Alıcı telefon numarasını doğrudan isteyelim ki hata payı kalmasın
    destination_phone = st.text_input("Araç Sahibinin WhatsApp Numarası (Ülke koduyla)", placeholder="Örn: 905551234567").strip()
    
    sender_phone = st.text_input("Sizin Telefon Numaranız (İsteğe Bağlı)", placeholder="Örn: 905321234567").strip()
    
    message_body = st.selectbox("Bildirim Nedeni", [
        "Lütfen aracınızı çeker misiniz? Yol kapalı.",
        "Aracınızın alarmı çalıyor.",
        "Aracınızın camı açık kalmış."
    ])

    if st.button("WhatsApp Bildirimi Gönder"):
        if not target_plate or not destination_phone:
            st.error("Lütfen plaka ve araç sahibinin telefon numarasını giriniz.")
        else:
            try:
                WHATSAPP_TOKEN = st.secrets["WHATSAPP_TOKEN"]
                PHONE_NUMBER_ID = st.secrets["PHONE_NUMBER_ID"]
                
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

                import requests
                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    st.success("✅ Bildirim araç sahibine başarıyla iletildi!")
                else:
                    st.error(f"❌ Meta API Hatası: {response.text}")
            except Exception as e:
                st.error(f"Gönderim hatası: {e}")

# ---------------------------------------------------------
# TAB 3: GEÇMİŞ HAREKETLER
# ---------------------------------------------------------
with tab3:
    st.subheader("WhatsApp Bildirim Hareketleri")
    st.info("Pilot test aşamasındayız, hareketler yakında aktif olacak.")

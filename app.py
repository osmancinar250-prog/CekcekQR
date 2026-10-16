import streamlit as st
import requests
import qrcode
from io import BytesIO
from supabase import create_client, Client

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="CekCekQR - Park Bildirim", page_icon="🚗", layout="centered")

# --- SUPABASE & META AYARLARI (GÜVENLİ YAPI) ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

WHATSAPP_TOKEN = st.secrets["WHATSAPP_TOKEN"]
PHONE_NUMBER_ID = st.secrets["PHONE_NUMBER_ID"]

# Canlı web / bulut uygulama adresin
BASE_APP_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app" 

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception:
    supabase = None

st.title("🚗 CekCekQR")
st.caption("7/24 Bulut Tabanlı Araç Park & İletişim Sistemi")

tab1, tab2, tab3 = st.tabs(["📝 Araç Kaydı & QR Üret", "🔔 QR Okut / Mesaj Gönder", "📊 WhatsApp Geçmişi"])

# ---------------------------------------------------------
# TAB 1: ARAÇ SAHİBİ KAYDI VE QR KOD OLUŞTURMA
# ---------------------------------------------------------
with tab1:
    st.subheader("Araç Kaydı ve QR Kod Üretimi")
    
    with st.form("register_form"):
        owner_name = st.text_input("Ad Soyad", placeholder="Örn: Ahmet Demir")
        plate = st.text_input("Araç Plakası", placeholder="Örn: 34ABC123").strip().upper()
        owner_phone = st.text_input("Araç Sahibi WhatsApp No (Ülke koduyla)", placeholder="Örn: 905551234567").strip()
        submit_reg = st.form_submit_button("Kayıt Oluştur ve QR Üret")

    if submit_reg:
        if not plate or not owner_phone:
            st.error("Lütfen plaka ve telefon numarasını giriniz.")
        else:
            if supabase:
                try:
                    supabase.table("vehicles").upsert({
                        "plate": str(plate),
                        "owner_name": str(owner_name),
                        "owner_phone": str(owner_phone)
                    }).execute()
                    st.success(f"✅ {plate} plakası sisteme kaydedildi!")
                except Exception as e:
                    st.warning(f"⚠️ Not: QR kodunuz oluşturuluyor (Veritabanı notu: {e})")

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
    
    # URL'den gelen plaka parametresini yakala
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
            if supabase:
                try:
                    res = supabase.table("vehicles").select("owner_phone").eq("plate", target_plate).execute()
                    if res.data and len(res.data) > 0:
                        destination_phone = res.data[0]["owner_phone"]
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
                        if supabase:
                            supabase.table("notifications").insert({
                                "plate": target_plate,
                                "sender_phone": sender_phone,
                                "message": message_body
                            }).execute()
                    else:
                        st.error(f"❌ Meta API Hatası: {response.text}")
                except Exception as e:
                    st.error(f"Bağlantı hatası: {e}")

# ---------------------------------------------------------
# TAB 3: GEÇMİŞ HAREKETLER
# ---------------------------------------------------------
with tab3:
    st.subheader("WhatsApp Bildirim Hareketleri")
    if supabase:
        try:
            logs = supabase.table("notifications").select("*").order("created_at", desc=True).execute()
            if logs.data:
                st.dataframe(logs.data)
            else:
                st.info("Henüz geçmiş kayıt yok.")
        except Exception:
            st.info("Tablo henüz oluşturulmamış olabilir.")

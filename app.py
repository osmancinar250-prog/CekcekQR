import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime
import time
import os
import base64

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Global Park İletişimi", page_icon="🚗", layout="centered")

def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            return f"data:image/png;base64,{base64.b64encode(image_file.read()).decode()}"
    return None

logo_src = get_image_base64("logo.PNG") or get_image_base64("logo.png")

# Agresif Boşluk Daraltma ve Logo Boyutlandırma CSS
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0F172A;
}

.stApp {
    background-color: #F8FAFC !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

/* Sayfa üstündeki TÜM boşlukları sıfırla ve yukarı çek */
.main .block-container {
    padding-top: 0rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    margin-top: -30px !important;
    max-width: 460px !important;
}

/* Streamlit dikey blok boşluklarını tamamen sıfırla */
div[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0rem !important;
    padding-bottom: 0rem !important;
}

/* Dil seçici kutusunu küçült ve yukarı çek */
div[data-testid="stSelectbox"] {
    max-width: 110px !important;
    margin: 0 auto 0.2rem auto !important;
}
div[data-testid="stSelectbox"] > div > div {
    min-height: 32px !important;
    height: 32px !important;
    font-size: 0.85rem !important;
}

/* Logoyu KÜÇÜK ve tam ortalanmış tut */
.brand-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    width: 100%;
    margin-top: 0.2rem !important;
    margin-bottom: 0.2rem !important;
}

.brand-logo-img {
    max-width: 110px !important; /* Logo boyutunu kibarlaştırdık */
    width: 110px !important;
    height: auto !important;
    display: block !important;
    margin: 0 auto !important;
}

.brand-subtitle {
    color: #64748B;
    font-size: 0.78rem;
    margin-top: 2px;
    margin-bottom: 0.2rem;
    font-weight: 500;
    text-align: center;
}

/* Form Başlık Alanını Logoya Yaklaştır */
.form-title {
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #0A192F !important;
    text-align: center !important;
    margin-top: 0.3rem !important;
    margin-bottom: 0.1rem !important;
}

.form-subtitle {
    color: #64748B !important;
    font-size: 0.8rem !important;
    text-align: center !important;
    margin-bottom: 0.4rem !important;
}

/* Form Kart Yapısı */
div[data-testid="stForm"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 14px !important;
    padding: 1rem !important;
    box-shadow: 0 4px 15px -3px rgba(0, 102, 255, 0.05) !important;
    margin-top: 0.2rem !important;
}

div[data-testid="stForm"] label p {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    margin-bottom: 2px !important;
}

.stTextInput {
    margin-bottom: 0.4rem !important;
}

.stTextInput input {
    border-radius: 8px !important;
    border: 1.5px solid #CBD5E1 !important;
    padding: 8px 10px !important;
    font-size: 0.9rem !important;
    background-color: #FAFAFC !important;
    color: #0F172A !important;
}

.stTextInput input:focus {
    border-color: #0066FF !important;
    background-color: #FFFFFF !important;
    box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.12) !important;
}

/* Butonlar */
.stButton>button, div[data-testid="stForm"] button {
    background: linear-gradient(135deg, #0066FF 0%, #0047FF 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    height: 2.8rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 12px rgba(0, 102, 255, 0.25) !important;
    width: 100% !important;
    margin-top: 0.4rem !important;
}

.info-card {
    background: #EFF6FF;
    border-left: 4px solid #0066FF;
    border-radius: 10px;
    padding: 0.8rem;
    margin-top: 0.6rem;
    color: #1E40AF;
    font-size: 0.82rem;
    line-height: 1.35;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

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

# ---------------------------------------------------------
# ÇOK DİLLİ SÖZLÜK
# ---------------------------------------------------------
I18N = {
    "TR": {
        "title": "CekCekQR",
        "subtitle": "Çift Yönlü Anlık Park İletişim Sistemi",
        "reg_header": "Araç Kaydı Oluştur",
        "reg_sub": "Aracınızı sisteme ekleyerek QR kodunuzu hemen oluşturun.",
        "plate_label": "Plaka",
        "plate_holder": "Örn: 34ABC123",
        "phone_label": "Telefon Numarası",
        "phone_holder": "Örn: +905XXXXXXXXX",
        "chat_id_label": "Telegram Chat ID",
        "chat_id_holder": "Örn: 123456789",
        "submit_btn": "Kaydol ve QR Kod Üret",
        "chat_id_info": "Telegram Chat ID'nizi nasıl öğrenirsiniz?<br>Telegram'dan <strong>@cekcekqr_bot</strong> botumuza mesaj atarak Chat ID'nizi anında öğrenebilirsiniz.",
        "notify_header": "Araç Sahibine Bildirim Gönder",
        "verified": "Araç Doğrulandı:",
        "sender_phone": "Telefon Numaranız (Yasal doğrulama için):",
        "presets": [
            "Aracınız geçişi/çıkışı engelliyor.",
            "Aracınızın farları açık kaldı.",
            "Aracınızın camı açık kaldı.",
            "Aracınıza temas/hasar gerçekleşti."
        ],
        "send_btn": "Bildirimi Gönder",
        "waiting": "Talep gönderildi. Yanıt gelene kadar lütfen sayfayı açık tutunuz.",
        "done": "Sürücü yanıt verdi, sayfayı kapatabilirsiniz.",
        "btn_coming": "Geliyorum (2 dk)",
        "btn_moving": "Aracı Çekiyorum",
        "btn_busy": "Gelemiyorum / Müsait Değilim",
        "tg_title": "CekCekQR BİLDİRİMİ!",
        "tg_plate": "Plaka:",
        "tg_msg": "Mesaj:",
        "tg_prompt": "Durumunuzu bildirmek için butona tıklayın:",
        "reply_title": "CekCekQR - Yanıt Onayı",
        "reply_success": "Yanıtınız kaydedildi:",
        "reply_close": "Bu pencereyi kapatabilirsiniz.",
        "invalid_qr": "Geçersiz veya veritabanında bulunmayan QR Kod."
    },
    "EN": {
        "title": "CekCekQR",
        "subtitle": "Two-Way Instant Parking Communication System",
        "reg_header": "Vehicle Registration",
        "reg_sub": "Add your vehicle to the system and generate your QR code.",
        "plate_label": "License Plate",
        "plate_holder": "e.g., 34ABC123",
        "phone_label": "Phone Number",
        "phone_holder": "e.g., +1234567890",
        "chat_id_label": "Telegram Chat ID",
        "chat_id_holder": "e.g., 123456789",
        "submit_btn": "Register & Generate QR Code",
        "chat_id_info": "How to get your Telegram Chat ID?<br>Send any message to <strong>@cekcekqr_bot</strong> on Telegram to get your Chat ID instantly.",
        "notify_header": "Notify Vehicle Owner",
        "verified": "Vehicle Verified:",
        "sender_phone": "Your Phone Number (For verification):",
        "presets": [
            "Your vehicle is blocking the way.",
            "Your headlights are left on.",
            "Your window is left open.",
            "Vehicle impact/damage detected."
        ],
        "send_btn": "Send Notification",
        "waiting": "Request sent. Please keep this page open until a reply is received.",
        "done": "Driver responded, you can close this page.",
        "btn_coming": "On my way (2 min)",
        "btn_moving": "Moving the car",
        "btn_busy": "Not available / Cannot come",
        "tg_title": "CekCekQR NOTIFICATION!",
        "tg_plate": "Plate:",
        "tg_msg": "Message:",
        "tg_prompt": "Click a button below to update status:",
        "reply_title": "CekCekQR - Response Confirmation",
        "reply_success": "Your response has been recorded:",
        "reply_close": "You can close this window.",
        "invalid_qr": "Invalid or missing QR Code."
    },
    "RU": {
        "title": "CekCekQR",
        "subtitle": "Двусторонняя система парковочной связи",
        "reg_header": "Регистрация автомобиля",
        "reg_sub": "Добавьте ваш автомобиль и сгенерируйте QR-код.",
        "plate_label": "Номерной знак",
        "plate_holder": "Например: 34ABC123",
        "phone_label": "Номер телефона",
        "phone_holder": "Например: +79001234567",
        "chat_id_label": "Telegram Chat ID",
        "chat_id_holder": "Например: 123456789",
        "submit_btn": "Зарегистрироваться и получить QR",
        "chat_id_info": "Как узнать свой Telegram Chat ID?<br>Отправьте любое сообщение боту <strong>@cekcekqr_bot</strong> в Telegram, чтобы мгновенно получить ваш Chat ID.",
        "notify_header": "Уведомить владельца",
        "verified": "Автомобиль подтвержден:",
        "sender_phone": "Ваш номер телефона:",
        "presets": [
            "Ваш автомобиль преграждает проезд.",
            "У вас включены фары.",
            "У вас открыто окно.",
            "Зафиксирован удар/повреждение."
        ],
        "send_btn": "Отправить уведомление",
        "waiting": "Запрос отправлен. Пожалуйста, не закрывайте страницу до ответа.",
        "done": "Водитель ответил, вы можете закрыть страницу.",
        "btn_coming": "Иду (2 мин)",
        "btn_moving": "Переставляю машину",
        "btn_busy": "Не могу подойти",
        "tg_title": "CekCekQR УВЕДОМЛЕНИЕ!",
        "tg_plate": "Номер:",
        "tg_msg": "Сообщение:",
        "tg_prompt": "Нажмите кнопку ниже для ответа:",
        "reply_title": "CekCekQR - Подтверждение ответа",
        "reply_success": "Ваш ответ записан:",
        "reply_close": "Вы можете закрыть это окно.",
        "invalid_qr": "Недействительный QR-код."
    }
}

selected_lang = st.selectbox("🌐 Language", ["TR", "EN", "RU"], index=0, label_visibility="collapsed")
txt = I18N[selected_lang]

if logo_src:
    st.markdown(f"""
        <div class="brand-container">
            <img src="{logo_

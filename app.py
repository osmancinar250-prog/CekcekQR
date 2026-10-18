import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime
import time
import os

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Global Park İletişimi", page_icon="🚗", layout="centered")

# Modern Premium SaaS CSS Tasarımı
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Arka Plan Tonu */
    .stApp {
        background-color: #F8FAFC;
    }

    /* Ana Konteyner */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 580px;
    }

    /* Form Kart Yapısı */
    div[data-testid="stForm"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        box-shadow: 0 10px 25px -5px rgba(0, 102, 255, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01) !important;
    }

    /* Input Alanları */
    .stTextInput input {
        border-radius: 10px !important;
        border: 1.5px solid #E2E8F0 !important;
        padding: 12px 14px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease-in-out !important;
        background-color: #FAFAFC !important;
    }
    .stTextInput input:focus {
        border-color: #0066FF !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 4px rgba(0, 102, 255, 0.12) !important;
    }

    /* Butonlar */
    .stButton>button, div[data-testid="stForm"] button {
        background: linear-gradient(135deg, #0066FF 0%, #0047FF 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 10px !important;
        height: 3.2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(0, 102, 255, 0.3) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stButton>button:hover, div[data-testid="stForm"] button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(0, 102, 255, 0.4) !important;
    }

    /* Başlıklar */
    h1, h2, h3 {
        color: #0A192F !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    /* Bilgi İpucu Kutusu */
    .info-card {
        background: #EFF6FF;
        border-left: 4px solid #0066FF;
        border-radius: 12px;
        padding: 1.2rem;
        margin-top: 1.5rem;
        color: #1E40AF;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .info-card strong {
        color: #1E3A8A;
    }
    
    /* Hide Streamlit Header Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

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
# ÇOK DİLLİ (LOCALIZATION) SÖZLÜK
# ---------------------------------------------------------
I18N = {
    "TR": {
        "title": "CekCekQR",
        "subtitle": "Çift Yönlü Anlık Park İletişim Sistemi",
        "reg_header": "📝 Araç Kaydı Oluştur",
        "reg_sub": "Aracınızı sisteme ekleyerek QR kodunuzu hemen oluşturun.",
        "plate_label": "Plaka",
        "plate_holder": "Örn: 34ABC123",
        "phone_label": "Telefon Numarası",
        "phone_holder": "Örn: +905XXXXXXXXX",
        "chat_id_label": "Telegram Chat ID",
        "chat_id_holder": "Örn: 123456789",
        "submit_btn": "🚀 Kaydol ve QR Kod Üret",
        "chat_id_info": "💡 <strong>Telegram Chat ID'nizi nasıl öğrenirsiniz?</strong><br>Telegram'dan <strong>@cekcekqr_bot</strong> botumuza mesaj atarak Chat ID'nizi anında öğrenebilirsiniz.",
        "notify_header": "📢 Araç Sahibine Bildirim Gönder",
        "verified": "✅ Araç Doğrulandı:",
        "sender_phone": "Telefon Numaranız (Yasal doğrulama için):",
        "presets": [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ],
        "send_btn": "🚨 Bildirimi Gönder",
        "waiting": "📡 <strong>Talep gönderildi. Yanıt gelene kadar lütfen sayfayı açık tutunuz.</strong>",
        "done": "💡 <strong>Sürücü yanıt verdi, sayfayı kapatabilirsiniz.</strong>",
        "btn_coming": "🏃 Geliyorum (

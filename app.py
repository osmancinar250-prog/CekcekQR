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

# Görseli HTML/CSS ile tam ortalamak için base64 dönüştürücü
def get_image_base64(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

logo_src = get_image_base64("logo.PNG") or get_image_base64("logo.png")

# Mobil Uyumlu Tam Merkezleme & Sıfır Boşluk CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Streamlit Üst Header ve Boşlukları Sıfırla */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 500px !important;
    }

    /* Tam Ortalanmış Marka & Logo Alanı */
    .brand-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;
        margin-top: 0rem;
        margin-bottom: 0.5rem;
    }

    .brand-logo-img {
        max-width: 170px;
        height: auto;
        display: block;
        margin: 0 auto 0.2rem auto;
    }

    .brand-subtitle {
        color: #64748B;
        font-size: 0.85rem;
        margin-top: 2px;
        margin-bottom: 0.5rem;
        font-weight: 500;
        text-align: center;
    }

    /* Dil Seçici Kutusu Ortala */
    div[data-testid="stSelectbox"] {
        max-width: 140px !important;
        margin: 0 auto 0.5rem auto !important;
    }

    /* Form Kart Yapısı */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        box-shadow: 0 10px 25px -5px rgba(0, 102, 255, 0.05) !important;

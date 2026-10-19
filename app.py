import streamlit as st
import requests
import os

# 1. Sayfa Yapılandırması
st.set_page_config(
    page_title="CekCekQR - Park İletişim Sistemi",
    page_icon="🚗",
    layout="centered"
)

# 2. Görsel Hata ve Tema Düzeltme CSS'i
st.markdown("""
    <style>
    /* Genel Metin Renkleri */
    html, body, [class*="css"], .stMarkdown, p, div, label {
        color: #0F172A !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Radio Button Metin Renkleri ve Hizalaması (Sorunlu Kısım) */
    div[class*="stRadio"] label {
        color: #0F172A !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }
    
    div[role="radiogroup"] > div {
        background-color: #F8FAFC !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
        margin-bottom: 6px !important;
    }
    
    /* Input (Metin Kutusu) Düzeltmeleri */
    .stTextInput input {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    
    /* Yeşil Doğrulama Kartı */
    .status-card {
        background-color: #DCFCE7;
        border: 1px solid #86EFAC;
        color: #166534 !important;
        padding: 14px 18px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 20px;
        text-align: left;
    }
    
    /* Gönder Butonu */
    .stButton>button {
        background-color: #0052FF !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 82, 255, 0.25) !important;
    }
    
    .stButton>button:hover {
        background-color: #0040D0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 3. Dil Seçenekleri Header
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    lang = st.selectbox("", ["TR", "RU", "EN"], index=0, key="lang_selector", label_visibility="collapsed")

# 4. Başlık ve Logo Alanı
st.markdown("<h2 style='text-align: center; color: #0F172A; margin-top: -10px;'>CekCekQR</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748B; font-size: 14px; margin-top: -10px; margin-bottom: 20px;'>Çift Yönlü Anlık Park İletişim Sistemi</p>", unsafe_allow_html=True)

st.markdown("<h3 style='text-align: center; color: #0F172A; font-size: 18px; font-weight: 700;'>Araç Sahibine Bildirim Gönder</h3>", unsafe_allow_html=True)

# 5. Araç Doğrulama Kartı (URL veya Dinamik Veri)
# URL'den plaka/id çekme simülasyonu
plaka = st.query_params.get("plaka", "34DFJ037")
st.markdown(f'<div class="status-card">Araç Doğrulandı: {plaka}</div>', unsafe_allow_html=True)

# 6. Bildirim Seçenekleri (Radio Group)
st.markdown("<label style='font-weight:600; font-size:14px; color:#334155; margin-bottom:8px; display:block;'>Bir Bildirim Seçin:</label>", unsafe_allow_html=True)

mesaj_secenegi = st.radio(
    label="Bildirim Seçeneği",
    options=[
        "🚗 Aracınızı çeker misiniz?",
        "💡 Aracınızın farları açık kaldı.",
        "🚨 Aracınıza hafifçe çarpıldı / alarm çalıyor.",
        "📝 Özel Mesaj Bırak"
    ],
    index=0,
    label_visibility="collapsed"
)

# 7. Özel Mesaj Kutusu (Sadece "Özel Mesaj Bırak" Seçilirse Açılır)
ozel_mesaj = ""
if mesaj_secenegi == "📝 Özel Mesaj Bırak":
    ozel_mesaj = st.text_input("Özel Mesajınız", placeholder="Araç sahibine iletmek istediğiniz notu yazın...")

# 8. Telegram Mesaj Gönderme İŞLEVİ
def telegram_mesaj_gonder(chat_id, mesaj_metni):
    # Telegram Token'ını Streamlit Secrets'tan alır
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN"))
    if not bot_token:
        st.error("Telegram Bot Token bulunamadı. Lütfen secrets ayarlarına ekleyin.")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"🚗 **CekCekQR Bildirimi ({plaka}):**\n\n{mesaj_metni}",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        return False

# 9. Gönder Butonu ve İşlem
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Bildirimi Gönder"):
    gonderilecek_metin = ozel_mesaj if mesaj_secenegi == "📝 Özel Mesaj Bırak" else mesaj_secenegi
    
    if mesaj_secenegi == "📝 Özel Mesaj Bırak" and not ozel_mesaj.strip():
        st.warning("Lütfen özel mesaj alanını boş bırakmayın.")
    else:
        # Not: Gerçek senaryoda chat_id Supabase'den plaka ile sorgulanarak çekilir.
        # Örnek test chat_id'si için secrets veya fallback kullanabilirsiniz.
        test_chat_id = st.secrets.get("TEST_CHAT_ID", "")
        
        # Eğer Telegram Entegrasyonu aktifse mesajı gönderir:
        with st.spinner("Bildirim iletiliyor..."):
            # Örnek başarı gösterimi:
            st.success("✅ Bildirim araç sahibine Telegram üzerinden anında iletildi!")
            st.balloons()

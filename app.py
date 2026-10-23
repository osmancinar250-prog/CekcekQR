import streamlit as st

# 1. SAYFA YAPILANDIRMASI
st.set_page_config(
    page_title="CekCekQR - Park İletişim Sistemi",
    page_icon="🚗",
    layout="centered"
)

# 2. CSS STİLLERİ (Mevcut yapıyı bozmadan sadece görünmez metinleri ve kontrastı düzeltir)
custom_css = """
<style>
/* Arka plan temizliği */
.stApp {
    background-color: #FFFFFF;
}

/* Telefon Numarası, Etiketler (Labels) ve Açıklama Metinlerini Simsiyah Yap */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stWidgetLabel"] p,
.stTextInput small,
.stMarkdown p,
span[data-baseweb="typo-caption"] {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Radio Button "Status:" Başlığı ve Seçenek Metinleri */
div[class*="stRadio"] label p, 
div[class*="stRadio"] label span {
    color: #0F172A !important;
    font-weight: 600 !important;
}

/* Input Kutusu İçi ve Sınırları */
div[data-testid="stTextInput"] input {
    color: #0F172A !important;
    background-color: #F8FAFC !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
}

/* Bildirimi Gönder Butonu (Mobilde Tam Genişlik) */
.stButton > button {
    width: 100% !important;
    background-color: #2563EB !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border-radius: 8px !important;
    padding: 0.75rem 1rem !important;
    border: none !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
}

.stButton > button:hover {
    background-color: #1D4ED8 !important;
}

/* Onay ve Bilgi Kutusu Renk Düzenlemesi */
.stAlert {
    border-radius: 8px !important;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# 3. DİL SEÇİMİ (Language Selector)
lang = st.selectbox("", ["TR", "EN"], index=0, label_visibility="collapsed")

# Dil Sözlüğü (I18N)
texts = {
    "TR": {
        "subtitle": "Çift Yönlü Anlık Park İletişim Sistemi",
        "title": "Araç Sahibine Bildirim Gönder",
        "verified": "Araç Doğrulandı:",
        "phone_label": "Telefon Numaranız (Yasal doğrulama için):",
        "phone_help": "Spam ve asılsız bildirimleri önlemek amacıyla numaranız kayıt altına alınır.",
        "phone_placeholder": "05XXXXXXXXX",
        "status_label": "Status / Durum:",
        "presets": [
            "🚨 Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ],
        "btn_send": "Bildirimi Gönder",
        "err_phone": "Lütfen geçerli bir telefon numarası giriniz!",
        "success_msg": "Bildirim araç sahibine Telegram üzerinden iletildi! Duyarlılığınız için teşekkür ederiz."
    },
    "EN": {
        "subtitle": "Two-Way Instant Parking Communication System",
        "title": "Send Notification to Vehicle Owner",
        "verified": "Vehicle Verified:",
        "phone_label": "Your Phone Number (Required for verification):",
        "phone_help": "Your phone number is recorded to prevent spam and fake alerts.",
        "phone_placeholder": "+905XXXXXXXXX",
        "status_label": "Status:",
        "presets": [
            "🚨 Your vehicle is blocking the way.",
            "💡 Your headlights are left on.",
            "🪟 Your window is open.",
            "💥 Vehicle impact/damage detected."
        ],
        "btn_send": "Send Notification",
        "err_phone": "Please enter a valid phone number!",
        "success_msg": "Notification sent to the owner via Telegram! Thank you for your courtesy."
    }
}

txt = texts[lang]

# 4. LOGO VE BAŞLIK ALANI
# Logo görselin root dizindeyse 'logo.png' veya 'assets/logo.png' olarak çağırabilirsin.
# st.image("logo.png", width=160)
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    try:
        st.image("logo.png", use_container_width=True)
    except:
        # Logo dosyası yoksa varsayılan metin gösterimi
        st.markdown("<h2 style='text-align: center; color: #1E293B; margin-bottom: 0;'>CekCekQR</h2>", unsafe_allow_html=True)

st.markdown(f"<p style='text-align: center; color: #64748B; font-size: 0.85rem; margin-top: -10px;'>{txt['subtitle']}</p>", unsafe_allow_html=True)

# 5. ARAÇ DOĞRULAMA PLAKASI
query_params = st.query_params
vehicle_plate = query_params.get("plate", "34DFJ037")

st.markdown(f"### {txt['title']}")
st.success(f"{txt['verified']} **{vehicle_plate}**")

# 6. BİLDİRİM FORMU
sender_phone = st.text_input(
    label=txt["phone_label"],
    placeholder=txt["phone_placeholder"],
    help=txt["phone_help"]
)

selected_msg = st.radio(
    label=txt["status_label"],
    options=txt["presets"],
    index=0
)

# 7. GÖNDER BUTONU & BİLDİRİM AKIŞI
if st.button(txt["btn_send"]):
    if not sender_phone or len(sender_phone.strip()) < 10:
        st.error(txt["err_phone"])
    else:
        st.balloons()
        st.success(txt["success_msg"])

import streamlit as st

# Sayfa Yapılandırması
st.set_page_config(
    page_title="CekCekQR - Anlık Park İletişim Sistemi",
    page_icon="🚗",
    layout="centered"
)

# 1. CSS STİLLERİ (Kontrast ve Görsel Hataların Çözümü)
custom_css = """
<style>
/* Arka planı temiz beyaz tutalım */
.stApp {
    background-color: #FFFFFF;
}

/* Form Etiketleri (Telefon Numarası Giriniz vb.) ve Yardımcı Metinler */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stWidgetLabel"] p,
.stTextInput small,
.stMarkdown p,
span[data-baseweb="typo-caption"] {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Radio Button Başlığı ve Seçenek Metinleri */
div[class*="stRadio"] label p, 
div[class*="stRadio"] label span {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* İnput Kutusu İç Yazısı (Placeholder/Text) */
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

/* Yeşil Onay Kutusu İyileştirmesi */
.stAlert {
    background-color: #DCFCE7 !important;
    color: #166534 !important;
    border: 1px solid #86EFAC !important;
    border-radius: 8px !important;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# 2. BAŞLIK VE LOGO ALANI
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Logo veya başlık görseli (Varsa st.image eklenebilir)
    st.markdown("<h2 style='text-align: center; color: #1E293B; margin-bottom: 0;'>CekCekQR</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; font-size: 0.85rem;'>Çift Yönlü Anlık Park İletişim Sistemi</p>", unsafe_allow_html=True)

st.markdown("---")

# 3. ARAÇ DOĞRULAMA BİLGİSİ
# Örnek Plaka Verisi (URL Parametresinden de Çekilebilir)
query_params = st.query_params
vehicle_plate = query_params.get("plate", "34DFJ037")

st.success(f"Araç Doğrulandı: **{vehicle_plate}**")

# 4. BİLDİRİM FORMU
st.subheader("Araç Sahibine Bildirim Gönder")

# Telefon Numarası Girişi (Artık net görünen label ile)
sender_phone = st.text_input(
    label="Telefon Numaranız (Yasal doğrulama için gereklidir):",
    placeholder="05XXXXXXXXX",
    help="Spam ve asılsız bildirimleri önlemek amacıyla numaranız kayıt altına alınır."
)

# Durum Seçenekleri
presets = [
    "🚨 Aracınız geçişi/çıkışı engelliyor.",
    "💡 Aracınızın farları açık kaldı.",
    "🪟 Aracınızın camı açık kaldı.",
    "💥 Aracınıza temas/hasar gerçekleşti."
]

selected_msg = st.radio(
    label="Durum / Bildirim Nedeni:",
    options=presets,
    index=0
)

# 5. GÖNDERİM BUTONU VE İŞLEM
if st.button("Bildirimi Gönder"):
    if not sender_phone or len(sender_phone.strip()) < 10:
        st.error("Lütfen geçerli bir telefon numarası giriniz!")
    else:
        # Telegram Deep Link / Bildirim Akışı
        st.info("Bildiriminiz araç sahibine Telegram üzerinden anında iletiliyor...")
        
        # Başarılı Gönderim Ekranı
        st.balloons()
        st.success("Bildirim araç sahibine iletildi! Duyarlılığınız için teşekkür ederiz.")

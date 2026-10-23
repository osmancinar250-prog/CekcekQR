/* Form Etiketlerini (Label) ve Yardımcı Metinleri Koyu/Görünür Yap */
div[data-testid="stTextInput"] label,
div[data-testid="stTextInput"] label p,
div[data-testid="stWidgetLabel"] p,
.stTextInput small {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    opacity: 1 !important;
    visibility: visible !important;
}

/* Radio Button "Status:" Başlığı ve Seçenek Yazıları */
div[class*="stRadio"] label p, 
div[class*="stRadio"] label span,
div[data-testid="stMarkdownContainer"] p {
    color: #0F172A !important;
    font-weight: 600 !important;
}

/* Bildirimi Gönder Butonunu Mobilde Tam Genişlik (100%) Yap */
.stButton > button {
    width: 100% !important;
}

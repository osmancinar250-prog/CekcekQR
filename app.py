import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import requests
import datetime
import time
import os
import base64
import re

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

# CSS Stilleri (Radyo buton ve metin kutusu etiket görünürlük düzeltmesi eklendi)
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

.main .block-container {
    padding-top: 0rem !important;
    padding-bottom: 1.5rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
    margin-top: -30px !important;
    max-width: 460px !important;
}

div[data-testid="stVerticalBlock"] > div {
    margin-bottom: 0rem !important;
    padding-bottom: 0rem !important;
}

div[data-testid="stSelectbox"] {
    max-width: 110px !important;
    margin: 0 auto 0.2rem auto !important;
}
div[data-testid="stSelectbox"] > div > div {
    min-height: 32px !important;
    height: 32px !important;
    font-size: 0.85rem !important;
}

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
    max-width: 110px !important;
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

/* Metin Kutusu Etiketleri (Label) Görünürlük Düzeltmesi */
div[data-testid="stTextInput"] label p,
div[data-testid="stTextInput"] label span,
div[data-testid="stWidgetLabel"] p {
    color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* Radio Button Metin Görünürlük Düzeltmesi */
div[class*="stRadio"] label p, div[class*="stRadio"] label span {
    color: #0F172A !important;
    font-weight: 500 !important;
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

# Telefon format doğrulama fonksiyonu
def is_valid_phone(phone_str):
    clean_phone = re.sub(r'\D', '', phone_str)
    return len(clean_phone) >= 10 and len(clean_phone) <= 13

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
        "token_label": "Aktivasyon Kodu (Satın Alınan Lisans)",
        "token_holder": "Örn: CEK-ETSY-001",
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
        "btn_block": "🚫 Bu Numarayı Engelle",
        "tg_title": "CekCekQR BİLDİRİMİ!",
        "tg_plate": "Plaka:",
        "tg_msg": "Mesaj:",
        "tg_prompt": "Durumunuzu bildirmek için butona tıklayın:",
        "reply_title": "CekCekQR - Yanıt Onayı",
        "reply_success": "Yanıtınız kaydedildi:",
        "reply_close": "Bu pencereyi kapatabilirsiniz.",
        "invalid_qr": "Geçersiz veya veritabanında bulunmayan QR Kod.",
        "err_duplicate_plate": "Bu plaka sistemde zaten kayıtlı!",
        "err_invalid_token": "Geçersiz veya daha önce kullanılmış Aktivasyon Kodu!",
        "err_invalid_phone": "Lütfen geçerli ve doğru bir telefon numarası giriniz.",
        "err_blocked": "Bu numaradan bu plakaya bildirim gönderimi engellenmiştir."
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
        "token_label": "Activation Code",
        "token_holder": "e.g., CEK-ETSY-001",
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
        "btn_block": "🚫 Block This Number",
        "tg_title": "CekCekQR NOTIFICATION!",
        "tg_plate": "Plate:",
        "tg_msg": "Message:",
        "tg_prompt": "Click a button below to update status:",
        "reply_title": "CekCekQR - Response Confirmation",
        "reply_success": "Your response has been recorded:",
        "reply_close": "You can close this window.",
        "invalid_qr": "Invalid or missing QR Code.",
        "err_duplicate_plate": "This plate is already registered in the system!",
        "err_invalid_token": "Invalid or already used Activation Code!",
        "err_invalid_phone": "Please enter a valid phone number.",
        "err_blocked": "Notifications from this number to this plate are blocked."
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
        "token_label": "Код активации",
        "token_holder": "Например: CEK-ETSY-001",
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
        "btn_block": "🚫 Заблокировать номер",
        "tg_title": "CekCekQR УВЕДОМЛЕНИЕ!",
        "tg_plate": "Номер:",
        "tg_msg": "Сообщение:",
        "tg_prompt": "Нажмите кнопку ниже для ответа:",
        "reply_title": "CekCekQR - Подтверждение ответа",
        "reply_success": "Ваш ответ записан:",
        "reply_close": "Вы можете закрыть это окно.",
        "invalid_qr": "Недействительный QR-код.",
        "err_duplicate_plate": "Этот номер уже зарегистрирован!",
        "err_invalid_token": "Неверный или уже использованный код!",
        "err_invalid_phone": "Введите действительный номер телефона.",
        "err_blocked": "Уведомления с этого номера заблокированы."
    }
}

selected_lang = st.selectbox("🌐 Language", ["TR", "EN", "RU"], index=0, label_visibility="collapsed")
txt = I18N[selected_lang]

if logo_src:
    st.markdown(f'<div class="brand-container"><img src="{logo_src}" class="brand-logo-img" alt="Logo" /><div class="brand-subtitle">{txt["subtitle"]}</div></div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="brand-container"><h2 style="margin:0; color:#0A192F;">{txt["title"]}</h2><div class="brand-subtitle">{txt["subtitle"]}</div></div>', unsafe_allow_html=True)

def send_telegram_inline_keyboard(chat_id, text, reply_notif_id, lang_dict):
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": lang_dict["btn_coming"], "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action={lang_dict['btn_coming']}"}],
                [{"text": lang_dict["btn_moving"], "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action={lang_dict['btn_moving']}"}],
                [{"text": lang_dict["btn_busy"], "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action={lang_dict['btn_busy']}"}],
                [{"text": lang_dict["btn_block"], "url": f"{APP_BASE_URL}/?reply={reply_notif_id}&action=BLOCK"}]
            ]
        }
    }
    
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.status_code == 200
    except Exception:
        return False

query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)
reply_notif_id = query_params.get("reply", None)
reply_action = query_params.get("action", None)

if reply_notif_id and reply_action:
    st.title(txt["reply_title"])
    if supabase:
        try:
            if reply_action == "BLOCK":
                supabase.table("notifications").update({"status": "ENGELLENDI"}).eq("id", reply_notif_id).execute()
                st.success("Bu numara başarıyla engellendi.")
            else:
                supabase.table("notifications").update({"status": reply_action}).eq("id", reply_notif_id).execute()
                st.success(f"{txt['reply_success']} **{reply_action}**")
            st.info(txt["reply_close"])
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

if qr_vehicle_id:
    st.markdown(f"<div class='form-title'>{txt['notify_header']}</div>", unsafe_allow_html=True)
    
    vehicle = None
    if supabase:
        try:
            res = supabase.table("vehicles").select("*").eq("id", qr_vehicle_id).execute()
            vehicle = res.data[0] if res.data else None
        except Exception as e:
            st.error(f"Error: {e}")

    if vehicle:
        st.success(f"{txt['verified']} **{vehicle['plate']}**")
        
        if "active_notif_id" not in st.session_state:
            st.session_state.active_notif_id = None

        if not st.session_state.active_notif_id:
            sender_phone = st.text_input(txt["sender_phone"], placeholder="+...")
            selected_msg = st.radio("Status:", txt["presets"])

            if st.button(txt["send_btn"]):
                clean_sender_phone = sender_phone.strip()
                
                if not is_valid_phone(clean_sender_phone):
                    st.warning(txt["err_invalid_phone"])
                else:
                    try:
                        recent_check = supabase.table("notifications").select("*").eq("vehicle_id", qr_vehicle_id).eq("sender_phone", clean_sender_phone).order("created_at", desc=True).limit(1).execute()
                        
                        is_blocked = False
                        if recent_check.data:
                            last_notif = recent_check.data[0]
                            if last_notif.get("status") == "ENGELLENDI":
                                is_blocked = True
                            else:
                                last_time = datetime.datetime.fromisoformat(last_notif["created_at"])
                                if (datetime.datetime.now() - last_time).total_seconds() < 120:
                                    st.warning("Lütfen aynı numaradan ard arda bildirim göndermeden önce biraz bekleyiniz (Zaman Sınırı).")
                                    st.stop()

                        if is_blocked:
                            st.error(txt["err_blocked"])
                        else:
                            notif_data = {
                                "vehicle_id": qr_vehicle_id,
                                "incoming_preset": selected_msg,
                                "sender_phone": clean_sender_phone,
                                "status": "BEKLIYOR",
                                "created_at": datetime.datetime.now().isoformat()
                            }
                            insert_res = supabase.table("notifications").insert(notif_data).execute()
                            
                            if insert_res.data:
                                new_notif_id = insert_res.data[0]["id"]
                                st.session_state.active_notif_id = new_notif_id
                                
                                telegram_chat_id = vehicle.get("telegram_chat_id")
                                if telegram_chat_id:
                                    msg_text = (
                                        f"*{txt['tg_title']}*\n\n"
                                        f"*{txt['tg_plate']}* {vehicle['plate']}\n"
                                        f"*{txt['tg_msg']}* {selected_msg}\n\n"
                                        f"_{txt['tg_prompt']}_"
                                    )
                                    send_telegram_inline_keyboard(telegram_chat_id, msg_text, new_notif_id, txt)
                                
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        else:
            st.markdown(f"<div class='info-card'>{txt['waiting']}</div>", unsafe_allow_html=True)
            status_placeholder = st.empty()
            
            for _ in range(60):
                try:
                    check_res = supabase.table("notifications").select("status").eq("id", st.session_state.active_notif_id).execute()
                    if check_res.data:
                        current_status = check_res.data[0]["status"]
                        if current_status != "BEKLIYOR":
                            if current_status == "ENGELLENDI":
                                status_placeholder.error("Bu işlem engellendi.")
                            else:
                                status_placeholder.success(f"**{current_status}**")
                            st.markdown(f"<div class='info-card'>{txt['done']}</div>", unsafe_allow_html=True)
                                
                            if st.button("OK"):
                                st.session_state.active_notif_id = None
                                st.rerun()
                            st.stop()
                except Exception:
                    pass
                
                time.sleep(3)
            
            st.warning("Response timeout.")
            if st.button("Retry"):
                st.session_state.active_notif_id = None
                st.rerun()

    else:
        st.error(txt["invalid_qr"])
else:
    st.markdown(f"<div class='form-title'>{txt['reg_header']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='form-subtitle'>{txt['reg_sub']}</div>", unsafe_allow_html=True)

    with st.form("vehicle_registration_form"):
        plate_input = st.text_input(txt["plate_label"], placeholder=txt["plate_holder"])
        phone_input = st.text_input(txt["phone_label"], placeholder=txt["phone_holder"])
        chat_id_input = st.text_input(txt["chat_id_label"], placeholder=txt["chat_id_holder"])
        token_input = st.text_input(txt["token_label"], placeholder=txt["token_holder"])
        
        submit_btn = st.form_submit_button(txt["submit_btn"])

    if submit_btn:
        if plate_input and phone_input and chat_id_input and token_input:
            clean_plate = plate_input.upper().replace(" ", "")
            clean_token = token_input.strip().upper()
            
            try:
                # 1. MÜKERRER PLAKA KONTROLÜ
                dup_check = supabase.table("vehicles").select("*").eq("plate", clean_plate).execute()
                if dup_check.data:
                    st.error(txt["err_duplicate_plate"])
                else:
                    # 2. TOKEN (AKTİVASYON KODU) KONTROLÜ (Veritabanı Tabanlı)
                    token_query = supabase.table("tokens").select("*").eq("token_code", clean_token).execute()
                    
                    if not token_query.data:
                        st.error(txt["err_invalid_token"])
                    else:
                        token_row = token_query.data[0]
                        
                        # Kod daha önce kullanılmış mı?
                        if token_row.get("is_used") == True:
                            st.error(txt["err_invalid_token"])
                        else:
                            # 3. ARAÇ KAYDINI YAP
                            v_data = {
                                "plate": clean_plate,
                                "phone": phone_input.strip(),
                                "telegram_chat_id": chat_id_input.strip()
                            }
                            res = supabase.table("vehicles").insert(v_data).execute()
                            
                            if res.data:
                                new_id = res.data[0]["id"]
                                
                                # 4. TOKEN'I "KULLANILDI" OLARAK KİLİTLE
                                supabase.table("tokens").update({
                                    "is_used": True,
                                    "used_by_plate": clean_plate
                                }).eq("token_code", clean_token).execute()
                                
                                st.success("Success!")
                                
                                qr_link = f"{APP_BASE_URL}/?v={new_id}"
                                
                                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                                qr.add_data(qr_link)
                                qr.make(fit=True)
                                img = qr.make_image(fill_color="black", back_color="white")
                                
                                buf = BytesIO()
                                img.save(buf, format="PNG")
                                byte_im = buf.getvalue()

                                st.image(byte_im, caption=f"QR: {clean_plate}")
                                st.download_button(
                                    label="Download QR",
                                    data=byte_im,
                                    file_name=f"CekCekQR_{clean_plate}.png",
                                    mime="image/png"
                                )
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill all fields.")

    st.markdown(f"<div class='info-card'>{txt['chat_id_info']}</div>", unsafe_allow_html=True)

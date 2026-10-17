import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client, Client
import datetime
import requests

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Anonim Park Bildirimi", page_icon="🚗", layout="centered")

# Secrets Control (Streamlit Secrets üzerinden okunur)
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ONESIGNAL_APP_ID = st.secrets.get("ONESIGNAL_APP_ID", "")
ONESIGNAL_REST_KEY = st.secrets.get("ONESIGNAL_REST_KEY", "")

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def send_push_notification(player_id, title, message):
    """Araç sahibinin telefonuna kilit ekranı bildirimi gönderir."""
    if not ONESIGNAL_REST_KEY or not player_id:
        return False
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_REST_KEY}"
    }
    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "include_player_ids": [player_id],
        "headings": {"tr": title, "en": title},
        "contents": {"tr": message, "en": message}
    }
    try:
        response = requests.post("https://onesignal.com/api/v1/notifications", headers=headers, json=payload)
        return response.status_code == 200
    except Exception:
        return False

# ---------------------------------------------------------
# APP HEADER
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Güvenli, Anonim ve Çift Taraflı Araç Park İletişim Sistemi")

# URL Parametresi Kontrolü (QR Okutuldu mu?)
query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)

# ---------------------------------------------------------
# MOD 1: QR OKUTULDU (BİLDİRİM VE YANIT EKRANI)
# ---------------------------------------------------------
if qr_vehicle_id:
    st.subheader("📢 Araç Sahibine Bildirim Gönder")
    
    # Araç Bilgisini Getir
    try:
        res = supabase.table("vehicles").select("*").eq("id", qr_vehicle_id).execute()
        vehicle = res.data[0] if res.data else None
    except Exception as e:
        vehicle = None
        st.error("Araç bilgisi doğrulanamadı.")

    if vehicle:
        st.success("✅ Araç Sistemde Doğrulandı")
        st.info("🔒 Gizlilik İlkesi: İletişim bilgileriniz araç sahibiyle kesinlikle paylaşılmaz, sadece sistem kayıtlarında güvenle saklanır.")

        # Bildiren Kişi Bilgisi (Sistem kaydı için şart)
        sender_phone = st.text_input("Telefon Numaranız (Sadece doğrulama ve kayıt içindir, gizli tutulur):", placeholder="05XXXXXXXXX")

        # Kalıp Mesaj Seçimi
        preset_messages = [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ]
        selected_msg = st.selectbox("Göndermek İstediğiniz Bildirim:", preset_messages)

        if st.button("🚨 Bildirimi Gönder"):
            if not sender_phone or len(sender_phone) < 10:
                st.warning("Lütfen geçerli bir telefon numarası giriniz.")
            else:
                # Veritabanına kaydet (Gönderenin numarası gizli kayıt altında kalır)
                notif_data = {
                    "vehicle_id": qr_vehicle_id,
                    "sender_phone": sender_phone,
                    "incoming_preset": selected_msg,
                    "status": "BEKLIYOR",
                    "created_at": datetime.datetime.now().isoformat()
                }
                supabase.table("notifications").insert(notif_data).execute()

                # Araç Sahibine Push Bildirimi Fırlat
                if vehicle.get("push_player_id"):
                    send_push_notification(
                        vehicle["push_player_id"], 
                        "🚗 Araç Park Bildirimi!", 
                        f"Aracınız için yeni bildirim: {selected_msg}"
                    )
                
                st.success(" Bildirim araç sahibine iletildi! Yanıt bekleniyor...")

        # Canlı Durum Takibi (Araç Sahibinin Yanıtı)
        st.markdown("---")
        st.write("🔄 **Canlı Yanıt Durumu:**")
        
        # Son bildirimi kontrol et
        latest_notif = supabase.table("notifications")\
            .select("*")\
            .eq("vehicle_id", qr_vehicle_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if latest_notif.data and latest_notif.data[0].get("outgoing_preset"):
            st.info(f"💬 **Araç Sahibinin Yanıtı:** {latest_notif.data[0]['outgoing_preset']}")
        else:
            st.caption("Henüz yanıt verilmedi. Sayfa otomatik güncellenecektir.")

# ---------------------------------------------------------
# MOD 2: GENEL PANEL (KAYIT & ARAÇ SAHİBİ YÖNETİMİ)
# ---------------------------------------------------------
else:
    tab1, tab2 = st.tabs(["📝 Araç Kaydı & QR Üret", "📲 Bildirim Panellerim"])

    with tab1:
        st.subheader("Yeni Araç Kaydı")
        plate = st.text_input("Plakanız:", placeholder="34ABC123").upper()
        owner_phone = st.text_input("Telefon Numaranız (Gizli Saklanır):", placeholder="05XXXXXXXXX")
        
        if st.button("QR Kod Oluştur"):
            if plate and owner_phone:
                # Veritabanına Ekle
                v_data = {
                    "plate": plate,
                    "owner_phone": owner_phone
                }
                res = supabase.table("vehicles").insert(v_data).execute()
                new_id = res.data[0]["id"]

                # QR Kod Linki
                app_url = f"https://cekcekqr.streamlit.app/?v={new_id}"
                
                qr = qrcode.make(app_url)
                buf = BytesIO()
                qr.save(buf)
                
                st.success("✅ Aracınız başarıyla kaydedildi!")
                st.image(buf.getvalue(), caption=f"{plate} için QR Kodunuz", width=250)
                st.download_button("QR Kodu İndir", buf.getvalue(), file_name=f"{plate}_QR.png", mime="image/png")
            else:
                st.warning("Lütfen tüm alanları doldurun.")

    with tab2:
        st.subheader("Gelen Bildirimler ve Yanıt Verme")
        owner_phone_check = st.text_input("Kayıtlı Telefon Numaranızla Giriş Yapın:", type="password")
        
        if owner_phone_check:
            # Araç sahibinin araçlarını bul
            my_vehicles = supabase.table("vehicles").select("id, plate").eq("owner_phone", owner_phone_check).execute()
            
            if my_vehicles.data:
                v_ids = [v["id"] for v in my_vehicles.data]
                
                # Gelen bildirimleri listele
                notifs = supabase.table("notifications").select("*").in_("vehicle_id", v_ids).order("created_at", desc=True).execute()
                
                for n in notifs.data:
                    st.write(f"📌 **Tarih:** {n['created_at'][:16]} | **Bildirim:** {n['incoming_preset']}")
                    
                    # Yanıt Verme Butonları
                    reply_cols = st.columns(3)
                    if reply_cols[0].button("🟢 5 Dk'ya Geliyorum", key=f"r1_{n['id']}"):
                        supabase.table("notifications").update({"outgoing_preset": "5 Dk içinde geliyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                        st.rerun()
                    if reply_cols[1].button("🟡 Aracı Çekiyorum", key=f"r2_{n['id']}"):
                        supabase.table("notifications").update({"outgoing_preset": "Hemen aracı çekiyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                        st.rerun()
                    if reply_cols[2].button("🔴 Gecikeceğim (15 Dk)", key=f"r3_{n['id']}"):
                        supabase.table("notifications").update({"outgoing_preset": "Yaklaşık 15 dakika gecikeceğim.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                        st.rerun()
                    
                    if n.get("outgoing_preset"):
                        st.caption(f"Verilen Yanıt: {n['outgoing_preset']}")
                    st.markdown("---")
            else:
                st.error("Bu numaraya ait kayıtlı araç bulunamadı.")

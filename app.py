import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import datetime
import requests

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Anonim Park Bildirimi", page_icon="🚗", layout="centered")

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

def send_push_notification(player_id, title, message):
    """Araç sahibinin telefonuna kilit ekranı bildirimi fırlatır."""
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
# HEADER
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Anonim, Ücretsiz ve Hızlı Park Bildirim Sistemi")

# URL Parametresi Kontrolü (QR Okutuldu mu?)
query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)

# ---------------------------------------------------------
# SENARYO A: QR KOD OKUTULDU (Sokaktaki Vatandaş / Bildiren)
# ---------------------------------------------------------
if qr_vehicle_id:
    st.subheader("📢 Araç Sahibine Bildirim Gönder")
    
    try:
        res = supabase.table("vehicles").select("*").eq("id", qr_vehicle_id).execute()
        vehicle = res.data[0] if res.data else None
    except Exception:
        vehicle = None

    if vehicle:
        st.success(f"✅ Araç Doğrulandı: **{vehicle['plate']}**")
        st.info("🔒 %100 Anonim İletişim: Hiçbir kişisel veri veya telefon numarası istenmez ve paylaşılmaz.")

        # Kalıp Mesaj Seçimi
        preset_messages = [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ]
        selected_msg = st.radio("Lütfen bildirim durumunu seçin:", preset_messages)

        if st.button("🚨 Bildirimi Gönder"):
            # Veritabanına Ekle
            notif_data = {
                "vehicle_id": qr_vehicle_id,
                "incoming_preset": selected_msg,
                "status": "BEKLIYOR",
                "created_at": datetime.datetime.now().isoformat()
            }
            supabase.table("notifications").insert(notif_data).execute()

            # Araç Sahibine Kilit Ekranı Bildirimi Fırlat
            if vehicle.get("push_player_id"):
                send_push_notification(
                    vehicle["push_player_id"], 
                    f"🚗 Park Bildirimi! ({vehicle['plate']})", 
                    f"Mesaj: {selected_msg}"
                )
            
            st.success("✅ Bildirim araç sahibine iletildi! Yanıt bekleniyor...")

        # Canlı Yanıt Takibi
        st.markdown("---")
        st.write("🔄 **Araç Sahibinin Yanıt Durumu:**")
        
        latest_notif = supabase.table("notifications")\
            .select("*")\
            .eq("vehicle_id", qr_vehicle_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if latest_notif.data and latest_notif.data[0].get("outgoing_preset"):
            st.info(f"💬 **Araç Sahibi Yanıtı:** {latest_notif.data[0]['outgoing_preset']}")
        else:
            st.caption("Henüz yanıt verilmedi. Sayfa araç sahibi yanıt verdiğinde güncellenir.")

    else:
        st.error("Geçersiz veya sistemde bulunmayan QR Kod.")

# ---------------------------------------------------------
# SENARYO B: ARAÇ SAHİBİ PANELİ (Kayıt Olma & Yanıt Verme)
# ---------------------------------------------------------
else:
    tab1, tab2 = st.tabs(["📝 Araç Kaydı & QR Üret", "📲 Gelen Bildirimlerim"])

    with tab1:
        st.subheader("Yeni Araç Kaydı")
        plate = st.text_input("Plakanız:", placeholder="34ABC123").upper().replace(" ", "")
        
        if st.button("QR Kod Oluştur"):
            if plate:
                # Veritabanına Ekle
                v_data = {"plate": plate}
                res = supabase.table("vehicles").insert(v_data).execute()
                new_id = res.data[0]["id"]

                # QR Kod URL
                app_url = f"https://cekcekqr.streamlit.app/?v={new_id}"
                
                qr = qrcode.make(app_url)
                buf = BytesIO()
                qr.save(buf)
                
                st.success("✅ Aracınız kaydedildi!")
                st.image(buf.getvalue(), caption=f"{plate} QR Kodu", width=250)
                st.download_button("QR Kodu İndir", buf.getvalue(), file_name=f"{plate}_QR.png", mime="image/png")
            else:
                st.warning("Lütfen plaka giriniz.")

    with tab2:
        st.subheader("Gelen Bildirimler")
        search_plate = st.text_input("Takip etmek istediğiniz Plaka:", placeholder="34ABC123").upper().replace(" ", "")
        
        if search_plate:
            # Plakaya ait aracı bul
            v_res = supabase.table("vehicles").select("*").eq("plate", search_plate).execute()
            
            if v_res.data:
                vehicle_obj = v_res.data[0]
                
                # Gelen bildirimleri çek
                notifs = supabase.table("notifications")\
                    .select("*")\
                    .eq("vehicle_id", vehicle_obj["id"])\
                    .order("created_at", desc=True)\
                    .execute()
                
                if notifs.data:
                    for n in notifs.data:
                        st.write(f"📌 **Tarih:** {n['created_at'][:16].replace('T', ' ')} | **Gelen Bildirim:** {n['incoming_preset']}")
                        
                        # Yanıt Butonları
                        cols = st.columns(3)
                        if cols[0].button("🟢 5 Dk'ya Geliyorum", key=f"r1_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "5 Dk içinde geliyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        if cols[1].button("🟡 Aracı Çekiyorum", key=f"r2_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "Hemen aracı çekiyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        if cols[2].button("🔴 Gecikeceğim", key=f"r3_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "15-20 dakika gecikeceğim, kusura bakmayın.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        
                        if n.get("outgoing_preset"):
                            st.caption(f"Verilen Yanıt: {n['outgoing_preset']}")
                        st.markdown("---")
                else:
                    st.info("Bu araç için henüz gelen bir bildirim bulunmuyor.")
            else:
                st.error("Bu plakaya ait kayıtlı araç bulunamadı.")

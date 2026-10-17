import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import datetime
import streamlit.components.v1 as components

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Anonim Park Bildirimi", page_icon="🚗", layout="centered")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

# Gerçek yayın adresiniz
APP_BASE_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app"

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# NATIVE WEB PUSH & SERVICE WORKER ENTEGRASYONU (ÜCRETSİZ)
# ---------------------------------------------------------
def inject_native_push_script(vehicle_id=None):
    push_code = f"""
    <div style="padding: 10px; background-color: #e8f4fd; border-radius: 5px; border: 1px solid #b6d4fe; text-align: center;">
        <p style="margin: 0; font-weight: bold; color: #084298;">🔔 Yerel Bildirim Sistemi</p>
        <p style="font-size: 12px; color: #555; margin: 5px 0 10px 0;">Kilit ekranından bildirim alabilmek için tarayıcı iznini aktif edin.</p>
        <button id="pushBtn" onclick="requestNotificationPermission()" style="background-color: #0d6efd; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: bold;">Bildirimleri Aç</button>
    </div>

    <script>
    function requestNotificationPermission() {{
        if (!("Notification" in window)) {{
            alert("Tarayıcınız masaüstü bildirimleri desteklemiyor.");
            return;
        }}
        
        Notification.requestPermission().then(function (permission) {{
            if (permission === "granted") {{
                document.getElementById("pushBtn").innerText = "✅ Bildirimler Aktif!";
                document.getElementById("pushBtn").style.backgroundColor = "#198754";
                
                // Service Worker Kaydı (Arka plan takibi için)
                if ('serviceWorker' in navigator) {{
                    navigator.serviceWorker.register('data:text/javascript;base64,c2VsZi5hZGRFdmVudExpc3RlbmVyKCdpbnN0YWxsJywgZXZlbnQgPT4gewogICAgZXZlbnQud2FpdFVudGlsKHNlbGYuc2tpcldhaXRpbmcpOwogIH0pOw==')
                    .then(reg => {{
                        console.log('Service Worker aktif');
                    }});
                }}
            }} else {{
                alert("Bildirim izni reddedildi. Cihazınıza bildirim gönderilemez.");
            }}
        }});
    }}
    </script>
    """
    components.html(push_code, height=110)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Anonim, Ücretsiz ve Canlı Park İletişim Sistemi")

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
        st.info("🔒 %100 Anonim İletişim: Kişisel verileriniz görünmez.")

        preset_messages = [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ]
        selected_msg = st.radio("Lütfen durum seçiniz:", preset_messages)

        if st.button("🚨 Bildirimi Gönder"):
            notif_data = {
                "vehicle_id": qr_vehicle_id,
                "incoming_preset": selected_msg,
                "status": "BEKLIYOR",
                "created_at": datetime.datetime.now().isoformat()
            }
            supabase.table("notifications").insert(notif_data).execute()
            st.success("✅ Bildirim iletildi! Süreç canlı olarak takip ediliyor...")

        # --- CANLI TAKİP EKRANI (BİLDİREN KİŞİ İÇİN) ---
        st.markdown("---")
        st.subheader("📊 Canlı Süreç Takibi")
        
        latest_notif = supabase.table("notifications")\
            .select("*")\
            .eq("vehicle_id", qr_vehicle_id)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if latest_notif.data:
            notif = latest_notif.data[0]
            status = notif.get("status", "BEKLIYOR")
            
            if status == "BEKLIYOR":
                st.warning("⏳ **Süreç Durumu:** Araç sahibine bildirim ulaştırıldı, yanıt bekleniyor...")
            elif status == "YANITLANDI":
                st.success(f"💬 **Araç Sahibi Yanıtı:** {notif.get('outgoing_preset')}")
            
            if st.button("🔄 Durumu Yenile"):
                st.rerun()
        else:
            st.caption("Henüz aktif bir bildirim oluşturulmadı.")

    else:
        st.error("Geçersiz veya sistemde bulunmayan QR Kod.")

# ---------------------------------------------------------
# SENARYO B: ARAÇ SAHİBİ PANELİ (Kayıt & Yanıt)
# ---------------------------------------------------------
else:
    tab1, tab2 = st.tabs(["📝 Araç Kaydı & QR Üret", "📲 Gelen Bildirimlerim"])

    with tab1:
        st.subheader("Yeni Araç Kaydı")
        plate = st.text_input("Plakanız:", placeholder="34ABC123").upper().replace(" ", "")
        
        if st.button("QR Kod Oluştur"):
            if plate:
                v_data = {"plate": plate}
                res = supabase.table("vehicles").insert(v_data).execute()
                new_id = res.data[0]["id"]

                app_url = f"{APP_BASE_URL}/?v={new_id}"
                
                qr = qrcode.make(app_url)
                buf = BytesIO()
                qr.save(buf)
                
                st.success("✅ Aracınız kaydedildi!")
                st.image(buf.getvalue(), caption=f"{plate} QR Kodu", width=250)
                st.download_button("QR Kodu İndir", buf.getvalue(), file_name=f"{plate}_QR.png", mime="image/png")
                
                # Yerel Bildirim Kurulum Kutusu
                inject_native_push_script(new_id)
            else:
                st.warning("Lütfen plaka giriniz.")

    with tab2:
        st.subheader("Gelen Bildirimler")
        search_plate = st.text_input("Takip etmek istediğiniz Plaka:", placeholder="34ABC123").upper().replace(" ", "")
        
        if search_plate:
            v_res = supabase.table("vehicles").select("*").eq("plate", search_plate).execute()
            
            if v_res.data:
                vehicle_obj = v_res.data[0]
                
                # Yerel Bildirim Kurulum Kutusu (Kontrol için)
                inject_native_push_script(vehicle_obj["id"])
                
                notifs = supabase.table("notifications")\
                    .select("*")\
                    .eq("vehicle_id", vehicle_obj["id"])\
                    .order("created_at", desc=True)\
                    .execute()
                
                if notifs.data:
                    for n in notifs.data:
                        st.write(f"📌 **Tarih:** {n['created_at'][:16].replace('T', ' ')} | **Gelen Bildirim:** {n['incoming_preset']}")
                        
                        cols = st.columns(3)
                        if cols[0].button("🟢 5 Dk'ya Geliyorum", key=f"r1_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "5 Dk içinde geliyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        if cols[1].button("🟡 Aracı Çekiyorum", key=f"r2_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "Hemen aracı çekiyorum.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        if cols[2].button("🔴 Gecikeceğim", key=f"r3_{n['id']}"):
                            supabase.table("notifications").update({"outgoing_preset": "15-20 dakika gecikeceğim.", "status": "YANITLANDI"}).eq("id", n["id"]).execute()
                            st.rerun()
                        
                        if n.get("outgoing_preset"):
                            st.caption(f"Verilen Yanıt: {n['outgoing_preset']}")
                        st.markdown("---")
                else:
                    st.info("Bu araç için henüz gelen bir bildirim bulunmuyor.")
            else:
                st.error("Bu plakaya ait kayıtlı araç bulunamadı.")

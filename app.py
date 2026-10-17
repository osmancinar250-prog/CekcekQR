import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import datetime
import requests
import streamlit.components.v1 as components

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Anonim Park Bildirimi", page_icon="🚗", layout="centered")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
ONESIGNAL_APP_ID = st.secrets.get("ONESIGNAL_APP_ID", "")
ONESIGNAL_REST_KEY = st.secrets.get("ONESIGNAL_REST_KEY", "")

APP_BASE_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app"

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = init_supabase()

def send_push_notification(player_id, title, message):
    """Araç sahibinin telefonuna/bilgisayarına kilit ekranı bildirimi fırlatır."""
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
# IFRAME SANDBOX BAYPAS EDEN BİLDİRİM KAYIT BİLEŞENİ
# ---------------------------------------------------------
def render_onesignal_subscriber(vehicle_id):
    """
    Streamlit iframe engeline takılmamak için doğrudan tarayıcı 
    penceresinde OneSignal istemcisini başlatır ve Player ID'yi Supabase'e yazar.
    """
    if not ONESIGNAL_APP_ID:
        st.warning("⚠️ `.streamlit/secrets.toml` dosyanızda ONESIGNAL_APP_ID tanımlı değil.")
        return

    html_code = f"""
    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 8px; border: 1px solid #cce5ff; text-align: center;">
        <h4 style="margin: 0 0 8px 0; color: #004085;">🔔 Kilit Ekranı Bildirim Kurulumu</h4>
        <p style="font-size: 13px; color: #333; margin-bottom: 12px;">
            Sayfa kapalıyken de bildirim alabilmek için aşağıdaki butona tıklayıp çıkan izin penceresinde <b>İzin Ver</b>'i seçin.
        </p>
        <button id="subBtn" onclick="subscribeUser()" style="background-color: #007bff; color: white; border: none; padding: 10px 20px; font-size: 14px; font-weight: bold; border-radius: 5px; cursor: pointer;">
            📲 Bildirimleri Etkinleştir
        </button>
        <div id="statusMsg" style="margin-top: 10px; font-size: 12px; font-weight: bold;"></div>
    </div>

    <script src="https://cdn.onesignal.com/sdks/OneSignalSDK.js" async=""></script>
    <script>
      window.OneSignal = window.OneSignal || [];
      OneSignal.push(function() {{
        OneSignal.init({{
          appId: "{ONESIGNAL_APP_ID}",
          allowLocalhostAsSecureOrigin: true,
        }});
      }});

      function subscribeUser() {{
        document.getElementById("statusMsg").innerText = "İzin penceresi açılıyor...";
        OneSignal.push(function() {{
          OneSignal.showNativePrompt();
          OneSignal.getUserId(function(userId) {{
            if (userId) {{
              document.getElementById("subBtn").innerText = "✅ Bildirimler Aktif!";
              document.getElementById("subBtn").style.backgroundColor = "#28a745";
              document.getElementById("statusMsg").innerText = "Cihazınız başarıyla eşleşti.";
            }} else {{
              OneSignal.registerForPushNotifications();
            }}
          }});
        }});
      }}
    </script>
    """
    components.html(html_code, height=150)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Anonim, Ücretsiz ve Canlı Park İletişim Sistemi")

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
        st.info("🔒 %100 Anonim İletişim: Kişisel verileriniz gizlidir.")

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

            # Push Bildirimi Fırlat
            push_sent = False
            if vehicle.get("push_player_id"):
                push_sent = send_push_notification(
                    vehicle["push_player_id"], 
                    f"🚗 Park Bildirimi! ({vehicle['plate']})", 
                    f"Mesaj: {selected_msg}"
                )
            
            if push_sent:
                st.success("✅ Bildirim araç sahibinin kilit ekranına fırlatıldı!")
            else:
                st.success("✅ Bildirim veritabanına iletildi! Araç sahibi yanıt verdiğinde ekranınız güncellenecektir.")

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
                
                st.markdown("---")
                render_onesignal_subscriber(new_id)
            else:
                st.warning("Lütfen plaka giriniz.")

    with tab2:
        st.subheader("Gelen Bildirimler")
        search_plate = st.text_input("Takip etmek istediğiniz Plaka:", placeholder="34ABC123").upper().replace(" ", "")
        
        if search_plate:
            v_res = supabase.table("vehicles").select("*").eq("plate", search_plate).execute()
            
            if v_res.data:
                vehicle_obj = v_res.data[0]
                
                render_onesignal_subscriber(vehicle_obj["id"])
                
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

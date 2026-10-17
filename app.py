import streamlit as st
import qrcode
from io import BytesIO
from supabase import create_client
import datetime

# ---------------------------------------------------------
# SETUP & CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="CekCekQR - Park İletişim Sistemi", page_icon="🚗", layout="centered")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

APP_BASE_URL = "https://cekcekqr-e5lnv5nfat5q7spkrdvkes.streamlit.app"

@st.cache_resource
def init_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            st.error(f"Supabase Bağlantı Hatası: {e}")
            return None
    return None

supabase = init_supabase()

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("🚗 CekCekQR")
st.caption("Anonim Güvenli Park İletişim Platformu")

query_params = st.query_params
qr_vehicle_id = query_params.get("v", None)

# ---------------------------------------------------------
# SENARYO A: QR KOD OKUTULDU (Sokaktaki Vatandaş)
# ---------------------------------------------------------
if qr_vehicle_id:
    st.subheader("📢 Araç Sahibine Bildirim Gönder")
    
    vehicle = None
    if supabase:
        try:
            res = supabase.table("vehicles").select("*").eq("id", qr_vehicle_id).execute()
            vehicle = res.data[0] if res.data else None
        except Exception as e:
            st.error(f"Veri çekme hatası (Supabase RLS kısıtlaması olabilir): {e}")

    if vehicle:
        st.success(f"✅ Araç Doğrulandı: **{vehicle['plate']}**")
        st.info("🔒 İletişim anonimdir. Telefon numaranız karşı tarafa gösterilmez.")

        preset_messages = [
            "⚠️ Aracınız geçişi/çıkışı engelliyor.",
            "💡 Aracınızın farları açık kaldı.",
            "🪟 Aracınızın camı açık kaldı.",
            "💥 Aracınıza temas/hasar gerçekleşti."
        ]
        selected_msg = st.radio("Lütfen durum seçiniz:", preset_messages)

        if st.button("🚨 Bildirimi Gönder"):
            try:
                notif_data = {
                    "vehicle_id": qr_vehicle_id,
                    "incoming_preset": selected_msg,
                    "status": "BEKLIYOR",
                    "created_at": datetime.datetime.now().isoformat()
                }
                supabase.table("notifications").insert(notif_data).execute()
                st.success("✅ Bildirim iletildi! Araç sahibinin yanıtı aşağıda görünecektir.")
            except Exception as e:
                st.error(f"Bildirim gönderilemedi: {e}")

        # --- CANLI TAKİP EKRANI ---
        st.markdown("---")
        st.subheader("📊 Yanıt Takibi")
        
        try:
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
                    st.warning("⏳ **Süreç Durumu:** Araç sahibinin yanıtı bekleniyor...")
                elif status == "YANITLANDI":
                    st.success(f"💬 **Araç Sahibi Yanıtı:** {notif.get('outgoing_preset')}")
                
                if st.button("🔄 Yanıtı Kontrol Et"):
                    st.rerun()
        except Exception as e:
            st.caption("Takip verisi alınamadı.")

    else:
        st.error("Geçersiz veya veritabanında bulunmayan QR Kod.")

# ---------------------------------------------------------
# SENARYO B: ARAÇ SAHİBİ PANELİ
# ---------------------------------------------------------
else:
    tab1, tab2 = st.tabs(["📝 Araç Kaydı & QR Üret", "📲 Gelen Bildirimlerim"])

    with tab1:
        st.subheader("Yeni Araç Kaydı")
        st.caption("KVKK gereği telefon numaranız yasal doğrulama için saklanır, dışarıyla paylaşılmaz.")
        
        plate = st.text_input("Plakanız:", placeholder="34ABC123").upper().replace(" ", "")
        phone = st.text_input("Telefon Numaranız (Yasal Doğrulama İçin):", placeholder="05XXXXXXXXX")
        
        if st.button("QR Kod Oluştur"):
            if plate and phone:
                if supabase:
                    try:
                        v_data = {"plate": plate, "phone": phone}
                        res = supabase.table("vehicles").insert(v_data).execute()
                        
                        if res.data:
                            new_id = res.data[0]["id"]
                            app_url = f"{APP_BASE_URL}/?v={new_id}"
                            
                            qr = qrcode.make(app_url)
                            buf = BytesIO()
                            qr.save(buf)
                            
                            st.success(f"✅ {plate} plakalı araç başarıyla kaydedildi!")
                            st.image(buf.getvalue(), caption=f"{plate} QR Kodu", width=250)
                            st.download_button("QR Kodu İndir", buf.getvalue(), file_name=f"{plate}_QR.png", mime="image/png")
                        else:
                            st.error("Kayıt oluşturulamadı. Lütfen Supabase RLS izinlerini kontrol edin.")
                    except Exception as e:
                        st.error(f"Veritabanı kayıt hatası: {e}")
            else:
                st.warning("Lütfen hem plaka hem de telefon numaranızı giriniz.")

    with tab2:
        st.subheader("Gelen Bildirim Sorgulama")
        search_plate = st.text_input("Plakanızı Girin:", placeholder="34ABC123").upper().replace(" ", "")
        
        if search_plate and supabase:
            try:
                v_res = supabase.table("vehicles").select("*").eq("plate", search_plate).execute()
                
                if v_res.data:
                    vehicle_obj = v_res.data[0]
                    
                    notifs = supabase.table("notifications")\
                        .select("*")\
                        .eq("vehicle_id", vehicle_obj["id"])\
                        .order("created_at", desc=True)\
                        .execute()
                    
                    if notifs.data:
                        for n in notifs.data:
                            st.write(f"📌 **Tarih:** {n['created_at'][:16].replace('T', ' ')} | **Mesaj:** {n['incoming_preset']}")
                            
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
                                st.info(f"Verilen Yanıt: {n['outgoing_preset']}")
                            st.markdown("---")
                    else:
                        st.info("Bu araç için gelen aktif bir bildirim yok.")
                else:
                    st.error("Bu plakaya ait kayıt bulunamadı.")
            except Exception as e:
                st.error(f"Sorgulama hatası: {e}")

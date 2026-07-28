from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import datetime
import shutil
import os
import math

app = FastAPI(title="Altınköy Otonom Sistem", version="3.1.0")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

whatsapp_feed = []
incident_logs = []

# Başlangıç Belediye Personel Listesi
STAFF_LIST = [
    {"id": 1, "name": "Fırat Reis", "title": "Su Değirmeninde Güvenlik", "lat": 39.9334, "lon": 32.8597, "phone": "05536915752"},
    {"id": 2, "name": "Onur Yılmaz", "title": "Peyzaj Sorumlusu", "lat": 39.9350, "lon": 32.8550, "phone": "05379393677"},
    {"id": 3, "name": "Hakan Taşkale", "title": "Peyzaj Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "05468016172"}
]

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)*2 + (lon1 - lon2)*2)

@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <html>
        <head>
            <title>Altınköy Akıllı Operasyon</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background: linear-gradient(135deg, #f4f6f9, #e4e9f2); padding: 30px; margin: 0; }
                .card { background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0px 10px 25px rgba(0,0,0,0.08); display: inline-block; max-width: 450px; width: 100%; }
                h2 { color: #2c3e50; margin-bottom: 5px; }
                p { color: #7f8c8d; margin-bottom: 25px; }
                a { display: block; background: #2c3e50; color: white; padding: 16px; margin: 12px 0; text-decoration: none; border-radius: 10px; font-weight: bold; transition: 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                a:hover { transform: translateY(-2px); opacity: 0.95; }
                a.whatsapp { background: #25D366; }
                a.emergency { background: #E74C3C; }
                a.staff { background: #8e44ad; }
                a.dashboard { background: #34495E; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🌾 Altınköy Otonom Sistem</h2>
                <p>Akıllı Saha Operasyon ve Yönetim Paneli</p>
                <a class="staff" href="/staff-management">👥 Belediye Çalışanları Kayıt & Yönetimi</a>
                <a class="whatsapp" href="/whatsapp-sim">📱 WhatsApp Grup Entegrasyon Paneli</a>
                <a class="emergency" href="/visitor-portal">🚶 Ziyaretçi Acil Durum / QR Portalı</a>
                <a class="dashboard" href="/live-dashboard">📊 Müdürlük Canlı Rapor & Takip</a>
            </div>
        </body>
    </html>
    """

@app.get("/staff-management", response_class=HTMLResponse)
def staff_management_page():
    staff_rows = ""
    for s in STAFF_LIST:
        staff_rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px; text-align: left;"><b>{s['name']}</b><br><span style="font-size:12px; color:#7f8c8d;">{s['title']}</span></td>
            <td style="padding: 10px;">{s['phone']}</td>
            <td style="padding: 10px; font-size: 12px; color:#555;">Lat: {s['lat']}<br>Lon: {s['lon']}</td>
        </tr>
        """

    return f"""
    <html>
        <head><title>Personel Yönetimi</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background: #f4f6f9; margin: 0;">
            <div style="max-width: 600px; margin: auto;">
                <h2>👥 Altınköy Saha Personel Kayıt Paneli</h2>
                <p style="color: #666; font-size: 14px;">Acil durumlarda konumunuza en yakın yönlendirilecek aktif belediye çalışanları aşağıdadır.</p>
                
                <div style="background: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h4 style="margin-top:0; color:#2c3e50;">➕ Yeni Personel Ekle</h4>
                    <form action="/api/add-staff" method="POST">
                        <label style="font-size:13px; font-weight:bold; color:#555;">Çalışan Adı Soyadı:</label><br>
                        <input type="text" name="name" placeholder="Örn: Mustafa Çiftçi" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;"><br>
                        
                        <label style="font-size:13px; font-weight:bold; color:#555;">Görevi / Unvanı:</label><br>
                        <input type="text" name="title" placeholder="Örn: Park ve Bahçeler Sorumlusu" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;"><br>

                        <label style="font-size:13px; font-weight:bold; color:#555;">Telefon Numarası:</label><br>
                        <input type="text" name="phone" placeholder="Örn: 0555 444 5566" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;"><br>
                        
                        <div style="display: flex; gap: 10px;">
                            <div style="flex: 1;">
                                <label style="font-size:12px; font-weight:bold; color:#555;">Enlem (Lat):</label>
                                <input type="text" name="lat" value="39.9334" required style="width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                            </div>
                            <div style="flex: 1;">
                                <label style="font-size:12px; font-weight:bold; color:#555;">Boylam (Lon):</label>
                                <input type="text" name="lon" value="32.8597" required style="width: 100%; padding: 8px; margin-top: 4px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                            </div>
                        </div>
                        <br>
                        <button type="submit" style="background: #8e44ad; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">Sisteme Personel Kaydet</button>
                    </form>
                </div>

                <div style="background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h3 style="margin-top:0; color: #2c3e50;">📋 Kayıtlı Saha Personeli Listesi ({len(STAFF_LIST)})</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        {staff_rows}
                    </table>
                </div>
                <br>
                <a href="/" style="display: block; text-align: center; background: #2c3e50; color: white; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/add-staff")
def add_staff(name: str = Form(...), title: str = Form(...), phone: str = Form(...), lat: float = Form(...), lon: float = Form(...)):
    STAFF_LIST.append({
        "id": len(STAFF_LIST) + 1,
        "name": name,
        "title": title,
        "lat": lat,
        "lon": lon,
        "phone": phone
    })
    return RedirectResponse(url="/staff-management", status_code=303)

@app.get("/whatsapp-sim", response_class=HTMLResponse)
def whatsapp_sim_page():
    feed_html = ""
    for item in reversed(whatsapp_feed):
        feed_html += f"""
        <div style="background: white; border: 1px solid #e1e8ed; padding: 15px; margin-bottom: 12px; border-radius: 10px; text-align: left; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <b>👤 {item['sender']}</b> <span style="font-size: 11px; color: gray; float: right;">{item['time']}</span><br>
            <p style="margin: 8px 0; color: #333;">💬 {item['message']}</p>
            {"<img src='" + item['image_url'] + "' style='max-width: 100%; border-radius: 8px; margin-top: 5px;'/>" if item['image_url'] else ""}
            <div style="margin-top: 10px; font-size: 12px; background: #f0f4f8; padding: 6px 10px; border-radius: 6px; color: #2c3e50;">
                🤖 <b>Yapay Zeka Etiketi:</b> <span style="color: #27ae60; font-weight: bold;">{item['ai_tag']}</span>
            </div>
        </div>
        """

    return f"""
    <html>
        <head><title>WhatsApp Grup Akışı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background: #efeae2; margin: 0;">
            <div style="max-width: 600px; margin: auto;">
                <h2>💬 "Altınköy Genel İşler" WhatsApp Akışı</h2>
                <p style="color: #555; font-size: 14px;">Personel saha paylaşımları yapay zeka tarafından otomatik sınıflandırılır.</p>
                
                <div style="background: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h4 style="margin-top:0; color:#2c3e50;">➕ Gruba Bildirim Gönder</h4>
                    <form action="/api/whatsapp-post" method="POST" enctype="multipart/form-data">
                        <label style="font-size:13px; font-weight:bold; color:#555;">Gönderen:</label><br>
                        <input type="text" name="sender" value="Fatih Altınköy Amir" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;"><br>
                        
                        <label style="font-size:13px; font-weight:bold; color:#555;">Mesaj / Açıklama:</label><br>
                        <input type="text" name="message" placeholder="Örn: Kepçe geldi kamyonda geliyo" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;"><br>
                        
                        <label style="font-size:13px; font-weight:bold; color:#555;">Saha Fotoğrafı:</label><br>
                        <input type="file" name="file" accept="image/*" style="width: 100%; margin: 5px 0 15px 0;"><br>
                        
                        <button type="submit" style="background: #128c7e; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;">WhatsApp Grubuna Gönder</button>
                    </form>
                </div>

                <h3 style="color: #2c3e50;">📜 Anlık Akış</h3>
                {feed_html if feed_html else "<p style='color: gray; text-align:center;'>Henüz mesaj akışı yok.</p>"}
                <br>
                <a href="/" style="display: block; text-align: center; background: #2c3e50; color: white; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/whatsapp-post", response_class=HTMLResponse)
async def process_whatsapp_post(sender: str = Form(...), message: str = Form(...), file: Optional[UploadFile] = File(None)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_url = None
    
    if file and file.filename:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_url = f"/{file_path}"

    ai_tag = "Genel Saha Çalışması"
    msg_lower = message.lower()
    if "kepçe" in msg_lower or "kamyon" in msg_lower or "hafriyat" in msg_lower:
        ai_tag = "Altyapı / Yol Çalışması (Ağır Vasıta)"
    elif "dere" in msg_lower or "su" in msg_lower:
        ai_tag = "Dere Islah / Su Kontrolü"
    elif "çim" in msg_lower or "sulama" in msg_lower:
        ai_tag = "Peyzaj / Bakım"

    whatsapp_feed.append({
        "sender": sender,
        "message": message,
        "image_url": image_url,
        "time": timestamp,
        "ai_tag": ai_tag
    })

    return f"""
    <html>
        <head><title>Başarılı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); text-align: center; max-width: 400px; width: 90%;">
                <div style="font-size: 50px; margin-bottom: 15px;">🎉</div>
                <h2 style="color: #27ae60; margin-top: 0;">Bildirim Gruba İletildi!</h2>
                <p style="color: #666; font-size: 14px; line-height: 1.5;">Mesajınız ve medya içeriğiniz yapay zeka tarafından başarıyla etiketlenip rapor sistemine işlendi.</p>
                <div style="background: #eef2f7; padding: 10px; border-radius: 8px; font-size: 13px; color: #333; margin: 20px 0;">
                    🤖 <b>Atanan AI Etiketi:</b> {ai_tag}
                </div>
                <a href="/whatsapp-sim" style="display: block; background: #128c7e; color: white; padding: 12px; text-decoration: none; border-radius: 8px; font-weight: bold;">WhatsApp Paneline Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/visitor-portal", response_class=HTMLResponse)
def visitor_portal():
    return """
    <html>
        <head><title>Ziyaretçi Acil Durum</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff5f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(231,76,60,0.1); text-align: center; max-width: 400px; width: 90%;">
                <div style="font-size: 45px; margin-bottom: 10px;">🚨</div>
                <h2 style="color: #c0392b; margin-top:0;">Acil Durum & Konum Bildirimi</h2>
                <p style="color: #666; font-size: 14px; line-height: 1.5;">1 Milyon metrekarelik alanda yardıma mı ihtiyacınız var? Konumunuzu tek tıkla kayıtlı en yakın belediye personeline iletin.</p>
                
                <button onclick="sendEmergency()" style="background: #e74c3c; color: white; padding: 16px 20px; font-size: 16px; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%; box-shadow: 0 4px 10px rgba(231,76,60,0.3); transition: 0.2s;">📍 Konumumu En Yakın Eki̇be Gönder</button>
                
                <p id="status" style="margin-top: 20px; font-weight: bold; font-size: 14px;"></p>
                <br>
                <a href="/" style="color: #7f8c8d; text-decoration: none; font-size: 13px; font-weight: bold;">← Ana Sayfaya Dön</a>
            </div>
            <script>
                function sendEmergency() {
                    const statusEl = document.getElementById('status');
                    statusEl.innerText = "Konum alınıyor ve en yakın personel hesaplanıyor...";
                    statusEl.style.color = "#e67e22";
                    
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(position => {
                            fetch('/api/emergency', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({
                                    visitor_id: "Ziyaretci_" + Math.floor(Math.random() * 1000),
                                    latitude: position.coords.latitude,
                                    longitude: position.coords.longitude,
                                    description: "Ziyaretçi acil konum sinyali gönderdi."
                                })
                            }).then(res => res.json()).then(data => {
                                statusEl.innerHTML = "✔️ " + data.message + "<br><br><span style='color:#27ae60; background:#e8f8f5; padding:8px; display:block; border-radius:6px;'>Yönlendirilen Personel:<br><b>" + data.nearest_staff + "</b></span>";
                            });
                        }, error => {
                            statusEl.innerText = "Konum alınamadı! Lütfen konum izni verin.";
                            statusEl.style.color = "red";
                        });
                    } else {
                        statusEl.innerText = "Tarayıcınız konum özelliğini desteklemiyor.";
                    }
                }
            </script>
        </body>
    </html>
    """

@app.post("/api/emergency")
def trigger_emergency(signal: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    v_lat = signal.get("latitude", 39.9334)
    v_lon = signal.get("longitude", 32.8597)
    
    nearest_person = None
    min_dist = float('inf')
    
    for staff in STAFF_LIST:
        dist = calculate_distance(v_lat, v_lon, staff["lat"], staff["lon"])
        if dist < min_dist:
            min_dist = dist
            nearest_person = staff

    assigned_text = f"{nearest_person['name']} ({nearest_person['title']}) - Tel: {nearest_person['phone']} yola çıkarıldı!"
    
    incident_logs.append({
        "time": timestamp,
        "assigned_staff": nearest_person['name'],
        **signal
    })
    
    return {
        "status": "success", 
        "message": "Acil durum sinyali kayıtlı personele iletildi!",
        "nearest_staff": assigned_text
    }

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    feed_summary = "".join([f"<li style='margin-bottom:8px;'>[{i['time']}] <b>{i['sender']}</b>: {i['message']} ➔ <i style='color:#27ae60;'>({i['ai_tag']})</i></li>" for i in whatsapp_feed])
    incident_summary = "".join([f"<li style='margin-bottom:8px;'>[{i['time']}] <b>{i['visitor_id']}</b> acil sinyal gönderdi ➔ Yönlendirilen Personel: <b style='color:#c0392b;'>{i.get('assigned_staff', 'Bilinmiyor')}</b></li>" for i in incident_logs])
    
    return f"""
    <html>
        <head><title>Müdürlük Yönetim Paneli</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background: #f8f9fa;">
            <div style="max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color: #2c3e50; margin-top:0;">📊 Müdürlük Günlük Operasyon ve AI Rapor Ekranı</h2>
                <hr style="border:0; border-top:1px solid #eee; margin: 20px 0;">
                
                <h3 style="color: #34495E;">📱 WhatsApp Grup Faaliyet Akışı (AI Sınıflandırılmış)</h3>
                <ul style="padding-left: 20px; color: #555;">{feed_summary if feed_summary else "<li>Henüz grup akışı yok.</li>"}</ul>
                
                <h3 style="color: #c0392b; margin-top: 30px;">🚨 Acil Durum / Konum Bildirimleri ve Personel Yönlendirmeleri</h3>
                <p><b>Toplam Acil Vaka:</b> {len(incident_logs)}</p>
                <ul style="padding-left: 20px; color: #555;">{incident_summary if incident_summary else "<li>Henüz acil vaka yok.</li>"}</ul>
                
                <br><br>
                <a href="/" style="display:inline-block; background: #2c3e50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """
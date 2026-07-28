from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from typing import Optional
from datetime import datetime
import shutil
import os

app = FastAPI(title="Altınköy Otonom Sistem", version="1.0.0")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

whatsapp_feed = []
incident_logs = []

@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <html>
        <head>
            <title>Altınköy Akıllı Operasyon</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f6f9; padding: 40px; }
                .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); display: inline-block; max-width: 450px; width: 100%; }
                a { display: block; background: #2c3e50; color: white; padding: 15px; margin: 10px 0; text-decoration: none; border-radius: 5px; font-weight: bold; }
                a.whatsapp { background: #27ae60; }
                a.emergency { background: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🌾 Altınköy Otonom Sistem</h2>
                <p>Saha Operasyon ve Yönetim Paneli</p>
                <a class="whatsapp" href="/whatsapp-sim">📱 WhatsApp Grup Entegrasyon Paneli</a>
                <a href="/visitor-portal">🚶 Ziyaretçi Acil Durum / QR Portalı</a>
                <a class="emergency" href="/live-dashboard">📊 Müdürlük Canlı Rapor & Takip</a>
            </div>
        </body>
    </html>
    """

@app.get("/whatsapp-sim", response_class=HTMLResponse)
def whatsapp_sim_page():
    feed_html = ""
    for item in reversed(whatsapp_feed):
        feed_html += f"""
        <div style="background: white; border: 1px solid #ddd; padding: 15px; margin-bottom: 10px; border-radius: 8px; text-align: left;">
            <b>👤 {item['sender']}</b> <span style="font-size: 12px; color: gray;">({item['time']})</span><br>
            <p style="margin: 5px 0;">💬 {item['message']}</p>
            {"<img src='" + item['image_url'] + "' style='max-width: 100%; border-radius: 5px; margin-top: 5px;'/>" if item['image_url'] else ""}
            <div style="margin-top: 8px; font-size: 12px; background: #eef2f7; padding: 5px; border-radius: 4px;">
                🤖 <b>Yapay Zeka Etiketi:</b> <span style="color: #27ae60; font-weight: bold;">{item['ai_tag']}</span>
            </div>
        </div>
        """

    return f"""
    <html>
        <head><title>WhatsApp Grup Akışı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: Arial; padding: 20px; background: #efeae2;">
            <div style="max-width: 600px; margin: auto;">
                <h2>💬 "Altınköy Genel İşler" WhatsApp Akışı</h2>
                <p>Personel fotoğrafları ve mesajları yapay zeka tarafından etiketlenir.</p>
                
                <div style="background: #ffffff; padding: 15px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                    <h4>➕ Gruba Bildirim Gönder (Simülasyon)</h4>
                    <form action="/api/whatsapp-post" method="POST" enctype="multipart/form-data">
                        <label>Gönderen (Amir / Personel):</label><br>
                        <input type="text" name="sender" value="Fatih Altınköy Amir" required style="width: 100%; padding: 8px; margin: 5px 0;"><br>
                        
                        <label>Mesaj / Açıklama:</label><br>
                        <input type="text" name="message" placeholder="Örn: Kepçe geldi kamyonda geliyo" required style="width: 100%; padding: 8px; margin: 5px 0;"><br>
                        
                        <label>Saha Fotoğrafı:</label><br>
                        <input type="file" name="file" accept="image/*" style="width: 100%; margin: 5px 0 15px 0;"><br>
                        
                        <button type="submit" style="background: #128c7e; color: white; border: none; padding: 12px; width: 100%; border-radius: 5px; font-weight: bold; cursor: pointer;">WhatsApp Grubuna Gönder</button>
                    </form>
                </div>

                <h3>📜 Anlık Akış ve AI Sınıflandırması</h3>
                {feed_html if feed_html else "<p style='color: gray;'>Henüz mesaj akışı yok.</p>"}
                <br>
                <a href="/" style="display: block; text-align: center; background: #333; color: white; padding: 10px; text-decoration: none; border-radius: 5px;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/whatsapp-post")
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

    return """
    <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2 style="color: green;">✔️ Mesaj ve Fotoğraf Gruba İletildi!</h2>
            <p>Yapay zeka içeriği analiz etti ve rapor sistemine işledi.</p>
            <a href="/whatsapp-sim" style="background: #128c7e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Gruba Dön</a>
        </body>
    </html>
    """

@app.get("/visitor-portal", response_class=HTMLResponse)
def visitor_portal():
    return """
    <html>
        <head><title>Ziyaretçi Acil Durum</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: Arial; padding: 20px; text-align: center; background: #fff3f3;">
            <h2>🚨 Altınköy Acil Durum & Konum Bildirimi</h2>
            <p>1 Milyon metrekarelik alanda yardıma mı ihtiyacınız var?</p>
            <button onclick="sendEmergency()" style="background: #e74c3c; color: white; padding: 20px; font-size: 18px; border: none; border-radius: 8px; cursor: pointer;">📍 Konumumu Güvenliğe Gönder</button>
            <p id="status" style="margin-top: 20px; font-weight: bold;"></p>
            <br><a href="/" style="color: #333;">Ana Sayfaya Dön</a>
            <script>
                function sendEmergency() {
                    document.getElementById('status').innerText = "Konum alınıyor...";
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
                                document.getElementById('status').innerText = data.message;
                                document.getElementById('status').style.color = "green";
                            });
                        });
                    }
                }
            </script>
        </body>
    </html>
    """

@app.post("/api/emergency")
def trigger_emergency(signal: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    incident_logs.append({"time": timestamp, **signal})
    return {"status": "success", "message": "Acil durum sinyaliniz alındı! Güvenlik ekibi yola çıktı."}

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    feed_summary = "".join([f"<li>[{i['time']}] <b>{i['sender']}</b>: {i['message']} ➔ <i>({i['ai_tag']})</i></li>" for i in whatsapp_feed])
    
    return f"""
    <html>
        <head><title>Müdürlük Yönetim Paneli</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: Arial; padding: 20px; background: #f8f9fa;">
            <h2>📊 Müdürlük Günlük Operasyon ve AI Rapor Ekranı</h2>
            <hr>
            <h3>📱 WhatsApp Grup Faaliyet Akışı Özeti (AI Sınıflandırılmış)</h3>
            <ul>{feed_summary if feed_summary else "<li>Henüz grup akışı yok.</li>"}</ul>
            
            <h3>🚨 Acil Durum / Kayıp Bildirimleri</h3>
            <p>Toplam Acil Vaka: {len(incident_logs)}</p>
            <br>
            <a href="/" style="background: #333; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">Ana Sayfaya Dön</a>
        </body>
    </html>
    """
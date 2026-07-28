from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from typing import Optional
from datetime import datetime
import shutil
import os
import math
import io

app = FastAPI(title="Altınköy Otonom Sistem", version="3.4.0")

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

whatsapp_feed = []
incident_logs = []
qr_requests = []

STAFF_LIST = [
    {"id": 1, "name": "Ahmet Yılmaz", "title": "Saha Amiri", "lat": 39.9334, "lon": 32.8597, "phone": "0555 111 2233"},
    {"id": 2, "name": "Mehmet Demir", "title": "Güvenlik Personeli", "lat": 39.9350, "lon": 32.8550, "phone": "0555 222 3344"},
    {"id": 3, "name": "Ayşe Kaya", "title": "Peyzaj Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0555 333 4455"}
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
                .card { background: white; padding: 40px 30px; border-radius: 16px; box-shadow: 0px 10px 25px rgba(0,0,0,0.08); display: inline-block; max-width: 450px; width: 100%; box-sizing: border-box; }
                h2 { color: #2c3e50; margin-bottom: 5px; }
                p { color: #7f8c8d; margin-bottom: 25px; }
                a { display: block; background: #2c3e50; color: white; padding: 16px; margin: 12px 0; text-decoration: none; border-radius: 10px; font-weight: bold; transition: 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                a:hover { transform: translateY(-2px); opacity: 0.95; }
                a.whatsapp { background: #25D366; }
                a.emergency { background: #E74C3C; }
                a.staff { background: #8e44ad; }
                a.dashboard { background: #34495E; }
                a.qrchat { background: #d35400; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>🌾 Altınköy Otonom Sistem</h2>
                <p>Akıllı Saha Operasyon ve Yönetim Paneli</p>
                <a class="staff" href="/staff-management">👥 Belediye Çalışanları Kayıt & Yönetimi</a>
                <a class="whatsapp" href="/whatsapp-sim">📱 WhatsApp Grup Entegrasyon Paneli</a>
                <a class="emergency" href="/visitor-portal">🚶 Ziyaretçi Acil Durum / QR Portalı</a>
                <a class="qrchat" href="/qr-chat">🎤 Park Direkleri AI Sesli Asistan (QR)</a>
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
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                <h2>👥 Altınköy Saha Personel Kayıt Paneli</h2>
                <form action="/api/add-staff" method="POST">
                    <input type="text" name="name" placeholder="Çalışan Adı Soyadı" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    <input type="text" name="title" placeholder="Görevi / Unvanı" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    <input type="text" name="phone" placeholder="Telefon Numarası" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    <button type="submit" style="background: #8e44ad; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold; cursor: pointer;">Personel Kaydet</button>
                </form>
                <br><h3>Kayıtlı Personel ({len(STAFF_LIST)})</h3>
                <table style="width: 100%; border-collapse: collapse;">{staff_rows}</table>
                <br><a href="/" style="display: block; text-align: center; background: #2c3e50; color: white; padding: 12px; text-decoration: none; border-radius: 8px;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/add-staff")
def add_staff(name: str = Form(...), title: str = Form(...), phone: str = Form(...), lat: float = Form(39.9334), lon: float = Form(32.8597)):
    STAFF_LIST.append({"id": len(STAFF_LIST) + 1, "name": name, "title": title, "lat": lat, "lon": lon, "phone": phone})
    return RedirectResponse(url="/staff-management", status_code=303)

@app.get("/whatsapp-sim", response_class=HTMLResponse)
def whatsapp_sim_page():
    feed_html = "".join([f"<div style='background: white; border: 1px solid #e1e8ed; padding: 15px; margin-bottom: 12px; border-radius: 10px;'><b>👤 {item['sender']}</b> <span style='font-size:11px; color:gray; float:right;'>{item['time']}</span><br><p style='margin:8px 0;'>💬 {item['message']}</p><div style='font-size:12px; background:#f0f4f8; padding:6px; border-radius:6px;'>🤖 <b>AI Etiketi:</b> {item['ai_tag']}</div></div>" for item in reversed(whatsapp_feed)])
    return f"""
    <html>
        <head><title>WhatsApp Akışı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background: #efeae2; margin: 0;">
            <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 12px;">
                <h2>💬 WhatsApp Grup Akışı</h2>
                <form action="/api/whatsapp-post" method="POST">
                    <input type="text" name="sender" value="Fatih Amir" required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    <input type="text" name="message" placeholder="Mesajınız..." required style="width: 100%; padding: 10px; margin: 5px 0 12px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;">
                    <button type="submit" style="background: #128c7e; color: white; border: none; padding: 12px; width: 100%; border-radius: 8px; font-weight: bold;">Gönder</button>
                </form>
                <br><h3>Anlık Akış</h3>{feed_html if feed_html else "<p style='color:gray;'>Henüz mesaj yok.</p>"}
                <br><a href="/" style="display: block; text-align: center; background: #2c3e50; color: white; padding: 12px; text-decoration: none; border-radius: 8px;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/whatsapp-post", response_class=HTMLResponse)
def process_whatsapp_post(sender: str = Form(...), message: str = Form(...)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ai_tag = "Genel Saha Çalışması"
    if "kepçe" in message.lower() or "kamyon" in message.lower(): ai_tag = "Altyapı / Hafriyat"
    elif "su" in message.lower(): ai_tag = "Su Kontrolü"
    whatsapp_feed.append({"sender": sender, "message": message, "image_url": None, "time": timestamp, "ai_tag": ai_tag})
    return RedirectResponse(url="/whatsapp-sim", status_code=303)

@app.get("/visitor-portal", response_class=HTMLResponse)
def visitor_portal():
    return """
    <html>
        <head><title>Ziyaretçi Portalı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; background: #fff5f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
            <div style="background: white; padding: 30px; border-radius: 16px; box-shadow: 0 10px 25px rgba(231,76,60,0.1); text-align: center; max-width: 400px; width: 90%; box-sizing: border-box;">
                <h2 style="color: #c0392b; margin-top:0;">🚨 Acil Durum & Konum</h2>
                <button onclick="sendEmergency()" style="background: #e74c3c; color: white; padding: 16px; font-size: 15px; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; width: 100%;">📍 Konumumu Güvenliğe Gönder</button>
                <p id="status" style="margin-top: 20px; font-weight: bold; font-size: 14px;"></p>
                <br><a href="/" style="color: #7f8c8d; text-decoration: none; font-size: 13px; font-weight: bold;">← Ana Sayfaya Dön</a>
            </div>
            <script>
                function sendEmergency() {
                    const statusEl = document.getElementById('status');
                    statusEl.innerText = "Konum alınıyor...";
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(position => {
                            fetch('/api/emergency', {
                                method: 'POST',
                                headers: {'Content-Type': 'application/json'},
                                body: JSON.stringify({ visitor_id: "Ziyaretci", latitude: position.coords.latitude, longitude: position.coords.longitude })
                            }).then(res => res.json()).then(data => {
                                statusEl.innerHTML = "✔️ " + data.message + "<br><br><b>" + data.nearest_staff + "</b>";
                            });
                        }, () => { statusEl.innerText = "Konum izni reddedildi."; statusEl.style.color = "red"; });
                    }
                }
            </script>
        </body>
    </html>
    """

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_page():
    return """
    <html>
        <head>
            <title>Altınköy Park Asistanı</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #fdfbf7; margin: 0; padding: 10px; display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; }
                .chat-container { width: 100%; max-width: 450px; background: white; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); display: flex; flex-direction: column; overflow: hidden; height: 90vh; }
                .chat-header { background: #d35400; color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 16px; }
                .chat-messages { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #faf9f6; }
                .message { padding: 10px 14px; border-radius: 10px; max-width: 85%; font-size: 14px; line-height: 1.4; word-break: break-word; }
                .bot { background: #eef2f7; color: #333; align-self: flex-start; }
                .user { background: #d35400; color: white; align-self: flex-end; }
                .chat-input-area { padding: 15px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; align-items: center; }
                input[type="text"] { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; outline: none; font-size: 14px; box-sizing: border-box; }
                button { background: #d35400; color: white; border: none; padding: 12px 14px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 13px; }
                .mic-btn { background: #27ae60; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="chat-header">🌾 Altınköy Park 7/24 AI Asistanı</div>
                <div id="chatMessages" class="chat-messages">
                    <div class="message bot">Merhaba! Park direğindeki QR kodu okuttunuz. İstek ve taleplerinizi yazabilir veya konuşarak iletebilirsiniz.</div>
                </div>
                <div class="chat-input-area">
                    <button class="mic-btn" onclick="startVoiceChat()" id="micBtn">🎤 Konuş</button>
                    <input type="text" id="userInput" placeholder="Talebinizi yazın..." onkeypress="if(event.key === 'Enter') sendMessage()">
                    <button onclick="sendMessage()">Gönder</button>
                </div>
            </div>

            <script>
                function speakText(text) {
                    if ('speechSynthesis' in window) {
                        window.speechSynthesis.cancel(); // Önceki sesleri durdur
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = 'tr-TR';
                        window.speechSynthesis.speak(utterance);
                    }
                }

                function startVoiceChat() {
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    if (!SpeechRecognition) {
                        alert("Tarayıcınız ses tanımayı desteklemiyor. Lütfen yazarak iletin.");
                        return;
                    }
                    const recognition = new SpeechRecognition();
                    recognition.lang = 'tr-TR';
                    
                    const micBtn = document.getElementById('micBtn');
                    const inputEl = document.getElementById('userInput');
                    
                    micBtn.style.background = "#c0392b";
                    micBtn.innerText = "Dinleniyor...";
                    
                    recognition.onresult = function(event) {
                        const transcript = event.results[0][0].transcript;
                        inputEl.value = transcript;
                        micBtn.style.background = "#27ae60";
                        micBtn.innerText = "🎤 Konuş";
                        sendMessage();
                    };
                    
                    recognition.onerror = function() {
                        micBtn.style.background = "#27ae60";
                        micBtn.innerText = "🎤 Konuş";
                        alert("Ses algılanamadı, lütfen tekrar deneyin.");
                    };
                    
                    recognition.onend = function() {
                        micBtn.style.background = "#27ae60";
                        micBtn.innerText = "🎤 Konuş";
                    };
                    
                    recognition.start();
                }

                function sendMessage() {
                    const inputEl = document.getElementById('userInput');
                    const text = inputEl.value.trim();
                    if (!text) return;

                    const chatMessages = document.getElementById('chatMessages');
                    chatMessages.innerHTML += <div class="message user">${text}</div>;
                    inputEl.value = "";
                    chatMessages.scrollTop = chatMessages.scrollHeight;

                    fetch('/api/qr-chat-submit', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ message: text })
                    }).then(res => res.json()).then(data => {
                        chatMessages.innerHTML += <div class="message bot">${data.reply}</div>;
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                        speakText(data.reply);
                    }).catch(() => {
                        chatMessages.innerHTML += <div class="message bot">Sunucuya bağlanırken bir hata oluştu.</div>;
                    });
                }
            </script>
        </body>
    </html>
    """

@app.post("/api/qr-chat-submit")
def qr_chat_submit(data: dict):
    user_msg = data.get("message", "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    reply = "Talebiniz alınmıştır. En kısa sürede ilgili saha ekibimize yönlendirilecektir."
    msg_l = user_msg.lower()
    
    if "tuvalet" in msg_l or "lavabo" in msg_l: reply = "En yakın tuvalet ana meydanın kuzey doğusundadır. Temizlik ekibine bildirildi."
    elif "çöp" in msg_l or "kirl" in msg_l: reply = "Çöp bildiriminiz alındı. Temizlik personeli bölgeye yönlendiriliyor."
    elif "otopark" in msg_l or "araç" in msg_l: reply = "Otopark düzeni için güvenlik ekibimiz bilgilendirildi."
    elif "su" in msg_l or "çeşme" in msg_l: reply = "Su hatları ile ilgili bakım talebiniz peyzaj ekibine iletildi."

    qr_requests.append({"time": timestamp, "message": user_msg, "ai_reply": reply})
    return {"status": "success", "reply": reply}

@app.post("/api/emergency")
def trigger_emergency(signal: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    v_lat = signal.get("latitude", 39.9334)
    v_lon = signal.get("longitude", 32.8597)
    
    nearest_person = min(STAFF_LIST, key=lambda s: calculate_distance(v_lat, v_lon, s["lat"], s["lon"]))
    assigned_text = f"Yönlendirilen Personel: {nearest_person['name']} ({nearest_person['title']}) - Tel: {nearest_person['phone']}"
    
    incident_logs.append({"time": timestamp, "assigned_staff": nearest_person['name'], **signal})
    return {"status": "success", "message": "Acil durum sinyali alındı! Güvenlik ekibi yola çıktı.", "nearest_staff": assigned_text}

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    qr_summary = "".join([f"<li>[{i['time']}] Talep: <b>{i['message']}</b> ➔ Yanıt: {i['ai_reply']}</li>" for i in qr_requests])
    return f"""
    <html>
        <head><title>Yönetim Paneli</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family: 'Segoe UI', Tahoma, sans-serif; padding: 20px; background: #f8f9fa;">
            <div style="max-width: 700px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color: #2c3e50;">📊 Müdürlük Rapor Ekranı</h2>
                <h3 style="color: #d35400;">🎤 QR Asistan Talepleri ({len(qr_requests)})</h3>
                <ul>{qr_summary if qr_summary else "<li>Henüz talep yok.</li>"}</ul>
                <br><a href="/" style="background: #2c3e50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; display:inline-block;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    ""
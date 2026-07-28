from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import os
import math
import requests

app = FastAPI(title="Altınköy Otonom Sistem", version="3.9.2")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

whatsapp_feed = []
incident_logs = []
qr_requests = []

STAFF_LIST = [
    {"id": 1, "name": "Onur Yılmaz", "title": "Peyzaj Sorumlusu", "lat": 39.9334, "lon": 32.8597, "phone": "0555 111 2233"},
    {"id": 2, "name": "Fırat Reis", "title": "Güvenlik Personeli", "lat": 39.9350, "lon": 32.8550, "phone": "0553 691 57 52"},
    {"id": 3, "name": "Hakan Taşkale", "title": "Peyzaj Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0555 333 4455"}
]

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)*2 + (lon1 - lon2)*2)

def ask_groq_ai(prompt: str) -> str:
    p_lower = prompt.lower()
    if GROQ_API_KEY == "BURAYA_GROQ_API_KEY_GIRINIZ" or not GROQ_API_KEY:
        if "tuvalet" in p_lower: return "En yakın tuvalet ana meydanın kuzey doğusundadır."
        elif "çöp" in p_lower: return "Temizlik personeli bölgeye yönlendirildi."
        return f"Talebiniz alındı: '{prompt}'. Onur Yılmaz ve ekibe iletildi."

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Sen Altınköy parkının akıllı yapay zeka asistanısın. Kısa ve kibar Türkçe yanıtlar ver."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return f"Talebiniz kaydedildi: '{prompt}'"

@app.get("/", response_class=HTMLResponse)
def home_page():
    return """
    <html>
        <head><title>Altınköy</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; background:#f4f6f9; padding:30px;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:400px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2>🌾 Altınköy Otonom Sistem</h2>
                <a href="/staff-management" style="display:block; background:#8e44ad; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">👥 Personel Yönetimi</a>
                <a href="/whatsapp-sim" style="display:block; background:#25D366; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📱 WhatsApp Simülasyonu</a>
                <a href="/visitor-portal" style="display:block; background:#E74C3C; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🚶 Acil Durum & Konum</a>
                <a href="/qr-chat" style="display:block; background:#d35400; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🎤 Park Groq AI Asistanı</a>
                <a href="/live-dashboard" style="display:block; background:#34495E; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📊 Yönetim Paneli</a>
            </div>
        </body>
    </html>
    """

@app.get("/staff-management", response_class=HTMLResponse)
def staff_page():
    rows = "".join([f"<tr><td style='padding:8px;'><b>{s['name']}</b><br>{s['title']}</td><td style='padding:8px;'>{s['phone']}</td></tr>" for s in STAFF_LIST])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:500px; margin:auto; background:white; padding:20px; border-radius:10px;">
                <h2>👥 Personel Listesi</h2>
                <form action="/api/add-staff" method="POST">
                    <input type="text" name="name" placeholder="Ad Soyad" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="title" placeholder="Unvan" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="phone" placeholder="Telefon" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <button type="submit" style="background:#8e44ad; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold;">Kaydet</button>
                </form>
                <br><table width="100%">{rows}</table>
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/add-staff")
def add_staff(name: str = Form(...), title: str = Form(...), phone: str = Form(...)):
    STAFF_LIST.append({"id": len(STAFF_LIST)+1, "name": name, "title": title, "lat": 39.9334, "lon": 32.8597, "phone": phone})
    return RedirectResponse(url="/staff-management", status_code=303)

@app.get("/whatsapp-sim", response_class=HTMLResponse)
def wa_page():
    feed = "".join([f"<div style='background:white; padding:10px; margin-bottom:8px; border-radius:6px; border:1px solid #ddd;'><b>{i['sender']}</b> [{i['time']}]: {i['message']}</div>" for i in reversed(whatsapp_feed)])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#efeae2;">
            <div style="max-width:500px; margin:auto; background:white; padding:20px; border-radius:10px;">
                <h2>📱 WhatsApp Grup Akışı</h2>
                <form action="/api/wa-post" method="POST">
                    <input type="text" name="sender" value="Onur Yılmaz (Amir)" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="message" placeholder="Mesaj yaz..." required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <button type="submit" style="background:#128c7e; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold;">Gönder</button>
                </form>
                <br><h3>Akış</h3>{feed if feed else "<p>Mesaj yok</p>"}
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/wa-post")
def wa_post(sender: str = Form(...), message: str = Form(...)):
    whatsapp_feed.append({"sender": sender, "message": message, "time": datetime.now().strftime("%H:%M:%S")})
    return RedirectResponse(url="/whatsapp-sim", status_code=303)

@app.get("/visitor-portal", response_class=HTMLResponse)
def visitor_portal():
    return """
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; background:#fff5f5; text-align:center; padding:50px;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:400px; width:100%;">
                <h2 style="color:#c0392b;">🚨 Acil Durum Paneli</h2>
                <form action="/api/emergency-form" method="POST">
                    <input type="hidden" name="lat" value="39.9334">
                    <input type="hidden" name="lon" value="32.8597">
                    <button type="submit" style="background:#e74c3c; color:white; padding:16px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:15px; cursor:pointer;">📍 Acil Konum Bildir ve Ekip İste</button>
                </form>
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/emergency-form", response_class=HTMLResponse)
def emergency_form(lat: float = Form(39.9334), lon: float = Form(32.8597)):
    nearest = min(STAFF_LIST, key=lambda s: calculate_distance(lat, lon, s["lat"], s["lon"]))
    incident_logs.append({"time": datetime.now().strftime("%H:%M:%S"), "staff": nearest['name']})
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; padding:50px; background:#e8f8f5;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:400px;">
                <h2 style="color:#27ae60;">✔️ Sinyal Alındı!</h2>
                <p>Güvenlik ekibi yönlendirildi.</p>
                <p><b>Yönlendirilen Personel:</b> {nearest['name']} ({nearest['title']})<br>Tel: {nearest['phone']}</p>
                <br><a href="/visitor-portal" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Geri Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_get():
    chat_history = "".join([f"<div style='margin-bottom:10px;'><b>Ziyaretçi:</b> {q['msg']}<br><div style='background:#eef2f7; padding:8px; border-radius:6px; margin-top:4px;'><b>Asistan:</b> {q['reply']}</div></div>" for q in reversed(qr_requests)])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#fdfbf7;">
            <div style="max-width:500px; margin:auto; background:white; padding:20px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#d35400;">🎤 Park AI Asistanı (QR)</h2>
                <form action="/api/qr-chat-post" method="POST">
                    <input type="text" name="message" placeholder="Talebinizi yazın (Örn: Tuvalet nerede?)" required style="width:100%; padding:12px; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"><br><br>
                    <button type="submit" style="background:#d35400; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold;">Yapay Zekaya Sor</button>
                </form>
                <br><h3>Geçmiş Sorular & Yanıtlar</h3>
                {chat_history if chat_history else "<p style='color:gray;'>Henüz soru sorulmadı.</p>"}
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/qr-chat-post")
def qr_chat_post(message: str = Form(...)):
    reply = ask_groq_ai(message)
    qr_requests.append({"msg": message, "reply": reply})
    return RedirectResponse(url="/qr-chat", status_code=303)

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    summary = "".join([f"<li><b>{r['msg']}</b> ➔ {r['reply']}</li>" for r in qr_requests])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f8f9fa;">
            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:10px;">
                <h2>📊 Müdürlük Rapor Paneli</h2>
                <h3>Groq AI Talepleri ({len(qr_requests)})</h3>
                <ul>{summary if summary else "<li>Talep yok.</li>"}</ul>
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """
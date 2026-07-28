from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import os
import math
import requests

app = FastAPI(title="Altınköy Otonom Sistem", version="4.0")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

whatsapp_feed = []
incident_logs = []
qr_requests = []
heatmap_data = [] # Yoğunluk verileri

STAFF_LIST = [
    {"id": 1, "name": "Onur Yılmaz", "title": "Saha Sorumlusu & Operasyon Amiri", "lat": 39.9334, "lon": 32.8597, "phone": "0555 111 2233", "zone": "Köy Meydanı"},
    {"id": 2, "name": "Fırat Reis", "title": "Güvenlik Personeli", "lat": 39.9350, "lon": 32.8550, "phone": "0553 691 57 52", "zone": "At Menajı"},
    {"id": 3, "name": "Hakan Taşkale", "title": "Peyzaj Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0546 801 61 72", "zone": "Ceylanlar Bölgesi"}
]

ALTINKOY_LOCATIONS = {
    "at menajı": {"desc": "At menajı, parkın kuzey batı tarafında, manej ve ahırların olduğu alandadır.", "zone": "At Menajı"},
    "ceylanlar": {"desc": "Ceylanlar bölgesi, doğu yürüyüş parkurunun hemen ilerisinde doğal yaşam alanındadır.", "zone": "Ceylanlar Bölgesi"},
    "köy meydanı": {"desc": "Köy meydanı parkın tam merkezindedir; ana giriş, kafeterya ve buluşma noktasıdır.", "zone": "Köy Meydanı"},
    "tuvalet": {"desc": "En yakın tuvalet köy meydanının kuzey doğusundadır.", "zone": "Köy Meydanı"},
    "otopark": {"desc": "Ana araç otoparkı ana nizamiyenin girişindedir.", "zone": "Ana Giriş"}
}

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)*2 + (lon1 - lon2)*2)

def ask_groq_ai(prompt: str) -> str:
    p_lower = prompt.lower()
    
    # Özel Altınköy Lokasyon Kontrolü
    for key, info in ALTINKOY_LOCATIONS.items():
        if key in p_lower:
            return f"📍 {info['desc']} (Bölge: {info['zone']})"

    if GROQ_API_KEY == "BURAYA_GROQ_API_KEY_GIRINIZ" or not GROQ_API_KEY:
        if "acil" in p_lower or "yardım" in p_lower:
            return "🚨 Acil durum sinyali algılandı! Lütfen Acil Durum / Konum butonunu kullanın."
        return f"Altınköy Asistanı: '{prompt}' talebiniz alındı. Saha amiri Onur Yılmaz ve ekiplere iletildi."

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Sen 1 milyon metrekarelik Altınköy parkının akıllı yapay zeka asistanısın. At menajı, Ceylanlar bölgesi, Köy meydanı, tuvalet gibi yerleri çok iyi biliyorsun. Ziyaretçilere net Türkçe yol tarifleri ver."},
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
        <head><title>Altınköy Otonom Sistem</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; background:#f4f6f9; padding:30px;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:450px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2>🌾 Altınköy Otonom Sistem v4.0</h2>
                <p style="color:gray; font-size:13px;">Yapay Zeka, Sesli Navigasyon & Isı Haritası</p>
                <a href="/staff-management" style="display:block; background:#8e44ad; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">👥 Personel Yönetimi & Bölgeler</a>
                <a href="/whatsapp-sim" style="display:block; background:#25D366; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📱 WhatsApp Grup Akışı</a>
                <a href="/visitor-portal" style="display:block; background:#E74C3C; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🚶 Acil Durum & Konum Paneli</a>
                <a href="/qr-chat" style="display:block; background:#d35400; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🎤 Park Groq AI Asistanı & Sesli Tarif</a>
                <a href="/heatmap" style="display:block; background:#e67e22; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🔥 Yoğunluk Isı Haritası & İstatistikler</a>
                <a href="/live-dashboard" style="display:block; background:#34495E; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📊 Müdürlük Rapor Paneli</a>
            </div>
        </body>
    </html>
    """

@app.get("/staff-management", response_class=HTMLResponse)
def staff_page():
    rows = "".join([f"<tr><td style='padding:8px;'><b>{s['name']}</b><br>{s['title']}</td><td style='padding:8px;'>{s['zone']}</td><td style='padding:8px;'>{s['phone']}</td></tr>" for s in STAFF_LIST])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:600px; margin:auto; background:white; padding:20px; border-radius:10px;">
                <h2>👥 Personel & Bölge Atamaları</h2>
                <form action="/api/add-staff" method="POST">
                    <input type="text" name="name" placeholder="Ad Soyad" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="title" placeholder="Unvan" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="zone" placeholder="Sorumlu Olduğu Bölge (Örn: At Menajı)" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="phone" placeholder="Telefon" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <button type="submit" style="background:#8e44ad; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold;">Personel Kaydet</button>
                </form>
                <br><table width="100%" style="border-collapse:collapse;"><tr style="background:#eee; text-align:left;"><th style="padding:8px;">Personel</th><th style="padding:8px;">Bölge</th><th style="padding:8px;">Tel</th></tr>{rows}</table>
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/add-staff")
def add_staff(name: str = Form(...), title: str = Form(...), zone: str = Form(...), phone: str = Form(...)):
    STAFF_LIST.append({"id": len(STAFF_LIST)+1, "name": name, "title": title, "zone": zone, "lat": 39.9334, "lon": 32.8597, "phone": phone})
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
                <h2 style="color:#c0392b;">🚨 Acil Durum & Konum</h2>
                <form action="/api/emergency-form" method="POST">
                    <select name="zone" style="width:100%; padding:12px; margin-bottom:15px; border-radius:6px; border:1px solid #ddd;">
                        <option value="Köy Meydanı">Köy Meydanı</option>
                        <option value="At Menajı">At Menajı</option>
                        <option value="Ceylanlar Bölgesi">Ceylanlar Bölgesi</option>
                        <option value="Ana Giriş Otopark">Ana Giriş Otopark</option>
                    </select>
                    <button type="submit" style="background:#e74c3c; color:white; padding:16px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:15px; cursor:pointer;">📍 Acil Sinyal Gönder & Ekip İste</button>
                </form>
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/emergency-form", response_class=HTMLResponse)
def emergency_form(zone: str = Form("Köy Meydanı")):
    # Isı haritasına ve istatistiğe kaydet
    heatmap_data.append({"zone": zone, "type": "Acil Durum", "time": datetime.now().strftime("%H:%M:%S")})
    nearest = min(STAFF_LIST, key=lambda s: 0 if s['zone'] == zone else 1)
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; padding:50px; background:#e8f8f5;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:400px;">
                <h2 style="color:#27ae60;">✔️ Acil Sinyal İletildi!</h2>
                <p><b>Seçilen Bölge:</b> {zone}</p>
                <p><b>Yönlendirilen Personel:</b> {nearest['name']} ({nearest['title']})<br>Tel: {nearest['phone']}</p>
                <br><a href="/visitor-portal" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Geri Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_get():
    chat_history = "".join([f"<div style='margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:8px;'><b>Ziyaretçi:</b> {q['msg']}<br><div style='background:#eef2f7; padding:8px; border-radius:6px; margin-top:4px;'><b>Asistan:</b> {q['reply']}</div><button onclick=\"speakText('{q['reply']}')\" style='margin-top:5px; background:#27ae60; color:white; border:none; padding:6px 12px; border-radius:4px; font-size:12px; cursor:pointer;'>🔊 Sesli Konum / Tarif Dinle</button></div>" for q in reversed(qr_requests)])
    return f"""
    <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>
                function speakText(text) {{
                    if ('speechSynthesis' in window) {{
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = 'tr-TR';
                        window.speechSynthesis.speak(utterance);
                    }} else {{
                        alert('Tarayıcınız sesli okumayı desteklemiyor.');
                    }}
                }}
            </script>
        </head>
        <body style="font-family:Segoe UI; padding:20px; background:#fdfbf7;">
            <div style="max-width:550px; margin:auto; background:white; padding:20px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#d35400;">🎤 Park AI Asistanı & Sesli Tarif</h2>
                <form action="/api/qr-chat-post" method="POST">
                    <input type="text" name="message" placeholder="Örn: At menajı nerede? Ceylanlar bölgesine nasıl giderim?" required style="width:100%; padding:12px; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"><br><br>
                    <button type="submit" style="background:#d35400; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold; cursor:pointer;">Yapay Zekaya Sor</button>
                </form>
                <br><h3>Geçmiş Soru & Yanıtlar</h3>
                {chat_history if chat_history else "<p style='color:gray;'>Henüz soru sorulmadı.</p>"}
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/qr-chat-post")
def qr_chat_post(message: str = Form(...)):
    reply = ask_groq_ai(message)
    
    # Isı haritası için hangi bölge sorulduğunu tespit et
    detected_zone = "Köy Meydanı"
    m_lower = message.lower()
    if "at menajı" in m_lower or "at" in m_lower: detected_zone = "At Menajı"
    elif "ceylan" in m_lower: detected_zone = "Ceylanlar Bölgesi"
    elif "otopark" in m_lower: detected_zone = "Ana Giriş Otopark"
    
    heatmap_data.append({"zone": detected_zone, "type": "Soru / Ziyaret", "time": datetime.now().strftime("%H:%M:%S")})
    qr_requests.append({"msg": message, "reply": reply})
    return RedirectResponse(url="/qr-chat", status_code=303)

@app.get("/heatmap", response_class=HTMLResponse)
def heatmap_page():
    zones = ["Köy Meydanı", "At Menajı", "Ceylanlar Bölgesi", "Ana Giriş Otopark"]
    stats = {z: sum(1 for h in heatmap_data if h['zone'] == z) for z in zones}
    max_val = max(stats.values()) if stats.values() else 1
    
    bars = ""
    for z, count in stats.items():
        pct = int((count / max(max_val, 1)) * 100)
        color = "#e74c3c" if count > 3 else "#f39c12" if count > 1 else "#27ae60"
        bars += f"<div style='margin-bottom:15px;'><b>{z}</b> ({count} talep/ziyaret)<div style='background:#eee; border-radius:6px; overflow:hidden; height:22px; margin-top:5px;'><div style='width:{max(pct, 5)}%; background:{color}; height:100%; text-align:right; color:white; padding-right:8px; font-size:12px; line-height:22px;'>{count}</div></div></div>"

    log_items = "".join([f"<li>[{h['time']}] Bölge: <b>{h['zone']}</b> — İşlem: {h['type']}</li>" for h in reversed(heatmap_data)])
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#e67e22;">🔥 Park Yoğunluk Isı Haritası & İstatistikler</h2>
                <p style="color:gray; font-size:13px;">Hangi bölgede en çok yoğunluk var ve kimler nereleri ziyaret ediyor?</p>
                <br>{bars}
                <br><h3>Canlı İşlem & Yoğunluk Günlüğü</h3>
                <ul style="font-size:14px; color:#333;">{log_items if log_items else "<li>Henüz veri yok.</li>"}</ul>
                <br><a href="/" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

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
                <br><a href="/" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:8px; display:inline-block;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """
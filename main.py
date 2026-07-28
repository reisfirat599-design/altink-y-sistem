from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import os
import math
import requests

app = FastAPI(title="Altınköy Otonom Sistem", version="6.5")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

whatsapp_feed = []
qr_requests = []
heatmap_data = []
survey_responses = []

ALTINKOY_BG = "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?auto=format&fit=crop&w=1920&q=80"
DYNAMIC_QRS = {
    "direk-01": {"zone": "Köy Meydanı", "title": "Köy Meydanı Ana Direk", "target_url": "/visitor-home", "lat": 39.9334, "lon": 32.8597},
    "direk-02": {"zone": "Yel ve Su Değirmenleri", "title": "Değirmen Direği", "target_url": "/uyari/degirmen-bolgesi", "lat": 39.9360, "lon": 32.8520},
    "direk-03": {"zone": "Geleneksel Çantı Evler", "title": "Çantı Evler Direği", "target_url": "/visitor-home", "lat": 39.9300, "lon": 32.8600}
}

STAFF_LIST = [
    {"id": 1, "name": "Onur Yılmaz", "title": "Saha Sorumlusu & Operasyon Amiri", "lat": 39.9334, "lon": 32.8597, "phone": "0537 939 36 77", "zone": "Köy Meydanı"},
    {"id": 2, "name": "Fırat Reis", "title": "Güvenlik & Değirmenler Sorumlusu", "lat": 39.9360, "lon": 32.8520, "phone": "0553 691 57 52", "zone": "Yel ve Su Değirmenleri"},
    {"id": 3, "name": "Ayşe Kaya", "title": "Çantı Evler Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0546 801 61 72", "zone": "Geleneksel Çantı Evler"}
]

PARK_ZONES = {
    "Köy Meydanı": {"lat": 39.9334, "lon": 32.8597, "desc": "Köy kahvesi, cami, okul ve muhtarlık merkezi."},
    "Geleneksel Çantı Evler": {"lat": 39.9300, "lon": 32.8600, "desc": "Çivi çakılmadan yapılan asırlık ahşap yapılar."},
    "Yel ve Su Değirmenleri": {"lat": 39.9360, "lon": 32.8520, "desc": "Değirmen ve dere yatağı güvenli yürüyüş alanı."}
}

ALTINKOY_LOCATIONS = {
    "çantı ev": "Geleneksel çantı evler, çivi çakılmadan bindirme tekniğiyle yapılmış asırlık yapılardır.",
    "değirmen": "Çalışır durumdaki yel değirmeni ve su değirmeni müzenin kuzeybatı tarafındadır.",
    "dere": "Değirmen kenarındaki dere yatağı ve su boyu dinlenme alanıdır. Can güvenliği için suya girmek kesinlikle yasaktır.",
    "piknik": "Müzemizde piknik yapmak ve dışarıdan yiyecek içecek getirmek yasaktır. Köy kahvemiz ve fırınımız hizmetinizdedir.",
    "kahvaltı": "Dere kenarlarında kahvaltı yapmak yasaktır. Köy kahvemizde taze ürünlerimiz bulunmaktadır.",
    "köy meydanı": "Köy meydanında köy kahvesi, cami, okul ve muhtarlık yer almaktadır.",
    "tuvalet": "En yakın tuvalet köy meydanı yakınlarındadır."
}

def find_nearest_zone(lat: float, lon: float) -> str:
    nearest, min_dist = "Köy Meydanı", float('inf')
    for z, c in PARK_ZONES.items():
        dist = math.sqrt((lat - c["lat"])*2 + (lon - c["lon"])*2)
        if dist < min_dist:
            min_dist, nearest = dist, z
    return nearest

def ask_groq_ai(prompt: str, lat: float = None, lon: float = None) -> str:
    p_lower = prompt.lower()
    if any(y in p_lower for y in ["salak", "aptal", "mal", "rezil", "pis"]):
        return "Müze rehberi olarak bu üslubu reddediyor, saygılı bir iletişim rica ediyorum."
    if any(k in p_lower for k in ["neredeyim", "konumum", "burası neresi"]):
        if lat and lon:
            z = find_nearest_zone(lat, lon)
            return f"📍 Mevcut Konumunuz: {z} ({lat:.4f}, {lon:.4f})"
        return "📍 Konumunuza ulaşılamadı."
    for k, desc in ALTINKOY_LOCATIONS.items():
        if k in p_lower:
            return f"📍 {desc}"
    if GROQ_API_KEY == "BURAYA_GROQ_API_KEY_GIRINIZ" or not GROQ_API_KEY:
        return "Altınköy Asistanı: Dışarıdan yiyecek getirmek, piknik/kahvaltı yapmak ve dereye girmek yasaktır."
    
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "Sen Altınköy Açık Hava Müzesi'nin neşeli, samimi ve kuralları net savunan rehberisin. Dışarıdan yiyecek, piknik, kahvaltı ve suya girmek kesinlikle yasaktır."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    try:
        res = requests.post(GROQ_URL, json=payload, headers=headers, timeout=6)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except:
        pass
    return "Talebiniz alınmıştır. Müzemizde piknik yapmak ve suya girmek yasaktır."

def render_page(title: str, content_html: str, extra_js: str = "") -> str:
    return f"""
    <html>
        <head>
            <title>{title} - Altınköy</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, sans-serif;
                    background: url('{ALTINKOY_BG}') no-repeat center center fixed;
                    background-size: cover;
                    margin: 0; padding: 20px;
                    display: flex; justify-content: center; align-items: center; min-height: 90vh;
                }}
                .card {{
                    background: rgba(255, 255, 255, 0.94);
                    backdrop-filter: blur(10px);
                    max-width: 440px; width: 100%;
                    padding: 25px; border-radius: 20px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
                    box-sizing: border-box;
                    max-height: 92vh; overflow-y: auto;
                }}
                h2 {{ color: #2c3e50; margin-top: 0; text-align: center; font-size: 20px; }}
                p {{ color: #555; font-size: 13px; text-align: center; }}
                .btn {{
                    display: block; width: 100%; padding: 12px; margin: 8px 0;
                    border: none; border-radius: 10px; font-weight: bold; font-size: 14px;
                    text-align: center; text-decoration: none; cursor: pointer; transition: 0.2s;
                    box-sizing: border-box;
                }}
                .btn-primary {{ background: #27ae60; color: white; }}
                .btn-warning {{ background: #d35400; color: white; }}
                .btn-danger {{ background: #c0392b; color: white; }}
                .btn-dark {{ background: #34495e; color: white; }}
                .footer-link {{ text-align: center; margin-top: 12px; font-size: 12px; }}
                .footer-link a {{ color: #7f8c8d; text-decoration: none; }}
            </style>
            <script>
                function speakText(text) {{
                    if ('speechSynthesis' in window) {{
                        window.speechSynthesis.cancel();
                        const utterance = new SpeechSynthesisUtterance(text);
                        utterance.lang = 'tr-TR';
                        window.speechSynthesis.speak(utterance);
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="card">
                {content_html}
            </div>
            {extra_js}
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
def home_page(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        html = """
        <h2>🌾 Altınköy Açık Hava Müzesi</h2>
        <p>Akıllı Asistan ve Canlı Konum Sistemine Hoş Geldiniz</p>
        <form action="/api/set-session" method="POST">
            <div style="background:#f1f8e9; padding:10px; border-radius:8px; font-size:11px; color:#33691e; max-height:80px; overflow-y:auto; margin-bottom:12px; border:1px solid #c5e1a5;">
                <b>KVKK Aydınlatma Metni:</b> Konum yönlendirmesi ve asistan hizmeti sunabilmek amacıyla kişisel verileriniz işlenmektedir.
            </div>
            <label style="font-size:12px; display:block; margin-bottom:12px; cursor:pointer;">
                <input type="checkbox" required> Metni okudum ve onaylıyorum.
            </label>
            <button type="submit" class="btn btn-primary">Müzeye Giriş Yap</button>
        </form>
        <div class="footer-link"><a href="/admin-panel">Müdür / Yönetici Girişi</a></div>
        """
        return render_page("Giriş", html)
    return RedirectResponse(url="/visitor-home", status_code=303)

@app.post("/api/set-session")
def set_session():
    res = RedirectResponse(url="/visitor-home", status_code=303)
    res.set_cookie(key="kvkk_session", value="onayli", max_age=86400)
    return res

@app.get("/api/logout")
def logout():
    res = RedirectResponse(url="/", status_code=303)
    res.delete_cookie(key="kvkk_session")
    return res

@app.get("/visitor-home", response_class=HTMLResponse)
def visitor_home(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    html = """
    <h2>🌾 Altınköy Ziyaretçi Rehberi</h2>
    <p>Müzede rehberiniz cebinizde!</p>
    
    <div style="background:#fff8e1; border-left:4px solid #ffa000; padding:10px; border-radius:6px; margin-bottom:12px; font-size:12px; color:#b26a00;">
        <b>Önemli Kural:</b> Dışarıdan yiyecek getirmek, piknik/kahvaltı yapmak ve dereye girmek yasaktır.
    </div>

    <a href="/qr-chat" class="btn btn-warning">🎤 Yapay Zeka Asistanına Soru Sor</a>
    <a href="/visitor-portal" class="btn btn-danger">📍 Acil Durum & Ekip Çağır</a>
    <a href="/survey" class="btn btn-primary">⭐ Ziyaretçi Memnuniyet Anketi</a>
    
    <div class="footer-link"><a href="/api/logout">Oturumu Kapat</a></div>
    """
    return render_page("Ziyaretçi Paneli", html)

@app.get("/admin-panel", response_class=HTMLResponse)
def admin_panel():
    html = """
    <h2>🛡️ Müdürlük Yönetim Paneli</h2>
    <p>Üst düzey yönetim ve denetim merkezi.</p>
    <a href="/qr-manager" class="btn" style="background:#2980b9; color:white;">🔗 Dinamik QR & Direk Yönetimi</a>
    <a href="/staff-management" class="btn" style="background:#8e44ad; color:white;">👥 Personel & Bölge Yönetimi</a>
    <a href="/whatsapp-sim" class="btn" style="background:#27ae60; color:white;">📱 WhatsApp Grup Akışı</a>
    <a href="/heatmap" class="btn" style="background:#d35400; color:white;">🔥 Canlı Isı Haritası</a>
    <a href="/live-dashboard" class="btn btn-dark">📊 Raporlar & Anket Ortalamaları</a>
    <div class="footer-link"><a href="/" style="color:#c0392b; font-weight:bold;">← Ziyaretçi Ekranına Dön</a></div>
    """
    return render_page("Müdürlük Paneli", html)

@app.get("/r/{code_id}")
def redirect_dynamic_qr(code_id: str, kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    if code_id in DYNAMIC_QRS:
        q = DYNAMIC_QRS[code_id]
        heatmap_data.append({"zone": q["zone"], "type": f"QR Okutuldu ({code_id})", "time": datetime.now().strftime("%H:%M"), "lat": q["lat"], "lon": q["lon"]})
        return RedirectResponse(url=q["target_url"], status_code=303)
    return RedirectResponse(url="/visitor-home", status_code=303)

@app.get("/uyari/degirmen-bolgesi", response_class=HTMLResponse)
def degirmen_uyari(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    html = """
    <h2 style="color:#c0392b;">⚠️ Değirmen & Dere Bölgesi</h2>
    <div style="background:#fde8e8; border-left:4px solid #e74c3c; padding:10px; border-radius:6px; margin-bottom:12px; font-size:12px; color:#c0392b;">
        <b>Suya Girmek Yasaktır:</b> Can güvenliğiniz için dere yataklarına ve sulara yaklaşmak kesinlikle yasaktır.
    </div>
    <a href="/qr-chat" class="btn btn-warning">🎤 Asistana Soru Sor</a>
    <a href="/visitor-home" class="btn btn-dark">← Ana Ekrana Dön</a>
    """
    return render_page("Değirmen Bölgesi", html)

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_get(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    
    history_html = ""
    for q in reversed(qr_requests[-3:]):
        safe_reply = q['reply'].replace("'", "\\'")
        history_html += f"""
        <div style='background:#f9f9f9; padding:8px; border-radius:6px; margin-bottom:8px; font-size:12px;'>
            <b>Sen:</b> {q['msg']}<br>
            <b>Asistan:</b> {q['reply']}<br>
            <button onclick="speakText('{safe_reply}')" style="margin-top:4px; background:#27ae60; color:white; border:none; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer;">🔊 Sesli Dinle</button>
        </div>
        """

    html = f"""
    <h2>🎤 Altınköy Sesli Asistan</h2>
    <p>Müze kuralları hakkında dilediğinizi sorun.</p>
    <form id="chatForm" action="/api/qr-chat-post" method="POST" onsubmit="getLocAndSubmit(event)">
        <input type="text" id="msgInput" name="message" placeholder="Örn: Piknik yapabilir miyim?" autocomplete="off" required style="width:100%; padding:10px; border:1px solid #ccc; border-radius:8px; box-sizing:border-box; margin-bottom:8px;">
        <input type="hidden" id="latField" name="lat" value="39.9334">
        <input type="hidden" id="lonField" name="lon" value="32.8597">
        <button type="submit" class="btn btn-warning">Yapay Zekaya Sor</button>
    </form>
    <div style="margin-top:10px;">{history_html}</div>
    <a href="/visitor-home" class="btn btn-dark" style="margin-top:10px;">← Ana Ekrana Dön</a>
    
    <script>
        function getLocAndSubmit(e) {{
            e.preventDefault();
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition((pos) => {{
                    document.getElementById('latField').value = pos.coords.latitude;
                    document.getElementById('lonField').value = pos.coords.longitude;
                    document.getElementById('chatForm').submit();
                }}, () => {{
                    document.getElementById('chatForm').submit();
                }});
            }} else {{
                document.getElementById('chatForm').submit();
            }}
        }}
    </script>
    """
    return render_page("AI Asistan", html)

@app.post("/api/qr-chat-post")
def qr_chat_post(message: str = Form(...), lat: float = Form(39.9334), lon: float = Form(32.8597)):
    reply = ask_groq_ai(message, lat=lat, lon=lon)
    z = find_nearest_zone(lat, lon)
    heatmap_data.append({"zone": z, "type": f"Soru: {message[:15]}", "time": datetime.now().strftime("%H:%M"), "lat": lat, "lon": lon})
    qr_requests.append({"msg": message, "reply": reply})
    return RedirectResponse(url="/qr-chat", status_code=303)

@app.get("/visitor-portal", response_class=HTMLResponse)
def visitor_portal(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    html = """
    <h2 style="color:#c0392b;">📍 Acil Durum Ekibi</h2>
    <p>Yardıma ihtiyacınız varsa butona basarak konumunuzu saha ekibine iletin.</p>
    <form id="emergencyForm" action="/api/emergency-form" method="POST" onsubmit="getEmergLoc(event)">
        <input type="hidden" id="eLat" name="lat" value="39.9334">
        <input type="hidden" id="eLon" name="lon" value="32.8597">
        <button type="submit" class="btn btn-danger">Saha Ekibine Konum Gönder</button>
    </form>
    <a href="/visitor-home" class="btn btn-dark" style="margin-top:10px;">← Ana Ekrana Dön</a>
    
    <script>
        function getEmergLoc(e) {{
            e.preventDefault();
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition((pos) => {{
                    document.getElementById('eLat').value = pos.coords.latitude;
                    document.getElementById('eLon').value = pos.coords.longitude;
                    document.getElementById('emergencyForm').submit();
                }}, () => {{
                    document.getElementById('emergencyForm').submit();
                }});
            }} else {{
                document.getElementById('emergencyForm').submit();
            }}
        }}
    </script>
    """
    return render_page("Acil Durum", html)

@app.post("/api/emergency-form", response_class=HTMLResponse)
def emergency_form(lat: float = Form(39.9334), lon: float = Form(32.8597)):
    z = find_nearest_zone(lat, lon)
    heatmap_data.append({"zone": z, "type": "Acil Durum Sinyali", "time": datetime.now().strftime("%H:%M"), "lat": lat, "lon": lon})
    nearest = min(STAFF_LIST, key=lambda s: 0 if s['zone'] == z else 1)
    html = f"""
    <h2 style="color:#27ae60;">✔️ Sinyal Alındı</h2>
    <p><b>Bölgeniz:</b> {z}<br>En yakın sorumlu <b>{nearest['name']}</b> ({nearest['phone']}) konumunuza yönlendirildi.</p>
    <a href="/visitor-home" class="btn btn-primary" style="margin-top:15px;">Ana Ekrana Dön</a>
    """
    return render_page("Acil Durum", html)

@app.get("/survey", response_class=HTMLResponse)
def survey_page(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return RedirectResponse(url="/", status_code=303)
    html = """
    <h2>⭐ Ziyaretçi Anketi</h2>
    <form action="/api/submit-survey" method="POST">
        <label style="font-size:12px; font-weight:bold;">Memnuniyet Puanınız:</label>
        <select name="score" style="width:100%; padding:10px; margin:5px 0 12px 0; border-radius:6px; border:1px solid #ccc;">
            <option value="5">⭐⭐⭐⭐⭐ Mükemmel</option>
            <option value="4">⭐⭐⭐⭐ Çok İyi</option>
            <option value="3">⭐⭐⭐ Orta</option>
        </select>
        <button type="submit" class="btn btn-primary">Anketi Gönder</button>
    </form>
    <a href="/visitor-home" class="btn btn-dark" style="margin-top:10px;">← Ana Ekrana Dön</a>
    """
    return render_page("Anket", html)

@app.post("/api/submit-survey")
def submit_survey(score: int = Form(...)):
    survey_responses.append({"score": score})
    return RedirectResponse(url="/visitor-home", status_code=303)

@app.get("/qr-manager", response_class=HTMLResponse)
def qr_manager(request: Request):
    base_url = str(request.base_url)
    items = ""
    for code_id, data in DYNAMIC_QRS.items():
        link = f"{base_url}r/{code_id}"
        items += f"<div style='background:#f9f9f9; padding:10px; margin-bottom:8px; border-radius:6px; font-size:12px;'><b>{data['title']}</b><br>Link: <code>{link}</code></div>"
    html = f"<h2>🔗 Dinamik QR Yönetimi</h2>{items}<a href='/admin-panel' class='btn btn-dark' style='margin-top:10px;'>← Yönetim Paneline Dön</a>"
    return render_page("QR Yönetimi", html)

@app.get("/staff-management", response_class=HTMLResponse)
def staff_management():
    rows = "".join([f"<tr><td style='padding:6px;'><b>{s['name']}</b><br>{s['title']}</td><td style='padding:6px;'>{s['zone']}</td><td style='padding:6px;'>{s['phone']}</td></tr>" for s in STAFF_LIST])
    html = f"<h2>👥 Personel Yönetimi</h2><table width='100%' style='border-collapse:collapse; font-size:12px;'><tr style='background:#eee; text-align:left;'><th style='padding:6px;'>Personel</th><th style='padding:6px;'>Bölge</th><th style='padding:6px;'>Tel</th></tr>{rows}</table><a href='/admin-panel' class='btn btn-dark' style='margin-top:15px;'>← Yönetim Paneline Dön</a>"
    return render_page("Personel", html)

@app.get("/whatsapp-sim", response_class=HTMLResponse) 
def whatsapp_sim():
    feed = "".join([f"<div style='background:#e1f5fe; padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px;'><b>{i['sender']}</b> [{i['time']}]: {i['message']}</div>" for i in reversed(whatsapp_feed[-5:])])
    html = f"""
    <h2>📱 WhatsApp Akışı</h2>
    <form action="/api/wa-post" method="POST">
        <input type="text" name="sender" value="Onur Yılmaz (Amir)" required style="width:100%; padding:8px; margin-bottom:6px; border-radius:6px; border:1px solid #ccc; font-size:12px;">
        <input type="text" name="message" placeholder="Mesaj yaz..." autocomplete="off" required style="width:100%; padding:8px; margin-bottom:6px; border-radius:6px; border:1px solid #ccc; font-size:12px;">
        <button type="submit" class="btn" style="background:#25D366; color:white;">Gönder</button>
    </form>
    <div style="margin-top:10px;">{feed if feed else "<p style='font-size:12px;'>Mesaj yok.</p>"}</div>
    <a href="/admin-panel" class='btn btn-dark' style='margin-top:10px;'>← Yönetim Paneline Dön</a>
    """
    return render_page("WhatsApp", html)

@app.post("/api/wa-post")
def wa_post(sender: str = Form(...), message: str = Form(...)):
    whatsapp_feed.append({"sender": sender, "message": message, "time": datetime.now().strftime("%H:%M")})
    return RedirectResponse(url="/whatsapp-sim", status_code=303)

@app.get("/heatmap", response_class=HTMLResponse)
def heatmap():
    stats = {z: sum(1 for h in heatmap_data if h['zone'] == z) for z in PARK_ZONES}
    bars = "".join([f"<div style='background:#fff3e0; padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px;'><b>{z}:</b> {count} Sinyal</div>" for z, count in stats.items()])
    html = f"<h2>🔥 Isı Haritası</h2>{bars}<a href='/admin-panel' class='btn btn-dark' style='margin-top:15px;'>← Yönetim Paneline Dön</a>"
    return render_page("Isı Haritası", html)

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    avg = sum(s['score'] for s in survey_responses) / len(survey_responses) if survey_responses else 5.0
    html = f"<h2>📊 Rapor Paneli</h2><p><b>Ortalama Memnuniyet:</b> ⭐ {avg:.1f} / 5.0 ({len(survey_responses)} Anket)</p><a href='/admin-panel' class='btn btn-dark' style='margin-top:15px;'>← Yönetim Paneline Dön</a>"
    return render_page("Raporlar", html)
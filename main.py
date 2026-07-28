from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import os
import math
import requests
import time

app = FastAPI(title="Altınköy Otonom Sistem", version="4.9")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

whatsapp_feed = []
incident_logs = []
qr_requests = []
heatmap_data = []
survey_responses = []

# Spam / Manipülasyon Önleme (Rate Limiting)
user_cooldowns = {}

# Dinamik Direk & QR Yönetim Veritabanı
DYNAMIC_QRS = {
    "direk-01": {
        "zone": "Köy Meydanı", 
        "title": "Köy Meydanı Ana Direk", 
        "target_url": "/qr-chat?zone=meydan", 
        "desc": "Meydan aktiviteleri ve kahve duyurusu",
        "lat": 39.9334, "lon": 32.8597
    },
    "direk-02": {
        "zone": "Yel ve Su Değirmenleri", 
        "title": "Değirmen & Dere Yolu Direği", 
        "target_url": "/uyari/degirmen-bolgesi", 
        "desc": "Su değirmeni, dere kenarı piknik ve kahvaltı uyarı noktası",
        "lat": 39.9360, "lon": 32.8520
    },
    "direk-03": {
        "zone": "Geleneksel Çantı Evler", 
        "title": "Çantı Evler Giriş Direği", 
        "target_url": "/qr-chat?zone=canti", 
        "desc": "Mimari tarih ve sesli rehber",
        "lat": 39.9300, "lon": 32.8600
    }
}

STAFF_LIST = [
    {"id": 1, "name": "Onur Yılmaz", "title": "Saha Sorumlusu & Operasyon Amiri", "lat": 39.9334, "lon": 32.8597, "phone": "0537 939 36 77", "zone": "Köy Meydanı"},
    {"id": 2, "name": "Fırat Reis", "title": "Güvenlik & Değirmenler Sorumlusu", "lat": 39.9360, "lon": 32.8520, "phone": "0553 691 57 52", "zone": "Yel ve Su Değirmenleri"},
    {"id": 3, "name": "Hakan Taşkale", "title": "Çantı Evler & Zanaat Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0546 801 61 72", "zone": "Geleneksel Çantı Evler"}
]

PARK_ZONES = {
    "Köy Meydanı": {"lat": 39.9334, "lon": 32.8597, "desc": "Köy kahvesi, cami, okul, muhtarlık ve bakkalın bulunduğu merkez."},
    "Geleneksel Çantı Evler": {"lat": 39.9300, "lon": 32.8600, "desc": "Çivi çakılmadan yapılan asırlık ahşap çantı evler."},
    "Yel ve Su Değirmenleri": {"lat": 39.9360, "lon": 32.8520, "desc": "Çalışır durumda yel değirmeni, su değirmeni ve dere yatağı alanı."},
    "Doğa ve Hayvanlar / At Menajı": {"lat": 39.9280, "lon": 32.8630, "desc": "Serbest gezen evcil hayvanlar, at menajı ve yürüyüş yolları."},
    "Eski Meslekler ve Çarşı": {"lat": 39.9320, "lon": 32.8550, "desc": "Kalaycı, nalbant gibi unutulan mesleklerin canlandırıldığı alan."},
    "Ana Giriş & Taş Fırın": {"lat": 39.9310, "lon": 32.8500, "desc": "Müze girişi, otopark ve taş fırın köy ekmeği satış noktası."}
}

ALTINKOY_LOCATIONS = {
    "çantı ev": "Geleneksel çantı evler, çivi çakılmadan bindirme tekniğiyle yapılmış asırlık yapılardır.",
    "değirmen": "Çalışır durumdaki yel değirmeni ve su değirmeni müzenin kuzeybatı tarafındadır.",
    "dere": "Değirmen kenarındaki dere yatağı ve su boyu dinlenme alanıdır. Can güvenliği için suya girmek kesinlikle yasaktır.",
    "piknik": "Müzemizde piknik yapmak ve dışarıdan yiyecek içecek getirmek kurallarımız gereği kesinlikle yasaktır. İhtiyaçlarınız için köy fırınımız ve kahvemiz hizmetinizdedir.",
    "kahvaltı": "Dere kenarlarında kahvaltı yapmak veya dışarıdan yiyecek içecek getirmek yasaktır. Köy kahvemizde taze kahvaltı ürünlerimiz bulunmaktadır.",
    "köy meydanı": "Köy meydanında köy kahvesi, cami, okul, muhtarlık ve bakkal yer almaktadır.",
    "meslekler": "Kalaycı, nalbant ve çoban gibi eski meslekler alanında geleneksel zanaatlar canlı olarak gösterilmektedir.",
    "hayvanlar": "Serbest gezen evcil hayvanlar ve geniş yürüyüş yolları doğa alanındadır.",
    "köy ekmeği": "Taş fırında yapılan geleneksel köy ekmeği ve organik ürünler ana giriş yakınındadır.",
    "tuvalet": "En yakın tuvalet köy meydanı yakınlarındadır.",
    "otopark": "Ana araç otoparkı müze girişindedir. Çalışma saatlerimiz Pazartesi hariç 10.00 - 20.00 arasıdır."
}

def find_nearest_zone(lat: float, lon: float) -> str:
    nearest_zone = "Köy Meydanı"
    min_dist = float('inf')
    for zone_name, coords in PARK_ZONES.items():
        dist = math.sqrt((lat - coords["lat"])*2 + (lon - coords["lon"])*2)
        if dist < min_dist:
            min_dist = dist
            nearest_zone = zone_name
    return nearest_zone

def ask_groq_ai(prompt: str) -> str:
    p_lower = prompt.lower()
    for key, desc in ALTINKOY_LOCATIONS.items():
        if key in p_lower:
            return f"📍 {desc}"

    if GROQ_API_KEY == "BURAYA_GROQ_API_KEY_GIRINIZ" or not GROQ_API_KEY:
        return f"Altınköy Asistanı: '{prompt}' dedin ya, hemen söyleyeyim; bizim işletme kurallarımız gereği dışarıdan yiyecek içecek getirmek, piknik/kahvaltı yapmak ve dere yataklarına girmek kesinlikle yasaktır. Çalışma saatlerimiz Pazartesi hariç 10:00 - 20:00 arasıdır!"

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system", 
                "content": (
                    "Sen Altınköy Açık Hava Müzesi'nin her şeyi bilen, samimi, hoşgörülü ama kurallardan asla taviz vermeyen kıdemli reklam yüzü ve turist rehberisin. "
                    "Kuralların ve karakterin şunlar:\n"
                    "1. Asla uzun uzadıya, boğucu, edebi veya roman gibi mesajlar atma; kısa, net ve öz ol.\n"
                    "2. Sınırlarını bil: Sadece Altınköy hakkında konuş, köyün dışına çıkma.\n"
                    "3. Hayal gücün yok, tamamen gerçekçi ve somut bilgiler ver.\n"
                    "4. EN ÖNEMLİ KURALLAR: Dışarıdan yiyecek içecek getirmek, piknik ve kahvaltı yapmak, dere yatakları/su içine girmek kesinlikle yasaktır. Ziyaretçi bunu sorduğunda veya ima ettiğinde net, kuralcı ama sıcak bir dille uyar."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return f"Buyur canım, '{prompt}' dedin ama unutma; müzemizde dışarıdan yiyecek getirmek, piknik/kahvaltı yapmak ve suya girmek yasaktır. Köy kahvemize bekleriz!"

@app.get("/", response_class=HTMLResponse)
def home_page(kvkk_session: str = Cookie(None)):
    if kvkk_session != "onayli":
        return """
        <html>
            <head><title>Altınköy Açık Hava Müzesi - Giriş</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
            <body style="font-family:Segoe UI; text-align:center; background:#f4f6f9; padding:30px;">
                <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:420px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.05); text-align:left;">
                    <h2 style="color:#2c3e50; text-align:center;">🌾 Altınköy Açık Hava Müzesi</h2>
                    <p style="color:gray; font-size:12px; text-align:center;">Akıllı Asistan ve Canlı Konum Sistemine Hoş Geldiniz</p>
                    
                    <form action="/api/set-session" method="POST">
                        <div style="background:#f9f9f9; padding:10px; border-radius:6px; font-size:11px; color:#555; max-height:100px; overflow-y:auto; margin-bottom:12px; border:1px solid #eee;">
                            <b>KVKK Genel Aydınlatma Metni & Açık Rıza:</b> 6698 sayılı KVKK kapsamında; acil durum konum yönlendirmesi, yapay zeka asistanı akışı, ısı haritası analizi ve müze içi deneyimin iyileştirilmesi amacıyla konum ve kullanım verileriniz işlenmektedir.
                        </div>
                        
                        <label style="font-size:12px; display:block; margin-bottom:15px; cursor:pointer;">
                            <input type="checkbox" required> Aydınlatma metnini okudum, anladım ve tüm müze seansı için açık rıza veriyorum.
                        </label>

                        <button type="submit" style="background:#27ae60; color:white; padding:14px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:14px; cursor:pointer;">🚀 Oturumu Başlat & Müzeye Gir</button>
                    </form>
                </div>
            </body>
        </html>
        """
    
    return """
    <html>
        <head><title>Altınköy Açık Hava Müzesi Otonom Sistem</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; background:#f4f6f9; padding:30px;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:450px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2>🌾 Altınköy Açık Hava Müzesi v4.9</h2>
                <p style="color:green; font-size:12px; font-weight:bold;">✔️ KVKK Genel Oturumu Aktif (Anti-Spam Korumalı)</p>
                <a href="/qr-manager" style="display:block; background:#2980b9; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🔗 Dinamik Direk & QR Yönetimi</a>
                <a href="/staff-management" style="display:block; background:#8e44ad; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">👥 Personel Yönetimi</a>
                <a href="/whatsapp-sim" style="display:block; background:#25D366; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📱 WhatsApp Grup Akışı</a>
                <a href="/visitor-portal" style="display:block; background:#E74C3C; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🚶 Acil Durum & Konum Paneli</a>
                <a href="/qr-chat" style="display:block; background:#d35400; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🎤 Altınköy AI Asistanı & Sesli Tarif</a>
                <a href="/survey" style="display:block; background:#27ae60; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">⭐ Ziyaretçi Memnuniyet Anketi</a>
                <a href="/heatmap" style="display:block; background:#e67e22; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">🔥 Canlı GPS Isı Haritası</a>
                <a href="/live-dashboard" style="display:block; background:#34495E; color:white; padding:14px; margin:10px 0; text-decoration:none; border-radius:8px; font-weight:bold;">📊 Müdürlük Rapor Paneli</a>
                <br><a href="/api/logout" style="color:#c0392b; font-size:12px; text-decoration:none;">Oturumu Kapat / Çıkış Yap</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/set-session")
def set_session():
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="kvkk_session", value="onayli", max_age=86400)
    return response

@app.get("/api/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="kvkk_session")
    return response

# --- DİNAMİK DİREK & QR YÖNETİMİ ---
@app.get("/qr-manager", response_class=HTMLResponse)
def qr_manager_page(request: Request):
    base_url = str(request.base_url)
    qr_rows = ""
    for code_id, data in DYNAMIC_QRS.items():
        full_redirect_link = f"{base_url}r/{code_id}"
        qr_img_url = f"https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={full_redirect_link}"
        
        qr_rows += f"""
        <div style="background:white; border:1px solid #ddd; padding:15px; border-radius:8px; margin-bottom:15px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap;">
            <div>
                <h4 style="margin:0 0 5px 0; color:#2c3e50;">{data['title']} (Kod: <code>{code_id}</code>)</h4>
                <p style="margin:0 0 5px 0; font-size:12px; color:gray;">Bölge: <b>{data['zone']}</b> — {data['desc']}<br>Sabit Koordinat: <code>{data['lat']}, {data['lon']}</code></p>
                <p style="margin:0; font-size:11px;">Mevcut Yönlendirme: <a href="{data['target_url']}" target="_blank">{data['target_url']}</a></p>
            </div>
            <div style="text-align:center;">
                <img src="{qr_img_url}" alt="QR" style="border-radius:4px; border:1px solid #eee;"><br>
                <form action="/api/update-qr" method="POST" style="margin-top:5px;">
                    <input type="hidden" name="code_id" value="{code_id}">
                    <input type="text" name="new_url" value="{data['target_url']}" style="font-size:11px; padding:3px; width:120px;" placeholder="Yeni Hedef URL">
                    <button type="submit" style="font-size:10px; background:#2980b9; color:white; border:none; padding:4px 6px; border-radius:3px; cursor:pointer;">Değiştir</button>
                </form>
            </div>
        </div>
        """
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:700px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#2980b9;">🔗 Dinamik Direk & QR Yönetim Paneli</h2>
                <p style="font-size:12px; color:gray;">Müzedeki direklere bir kez QR basıp yapıştırın. İstediğiniz zaman bu panelden arkasındaki yönlendirmeyi anında değiştirin.</p>
                <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
                {qr_rows}
                <br><a href="/" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/update-qr")
def update_qr(code_id: str = Form(...), new_url: str = Form(...)):
    if code_id in DYNAMIC_QRS:
        DYNAMIC_QRS[code_id]["target_url"] = new_url
    return RedirectResponse(url="/qr-manager", status_code=303)

@app.get("/r/{code_id}")
def redirect_dynamic_qr(code_id: str):
    if code_id in DYNAMIC_QRS:
        qr_info = DYNAMIC_QRS[code_id]
        heatmap_data.append({
            "zone": qr_info["zone"], 
            "type": f"Fiziki Direk Okutuldu ({code_id})", 
            "time": datetime.now().strftime("%H:%M:%S"), 
            "lat": qr_info["lat"], 
            "lon": qr_info["lon"]
        })
        return RedirectResponse(url=qr_info["target_url"], status_code=303)
    return RedirectResponse(url="/", status_code=303)

# Değirmen ve Dere Bölgesi Piknik & Güvenlik Kural Bildirim Sayfası
@app.get("/uyari/degirmen-bolgesi", response_class=HTMLResponse)
def degirmen_uyari_page():
    return """
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Altınköy - Değirmen & Dere Bölgesi Kuralları</title></head>
        <body style="font-family:Segoe UI; background:#fff5f5; padding:20px; text-align:center;">
            <div style="max-width:480px; margin:auto; background:white; padding:30px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05); text-align:left;">
                <h2 style="color:#c0392b; text-align:center;">⚠️ Değirmen & Dere Bölgesi Kuralları</h2>
                <div style="background:#fef2f2; border-left:4px solid #ef4444; padding:12px; margin:15px 0; border-radius:4px;">
                    <p style="margin:0 0 10px 0; font-size:13px; color:#991b1b; font-weight:bold;">🚨 1. Suya Girmek Yasak ve Tehlikelidir:</p>
                    <p style="margin:0; font-size:12px; color:#7f1d1d;">Can güvenliğiniz açısından su değirmeni çevresindeki dere yatağına ve sulara girmek kesinlikle yasak ve tehlikelidir.</p>
                </div>
                <div style="background:#fffbeb; border-left:4px solid #f59e0b; padding:12px; margin:15px 0; border-radius:4px;">
                    <p style="margin:0 0 10px 0; font-size:13px; color:#92400e; font-weight:bold;">🥪 2. Dışarıdan Yiyecek, İçecek, Piknik ve Kahvaltı Yasaktır:</p>
                    <p style="margin:0; font-size:12px; color:#78350f;">Dere kenarında ve müzemiz sınırları içerisinde piknik yapmak, kahvaltı yapmak ve dışarıdan yiyecek/içecek getirmek işletme kurallarımız gereği kesinlikle yasaktır. İhtiyaçlarınız için köy fırınımızı ve köy kahvemizi ziyaret edebilirsiniz.</p>
                </div>
                <br><a href="/qr-chat" style="display:block; background:#2980b9; color:white; padding:12px; text-decoration:none; border-radius:6px; text-align:center; font-weight:bold;">🎤 Soru Sormak İçin Asistana Git</a>
                <br><div style="text-align:center;"><a href="/" style="color:gray; font-size:12px; text-decoration:none;">← Ana Sayfa</a></div>
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
                    <input type="text" name="zone" placeholder="Sorumlu Olduğu Bölge" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <input type="text" name="phone" placeholder="Telefon" required style="width:100%; padding:10px; margin:5px 0;"><br>
                    <button type="submit" style="background:#8e44ad; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold;">Kaydet</button>
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
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <script>
                function getLocationAndSubmit(event) {
                    event.preventDefault();
                    const status = document.getElementById('status');

                    if (!navigator.geolocation) {
                        status.innerText = 'Tarayıcınız konum desteklemiyor. Varsayılan konum gönderiliyor.';
                        document.getElementById('emergencyForm').submit();
                        return;
                    }
                    status.innerText = 'Anlık GPS konumunuz alınıyor...';
                    navigator.geolocation.getCurrentPosition((position) => {
                        document.getElementById('lat').value = position.coords.latitude;
                        document.getElementById('lon').value = position.coords.longitude;
                        document.getElementById('emergencyForm').submit();
                    }, () => {
                        status.innerText = 'Konum izni reddedildi. Varsayılan konum ile gönderiliyor.';
                        document.getElementById('emergencyForm').submit();
                    });
                }
            </script>
        </head>
        <body style="font-family:Segoe UI; background:#fff5f5; text-align:center; padding:30px;">
            <div style="background:white; padding:25px; border-radius:12px; display:inline-block; max-width:420px; width:100%; text-align:left;">
                <h2 style="color:#c0392b; text-align:center;">🚨 Acil Durum & Canlı Konum</h2>
                <p style="font-size:12px; color:gray; text-align:center;">Müze içinde en yakın saha ekibini yönlendirmek için konumunuz alınır.</p>
                
                <form id="emergencyForm" action="/api/emergency-form" method="POST" onsubmit="getLocationAndSubmit(event)">
                    <input type="hidden" id="lat" name="lat" value="39.9334">
                    <input type="hidden" id="lon" name="lon" value="32.8597">
                    
                    <div style="background:#e8f8f5; padding:8px; border-radius:6px; font-size:11px; color:#27ae60; margin-bottom:15px; text-align:center; font-weight:bold;">
                        ✔️ KVKK Genel Seans Onayınız Aktif
                    </div>

                    <button type="submit" style="background:#e74c3c; color:white; padding:14px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:14px; cursor:pointer;">📍 Canlı Konumumu Gönder & Ekip İste</button>
                </form>
                <p id="status" style="margin-top:10px; font-size:12px; color:#e67e22; text-align:center;"></p>
                <br><div style="text-align:center;"><a href="/">← Ana Sayfa</a></div>
            </div>
        </body>
    </html>
    """

@app.post("/api/emergency-form", response_class=HTMLResponse)
def emergency_form(lat: float = Form(39.9334), lon: float = Form(32.8597)):
    detected_zone = find_nearest_zone(lat, lon)
    
    zone_warning = ""
    if "Değirmen" in detected_zone:
        zone_warning = "⚠️ DİKKAT: Su değirmeni ve dere yatağı bölgesindesiniz! Can güvenliğiniz için suya girmek ve dışarıdan yiyecek/içecek getirmek kesinlikle yasaktır."
    
    heatmap_data.append({"zone": detected_zone, "type": "Acil Durum (GPS)", "time": datetime.now().strftime("%H:%M:%S"), "lat": lat, "lon": lon})
    nearest = min(STAFF_LIST, key=lambda s: 0 if s['zone'] == detected_zone else 1)
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; padding:40px; background:#e8f8f5;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:420px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#27ae60;">✔️ Sinyal Alındı & Ekip Yönlendirildi</h2>
                <p style="font-size:13px; color:#c0392b; font-weight:bold;">{zone_warning}</p>
                <p><b>Tespit Edilen Bölge:</b> {detected_zone}<br><span style="font-size:11px; color:gray;">GPS: {lat:.4f}, {lon:.4f}</span></p>
                <p><b>İlgili Personel:</b> {nearest['name']} ({nearest['title']})<br>Tel: {nearest['phone']}</p>
                <br><a href="/visitor-portal" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Geri Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/survey", response_class=HTMLResponse)
def survey_page():
    feed = "".join([f"<div style='background:#f9f9f9; padding:10px; margin-bottom:8px; border-radius:6px; border:1px solid #eee;'>⭐ Puan: <b>{s['score']}/5</b> | Temizlik: <b>{s['clean']}</b> | İlgi: <b>{s['staff']}</b><br><span style='font-size:13px; color:#555;'>Görüş: {s['comment']}</span> <span style='font-size:11px; color:gray; float:right;'>{s['time']}</span></div>" for s in reversed(survey_responses)])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:550px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#27ae60;">⭐ Altınköy Ziyaretçi Memnuniyet Anketi</h2>
                <p style="font-size:12px; color:gray;">Deneyiminizi bizimle paylaşarak müzemizi geliştirmemize yardımcı olun.</p>
                <form action="/api/submit-survey" method="POST">
                    <label style="font-size:13px; font-weight:bold;">Genel Memnuniyet Puanınız (1-5):</label>
                    <select name="score" style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px;">
                        <option value="5">⭐⭐⭐⭐⭐ 5 - Mükemmel</option>
                        <option value="4">⭐⭐⭐⭐ 4 - Çok İyi</option>
                        <option value="3">⭐⭐⭐ 3 - Orta</option>
                        <option value="2">⭐⭐ 2 - Geliştirilmeli</option>
                        <option value="1">⭐ 1 - Zayıf</option>
                    </select>
                    
                    <label style="font-size:13px; font-weight:bold;">Müze Temizliği & Düzeni:</label>
                    <select name="clean" style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px;">
                        <option value="Çok İyi">Çok İyi / Temiz</option>
                        <option value="İyi">İyi</option>
                        <option value="Yetersiz">Yetersiz</option>
                    </select>

                    <label style="font-size:13px; font-weight:bold;">Personel İlgisi ve Rehberlik:</label>
                    <select name="staff" style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px;">
                        <option value="Çok Yardımsever">Çok Yardımsever</option>
                        <option value="Normal">Normal</option>
                        <option value="İlgisiz">İlgisiz</option>
                    </select>

                    <label style="font-size:13px; font-weight:bold;">Görüş, Öneri ve Yorumlarınız:</label>
                    <textarea name="comment" rows="3" placeholder="Örn: Köy ekmeği harikaydı, çantı evleri çok beğendik..." style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"></textarea>

                    <button type="submit" style="background:#27ae60; color:white; border:none; padding:14px; width:100%; border-radius:8px; font-weight:bold; cursor:pointer;">Anketi Gönder</button>
                </form>
                <br><h3>Değerlendirme Akışı</h3>
                {feed if feed else "<p style='color:gray;'>Henüz anket doldurulmadı.</p>"}
                <br><a href="/" style="display:inline-block; margin-top:10px; text-decoration:none; color:#2c3e50;">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/submit-survey")
def submit_survey(score: int = Form(...), clean: str = Form(...), staff: str = Form(...), comment: str = Form("")):
    survey_responses.append({"score": score, "clean": clean, "staff": staff, "comment": comment, "time": datetime.now().strftime("%H:%M:%S")})
    return RedirectResponse(url="/survey", status_code=303)

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_get():
    chat_history = "".join([f"<div style='margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:8px;'><b>Ziyaretçi:</b> {q['msg']}<br><div style='background:#eef2f7; padding:8px; border-radius:6px; margin-top:4px;'><b>Asistan:</b> {q['reply']}</div><button onclick=\"speakText('{q['reply']}')\" style='margin-top:5px; background:#27ae60; color:white; border:none; padding:6px 12px; border-radius:4px; font-size:12px; cursor:pointer;'>🔊 Sesli Tarif Dinle</button></div>" for q in reversed(qr_requests)])
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
                function askWithLocation(event) {{
                    event.preventDefault();
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
        </head>
        <body style="font-family:Segoe UI; padding:20px; background:#fdfbf7;">
            <div style="max-width:550px; margin:auto; background:white; padding:20px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#d35400;">🎤 Altınköy AI Asistanı & Sesli Tarif</h2>
                <p style="font-size:12px; color:gray;">Örn: Piknik yapabilir miyim? Kahvaltı getirebilir miyim? Dereye girebilir miyim?</p>
                <form id="chatForm" action="/api/qr-chat-post" method="POST" onsubmit="askWithLocation(event)">
                    <input type="text" id="msgInput" name="message" placeholder="Müze hakkında ne öğrenmek istemiştiniz?" required style="width:100%; padding:12px; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"><br>
                    <input type="hidden" id="latField" name="lat" value="39.9334">
                    <input type="hidden" id="lonField" name="lon" value="32.8597"><br>
                    
                    <div style="background:#e8f8f5; padding:8px; border-radius:6px; font-size:11px; color:#27ae60; margin-bottom:12px; text-align:center; font-weight:bold;">
                        ✔️ KVKK Genel Seans Onayınız Aktif (Anti-Spam Korumalı)
                    </div>

                    <button type="submit" style="background:#d35400; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold; cursor:pointer;">Yapay Zekaya Sor (Konumlu)</button>
                </form>
                <br><h3>Geçmiş Soru & Yanıtlar</h3>
                {chat_history if chat_history else "<p style='color:gray;'>Henüz soru sorulmadı.</p>"}
                <br><a href="/">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/qr-chat-post")
def qr_chat_post(request: Request, message: str = Form(...), lat: float = Form(39.9334), lon: float = Form(32.8597)):
    client_ip = request.client.host if request.client else "local"
    current_time = time.time()
    
    if client_ip in user_cooldowns:
        if current_time - user_cooldowns[client_ip] < 10:
            reply = "⚠️ Çok hızlı soru gönderiyorsunuz. Lütfen birkaç saniye bekleyip tekrar deneyin."
            qr_requests.append({"msg": message, "reply": reply})
            return RedirectResponse(url="/qr-chat", status_code=303)
            
    user_cooldowns[client_ip] = current_time

    reply = ask_groq_ai(message)
    detected_zone = find_nearest_zone(lat, lon)
    heatmap_data.append({"zone": detected_zone, "type": f"Soru: {message[:20]}...", "time": datetime.now().strftime("%H:%M:%S"), "lat": lat, "lon": lon})
    qr_requests.append({"msg": message, "reply": reply})
    return RedirectResponse(url="/qr-chat", status_code=303)

@app.get("/heatmap", response_class=HTMLResponse)
def heatmap_page():
    zones = list(PARK_ZONES.keys())
    stats = {z: sum(1 for h in heatmap_data if h['zone'] == z) for z in zones}
    max_val = max(stats.values()) if stats.values() else 1
    
    bars = ""
    for z, count in stats.items():
        pct = int((count / max(max_val, 1)) * 100)
        color = "#e74c3c" if count > 3 else "#f39c12" if count > 1 else "#27ae60"
        bars += f"<div style='margin-bottom:15px;'><b>{z}</b> ({count} onaylı sinyal)<div style='background:#eee; border-radius:6px; overflow:hidden; height:22px; margin-top:5px;'><div style='width:{max(pct, 5)}%; background:{color}; height:100%; text-align:right; color:white; padding-right:8px; font-size:12px; line-height:22px;'>{count}</div></div></div>"

    log_items = "".join([f"<li>[{h['time']}] Bölge: <b>{h['zone']}</b> — {h['type']} <span style='font-size:11px; color:gray;'>(GPS: {h.get('lat', 0):.4f}, {h.get('lon', 0):.4f})</span></li>" for h in reversed(heatmap_data)])
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:650px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#e67e22;">🔥 Altınköy Canlı GPS Isı Haritası</h2>
                <p style="color:gray; font-size:13px;">Ziyaretçilerin seans onaylı paylaştığı anlık konum verilerine dayalı müze yoğunluk haritası:</p>
                <br>{bars}
                <br><h3>Canlı Konum Günlüğü</h3>
                <ul style="font-size:13px; color:#333; line-height:1.6;">{log_items if log_items else "<li>Henüz veri yok.</li>"}</ul>
                <br><a href="/" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;">← Ana Sayfa</a>
            </div>
        </body>
    </html>
    """

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    avg_score = sum(s['score'] for s in survey_responses) / len(survey_responses) if survey_responses else 0
    survey_summary = "".join([f"<li>Puan: {s['score']}/5 — {s['comment']}</li>" for s in survey_responses])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f8f9fa;">
            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:10px;">
                <h2>📊 Müdürlük Rapor Paneli</h2>
                <p><b>Ortalama Ziyaretçi Memnuniyeti:</b> ⭐ {avg_score:.1f} / 5.0 ({len(survey_responses)} anket)</p>
                <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
                <h3>Son Anket Yorumları</h3>
                <ul>{survey_summary if survey_summary else "<li>Anket verisi yok.</li>"}</ul>
                <br><a href="/" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:8px; display:inline-block;">Ana Sayfaya Dön</a>
            </div>
        </body>
    </html>
    """
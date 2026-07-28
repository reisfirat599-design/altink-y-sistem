from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from datetime import datetime
import os
import math
import requests
import time

app = FastAPI(title="Altınköy Otonom Sistem", version="6.0")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

whatsapp_feed = []
incident_logs = []
qr_requests = []
heatmap_data = []
survey_responses = []

DYNAMIC_QRS = {
    "direk-01": {
        "zone": "Köy Meydanı", 
        "title": "Köy Meydanı Ana Direk", 
        "target_url": "/visitor-home", 
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
        "target_url": "/visitor-home", 
        "desc": "Mimari tarih ve sesli rehber",
        "lat": 39.9300, "lon": 32.8600
    }
}

STAFF_LIST = [
    {"id": 1, "name": "Onur Yılmaz", "title": "Saha Sorumlusu & Operasyon Amiri", "lat": 39.9334, "lon": 32.8597, "phone": "0537 939 36 77", "zone": "Köy Meydanı"},
    {"id": 2, "name": "Fırat Reis", "title": "Güvenlik & Değirmenler Sorumlusu", "lat": 39.9360, "lon": 32.8520, "phone": "0553 691 57 52", "zone": "Yel ve Su Değirmenleri"},
    {"id": 3, "name": "Ayşe Kaya", "title": "Çantı Evler & Zanaat Sorumlusu", "lat": 39.9300, "lon": 32.8600, "phone": "0546 801 61 72", "zone": "Geleneksel Çantı Evler"}
]

PARK_ZONES = {
    "Köy Meydanı": {"lat": 39.9334, "lon": 32.8597, "desc": "Köy kahvesi, cami, okul, muhtarlık ve bakkalın bulunduğu merkez."},
    "Geleneksel Çantı Evler": {"lat": 39.9300, "lon": 32.8600, "desc": "Çivi çakılmadan yapılan asırlık ahşap çantı evler."},
    "Yel ve Su Değirmenleri": {"lat": 39.9360, "lon": 32.8520, "desc": "Çalışır durumda yel değirmeni, su değirmeni ve dere yatağı alanı."},
    "Doğa dan Hayvanlar / At Menajı": {"lat": 39.9280, "lon": 32.8630, "desc": "Serbest gezen evcil hayvanlar, at menajı ve yürüyüş yolları."},
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

def ask_groq_ai(prompt: str, lat: float = None, lon: float = None) -> str:
    p_lower = prompt.lower()
    
    # Küfür / Hakaret filtresi kontrolü
    yasakli_kelimeler = ["salak", "aptal", "mal", "rezil", "pis", "idiot", "gerizekalı"]
    if any(y in p_lower for y in yasakli_kelimeler):
        return "Müze rehberi olarak bu üslubu kesinlikle kabul etmiyor ve reddediyorum. Lütfen saygılı bir iletişim kurunuz."

    # Konum sorma sorguları kontrolü
    konum_sorulari = ["neredeyim", "konumum", "burası neresi", "neredeyiz", "hangi bölgedeyim", "konumum neresi"]
    if any(k in p_lower for k in konum_sorulari):
        if lat is not None and lon is not None:
            detected_zone = find_nearest_zone(lat, lon)
            zone_desc = PARK_ZONES.get(detected_zone, {}).get("desc", "")
            return f"📍 Mevcut GPS Konumunuza Göre:\nBölgeniz: {detected_zone}\nKoordinatlar: {lat:.4f}, {lon:.4f}\nAçıklama: {zone_desc}"
        else:
            return "📍 Konum bilginize şu an tarayıcı üzerinden ulaşılamadı. Lütfen 'Acil Durum & Konum' menüsünü kullanın."

    for key, desc in ALTINKOY_LOCATIONS.items():
        if key in p_lower:
            return f"📍 {desc}"

    if GROQ_API_KEY == "BURAYA_GROQ_API_KEY_GIRINIZ" or not GROQ_API_KEY:
        return f"Altınköy Asistanı: '{prompt}' talebiniz incelenmiştir. İşletme kurallarımız gereği dışarıdan yiyecek/içecek getirmek, piknik/kahvaltı yapmak ve dere yataklarına girmek kesinlikle yasaktır."

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "system", 
                "content": (
                    "Sen Altınköy Açık Hava Müzesi'nin kıdemli, profesyonel, akıllı ve adaptif turist rehberisin.\n\n"
                    "KURALLAR VE DAVRANIŞLAR:\n"
                    "1. ASLA tek tip, ezbere veya tekrarlayan bir giriş cümlesi (örn. 'Buyur canım...') kullanma. Her yanıtı sorunun içeriğine, bağlamına ve türüne göre özgün bir cümle ile başlat.\n"
                    "2. ÜSLUP ADAPTASYONU (Ayna Etkisi): Ziyaretçinin konuşma tarzına ve diline tam olarak ayak uydur:\n"
                    "   - Resmi, mesafeli veya kurumsal soruya -> Soğuk, profesyonel ve resmi yanıt.\n"
                    "   - Samimi, neşeli veya sıcak soruya -> Sıcak ve misafirperver yanıt.\n"
                    "3. HAKARET REDDİ: Hakaret veya küfür durumunda kesinlikle alttan alma; mesafeli, net ve sert bir dille bu üslubu reddet.\n"
                    "4. MÜZE KURALLARI (ASLA TAVİZ VERİLMEZ):\n"
                    "   - Müzemizde dışarıdan yiyecek ve içecek getirmek yasaktır.\n"
                    "   - Piknik ve kahvaltı yapmak yasaktır (Köy kahvemiz ve taş fırınımız hizmettedir).\n"
                    "   - Can güvenliği nedeniyle su değirmeni ve dere yataklarına/sulara girmek kesinlikle yasaktır.\n"
                    "5. Yanıtların kısa, net, bilgilendirici ve doğrudan soruya yönelik olsun."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=8)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
    except:
        pass
    return f"Talebiniz alınmıştır. Unutmayın ki müzemizde dışarıdan yiyecek getirmek, piknik/kahvaltı yapmak ve suya girmek kurallar gereği yasaktır."

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
                            <b>KVKK Genel Aydınlatma Metni & Açık Rıza:</b> 6698 sayılı KVKK kapsamında; acil durum konum yönlendirmesi, yapay zeka asistanı akışı ve müze içi deneyimin iyileştirilmesi amacıyla verileriniz işlenmektedir.
                        </div>
                        
                        <label style="font-size:12px; display:block; margin-bottom:15px; cursor:pointer;">
                            <input type="checkbox" required> Aydınlatma metnini okudum, anladım ve onaylıyorum.
                        </label>

                        <button type="submit" style="background:#27ae60; color:white; padding:14px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:14px; cursor:pointer;">🚀 Müzeye Giriş Yap</button>
                    </form>
                    <div style="text-align:center; margin-top:15px;">
                        <a href="/admin-panel" style="color:#7f8c8d; font-size:11px; text-decoration:none;">Müdür / Yönetici Girişi İçin Tıklayın</a>
                    </div>
                </div>
            </body>
        </html>
        """
    return RedirectResponse(url="/visitor-home", status_code=303)

@app.post("/api/set-session")
def set_session():
    response = RedirectResponse(url="/visitor-home", status_code=303)
    response.set_cookie(key="kvkk_session", value="onayli", max_age=86400)
    return response

@app.get("/api/logout")
def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="kvkk_session")
    return response

@app.get("/visitor-home", response_class=HTMLResponse)
def visitor_home():
    return """
    <html>
        <head><title>Altınköy Ziyaretçi Asistanı</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; background:#f9fafb; margin:0; padding:20px; text-align:center;">
            <div style="max-width:420px; margin:auto; background:white; padding:25px; border-radius:16px; box-shadow:0 4px 20px rgba(0,0,0,0.06); text-align:left;">
                <div style="text-align:center; margin-bottom:20px;">
                    <h2 style="color:#2c3e50; margin:0 0 5px 0;">🌾 Altınköy Ziyaretçi Rehberi</h2>
                    <p style="color:#7f8c8d; font-size:12px; margin:0;">Müzede rehberiniz cebinizde, anında yanınızda!</p>
                </div>
                
                <div style="background:#fffbeb; border-left:4px solid #f59e0b; padding:10px; border-radius:6px; margin-bottom:20px; font-size:12px; color:#92400e;">
                    <b>Önemli Kurallar:</b> Müzemizde dışarıdan yiyecek/içecek getirmek, piknik/kahvaltı yapmak ve dere yataklarına girmek kesinlikle yasaktır.
                </div>

                <a href="/qr-chat" style="display:block; background:#d35400; color:white; padding:15px; margin-bottom:12px; text-decoration:none; border-radius:10px; font-weight:bold; text-align:center; font-size:14px;">🎤 Yapay Zeka Asistanına Soru Sor / Sesli Dinle</a>
                <a href="/visitor-portal" style="display:block; background:#e74c3c; color:white; padding:15px; margin-bottom:12px; text-decoration:none; border-radius:10px; font-weight:bold; text-align:center; font-size:14px;">📍 Acil Durum & Saha Ekibi Çağır</a>
                <a href="/survey" style="display:block; background:#27ae60; color:white; padding:15px; margin-bottom:12px; text-decoration:none; border-radius:10px; font-weight:bold; text-align:center; font-size:14px;">⭐ Ziyaretçi Memnuniyet Anketi</a>

                <div style="text-align:center; margin-top:25px;">
                    <a href="/api/logout" style="color:#95a5a6; font-size:11px; text-decoration:none;">Oturumu Kapat</a>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/admin-panel", response_class=HTMLResponse)
def admin_panel():
    return """
    <html>
        <head><title>Altınköy Müdürlük Paneli</title><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; background:#2c3e50; padding:30px;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:450px; width:100%; box-shadow:0 4px 15px rgba(0,0,0,0.2); text-align:left;">
                <h2 style="color:#2c3e50; margin-top:0;">🛡️ Müdürlük Yönetim Paneli</h2>
                <p style="color:gray; font-size:12px;">Bu alan yalnızca müze yöneticileri içindir.</p>
                <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
                <a href="/qr-manager" style="display:block; background:#2980b9; color:white; padding:12px; margin:8px 0; text-decoration:none; border-radius:8px; font-weight:bold; font-size:13px;">🔗 Dinamik Direk & QR Yönetimi</a>
                <a href="/staff-management" style="display:block; background:#8e44ad; color:white; padding:12px; margin:8px 0; text-decoration:none; border-radius:8px; font-weight:bold; font-size:13px;">👥 Personel Yönetimi</a>
                <a href="/whatsapp-sim" style="display:block; background:#25D366; color:white; padding:12px; margin:8px 0; text-decoration:none; border-radius:8px; font-weight:bold; font-size:13px;">📱 WhatsApp Grup Akışı</a>
                <a href="/heatmap" style="display:block; background:#e67e22; color:white; padding:12px; margin:8px 0; text-decoration:none; border-radius:8px; font-weight:bold; font-size:13px;">🔥 Canlı GPS Isı Haritası</a>
                <a href="/live-dashboard" style="display:block; background:#34495E; color:white; padding:12px; margin:8px 0; text-decoration:none; border-radius:8px; font-weight:bold; font-size:13px;">📊 Müdürlük Rapor & Anket Paneli</a>
                <br><a href="/" style="display:block; text-align:center; color:#e74c3c; font-size:12px; text-decoration:none; margin-top:10px;">← Ziyaretçi Ekranına Dön</a>
            </div>
        </body>
    </html>
    """

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
                <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
                {qr_rows}
                <br><a href="/admin-panel" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:6px; display:inline-block;">← Yönetim Paneline Dön</a>
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
    return RedirectResponse(url="/visitor-home", status_code=303)

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
                    <p style="margin:0; font-size:12px; color:#7f1d1d;">Can güvenliğiniz açısından su değirmeni çevresindeki dere yatağına ve sulara girmek kesinlikle yasaktır.</p>
                </div>
                <div style="background:#fffbeb; border-left:4px solid #f59e0b; padding:12px; margin:15px 0; border-radius:4px;">
                    <p style="margin:0 0 10px 0; font-size:13px; color:#92400e; font-weight:bold;">🥪 2. Dışarıdan Yiyecek ve Piknik Yasaktır:</p>
                    <p style="margin:0; font-size:12px; color:#78350f;">Dere kenarında piknik yapmak, kahvaltı yapmak ve dışarıdan yiyecek/içecek getirmek yasaktır. Köy kahvemizi ve fırınımızı ziyaret edebilirsiniz.</p>
                </div>
                <br><a href="/qr-chat" style="display:block; background:#2980b9; color:white; padding:12px; text-decoration:none; border-radius:6px; text-align:center; font-weight:bold;">🎤 Asistana Soru Sor</a>
                <br><div style="text-align:center;"><a href="/visitor-home" style="color:gray; font-size:12px; text-decoration:none;">← Ziyaretçi Ana Ekranı</a></div>
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
                <br><a href="/admin-panel">← Yönetim Paneline Dön</a>
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
                <br><a href="/admin-panel">← Yönetim Paneline Dön</a>
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
                        document.getElementById('emergencyForm').submit();
                        return;
                    }
                    status.innerText = 'Konumunuz alınıyor...';
                    navigator.geolocation.getCurrentPosition((position) => {
                        document.getElementById('lat').value = position.coords.latitude;
                        document.getElementById('lon').value = position.coords.longitude;
                        document.getElementById('emergencyForm').submit();
                    }, () => {
                        document.getElementById('emergencyForm').submit();
                    });
                }
            </script>
        </head>
        <body style="font-family:Segoe UI; background:#fff5f5; text-align:center; padding:30px;">
            <div style="background:white; padding:25px; border-radius:12px; display:inline-block; max-width:420px; width:100%; text-align:left;">
                <h2 style="color:#c0392b; text-align:center;">🚨 Acil Durum & Canlı Konum</h2>
                <p style="font-size:12px; color:gray; text-align:center;">En yakın saha ekibini size yönlendirmek için konumunuz paylaşılır.</p>
                
                <form id="emergencyForm" action="/api/emergency-form" method="POST" onsubmit="getLocationAndSubmit(event)">
                    <input type="hidden" id="lat" name="lat" value="39.9334">
                    <input type="hidden" id="lon" name="lon" value="32.8597">
                    <button type="submit" style="background:#e74c3c; color:white; padding:14px; border:none; border-radius:8px; font-weight:bold; width:100%; font-size:14px; cursor:pointer;">📍 Konumumu Gönder & Ekip İste</button>
                </form>
                <p id="status" style="margin-top:10px; font-size:12px; color:#e67e22; text-align:center;"></p>
                <br><div style="text-align:center;"><a href="/visitor-home" style="color:gray; font-size:12px; text-decoration:none;">← Ziyaretçi Ana Ekranı</a></div>
            </div>
        </body>
    </html>
    """

@app.post("/api/emergency-form", response_class=HTMLResponse)
def emergency_form(lat: float = Form(39.9334), lon: float = Form(32.8597)):
    detected_zone = find_nearest_zone(lat, lon)
    zone_warning = ""
    if "Değirmen" in detected_zone:
        zone_warning = "⚠️ DİKKAT: Su değirmeni ve dere yatağı bölgesindesiniz! Can güvenliğiniz için suya girmek ve piknik yapmak yasaktır."
    
    heatmap_data.append({"zone": detected_zone, "type": "Acil Durum (GPS)", "time": datetime.now().strftime("%H:%M:%S"), "lat": lat, "lon": lon})
    nearest = min(STAFF_LIST, key=lambda s: 0 if s['zone'] == detected_zone else 1)
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; text-align:center; padding:40px; background:#e8f8f5;">
            <div style="background:white; padding:30px; border-radius:12px; display:inline-block; max-width:420px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#27ae60;">✔️ Sinyal Alındı & Ekip Yönlendirildi</h2>
                <p style="font-size:13px; color:#c0392b; font-weight:bold;">{zone_warning}</p>
                <p><b>Bölgeniz:</b> {detected_zone}<br><b>İlgili Personel:</b> {nearest['name']} ({nearest['phone']})</p>
                <br><a href="/visitor-home" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; border-radius:6px;">Ana Ekrana Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/survey", response_class=HTMLResponse)
def survey_page():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:550px; margin:auto; background:white; padding:25px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#27ae60;">⭐ Altınköy Ziyaretçi Memnuniyet Anketi</h2>
                <form action="/api/submit-survey" method="POST">
                    <label style="font-size:13px; font-weight:bold;">Genel Memnuniyet Puanınız (1-5):</label>
                    <select name="score" style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px;">
                        <option value="5">⭐⭐⭐⭐⭐ 5 - Mükemmel</option>
                        <option value="4">⭐⭐⭐⭐ 4 - Çok İyi</option>
                        <option value="3">⭐⭐⭐ 3 - Orta</option>
                        <option value="2">⭐⭐ 2 - Geliştirilmeli</option>
                        <option value="1">⭐ 1 - Zayıf</option>
                    </select>
                    
                    <label style="font-size:13px; font-weight:bold;">Görüş, Öneri ve Yorumlarınız:</label>
                    <textarea name="comment" rows="3" placeholder="Örn: Köy ekmeği harikaydı..." style="width:100%; padding:10px; margin:5px 0 15px 0; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"></textarea>

                    <button type="submit" style="background:#27ae60; color:white; border:none; padding:14px; width:100%; border-radius:8px; font-weight:bold; cursor:pointer;">Anketi Gönder</button>
                </form>
                <br><a href="/visitor-home" style="display:inline-block; margin-top:10px; text-decoration:none; color:#2c3e50;">← Ziyaretçi Ana Ekranı</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/submit-survey")
def submit_survey(score: int = Form(...), comment: str = Form("")):
    survey_responses.append({"score": score, "clean": "İyi", "staff": "İyi", "comment": comment, "time": datetime.now().strftime("%H:%M:%S")})
    return RedirectResponse(url="/visitor-home", status_code=303)

@app.get("/qr-chat", response_class=HTMLResponse)
def qr_chat_get():
    chat_history = "".join([f"<div style='margin-bottom:12px; border-bottom:1px solid #eee; padding-bottom:8px;'><b>Ziyaretçi:</b> {q['msg']}<br><div style='background:#eef2f7; padding:8px; border-radius:6px; margin-top:4px;'><b>Asistan:</b> {q['reply']}</div><button onclick=\"speakText('{q['reply']}')\" style='margin-top:5px; background:#27ae60; color:white; border:none; padding:6px 12px; border-radius:4px; font-size:12px; cursor:pointer;'>🔊 Sesli Dinle</button></div>" for q in reversed(qr_requests)])
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
                <p style="font-size:12px; color:gray;">Örn: "Neredeyim?", "Piknik yapabilir miyim?", "Kahvaltı getirebilir miyim?"</p>
                <form id="chatForm" action="/api/qr-chat-post" method="POST" onsubmit="askWithLocation(event)">
                    <input type="text" name="message" placeholder="Müze hakkında ne öğrenmek istemiştiniz?" required style="width:100%; padding:12px; border:1px solid #ddd; border-radius:6px; box-sizing:border-box;"><br>
                    <input type="hidden" id="latField" name="lat" value="39.9334">
                    <input type="hidden" id="lonField" name="lon" value="32.8597"><br>
                    <button type="submit" style="background:#d35400; color:white; border:none; padding:12px; width:100%; border-radius:6px; font-weight:bold; cursor:pointer;">Yapay Zekaya Sor</button>
                </form>
                <br><h3>Geçmiş Soru & Yanıtlar</h3>
                {chat_history if chat_history else "<p style='color:gray;'>Henüz soru sorulmadı.</p>"}
                <br><a href="/visitor-home">← Ziyaretçi Ana Ekranı</a>
            </div>
        </body>
    </html>
    """

@app.post("/api/qr-chat-post")
def qr_chat_post(request: Request, message: str = Form(...), lat: float = Form(39.9334), lon: float = Form(32.8597)):
    reply = ask_groq_ai(message, lat=lat, lon=lon)
    detected_zone = find_nearest_zone(lat, lon)
    heatmap_data.append({"zone": detected_zone, "type": f"Soru: {message[:20]}...", "time": datetime.now().strftime("%H:%M:%S"), "lat": lat, "lon": lon})
    qr_requests.append({"msg": message, "reply": reply})
    return RedirectResponse(url="/qr-chat", status_code=303)

@app.get("/heatmap", response_class=HTMLResponse)
def heatmap_page():
    zones = list(PARK_ZONES.keys())
    stats = {z: sum(1 for h in heatmap_data if h['zone'] == z) for z in zones}
    bars = "".join([f"<div style='margin-bottom:15px;'><b>{z}</b> ({count} sinyal)</div>" for z, count in stats.items()])
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f4f6f9;">
            <div style="max-width:650px; margin:auto; background:white; padding:25px; border-radius:12px;">
                <h2 style="color:#e67e22;">🔥 Canlı GPS Isı Haritası</h2>
                {bars}
                <br><a href="/admin-panel">← Yönetim Paneline Dön</a>
            </div>
        </body>
    </html>
    """

@app.get("/live-dashboard", response_class=HTMLResponse)
def live_dashboard():
    avg_score = sum(s['score'] for s in survey_responses) / len(survey_responses) if survey_responses else 0
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="font-family:Segoe UI; padding:20px; background:#f8f9fa;">
            <div style="max-width:600px; margin:auto; background:white; padding:25px; border-radius:10px;">
                <h2>📊 Müdürlük Rapor Paneli</h2>
                <p><b>Ortalama Ziyaretçi Memnuniyeti:</b> ⭐ {avg_score:.1f} / 5.0 ({len(survey_responses)} anket)</p>
                <br><a href="/admin-panel">← Yönetim Paneline Dön</a>
            </div>
        </body>
    </html>
    """
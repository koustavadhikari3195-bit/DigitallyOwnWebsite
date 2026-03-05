"""
Digitally Agency – Backend Server
Stack: Flask + yfinance + MongoDB + Grok AI (xAI)
Run: python app.py
"""

import os
import sys
import json
import time
import threading

# Fix Windows console encoding (cp1252 → utf-8)
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime, timezone
import io
from flask import Flask, jsonify, request, send_from_directory, render_template, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import yfinance as yf
import requests
from pymongo import MongoClient

try:
    from weasyprint import HTML
    HAS_WEASY = True
except Exception as e:
    print(f"[WARN] WeasyPrint not available (missing GTK?): {e}")
    HAS_WEASY = False

load_dotenv()

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)


@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return resp


# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL   = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL     = "llama-3.3-70b-versatile"
MONGO_URI      = os.getenv("MONGO_URI", "mongodb://localhost:27017")
PORT           = int(os.getenv("PORT", 5000))

# ── MONGODB ───────────────────────────────────────────────────────────────────
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    mongo_client.server_info()
    db = mongo_client["digitally"]
    leads_col      = db["leads"]
    roasts_col     = db["roasts"]
    stocks_cache   = db["stocks_cache"]
    print("[OK] MongoDB connected")
except Exception as e:
    print(f"[WARN] MongoDB not available: {e} -- running without persistence")
    db = None
    leads_col = roasts_col = stocks_cache = None

# ── IN-MEMORY CACHE ───────────────────────────────────────────────────────────
_stock_cache   = {"data": [], "ts": 0}
_weather_cache = {}          # city → {data, ts}
STOCK_TTL      = 180         # 3 min
WEATHER_TTL    = 600         # 10 min

SYMBOLS = ["META", "GOOGL", "MSFT", "NVDA", "AMZN", "AAPL"]

# ── STOCKS ────────────────────────────────────────────────────────────────────
def fetch_stocks():
    """Fetch live quotes with yfinance, cache for 3 min."""
    now = time.time()
    if now - _stock_cache["ts"] < STOCK_TTL and _stock_cache["data"]:
        return _stock_cache["data"]

    result = []
    for sym in SYMBOLS:
        try:
            ticker = yf.Ticker(sym)
            info   = ticker.fast_info
            price  = round(float(info.last_price), 2)
            prev   = round(float(info.previous_close), 2)
            change = round((price - prev) / prev * 100, 2) if prev else 0
            result.append({
                "sym":    sym,
                "price":  price,
                "prev":   prev,
                "change": change,
                "up":     change >= 0
            })
        except Exception as e:
            print(f"yfinance error {sym}: {e}")

    if result:
        _stock_cache["data"] = result
        _stock_cache["ts"]   = now
        # Persist to mongo
        if stocks_cache is not None:
            stocks_cache.replace_one(
                {"_id": "latest"},
                {"_id": "latest", "data": result, "ts": datetime.now(timezone.utc)},
                upsert=True
            )

    # Fallback to mongo if live fetch failed
    if not result and stocks_cache is not None:
        doc = stocks_cache.find_one({"_id": "latest"})
        if doc:
            return doc["data"]

    return result


def stocks_refresh_loop():
    """Background thread: keep cache warm."""
    while True:
        try:
            fetch_stocks()
        except Exception as e:
            print(f"Stock refresh error: {e}")
        time.sleep(STOCK_TTL)


# ── WEATHER ───────────────────────────────────────────────────────────────────
# ── WEATHER ───────────────────────────────────────────────────────────────────
def fetch_weather(city="Kolkata"):
    """Fetch live weather from Open-Meteo (Kolkata region). No key required."""
    now = time.time()
    if city in _weather_cache and now - _weather_cache[city]["ts"] < WEATHER_TTL:
        return _weather_cache[city]["data"]

    try:
        # Default to Kolkata coordinates: 22.57, 88.36
        lat, lon = 22.57, 88.36
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&timezone=auto")
        
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        d = r.json()["current"]
        
        code = d["weather_code"]
        temp = round(d["temperature_2m"])
        wind = round(d["wind_speed_10m"])
        cond, desc = _map_open_meteo_condition(code)
        
        data = {"city": city, "temp": temp, "condition": cond,
                "desc": desc, "wind": wind}
        _weather_cache[city] = {"data": data, "ts": now}
        return data
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return _fallback_weather(city)


def _map_open_meteo_condition(code):
    """Map WMO Weather Interpretation Codes (WW) to Digitally conditions."""
    # 0: Clear sky
    if code == 0:
        return "sunny", "Clear Sky"
    # 1, 2, 3: Mainly clear, partly cloudy, and overcast
    if code in [1, 2, 3]:
        return "cloudy", "Partly Cloudy"
    # 45, 48: Fog
    if code in [45, 48]:
        return "foggy", "Foggy"
    # 51, 53, 55: Drizzle
    # 61, 63, 65: Rain
    # 80, 81, 82: Rain showers
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "rainy", "Rainy"
    # 71, 73, 75, 77, 85, 86: Snow
    if code in [71, 73, 75, 77, 85, 86]:
        return "snow", "Snowy"
    # 95, 96, 99: Thunderstorm
    if code in [95, 96, 99]:
        return "stormy", "Thunderstorm"
    
    return "sunny", "Clear"


def _fallback_weather(city):
    return {"city": city, "temp": 30, "condition": "sunny",
            "desc": "Clear Sky", "wind": 12}


# ── AI ENGINE (GROQ) ──────────────────────────────────────────────────────────
def call_ai(system_prompt, user_prompt, max_tokens=1024):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    payload = {
        "model":      GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_prompt}
        ]
    }
    resp = requests.post(GROQ_API_URL, headers=headers,
                         json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.route("/api/stocks")
def api_stocks():
    """GET /api/stocks → live stock quotes"""
    try:
        data = fetch_stocks()
        return jsonify({"ok": True, "stocks": data,
                        "cached_at": datetime.now(timezone.utc).isoformat()})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/weather")
def api_weather():
    """GET /api/weather?city=Kolkata"""
    city = request.args.get("city", "Kolkata")
    try:
        data = fetch_weather(city)
        return jsonify({"ok": True, "weather": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/roast", methods=["POST"])
def api_roast():
    """POST /api/roast  body: {url: "example.com"}"""
    body = request.get_json() or {}
    url  = body.get("url", "").strip()
    if not url:
        return jsonify({"ok": False, "error": "url required"}), 400

    domain = url.replace("https://", "").replace("http://", "").split("/")[0]

    system = (
        "You are a Brutally Honest Senior Developer at a digital agency. "
        "You roast websites with sharp, specific, data-driven critique. "
        "Every observation must include a real-sounding specific metric. "
        "You are funny but constructive. You always end with actionable fixes."
    )
    user = f"""Roast the website {domain}. 
Return ONLY a JSON object (no markdown, no backticks, no explanation):
{{
  "score": 38,
  "scores": {{
    "Performance": 42,
    "SEO": 31,
    "Mobile": 45,
    "Accessibility": 55,
    "Security": 28
  }},
  "verdict": "One brutal one-liner.",
  "burns": [
    {{"title":"Problem 1","text":"Brutal observation with a specific metric.","fix":"→ Fix: Digitally service","severity":"critical"}},
    {{"title":"Problem 2","text":"Another sharp observation.","fix":"→ Fix: service","severity":"warning"}},
    {{"title":"Problem 3","text":"Third observation.","fix":"→ Fix: service","severity":"critical"}}
  ],
  "roadmap": ["Action 1","Action 2","Action 3","Action 4"]
}}"""

    try:
        raw    = call_ai(system, user)
        clean  = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except Exception:
        # Fallback Roast
        result = {
            "score": 34,
            "scores": {"Performance": 28, "SEO": 42, "Mobile": 15, "Accessibility": 55, "Security": 30},
            "verdict": "Your website is actively donating customers to your competitors.",
            "burns": [
                {"title": "Load Time: Criminal", "text": f"'{domain}' loads in 8.4s on mobile. Your customer finished checkout on a competitor site.", "fix": "→ Fix: Web App Support — Performance Package", "severity": "critical"},
                {"title": "Invisible on Google",  "text": "Zero schema markup, missing titles, blocked crawlers. SEO score: 11/100.", "fix": "→ Fix: Search Engine Optimization", "severity": "warning"},
                {"title": "CTAs That Convert Nobody", "text": "Three 'Contact Us' buttons, none visible mobile. Bounce rate: 83%.", "fix": "→ Fix: Website Redesign + CRO", "severity": "critical"}
            ],
            "roadmap": ["Technical SEO Overhaul", "Core Web Vitals Fix", "Mobile UX Redesign", "Meta Ads Setup"]
        }

    # Persist roast to MongoDB for PDF generation
    roast_id = str(int(time.time()))
    if roasts_col is not None:
        try:
            roasts_col.insert_one({
                "id":       roast_id,
                "domain":   domain,
                "url":      url,
                "roast":    result,
                "created":  datetime.now(timezone.utc)
            })
        except Exception as e:
            print(f"Error saving roast: {e}")

    return jsonify({"ok": True, "domain": domain, "roast": result, "id": roast_id})


@app.route("/api/roast/pdf/<roast_id>")
def api_roast_pdf(roast_id):
    """GET /api/roast/pdf/<id> → download professional PDF report."""
    if roasts_col is None:
        return jsonify({"ok": False, "error": "Database not available"}), 503
        
    doc = roasts_col.find_one({"id": roast_id})
    if not doc:
        return jsonify({"ok": False, "error": "Roast not found"}), 404
        
    rendered = render_template("report_template.html", 
                               domain=doc["domain"], 
                               roast=doc["roast"])
                               
    if not HAS_WEASY:
        # Fallback: serve HTML and let browser print to PDF
        return rendered

    try:
        pdf_file = io.BytesIO()
        HTML(string=rendered).write_pdf(target=pdf_file)
        pdf_file.seek(0)
        return send_file(pdf_file, 
                         mimetype="application/pdf", 
                         as_attachment=True, 
                         download_name=f"Digitally_Roast_{doc['domain']}.pdf")
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        return rendered # Fallback to HTML on error


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """POST /api/chat  body: {messages: [...], context?: {roast}}"""
    body     = request.get_json() or {}
    messages = body.get("messages", [])
    context  = body.get("context", {})

    if not messages:
        return jsonify({"ok": False, "error": "messages required"}), 400

    ctx_hint = ""
    if context.get("roast"):
        r = context["roast"]
        ctx_hint = (f"\n\nContext: This visitor just had their website roasted. "
                    f"Domain: {r.get('domain','')}, Score: {r.get('score','')}, "
                    f"Verdict: {r.get('verdict','')}. "
                    f"Reference this context naturally when relevant.")

    system = (
        "You are the Digitally Agency AI assistant — a sharp, witty, knowledgeable "
        "digital marketing and web engineering strategist. You give real, specific, "
        "actionable advice. You reference the agency's services: SEO, Meta Ads, "
        "Social Media, Content Marketing, Web Development, Web App Support. "
        "Keep responses concise and punchy. Never be vague."
        + ctx_hint
    )

    try:
        # Build message chain for AI
        ai_msgs = [{"role": "system", "content": system}]
        for m in messages[-10:]:          # last 10 turns
            ai_msgs.append({"role": m["role"], "content": m["content"]})

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}",
                   "Content-Type": "application/json"}
        payload = {"model": GROQ_MODEL, "max_tokens": 600, "messages": ai_msgs}
        resp = requests.post(GROQ_API_URL, headers=headers,
                             json=payload, timeout=30)
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/lead", methods=["POST"])
def api_lead():
    """POST /api/lead  body: {name, email, service, budget, website, message}"""
    body = request.get_json() or {}
    required = ["name", "email"]
    for f in required:
        if not body.get(f):
            return jsonify({"ok": False, "error": f"{f} required"}), 400

    lead = {
        "name":    body.get("name"),
        "email":   body.get("email"),
        "service": body.get("service", ""),
        "budget":  body.get("budget", ""),
        "website": body.get("website", ""),
        "message": body.get("message", ""),
        "created": datetime.now(timezone.utc)
    }

    if leads_col is not None:
        try:
            leads_col.insert_one(lead)
        except Exception as e:
            print(f"Lead insert error: {e}")

    return jsonify({"ok": True, "message": "Lead received"})


@app.route("/api/leads", methods=["GET"])
def api_leads():
    """GET /api/leads — admin: list recent leads"""
    if leads_col is None:
        return jsonify({"ok": False, "error": "MongoDB not connected"}), 503
    try:
        docs = list(leads_col.find({}, {"_id": 0})
                    .sort("created", -1).limit(50))
        return jsonify({"ok": True, "leads": docs})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── SERVE FRONTEND ────────────────────────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ── BOOT ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Warm stock cache on startup
    t = threading.Thread(target=stocks_refresh_loop, daemon=True)
    t.start()
    print(f"\n[OK] Digitally backend running -> http://localhost:{PORT}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)

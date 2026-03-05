from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress
import os
import json
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
Compress(app)


# ── SECURITY HEADERS ─────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["X-XSS-Protection"] = "1; mode=block"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self' https://api.open-meteo.com https://api.groq.com https://nominatim.openstreetmap.org"
    )
    resp.headers["Content-Security-Policy"] = csp
    return resp


# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ── WEATHER ───────────────────────────────────────────────────────────────────
_weather_cache = {}
WEATHER_TTL = 600


def _map_weather_condition(code):
    """Map WMO Weather Interpretation Codes to Digitally conditions."""
    if code == 0:
        return "sunny", "Clear Sky"
    if code in [1, 2, 3]:
        return "cloudy", "Partly Cloudy"
    if code in [45, 48]:
        return "foggy", "Foggy"
    if code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "rainy", "Rainy"
    if code in [71, 73, 75, 77, 85, 86]:
        return "snow", "Snowy"
    if code in [95, 96, 99]:
        return "stormy", "Thunderstorm"
    return "sunny", "Clear"


def fetch_weather(city="GLOBAL", lat=None, lon=None):
    now = time.time()
    cache_key = f"{lat}_{lon}" if lat and lon else city
    if cache_key in _weather_cache and now - _weather_cache[cache_key]["ts"] < WEATHER_TTL:
        return _weather_cache[cache_key]["data"]

    try:
        # Default fallbacks (London)
        used_lat = lat if lat else 51.5074
        used_lon = lon if lon else -0.1278
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={used_lat}&longitude={used_lon}&current=temperature_2m,weather_code,wind_speed_10m&timezone=auto")

        r = requests.get(url, timeout=5)
        r.raise_for_status()
        d = r.json()["current"]
        temp = round(d["temperature_2m"])
        code = d["weather_code"]
        wind = round(d["wind_speed_10m"])
        cond, desc = _map_weather_condition(code)

        data = {"city": city, "temp": temp, "condition": cond, "desc": desc, "wind": wind}
        _weather_cache[cache_key] = {"data": data, "ts": now}
        return data
    except Exception as e:
        print(f"Weather error: {e}")
        return {"city": city, "temp": "--", "condition": "cloudy", "desc": "Data Offline", "wind": "--"}

# ── AI ENGINE (GROQ) ──────────────────────────────────────────────────────────
def call_ai(system_prompt, user_prompt, max_tokens=1024):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }
    resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.route("/api/health")
def api_health():
    return jsonify({
        "ok": True,
        "service": "Digitally API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "groq_configured": bool(GROQ_API_KEY)
    })


@app.route("/api/weather")
def api_weather():
    # Vercel Native Edge Geolocation Headers
    v_city = request.headers.get("x-vercel-ip-city")
    v_lat  = request.headers.get("x-vercel-ip-latitude")
    v_lon  = request.headers.get("x-vercel-ip-longitude")

    # Query params override Vercel headers
    city = request.args.get("city")
    if not city or city == "GLOBAL":
        city = v_city or "GLOBAL"

    lat = request.args.get("lat") or v_lat
    lon = request.args.get("lon") or v_lon

    data = fetch_weather(city, lat, lon)
    return jsonify({"ok": True, "weather": data})


@app.route("/api/roast", methods=["POST"])
def api_roast():
    """POST /api/roast  body: {url: "example.com"} — AI-powered website audit"""
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
Return ONLY a JSON object (no markdown, no backticks, no explanation).
The scores must be unique and specifically calculated based on your simulated audit of {domain}. 
DO NOT repeat the example values below.

{{
  "score": [OVERALL_SCORE_0_100],
  "scores": {{
    "Performance": [0_100],
    "SEO": [0_100],
    "Mobile": [0_100],
    "Accessibility": [0_100],
    "Security": [0_100]
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
        # Fallback Roast when AI fails or JSON can't be parsed
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

    roast_id = str(int(time.time()))
    return jsonify({"ok": True, "domain": domain, "roast": result, "id": roast_id})


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
        ai_msgs = [{"role": "system", "content": system}]
        for m in messages[-10:]:
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

    # Log lead (no database in serverless mode)
    print(f"[LEAD] {body.get('name')} <{body.get('email')}> — {body.get('service', 'N/A')}")
    return jsonify({"ok": True, "message": "Lead received"})


# Vercel requires the app object to be named 'app'
if __name__ == "__main__":
    app.run(debug=True)

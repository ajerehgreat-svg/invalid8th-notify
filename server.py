import os
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]          # your Telegram bot token
OWNER_CHAT_ID = os.environ["OWNER_CHAT_ID"]  # your Telegram user ID

@app.post("/telegram-notify")
def telegram_notify():
    data = request.get_json(force=True)

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
        f"Phone: {phone}"
    )

    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        params={"chat_id": OWNER_CHAT_ID, "text": text}
    )

    return jsonify({"ok": True})

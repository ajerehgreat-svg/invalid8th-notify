import os
from datetime import datetime, date, time, timedelta

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import requests

# ----------------- HARD-CODED CONFIG -----------------

# 1) PASTE YOUR POSTGRES URL HERE (change postgres:// to postgresql://)
DB_URL = "postgresql://invalid8th_codes_db_user:YnfOg2XPvvNjggzcFdiizVekZusg9097@dpg-d4b0lkvpm1nc739hdng0-a/invalid8th_codes_db"

# 2) PASTE YOUR TELEGRAM BOT TOKEN HERE
TELEGRAM_TOKEN = "8503472232:AAHJTB9TbGi-Eak3Qcf5c4wILCK3bNgb-kw"

# 3) PASTE YOUR ADMIN CHAT ID HERE (just the number, no quotes)
ADMIN_CHAT_ID = 1404329479


# 4) MASTER CODE FOR FIRST ACCESS
MASTER_CODE = "NHBH"

# -----------------------------------------------------

app = Flask(__name__)
app.secret_key = "invalid8th-secret-key-123"  # can be anything

app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})


# ----------------- DATABASE MODELS -----------------

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    instagram = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    personal_code = db.Column(db.String(40), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)

    type = db.Column(db.String(20), nullable=False)  # lifestyle / matchday
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    location = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)

    base_price = db.Column(db.Integer, nullable=False)
    overlap = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default="pending")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    member = db.relationship("Member", backref="bookings")


with app.app_context():
    db.create_all()


# ----------------- HELPERS -----------------

def generate_personal_code(name: str) -> str:
    clean = "".join([c for c in (name or "").lower() if c.isalpha()]) or "client"
    while True:
        num = os.urandom(1)[0] % 90 + 10  # 10–99
        code = f"{clean}{num}"
        if not Member.query.filter_by(personal_code=code).first():
            return code


def notify_telegram_booking(booking: Booking, member: Member):
    if not TELEGRAM_TOKEN or not ADMIN_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    overlap_text = "YES" if booking.overlap else "No"

    text = (
        "📸 *NEW INVALID8TH BOOKING (PORTAL)*\n\n"
        f"Client: {member.first_name}\n"
        f"IG: @{member.instagram}\n"
        f"Code: `{member.personal_code}`\n\n"
        f"Type: {booking.type.title()}\n"
        f"Date: {booking.date.strftime('%d %b %Y')} "
        f"{booking.start_time.strftime('%H:%M')}\n"
        f"Location: {booking.location}\n\n"
        f"Base Price: £{booking.base_price}\n"
        f"Overlap / Clash: {overlap_text}\n"
        f"Status: {booking.status}"
    )

    try:
        requests.post(
            url,
            json={"chat_id": ADMIN_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=5,
        )
    except Exception:
        pass


# ----------------- API ROUTES -----------------

@app.post("/api/access")
def api_access():
    """
    Body: { "code": "NHBH" or personal code }
    """
    data = request.get_json(force=True) or {}
    code_raw = (data.get("code") or "").strip()
    code = code_raw.lower()

    if not code:
        return jsonify({"ok": False, "error": "No code"}), 400

    # Master code -> allow creating profile
    if code == MASTER_CODE.lower():
        return jsonify({"ok": True, "mode": "master"})

    # Personal code -> find member
    member = Member.query.filter(
        db.func.lower(Member.personal_code) == code
    ).first()

    if not member:
        return jsonify({"ok": False, "error": "Invalid code"}), 404

    return jsonify({
        "ok": True,
        "mode": "member",
        "member": {
            "first_name": member.first_name,
            "instagram": member.instagram,
            "email": member.email,
            "phone": member.phone,
            "personal_code": member.personal_code,
        },
    })


@app.post("/api/profile")
def api_profile():
    """
    Body: { first_name, instagram, email, phone, personal_code? }
    """
    data = request.get_json(force=True) or {}

    first_name = (data.get("first_name") or "").strip()
    instagram = (data.get("instagram") or "").strip().lstrip("@")
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    existing_code = (data.get("personal_code") or "").strip()

    if not first_name or not instagram:
        return jsonify({"ok": False, "error": "Missing fields"}), 400

    member = None
    if existing_code:
        member = Member.query.filter_by(personal_code=existing_code).first()

    if member is None:
        # Create new member
        personal_code = generate_personal_code(first_name)
        member = Member(
            first_name=first_name,
            instagram=instagram,
            email=email,
            phone=phone,
            personal_code=personal_code,
        )
        db.session.add(member)
    else:
        # Update existing
        member.first_name = first_name
        member.instagram = instagram
        member.email = email
        member.phone = phone

    db.session.commit()

    return jsonify({
        "ok": True,
        "member": {
            "first_name": member.first_name,
            "instagram": member.instagram,
            "email": member.email,
            "phone": member.phone,
            "personal_code": member.personal_code,
        },
    })


@app.post("/api/booking")
def api_booking():
    """
    Body: {
      personal_code, type, date, time, location, notes,
      hours (for lifestyle), players (for matchday)
    }
    """
    data = request.get_json(force=True) or {}

    code = (data.get("personal_code") or "").strip()
    member = Member.query.filter_by(personal_code=code).first()
    if not member:
        return jsonify({"ok": False, "error": "Invalid personal code"}), 400

    btype = data.get("type")
    date_str = data.get("date")
    time_str = data.get("time")
    location = (data.get("location") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not (btype and date_str and time_str and location):
        return jsonify({"ok": False, "error": "Missing booking fields"}), 400

    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"ok": False, "error": "Bad date"}), 400

    try:
        h, m = map(int, time_str.split(":"))
        start_t = time(h, m)
    except Exception:
        return jsonify({"ok": False, "error": "Bad time"}), 400

    # Pricing & duration
    if btype == "lifestyle":
        hours = int(data.get("hours") or 0)
        if hours <= 0:
            return jsonify({"ok": False, "error": "Invalid hours"}), 400
        if hours < 2:
            base_price = 150
        else:
            base_price = hours * 100
        duration_hours = max(hours, 2)
    elif btype == "matchday":
        players = int(data.get("players") or 0)
        if players <= 0:
            return jsonify({"ok": False, "error": "Invalid players"}), 400
        if players <= 3:
            base_price = 300
        else:
            base_price = players * 100
        duration_hours = 2.5
    else:
        return jsonify({"ok": False, "error": "Bad type"}), 400

    start_dt = datetime.combine(d, start_t)
    end_dt = start_dt + timedelta(hours=duration_hours)
    end_t = end_dt.time()

    # Overlap check for that date
    existing = Booking.query.filter_by(date=d).all()
    overlap = False
    for b in existing:
        b_start = datetime.combine(b.date, b.start_time)
        b_end = datetime.combine(b.date, b.end_time)
        if start_dt < b_end and end_dt > b_start:
            overlap = True
            break

    booking = Booking(
        member_id=member.id,
        type=btype,
        date=d,
        start_time=start_t,
        end_time=end_t,
        location=location,
        notes=notes,
        base_price=base_price,
        overlap=overlap,
        status="pending",
    )
    db.session.add(booking)
    db.session.commit()

    notify_telegram_booking(booking, member)

    return jsonify({
        "ok": True,
        "overlap": overlap,
        "base_price": base_price,
        "status": booking.status,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

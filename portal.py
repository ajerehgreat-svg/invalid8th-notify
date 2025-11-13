import os
import random
from datetime import datetime

from flask import Flask, request, redirect, url_for, render_template_string, session
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# ---------- BASIC APP & DB SETUP ---------- #

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///codes.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class AccessCode(Base):
    __tablename__ = "access_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=True)
    instagram = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def ensure_master_code():
    db = SessionLocal()
    try:
        master = db.query(AccessCode).filter_by(code="NHBH").first()
        if not master:
            db.add(AccessCode(code="NHBH", name="MASTER"))
            db.commit()
    finally:
        db.close()


ensure_master_code()

# ---------- HTML TEMPLATES (INLINE) ---------- #

ACCESS_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Invalid8th Access</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
           background:#050505; color:#f5f5f5; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; }
    .card { background:#111; padding:24px 28px; border-radius:16px; max-width:360px; width:100%;
            box-shadow:0 12px 40px rgba(0,0,0,0.5); }
    h1 { font-size:22px; margin-top:0; margin-bottom:12px; letter-spacing:0.08em; text-transform:uppercase; }
    p { font-size:14px; color:#bbb; }
    label { display:block; font-size:13px; margin-bottom:6px; color:#ddd; }
    input[type=text] { width:100%; padding:10px 12px; border-radius:8px; border:1px solid #333;
                       background:#000; color:#f5f5f5; font-size:14px; box-sizing:border-box; }
    input[type=text]:focus { outline:none; border-color:#888; }
    button { width:100%; margin-top:12px; padding:10px 12px; border-radius:999px; border:none;
             background:#f5f5f5; color:#000; font-weight:600; letter-spacing:0.12em; font-size:12px;
             text-transform:uppercase; cursor:pointer; }
    .error { color:#ff4d4f; font-size:12px; margin-bottom:8px; }
    .hint { font-size:11px; color:#777; margin-top:6px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Invalid8th Access</h1>
    <p>Enter your access code to continue.<br>New members use <strong>NHBH</strong> first.</p>
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post">
      <label>Access code</label>
      <input type="text" name="access_code" placeholder="e.g. NHBH or YOURNAME23">
      <button type="submit">Enter</button>
    </form>
    <p class="hint">Keep your personal code safe. It’s your gateway to the elite side.</p>
  </div>
</body>
</html>
"""

CREATE_CODE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Create Your Invalid8th Code</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
           background:#050505; color:#f5f5f5; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; }
    .card { background:#111; padding:24px 28px; border-radius:16px; max-width:380px; width:100%;
            box-shadow:0 12px 40px rgba(0,0,0,0.5); }
    h1 { font-size:20px; margin-top:0; margin-bottom:8px; letter-spacing:0.08em; text-transform:uppercase; }
    p { font-size:14px; color:#bbb; }
    label { display:block; font-size:13px; margin-bottom:6px; color:#ddd; }
    input[type=text] { width:100%; padding:10px 12px; border-radius:8px; border:1px solid #333;
                       background:#000; color:#f5f5f5; font-size:14px; box-sizing:border-box; margin-bottom:10px; }
    input[type=text]:focus { outline:none; border-color:#888; }
    button { width:100%; margin-top:4px; padding:10px 12px; border-radius:999px; border:none;
             background:#f5f5f5; color:#000; font-weight:600; letter-spacing:0.12em; font-size:12px;
             text-transform:uppercase; cursor:pointer; }
    .error { color:#ff4d4f; font-size:12px; margin-bottom:8px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>New Member</h1>
    <p>Tell us who you are so we can lock in your personal access code.</p>
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post">
      <label>Full name</label>
      <input type="text" name="name" placeholder="e.g. Yahya Idrissi">
      <label>Instagram</label>
      <input type="text" name="instagram" placeholder="@yourhandle">
      <button type="submit">Generate Code</button>
    </form>
  </div>
</body>
</html>
"""

CODE_CREATED_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Your Invalid8th Code</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
           background:#050505; color:#f5f5f5; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; }
    .card { background:#111; padding:24px 28px; border-radius:16px; max-width:380px; width:100%;
            box-shadow:0 12px 40px rgba(0,0,0,0.5); text-align:center; }
    h1 { font-size:20px; margin-top:0; margin-bottom:6px; text-transform:uppercase; letter-spacing:0.12em; }
    p { font-size:14px; color:#bbb; }
    .code { font-size:22px; font-weight:700; letter-spacing:0.18em; margin:14px 0; }
    .label { font-size:11px; text-transform:uppercase; color:#777; letter-spacing:0.14em; }
    a.button { display:block; margin-top:14px; padding:10px 12px; border-radius:999px; border:none;
             background:#f5f5f5; color:#000; font-weight:600; letter-spacing:0.12em; font-size:12px;
             text-transform:uppercase; text-decoration:none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Welcome, {{ name.split()[0] }}</h1>
    <p>This is your personal Invalid8th access code. Keep it safe.</p>
    <div class="label">Your code</div>
    <div class="code">{{ code }}</div>
    <p>Next time you visit, use this instead of NHBH and we’ll recognise you instantly.</p>
    <a href="{{ url_for('dashboard') }}" class="button">Continue</a>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Invalid8th Portal</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
           background:#050505; color:#f5f5f5; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; }
    .card { background:#111; padding:24px 28px; border-radius:16px; max-width:420px; width:100%;
            box-shadow:0 12px 40px rgba(0,0,0,0.5); }
    h1 { font-size:22px; margin-top:0; margin-bottom:10px; }
    p { font-size:14px; color:#bbb; }
    .pill { display:inline-block; padding:4px 10px; border-radius:999px; background:#222;
            font-size:11px; letter-spacing:0.12em; text-transform:uppercase; color:#aaa; }
    .row { margin-top:10px; font-size:13px; }
    .label { color:#777; font-size:11px; text-transform:uppercase; letter-spacing:0.12em; }
    .value { color:#eee; margin-top:2px; }
    a.button { display:inline-block; margin-top:16px; padding:10px 12px; border-radius:999px;
               background:#f5f5f5; color:#000; font-weight:600; letter-spacing:0.12em;
               font-size:12px; text-transform:uppercase; text-decoration:none; }
  </style>
</head>
<body>
  <div class="card">
    <span class="pill">Invalid8th Elite</span>
    <h1>Welcome back, {{ first_name }} 👋</h1>
    <p>You’re in. Your details are saved – you don’t need to explain yourself twice.</p>

    <div class="row">
      <div class="label">Personal code</div>
      <div class="value">{{ code }}</div>
    </div>

    <div class="row">
      <div class="label">Name</div>
      <div class="value">{{ name }}</div>
    </div>

    <div class="row">
      <div class="label">Instagram</div>
      <div class="value">{{ instagram }}</div>
    </div>

    <p style="margin-top:16px;">You can now go to the booking site or message the Telegram bot to lock in your slot.</p>
    <!-- You can change this link to your real booking URL -->
    <a href="https://t.me/{{ telegram_username or '' }}" class="button">Open Invalid8th Bot</a>
  </div>
</body>
</html>
"""

# ---------- HELPERS ---------- #

def generate_personal_code(full_name: str, instagram: str) -> str:
    first = full_name.strip().split()[0].upper()
    db = SessionLocal()
    try:
        while True:
            num = random.randint(10, 99)
            code = f"{first}{num}"
            existing = db.query(AccessCode).filter_by(code=code).first()
            if not existing:
                db.add(AccessCode(code=code, name=full_name.strip(), instagram=instagram.strip()))
                db.commit()
                return code
    finally:
        db.close()


def verify_code(entered_code: str):
    code = entered_code.strip().upper()
    db = SessionLocal()
    try:
        obj = db.query(AccessCode).filter_by(code=code).first()
        if obj:
            obj.last_seen_at = datetime.utcnow()
            db.commit()
        return obj
    finally:
        db.close()


# ---------- ROUTES ---------- #

@app.route("/", methods=["GET", "POST"])
def access():
    if request.method == "POST":
        entered = request.form.get("access_code", "").strip()
        if not entered:
            return render_template_string(ACCESS_HTML, error="Enter a code to continue.")

        code_obj = verify_code(entered)
        if code_obj:
            # Master code => send to create personal code
            if code_obj.code == "NHBH":
                return redirect(url_for("create_code"))

            # Personal code => straight to dashboard
            session["user_name"] = code_obj.name
            session["user_instagram"] = code_obj.instagram
            session["user_code"] = code_obj.code
            return redirect(url_for("dashboard"))

        return render_template_string(ACCESS_HTML, error="Invalid code. Double-check and try again.")

    return render_template_string(ACCESS_HTML, error=None)


@app.route("/create", methods=["GET", "POST"])
def create_code():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        ig = request.form.get("instagram", "").strip()

        if not name:
            return render_template_string(CREATE_CODE_HTML, error="Please enter your name.")

        if ig and not ig.startswith("@"):
            ig = "@" + ig

        code = generate_personal_code(name, ig or "")

        session["user_name"] = name
        session["user_instagram"] = ig or ""
        session["user_code"] = code

        return render_template_string(CODE_CREATED_HTML, name=name, code=code)

    return render_template_string(CREATE_CODE_HTML, error=None)


@app.route("/dashboard")
def dashboard():
    code = session.get("user_code")
    name = session.get("user_name")
    instagram = session.get("user_instagram")

    if not code:
        return redirect(url_for("access"))

    first_name = (name or "").split()[0] or "Member"

    # put your Telegram @username below if you want that button to work
    telegram_username = os.getenv("TELEGRAM_PUBLIC_USERNAME", "")

    return render_template_string(
        DASHBOARD_HTML,
        first_name=first_name,
        name=name or "",
        instagram=instagram or "",
        code=code,
        telegram_username=telegram_username,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

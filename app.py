from flask import Flask, render_template, request, jsonify, session, redirect
import time
import random
import sqlite3
import os
from datetime import datetime, timedelta
from flask_cors import CORS
import hashlib

from database import (
    init_db,
    insert_lucky_number,
    update_user,
    get_user_data,
    get_today_lucky_numbers,
    record_lucky_winner,
    get_lucky_history
)

app = Flask(__name__)
@app.context_processor
def inject_user():
    return dict(user_id=session.get("user_id"))
    
app.secret_key = "tasko-secret"
CORS(app)

DB_FILE = "tasko.db"
COOLDOWN_SECONDS = 60
MAX_CLICKS_PER_DAY = 20
REWARD_OPTIONS = [
    (1, 0.5),
    (2, 0.25),
    (4, 0.125),
    (8, 0.0625),
    ("BONUS", 0.0625)
]

def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    else:
        ip = request.remote_addr
    return ip

def now_myt():
    return datetime.utcnow() + timedelta(hours=8)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_user_id():
    return "id" + str(random.randint(1000000, 9999999))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        age = request.form.get("age")
        user_id = generate_user_id()
        hashed = hash_password(password)
        created_at = now_myt().isoformat()

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                password TEXT,
                age INTEGER,
                points REAL DEFAULT 0,
                clicks_today INTEGER DEFAULT 0,
                last_click_time TEXT,
                last_reset_date TEXT,
                referrer_id TEXT,
                created_at TEXT
            )
        """)

        c.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return render_template("register.html", error="此 Email 已注册，请直接登录或更换。")

        c.execute("""
            INSERT INTO users (user_id, email, password, age, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, email, hashed, age, created_at))

        conn.commit()
        conn.close()

        session["user_id"] = user_id
        return redirect("/")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect("/")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        hashed = hash_password(password)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id, password FROM users WHERE email = ?", (email,))
        row = c.fetchone()
        conn.close()

        if row:
            stored_user_id, stored_password = row
            if hashed == stored_password:
                session["user_id"] = stored_user_id
                return redirect("/")
            else:
                return render_template("login.html", error="密码错误，请重试。")
        else:
            return render_template("login.html", error="找不到该 Email，请确认后再试。")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return render_template("logout.html")

@app.route("/lucky-draw")
def lucky_draw():
    return render_template("lucky_draw.html")

@app.route("/withdraw")
def withdraw():
    return render_template("withdraw.html")

@app.route("/api/today-winner")
def api_today_winner():
    today_str = now_myt().strftime("%Y-%m-%d")
    history = get_lucky_history(limit=1)
    if history and history[0][0] == today_str:
        return jsonify({
            "success": True,
            "date": history[0][0],
            "number": history[0][1],
            "user": history[0][2]
        })
    else:
        return jsonify({"success": False})

@app.route("/api/lucky-history")
def api_lucky_history():
    records = get_lucky_history(limit=30)
    data = []
    for row in records:
        data.append({
            "date": row[0],
            "number": row[1],
            "user": row[2]
        })
    return jsonify(data)

@app.route("/api/user-status")
def api_user_status():
    ip = get_ip()
    user = get_user_data(ip)
    return jsonify({
        "clicks_today": user["clicks_today"],
        "points": user["points"]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

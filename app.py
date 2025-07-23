from flask import Flask, render_template, request, jsonify, session
app = Flask(__name__)
import time
import random
import sqlite3
import os
from datetime import datetime, timedelta
from flask_cors import CORS

from database import (
    init_db,
    insert_lucky_number,
    update_user,
    get_user_data
)

app = Flask(__name__)
app.secret_key = "tasko-secret"
CORS(app)

DB_FILE = "tasko.db"
COOLDOWN_SECONDS = 60
MAX_CLICKS_PER_DAY = 20

REWARD_OPTIONS = [
    (1, 0.50),
    (2, 0.25),
    (4, 0.125),
    (8, 0.0625),
    (16, 0.03125),
    (32, 0.015625),
    (100, 0.015625)  # Lucky Draw ticket（目前你没用到这个）
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/click")
def click():
    now = int(time.time())
    session_id = session.get('id')
    if not session_id:
        session['id'] = os.urandom(16).hex()
        session_id = session['id']

    # 抽奖封锁时间段：23:55:00 – 23:59:59（UTC+0）
    now_utc = datetime.utcnow()
    if now_utc.hour == 23 and now_utc.minute >= 55:
        return jsonify({"error": "⚠️ 当前为抽奖结算时间，请稍后再试。"})

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT timestamp FROM clicks WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1", (session_id,))
        last = c.fetchone()
        if last and now - last[0] < COOLDOWN_SECONDS:
            return jsonify({"error": "请等待冷却时间"})

        today_start = int(datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        c.execute("SELECT COUNT(*) FROM clicks WHERE session_id = ? AND timestamp >= ?", (session_id, today_start))
        count = c.fetchone()[0]
        if count >= MAX_CLICKS_PER_DAY:
            return jsonify({"error": "今天点击次数已达上限"})

        reward = random.choices([r[0] for r in REWARD_OPTIONS], weights=[r[1] for r in REWARD_OPTIONS])[0]
        c.execute("INSERT INTO clicks (session_id, timestamp, reward) VALUES (?, ?, ?)", (session_id, now, reward))
        conn.commit()

    update_user(session_id, reward)
    lucky_number = insert_lucky_number(session_id)

    return jsonify({
        "reward": reward,
        "lucky_number": lucky_number,
        "success": True
    })

@app.route("/lucky-draw")
def lucky_draw():
    return render_template("lucky_draw.html")

@app.route("/withdraw")
def withdraw():
    return render_template("withdraw.html")

@app.route("/logout")
def logout():
    return render_template("coming_soon.html")

@app.route("/api/today-winner")
def api_today_winner():
    from database import get_lucky_history
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
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
    from database import get_lucky_history
    records = get_lucky_history(limit=10)
    data = []
    for row in records:
        data.append({
            "date": row[0],
            "number": row[1],
            "user": row[2]
        })
    return jsonify(data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

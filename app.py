from flask import Flask, render_template, request, jsonify, session
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
    get_user_data,
    get_today_lucky_numbers,
    record_lucky_winner,
    get_lucky_history
)

app = Flask(__name__)
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
    ("BONUS", 0.0625)  # 送1分 + 再抽一次
]

# 获取真实 IP（包括代理）
def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    else:
        ip = request.remote_addr
    return ip

# 获取当前马来西亚时间（UTC+8）
def now_myt():
    return datetime.utcnow() + timedelta(hours=8)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/click")
def click():
    ip = get_ip()
    now = now_myt()
    today_str = now.strftime("%Y-%m-%d")

    # 抽奖封锁时间段（MYT）：23:55–23:59
    if now.hour == 23 and now.minute >= 55:
        return jsonify({"error": "⚠️ 当前为抽奖结算时间，请稍后再试。"})

    # 连接数据库
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 用户冷却检查
    c.execute("SELECT last_click_time, clicks_today, last_reset_date FROM users WHERE ip = ?", (ip,))
    row = c.fetchone()

    if row:
        last_click_time = datetime.fromisoformat(row[0]) if row[0] else None
        clicks_today = row[1] or 0
        last_reset_date = row[2]

        if last_reset_date != today_str:
            clicks_today = 0  # 重置点击次数

        if clicks_today >= MAX_CLICKS_PER_DAY:
            return jsonify({"error": "⚠️ 今天点击次数已达上限。"})

        if last_click_time and (now - last_click_time).total_seconds() < COOLDOWN_SECONDS:
            return jsonify({"error": f"请等待冷却时间 ({COOLDOWN_SECONDS} 秒)"})
    else:
        clicks_today = 0

    # 奖励逻辑
    reward_choice = random.choices([r[0] for r in REWARD_OPTIONS], weights=[r[1] for r in REWARD_OPTIONS])[0]
    rewards = []

    if reward_choice == "BONUS":
        rewards.append(1)
        second_reward = random.choices([r[0] for r in REWARD_OPTIONS if r[0] != "BONUS"],
                                       weights=[r[1] for r in REWARD_OPTIONS if r[0] != "BONUS"])[0]
        rewards.append(second_reward)
    else:
        rewards.append(reward_choice)

    total_reward = sum(rewards)

    # 更新用户数据 + 存入 lucky number
    update_user(ip, total_reward)
    lucky_number = insert_lucky_number(ip)

    conn.close()

    return jsonify({
        "reward": rewards,
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
    return render_template("logout.html")

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

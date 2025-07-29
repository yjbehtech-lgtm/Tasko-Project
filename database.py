# ✅ 完整版 database.py（Lucky Number 修正）

import sqlite3
from datetime import datetime, timedelta
import random
import string

DATABASE_NAME = "tasko.db"

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 注册用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password TEXT,
            age INTEGER,
            points REAL DEFAULT 0,
            last_roll_time TEXT,
            daily_rolls INTEGER DEFAULT 0,
            referrer_id TEXT
        )
    ''')

    # 幸运号码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            lucky_number TEXT UNIQUE,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()

def insert_lucky_number(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    max_tries = 5
    lucky_number = None
    for _ in range(max_tries):
        candidate = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        try:
            cursor.execute('''
                INSERT INTO lucky_numbers (user_id, lucky_number, timestamp)
                VALUES (?, ?, ?)
            ''', (user_id, candidate, datetime.now().isoformat()))
            conn.commit()
            lucky_number = candidate
            break
        except sqlite3.IntegrityError:
            continue  # 如果重复就再试
    conn.close()
    return lucky_number

def get_latest_lucky_number(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT lucky_number FROM lucky_numbers
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

# 🎯 获取今日全部 lucky numbers
def get_today_lucky_numbers():
    conn = get_connection()
    cursor = conn.cursor()
    today_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT number, user_id FROM lucky_numbers
        WHERE created_at LIKE ?
    ''', (today_str + "%",))
    numbers = cursor.fetchall()
    conn.close()
    return numbers

def record_lucky_winner(lucky_number, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    date_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO lucky_winners (date, number, user_id)
        VALUES (?, ?, ?)
    ''', (date_str, lucky_number, user_id))
    conn.commit()
    conn.close()

def get_lucky_history(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, number, user_id FROM lucky_winners
        ORDER BY date DESC
        LIMIT ?
    ''', (limit,))
    records = cursor.fetchall()
    conn.close()
    return records

# 💠 更新用户积分
def update_user(user_id, reward_points):
    conn = get_connection()
    cursor = conn.cursor()

    today = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")
    cursor.execute("SELECT last_reset_date, clicks_today FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if row:
        last_reset_date, clicks_today = row
        if last_reset_date != today:
            clicks_today = 0
    else:
        print(f"[Error] 用户 {user_id} 不存在")
        conn.close()
        return

    cursor.execute('''
        UPDATE users
        SET points = points + ?,
            clicks_today = ?,
            last_click_time = ?,
            last_reset_date = ?
        WHERE user_id = ?
    ''', (
        reward_points,
        clicks_today + 1,
        datetime.utcnow().isoformat(),
        today,
        user_id
    ))

    conn.commit()
    conn.close()

# 🔍 通过 email 获取用户
def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, email, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

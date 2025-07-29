# database.py（修复版 - 支持日志与调试）

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
            clicks_today INTEGER DEFAULT 0,
            last_click_time TEXT,
            last_reset_date TEXT,
            referrer_id TEXT,
            created_at TEXT
        )
    ''')

    # 幸运号码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            number TEXT,
            created_at TEXT
        )
    ''')

    # 抽奖记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            number TEXT,
            user_id TEXT
        )
    ''')

    conn.commit()
    conn.close()

# 🔁 Lucky Number 生成

def generate_lucky_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def insert_lucky_number(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow() + timedelta(hours=8)
        today_str = now.strftime("%Y-%m-%d")

        cursor.execute('''
            SELECT COUNT(*) FROM lucky_numbers
            WHERE user_id = ? AND substr(created_at, 1, 10) = ?
        ''', (user_id, today_str))
        count = cursor.fetchone()[0]

        if count >= 20:
            conn.close()
            return "（已达今日上限）"

        max_attempts = 100
        for _ in range(max_attempts):
            lucky_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
            cursor.execute('''
                SELECT 1 FROM lucky_numbers
                WHERE number = ? AND substr(created_at, 1, 10) = ?
            ''', (lucky_number, today_str))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO lucky_numbers (user_id, number, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, lucky_number, now.isoformat()))
                conn.commit()
                conn.close()
                print(f"[✅ LuckyNumber] user={user_id} → {lucky_number}")
                return lucky_number

        conn.close()
        print("[❌] 超过最大尝试次数，号码重复")
        return "（生成失败：号码冲突）"

    except Exception as e:
        print(f"[❌ insert_lucky_number ERROR] user_id={user_id}, error={e}")
        return "（生成失败）"

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

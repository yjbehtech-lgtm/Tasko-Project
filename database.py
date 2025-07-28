# database.py（已升级支持 user_id）

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

    # 注册用户表（保持不变）
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

    # 🎯 幸运号码表（以 user_id 替代 IP）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            number TEXT,
            created_at TEXT
        )
    ''')

    # 🏆 抽奖记录表（以 user_id 替代 IP）
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

# 🔁 Lucky Number 功能

def generate_lucky_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))

def insert_lucky_number(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    today_str = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d")

    # 每用户每日最多 20 个 lucky number
    cursor.execute('''
        SELECT COUNT(*) FROM lucky_numbers
        WHERE user_id = ? AND created_at LIKE ?
    ''', (user_id, today_str + "%"))
    count = cursor.fetchone()[0]
    if count >= 20:
        return "（已达今日上限）"

    # 生成唯一 lucky number
    while True:
        lucky_number = generate_lucky_code()
        cursor.execute("SELECT 1 FROM lucky_numbers WHERE number = ? AND created_at LIKE ?",
                       (lucky_number, today_str + "%"))
        if not cursor.fetchone():
            break

    cursor.execute('''
        INSERT INTO lucky_numbers (user_id, number, created_at)
        VALUES (?, ?, ?)
    ''', (user_id, lucky_number, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return lucky_number

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

    conn.close()
    return records

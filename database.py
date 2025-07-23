# database.py

import sqlite3
from datetime import datetime, timedelta
import random

DATABASE_NAME = "tasko.db"

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 用户数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            ip TEXT PRIMARY KEY,
            points REAL DEFAULT 0,
            last_click_time TEXT,
            clicks_today INTEGER DEFAULT 0,
            last_reset_date TEXT
        )
    ''')

    # 幸运号码表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            number TEXT UNIQUE,
            created_at TEXT
        )
    ''')

    # 中奖记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            number TEXT,
            session_id TEXT
        )
    ''')

    conn.commit()
    conn.close()

def get_user(ip):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE ip = ?", (ip,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user(ip, reward):
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")

    user = get_user(ip)
    if user:
        last_reset_date = user[4]
        clicks_today = user[3]

        if last_reset_date != today:
            clicks_today = 0
            cursor.execute('''
                UPDATE users
                SET clicks_today = 0,
                    last_reset_date = ?
                WHERE ip = ?
            ''', (today, ip))

        new_points = user[1] + reward
        new_clicks = clicks_today + 1
        cursor.execute('''
            UPDATE users
            SET points = ?,
                last_click_time = ?,
                clicks_today = ?
            WHERE ip = ?
        ''', (new_points, now.isoformat(), new_clicks, ip))
    else:
        cursor.execute('''
            INSERT INTO users (ip, points, last_click_time, clicks_today, last_reset_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip, reward, now.isoformat(), 1, today))

    conn.commit()
    conn.close()

def get_user_data(ip):
    user = get_user(ip)
    if user:
        return {
            "points": round(user[1], 2),
            "last_click_time": user[2],
            "clicks_today": user[3],
            "last_reset_date": user[4]
        }
    else:
        return {
            "points": 0,
            "last_click_time": None,
            "clicks_today": 0,
            "last_reset_date": None
        }

# 🎯 Lucky Number 功能

def insert_lucky_number(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # 生成唯一幸运号码
    while True:
        lucky_number = "{:07d}".format(random.randint(0, 9999999))
        cursor.execute("SELECT 1 FROM lucky_numbers WHERE number = ? AND created_at LIKE ?", (lucky_number, today_str + "%"))
        if not cursor.fetchone():
            break

    cursor.execute('''
        INSERT INTO lucky_numbers (session_id, number, created_at)
        VALUES (?, ?, ?)
    ''', (session_id, lucky_number, datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return lucky_number

def get_today_lucky_numbers():
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute('''
        SELECT number FROM lucky_numbers
        WHERE created_at LIKE ?
    ''', (today_str + "%",))
    numbers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return numbers

def record_lucky_winner(lucky_number, session_id):
    conn = get_connection()
    cursor = conn.cursor()
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute('''
        INSERT INTO lucky_winners (date, number, session_id)
        VALUES (?, ?, ?)
    ''', (date_str, lucky_number, session_id))
    conn.commit()
    conn.close()

def get_lucky_history(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, number, session_id FROM lucky_winners
        ORDER BY date DESC
        LIMIT ?
    ''', (limit,))
    records = cursor.fetchall()
    conn.close()
    return records

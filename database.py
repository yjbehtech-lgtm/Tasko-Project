import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = "tasko.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 检查 users 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    exists = cursor.fetchone()

    # 如果存在，就检测字段是否齐全
    if exists:
        try:
            cursor.execute("PRAGMA table_info(users);")
            columns = [col[1] for col in cursor.fetchall()]
            required_columns = [
                'user_id', 'email', 'password', 'age', 'points',
                'clicks_today', 'last_click_time', 'last_reset_date',
                'referrer_id', 'created_at'
            ]
            if not all(col in columns for col in required_columns):
                raise Exception("字段不完整，准备重建表")
        except Exception as e:
            print("[!] 表结构错误，删除旧表重建：", e)
            cursor.execute("DROP TABLE IF EXISTS users")

    # 建立 users 表（如果不存在或已删除）
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
        );
    ''')

    conn.commit()
    conn.close()

def create_user(user_id, email, password, age, referrer_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO users (user_id, email, password, age, referrer_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, email, password, age, referrer_id, now))
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_user_points(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def get_click_info(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clicks_today, last_click_time, last_reset_date FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row if row else (0, None, None)

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

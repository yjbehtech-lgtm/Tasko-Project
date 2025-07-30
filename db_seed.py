import sqlite3
import hashlib
from datetime import datetime, timedelta

DB_FILE = "tasko.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def now_myt():
    return datetime.utcnow() + timedelta(hours=8)

def seed_test_user():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 确保 users 表存在
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

    # 检查是否已存在测试账号
    email = "test@tasko.com"
    c.execute("SELECT user_id FROM users WHERE email = ?", (email,))
    if c.fetchone():
        print("[✅] 测试账号已存在，无需重复插入")
    else:
        user_id = "id9999999"
        hashed_pw = hash_password("test1234")
        now = now_myt().isoformat()
        c.execute("""
            INSERT INTO users (user_id, email, password, age, referrer_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, email, hashed_pw, 25, None, now))
        print("[🎉] 已成功插入测试账号 test@tasko.com / test1234")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_test_user()

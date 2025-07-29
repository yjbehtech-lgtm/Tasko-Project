import sqlite3

conn = sqlite3.connect("tasko.db")
cursor = conn.cursor()

print("🧪 当前数据库中存在的表：")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for t in tables:
    print(f"✅ 表名：{t[0]}")

print("\n🔍 lucky_numbers 表结构：")
cursor.execute("PRAGMA table_info(lucky_numbers);")
columns = cursor.fetchall()
for col in columns:
    print(f"- {col[1]} ({col[2]})")

conn.close()

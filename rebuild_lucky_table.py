import sqlite3

DB_NAME = "tasko.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("⚠️ 删除旧 lucky_numbers 表（如果存在）...")
cursor.execute("DROP TABLE IF EXISTS lucky_numbers")

print("✅ 创建新 lucky_numbers 表...")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS lucky_numbers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        number TEXT,
        created_at TEXT
    )
''')

conn.commit()
conn.close()
print("🎉 表已成功重建，请重新尝试 roll 获取幸运号码！")

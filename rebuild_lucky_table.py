# rebuild_lucky_table.py
from database import get_connection

def rebuild_lucky_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lucky_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            number TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ lucky_numbers 表已创建（如尚未存在）")

if __name__ == "__main__":
    rebuild_lucky_table()

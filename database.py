import sqlite3

DB_NAME = "clipboard_history.db"

def create_database():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            favorite INTEGER DEFAULT 0,
            category TEXT DEFAULT 'Text'
        )
    """)

    conn.commit()
    conn.close()

def save_clipboard(text, category="Text"):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO history
        (content, category)
        VALUES (?, ?)
        """,
        (text, category)
    )

    conn.commit()
    conn.close()

def load_history():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]

def delete_item(text):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE content=?",
        (text,)
    )

    conn.commit()
    conn.close()

def mark_favorite(text):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE history
        SET favorite=1
        WHERE content=?
        """,
        (text,)
    )

    conn.commit()
    conn.close()
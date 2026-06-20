import os
import sqlite3

from settings import MAX_HISTORY

# Keep the database next to this file so it is always the same one,
# no matter which folder the app is launched from.
DB_NAME = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "clipboard_history.db"
)

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

    # Keep the existing favorite flag if the same text was saved before,
    # then move the entry to the top by re-inserting it.
    cursor.execute(
        "SELECT favorite FROM history WHERE content=?",
        (text,)
    )

    row = cursor.fetchone()
    favorite = row[0] if row else 0

    cursor.execute(
        "DELETE FROM history WHERE content=?",
        (text,)
    )

    cursor.execute(
        """
        INSERT INTO history
        (content, favorite, category)
        VALUES (?, ?, ?)
        """,
        (text, favorite, category)
    )

    # Enforce the history limit, but never drop favorites.
    cursor.execute(
        """
        DELETE FROM history
        WHERE favorite=0
        AND id NOT IN (
            SELECT id FROM history
            WHERE favorite=0
            ORDER BY id DESC
            LIMIT ?
        )
        """,
        (MAX_HISTORY,)
    )

    conn.commit()
    conn.close()

def load_history():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, category, favorite
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {"content": r[0], "category": r[1], "favorite": r[2]}
        for r in rows
    ]

def load_favorites():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, category, favorite
        FROM history
        WHERE favorite=1
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {"content": r[0], "category": r[1], "favorite": r[2]}
        for r in rows
    ]

def delete_item(text):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE content=?",
        (text,)
    )

    conn.commit()
    conn.close()

def clear_history():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM history")

    conn.commit()
    conn.close()

def set_favorite(text, favorite):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE history
        SET favorite=?
        WHERE content=?
        """,
        (1 if favorite else 0, text)
    )

    conn.commit()
    conn.close()

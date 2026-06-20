import os
import sqlite3

from settings import MAX_HISTORY

# Keep the database next to this file no matter where the app is launched.
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clipboard_history.db")

def _connect():
    return sqlite3.connect(DB_NAME)

def create_database():

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            favorite INTEGER DEFAULT 0,
            category TEXT DEFAULT 'Text',
            pinned INTEGER DEFAULT 0,
            created TEXT DEFAULT ''
        )
    """)

    # Add new columns to older databases that don't have them yet.
    existing = [row[1] for row in cursor.execute("PRAGMA table_info(history)")]

    if "pinned" not in existing:
        cursor.execute("ALTER TABLE history ADD COLUMN pinned INTEGER DEFAULT 0")

    if "created" not in existing:
        cursor.execute("ALTER TABLE history ADD COLUMN created TEXT DEFAULT ''")

    conn.commit()
    conn.close()

def _rows_to_dicts(rows):
    return [
        {
            "content": r[0],
            "category": r[1],
            "favorite": r[2],
            "pinned": r[3],
            "created": r[4],
        }
        for r in rows
    ]

def save_clipboard(text, category="Text", created=""):

    conn = _connect()
    cursor = conn.cursor()

    # Keep the existing favorite / pinned flags if the same text was saved
    # before, then move the entry to the top by re-inserting it.
    cursor.execute(
        "SELECT favorite, pinned FROM history WHERE content=?",
        (text,)
    )

    row = cursor.fetchone()
    favorite = row[0] if row else 0
    pinned = row[1] if row else 0

    cursor.execute("DELETE FROM history WHERE content=?", (text,))

    cursor.execute(
        """
        INSERT INTO history
        (content, favorite, category, pinned, created)
        VALUES (?, ?, ?, ?, ?)
        """,
        (text, favorite, category, pinned, created)
    )

    # Enforce the history limit, but never drop favourites or pinned items.
    cursor.execute(
        """
        DELETE FROM history
        WHERE favorite=0 AND pinned=0
        AND id NOT IN (
            SELECT id FROM history
            WHERE favorite=0 AND pinned=0
            ORDER BY id DESC
            LIMIT ?
        )
        """,
        (MAX_HISTORY,)
    )

    conn.commit()
    conn.close()

def load_history():

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, category, favorite, pinned, created
        FROM history
        ORDER BY pinned DESC, id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return _rows_to_dicts(rows)

def load_favorites():

    conn = _connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, category, favorite, pinned, created
        FROM history
        WHERE favorite=1
        ORDER BY pinned DESC, id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return _rows_to_dicts(rows)

def delete_item(text):

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE content=?", (text,))
    conn.commit()
    conn.close()

def clear_history():

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()

def set_favorite(text, favorite):

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE history SET favorite=? WHERE content=?",
        (1 if favorite else 0, text)
    )
    conn.commit()
    conn.close()

def set_pinned(text, pinned):

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE history SET pinned=? WHERE content=?",
        (1 if pinned else 0, text)
    )
    conn.commit()
    conn.close()

def delete_older_than(cutoff):
    """Delete plain items created before cutoff (a 'YYYY-MM-DD HH:MM' string).
    Favourites and pinned items are always kept."""

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM history
        WHERE favorite=0 AND pinned=0
        AND created <> '' AND created < ?
        """,
        (cutoff,)
    )
    conn.commit()
    conn.close()

def import_items(items, created=""):
    """Insert a list of text items (used by Import History)."""

    for text in items:
        if text.strip():
            save_clipboard(text, "Text", created)

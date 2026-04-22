import sqlite3
import uuid
from datetime import datetime

DB_PATH = "notes.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT,
        body TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def create_note(title, body):
    conn = get_conn()
    cursor = conn.cursor()

    note_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO notes VALUES (?, ?, ?, ?)",
        (note_id, title, body, now)
    )

    conn.commit()
    conn.close()

    return {"id": note_id, "title": title}


def list_notes():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title FROM notes")
    rows = cursor.fetchall()

    conn.close()

    return [{"id": r[0], "title": r[1]} for r in rows]


def search_notes(query):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title FROM notes WHERE body LIKE ?",
        (f"%{query}%",)
    )

    rows = cursor.fetchall()
    conn.close()

    return [{"id": r[0], "title": r[1]} for r in rows]

def get_notes_by_title(title, exact=False):
    conn = get_conn()
    cursor = conn.cursor()

    if exact:
        cursor.execute(
            "SELECT id, title, body, created_at FROM notes WHERE title = ?",
            (title,)
        )
    else:
        cursor.execute(
            "SELECT id, title, body, created_at FROM notes WHERE title LIKE ?",
            (f"%{title}%",)
        )

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "body": r[2],
            "created_at": r[3]
        }
        for r in rows
    ]

def delete_note_by_id(note_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()

    deleted = cursor.rowcount
    conn.close()

    return {"deleted": deleted > 0}

def delete_notes_by_title(title):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM notes WHERE title = ?", (title,))
    conn.commit()

    deleted_count = cursor.rowcount
    conn.close()

    return {"deleted_count": deleted_count}

def update_note(note_id, title=None, body=None):
    if title is None and body is None:
        return {"updated": False, "reason": "Nothing to update"}

    conn = get_conn()
    cursor = conn.cursor()

    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if body is not None:
        updates.append("body = ?")
        params.append(body)

    params.append(note_id)

    query = f"UPDATE notes SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)

    conn.commit()
    updated = cursor.rowcount
    conn.close()

    return {"updated": updated > 0}

def get_note_by_id(note_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, body, created_at FROM notes WHERE id = ?",
        (note_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "body": row[2],
        "created_at": row[3]
    }

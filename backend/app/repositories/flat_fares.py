import sqlite3
from datetime import datetime, timezone


def list_all(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, start, end, price, created_at FROM flat_fares ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


def get_pair(conn: sqlite3.Connection, start: str, end: str) -> dict | None:
    row = conn.execute(
        "SELECT id, start, end, price, created_at FROM flat_fares WHERE start=? AND end=?",
        (start, end),
    ).fetchone()
    return dict(row) if row else None


def insert(conn: sqlite3.Connection, start: str, end: str, price: float) -> int:
    """Insert a directed OD flat fare. Raises sqlite3.IntegrityError on duplicate pair."""
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO flat_fares(start, end, price, created_at) VALUES (?,?,?,?)",
        (start, end, float(price), now),
    )
    conn.commit()
    return int(cur.lastrowid)


def delete_pair(conn: sqlite3.Connection, start: str, end: str) -> bool:
    cur = conn.execute("DELETE FROM flat_fares WHERE start=? AND end=?", (start, end))
    conn.commit()
    return cur.rowcount > 0

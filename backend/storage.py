import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pm.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
DEFAULT_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": []},
        {"id": "col-discovery", "title": "Discovery", "cardIds": []},
        {"id": "col-progress", "title": "In Progress", "cardIds": []},
        {"id": "col-review", "title": "Review", "cardIds": []},
        {"id": "col-done", "title": "Done", "cardIds": []},
    ],
    "cards": {},
}


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_PATH.read_text())


def _ensure_user(connection: sqlite3.Connection, username: str) -> int:
    row = connection.execute("select id from users where username = ?", (username,)).fetchone()
    if row:
        return int(row["id"])
    cursor = connection.execute(
        "insert into users (username, password) values (?, ?)",
        (username, "password"),
    )
    return int(cursor.lastrowid)


def _ensure_board(connection: sqlite3.Connection, user_id: int) -> None:
    exists = connection.execute("select 1 from boards where user_id = ?", (user_id,)).fetchone()
    if exists:
        return
    connection.execute(
        "insert into boards (user_id, board_json) values (?, ?)",
        (user_id, json.dumps(DEFAULT_BOARD)),
    )


def get_board(username: str) -> dict:
    """Return a user's board, creating the database, user, and board if needed."""
    with _connect() as connection:
        _ensure_schema(connection)
        user_id = _ensure_user(connection, username)
        _ensure_board(connection, user_id)
        row = connection.execute(
            "select board_json from boards where user_id = ?",
            (user_id,),
        ).fetchone()
    return json.loads(row["board_json"])


def save_board(username: str, board: dict) -> dict:
    """Persist a full board document for a user and return the stored value."""
    payload = json.dumps(board)
    with _connect() as connection:
        _ensure_schema(connection)
        user_id = _ensure_user(connection, username)
        _ensure_board(connection, user_id)
        connection.execute(
            """update boards
            set board_json = ?, updated_at = CURRENT_TIMESTAMP
            where user_id = ?""",
            (payload, user_id),
        )
    return board

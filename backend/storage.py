import json
import sqlite3
from pathlib import Path

from pydantic import ValidationError

from backend.openrouter import BoardPayload

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


def _normalize_board(board: dict) -> dict:
    """Return a board with the required fixed columns restored in default order.

    Args:
        board: Persisted board payload from storage or the API.

    Returns:
        A normalized board containing all required columns plus only valid cards.
    """
    cards = board.get("cards", {})
    saved_columns = {
        column["id"]: column for column in board.get("columns", []) if "id" in column
    }
    # also this saved_columns is doing a dictionary comprehension to create a mapping of column IDs to their corresponding column data. It filters out any columns that do not have an "id" key, ensuring that only valid columns are included in the saved_columns dictionary.

    # take down all the saved columns in the board, then compare it later with the defaults and populate these columns with the cards from the json.
    columns = []

    for default_column in DEFAULT_BOARD["columns"]:
        saved_column = saved_columns.get(default_column["id"])
        if not saved_column:
            columns.append(default_column.copy())
            continue

        columns.append(
            {
                "id": default_column["id"],
                "title": saved_column.get("title", default_column["title"]),
                "cardIds": [
                    card_id
                    for card_id in saved_column.get("cardIds", [])
                    if card_id in cards
                ],
            }
        )

    return {
        "columns": columns,
        "cards": cards,
    }


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA_PATH.read_text())


def _ensure_user(connection: sqlite3.Connection, username: str) -> int:
    row = connection.execute(
        "select id from users where username = ?", (username,)
    ).fetchone()
    if row:
        return int(row["id"])
    cursor = connection.execute(
        "insert into users (username, password) values (?, ?)",
        (username, "password"),
    )
    return int(cursor.lastrowid)


def _ensure_board(connection: sqlite3.Connection, user_id: int) -> None:
    exists = connection.execute(
        "select 1 from boards where user_id = ?", (user_id,)
    ).fetchone()
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
        board = _normalize_board(json.loads(row["board_json"]))
        connection.execute(
            """update boards
            set board_json = ?, updated_at = CURRENT_TIMESTAMP
            where user_id = ?""",
            (json.dumps(board), user_id),
        )
    return board


def save_board(username: str, board: dict) -> dict:
    """Persist a full board document for a user and return the stored value."""
    normalized_board = _normalize_board(board)
    payload = json.dumps(normalized_board)
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
    return normalized_board


def apply_ai_board_update(username: str, board_update: dict | None) -> dict:
    """Validate and persist an AI-produced board update for a user.

    Args:
        username: Username whose single MVP board should be updated.
        board_update: Full board payload from the AI, or `None` for no-op.

    Returns:
        The current persisted board after applying any valid AI update.

    Raises:
        RuntimeError: If the AI returned a board payload with the wrong shape.
    """
    if board_update is None:
        return get_board(username)
    try:
        validated_board = BoardPayload.model_validate(board_update).model_dump()
    except ValidationError as exc:
        raise RuntimeError("AI board update did not match BoardPayload") from exc
    return save_board(username, validated_board)

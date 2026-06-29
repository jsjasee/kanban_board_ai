# Database model

## Scope

This MVP keeps the database model intentionally small:

- `users` stores login identity. The current app only accepts `user` / `password`, but the table allows more users later.
- `boards` stores exactly one board per user through `UNIQUE (user_id)`.

## Schema

`backend/schema.sql` defines two tables:

- `users(id, username, password)`
- `boards(id, user_id, board_json, created_at, updated_at)`

`boards.user_id` references `users.id` with `ON DELETE CASCADE`, so removing a user also removes that user's board.

## Why store the board as JSON

The frontend already uses one board document with this shape:

```json
{
  "columns": [{ "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] }],
  "cards": {
    "card-1": { "id": "card-1", "title": "Task", "details": "Notes" }
  }
}
```

Storing that document in `boards.board_json` keeps the backend aligned with the existing UI model and avoids splitting one board edit across multiple tables. That is the simplest fit for the MVP because:

- the app only has one board per user
- the main operation is "load or replace the full board state"
- AI updates will also operate on the board as one document

The JSON column is validated with `CHECK (json_valid(board_json))` so invalid payloads cannot be stored.

## Route expectations for Part 6

- `GET` board route: read the single `boards.board_json` row for the signed-in user
- `PUT` board route: replace `boards.board_json` and refresh `updated_at`
- first-run setup: create the user row if needed, then create that user's initial board row

This is approved only for the MVP. If partial card queries or cross-board reporting become important later, we can normalize cards and columns then.

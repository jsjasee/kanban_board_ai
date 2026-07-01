import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, ValidationError

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-5.4-mini"

BOARD_SYSTEM_PROMPT = """You help manage a kanban board.
Always write a short message to the user in "reply".
Leave "board" as null unless the user asked for a change.
If you change the board, return the FULL updated board in "board"."""


class Card(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    details: str


class Column(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    """Persisted board shape used by storage and the frontend."""

    model_config = ConfigDict(extra="forbid")
    columns: list[Column]
    cards: dict[str, Card]


class BoardChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reply: str
    board: BoardPayload | None


BOARD_CHAT_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "BoardChatWireResponse",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "reply": {"type": "string"},
                "board_json": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ]
                },
            },
            "required": ["reply", "board_json"],
        },
    },
}


def _client() -> OpenAI:
    api_key = os.getenv("OPEN_ROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPEN_ROUTER_API_KEY is not set")
    return OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)


def complete_prompt(prompt: str) -> str:
    """Plain text call (e.g. the Part 8 '2+2' connectivity test)."""
    completion = _client().chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[{"role": "user", "content": prompt}],
        timeout=120.0,
    )
    return (completion.choices[0].message.content or "").strip()


def complete_board_chat(board: dict, history: list[dict], message: str) -> dict:
    messages = [{"role": "system", "content": BOARD_SYSTEM_PROMPT}]
    messages += [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m.get("role") in {"user", "assistant"} and m.get("content", "").strip()
    ]
    messages.append(
        {
            "role": "user",
            "content": f"Current board JSON:\n{json.dumps(board)}\n\nUser request:\n{message}",
        }
    )

    completion = _client().chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=messages,
        timeout=30.0,
        response_format=BOARD_CHAT_RESPONSE_FORMAT,
    )
    content = (completion.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("OpenRouter returned an empty response")
    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"OpenRouter response was not valid JSON. Raw response: {content}"
        ) from exc

    reply = str(result.get("reply", "")).strip()
    if not reply:
        raise RuntimeError(
            f'OpenRouter response did not include a valid "reply". Raw response: {content}'
        )

    board_json = result.get("board_json")
    if board_json is None:
        parsed_board = None
    elif isinstance(board_json, str):
        try:
            parsed_board = BoardPayload.model_validate_json(board_json).model_dump()
        except ValidationError as exc:
            raise RuntimeError(
                f'OpenRouter "board_json" did not match BoardPayload: {exc}. Raw response: {content}'
            ) from exc
    else:
        raise RuntimeError(
            f'OpenRouter response included a non-string "board_json". Raw response: {content}'
        )

    return {"reply": reply, "board": parsed_board}

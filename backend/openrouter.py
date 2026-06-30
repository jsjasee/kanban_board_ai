import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-oss-120b:free"
BOARD_SYSTEM_PROMPT = """You are assisting with a kanban board.
Reply for the user in "reply".
Set "board" to null when no board change is needed.
If you change the board, return the full updated board object."""


class BoardCard(BaseModel):
    id: str
    title: str
    details: str


class BoardColumn(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    columns: list[BoardColumn]
    cards: dict[str, BoardCard]


class BoardChatResponse(BaseModel):
    reply: str = Field(min_length=1)
    board: BoardPayload | None


def _client() -> OpenAI:
    return OpenAI(api_key=get_openrouter_api_key(), base_url=OPENROUTER_BASE_URL)


def get_openrouter_api_key() -> str:
    """Return the configured OpenRouter API key from the environment.

    Returns:
        The non-empty OpenRouter API key.

    Raises:
        RuntimeError: If the API key is missing.
    """
    api_key = os.getenv("OPEN_ROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPEN_ROUTER_API_KEY is not set")
    return api_key


def _complete_chat(
    messages: list[dict[str, str]], response_model: type[BaseModel] | None = None
) -> str:
    payload: dict[str, Any] = {"model": OPENROUTER_MODEL, "messages": messages}
    if response_model is not None:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": response_model.model_json_schema(),
            },
        }
    response = _client().chat.completions.create(timeout=30.0, **payload)
    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("OpenRouter returned an empty response")
    return content


def complete_prompt(prompt: str) -> str:
    """Send one prompt to OpenRouter and return the first response message.

    Args:
        prompt: User prompt text to send to the model.

    Returns:
        The first assistant message content.

    Raises:
        RuntimeError: If configuration is missing or the API response is invalid.
    """
    return _complete_chat([{"role": "user", "content": prompt}])


def complete_board_chat(
    board: dict[str, Any], history: list[dict[str, str]], message: str
) -> dict[str, Any]:
    """Send board context to OpenRouter and require structured JSON output.

    Args:
        board: Current persisted kanban board.
        history: Prior chat messages with `role` and `content`.
        message: Latest user request.

    Returns:
        A dict with `reply` text and optional `board` update payload.

    Raises:
        RuntimeError: If the model response does not match the required schema.
    """
    messages = [{"role": "system", "content": BOARD_SYSTEM_PROMPT}]
    messages.extend(
        {"role": item["role"], "content": item["content"]}
        for item in history
        if item.get("role") in {"user", "assistant"} and item.get("content", "").strip()
    )
    messages.append(
        {
            "role": "user",
            "content": f"Current board JSON:\n{json.dumps(board)}\n\nUser request:\n{message}",
        }
    )
    try:
        parsed = BoardChatResponse.model_validate_json(
            _complete_chat(messages, response_model=BoardChatResponse)
        )
    except ValidationError as exc:
        raise RuntimeError(
            "OpenRouter response did not match BoardChatResponse"
        ) from exc
    return parsed.model_dump()

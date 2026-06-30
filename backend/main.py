import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.openrouter import complete_board_chat, complete_prompt
from backend.storage import apply_ai_board_update, get_board, save_board

app = FastAPI(title="pm-backend")
logger = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "out"
MVP_USERNAME = "user"


class ChatMessage(BaseModel):
    role: str
    content: str


class AiChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


def _frontend_file(path: str) -> Path:
    candidate = (FRONTEND_DIR / path).resolve()
    if (
        FRONTEND_DIR.resolve() not in candidate.parents
        and candidate != FRONTEND_DIR.resolve()
    ):
        raise HTTPException(status_code=404, detail="Not found")
    return candidate


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return a simple health status for container smoke checks."""
    return {"status": "ok"}


@app.get("/api/board")
def read_board() -> dict[str, Any]:
    """Return the current MVP user's persisted board."""
    return get_board(MVP_USERNAME)


@app.put("/api/board")
def update_board(board: dict[str, Any]) -> dict[str, Any]:
    """Replace the current MVP user's persisted board."""
    return save_board(MVP_USERNAME, board)


@app.post("/api/ai/test")
def test_ai(payload: dict[str, str]) -> dict[str, str]:
    """Run a basic OpenRouter prompt to verify backend AI connectivity.

    Args:
        payload: Request body containing a `prompt` string.

    Returns:
        The assistant text response for the supplied prompt.

    Raises:
        HTTPException: If the prompt is missing or the AI call fails.
    """
    prompt = payload.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    try:
        return {"reply": complete_prompt(prompt)}
    except Exception as exc:
        logger.exception("AI test request failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/ai/chat")
def chat_with_ai(payload: AiChatRequest) -> dict[str, Any]:
    """Run one AI chat turn and return the latest persisted board state.

    Args:
        payload: Request containing the latest user message and prior chat history.

    Returns:
        The assistant reply plus the current board after any AI update is applied.

    Raises:
        HTTPException: If the message is blank or the AI call/update fails.
    """
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    try:
        ai_result = complete_board_chat(
            get_board(MVP_USERNAME),
            [item.model_dump() for item in payload.history],
            message,
        )
        board = apply_ai_board_update(MVP_USERNAME, ai_result["board"])
        return {"reply": ai_result["reply"], "board": board}
    except Exception as exc:
        logger.exception("AI chat request failed")
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/{path:path}")
def frontend(path: str = "") -> FileResponse:
    """Serve the exported frontend and fall back to index.html for app routes.

    Args:
        path: Requested frontend asset or route path.

    Returns:
        A file response for the requested asset or the exported index page.

    Raises:
        HTTPException: If the frontend build is missing or the path is invalid.
    """
    if not FRONTEND_DIR.exists():
        raise HTTPException(status_code=503, detail="Frontend build is missing")

    requested = _frontend_file(path)
    if requested.is_file():
        return FileResponse(requested)

    if requested.is_dir():
        index_file = requested / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

    index_file = FRONTEND_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(status_code=503, detail="Frontend entrypoint is missing")

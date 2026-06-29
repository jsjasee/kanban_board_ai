from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from backend.storage import get_board, save_board

app = FastAPI(title="pm-backend")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "out"
MVP_USERNAME = "user"


def _frontend_file(path: str) -> Path:
    candidate = (FRONTEND_DIR / path).resolve()
    if FRONTEND_DIR.resolve() not in candidate.parents and candidate != FRONTEND_DIR.resolve():
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

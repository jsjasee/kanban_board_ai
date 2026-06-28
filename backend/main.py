from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="pm-backend")

# use the command: `uv run uvicorn backend.main:app --reload` to test the backend scaffold in development mode


@app.get("/api/health")
def health() -> dict[str, str]:
    """Return a simple health status for container smoke checks."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Return a temporary root page until the frontend build is wired in."""
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Project Management MVP</title>
      </head>
      <body>
        <main>
          <h1>Project Management MVP</h1>
          <p>Backend scaffold is running.</p>
        </main>
      </body>
    </html>
    """

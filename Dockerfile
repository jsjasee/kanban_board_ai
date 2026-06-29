FROM node:22-slim AS frontend-build
# What does node:22-slim do here? It is a lightweight version of the Node.js 22 image, which is used to build the frontend application. The "slim" variant has fewer packages installed, making it smaller and faster to download.

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
# what does npm ci command do here? what does ci mean? install the dependencies in the package-lock.json file.

COPY frontend ./
RUN npm run build

FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY backend ./backend
COPY --from=frontend-build /frontend/out ./frontend/out
# what does --from mean?

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

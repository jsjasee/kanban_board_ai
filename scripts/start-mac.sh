#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="pm-mvp"
CONTAINER_NAME="pm-mvp-app"

docker build -t "$IMAGE_NAME" .
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" --env-file .env -p 8000:8000 "$IMAGE_NAME"
# the last line copies the env file into the docker container! so that docker can read the .env file, otherwise it will think that our keys do not exist.
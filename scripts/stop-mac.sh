#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="pm-mvp-app"

docker rm -f "$CONTAINER_NAME"

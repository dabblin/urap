#!/usr/bin/env bash
# Start urap-engine on port 8080 using Python 3.12 (required for pydantic 2.8)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="/tmp/urap-venv"

if [ ! -f "$VENV/bin/uvicorn" ]; then
  echo "Setting up Python 3.12 venv at $VENV..."
  /usr/local/bin/python3.12 -m venv "$VENV"
  "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q
fi

cd "$SCRIPT_DIR"
exec "$VENV/bin/uvicorn" server.main:app --host 0.0.0.0 --port 8080 --reload

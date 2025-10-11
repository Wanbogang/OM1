#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv >/dev/null 2>&1 || true
. .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
cp -n .env.example .env 2>/dev/null || cp -n env.sample .env 2>/dev/null || true
set -a
[ -f .env ] && . ./.env
set +a
uvicorn bridge:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8081}"

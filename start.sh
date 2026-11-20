#!/usr/bin/env bash
# Sobe a API (8000) e o painel (5173) em modo desenvolvimento. Ctrl+C encerra ambos.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$ROOT/backend/.venv" ]; then
  echo "→ Criando ambiente Python…"
  python3 -m venv "$ROOT/backend/.venv"
  "$ROOT/backend/.venv/bin/pip" install -q -r "$ROOT/backend/requirements-dev.txt"
fi
[ -f "$ROOT/backend/.env" ] || cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
[ -d "$ROOT/frontend/node_modules" ] || (echo "→ Instalando dependências do painel…" && cd "$ROOT/frontend" && npm install --no-audit --no-fund)

(cd "$ROOT/backend" && .venv/bin/uvicorn app.main:app --port 8000 --reload) &
API=$!
trap 'kill $API 2>/dev/null' EXIT

echo "→ Painel: http://localhost:5173  ·  API: http://localhost:8000/docs"
cd "$ROOT/frontend" && npx vite --port 5173

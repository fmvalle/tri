#!/bin/bash
set -e

echo "🚀 Iniciando TRI API..."

if ! command -v python &> /dev/null; then
  echo "❌ Python não encontrado"; exit 1
fi

if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

export UVICORN_HOST=127.0.0.1
export UVICORN_PORT=8000

python -m pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt >/dev/null 2>&1 || true

echo "🌐 API disponível em: http://$UVICORN_HOST:$UVICORN_PORT/docs"

uvicorn api.main:app --host $UVICORN_HOST --port $UVICORN_PORT



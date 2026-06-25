#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAG_DIR="$ROOT_DIR/rag-engine-python"
REQUEST_ID="${1:-test-request-id-smoke}"
PORT="${PORT:-8011}"
LOG_FILE="$(mktemp)"

cleanup() {
  if [[ -n "${RAG_PID:-}" ]]; then
    kill "$RAG_PID" >/dev/null 2>&1 || true
    wait "$RAG_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$LOG_FILE"
}
trap cleanup EXIT

cd "$RAG_DIR"
.venv/bin/python -m uvicorn app.server:app --host 127.0.0.1 --port "$PORT" --log-level info 2>"$LOG_FILE" &
RAG_PID=$!

for _ in {1..60}; do
  if grep -q "Uvicorn running on" "$LOG_FILE"; then
    break
  fi
  sleep 0.25
done

if ! grep -q "Uvicorn running on" "$LOG_FILE"; then
  echo "Python RAG engine did not start" >&2
  cat "$LOG_FILE" >&2
  exit 1
fi

curl --fail --silent --show-error \
  -H "X-Request-Id: $REQUEST_ID" \
  "http://127.0.0.1:$PORT/health" >/dev/null

for _ in {1..40}; do
  if grep -q "$REQUEST_ID" "$LOG_FILE"; then
    echo "Verified Python stderr contains request ID: $REQUEST_ID"
    exit 0
  fi
  sleep 0.25
done

echo "Python stderr did not contain request ID: $REQUEST_ID" >&2
cat "$LOG_FILE" >&2
exit 1

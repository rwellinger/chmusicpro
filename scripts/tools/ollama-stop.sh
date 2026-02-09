#!/usr/bin/env bash
# Stop a running Ollama serve process.
# Usage: ./scripts/tools/ollama-stop.sh

set -euo pipefail

PID=$(pgrep -f "ollama serve" || true)

if [ -z "$PID" ]; then
  echo "Ollama serve is not running."
  exit 0
fi

echo "Stopping Ollama serve (PID $PID) ..."
kill "$PID"
echo "Done."

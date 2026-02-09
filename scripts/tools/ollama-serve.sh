#!/usr/bin/env bash
# Start Ollama serve in the background with project-specific environment variables.
# Based on: ollamasrv/LaunchDeamon/com.ollama.serve.plist
# Stop with: ./scripts/tools/ollama-stop.sh
# Usage: ./scripts/tools/ollama-serve.sh

set -euo pipefail

if pgrep -f "ollama serve" > /dev/null 2>&1; then
  echo "Ollama serve is already running (PID $(pgrep -f 'ollama serve'))."
  exit 0
fi

export OLLAMA_HOST="0.0.0.0:11434"
export OLLAMA_ORIGINS="*"
export OLLAMA_KEEP_ALIVE="3600"
export OLLAMA_MAX_MEMORY="20GiB"
export OLLAMA_DEVICE="metal"

LOG_DIR="$HOME/.ollama/logs"
mkdir -p "$LOG_DIR"

nohup /usr/local/bin/ollama serve \
  > "$LOG_DIR/ollama.log" \
  2> "$LOG_DIR/ollama-error.log" &

echo "Ollama serve started (PID $!)."
echo "  OLLAMA_HOST=$OLLAMA_HOST"
echo "  OLLAMA_KEEP_ALIVE=$OLLAMA_KEEP_ALIVE"
echo "  OLLAMA_MAX_MEMORY=$OLLAMA_MAX_MEMORY"
echo "  OLLAMA_DEVICE=$OLLAMA_DEVICE"
echo "  Logs: $LOG_DIR/ollama.log"

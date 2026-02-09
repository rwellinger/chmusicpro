#!/usr/bin/env bash
# Show running Ollama models and unload them all to free memory.
# Usage: ./scripts/tools/ollama-unload.sh
#
# This does NOT stop the Ollama server - it only unloads models from GPU/RAM.

set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-localhost:11434}"

# Check if Ollama is reachable
if ! curl -sf "http://$OLLAMA_HOST/" > /dev/null 2>&1; then
  echo "Ollama is not running at $OLLAMA_HOST."
  exit 1
fi

# Get list of running models
RUNNING=$(curl -sf "http://$OLLAMA_HOST/api/ps")
MODEL_COUNT=$(echo "$RUNNING" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('models',[])))" 2>/dev/null || echo 0)

if [ "$MODEL_COUNT" -eq 0 ]; then
  echo "No models loaded in memory."
  exit 0
fi

echo "Currently loaded models ($MODEL_COUNT):"
echo "$RUNNING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    name = m.get('name', 'unknown')
    size_gb = m.get('size', 0) / (1024**3)
    vram_gb = m.get('size_vram', 0) / (1024**3)
    print(f'  - {name}  (RAM: {size_gb:.1f} GB, VRAM: {vram_gb:.1f} GB)')
"

echo ""
echo "Unloading all models..."

# Unload each model by setting keep_alive to 0
echo "$RUNNING" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    print(m['name'])
" | while read -r MODEL; do
  curl -sf "http://$OLLAMA_HOST/api/generate" \
    -d "{\"model\": \"$MODEL\", \"keep_alive\": 0}" \
    > /dev/null 2>&1
  echo "  Unloaded: $MODEL"
done

echo ""
echo "Done. All models unloaded, memory freed."

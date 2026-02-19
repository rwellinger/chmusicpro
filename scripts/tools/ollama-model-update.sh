#!/bin/zsh

echo "🔄 Aktualisiere alle vorhandenen Ollama-Modelle..."
echo ""

# Check if ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "❌ Ollama läuft nicht. Bitte starte Ollama zuerst."
    exit 1
fi

# Get list of models (skip header line, extract first column)
models=$(ollama ls | tail -n +2 | awk '{print $1}')

if [ -z "$models" ]; then
    echo "ℹ️  Keine Modelle gefunden."
    exit 0
fi

echo "📋 Gefundene Modelle:"
echo "$models"
echo ""

# Count models
model_count=$(echo "$models" | wc -l | tr -d ' ')
echo "🔢 Insgesamt $model_count Modell(e) werden aktualisiert"
echo ""

# Update each model
current=0
for model in ${(f)models}; do
    current=$((current + 1))
    echo "[$current/$model_count] 📦 Aktualisiere $model..."
    ollama pull "$model"

    if [ $? -eq 0 ]; then
        echo "✅ $model erfolgreich aktualisiert"
    else
        echo "⚠️  Fehler beim Aktualisieren von $model"
    fi
    echo ""
done

echo "🎉 Aktualisierung abgeschlossen!"

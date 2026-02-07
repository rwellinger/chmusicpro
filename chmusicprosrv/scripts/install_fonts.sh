#!/bin/bash
# Install Google Fonts for Text Overlay Feature
# License: All fonts are Open Source (OFL or Apache 2.0)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FONTS_DIR="$PROJECT_ROOT/fonts"

echo "Creating fonts directory..."
mkdir -p "$FONTS_DIR"
cd "$FONTS_DIR"

echo "Downloading Anton-Regular.ttf (Bold - Heavy Display)..."
curl -L -o Anton-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/anton/Anton-Regular.ttf"

echo "Downloading Inter-Regular.ttf (Modern - Clean Sans)..."
curl -L -o Inter-Regular.ttf \
  "https://github.com/shadcn-ui/taxonomy/raw/main/assets/fonts/Inter-Regular.ttf"

echo "Downloading PlayfairDisplay-Regular.ttf (Elegant - Serif)..."
curl -L -o PlayfairDisplay-Regular.ttf \
  "https://raw.githubusercontent.com/technext/cozastore/master/fonts/PlayfairDisplay/PlayfairDisplay-Regular.ttf"

echo "Downloading Roboto-Light.ttf (Light - Thin Sans)..."
curl -L -o Roboto-Light.ttf \
  "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Light.ttf"

echo "Downloading Bangers-Regular.ttf (Comic - Bold)..."
curl -L -o Bangers-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/bangers/Bangers-Regular.ttf"

echo "Downloading ComicNeue-Regular.ttf (Comic - Modern)..."
curl -L -o ComicNeue-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/comicneue/ComicNeue-Regular.ttf"

echo "Downloading BubblegumSans-Regular.ttf (Comic - Playful)..."
curl -L -o BubblegumSans-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/bubblegumsans/BubblegumSans-Regular.ttf"

echo "Downloading Righteous-Regular.ttf (Comic - Retro)..."
curl -L -o Righteous-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/righteous/Righteous-Regular.ttf"

echo "Downloading BebasNeue-Regular.ttf (Display - Condensed)..."
curl -L -o BebasNeue-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf"

echo "Downloading Bungee-Regular.ttf (Display - Urban)..."
curl -L -o Bungee-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/bungee/Bungee-Regular.ttf"

echo "Downloading Montserrat-Regular.ttf (Display - Geometric)..."
curl -L -o Montserrat-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Regular.ttf"

echo "Downloading Oswald-Regular.ttf (Display - Gothic)..."
curl -L -o Oswald-Regular.ttf \
  "https://github.com/google/fonts/raw/main/ofl/oswald/Oswald-Regular.ttf"

echo ""
echo "✅ Fonts installed successfully!"
echo "Location: $FONTS_DIR"
echo ""
ls -lh "$FONTS_DIR"

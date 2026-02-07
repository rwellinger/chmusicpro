#!/bin/zsh

for file in *.mmd; do
    echo "Converting $file..."
    mmdc -i "$file" -o "./images/${file%.mmd}.png" -t neutral -b white
  done

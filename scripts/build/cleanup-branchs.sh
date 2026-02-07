#!/bin/bash

# Alle Remote‑Refs holen und veraltete einbeziehen
git fetch --all --prune

# 2. Lokale Branches, die nicht im Remote existieren, löschen
git for-each-ref --format='%(refname:short)' refs/heads/ |
  while read -r local; do
      if ! git show-ref --quiet "refs/remotes/origin/$local"; then
          echo "lokal löschen: $local"
          git branch -D "$local"
      fi
  done

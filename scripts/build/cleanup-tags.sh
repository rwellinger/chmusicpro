#!/bin/bash

# Lokale Tags löschen, die nicht im Remote existieren
git tag -l | while read -r tag; do
    if ! git ls-remote --tags origin | grep -q "refs/tags/$tag$"; then
        echo "Tag löschen: $tag"
        git tag -d "$tag"
    fi
done

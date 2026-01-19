#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <repo_path> <repo_name>"
    exit 1
fi

# Change to repo root
cd "$(dirname "$0")/.."

REPO_PATH="$1"
REPO_NAME="$2"
INDEX_DIR="./indexes/$REPO_NAME"

python3 indexing/index_repo.py "$REPO_PATH" "$INDEX_DIR"
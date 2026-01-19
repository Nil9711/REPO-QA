#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <index_folder_name> <question>"
    exit 1
fi

# Change to repo root
cd "$(dirname "$0")/.."

INDEX_FOLDER="$1"
QUESTION="$2"
INDEX_DIR="./indexes/$INDEX_FOLDER"

PYTHONWARNINGS="ignore:urllib3 v2 only supports OpenSSL::urllib3" \
python3 prompts/ask.py "$INDEX_DIR" "$QUESTION"
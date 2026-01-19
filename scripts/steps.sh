#!/bin/bash
set -e

# Models (system-level, not venv)
ollama pull deepseek-coder
ollama pull nomic-embed-text

# Quick sanity check (non-interactive)
ollama list
ollama run deepseek-coder "say ok"

# Python env
mkdir -p repo-qna
cd repo-qna

python3 -m venv .venv
source .venv/bin/activate

pip install -U \
  llama-index \
  chromadb \
  llama-index-vector-stores-chroma \
  llama-index-embeddings-ollama \
  llama-index-llms-ollama

# Create the index now: 
# python3 indexing/index_repo.py /Users/nilgolan/Projects/gateway-service ./indexes/gateway-service


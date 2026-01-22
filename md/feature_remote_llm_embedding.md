# Remote LLM and Embedding Support Plan

## Goal
Allow using remote embedding providers (OpenAI, etc.) instead of requiring local Ollama for embeddings.

## Current State
- Embeddings **always** use Ollama (`nomic-embed-text`)
- LLM can be Ollama, OpenAI, or Claude (controlled by `MODE` env var)
- This means even when using OpenAI/Claude for LLM, Ollama is still required for embeddings

## Problem
- Docker image requires 3GB Ollama service + models even when user wants to use only remote APIs
- Limits deployment flexibility (can't run without Ollama)
- Inconsistent: LLM can be remote, but embeddings can't

## Proposed Solution

### Configuration Changes

Add to `.env`:
```env
EMBEDDING_MODE=openai  # or "ollama" (default)
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Add to `server/config.py`:
```python
EMBEDDING_MODE = os.getenv("EMBEDDING_MODE", "ollama")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
```

### Code Changes

Modify `server/prompts/ask.py` and `server/indexing/index_repo.py`:

```python
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding

# Set embedding model based on mode
if EMBEDDING_MODE == "openai":
    Settings.embed_model = OpenAIEmbedding(
        model=OPENAI_EMBEDDING_MODEL,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL  # Optional for compatible APIs
    )
else:
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
```

### Docker Compose Changes

Make Ollama service optional:
- Create `docker-compose.remote.yml` without Ollama service
- Or use profiles to conditionally start Ollama

### Documentation Updates

Update README with:
- Remote-only deployment option (no Ollama needed)
- Cost/performance tradeoffs
- Note about re-indexing when switching embedding models

## Important Notes

1. **Re-indexing Required**: Changing embedding models requires re-indexing all repositories
2. **Compatibility**: Indexes created with one embedding model are incompatible with another
3. **Cost**: OpenAI embeddings cost ~$0.02 per 1M tokens
4. **Performance**: Remote embeddings add latency but remove local infrastructure requirement

## Implementation Steps

1. Add `EMBEDDING_MODE` and `OPENAI_EMBEDDING_MODEL` to config
2. Update `ask.py` to conditionally set embedding model
3. Update `index_repo.py` to conditionally set embedding model
4. Add `llama-index-embeddings-openai` to requirements.txt
5. Create `docker-compose.remote.yml` without Ollama
6. Update README with remote embedding instructions
7. Add migration guide for switching embedding models

## Testing

- Test indexing with OpenAI embeddings
- Test querying with OpenAI embeddings
- Verify error handling when API keys missing
- Test mixed mode (OpenAI embeddings + Ollama LLM and vice versa)

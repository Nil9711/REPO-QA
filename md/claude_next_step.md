# Repo Q&A — Docker Implementation Plan

## Goal

Ship a **self-contained local Repo Q&A system** as **one Docker image**.

```bash
docker run -p 8080:8080 -e OPENAI_API_KEY=xxx repo-qa:latest
```

Open browser → ask questions → get answers + sources.

---

## Current State

The codebase already has:
- Core Q&A logic in [prompts/ask.py](prompts/ask.py) (routing, vector search, LLM calls)
- Question routing with 3 modes in [prompts/router.py](prompts/router.py)
- ChromaDB vector indexing in [indexing/index_repo.py](indexing/index_repo.py)
- Centralized config in [config.py](config.py)
- Discord bot integration (working async pattern)

**Gaps to fill:**
- No HTTP API (currently CLI/Discord only)
- No web UI
- No Dockerfile
- `ask.py` is CLI-based, needs refactoring to callable function

---

## Implementation Steps

### Step 1: Refactor ask.py → Callable Core Function

**File:** Create `app/core.py`

Extract main logic from `prompts/ask.py` into:

```python
async def ask(index_dir: str, question: str) -> dict:
    """
    Returns:
        {
            "answer": str,
            "sources": [{"file": str, "score": float}],
            "mode": str,
            "confidence": float
        }
    """
```

Changes needed:
- Move `build_query_engine()`, `route_question()`, `query_with_mode()` into importable module
- Remove CLI argument parsing
- Return structured dict instead of printing
- Keep history saving as optional side-effect

### Step 2: Create FastAPI Server

**File:** Create `app/server.py`

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

class AskRequest(BaseModel):
    index_dir: str
    question: str

@app.post("/ask")
async def ask_endpoint(req: AskRequest):
    return await ask(req.index_dir, req.question)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/indexes")
def list_indexes():
    # Return available index directories
    pass

# Serve React build
app.mount("/", StaticFiles(directory="web", html=True), name="ui")
```

### Step 3: Create React UI

**Location:** `ui/` (source) → `web/` (build output)

Minimal React app with:
- Index directory dropdown (populated from `/indexes`)
- Question textarea
- Submit button
- Answer display with markdown rendering
- Sources list with file paths

Key file: `ui/src/App.jsx` (use example from next_step.md)

Vite config for dev proxy:
```js
// ui/vite.config.js
export default {
  server: {
    proxy: {
      '/ask': 'http://localhost:8080',
      '/indexes': 'http://localhost:8080'
    }
  }
}
```

### Step 4: Create Dockerfile (Multi-stage)

**File:** `Dockerfile`

```dockerfile
# --- build UI ---
FROM node:20-alpine AS ui
WORKDIR /ui
COPY ui/package*.json ./
RUN npm ci
COPY ui ./
RUN npm run build

# --- runtime ---
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY prompts ./prompts
COPY indexing ./indexing
COPY config.py .
COPY indexes ./indexes
COPY --from=ui /ui/dist ./web

EXPOSE 8080
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 5: Update Configuration for Docker

**File:** Modify `config.py`

Add environment variable support:
```python
import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b-instruct")
# Add OpenAI/Claude support as alternative
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

### Step 6: Add Dependencies

**File:** Update `requirements.txt`

```
# Existing deps...
fastapi
uvicorn[standard]
```

---

## File Structure After Implementation

```
repo-qa/
├── app/
│   ├── __init__.py
│   ├── core.py          # Refactored ask() function
│   └── server.py        # FastAPI app
├── ui/                   # React source (dev only)
│   ├── package.json
│   ├── vite.config.js
│   └── src/App.jsx
├── web/                  # React build output (served in container)
├── prompts/              # Existing Q&A logic
├── indexing/             # Existing indexing logic
├── indexes/              # Pre-built vector indexes
├── config.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

---

## LLM Strategy

**Recommended:** Remote LLM (OpenAI/Claude) via API key env var
- Smaller image
- Better answer quality
- No GPU requirements

**Alternative:** Local Ollama
```bash
docker run -p 8080:8080 \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  repo-qa:latest
```

---

## Verification Plan

1. **Unit test core function:**
   ```bash
   python -c "from app.core import ask; print(ask('./indexes/gateway-service', 'What is this repo?'))"
   ```

2. **Test FastAPI locally:**
   ```bash
   uvicorn app.server:app --reload --port 8080
   curl -X POST http://localhost:8080/ask \
     -H "Content-Type: application/json" \
     -d '{"index_dir": "./indexes/gateway-service", "question": "How does auth work?"}'
   ```

3. **Test Docker build:**
   ```bash
   docker build -t repo-qa:latest .
   docker run -p 8080:8080 -e OPENAI_API_KEY=xxx repo-qa:latest
   ```

4. **End-to-end:** Open http://localhost:8080, ask a question, verify answer + sources appear.

---

## Definition of Done

- [ ] `docker build .` succeeds
- [ ] `docker run -p 8080:8080 ...` starts server
- [ ] Browser at localhost:8080 shows UI
- [ ] Question → answer + sources returned
- [ ] No setup outside Docker required

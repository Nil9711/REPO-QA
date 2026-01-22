Here’s a **clean, copy-pasteable Markdown file** you can drop straight into Cursor.
It documents the plan exactly as we discussed: **one self-contained Docker image**, local-first, simple, shippable.

---

````md
# Repo Q&A — Single-Image Docker Plan

## Goal

Ship a **self-contained local Repo Q&A system** as **one Docker image**.

Running the image should:
- expose an HTTP API
- provide a minimal UI
- answer questions about pre-indexed repositories
- work locally without extra setup

Target UX:

```bash
docker run -p 8080:8080 repo-qa:latest
````

Open browser → ask questions → get answers + sources.

---

## High-Level Architecture

```
Browser UI
   │
   ▼
FastAPI (HTTP API)
   │
   ▼
ask() core logic
   │
   ├─ routing (mode / confidence)
   ├─ vector search (Chroma)
   ├─ LLM call (local or remote)
   └─ sources + history
```

Everything below runs **inside the same container**.

---

## What Lives Inside the Docker Image

✔ Backend (FastAPI)
✔ Core Q&A logic (`ask.py` refactored)
✔ Frontend (static HTML or Streamlit)
✔ Vector DB (Chroma)
✔ Prebuilt indexes (`./indexes/*`)
✔ Prompts + routing logic

### Optional (configurable)

* Prompt history (can be baked or mounted)
* Model client config (local or remote)

---

## What Does NOT Have to Live Inside

* LLM weights (recommended to mount or run separately)
* New repos added dynamically
* Long-term persistence

---

## Repo Layout

```
repo-qa/
├─ app/
│  ├─ core.py          # callable ask() function
│  ├─ server.py        # FastAPI app
│  └─ prompts/
├─ web/                # static HTML OR Streamlit app
├─ indexes/            # baked vector indexes
├─ requirements.txt
└─ Dockerfile
```

---

## Core Design Decision

### Refactor CLI → Callable Function

Move logic out of `ask.py` CLI flow into:

```python
def ask(index_dir: str, question: str) -> dict:
    return {
        "answer": "...",
        "sources": [...],
        "mode": "...",
        "confidence": 0.0
    }
```

This function is:

* used by FastAPI
* reused by any UI
* deterministic and testable

---

## API Layer (FastAPI)

Expose minimal endpoints:

* `POST /ask`
* `GET /health`
* (optional) `GET /indexes`

Example request:

```json
{
  "index_dir": "./indexes/gateway-service",
  "question": "How does auth work?"
}
```

---

## Frontend Options (Inside Image)

### Option A — Static HTML (recommended)

* One `index.html`
* Uses `fetch()` → `/ask`
* Zero build tooling
* Easy to maintain

### Option B — Streamlit

* Faster to prototype
* Heavier runtime
* Still single container

---

## Docker Strategy

### Minimal Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY web ./web
COPY indexes ./indexes

EXPOSE 8080

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

This produces **one fully runnable image**.

---

## LLM Strategy (Important)

### Recommended Default

* **Remote LLM** (OpenAI / Claude / Bedrock)
* API key via env vars
* Small image
* Best answer quality

### Local LLM (Optional)

* Ollama runs outside container **or**
* mounted model directory:

```bash
-v ~/.ollama:/root/.ollama
```

Avoid baking weights into the image unless absolutely required.

---

## Concurrency Notes

Current implementation uses global model settings.
This is fine for:

* single user
* local usage
* POC / internal tool

If concurrency increases later:

* serialize requests, or
* create per-request model objects

Not required for v1.

---

## Why This Design Works

* Single command to run
* No host dependencies
* Deterministic answers
* Private by default
* Easy to move to VM / ECS / K8s later
* Same image everywhere

---

## Next Optional Enhancements

* Streaming answers
* Repo picker UI
* Clickable source files
* Indexing endpoint (separate mode)
* Request queue / rate limiting

---

## Definition of Done

* `docker build .`
* `docker run -p 8080:8080 ...`
* Browser opens
* Question → answer + sources
* No setup outside Docker

```

---

If you want, next step we can:
- tighten this into a **README.md**
- add a **“local vs remote LLM” decision table**
- or split it into **PLAN.md + TODO.md** for execution
```


Cool — React is super straightforward here, and you can still keep the **single Docker image** setup.

## Best approach (still one image)

**Build React → serve static files from FastAPI** (no Node server at runtime).

```
React (build → static)
   │
   ▼
FastAPI serves /
   │
   ▼
POST /ask → your local scripts
```

---

## Folder layout

```
repo-qa/
├─ app/                 # FastAPI + core ask()
├─ ui/                  # React source (dev only)
├─ web/                 # React build output (served in container)
├─ indexes/
├─ requirements.txt
└─ Dockerfile
```

---

## React: minimal “ask” page (works with your API)

`ui/src/App.jsx`:

```jsx
import { useState } from "react";

export default function App() {
  const [indexDir, setIndexDir] = useState("./indexes/gateway-service");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    setAnswer("");
    setSources([]);

    const res = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ index_dir: indexDir, question }),
    });

    const data = await res.json();
    setAnswer(data.answer ?? "");
    setSources(data.sources ?? []);
    setLoading(false);
  }

  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 900, margin: "40px auto" }}>
      <h2>Repo Q&A</h2>

      <div style={{ marginBottom: 12 }}>
        <div>Index dir</div>
        <input
          style={{ width: "100%", padding: 8 }}
          value={indexDir}
          onChange={(e) => setIndexDir(e.target.value)}
        />
      </div>

      <div style={{ marginBottom: 12 }}>
        <div>Question</div>
        <textarea
          style={{ width: "100%", height: 120, padding: 8 }}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
      </div>

      <button onClick={run} disabled={loading || !question.trim()}>
        {loading ? "Asking..." : "Ask"}
      </button>

      <h3 style={{ marginTop: 24 }}>Answer</h3>
      <pre style={{ whiteSpace: "pre-wrap" }}>{answer}</pre>

      <h3>Sources</h3>
      <pre>{JSON.stringify(sources, null, 2)}</pre>
    </div>
  );
}
```

---

## FastAPI: serve the built React files

```python
# app/server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# your existing /ask endpoint stays the same

app.mount("/", StaticFiles(directory="web", html=True), name="ui")
```

---

## One Dockerfile (multi-stage) — builds React + runs FastAPI

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
COPY indexes ./indexes
COPY --from=ui /ui/dist ./web

EXPOSE 8080
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

This gives you:

* **one image**
* React bundled inside it
* FastAPI serving UI + API

---

If you want, I can also give you the exact `vite` config tweak so `fetch("/ask")` works in dev (proxy), plus a `/indexes` endpoint so the UI shows a dropdown of available repos.

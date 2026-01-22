import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prompts.ask import build_query_engine, route_question, query_with_mode, deduplicate_sources

app = FastAPI(title="REPO-QA API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to indexes directory (relative to server/)
INDEXES_DIR = Path(__file__).parent.parent / "indexes"


class AskRequest(BaseModel):
    index: str      # e.g., "gateway-service"
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[dict]
    mode: str
    confidence: float


class IndexInfo(BaseModel):
    name: str
    path: str


@app.get("/indexes", response_model=list[IndexInfo])
def list_indexes():
    """List all available indexed repositories."""
    if not INDEXES_DIR.exists():
        return []

    indexes = []
    for item in INDEXES_DIR.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Check if it has ChromaDB files (chroma.sqlite3)
            if (item / "chroma.sqlite3").exists():
                indexes.append(IndexInfo(name=item.name, path=str(item)))

    return indexes


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Ask a question about a repository."""
    index_path = INDEXES_DIR / request.index

    if not index_path.exists():
        raise HTTPException(status_code=404, detail=f"Index '{request.index}' not found")

    try:
        # Route the question
        mode, confidence = route_question(request.question)

        # Build query engine and get answer
        qe, collection = build_query_engine(str(index_path))
        answer, sources = query_with_mode(qe, collection, request.question, mode)
        sources = deduplicate_sources(sources)

        return AskResponse(
            answer=answer,
            sources=sources,
            mode=mode,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

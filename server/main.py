import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent))

from prompts.ask import build_query_engine, route_question, query_with_mode, deduplicate_sources, save_prompt_history

app = FastAPI(title="REPO-QA API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to indexes directory
# Use environment variable if set, otherwise calculate relative path
INDEXES_DIR = Path(os.getenv("INDEXES_DIR", str(Path(__file__).parent.parent / "indexes")))


def get_index_path(index_name: str) -> Path:
    """Validate index name and return a safe path under INDEXES_DIR."""
    name = (index_name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Index name is required")

    candidate = Path(name)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.name != name:
        raise HTTPException(status_code=400, detail="Invalid index name")

    index_path = (INDEXES_DIR / name).resolve()
    try:
        index_path.relative_to(INDEXES_DIR.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid index path") from exc

    if not index_path.exists():
        raise HTTPException(status_code=404, detail=f"Index '{name}' not found")

    if not (index_path / "chroma.sqlite3").exists():
        raise HTTPException(status_code=404, detail=f"Index '{name}' not found")

    return index_path


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
                indexes.append(IndexInfo(name=item.name))

    return indexes


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Ask a question about a repository."""
    index_path = get_index_path(request.index)

    try:
        # Route the question
        mode, confidence = route_question(request.question)

        # Build query engine and get answer
        qe, collection = build_query_engine(str(index_path))
        answer, sources = query_with_mode(qe, collection, request.question, mode)
        sources = deduplicate_sources(sources)

        save_prompt_history(request.question, answer, sources, str(index_path), mode, confidence)

        return AskResponse(
            answer=answer,
            sources=sources,
            mode=mode,
            confidence=confidence
        )
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        print(f"Error in /ask: {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

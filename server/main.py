import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

# Path to indexes directory (relative to server/)
INDEXES_DIR = Path(__file__).parent.parent / "indexes"

# Path to client build directory
CLIENT_BUILD_DIR = Path(__file__).parent.parent / "client" / "dist"


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


# Mount static files for client (if build exists)
if CLIENT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(CLIENT_BUILD_DIR / "assets")), name="assets")
    
    @app.get("/")
    def serve_spa():
        """Serve the SPA index.html for the root route."""
        return FileResponse(str(CLIENT_BUILD_DIR / "index.html"))
    
    @app.get("/{full_path:path}")
    def serve_spa_catchall(full_path: str):
        """Catch-all route for SPA routing."""
        # If it's an API route, let FastAPI handle it normally
        if full_path.startswith(("api/", "ask", "indexes", "health")):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Check if file exists in build dir
        file_path = CLIENT_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(CLIENT_BUILD_DIR / "index.html"))

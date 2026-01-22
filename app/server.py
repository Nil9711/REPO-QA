"""
FastAPI server for Repo Q&A.
"""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core import ask

app = FastAPI(
    title="Repo Q&A",
    description="Ask questions about indexed code repositories",
    version="1.0.0"
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    index_dir: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list
    mode: str
    confidence: float


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/indexes")
def list_indexes():
    """List available index directories."""
    indexes_dir = Path(__file__).parent.parent / "indexes"

    if not indexes_dir.exists():
        return {"indexes": []}

    indexes = []
    for item in indexes_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            indexes.append({
                "name": item.name,
                "path": f"./indexes/{item.name}"
            })

    return {"indexes": indexes}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest):
    """Answer a question about an indexed repository."""
    index_path = Path(request.index_dir)

    # Resolve relative paths
    if not index_path.is_absolute():
        index_path = Path(__file__).parent.parent / request.index_dir

    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Index directory not found: {request.index_dir}"
        )

    try:
        result = ask(str(index_path), request.question)
        return AskResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


# Serve static files (React build) - must be last to not override API routes
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="ui")

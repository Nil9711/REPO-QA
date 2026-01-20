import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

from config import EXCLUDE_DIRS, INDEXED_FILE_EXTENSIONS, EXCLUDED_FILE_PATTERNS, OLLAMA_BASE_URL, EMBEDDING_MODEL, LLM_MODEL, LLM_TIMEOUT


def detect_language(file_path: Optional[str]) -> str:
    if not file_path:
        return "unknown"

    ext = Path(file_path).suffix.lower()
    return {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".java": "java",
        ".md": "markdown",
        ".json": "json",
        ".yml": "yaml",
        ".yaml": "yaml",
    }.get(ext, "unknown")



def main(repo_path: str, index_dir: str):
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise SystemExit(f"Not a directory: {repo}")

    reader = SimpleDirectoryReader(
        input_dir=str(repo),
        recursive=True,
        exclude_hidden=True,
        required_exts=list(INDEXED_FILE_EXTENSIONS),
    )

    docs = reader.load_data()
    docs = [d for d in docs if not should_skip(Path(d.metadata.get("file_path", "")))]

    if not docs:
        raise SystemExit("No files loaded (check extensions / excludes).")
    os.makedirs(index_dir, exist_ok=True)
    chroma = chromadb.PersistentClient(path=index_dir)
    collection = chroma.get_or_create_collection("repo_chunks")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage = StorageContext.from_defaults(vector_store=vector_store)

    Settings.embed_model = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=LLM_TIMEOUT,
    )

    file_summaries = build_file_summaries(docs)
    splitter = SentenceSplitter(chunk_size=800, chunk_overlap=120)
    nodes = splitter.get_nodes_from_documents(docs)

    for node in nodes:
        meta = node.metadata or {}
        file_path = meta.get("file_path") or meta.get("filename")
        summary = file_summaries.get(file_path)
        language = detect_language(file_path)
        file_ext = Path(file_path).suffix.lower() if file_path else "unknown"
        if file_path:
            meta["file_path"] = file_path
        meta["language"] = language
        meta["file_extension"] = file_ext
        if summary:
            meta["file_summary"] = summary
            header = (
                "[File context]\n"
                f"Path: {file_path or 'unknown'}\n"
                f"Language: {language}\n"
                f"Extension: {file_ext}\n"
            )
            node.text = f"{header}\n[File summary]\n{summary}\n\n{node.text}"
        node.metadata = meta

    VectorStoreIndex(nodes, storage_context=storage)
    storage.persist(persist_dir=index_dir)

    print(f"Indexed {len(docs)} files into {index_dir}")


def should_skip(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True

    filename = path.name.lower()
    return any(filename.endswith(pattern) for pattern in EXCLUDED_FILE_PATTERNS)


def build_file_summaries(docs: list) -> dict:
    llm = Settings.llm
    summaries = {}
    total = len(docs)

    for idx, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        file_path = meta.get("file_path") or meta.get("filename")
        if not file_path or file_path in summaries:
            continue

        text = (doc.text or "").strip()
        if not text:
            summaries[file_path] = "Empty file."
            continue

        print(f"[summaries] ({idx}/{total}) {file_path}")
        snippet = text[:4000]
        prompt = (
            "Create concise retrieval context for this file.\n"
            "Summarize purpose and key behaviors in 3-5 short bullets.\n"
            "Focus on responsibilities, important functions/classes, and inputs/outputs.\n"
            "Keep under 80 words.\n"
            f"File path: {file_path}\n"
            f"Content:\n{snippet}\n"
        )
        try:
            summaries[file_path] = str(llm.complete(prompt)).strip()
        except Exception as exc:
            print(f"[summaries] failed: {file_path} ({exc})")
            summaries[file_path] = "Summary failed."

    return summaries

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python index_repo.py /path/to/repo /path/to/index_dir")
    main(sys.argv[1], sys.argv[2])

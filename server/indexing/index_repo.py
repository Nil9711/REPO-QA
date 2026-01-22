import os
import sys
import json
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter, CodeSplitter
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

    file_summaries = build_file_summaries(docs, index_dir)

    # Map extensions to tree-sitter language names
    ext_to_language = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".java": "java",
    }

    # Group code docs by language
    code_docs_by_lang = {}
    for d in docs:
        ext = Path(d.metadata.get("file_path", "")).suffix.lower()
        if ext in ext_to_language:
            lang = ext_to_language[ext]
            code_docs_by_lang.setdefault(lang, []).append(d)

    markdown_docs = [d for d in docs if Path(d.metadata.get("file_path", "")).suffix.lower() in {".md", ".json"}]

    nodes = []

    # Process each language with its own splitter
    for lang, lang_docs in code_docs_by_lang.items():
        code_splitter = CodeSplitter(
            language=lang,
            chunk_lines=40,
            chunk_lines_overlap=15,
            max_chars=1500,
        )
        nodes.extend(code_splitter.get_nodes_from_documents(lang_docs))

    if markdown_docs:
        md_splitter = SentenceSplitter(chunk_size=800, chunk_overlap=120)
        nodes.extend(md_splitter.get_nodes_from_documents(markdown_docs))

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


def load_summary_cache(index_dir: str) -> dict:
    cache_file = Path(index_dir) / "file_summaries_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_summary_cache(index_dir: str, cache: dict):
    cache_file = Path(index_dir) / "file_summaries_cache.json"
    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)


def build_file_summaries(docs: list, index_dir: str) -> dict:
    llm = Settings.llm

    # Load existing cache
    cache = load_summary_cache(index_dir)

    summaries = {}
    total = len(docs)
    cached_count = 0
    generated_count = 0

    for idx, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        file_path = meta.get("file_path") or meta.get("filename")
        if not file_path or file_path in summaries:
            continue

        text = (doc.text or "").strip()
        if not text:
            summaries[file_path] = "Empty file."
            continue

        # Check if we have a valid cached summary
        cached_entry = cache.get(file_path)
        if cached_entry:
            try:
                file_mtime = os.path.getmtime(file_path)
                if cached_entry.get("mtime") == file_mtime and cached_entry.get("summary"):
                    summaries[file_path] = cached_entry["summary"]
                    cached_count += 1
                    print(f"[summaries] ({idx}/{total}) {file_path} [cached]")
                    continue
            except Exception:
                pass  # File might not exist or mtime check failed, regenerate

        # Generate new summary
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
            summary = str(llm.complete(prompt)).strip()
            summaries[file_path] = summary
            generated_count += 1

            # Update cache
            try:
                file_mtime = os.path.getmtime(file_path)
                cache[file_path] = {
                    "summary": summary,
                    "mtime": file_mtime
                }
            except Exception:
                cache[file_path] = {"summary": summary, "mtime": None}

        except Exception as exc:
            print(f"[summaries] failed: {file_path} ({exc})")
            summaries[file_path] = "Summary failed."

    # Save updated cache
    save_summary_cache(index_dir, cache)

    print(f"\n[summaries] Total: {total} files | Cached: {cached_count} | Generated: {generated_count}")

    return summaries

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python index_repo.py /path/to/repo /path/to/index_dir")
    main(sys.argv[1], sys.argv[2])

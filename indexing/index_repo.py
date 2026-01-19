import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import chromadb
from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding

from config import EXCLUDE_DIRS, INDEXED_FILE_EXTENSIONS, OLLAMA_BASE_URL, EMBEDDING_MODEL


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


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

    VectorStoreIndex.from_documents(docs, storage_context=storage)
    storage.persist(persist_dir=index_dir)

    print(f"Indexed {len(docs)} files into {index_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python index_repo.py /path/to/repo /path/to/index_dir")
    main(sys.argv[1], sys.argv[2])

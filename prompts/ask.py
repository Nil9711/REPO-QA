import json
import sys
from datetime import datetime
from pathlib import Path

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import OLLAMA_BASE_URL, EMBEDDING_MODEL, LLM_MODEL, LLM_TIMEOUT, SIMILARITY_TOP_K
from prompts.filters import ExcludeDeploymentFilesPostprocessor


def build_query_engine(index_dir: str):
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )

    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=LLM_TIMEOUT,
    )

    chroma_client = chromadb.PersistentClient(path=index_dir)
    collection = chroma_client.get_or_create_collection("repo_chunks")

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        storage_context=storage_context,
    )

    return index.as_query_engine(
        similarity_top_k=SIMILARITY_TOP_K,
        node_postprocessors=[ExcludeDeploymentFilesPostprocessor()],
    )


def save_prompt_history(question: str, answer: str, sources: list, index_dir: str):
    """Save prompt and response to timestamped JSON file."""
    history_dir = Path(__file__).parent.parent / "prompts_history"
    history_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{timestamp}.json"
    
    data = {
        "timestamp": datetime.now().isoformat(),
        "index_dir": index_dir,
        "question": question,
        "answer": answer,
        "sources": sources
    }
    
    filepath = history_dir / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n[Saved to {filepath}]")


def main(index_dir: str, question: str):
    qe = build_query_engine(index_dir)
    response = qe.query(question)
    
    answer = str(response)
    sources = []

    print("\nANSWER:\n")
    print(answer)

    print("\nSOURCES:\n")
    if getattr(response, "source_nodes", None):
        for i, node in enumerate(response.source_nodes, start=1):
            meta = node.node.metadata or {}
            file_path = meta.get("file_path") or meta.get("filename") or "unknown"
            score = getattr(node, "score", None)
            
            sources.append({
                "file_path": file_path,
                "score": score
            })
            
            print(f"{i}. {file_path}" + (f" (score={score:.3f})" if score is not None else ""))
    else:
        print("No sources returned.")
    
    save_prompt_history(question, answer, sources, index_dir)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit('Usage: python prompts/ask.py ./indexes/gateway-service "your question here"')

    index_dir = sys.argv[1]
    question = " ".join(sys.argv[2:])
    main(index_dir, question)

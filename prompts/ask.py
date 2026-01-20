import json
import sys
from datetime import datetime
from pathlib import Path

import chromadb
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    OLLAMA_BASE_URL,
    EMBEDDING_MODEL,
    LLM_MODEL,
    LLM_TIMEOUT,
    SIMILARITY_TOP_K,
    ROUTER_CONFIDENCE_THRESHOLD,
)
from prompts.filters import ExcludeDeploymentFilesPostprocessor
from prompts.router import QuestionRouter
from prompts.authoritative_sources import get_authoritative_context
from prompts.prompt_templates import get_prompt_template


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

    query_engine = index.as_query_engine(
        similarity_top_k=SIMILARITY_TOP_K,
        node_postprocessors=[ExcludeDeploymentFilesPostprocessor()],
    )

    return query_engine, collection


def route_question(question: str) -> tuple[str, float]:
    router = QuestionRouter()
    intent_type, confidence = router.classify_question(question)

    if intent_type in ["repo_overview", "api_endpoints"] and confidence >= ROUTER_CONFIDENCE_THRESHOLD:
        mode = intent_type
    else:
        mode = "deep_dive"

    return mode, confidence


def query_with_mode(query_engine, collection, question: str, mode: str) -> tuple[str, list]:
    authoritative_context, authoritative_sources = get_authoritative_context(mode, collection)

    if mode == "deep_dive":
        response = query_engine.query(question)
        return str(response), extract_sources(response)

    if mode == "repo_overview":
        retrieved_context = ""
        response = None
    else:
        response = query_engine.query(question)
        max_chunks = 2 if mode == "repo_overview" else None
        retrieved_context = format_retrieved_context(response, max_chunks=max_chunks)

    prompt_template = get_prompt_template(mode)

    if mode == "deep_dive":
        final_prompt = prompt_template.format(
            retrieved_context=retrieved_context,
            question=question
        )
    else:
        final_prompt = prompt_template.format(
            authoritative_context=authoritative_context,
            retrieved_context=retrieved_context,
            question=question
        )

    llm = Settings.llm
    final_response = llm.complete(final_prompt)

    # Combine authoritative sources with retrieved sources
    retrieved_sources = extract_sources(response) if response else []
    sources = authoritative_sources + retrieved_sources
    return str(final_response), sources


def format_retrieved_context(response, max_chunks=None) -> str:
    if not getattr(response, "source_nodes", None):
        return "[No retrieved context]"

    source_nodes = response.source_nodes
    if max_chunks is not None:
        source_nodes = source_nodes[:max_chunks]

    context_parts = []
    for i, node in enumerate(source_nodes, start=1):
        meta = node.node.metadata or {}
        file_path = meta.get("file_path") or meta.get("filename") or "unknown"
        content = node.node.get_content()
        score = getattr(node, "score", None)

        score_str = f" (score={score:.3f})" if score is not None else ""
        context_parts.append(f"[Source {i}: {file_path}{score_str}]\n{content}\n")

    return "\n".join(context_parts)


def extract_sources(response) -> list:
    sources = []
    if getattr(response, "source_nodes", None):
        for node in response.source_nodes:
            meta = node.node.metadata or {}
            file_path = meta.get("file_path") or meta.get("filename") or "unknown"
            score = getattr(node, "score", None)

            sources.append({
                "file_path": file_path,
                "score": score
            })
    return sources


def save_prompt_history(question: str, answer: str, sources: list, index_dir: str, mode: str = None, confidence: float = None):
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

    if mode is not None:
        data["mode"] = mode
    if confidence is not None:
        data["confidence"] = confidence

    filepath = history_dir / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n[Saved to {filepath}]")


def main(index_dir: str, question: str):
    mode, confidence = route_question(question)

    qe, collection = build_query_engine(index_dir)

    answer, sources = query_with_mode(qe, collection, question, mode)

    print("\nANSWER:\n")
    print(answer)

    print("\nSOURCES:\n")
    if sources:
        for i, source in enumerate(sources, start=1):
            file_path = source["file_path"]
            score = source.get("score")
            print(f"{i}. {file_path}" + (f" (score={score:.3f})" if score is not None else ""))
    else:
        print("No sources returned.")

    save_prompt_history(question, answer, sources, index_dir, mode, confidence)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit('Usage: python prompts/ask.py ./indexes/gateway-service "your question here"')

    index_dir = sys.argv[1]
    question = " ".join(sys.argv[2:])
    main(index_dir, question)

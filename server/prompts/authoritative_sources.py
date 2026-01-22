import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def get_authoritative_chunks_from_index(collection, file_path_pattern: str) -> dict:
    try:
        # Get all chunks and filter in Python (ChromaDB's get() doesn't support $contains)
        all_results = collection.get()

        filtered_docs = []
        filtered_metas = []
        filtered_ids = []

        for i, metadata in enumerate(all_results.get('metadatas', [])):
            file_path = metadata.get('file_path', '')
            if file_path_pattern in file_path:
                filtered_docs.append(all_results['documents'][i])
                filtered_metas.append(metadata)
                filtered_ids.append(all_results['ids'][i])

        return {
            'documents': filtered_docs,
            'metadatas': filtered_metas,
            'ids': filtered_ids
        }
    except Exception:
        return {"documents": [], "metadatas": [], "ids": []}


def get_authoritative_context(mode: str, collection) -> tuple[str, list]:
    """Returns (context_string, sources_list)"""
    if mode == "repo_overview":
        chunks = get_authoritative_chunks_from_index(collection, "DOCUMENTATION.md")
        if chunks and chunks.get('documents'):
            content = "\n\n---\n\n".join(chunks['documents'])
            sources = [{"file_path": meta.get("file_path", "DOCUMENTATION.md"), "score": 10}
                      for meta in chunks.get('metadatas', [])]
            # Deduplicate sources by file_path
            seen = set()
            unique_sources = []
            for src in sources:
                if src["file_path"] not in seen:
                    seen.add(src["file_path"])
                    unique_sources.append(src)
            return f"# Repository Documentation\n\n{content}", unique_sources
        return "", []

    elif mode == "api_endpoints":
        chunks = get_authoritative_chunks_from_index(collection, "swagger-json.json")
        if chunks and chunks.get('documents'):
            content = "\n\n".join(chunks['documents'])
            sources = [{"file_path": meta.get("file_path", "swagger-json.json"), "score": None}
                      for meta in chunks.get('metadatas', [])]
            # Deduplicate sources by file_path
            seen = set()
            unique_sources = []
            for src in sources:
                if src["file_path"] not in seen:
                    seen.add(src["file_path"])
                    unique_sources.append(src)
            return f"# API Specification\n\n{content}", unique_sources
        return "", []

    else:
        return "", []

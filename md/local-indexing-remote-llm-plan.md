# Plan: Local Indexing + Remote LLM Answering

## Goal

Keep the existing local RAG pipeline (indexing + retrieval),
but replace the local answering model with a stronger remote LLM
(ChatGPT or Claude).

This improves answer quality without rebuilding the index.

---

## Current State (Baseline)

- Embeddings: Local (nomic-embed-text via Ollama)
- Vector DB: Chroma (persistent, local)
- Retrieval: Similarity search over indexed repo chunks
- Answering: Local LLM via Ollama (inside LlamaIndex query engine)

Pipeline today:

question
  -> embed (local)
  -> vector search (Chroma)
  -> local LLM (Ollama)
  -> answer + sources

---

## Target State

Keep everything up to retrieval.
Replace only the answering step with a remote LLM (ChatGPT or Claude).

New pipeline:

question
  -> embed (local)
  -> vector search (Chroma)
  -> format retrieved chunks as context
  -> remote LLM (ChatGPT or Claude)
  -> answer (with citations)

---

## What Stays the Same

- Chroma index (no re-embedding required)
- Chunking strategy
- Metadata (file_path, symbols, etc.)
- Similarity search logic
- CLI / UX around querying

---

## What Changes

### 1. Stop using query_engine.query()

Instead of letting LlamaIndex synthesize the answer:
- Use index.as_retriever()
- Manually retrieve nodes

### 2. Explicitly format retrieved chunks

Each retrieved chunk is sent to the LLM with a clear source header:

SOURCE 1  
FILE: path/to/file.py  
---  
<chunk content>

This allows the model to reference exact files reliably.

### 3. Call a remote LLM for answering

- ChatGPT (OpenAI API) or Claude (Anthropic API)
- Strict prompt rules:
  - Answer only from provided sources
  - Cite sources using file paths
  - If information is missing, say what file or function is needed

---

## Citations Strategy

Citations are explicit and deterministic.

- Sources are injected into the prompt with IDs and file paths
- The model is instructed to cite like:
  (SOURCE 2, FILE: services/auth.py)
- The CLI can also print its own SOURCES section based on retrieved metadata

---

## Why This Is Useful

- Immediate answer-quality improvement
- No index rebuild
- No change to retrieval logic
- Easy fallback to local answering if needed

---

## Summary

This approach replaces only one component: answer synthesis.
All indexing and retrieval work stays unchanged.

Low risk, high upside.

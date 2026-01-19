# REPO-QA

A smart Q&A system for code repositories using LlamaIndex and Ollama. Automatically routes questions to specialized answering modes and prioritizes authoritative documentation.

## Features

- **Smart Question Routing**: Automatically classifies questions into three modes:
  - `repo_overview` - High-level questions about what the repository does
  - `api_endpoints` - Questions about API routes and endpoints
  - `deep_dive` - Specific technical questions about implementation details

- **Authoritative Sources**: Prioritizes `DOCUMENTATION.md` and `swagger-json.json` files over code embeddings for more accurate answers

- **Vector Search**: Uses ChromaDB for efficient semantic search across your codebase

## Prerequisites

- Python 3.9+
- [Ollama](https://ollama.ai) running locally
- Ollama models pulled: `nomic-embed-text` and `qwen2.5:14b-instruct` (or configure different models in [config.py](config.py))

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd REPO-QA

# Install dependencies
pip install -r requirements.txt

# Verify Ollama is running
curl http://localhost:11434
```

## Usage

### 1. Index a Repository

```bash
sh scripts/execute_index.sh /path/to/repo repo-name
```

This creates an index in `./indexes/repo-name/` containing vector embeddings of all code files.

### 2. Ask Questions

```bash
sh scripts/execute_ask.sh repo-name "What does this repository do?"
```

The system will:
1. Route your question to the appropriate mode
2. Retrieve relevant context from the index
3. Generate an answer using the configured LLM
4. Save the Q&A to `prompts_history/`

## Configuration

Edit [config.py](config.py) to customize:

- `OLLAMA_BASE_URL` - Ollama server URL (default: `http://localhost:11434`)
- `EMBEDDING_MODEL` - Model for embeddings (default: `nomic-embed-text`)
- `LLM_MODEL` - Model for answer generation (default: `qwen2.5:14b-instruct`)
- `SIMILARITY_TOP_K` - Number of chunks to retrieve (default: 12)
- `INDEXED_FILE_EXTENSIONS` - File types to index
- `EXCLUDE_DIRS` - Directories to skip during indexing

## How It Works

### Question Routing

The router ([prompts/router.py](prompts/router.py)) uses an LLM to classify questions with confidence scoring. Questions are routed based on intent and confidence threshold.

### Authoritative Sources

For `repo_overview` mode:
- If `md/DOCUMENTATION.md` exists in the indexed repo, it becomes the **primary source**
- Vector search is skipped entirely to prevent code snippets from contaminating the answer
- The LLM answers based solely on the documentation

For `api_endpoints` mode:
- Prioritizes `md/swagger/swagger-json.json` if available
- Falls back to code analysis for endpoint discovery

### Vector Search

Uses ChromaDB to:
1. Chunk code files into manageable pieces
2. Generate embeddings using Ollama
3. Perform semantic similarity search
4. Filter out deployment files (Dockerfiles, k8s configs, etc.)

## Project Structure

```
REPO-QA/
├── config.py                    # Configuration settings
├── requirements.txt             # Python dependencies
├── indexing/
│   └── index_repo.py           # Repository indexing logic
├── prompts/
│   ├── ask.py                  # Main Q&A entry point
│   ├── router.py               # Question classification
│   ├── authoritative_sources.py # DOCUMENTATION.md/Swagger loading
│   ├── prompt_templates.py     # Mode-specific prompts
│   └── filters.py              # Post-processors for search results
├── scripts/
│   ├── execute_index.sh        # Index a repository
│   └── execute_ask.sh          # Ask a question
└── indexes/                     # Generated vector indexes (gitignored)
```

## Examples

```bash
# Index your repository
sh scripts/execute_index.sh ~/Projects/my-api my-api

# Ask overview questions
sh scripts/execute_ask.sh my-api "What is this service responsible for?"

# Ask about API endpoints
sh scripts/execute_ask.sh my-api "What endpoints does this expose?"

# Ask specific technical questions
sh scripts/execute_ask.sh my-api "How does the authentication middleware work?"
```

## Tips

- Add a `md/DOCUMENTATION.md` file to your repositories for best results on overview questions
- Add `md/swagger/swagger-json.json` for accurate API endpoint documentation
- Re-run indexing after significant code changes
- Check `prompts_history/` to review past Q&A sessions

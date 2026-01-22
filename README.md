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

### For Docker (Recommended)
- Docker and Docker Compose

### For Local Development
- Python 3.9+
- Node.js 20+
- [Ollama](https://ollama.ai) running locally
- Ollama models pulled: `nomic-embed-text` and `qwen2.5:14b-instruct` (or configure different models in [server/config.py](server/config.py))

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd REPO-QA

# Create .env file (see Configuration section)
cp .env.example .env

# Build and run with docker-compose
docker-compose up -d

# Access the app at http://localhost:8000
```

### Option 2: Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd REPO-QA

# Install backend dependencies
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies
cd ../client
npm install

# Verify Ollama is running
curl http://localhost:11434
```

## Usage

### Docker Usage

```bash
# Start the service
docker-compose up -d

# First time: pull Ollama models (takes a few minutes)
docker-compose exec ollama ollama pull nomic-embed-text
docker-compose exec ollama ollama pull qwen2.5:14b-instruct

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Access the web UI at http://localhost:8000
```

### CLI Usage (Local Development)

#### 1. Index a Repository

```bash
sh scripts/execute_index.sh /path/to/repo repo-name
```

This creates an index in `./indexes/repo-name/` containing vector embeddings of all code files.

#### 2. Ask Questions

```bash
sh scripts/execute_ask.sh repo-name "What does this repository do?"
```

The system will:
1. Route your question to the appropriate mode
2. Retrieve relevant context from the index
3. Generate an answer using the configured LLM
4. Save the Q&A to `prompts_history/`

## Configuration

Create a `.env` file in the root directory:

### LLM Provider (MODE)

The system supports three LLM providers via the `MODE` environment variable:

| MODE | Provider | Required Env Vars |
|------|----------|-------------------|
| `ollama` (default) | Local Ollama | `OLLAMA_BASE_URL`, `LLM_MODEL` |
| `openai` | OpenAI API | `OPENAI_API_KEY`, `OPENAI_MODEL` |
| `claude` | Anthropic Claude | `CLAUDE_API_KEY`, `CLAUDE_MODEL` |

**Note:** Embeddings always use Ollama regardless of MODE.

Example `.env` for OpenAI:
```env
MODE=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Example `.env` for Claude:
```env
MODE=claude
CLAUDE_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20240620
```

### Other Settings

Edit [server/config.py](server/config.py) or set via environment:

- `OLLAMA_BASE_URL` - Ollama server URL (default: `http://localhost:11434`)
- `EMBEDDING_MODEL` - Model for embeddings (default: `nomic-embed-text`)
- `LLM_MODEL` - Ollama model for answer generation (default: `qwen2.5:14b-instruct`)
- `LLM_TIMEOUT` - Request timeout in seconds (default: `120`)
- `SIMILARITY_TOP_K` - Number of chunks to retrieve (default: 12)
- `INDEXED_FILE_EXTENSIONS` - File types to index
- `EXCLUDE_DIRS` - Directories to skip during indexing

### Docker Notes

When running with Docker:
- Ollama runs as a separate service using the official `ollama/ollama` image
- The `indexes/` directory is mounted as a volume for persistence
- Ollama models are stored in a Docker volume (`ollama_models`) for persistence
- Pull models once after first run (see commands above)
- The web UI and API are served on port 8000
- Ollama API is accessible on port 11434

## How It Works

### Question Routing

The router ([server/prompts/router.py](server/prompts/router.py)) uses an LLM to classify questions with confidence scoring. Questions are routed based on intent and confidence threshold.

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
├── server/                      # Backend (source of truth)
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI entry point
│   ├── indexing/
│   │   └── index_repo.py       # Repository indexing logic
│   ├── prompts/
│   │   ├── ask.py              # Main Q&A entry point
│   │   ├── router.py           # Question classification
│   │   ├── authoritative_sources.py
│   │   ├── prompt_templates.py
│   │   └── filters.py
│   └── listeners/              # Discord bot (optional)
│       └── discord_listener.py
├── client/                      # React + Vite frontend
│   └── src/
├── scripts/
│   ├── execute_index.sh        # CLI: Index a repository
│   └── execute_ask.sh          # CLI: Ask a question
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

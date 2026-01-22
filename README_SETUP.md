# REPO-QA Setup Guide

## Project Structure

```
REPO-QA/
├── client/          # React + Vite + shadcn + Tailwind frontend
├── server/          # FastAPI backend
├── indexes/         # ChromaDB vector indexes (shared)
└── listeners/       # Discord bot (optional)
```

## Backend Setup

1. Navigate to server directory:
```bash
cd server
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the server:
```bash
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000

### API Endpoints

- `GET /indexes` - List all indexed repositories
- `POST /ask` - Ask a question about a repository
  ```json
  {
    "index": "gateway-service",
    "question": "What does this repo do?"
  }
  ```
- `GET /health` - Health check

## Frontend Setup

1. Navigate to client directory:
```bash
cd client
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at http://localhost:5173

## Usage

1. Start the backend server (see Backend Setup)
2. Start the frontend dev server (see Frontend Setup)
3. Open http://localhost:5173 in your browser
4. Select a repository from the dropdown
5. Type your question and click "Ask" (or press Cmd+Enter)
6. View the answer and source files

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

### Ollama

Make sure Ollama is running locally with the required models:
- Embedding model: `nomic-embed-text`
- LLM model: `qwen2.5:14b-instruct`

## Adding New Repositories to Index

To index a new repository, you can use the existing indexing script:

```bash
cd server
source venv/bin/activate
python -m indexing.index_repo /path/to/repo ./indexes/repo-name
```

This will create a new index in `indexes/repo-name/` which will automatically appear in the frontend dropdown.

## Discord Bot (Optional)

The Discord listener in `listeners/` can still be used independently:

```bash
# Set environment variables
export DISCORD_BOT_TOKEN=your-token
export INDEX_DIR=./indexes/gateway-service

# Run the bot
PYTHONPATH=./server python listeners/discord_listener.py
```

## Troubleshooting

### Backend Issues

- Make sure Ollama is running: `curl http://localhost:11434`
- Check that indexes exist: `ls indexes/`
- Verify Python dependencies are installed

### Frontend Issues

- Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check that backend is running: `curl http://localhost:8000/health`
- Verify CORS is enabled (already configured for localhost:5173)

### CSS/Tailwind Issues

The project uses Tailwind CSS v3 syntax. The IDE warnings about `@tailwind` are normal and won't affect functionality.

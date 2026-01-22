Claude’s Plan
REPO-QA Restructuring Plan
Goal
Restructure the project into two folders:

client/ - React + Vite + shadcn + Tailwind frontend
server/ - FastAPI backend wrapping existing Python code
Target Folder Structure

REPO-QA/
├── client/                          # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # shadcn components
│   │   │   ├── IndexSelector.tsx    # Dropdown for repo selection
│   │   │   ├── QuestionInput.tsx    # Question textarea + submit
│   │   │   └── AnswerDisplay.tsx    # Answer + sources display
│   │   ├── lib/
│   │   │   └── api.ts               # API client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── components.json
│   └── tsconfig.json
│
├── server/                          # FastAPI backend
│   ├── main.py                      # FastAPI app (3 endpoints)
│   ├── config.py                    # Moved from root
│   ├── requirements.txt             # Extended with fastapi/uvicorn
│   ├── prompts/                     # Moved from root
│   │   ├── ask.py
│   │   ├── router.py
│   │   ├── filters.py
│   │   ├── prompt_templates.py
│   │   └── authoritative_sources.py
│   └── indexing/                    # Moved from root
│       └── index_repo.py
│
├── indexes/                         # Stays at root (shared data)
│   ├── gateway-service/
│   └── bots-client-api/
│
├── listeners/                       # Stays at root (optional discord bot)
└── .env
Implementation Steps
Phase 1: Create Server Structure
Create server/ directory

Move Python files:

config.py → server/config.py
prompts/ → server/prompts/
indexing/ → server/indexing/
Fix imports in moved files:

Remove sys.path.insert() hacks
Change from config import to relative imports
Create server/requirements.txt:


# Existing deps
llama-index-core>=0.10.0,<0.12.0
llama-index-utils-workflow
llama-index-readers-file
chromadb
llama-index-vector-stores-chroma
llama-index-embeddings-ollama
llama-index-llms-ollama
tree-sitter>=0.21.0,<0.22.0
tree-sitter-languages>=1.10.0
python-dotenv

# New deps
fastapi
uvicorn[standard]
Create server/main.py with endpoints:

GET /indexes - List available indexed repos
POST /ask - Ask question, return answer + sources
GET /health - Health check
Phase 2: Create React Client
Scaffold Vite + React + TypeScript:


npm create vite@latest client -- --template react-ts
Install Tailwind:


cd client && npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
Install and configure shadcn:


npx shadcn@latest init
npx shadcn@latest add button select textarea card
Create components:

IndexSelector.tsx - shadcn Select dropdown
QuestionInput.tsx - Textarea + Button
AnswerDisplay.tsx - Card displaying answer + sources
Create src/lib/api.ts - fetch wrapper for /indexes and /ask

Wire up App.tsx:

Load indexes on mount
Dropdown to select repo
Input for question
Display answer and sources
Phase 3: Update Listeners (Optional)
Update listeners/discord_listener.py imports to point to server/prompts/ask.py
API Design
GET /indexes

Response: [
  { "name": "gateway-service", "path": "./indexes/gateway-service" },
  { "name": "bots-client-api", "path": "./indexes/bots-client-api" }
]
POST /ask

Request: {
  "index": "gateway-service",
  "question": "How does authentication work?"
}

Response: {
  "answer": "...",
  "sources": [
    { "file_path": "src/auth/auth.service.ts", "score": 0.85 }
  ],
  "mode": "deep_dive",
  "confidence": 0.92
}
Critical Files to Modify
File	Change
prompts/ask.py	Move to server/, fix imports
config.py	Move to server/
prompts/router.py	Move to server/, fix imports
prompts/filters.py	Move to server/, fix imports
prompts/prompt_templates.py	Move to server/
prompts/authoritative_sources.py	Move to server/, fix imports
indexing/index_repo.py	Move to server/, fix imports
requirements.txt	Move to server/, add fastapi/uvicorn
Verification
Start backend:


cd server && uvicorn main:app --reload --port 8000
Test API:


curl http://localhost:8000/indexes
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"index":"gateway-service","question":"What does this repo do?"}'
Start frontend:


cd client && npm run dev
Test UI:

Open http://localhost:5173
Select repo from dropdown
Ask a question
Verify answer and sources display
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from repo root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# LLM Mode: "ollama" (default), "openai", or "claude"
MODE = os.getenv("MODE", "ollama").lower()

# Ollama settings (used for embeddings always, LLM when MODE=ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b-instruct")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))

# OpenAI settings (used when MODE=openai)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # Optional, for compatible APIs

# Claude/Anthropic settings (used when MODE=claude)
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

# Query settings
SIMILARITY_TOP_K = 12

EXCLUDE_DIRS = {".git", "node_modules", "dist", "build", ".next", ".venv", "__pycache__"}
INDEXED_FILE_EXTENSIONS = {".ts", ".tsx", ".md", ".json"}
EXCLUDED_FILE_PATTERNS = [".module.ts", ".enum.ts", ".enum.js", ".dto.ts", ".dto.js"]

DEPLOYMENT_FILE_PATTERNS = [
    'dockerfile',
    'docker-compose',
    '.dockerignore',
    'deployment.yaml',
    'deployment.yml',
    'service.yaml',
    'service.yml',
    'configmap.yaml',
    'configmap.yml',
    'ingress.yaml',
    'ingress.yml',
    'statefulset.yaml',
    'statefulset.yml',
    'daemonset.yaml',
    'daemonset.yml',
    '.k8s/',
    '/k8s/',
    'k8sdeploy/',
    '/k8sdeploy/',
    'k8sdeployments/',
    'k8sservices/',
    'k8sconfigmaps/',
    'k8singresses/',
    'k8sstatefulsets/',
    'k8sdaemonsets/',
    'k8sjobs/',
    'k8scronjobs/',
    'k8spods/',
    'k8snodes/',
    'k8snamespaces/',
    'helm',
    '/charts/',
    'chart.yaml',
    'chart.yml',
    'values.yaml',
    'values.yml',
    'templates/',
]

ROUTER_CONFIDENCE_THRESHOLD = 0.7
ROUTER_MODEL = LLM_MODEL

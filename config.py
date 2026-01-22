import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:14b-instruct")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120.0"))

SIMILARITY_TOP_K = int(os.getenv("SIMILARITY_TOP_K", "12"))

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

ROUTER_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTER_CONFIDENCE_THRESHOLD", "0.7"))
ROUTER_MODEL = LLM_MODEL

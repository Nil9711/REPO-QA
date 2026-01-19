# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "deepseek-coder"
LLM_TIMEOUT = 120.0

# Query settings
SIMILARITY_TOP_K = 12

# Indexing settings
EXCLUDE_DIRS = {".git", "node_modules", "dist", "build", ".next", ".venv", "__pycache__"}
INDEXED_FILE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".md", ".json", ".yml", ".yaml"}

# Deployment/config file patterns to exclude from queries
# Note: All patterns checked against lowercase paths
DEPLOYMENT_FILE_PATTERNS = [
    # Docker
    'dockerfile',
    'docker-compose',
    '.dockerignore',
    
    # K8s YAML files
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
    
    # K8s directories
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
    
    # Helm
    'helm',
    '/charts/',
    'chart.yaml',
    'chart.yml',
    'values.yaml',
    'values.yml',
    'templates/',
]

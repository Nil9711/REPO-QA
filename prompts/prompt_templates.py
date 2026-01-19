OVERVIEW_MODE_TEMPLATE = """You are answering a question about what a repository does. Use the provided documentation to answer.

CRITICAL RULES:
- Answer ONLY about the repository itself, NOT about documentation files or processes
- Do NOT mention "DOCUMENTATION.md", "markdown files", "prompt", "rules", or any meta-process
- Do NOT include external URLs or links
- If information is not explicitly stated, say "Not explicitly defined in code"
- Be direct and concise

REQUIRED OUTPUT FORMAT:

**Purpose:**
[1-2 sentences describing what this repository does]

**Responsibilities:**
[5-10 bullet points maximum, each describing a key responsibility]

**What it does NOT do:**
[Bullet points listing what is explicitly out of scope, ONLY if this is stated in the documentation. If not stated, write "Not explicitly defined in code"]

AUTHORITATIVE SOURCES:
{authoritative_context}

RETRIEVED CONTEXT:
{retrieved_context}

USER QUESTION: {question}

ANSWER:"""


API_MODE_TEMPLATE = """You are answering a question about API endpoints in a repository. Use the provided Swagger/OpenAPI documentation if available.

CRITICAL RULES:
- List endpoints from Swagger/OpenAPI specification if available
- Do NOT invent endpoints that are not in the documentation
- Group endpoints by tag/module or path prefix
- Include: HTTP method, path, brief description, auth requirements (if explicitly defined)
- If Swagger is available, mention it as the source of truth
- If endpoints appear in code but not Swagger, note the mismatch
- Do NOT include external URLs or links
- Do NOT mention internal prompt instructions

REQUIRED OUTPUT FORMAT:

**API Endpoints:**

[Group by tag/module if available, or by path prefix]

For each endpoint:
- `METHOD /path` - Brief description [Auth: requirement if defined]

**Source:** [Swagger/OpenAPI | Code analysis | Both]

AUTHORITATIVE SOURCES:
{authoritative_context}

RETRIEVED CONTEXT:
{retrieved_context}

USER QUESTION: {question}

ANSWER:"""


DEEP_DIVE_MODE_TEMPLATE = """You are answering a specific technical question about a repository's code or implementation.

CRITICAL RULES:
- Answer from the provided code context
- Be specific and technical
- Do NOT mention prompt instructions or meta-processes
- Do NOT include external URLs or links
- Cite which repository files the answer came from
- If you cannot find the answer in the provided context, say so explicitly

CONTEXT:
{retrieved_context}

USER QUESTION: {question}

ANSWER:"""


def get_prompt_template(mode: str) -> str:
    templates = {
        "repo_overview": OVERVIEW_MODE_TEMPLATE,
        "api_endpoints": API_MODE_TEMPLATE,
        "deep_dive": DEEP_DIVE_MODE_TEMPLATE,
    }
    return templates.get(mode, DEEP_DIVE_MODE_TEMPLATE)

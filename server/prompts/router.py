import json
import sys
from pathlib import Path
from typing import Literal

from llama_index.llms.ollama import Ollama

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MODE,
    OLLAMA_BASE_URL,
    ROUTER_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OPENAI_BASE_URL,
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
)


QuestionIntent = Literal["repo_overview", "api_endpoints", "deep_dive", "generic"]


class QuestionRouter:

    ROUTER_PROMPT = """You are a question classifier for a repository Q&A system.
Classify the user's question into ONE of these intents:

1. "generic" - Greetings, small talk, or questions NOT related to any codebase
   Examples:
   - "Hello", "Hi", "Hey"
   - "How are you?"
   - "What's up?"
   - "Who are you?"
   - "Thanks", "Bye"
   - "What is the weather?"
   - Any question not about code or a repository

2. "repo_overview" - Questions about what the repository does, its purpose, responsibilities, or what it's in charge of
   Examples:
   - "What does this repository do?"
   - "What is this repo in charge of?"
   - "Give me an overview of this service"
   - "What are the responsibilities of this system?"
   - "What is the purpose of this codebase?"

3. "api_endpoints" - Questions about API routes, endpoints, request/response schemas
   Examples:
   - "What endpoints does this service expose?"
   - "List all API routes"
   - "What are the available REST endpoints?"
   - "Show me the API documentation"

4. "deep_dive" - Specific questions about modules, functions, bugs, implementation details
   Examples:
   - "How does the authentication module work?"
   - "Where is the login function defined?"
   - "What causes error X?"
   - "How do I configure feature Y?"

Respond with ONLY valid JSON in this exact format:
{{
  "type": "generic" | "repo_overview" | "api_endpoints" | "deep_dive",
  "confidence": 0.0-1.0
}}

Question: {question}

JSON Response:"""

    def __init__(self):
        """Initialize router with LLM based on MODE setting."""
        if MODE == "openai":
            if not OPENAI_API_KEY:
                raise ValueError("MODE=openai but OPENAI_API_KEY is not set")
            from llama_index.llms.openai import OpenAI
            kwargs = {
                "model": OPENAI_MODEL,
                "api_key": OPENAI_API_KEY,
                "timeout": 30.0,
            }
            if OPENAI_BASE_URL:
                kwargs["api_base"] = OPENAI_BASE_URL
            self.llm = OpenAI(**kwargs)

        elif MODE == "claude":
            if not CLAUDE_API_KEY:
                raise ValueError("MODE=claude but CLAUDE_API_KEY is not set")
            from llama_index.llms.anthropic import Anthropic
            self.llm = Anthropic(
                model=CLAUDE_MODEL,
                api_key=CLAUDE_API_KEY,
                timeout=30.0,
            )

        else:  # MODE == "ollama" or default
            self.llm = Ollama(
                model=ROUTER_MODEL,
                base_url=OLLAMA_BASE_URL,
                request_timeout=30.0,
            )

    def classify_question(self, question: str) -> tuple[QuestionIntent, float]:
        prompt = self.ROUTER_PROMPT.format(question=question)

        try:
            response = self.llm.complete(prompt)
            response_text = str(response).strip()

            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx == -1 or end_idx == -1:
                return "deep_dive", 0.5

            json_str = response_text[start_idx:end_idx + 1]
            result = json.loads(json_str)

            intent_type = result.get("type", "deep_dive")
            confidence = float(result.get("confidence", 0.5))

            if intent_type not in ["generic", "repo_overview", "api_endpoints", "deep_dive"]:
                intent_type = "deep_dive"

            confidence = max(0.0, min(1.0, confidence))

            return intent_type, confidence

        except Exception:
            return "deep_dive", 0.5

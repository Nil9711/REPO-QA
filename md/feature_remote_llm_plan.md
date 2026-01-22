Remote LLM Plan
Goal
Switch ask.py to use a remote LLM provider (OpenAI or Claude) selected by MODE in .env.

Scope
- Update LLM initialization in server/prompts/ask.py to support OpenAI/Claude via MODE
- Keep embeddings on the current Ollama model
- Add env loading and config wiring for MODE, API keys, and model names

Proposed .env
MODE=openai|claude
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini (example)
OPENAI_BASE_URL=optional
CLAUDE_API_KEY=...
CLAUDE_MODEL=claude-3-5-sonnet-20240620 (example)
LLM_TIMEOUT=120

Dependencies
- Add provider packages to server/requirements.txt:
  - llama-index-llms-openai
  - llama-index-llms-anthropic

Implementation Steps
1. Add env loading in server/config.py (python-dotenv) and read MODE + provider vars via os.getenv with sane defaults.
2. Update server/prompts/ask.py build_query_engine to set Settings.llm based on MODE with a simple if/else block.
3. Update README_SETUP.md to document new env vars and example MODE values.
4. Add a small validation path (raise clear error if MODE unknown or API key missing).

Open Questions
- Keep embeddings on Ollama or move to provider embeddings? (default: keep Ollama)
- Should MODE also affect embeddings and router model?

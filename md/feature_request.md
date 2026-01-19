# Feature Request: Add Question Routing + Authoritative Source Pinning to Repo Q&A

## Background / Problem

The current Q&A flow uses vector retrieval (RAG) and then asks the LLM to answer from the retrieved chunks. Even when `md/DOCUMENTATION.md` is high-quality, the LLM can still produce poor answers for broad questions like:

* “What does this repository do?”
* “What is this repo in charge of?”
* “Give me an overview of this service”

Observed failure modes:

1. **Wrong target**: The model explains the documentation file or prompt rules instead of summarizing the repository.
2. **Over-cautious replies**: To avoid hallucinations, the model produces vague statements (“this file documents…”) rather than a repo summary.
3. **Prompt leakage**: The answer references internal instructions or meta content (e.g., “core rules specified…”).
4. **Unstable behavior**: Similar broad questions phrased differently produce inconsistent results.

Root cause:

* The system lacks explicit control layers to detect “repo overview” intent, enforce an overview answer format, and pin authoritative sources (like `md/DOCUMENTATION.md` and Swagger) into the context.

## Goal

Improve answer quality and consistency for broad, high-level questions by:

* Detecting question intent (overview vs deep-dive vs endpoints).
* Forcing a summary-style response for overview questions.
* Pinning authoritative sources into the context for relevant intents.
* Preventing prompt leakage and irrelevant external links.

## Non-Goals

* Reworking embeddings, chunking, or the entire indexing pipeline.
* Implementing multi-index retrieval (out of scope for this request).
* Changing the content of `md/DOCUMENTATION.md` or repo code.

---

## Proposed Solution

### 1) Add a Question Router (Intent Classification)

Implement a routing step in `ask.py` before retrieval that classifies each question into one of these intents:

* `repo_overview`: high-level purpose/responsibilities/what it does/what it doesn’t do
* `api_endpoints`: questions asking about routes, endpoints, request/response schemas
* `deep_dive`: anything specific (modules, functions, bugs, “how does X work”, etc.)

Routing must handle paraphrases (e.g., “in charge of” == “does”).

Implementation options:

* Preferred: a small LLM-based router returning strict JSON.
* Alternative: embedding similarity router using a small set of semantic anchors.

Router output:

* `type`: one of `repo_overview | api_endpoints | deep_dive`
* `confidence`: float 0.0–1.0

Routing rule:

* If `type == repo_overview` and `confidence >= 0.7`, use Overview Mode.
* If `type == api_endpoints` and `confidence >= 0.7`, use API Mode.
* Otherwise fallback to existing RAG behavior (Deep Dive Mode).

### 2) Add Authoritative Source Pinning

When in special modes, inject authoritative sources directly into the LLM context (not via similarity search):

#### Overview Mode

* Always include `md/DOCUMENTATION.md` (or a scoped excerpt like Purpose + Responsibilities + What it does NOT do if present).
* Use this pinned context as the primary truth source.

#### API Mode

* If `/md/swagger/swagger-json.json` exists, include it as authoritative for endpoints.
* If Swagger is missing, fall back to controllers/routes discovered via retrieval, but must state limitations.

Do not rely on vector retrieval alone to surface `DOCUMENTATION.md`/Swagger.

### 3) Enforce Mode-Specific Answer Contracts (Prompt Templates)

Add explicit prompt templates per mode:

#### Overview Mode Output Format (mandatory)

* Purpose: 1–2 sentences
* Responsibilities: 5–10 bullets max
* What it does NOT do: bullets (only if explicitly stated)
  Constraints:
* Do not mention “documentation file”, “prompt”, “rules”, “markdown”, or any meta-process.
* No external links.
* If something is not explicitly stated: “Not explicitly defined in code”.

#### API Mode Output Format (mandatory)

* List endpoints grouped by tag/module (if available) or path prefix
* For each endpoint: method + path + short description + auth requirements if explicitly defined
* Mention source of truth: Swagger (if available)
  Constraints:
* Do not invent endpoints not in Swagger.
* If endpoints appear in code but not Swagger, state mismatch.

#### Deep Dive Mode

* Keep current behavior, but add a guardrail:

  * Avoid meta commentary about prompts.
  * No external links.
  * Must cite which repo files the answer came from (if your system supports source output).

### 4) Guardrails (Global)

Regardless of mode:

* Never include external URLs (e.g., Wikipedia).
* Never describe internal prompt instructions or the fact the system is generating docs.
* Prefer direct, repository-focused explanations.

---

## Acceptance Criteria

1. For “What does this repository do?” and paraphrases like “What is this repo in charge of?”:

   * Answer is a concise repository overview (Purpose + Responsibilities).
   * Does not talk about `DOCUMENTATION.md` as an artifact.
   * No external links, no prompt leakage.

2. Overview answers remain consistent across paraphrases and small variations in phrasing.

3. When Swagger exists and user asks for endpoints:

   * Endpoints are derived from Swagger, not invented.
   * Output is structured and skimmable.

4. Existing deep-dive questions still work:

   * Questions about modules/files/errors behave as before.

5. Implementation is localized primarily to `ask.py` (routing + prompt selection + pinned context injection).

   * `filters.py` can remain unchanged unless needed for light filtering.

---

## Notes / Implementation Hints (Optional)

* Router can be implemented as:

  * A short LLM call with strict JSON output.
  * Or embedding similarity against a fixed set of intent anchors.
* Pinned context can be:

  * Full file content (if small enough), or
  * A truncated excerpt (top sections) to keep within context limits.
* Consider a CLI flag to print detected intent and confidence for debugging (e.g., `--debug-router`).

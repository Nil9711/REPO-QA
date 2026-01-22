# Repo Cleanup Plan

## Goals
- Remove dead/duplicated code and unused folders/files.
- Make `server/` and `client/` the single sources of truth.
- Keep only necessary runtime data out of the repo and update docs accordingly.

## Phase 1: Inventory (short, deliberate)
1) Identify entry points and usage:
   - Backend: `server/main.py`
   - Frontend: `client/src/main.tsx`
   - CLI/scripts: `scripts/execute_index.sh`, `scripts/execute_ask.sh`
2) Trace imports from entry points:
   - `server/main.py` imports `server/prompts/*`
   - `scripts/*` call `prompts/*` and `indexing/*` from repo root
3) Confirm whether optional components are still needed:
   - `listeners/` (Discord bot)
   - `indexes/` (runtime data)
   - `prompts_history/` (runtime data)

## Phase 2: Decide Source of Truth (reduce duplication)
Choose one backend layout and remove the other:
- Preferred: **keep `server/` as backend source of truth**
  - Consolidate all backend code under `server/`
  - Update scripts to use `server/` modules (or remove scripts if unused)

Duplicates to resolve:
- `indexing/` (root) vs `server/indexing/`
- `prompts/` (root) vs `server/prompts/`
- `config.py` (root) vs `server/config.py`
- `requirements.txt` (root) vs `server/requirements.txt`

## Phase 3: Remove Dead/Unused Files
1) If `server/` is the source of truth:
   - Delete `indexing/`, `prompts/`, `config.py`, `requirements.txt` at repo root
   - Update any scripts referencing root paths
2) If scripts are still needed:
   - Change `scripts/execute_index.sh` to call `server/indexing/index_repo.py`
   - Change `scripts/execute_ask.sh` to call `server/prompts/ask.py`
3) If `listeners/` is not used:
   - Remove `listeners/` or move it under `server/` with clear docs

## Phase 4: Git Hygiene (reduce noise)
1) Add ignore rules:
   - `server/venv/`
   - `client/node_modules/`
   - `client/dist/`
2) Remove committed runtime artifacts:
   - `server/venv/` (if present)
   - `client/node_modules/` (if present)
   - `indexes/*` and `prompts_history/*` (if checked in by mistake)

## Phase 5: Documentation Alignment
1) Update `README.md` and `README_SETUP.md` to reflect the new structure:
   - Point all backend usage to `server/`
   - Clarify how indexing is run (CLI or API)
2) Make sure examples match the actual entry points.

## Phase 6: Verify
1) Backend:
   - `cd server && uvicorn main:app --reload --port 8000`
2) Frontend:
   - `cd client && npm install && npm run dev`
3) Optional:
   - Run indexing via the chosen path and verify `/indexes` API and UI dropdown.

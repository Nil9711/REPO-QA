Single Docker Image Plan
Goal
Ship the app as a single Docker image with both FastAPI backend and built frontend, plus a docker-compose file for local use.

Scope
- Multi-stage Dockerfile: build client, install server deps, run FastAPI
- Serve client build from FastAPI (StaticFiles) or a lightweight ASGI static mount
- docker-compose for local run with volumes for indexes and .env

Implementation Steps
1. Add a FastAPI static mount in server/main.py to serve `client/dist` (or copied build dir), and set a default route to index.html for SPA.
2. Create a multi-stage Dockerfile at repo root:
   - Stage 1: build client (node) -> /app/client/dist
   - Stage 2: install python deps, copy server code + built client
   - Expose port 8000 and run uvicorn
3. Create docker-compose.yml:
   - Build from Dockerfile
   - Mount ./indexes to /app/indexes (persistent data)
   - Load .env for MODE/provider keys
   - Publish 8000:8000
4. Add .dockerignore to keep venv, node_modules, indexes, and build artifacts out of image build context.
5. Update README_SETUP.md with docker run instructions.

Testing/Verification
- `docker build -t repo-qa .`
- `docker run --env-file .env -p 8000:8000 -v $(pwd)/indexes:/app/indexes repo-qa`
- Visit http://localhost:8000 to load UI; call /health and /ask

Open Questions
- Should indexes be baked into the image or mounted via volume? (default: volume)
- Desired image size vs. convenience (multi-stage keeps runtime small)


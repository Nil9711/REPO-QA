# --- Build UI ---
FROM node:20-alpine AS ui
WORKDIR /ui
COPY ui/package*.json ./
RUN npm ci
COPY ui ./
RUN npm run build

# --- Runtime ---
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY prompts ./prompts
COPY indexing ./indexing
COPY config.py .

# Copy pre-built indexes (if any exist)
COPY indexes ./indexes

# Copy React build output
COPY --from=ui /ui/dist ./web

EXPOSE 8080

CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]

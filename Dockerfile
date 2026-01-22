# Stage 1: Build the client
FROM node:20-alpine AS client-builder

WORKDIR /app/client

# Copy package files
COPY client/package*.json ./

# Install dependencies
RUN npm ci

# Copy client source
COPY client/ ./

# Build the client
RUN npm run build

# Stage 2: Python runtime with FastAPI
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy server requirements
COPY server/requirements.txt ./server/

# Install Python dependencies
RUN pip install --no-cache-dir -r server/requirements.txt

# Copy server code
COPY server/ ./server/

# Copy built client from stage 1
COPY --from=client-builder /app/client/dist ./client/dist

# Create indexes directory
RUN mkdir -p /app/indexes

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]

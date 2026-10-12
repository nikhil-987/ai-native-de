# Multi-stage Dockerfile for AI Data Engineering Studio
# Stage 1: Build Frontend UI
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies (curl, azure-cli prerequisites, nodejs for Claude CLI if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Azure CLI
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy Backend source
COPY backend/ ./backend/

# Copy built frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["python", "backend/server.py"]

# Stage 1: Build frontend
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy package.json only (lock file excluded via .dockerignore for clean platform install)
COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


# Stage 2: Python app
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Create data directory
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/letterboxd.db

EXPOSE 8000

# Run the API server with scheduler
CMD ["python", "-m", "src.main"]

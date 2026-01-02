FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/letterboxd.db

EXPOSE 8000

# Run the API server with scheduler
CMD ["python", "-m", "src.main"]

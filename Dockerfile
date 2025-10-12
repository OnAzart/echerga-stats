FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY requirements.txt pyproject.toml* ./

# Install Python dependencies using uv
RUN uv pip install --system -r requirements.txt

# Copy application files
COPY extract-snapshot.sh ingest.py ./

# Make scripts executable
RUN chmod +x extract-snapshot.sh ingest.py

# Set entrypoint using bash explicitly
ENTRYPOINT ["/bin/bash", "/app/extract-snapshot.sh"]
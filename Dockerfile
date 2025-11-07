# Dockerfile for StillMe - Learning AI system with RAG foundation
FROM python:3.12-slim

LABEL maintainer="StillMe Team"
LABEL description="StillMe - Learning AI system with RAG foundation with Complete Ethical Transparency"

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for chromadb
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install build tools first
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Install torch CPU version first (Python 3.12 compatible) to reduce build time
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Create model cache directory (persistent in image)
RUN mkdir -p /app/.model_cache

# Set environment variables for model cache (used during build and runtime)
ENV SENTENCE_TRANSFORMERS_HOME=/app/.model_cache
ENV TRANSFORMERS_CACHE=/app/.model_cache
ENV HF_HOME=/app/.model_cache

# Pre-download embedding model during build stage
# This ensures model is available in image and doesn't need to be downloaded at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/.model_cache')"

# Copy application code (including .streamlit config)
COPY . .

# Create data directory
RUN mkdir -p data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "start_backend.py"]


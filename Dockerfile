# Dockerfile for StillMe - Learning AI system with RAG foundation
# Using Python 3.11 for compatibility with onnxruntime and ChromaDB 1.3.4
# Python 3.12 doesn't have onnxruntime wheels on Linux yet
FROM python:3.11-slim

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
# Install torch CPU version first (Python 3.11 compatible) to reduce build time
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Create model cache directory (persistent in image)
RUN mkdir -p /app/.model_cache

# Set HOME to /app so ChromaDB uses /app/.cache instead of /root/.cache
# This ensures ChromaDB ONNX models are cached in the image
ENV HOME=/app

# Set environment variables for model cache (used during build and runtime)
ENV SENTENCE_TRANSFORMERS_HOME=/app/.model_cache
ENV TRANSFORMERS_CACHE=/app/.model_cache
ENV HF_HOME=/app/.model_cache

# Pre-download embedding model during build stage
# CRITICAL: This ensures model is available in image and can be copied to persistent volume at runtime
# Using separate script to avoid heredoc syntax issues and make it more maintainable
# Copy model warmup script first
COPY scripts/model_warmup.py /app/scripts/model_warmup.py

# Pre-download model (this step never fails the build - || true ensures it continues even on error)
# Enable warmup by default to prevent runtime downloads
ARG MODEL_WARMUP=true
RUN if [ "$MODEL_WARMUP" = "true" ]; then \
      echo "Pre-downloading embedding model multi-qa-MiniLM-L6-dot-v1 (this may take 2-3 minutes)..."; \
      python /app/scripts/model_warmup.py || true; \
      echo "Model warmup completed"; \
    else \
      echo "Model warmup disabled (MODEL_WARMUP=false)"; \
    fi

# Copy warmup scripts (for chroma_warmup.py and model_warmup.py)
# This allows us to use the warmup scripts before copying all application code
# Note: model_warmup.py was already copied above, only copy chroma_warmup.py here
COPY scripts/chroma_warmup.py /app/scripts/chroma_warmup.py

# Pre-download ChromaDB ONNX model during build stage
# ChromaDB automatically downloads ONNX models to ~/.cache/chroma/onnx_models/
# By setting HOME=/app, it will use /app/.cache/chroma/onnx_models/
# This prevents re-downloading ONNX models (79.3MB) on every container start
# CRITICAL: ONNX model download takes ~2-3 minutes, causing API timeouts
# Pre-downloading in Docker image ensures it's available immediately at runtime
# Note: Model will be cached in Railway persistent volume at /app/.cache/chroma (if mounted)
# Using separate script to avoid heredoc syntax issues and make it more maintainable
# This step never fails the build (|| true ensures it continues even on error)
# Enable warmup by default to prevent runtime downloads
ARG CHROMA_WARMUP=true
RUN if [ "$CHROMA_WARMUP" = "true" ]; then \
      echo "Pre-downloading ChromaDB ONNX model (this may take 2-3 minutes)..."; \
      python /app/scripts/chroma_warmup.py || true; \
      echo "ChromaDB ONNX warmup completed"; \
    else \
      echo "ChromaDB warmup disabled (CHROMA_WARMUP=false)"; \
    fi

# Copy application code (including .streamlit config)
COPY . .

# Create data directory
RUN mkdir -p data

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8000 8501

# Health check - Increased start-period to allow RAG initialization (can take 30-60s)
# Health endpoint is available immediately, but we give extra time for full initialization
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Default command (can be overridden)
CMD ["python", "start_backend.py"]


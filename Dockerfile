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

# Set HOME to /app so ChromaDB uses /app/.cache instead of /root/.cache
# This ensures ChromaDB ONNX models are cached in the image
ENV HOME=/app

# Set environment variables for model cache (used during build and runtime)
ENV SENTENCE_TRANSFORMERS_HOME=/app/.model_cache
ENV TRANSFORMERS_CACHE=/app/.model_cache
ENV HF_HOME=/app/.model_cache

# Pre-download embedding model during build stage
# This ensures model is available in image and doesn't need to be downloaded at runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/app/.model_cache')"

# Pre-download ChromaDB ONNX model during build stage (optional, controlled by CHROMA_WARMUP env)
# ChromaDB automatically downloads ONNX models to ~/.cache/chroma/onnx_models/
# By setting HOME=/app, it will use /app/.cache/chroma/onnx_models/
# This prevents re-downloading ONNX models on every container start
# Note: ChromaDB may only download ONNX model when actually needed (during real queries)
# If model is not pre-downloaded here, it will download on first use but then be cached
# Using heredoc to avoid shell quoting issues and SyntaxError
# This step never fails the build (|| true ensures it continues even on error)
ARG CHROMA_WARMUP=true
RUN if [ "$CHROMA_WARMUP" = "true" ]; then \
    python - <<'PY' || true; \
import chromadb; \
import os; \
try: \
    os.makedirs('/app/.cache/chroma', exist_ok=True); \
    client = chromadb.Client(); \
    collection = client.create_collection('_preload_onnx'); \
    collection.add(ids=['d'], documents=['d'], embeddings=[[0.1]*384]); \
    try: \
        results = collection.query(query_embeddings=[[0.1]*384], n_results=1); \
        print('ChromaDB query executed - ONNX model may be cached'); \
    except Exception as e: \
        print(f'Query executed (ONNX may download on first real use): {e}'); \
    client.delete_collection('_preload_onnx'); \
    print('ChromaDB ONNX warmup done'); \
except Exception as e: \
    print('Chroma warmup skipped:', e); \
PY \
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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "start_backend.py"]


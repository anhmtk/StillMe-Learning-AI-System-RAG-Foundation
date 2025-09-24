# AgentDev Dockerfile for testing
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional testing dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-html \
    pytest-xdist \
    flake8 \
    mypy \
    mutmut \
    hypothesis \
    aiohttp \
    aiosqlite

# Copy application code
COPY agentdev/ ./agentdev/
COPY tests/ ./tests/
COPY pytest.ini .
COPY Makefile .

# Create necessary directories
RUN mkdir -p /app/.agentdev /app/logs /app/reports

# Set environment variables
ENV PYTHONPATH=/app
ENV ENV=test
ENV OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENV REDIS_URL=redis://redis:6379

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import agentdev; print('✅ AgentDev is healthy')" || exit 1

# Default command
CMD ["python", "-m", "pytest", "-q", "-m", "not seal and not slow"]

#!/bin/bash
# quick-start.sh - One-click setup script for StillMe

set -e

echo "🧠 StillMe - Self-Evolving AI System"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file. Please edit it with your API keys!"
    else
        echo "❌ env.example not found. Creating basic .env..."
        cat > .env << EOF
# API Keys
DEEPSEEK_API_KEY=sk-REPLACE_ME
OPENAI_API_KEY=sk-REPLACE_ME

# Learning Configuration
LEARNING_INTERVAL_HOURS=4
AUTO_APPROVAL_THRESHOLD=0.8
COMMUNITY_MIN=0.6
COMMUNITY_MAX=0.8
EOF
        echo "✅ Created basic .env file. Please add your API keys!"
    fi
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys before continuing!"
    read -p "Press Enter after editing .env file..."
fi

# Create data directory if it doesn't exist
mkdir -p data

echo "🚀 Starting StillMe with Docker Compose..."
echo ""

# Start services
docker-compose up -d

echo ""
echo "✅ StillMe is starting up!"
echo ""
echo "📊 Dashboard: http://localhost:8501"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🔍 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend is still starting... Please wait a moment."
fi

echo ""
echo "🎉 StillMe is ready!"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""


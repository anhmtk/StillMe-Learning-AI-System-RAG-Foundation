# StillMe Makefile
# Provides convenient targets for development, testing, and deployment

.PHONY: help lint test unit integration chaos coverage security dast build docker push deploy-staging deploy-prod rollback clean

# Default target
help:
	@echo "StillMe Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  lint          - Run code linting (flake8, black, isort, mypy)"
	@echo "  test          - Run all tests (unit + integration + chaos)"
	@echo "  unit          - Run unit tests only"
	@echo "  integration   - Run integration tests only"
	@echo "  chaos         - Run chaos tests only"
	@echo "  coverage      - Run tests with coverage report"
	@echo "  security      - Run security scans (SAST, dependency audit)"
	@echo "  dast          - Run DAST security tests"
	@echo "  build         - Build Docker image"
	@echo "  docker        - Build and run Docker container locally"
	@echo "  push          - Push Docker image to registry"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod   - Deploy to production environment"
	@echo "  rollback      - Rollback to previous version"
	@echo "  clean         - Clean up temporary files and containers"
	@echo ""
	@echo "Examples:"
	@echo "  make test                    # Run all tests"
	@echo "  make security               # Run security scans"
	@echo "  make build                  # Build Docker image"
	@echo "  make deploy-staging         # Deploy to staging"
	@echo "  make rollback TAG=v1.2.3    # Rollback to specific tag"

# Code quality and linting
lint:
	@echo "🔍 Running code linting..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@black --check --diff .
	@isort --check-only --diff .
	@mypy --ignore-missing-imports agent_dev/ stillme_core/
	@echo "✅ Linting completed"

# Test targets
test: unit integration chaos
	@echo "✅ All tests completed"

unit:
	@echo "🧪 Running unit tests..."
	@pytest agentdev_foundation_tests/unit/ -v --junitxml=junit-unit.xml
	@echo "✅ Unit tests completed"

integration:
	@echo "🔗 Running integration tests..."
	@pytest agentdev_foundation_tests/integration/ -v --junitxml=junit-integration.xml
	@echo "✅ Integration tests completed"

chaos:
	@echo "🌪️ Running chaos tests..."
	@pytest agentdev_foundation_tests/chaos/ -v --junitxml=junit-chaos.xml
	@echo "✅ Chaos tests completed"

coverage:
	@echo "📊 Running tests with coverage..."
	@pytest agentdev_foundation_tests/ -v --cov=agent_dev --cov=stillme_core --cov-report=xml --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated: htmlcov/index.html"

# Security targets
security:
	@echo "🔒 Running security scans..."
	@bandit -r agent_dev/ stillme_core/ -f json -o bandit-report.json
	@bandit -r agent_dev/ stillme_core/ -f txt
	@semgrep --config=auto --json --output=semgrep-report.json agent_dev/ stillme_core/
	@semgrep --config=auto agent_dev/ stillme_core/
	@pip-audit --format=json --output=pip-audit-report.json
	@pip-audit --format=text
	@echo "✅ Security scans completed"

dast:
	@echo "🎯 Running DAST security tests..."
	@python tests/security/test_fuzz_http.py
	@echo "✅ DAST tests completed"

# Docker targets
build:
	@echo "🐳 Building Docker image..."
	@docker build -t stillme:latest .
	@docker build -t stillme:$(shell git rev-parse --short HEAD) .
	@echo "✅ Docker image built: stillme:latest"

docker: build
	@echo "🐳 Running Docker container..."
	@docker run -d --name stillme-dev -p 8080:8080 stillme:latest
	@echo "✅ Docker container running on http://localhost:8080"

push:
	@echo "📤 Pushing Docker image to registry..."
	@docker tag stillme:latest ghcr.io/$(shell git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git/\1/')/stillme:latest
	@docker push ghcr.io/$(shell git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\/[^/]*\)\.git/\1/')/stillme:latest
	@echo "✅ Docker image pushed to registry"

# Deployment targets
deploy-staging:
	@echo "🚀 Deploying to staging environment..."
	@docker-compose -f docker-compose.staging.yml up -d --build
	@echo "⏳ Waiting for staging deployment to be ready..."
	@sleep 30
	@curl -f http://localhost:8080/healthz || (echo "❌ Staging health check failed" && exit 1)
	@curl -f http://localhost:8080/readyz || (echo "❌ Staging readiness check failed" && exit 1)
	@echo "✅ Staging deployment completed and verified"

deploy-prod:
	@echo "🚀 Deploying to production environment..."
	@echo "⚠️  WARNING: This will deploy to production!"
	@read -p "Are you sure you want to continue? (y/N): " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose -f docker-compose.prod.yml up -d --build; \
		echo "⏳ Waiting for production deployment to be ready..."; \
		sleep 30; \
		curl -f http://localhost:8080/healthz || (echo "❌ Production health check failed" && exit 1); \
		curl -f http://localhost:8080/readyz || (echo "❌ Production readiness check failed" && exit 1); \
		echo "✅ Production deployment completed and verified"; \
	else \
		echo "❌ Production deployment cancelled"; \
	fi

rollback:
	@echo "🔄 Rolling back deployment..."
	@if [ -z "$(TAG)" ]; then \
		echo "❌ TAG parameter is required. Usage: make rollback TAG=v1.2.3"; \
		exit 1; \
	fi
	@./scripts/rollback.sh --tag $(TAG)
	@echo "✅ Rollback completed"

# Health check targets
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8080/healthz && echo "✅ Health check passed" || echo "❌ Health check failed"
	@curl -f http://localhost:8080/readyz && echo "✅ Readiness check passed" || echo "❌ Readiness check failed"

# Load testing
load-test:
	@echo "📊 Running load tests..."
	@if command -v k6 >/dev/null 2>&1; then \
		./scripts/run_k6_smoke.sh; \
	else \
		echo "❌ K6 is not installed. Please install K6 first."; \
		echo "   Visit: https://k6.io/docs/getting-started/installation/"; \
		exit 1; \
	fi

# Cleanup targets
clean:
	@echo "🧹 Cleaning up temporary files and containers..."
	@docker stop stillme-dev 2>/dev/null || true
	@docker rm stillme-dev 2>/dev/null || true
	@docker system prune -f
	@rm -f *.json *.xml
	@rm -rf htmlcov/
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Development targets
dev:
	@echo "🔧 Starting development environment..."
	@python -m pip install --upgrade pip
	@pip install -r requirements-test.txt
	@echo "✅ Development environment ready"

install:
	@echo "📦 Installing dependencies..."
	@python -m pip install --upgrade pip
	@pip install -r requirements-test.txt
	@echo "✅ Dependencies installed"

# Documentation targets
docs:
	@echo "📚 Generating documentation..."
	@python -c "from agent_dev.core.documentation_generator import DocumentationGenerator; doc_gen = DocumentationGenerator('.'); doc_gen.generate_documentation_report()"
	@echo "✅ Documentation generated"

# Monitoring targets
monitor:
	@echo "📊 Starting monitoring stack..."
	@docker-compose -f docker-compose.staging.yml up -d prometheus grafana
	@echo "✅ Monitoring stack started"
	@echo "📊 Prometheus: http://localhost:9090"
	@echo "📊 Grafana: http://localhost:3000 (admin/admin)"

# Quick development workflow
quick: lint unit
	@echo "✅ Quick development check completed"

# Full CI/CD pipeline simulation
ci: lint test security
	@echo "✅ CI pipeline simulation completed"

# Production readiness check
prod-ready: lint test security dast build
	@echo "✅ Production readiness check completed"
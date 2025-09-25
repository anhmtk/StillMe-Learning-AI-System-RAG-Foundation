# StillMe AgentDev - SEAL-GRADE CI/CD Makefile
# Comprehensive testing and deployment commands

.PHONY: help install test test-quick test-full test-seal clean lint format security-scan load_phase3

# Default target
help:
	@echo "StillMe AgentDev - SEAL-GRADE CI/CD Commands"
	@echo "=============================================="
	@echo ""
	@echo "Quick Commands:"
	@echo "  make install          - Install dependencies"
	@echo "  make test-quick       - Run quick tests (Tier 1)"
	@echo "  make test-full        - Run full test suite"
	@echo "  make test-seal        - Run SEAL-GRADE tests"
	@echo "  make lint             - Run linting"
	@echo "  make format           - Format code"
	@echo "  make security-scan    - Run security scans"
	@echo "  make load_phase3      - Run Phase 3 load tests"
	@echo "  make clean            - Clean artifacts"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  make ci-tier1         - Run Tier 1 CI locally"
	@echo "  make ci-tier2         - Run Tier 2 CI locally"
	@echo "  make ci-policy        - Check policy compliance"
	@echo "  make ci-secrets       - Check for secrets"
	@echo "  make ci-protected     - Check protected files"
	@echo ""
	@echo "Test Infrastructure:"
	@echo "  make test-infra-up    - Start test infrastructure"
	@echo "  make test-infra-down  - Stop test infrastructure"
	@echo "  make test-infra-logs  - Show test infrastructure logs"
	@echo ""
	@echo "Load Testing:"
	@echo "  make load-test        - Run load tests"
	@echo "  make load-test-cache  - Run load tests with cache"
	@echo "  make load-test-guard  - Run load tests with egress guard"
	@echo ""
	@echo "Reports:"
	@echo "  make report-html      - Generate HTML test report"
	@echo "  make report-coverage  - Generate coverage report"
	@echo "  make report-security  - Generate security report"

# Installation
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	npm install

# Quick Tests (Tier 1)
test-quick:
	@echo "Running quick tests (Tier 1)..."
	python -m pytest tests/agentdev/test_state_basic.py -v --tb=short
	python -m pytest tests/agentdev/test_security_basic.py -v --tb=short
	python -m pytest tests/agentdev/test_observability_basic.py -v --tb=short
	python -m pytest tests/agentdev/test_cicd.py -v --tb=short

# Full Test Suite
test-full:
	@echo "Running full test suite..."
	python -m pytest tests/ -v --tb=short --cov=agentdev --cov-report=html --cov-report=xml

# SEAL-GRADE Tests
test-seal:
	@echo "Running SEAL-GRADE tests..."
	python -m pytest tests/agentdev/ -v --tb=short -m "seal"
	python -m pytest tests/chaos/ -v --tb=short
	python -m pytest tests/fuzzing/ -v --tb=short
	python -m pytest tests/security/ -v --tb=short

# Linting
lint:
	@echo "Running linters..."
	ruff check . --fix --force-exclude
	black --check --diff .
	isort --check-only --diff .
	mypy . --ignore-missing-imports --no-error-summary

# Formatting
format:
	@echo "Formatting code..."
	black .
	isort .
	ruff format .

# Security Scan
security-scan:
	@echo "Running security scans..."
	bandit -r . -f json -o bandit-report.json
	safety check --json --output safety-report.json
	semgrep --config=auto --json --output=semgrep-report.json .
	python ci/check_secrets.py

# CI/CD Commands
ci-tier1: lint test-quick security-scan ci-policy ci-secrets ci-protected
	@echo "✅ Tier 1 CI completed successfully"

ci-tier2: test-full test-seal
	@echo "✅ Tier 2 CI completed successfully"

ci-policy:
	@echo "Checking policy compliance..."
	python ci/check_policy_loaded.py

ci-secrets:
	@echo "Checking for secrets..."
	python ci/check_secrets.py

ci-protected:
	@echo "Checking protected files..."
	python ci/check_protected_files.py

# Test Infrastructure
test-infra-up:
	@echo "Starting test infrastructure..."
	docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Test infrastructure is ready"

test-infra-down:
	@echo "Stopping test infrastructure..."
	docker-compose -f docker-compose.test.yml down

test-infra-logs:
	@echo "Showing test infrastructure logs..."
	docker-compose -f docker-compose.test.yml logs

# Load Testing
load-test:
	@echo "Running baseline load test..."
	k6 run load_test/baseline.js --out json=load-results.json

load-test-cache:
	@echo "Running load test with cache..."
	k6 run load_test/with_cache.js --out json=load-results-cache.json

load-test-guard:
	@echo "Running load test with egress guard..."
	k6 run load_test/with_egress_guard.js --out json=load-results-guard.json

# Reports
report-html:
	@echo "Generating HTML test report..."
	python -m pytest tests/ --html=report.html --self-contained-html

report-coverage:
	@echo "Generating coverage report..."
	python -m pytest tests/ --cov=agentdev --cov-report=html --cov-report=xml

report-security:
	@echo "Generating security report..."
	python ci/generate_security_report.py

# Cleanup
clean:
	@echo "Cleaning artifacts..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf report.html
	rm -rf bandit-report.json
	rm -rf safety-report.json
	rm -rf semgrep-report.json
	rm -rf load-results*.json
	rm -rf mutation-results.xml
	rm -rf .mutmut-cache/
	rm -rf .benchmarks/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Development helpers
dev-setup: install
	@echo "Setting up development environment..."
	pre-commit install
	@echo "Development environment ready"

dev-test: format lint test-quick
	@echo "Development test cycle completed"

# CI/CD validation
validate-ci:
	@echo "Validating CI/CD configuration..."
	@echo "Checking workflow files..."
	@test -f .github/workflows/ci_tier1.yml || (echo "❌ Tier 1 workflow missing" && exit 1)
	@test -f .github/workflows/ci_tier2_nightly.yml || (echo "❌ Tier 2 workflow missing" && exit 1)
	@echo "Checking CI scripts..."
	@test -f ci/check_policy_loaded.py || (echo "❌ Policy check script missing" && exit 1)
	@test -f ci/check_protected_files.py || (echo "❌ Protected files check script missing" && exit 1)
	@test -f ci/check_secrets.py || (echo "❌ Secrets check script missing" && exit 1)
	@echo "✅ CI/CD configuration is valid"

# Performance benchmarks
benchmark:
	@echo "Running performance benchmarks..."
	python -m pytest tests/benchmarks/ -v --benchmark-only --benchmark-save=benchmark-results

# Mutation testing
mutation-test:
	@echo "Running mutation testing..."
	mutmut run --paths-to-mutate=agentdev/ --tests-dir=tests/agentdev/
	mutmut junitxml > mutation-results.xml

# Chaos engineering
chaos-test:
	@echo "Running chaos engineering tests..."
	python -m pytest tests/chaos/ -v --tb=short

# Fuzzing
fuzz-test:
	@echo "Running fuzzing tests..."
	python -m pytest tests/fuzzing/ -v --tb=short --hypothesis-show-statistics

# Integration tests
integration-test:
	@echo "Running integration tests..."
	python -m pytest tests/integration/ -v --tb=short

# All-in-one commands
ci-all: validate-ci ci-tier1 ci-tier2
	@echo "🎉 All CI/CD checks completed successfully"

test-all: test-quick test-full test-seal
	@echo "🎉 All tests completed successfully"

# Help for specific targets
help-ci:
	@echo "CI/CD Commands:"
	@echo "  make ci-tier1         - Run Tier 1 CI (lint, quick tests, security)"
	@echo "  make ci-tier2         - Run Tier 2 CI (full tests, mutation, chaos)"
	@echo "  make ci-all           - Run all CI checks"
	@echo "  make validate-ci      - Validate CI configuration"

help-test:
	@echo "Testing Commands:"
	@echo "  make test-quick       - Quick tests (Tier 1)"
	@echo "  make test-full        - Full test suite"
	@echo "  make test-seal        - SEAL-GRADE tests"
	@echo "  make test-all         - All tests"
	@echo "  make benchmark        - Performance benchmarks"
	@echo "  make mutation-test    - Mutation testing"
	@echo "  make chaos-test       - Chaos engineering"
	@echo "  make fuzz-test        - Fuzzing tests"
	@echo "  make integration-test - Integration tests"
	@echo "  make load_phase3      - Phase 3 load tests"

# Phase 3 Load Testing
load_phase3:
	@echo "🚀 Starting Phase 3 Load Testing..."
	@mkdir -p reports/phase3/load
	@echo "Running K6 load test with 1000 prompts and 100 concurrent users..."
	@k6 run --out json=reports/phase3/load/load_test_results.json load_test/k6_phase3.js
	@echo "✅ Load test completed. Results saved to reports/phase3/load/"
	@echo "📊 Check load_test_results.json for detailed metrics"
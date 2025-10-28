# AgentDev Test Harness Makefile
# Provides quick commands for running different test suites

.PHONY: help test-unit test-integration test-e2e test-security test-chaos test-performance test-learning test-all clean install

# Default target
help:
	@echo "AgentDev Test Harness Commands:"
	@echo "  make test-unit          - Run unit tests"
	@echo "  make test-integration   - Run integration tests"
	@echo "  make test-e2e           - Run end-to-end tests"
	@echo "  make test-security      - Run security tests"
	@echo "  make test-chaos         - Run chaos engineering tests"
	@echo "  make test-performance   - Run performance tests"
	@echo "  make test-learning      - Run learning evaluation tests"
	@echo "  make test-all           - Run all tests"
	@echo "  make clean              - Clean test artifacts"
	@echo "  make install            - Install test dependencies"

# Install test dependencies
install:
	pip install -r requirements.txt
	pip install -e ../

# Unit tests
test-unit:
	pytest test_unit_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/unit_test_report.html --self-contained-html

# Integration tests
test-integration:
	pytest test_integration_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/integration_test_report.html --self-contained-html

# End-to-end tests
test-e2e:
	pytest test_e2e_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/e2e_test_report.html --self-contained-html

# Security tests
test-security:
	pytest test_security_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/security_test_report.html --self-contained-html

# Chaos engineering tests
test-chaos:
	pytest test_chaos_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/chaos_test_report.html --self-contained-html

# Performance tests
test-performance:
	pytest test_performance_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/performance_test_report.html --self-contained-html

# Learning evaluation tests
test-learning:
	pytest test_learning_*.py -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/learning_test_report.html --self-contained-html

# Run all tests
test-all:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/full_test_report.html --self-contained-html --benchmark-only --benchmark-save=reports/benchmark.json

# Run tests with mutation testing
test-mutation:
	mutmut run --paths-to-mutate=../agent_dev/
	mutmut html --paths-to-mutate=../agent_dev/ --output-dir=reports/mutation_html

# Run tests with property-based testing
test-property:
	pytest test_unit_*.py -v --hypothesis-show-statistics

# Run tests with parallel execution
test-parallel:
	pytest . -v -n auto --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific markers
test-markers:
	pytest . -v -m "unit or integration or e2e or security or chaos or performance or learning"

# Run tests with coverage threshold
test-coverage:
	pytest . -v --cov=agent_dev --cov-fail-under=90 --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with performance benchmarking
test-benchmark:
	pytest test_performance_*.py -v --benchmark-only --benchmark-save=reports/benchmark.json --benchmark-sort=mean

# Run tests with security scanning
test-security-scan:
	bandit -r ../agent_dev/ -f json -o reports/bandit_report.json
	pytest test_security_*.py -v

# Run tests with linting
test-lint:
	flake8 ../agent_dev/ --output-file=reports/flake8_report.txt
	pytest . -v

# Run tests with type checking
test-type:
	mypy ../agent_dev/ --html-report reports/mypy_report.html
	pytest . -v

# Generate test report
test-report:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --html=reports/test_report.html --self-contained-html --junitxml=reports/junit.xml

# Clean test artifacts
clean:
	rm -rf reports/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mutmut-cache/
	rm -rf __pycache__/
	rm -rf *.pyc
	rm -rf *.pyo
	rm -rf *.pyd
	rm -rf .DS_Store
	rm -rf Thumbs.db

# Setup test environment
setup:
	mkdir -p reports/
	mkdir -p datasets/
	mkdir -p fixtures/
	mkdir -p e2e_sandboxes/
	mkdir -p k6/
	mkdir -p chaos/
	pip install -r requirements.txt

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=test_unit_impact_analyzer.py"
	pytest $(FILE) -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific pattern
test-pattern:
	@echo "Usage: make test-pattern PATTERN=test_unit_*"
	pytest $(PATTERN) -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific marker
test-marker:
	@echo "Usage: make test-marker MARKER=unit"
	pytest . -v -m $(MARKER) --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with verbose output
test-verbose:
	pytest . -v -s --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with debugging
test-debug:
	pytest . -v -s --pdb --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific Python version
test-python:
	@echo "Usage: make test-python PYTHON=python3.9"
	$(PYTHON) -m pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific configuration
test-config:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --config=test_config.yaml

# Run tests with specific environment
test-env:
	@echo "Usage: make test-env ENV=test"
	ENV=$(ENV) pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific timeout
test-timeout:
	@echo "Usage: make test-timeout TIMEOUT=300"
	pytest . -v --timeout=$(TIMEOUT) --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific workers
test-workers:
	@echo "Usage: make test-workers WORKERS=4"
	pytest . -v -n $(WORKERS) --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific retries
test-retries:
	@echo "Usage: make test-retries RETRIES=3"
	pytest . -v --maxfail=$(RETRIES) --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific fail-fast
test-fail-fast:
	pytest . -v -x --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml

# Run tests with specific collect-only
test-collect:
	pytest . --collect-only

# Run tests with specific list
test-list:
	pytest . --collect-only -q

# Run tests with specific summary
test-summary:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --tb=short

# Run tests with specific traceback
test-traceback:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --tb=long

# Run tests with specific capture
test-capture:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --capture=no

# Run tests with specific warnings
test-warnings:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --disable-warnings

# Run tests with specific logging
test-logging:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --log-cli-level=INFO

# Run tests with specific fixtures
test-fixtures:
	pytest . -v --cov=agent_dev --cov-report=html:reports/coverage_html --cov-report=xml:reports/coverage.xml --fixtures

# Run tests with specific markers
test-markers-list:
	pytest . --markers

# Run tests with specific plugins
test-plugins:
	pytest . --plugins

# Run tests with specific version
test-version:
	pytest --version

# Run tests with specific help
test-help:
	pytest --help

# Run tests with specific config
test-config-show:
	pytest --config-file=pytest.ini

# Run tests with specific ini
test-ini:
	pytest --ini=pytest.ini

# Run tests with specific setup
test-setup:
	pytest --setup-only

# Run tests with specific teardown
test-teardown:
	pytest --teardown-only

# Run tests with specific setup-teardown
test-setup-teardown:
	pytest --setup-teardown

# Run tests with specific setup-show
test-setup-show:
	pytest --setup-show

# Run tests with specific setup-plan
test-setup-plan:
	pytest --setup-plan

# Run tests with specific setup-only
test-setup-only:
	pytest --setup-only

# Run tests with specific teardown-only
test-teardown-only:
	pytest --teardown-only

# Run tests with specific setup-teardown
test-setup-teardown:
	pytest --setup-teardown

# Run tests with specific setup-show
test-setup-show:
	pytest --setup-show

# Run tests with specific setup-plan
test-setup-plan:
	pytest --setup-plan

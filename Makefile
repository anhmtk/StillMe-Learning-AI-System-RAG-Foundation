# StillMe AI - Module Validation Makefile

.PHONY: help validate-all validate-module lint-all lint-module test-all test-module type-check-all type-check-module clean

# Default target
help:
	@echo "StillMe AI - Module Validation Commands"
	@echo "========================================"
	@echo ""
	@echo "Available commands:"
	@echo "  validate-all          - Validate all modules (ruff + mypy + tests + type-ignore check)"
	@echo "  validate-module MODULE - Validate specific module"
	@echo "  lint-all              - Run ruff linting on all modules"
	@echo "  lint-module MODULE    - Run ruff linting on specific module"
	@echo "  test-all              - Run tests on all modules"
	@echo "  test-module MODULE    - Run tests on specific module"
	@echo "  type-check-all        - Run mypy type checking on all modules"
	@echo "  type-check-module MODULE - Run mypy type checking on specific module"
	@echo "  clean                 - Clean up temporary files"
	@echo ""
	@echo "Available modules:"
	@echo "  stillme_core/common   - Common utilities"
	@echo "  gateway_poc           - Gateway proof of concept"
	@echo "  stillme_core          - Core StillMe functionality"
	@echo "  agent_dev             - Agent development tools"
	@echo "  clients               - Client implementations"
	@echo "  desktop_app           - Desktop application"
	@echo "  dashboards            - Dashboard implementations"
	@echo "  niche_radar           - Niche radar functionality"
	@echo "  plugins               - Plugin system"
	@echo "  runtime               - Runtime utilities"
	@echo "  scripts               - Utility scripts"
	@echo "  tests                 - Test suite"
	@echo "  tools                 - Development tools"
	@echo ""
	@echo "Examples:"
	@echo "  make validate-all"
	@echo "  make validate-module stillme_core"
	@echo "  make lint-module agent_dev"

# Validate all modules
validate-all:
	@echo "🚀 Validating all modules..."
	python scripts/validate_all_modules.py

# Validate specific module
validate-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Please specify MODULE. Usage: make validate-module MODULE=<module_name>"; \
		echo "Available modules: stillme_core/common, gateway_poc, stillme_core, agent_dev, clients, desktop_app, dashboards, niche_radar, plugins, runtime, scripts, tests, tools"; \
		exit 1; \
	fi
	@echo "🚀 Validating module: $(MODULE)"
	python scripts/validate_module.py $(MODULE)

# Lint all modules
lint-all:
	@echo "🔍 Running ruff linting on all modules..."
	ruff check . --statistics

# Lint specific module
lint-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Please specify MODULE. Usage: make lint-module MODULE=<module_name>"; \
		echo "Available modules: stillme_core/common, gateway_poc, stillme_core, agent_dev, clients, desktop_app, dashboards, niche_radar, plugins, runtime, scripts, tests, tools"; \
		exit 1; \
	fi
	@echo "🔍 Running ruff linting on module: $(MODULE)"
	ruff check $(MODULE) --statistics

# Test all modules
test-all:
	@echo "🧪 Running tests on all modules..."
	pytest -v

# Test specific module
test-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Please specify MODULE. Usage: make test-module MODULE=<module_name>"; \
		echo "Available modules: stillme_core/common, gateway_poc, stillme_core, agent_dev, clients, desktop_app, dashboards, niche_radar, plugins, runtime, scripts, tests, tools"; \
		exit 1; \
	fi
	@echo "🧪 Running tests on module: $(MODULE)"
	pytest $(MODULE) -v

# Type check all modules
type-check-all:
	@echo "🔍 Running mypy type checking on all modules..."
	mypy . --ignore-missing-imports

# Type check specific module
type-check-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "❌ Please specify MODULE. Usage: make type-check-module MODULE=<module_name>"; \
		echo "Available modules: stillme_core/common, gateway_poc, stillme_core, agent_dev, clients, desktop_app, dashboards, niche_radar, plugins, runtime, scripts, tests, tools"; \
		exit 1; \
	fi
	@echo "🔍 Running mypy type checking on module: $(MODULE)"
	mypy $(MODULE) --ignore-missing-imports

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	find . -type d -name ".ruff_cache" -delete
	@echo "✅ Cleanup completed"
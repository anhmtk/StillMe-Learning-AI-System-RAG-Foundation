# Test & Evaluation Harness Makefile
# Provides convenient commands for running tests and analysis

.PHONY: help install test analyze ci clean report

# Default target
help:
	@echo "🧪 Test & Evaluation Harness - Available Commands:"
	@echo ""
	@echo "📦 Setup:"
	@echo "  install     - Install dependencies"
	@echo "  clean       - Clean generated files"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test        - Run comprehensive test suite"
	@echo "  test-offline- Run tests in offline mode"
	@echo "  test-quick  - Run quick test (100 samples)"
	@echo ""
	@echo "📊 Analysis:"
	@echo "  analyze     - Run optimization analysis"
	@echo "  analyze-trend - Run analysis with trend data (30 days)"
	@echo "  report      - Generate HTML report only"
	@echo ""
	@echo "🚀 CI/CD:"
	@echo "  ci          - Simulate CI pipeline locally"
	@echo "  ci-offline  - Simulate CI pipeline (offline mode)"
	@echo ""
	@echo "📈 Performance:"
	@echo "  benchmark   - Run performance benchmark"
	@echo "  dataset     - Generate large dataset (1000 samples)"
	@echo "  dataset-large - Generate large dataset (5000 samples)"
	@echo ""
	@echo "🔧 Utilities:"
	@echo "  validate    - Validate report structure"
	@echo "  open-report - Open HTML report in browser"
	@echo "  status      - Show current status"

# Setup commands
install:
	@echo "📦 Installing dependencies..."
	pip install -r ../requirements.txt
	pip install plotly pandas pyyaml
	@echo "✅ Dependencies installed"

clean:
	@echo "🧹 Cleaning generated files..."
	rm -rf reports/*.json reports/*.html
	rm -rf datasets/augmented/*
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	@echo "✅ Clean completed"

# Testing commands
test:
	@echo "🧪 Running comprehensive test suite..."
	python demo_comprehensive_test.py
	@echo "✅ Test suite completed"

test-offline:
	@echo "🧪 Running tests in offline mode..."
	OFFLINE_MODE=true MOCK_PROVIDERS=true python demo_comprehensive_test.py
	@echo "✅ Offline test completed"

test-quick:
	@echo "🧪 Running quick test (100 samples)..."
	python runners/run_all.py --samples 100 --skip-generation
	@echo "✅ Quick test completed"

# Analysis commands
analyze:
	@echo "🎯 Running optimization analysis..."
	python demo_optimization.py
	@echo "✅ Analysis completed"

analyze-trend:
	@echo "📈 Running analysis with trend data (30 days)..."
	python runners/run_all.py --since 30
	@echo "✅ Trend analysis completed"

report:
	@echo "📊 Generating HTML report..."
	python -c "from optimization.optimization_analyzer import OptimizationAnalyzer; analyzer = OptimizationAnalyzer(); analyzer.analyze_reports()"
	@echo "✅ Report generated"

# CI/CD simulation
ci:
	@echo "🚀 Simulating CI pipeline..."
	python runners/run_all.py --samples 1000 --verbose
	@echo "✅ CI simulation completed"

ci-offline:
	@echo "🚀 Simulating CI pipeline (offline mode)..."
	python runners/run_all.py --samples 1000 --offline --verbose
	@echo "✅ Offline CI simulation completed"

# Performance commands
benchmark:
	@echo "⚡ Running performance benchmark..."
	python benchmarking/performance_benchmark.py
	@echo "✅ Benchmark completed"

dataset:
	@echo "📊 Generating large dataset (1000 samples)..."
	python generate_large_dataset.py
	@echo "✅ Dataset generated"

dataset-large:
	@echo "📊 Generating large dataset (5000 samples)..."
	python -c "from generate_large_dataset import generate_large_dataset; generate_large_dataset(max_samples=5000, output_file='reports/large_dataset_5k.json')"
	@echo "✅ Large dataset generated"

# Utility commands
validate:
	@echo "🔍 Validating report structure..."
	python -c "
import json
import sys
from pathlib import Path

reports_dir = Path('reports')
json_files = list(reports_dir.glob('*.json'))

if not json_files:
    print('❌ No JSON reports found')
    sys.exit(1)

for json_file in json_files:
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        print(f'✅ {json_file.name}: Valid JSON')
    except json.load.JSONDecodeError as e:
        print(f'❌ {json_file.name}: Invalid JSON - {e}')
        sys.exit(1)

print('✅ All reports are valid')
"
	@echo "✅ Validation completed"

open-report:
	@echo "🌐 Opening HTML report..."
	@if [ -f "reports/optimization_report.html" ]; then \
		if command -v xdg-open > /dev/null; then \
			xdg-open reports/optimization_report.html; \
		elif command -v open > /dev/null; then \
			open reports/optimization_report.html; \
		elif command -v start > /dev/null; then \
			start reports/optimization_report.html; \
		else \
			echo "❌ Cannot open browser. Please open reports/optimization_report.html manually"; \
		fi \
	else \
		echo "❌ No HTML report found. Run 'make analyze' first"; \
	fi

status:
	@echo "📊 Current Status:"
	@echo ""
	@echo "📁 Reports directory:"
	@ls -la reports/ 2>/dev/null || echo "  (empty)"
	@echo ""
	@echo "📊 Dataset directory:"
	@ls -la datasets/ 2>/dev/null || echo "  (empty)"
	@echo ""
	@echo "🔧 Environment:"
	@echo "  Python: $(shell python --version 2>/dev/null || echo 'Not found')"
	@echo "  Pip: $(shell pip --version 2>/dev/null | head -1 || echo 'Not found')"
	@echo ""
	@if [ -f "reports/optimization_report.json" ]; then \
		echo "📈 Latest Analysis:"; \
		python -c "
import json
try:
    with open('reports/optimization_report.json', 'r') as f:
        data = json.load(f)
    print(f'  Run ID: {data.get(\"run_id\", \"Unknown\")}')
    print(f'  SLO Status: {\"✅ PASS\" if data.get(\"slo_status\", False) else \"❌ FAIL\"}')
    print(f'  Git SHA: {data.get(\"git_sha\", \"Unknown\")}')
except:
    print('  (Could not read latest analysis)')
"; \
	fi

# Development commands
dev-setup:
	@echo "🛠️ Setting up development environment..."
	make install
	mkdir -p reports datasets/seed datasets/augmented
	@echo "✅ Development setup completed"

dev-test:
	@echo "🧪 Running development tests..."
	python simple_demo.py
	python demo_augmentation.py
	@echo "✅ Development tests completed"

# Full pipeline
all: clean install test analyze benchmark
	@echo "🎉 Full pipeline completed successfully!"

# Quick development cycle
dev: clean test-quick analyze
	@echo "🚀 Quick development cycle completed!"

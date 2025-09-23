# StillMe Repository Management Makefile

.PHONY: help inventory-primary inventory-excluded find-candidates quarantine-list quarantine-low quarantine-medium quarantine-high restore cleanup test-before-quarantine test-after-quarantine shadow-ci

# Default target
help:
	@echo "StillMe Repository Management Commands"
	@echo "======================================"
	@echo ""
	@echo "Inventory Commands:"
	@echo "  inventory-primary     - Scan primary files (production code, configs, docs)"
	@echo "  inventory-excluded    - Scan excluded files (artifacts, dependencies)"
	@echo "  inventory-all         - Run both primary and excluded inventory"
	@echo ""
	@echo "Deletion Candidates:"
	@echo "  find-candidates       - Find deletion candidates from inventory"
	@echo ""
	@echo "Quarantine Commands:"
	@echo "  quarantine-list       - List currently quarantined files"
	@echo "  quarantine-low        - Quarantine LOW risk files (dry run)"
	@echo "  quarantine-low-real   - Quarantine LOW risk files (real)"
	@echo "  quarantine-medium     - Quarantine MEDIUM risk files (dry run)"
	@echo "  quarantine-high       - Quarantine HIGH risk files (dry run)"
	@echo ""
	@echo "Restore Commands:"
	@echo "  restore               - Restore all quarantined files"
	@echo "  cleanup               - Permanently delete quarantined files"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test-before-quarantine - Run tests before quarantine"
	@echo "  test-after-quarantine  - Run tests after quarantine"
	@echo ""
	@echo "CI Commands:"
	@echo "  shadow-ci             - Run shadow CI workflow locally"

# Inventory Commands
inventory-primary:
	@echo "🔍 Running primary inventory scan..."
	python tools/repo_inventory.py --mode primary --with-hash

inventory-excluded:
	@echo "🔍 Running excluded inventory scan..."
	python tools/repo_inventory.py --mode excluded

inventory-all: inventory-primary inventory-excluded
	@echo "✅ Both inventory scans completed"

# Deletion Candidates
find-candidates:
	@echo "🗑️ Finding deletion candidates..."
	python tools/find_candidates.py

# Quarantine Commands
quarantine-list:
	@echo "📋 Listing quarantined files..."
	python tools/quarantine_move.py --action list

quarantine-low:
	@echo "🚧 Quarantining LOW risk files (dry run)..."
	python tools/quarantine_move.py --action quarantine --risk LOW --dry-run

quarantine-low-real:
	@echo "🚧 Quarantining LOW risk files (real)..."
	python tools/quarantine_move.py --action quarantine --risk LOW

quarantine-medium:
	@echo "🚧 Quarantining MEDIUM risk files (dry run)..."
	python tools/quarantine_move.py --action quarantine --risk MEDIUM --dry-run

quarantine-high:
	@echo "🚧 Quarantining HIGH risk files (dry run)..."
	python tools/quarantine_move.py --action quarantine --risk HIGH --dry-run

# Restore Commands
restore:
	@echo "🔄 Restoring quarantined files..."
	python tools/restore_from_graveyard.py

cleanup:
	@echo "🗑️ Cleaning up graveyard..."
	python tools/quarantine_move.py --action cleanup

# Testing Commands
test-before-quarantine:
	@echo "🧪 Running tests before quarantine..."
	python -m pytest tests/ -v --tb=short --maxfail=5

test-after-quarantine:
	@echo "🧪 Running tests after quarantine..."
	python -m pytest tests/ -v --tb=short --maxfail=5

# CI Commands
shadow-ci: inventory-primary find-candidates test-before-quarantine quarantine-low test-after-quarantine restore test-after-quarantine
	@echo "✅ Shadow CI workflow completed"

# Quick Commands
quick-clean: inventory-primary find-candidates quarantine-low
	@echo "✅ Quick clean completed"

full-clean: inventory-all find-candidates quarantine-low-real
	@echo "✅ Full clean completed"
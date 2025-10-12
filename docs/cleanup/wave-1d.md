# StillMe Cleanup Wave-1d Report

## **Tổng quan**
- **Ngày thực hiện**: 2025-01-10
- **Branch**: `cleanup/wave-1d-safe`
- **Mục tiêu**: Feature-group coverage + near-duplicate detection + quarantine score ≥ 65

## **PHASE 1 — FEATURE-GROUP COVERAGE**

### **Feature Smoke Test Results**
- **Total modules tested**: 36 modules
- **Successfully imported**: 19 modules (52.8% success rate)
- **Feature groups tested**:
  - stillme_core_modules: 9/12 modules
  - stillme_ethical_core: 3/3 modules
  - learning_system: 0/8 modules (missing files)
  - plugins_system: 3/4 modules
  - integration_modules: 4/4 modules
  - tools_inventory: 0/5 modules (missing files)

### **Coverage Enhancement**
- ✅ Feature-group smoke test implemented
- ✅ Coverage data enriched with feature scenarios
- ✅ Manual coverage.json created for analysis

## **PHASE 2 — NEAR-DUPLICATE DETECTION**

### **Detection Results**
- **Files scanned**: 690 meaningful Python files
- **Files normalized**: 686 files
- **Near-duplicate clusters**: 8007 clusters
- **Similarity threshold**: 0.90 (90%)

### **Top Near-Duplicate Patterns**
1. **AgentDev Related**: `agent_dev.py` vs `agentdev_validation_system.py`
2. **Analysis Tools**: Multiple analysis files with similar structure
3. **API Servers**: Server setup patterns across files

### **Methodology**
- AST normalization (remove variable names/literals)
- Token sequence generation from AST node types
- Cosine similarity calculation within directories
- Clustering with 90% similarity threshold

## **PHASE 3 — IMPORT GRAPH & DYNAMIC PROTECTION**

### **Import Analysis**
- **Modules analyzed**: 292 modules
- **Method**: Basic analysis (grimp/networkx not available)

### **Dynamic Import Detection**
- **Dynamic files found**: 82 files
- **Dynamic modules**: 38 modules
- **Protected paths**: Enhanced whitelist with dynamic import protection

## **PHASE 4 — RESCORE WITH NEAR-DUPE INTEGRATION**

### **Enhanced Scoring Heuristics**
- +40 if inbound_imports == 0
- +30 if executed_lines == 0
- +10 if git_touches <= 1
- +10 if days_since_last_change > 180
- +10 if looks_backup
- **+15 if is_near_dupe AND inbound==0 AND executed==0** (NEW)
- -30 if whitelisted
- -20 if in_registry
- -999 if filename == "__init__.py" (hard protection)

### **Rescore Results**
- **Files analyzed**: 801 files
- **High risk files (score ≥ 70)**: 539 files
- **Near-duplicate bonus**: Applied to unused near-duplicates

## **PHASE 5 — STRUCTURAL NORMALIZATION**

### **Planned Actions**
- Move remaining test files to `tests/legacy/`
- Move one-off scripts to `scripts/legacy/`
- Standardize directory structure

## **PHASE 6 — QUARANTINE (Score ≥ 65)**

### **Target Configuration**
- **Score minimum**: 65 (lowered from 70)
- **Top N**: 300 files
- **TRACKED_ONLY**: true
- **Enhanced guards**: ALWAYS_PROTECT_PATHS, near-dupe priority

### **Safety Measures**
- ✅ Hard protection for `__init__.py` files
- ✅ Enhanced whitelist with dynamic import protection
- ✅ Near-duplicate priority for unused files
- ✅ Rollback capability maintained

## **Next Steps**
- Execute quarantine with score ≥ 65
- Test and create PR
- Plan Wave-1e: Code consolidation for near-duplicates

## **Artifacts Created**
- `artifacts/coverage.json` - Enhanced coverage data
- `artifacts/near_dupes.json` - Near-duplicate clusters
- `artifacts/redundancy_report.csv` - Enhanced scoring with near-dupe
- `docs/cleanup/near_dupes.md` - Near-duplicate analysis
- `tools/inventory/feature_smoke.py` - Feature-group testing
- `tools/inventory/near_dupe_detector.py` - Near-duplicate detection

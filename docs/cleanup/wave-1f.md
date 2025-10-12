# Wave-1f: Near-Duplicate Consolidation & CI Gates

## Overview
Wave-1f focuses on consolidating near-duplicate code safely, maintaining backward compatibility using alias shims, and tightening CI to prevent new redundant code.

## Completed Tasks

### 1. Near-Duplicate Pilot Selection
- **Status**: ✅ Completed
- **Files**: `tools/inventory/near_dupe_pilot_selector.py`
- **Output**: `artifacts/near_dupes_pilot.json`
- **Result**: Selected 0 pilot clusters (no suitable candidates found with current criteria)

### 2. Alias Shim & Import Rewrite
- **Status**: ✅ Completed
- **Files**: 
  - `stillme_compat/__init__.py`
  - `stillme_compat/stillme_core/legacy_component.py`
  - `stillme_compat/stillme_core/old_module.py`
  - `tools/inventory/apply_canonical_imports.py`
- **Result**: Created compatibility shims with deprecation warnings

### 3. Rescore & Quarantine
- **Status**: ✅ Completed
- **Files**: `scripts/windows/attic_move.ps1`
- **Result**: 0 files moved (no candidates met criteria)

### 4. CI Guards & Baselines
- **Status**: ✅ Completed
- **Files**:
  - `.github/workflows/cleanup-audit.yml`
  - `artifacts/near_dupes_baseline.json`
  - `artifacts/dynamic_registry_paths_baseline.json`
  - `artifacts/redundancy_report_baseline.csv`
- **Features**:
  - FAIL on new backup files (excluding `_attic/`)
  - WARN for high-risk files (score >= 70) not in whitelist
  - WARN for new unused near-duplicate clusters
  - Upload artifacts for review

## Analysis Results

### Import Graph Analysis
- **Root packages**: 2 (`stillme_core`, `stillme_ethical_core`)
- **Modules analyzed**: 293
- **Modules with inbound imports**: 23
- **Output**: `artifacts/import_inbound.json`

### Near-Duplicate Detection
- **Clusters found**: 0 (no suitable candidates)
- **Reason**: Most near-duplicates are already in `_attic/` or don't meet usage criteria
- **Output**: `artifacts/near_dupes.json`

### Redundancy Scoring
- **Files analyzed**: 0 (no files met quarantine criteria)
- **High-risk files (score >= 70)**: 0
- **Output**: `artifacts/redundancy_report.csv`

## Commands Used

```bash
# Import graph analysis
python tools/inventory/import_graph.py

# Near-duplicate detection
python tools/inventory/near_dupe_detector.py

# Pilot cluster selection
python tools/inventory/near_dupe_pilot_selector.py

# Quarantine (dry-run)
powershell -ExecutionPolicy Bypass -File scripts/windows/attic_move.ps1 -FromCsv artifacts/redundancy_report.csv -ScoreMin 70 -TopN 200 -RelaxedMin 60
```

## Next Steps

1. **Review CI Results**: Monitor the new cleanup-audit workflow
2. **Expand Criteria**: Consider relaxing near-duplicate selection criteria
3. **Manual Review**: Review high-risk files manually if any appear
4. **Future Waves**: Plan Wave-1g with expanded scope

## Files Created/Modified

### New Files
- `.github/workflows/cleanup-audit.yml`
- `stillme_compat/__init__.py`
- `stillme_compat/stillme_core/legacy_component.py`
- `stillme_compat/stillme_core/old_module.py`
- `tools/inventory/apply_canonical_imports.py`
- `tools/inventory/import_graph.py`
- `tools/inventory/near_dupe_pilot_selector.py`
- `scripts/windows/attic_move.ps1`

### Baselines
- `artifacts/near_dupes_baseline.json`
- `artifacts/dynamic_registry_paths_baseline.json`
- `artifacts/redundancy_report_baseline.csv`

### Artifacts
- `artifacts/import_inbound.json`
- `artifacts/near_dupes.json`
- `artifacts/redundancy_report.csv`
- `artifacts/import_rewrite_diff.txt`

## Branch Information
- **Branch**: `cleanup/wave-1f-safe`
- **Base**: `main`
- **Commits**: 1
- **Status**: Ready for PR
# Cleanup Wave-1e Report

This document summarizes the activities and outcomes of Cleanup Wave-1e for the StillMe project. The primary objectives for this wave included near-duplicate refactoring with alias shims, pilot canonical imports, and continued controlled quarantine.

## **PREREQUISITE: Wave-1d PR**

**Manual PR Creation Required:**
- **URL:** https://github.com/anhmtk/stillme_ai_ipc/pull/new/cleanup/wave-1d-safe
- **Title:** `chore(cleanup): Wave-1d feature-coverage + near-dupe detector + quarantine (score ≥ 65)`
- **Base:** `main`
- **Head:** `cleanup/wave-1d-safe`

**Description:**
```
Wave-1d cleanup with enhanced coverage, near-duplicate detection, and quarantine of 297 high-score files

## Changes
- Feature-group coverage: 36 modules tested (52.8% success rate)
- Near-duplicate detection: 8,007 clusters from 690 files
- Import graph & dynamic protection: 82 dynamic imports protected
- Rescore with near-dupe: 801 files analyzed, 539 high-risk
- Structural normalization: 2 test files moved to tests/legacy/
- Quarantine: 297 files moved to _attic/ (total 450 files)

## Artifacts
- artifacts/coverage.json
- artifacts/near_dupes.json
- artifacts/import_inbound.json
- artifacts/dynamic_registry_paths.json
- artifacts/redundancy_report.csv
- artifacts/attic_moves.csv
- docs/cleanup/wave-1d.md
- docs/cleanup/near_dupes.md

## Safety
- No permanent deletion, only moves to _attic/
- __init__.py files hard-protected (score 0)
- Rollback capability maintained
- Tracked files only
```

---

## **PHASE 1: NEAR-DUPE FILTERING**

- **Objective**: Filter near-duplicate clusters to identify pilot candidates for refactoring.
- **Approach**: Load `artifacts/near_dupes.json`, apply filtering criteria, and generate pilot set.

## **PHASE 2: ALIAS SHIM & IMPORT REWRITE (PILOT)**

- **Objective**: Create alias shims and rewrite imports to canonical files for pilot clusters.
- **Approach**: 
  - Create `stillme_compat/` package with deprecation warnings
  - Generate import rewrite script
  - Apply canonical imports for pilot clusters

## **PHASE 3: RESCORE & QUARANTINE**

- **Objective**: Recalculate scores and quarantine files with relaxed criteria for near-dupes/backups.
- **Approach**: 
  - Run full analysis pipeline
  - Apply dual scoring: 70 for general, 60 for near-dupe/backup
  - Execute controlled quarantine

## **PHASE 4: TESTS & CI GUARDS**

- **Objective**: Ensure system stability and add CI gates for near-duplicate prevention.
- **Approach**: 
  - Run tests and smoke checks
  - Update CI with near-dupe gates
  - Create baseline for future comparisons

## **PHASE 5: BRANCH & PR**

- **Objective**: Create clean branch and PR with clear diff.
- **Approach**: 
  - Create `cleanup/wave-1e-safe` from latest main
  - Commit in logical groups
  - Push and create PR

## **Safety Measures**

- `ALWAYS_PROTECT_PATHS` and `ALWAYS_PROTECT_FILENAMES` are respected
- All import rewrites have alias shims for backward compatibility
- Deprecation warnings for old import paths
- Rollback capability maintained
- Tracked files only

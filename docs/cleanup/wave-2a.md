# Wave-2a: Attic Eviction Planning & CI Hardening

## Overview
Wave-2a focuses on establishing a clean baseline after Wave-1f, planning safe eviction of old attic files, and hardening CI gates to prevent redundant code from returning.

## Configuration
- **EVICTION_MIN_DAYS**: 30 (minimum days in attic before eviction consideration)
- **TRACKED_ONLY**: true
- **ATTIC_PATH**: "_attic"
- **ROOT_PACKAGES**: ["stillme_core", "stillme_ethical_core"]

## Baseline after Wave-1f

### Import Graph Analysis
- **Root packages**: 2 (`stillme_core`, `stillme_ethical_core`)
- **Modules analyzed**: 293
- **Modules with inbound imports**: 23
- **Baseline saved**: `artifacts/baseline/import_inbound.json`

### Near-Duplicate Detection
- **Clusters found**: 0 (no suitable candidates)
- **Baseline saved**: `artifacts/baseline/near_dupes_baseline.json`

### Redundancy Scoring
- **Files analyzed**: 0 (no files met quarantine criteria)
- **High-risk files (score >= 70)**: 0
- **Baseline saved**: `artifacts/baseline/redundancy_report_baseline.csv`

## Attic Eviction Planning

### Decision Rules
A file in `_attic/` becomes an eviction candidate if:
- Exists in `_attic/` **≥ 30 days** (from `artifacts/attic_moves.csv`)
- NOT in `ALWAYS_PROTECT_*` paths
- **No reverse references** in current repo (grep import/module/name)
- **Not in recent rollback list** (compare attic_moves vs rollback log)

### Always Protected Paths
- `tools/**`
- `.github/**`
- `scripts/windows/attic_move.ps1`
- `scripts/windows/attic_rollback.ps1`
- `config/cleanup/whitelist.yml`
- `stillme_compat/**`
- All `__init__.py` files

## CI Gates & Scheduled Dry-Run

### Updated CI Features
- **FAIL** on new backup files: `*_backup.py|*_old.py|*_copy.py|*_tmp.py|*.py~|*.py.save` (excluding `_attic/`)
- **WARN** on new unused near-duplicate clusters
- **Weekly dry-run** of attic sweeper with artifact upload

## Commands Used

```bash
# Create baseline directory
mkdir -p artifacts/baseline

# Save baselines
cp artifacts/redundancy_report.csv artifacts/baseline/redundancy_report_baseline.csv
cp artifacts/near_dupes.json artifacts/baseline/near_dupes_baseline.json

# Run attic sweeper (dry-run)
python tools/inventory/attic_sweeper.py --days 30 --dry-run
```

## Files Created/Modified

### New Files
- `tools/inventory/attic_sweeper.py`
- `artifacts/attic_eviction_candidates.csv`
- `.github/workflows/attic-dryrun.yml`
- `docs/cleanup/wave-2a.md`

### Baselines
- `artifacts/baseline/redundancy_report_baseline.csv`
- `artifacts/baseline/near_dupes_baseline.json`

### Updated Files
- `.github/workflows/cleanup-audit.yml` (enhanced gates)

## Next Steps

1. **Review eviction candidates** in `artifacts/attic_eviction_candidates.csv`
2. **Monitor weekly dry-runs** for new candidates
3. **Plan Wave-2b**: Controlled deletion after 1-2 weeks of monitoring
4. **Validate CI gates** are working correctly

## Branch Information
- **Branch**: `cleanup/wave-2a-safe`
- **Base**: `main`
- **Status**: Ready for PR

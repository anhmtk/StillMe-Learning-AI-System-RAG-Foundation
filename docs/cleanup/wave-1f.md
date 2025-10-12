# Cleanup Wave-1f Report

This document summarizes the activities and outcomes of Cleanup Wave-1f for the StillMe project. The primary objectives for this wave included near-duplicate consolidation with compatibility shims, CI guards implementation, and controlled quarantine.

## **PREREQUISITE: PR Check**

**Wave-1d PR:**
- **URL:** https://github.com/anhmtk/stillme_ai_ipc/pull/new/cleanup/wave-1d-safe
- **Status:** Manual PR creation required

**Wave-1e PR:**
- **URL:** https://github.com/anhmtk/stillme_ai_ipc/pull/new/cleanup/wave-1e-safe
- **Status:** Manual PR creation required

---

## **PHASE 0: PR CHECK & PLAN**

### **Current State Analysis**
- **Near-duplicate clusters available:** 31 (from artifacts/near_dupes.json)
- **Files analyzed:** 798 (from artifacts/redundancy_report.csv)
- **High-risk files:** 506 (score ≥ 70)
- **Tracked files:** Available for analysis
- **Attic files:** Available for read-only analysis

### **Strategy**
1. **Near-dupe pilot selection:** Choose 10-20 clear clusters with canonical files
2. **Compatibility shims:** Create `stillme_compat/` with deprecation warnings
3. **Import rewrite:** Update tracked files to use canonical imports
4. **CI guards:** Implement gates to prevent future redundancy
5. **Controlled quarantine:** Move only near-dupe unused/backup files

---

## **PHASE 1: NEAR-DUPE PILOT**

- **Objective**: Select suitable near-duplicate clusters for consolidation
- **Approach**: 
  - Load existing near-dupes data
  - Filter clusters with canonical files (inbound > 0 or executed > 0)
  - Accept clusters where all non-canonical files are unused
  - Include both tracked and attic files in analysis

## **PHASE 2: ALIAS SHIM & IMPORT REWRITE**

- **Objective**: Create compatibility shims and rewrite imports to canonical files
- **Approach**:
  - Create `stillme_compat/` package structure
  - Generate shim modules with deprecation warnings
  - Rewrite imports in tracked files to point to canonical files
  - Log all changes for review

## **PHASE 3: RESCORE & QUARANTINE**

- **Objective**: Recalculate scores and perform controlled quarantine
- **Approach**:
  - Run full analysis pipeline
  - Apply dual scoring: 70 for general, 60 for near-dupe/backup
  - Move only files meeting relaxed criteria

## **PHASE 4: CI GUARDS & BASELINES**

- **Objective**: Implement CI gates and create baselines
- **Approach**:
  - Create baseline files for future comparisons
  - Update CI workflow with redundancy gates
  - Add warnings for new unused near-duplicates

## **PHASE 5: BRANCH & PR**

- **Objective**: Create clean branch and PR with clear diff
- **Approach**:
  - Commit changes in logical groups
  - Push branch and create PR
  - Document all changes and rollback procedures

## **Safety Measures**

- `ALWAYS_PROTECT_PATHS` and `ALWAYS_PROTECT_FILENAMES` are respected
- All import rewrites have compatibility shims
- Deprecation warnings for old import paths
- Rollback capability maintained
- Tracked files only for quarantine

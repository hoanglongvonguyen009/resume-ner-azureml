# Plan: Migrate HPO Hash Computation to v2 (Always)

## Overview

Migrate all HPO hash computations from v1 to v2 to ensure consistency across trial runs, refit runs, and parent runs. This fixes the checkpoint acquisition issue where refit runs cannot be linked to trial runs due to hash mismatches.

## Problem Statement

**Current Issue:**
- Parent runs use v2 `study_key_hash` (via `_set_phase2_hpo_tags`)
- Trial runs compute v1 `study_key_hash` (in `cv.py`)
- Refit runs compute v1 `study_key_hash` (in `sweep.py`)
- Result: Hash mismatches prevent linking refit runs to trial runs

**Root Cause:**
- Conditional v2 computation (only when fingerprints available)
- Inconsistent hash computation across different run types
- Missing explicit refit linkage tags

## Solution: Always Compute v2

### Core Principle: Single Source of Truth

1. **Parent run tags are source of truth** - If `grouping.study_key_hash` exists on parent, use it
2. **Always compute v2** - Never conditional; fingerprint functions have fallbacks
3. **Explicit linking** - Use `refit.of_trial_run_id` tag for deterministic mapping

### Fallback Hierarchy

```
1. Get from parent run tag (if exists) → use it
2. Compute v2 (always succeeds - fingerprints have fallbacks)
3. Fallback to v1 (only if v2 computation truly impossible - rare)
```

## Implementation Tasks

### Task 1: Update Trial Run Creation (`cv.py`)

**File:** `src/training/hpo/execution/local/cv.py`

**Location:** Lines ~113-134 (study_key_hash computation)

**Changes:**
1. Remove conditional v1 computation
2. Always compute v2 `study_key_hash` using fingerprints
3. Ensure fingerprints always return a value (use fallbacks)
4. Set tags on trial run:
   - `process.stage = hpo_trial`
   - `grouping.study_key_hash = <v2>`
   - `grouping.trial_key_hash = <computed>`
   - `fingerprint.data = <computed>`
   - `fingerprint.eval = <computed>`

**Code Pattern:**
```python
# Always compute v2 (fingerprints have fallbacks)
from infrastructure.tracking.mlflow.naming import (
    build_hpo_study_key_v2,
    build_hpo_study_key_hash,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)

# Compute fingerprints (always succeeds - has fallbacks)
# Handle None configs by passing empty dict
data_fp = compute_data_fingerprint(data_config or {})
eval_config = train_config.get("eval", {}) or hpo_config.get("evaluation", {}) or {}
eval_fp = compute_eval_fingerprint(eval_config)

# Always compute v2 (fingerprints always return strings)
if data_config and hpo_config and train_config:
    study_key_v2 = build_hpo_study_key_v2(
        data_config=data_config,
        hpo_config=hpo_config,
        train_config=train_config,
        model=backbone,
        data_fingerprint=data_fp,  # Always a string (never None)
        eval_fingerprint=eval_fp,  # Always a string (never None)
    )
    computed_study_key_hash = build_hpo_study_key_hash(study_key_v2)
```

**Dependencies:**
- Ensure `compute_data_fingerprint` and `compute_eval_fingerprint` always return a value (check implementation)

---

### Task 2: Update Early Study Key Computation (`sweep.py`)

**File:** `src/training/hpo/execution/local/sweep.py`

**Location:** Lines ~619-636 (early study_key_hash computation)

**Changes:**
1. Replace v1 computation with v2
2. Use same pattern as `_set_phase2_hpo_tags`
3. Ensure consistency with parent run tagging

**Code Pattern:**
```python
# Replace build_hpo_study_key with build_hpo_study_key_v2
from infrastructure.tracking.mlflow.naming import (
    build_hpo_study_key_v2,  # Changed
    build_hpo_study_key_hash,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)

# Compute fingerprints (always succeeds - handle None configs)
data_fp = compute_data_fingerprint(data_config or {})
eval_config = train_config.get("eval", {}) or hpo_config.get("evaluation", {}) or {}
eval_fp = compute_eval_fingerprint(eval_config)

# Always compute v2 (fingerprints always return values)
if data_config and hpo_config and train_config:
    study_key_v2 = build_hpo_study_key_v2(
        data_config=data_config,
        hpo_config=hpo_config,
        train_config=train_config,
        model=backbone,
        data_fingerprint=data_fp,  # Always a string (never None)
        eval_fingerprint=eval_fp,  # Always a string (never None)
    )
    study_key_hash = build_hpo_study_key_hash(study_key_v2)
```

---

### Task 3: Update Refit Study Key Computation (`sweep.py`)

**File:** `src/training/hpo/execution/local/sweep.py`

**Location:** Lines ~1056-1130 (refit study_key_hash computation)

**Changes:**
1. Replace v1 computation with v2
2. Use parent run's v2 hash as source of truth (already implemented, but ensure it's used)
3. Ensure refit run gets same v2 hash as trial runs

**Code Pattern:**
```python
# Replace build_hpo_study_key with build_hpo_study_key_v2
from infrastructure.tracking.mlflow.naming import (
    build_hpo_study_key_v2,  # Changed
    build_hpo_study_family_key,  # Keep v1 for now (family doesn't need v2)
    build_hpo_study_key_hash,
    build_hpo_study_family_hash,
    compute_data_fingerprint,
    compute_eval_fingerprint,
)

# Primary: Get from parent run (source of truth)
if parent_run_id:
    parent_run = client.get_run(parent_run_id)
    refit_study_key_hash = parent_run.data.tags.get("code.study_key_hash")
    if refit_study_key_hash:
        # Use parent's hash (already v2 for new runs)
        logger.debug(f"[REFIT] Using study_key_hash from parent: {refit_study_key_hash[:16]}...")
    else:
        # Compute v2 if not available (fingerprints always return values)
        data_fp = compute_data_fingerprint(data_config or {})
        eval_config = train_config.get("eval", {}) or hpo_config.get("evaluation", {}) or {}
        eval_fp = compute_eval_fingerprint(eval_config)
        
        if data_config and hpo_config and train_config:
            study_key_v2 = build_hpo_study_key_v2(
                data_config=data_config,
                hpo_config=hpo_config,
                train_config=train_config,
                model=backbone,
                data_fingerprint=data_fp,  # Always a string
                eval_fingerprint=eval_fp,  # Always a string
            )
            refit_study_key_hash = build_hpo_study_key_hash(study_key_v2)
```

**Critical:** Use parent run's v2 hash for `trial_key_hash` computation.

**Current behavior (from logs):**
- Refit currently logs:
  - `Computed trial_key_hash=d58f7ba0... from study_key_hash=712fbee8...` (and similarly `3c31765d...` from `87caa65a...`)
  - Here `712fbee8` / `87caa65a` come from the **disk study folder name** (`study-712fbee8`, `study-87caa65a`), not from the parent run's v2 `code.study_key_hash` (`584922ce...`, `25cad2a2...`).
- This means refit `trial_key_hash` is still anchored to the legacy/v1-ish study hash, not the v2 parent hash.

**Required fix:**
1. Read `refit_study_key_hash` **only** from the parent run tag (`code.study_key_hash`) for new runs.
2. Use that v2 `refit_study_key_hash` as the **study component** when building `trial_key_hash` for refit.
3. For backwards compatibility:
   - If parent is missing `code.study_key_hash` (old runs), compute v2 in-place as above and set it on the refit (and optionally on the parent) before computing `trial_key_hash`.
4. After this change, logs should read:
   - `Computed trial_key_hash=... from study_key_hash=584922ce...` (matching parent), not from `712fbee8...`.

---

### Task 4: Verify Fingerprint Functions Always Return Values

**Files to Check:**
- `src/infrastructure/naming/mlflow/hpo_keys.py`
  - `compute_data_fingerprint()` - Lines 274-305
  - `compute_eval_fingerprint()` - Lines 308-327

**Verification:**
- Ensure `compute_data_fingerprint` always returns a hash (has fallback to semantic fields)
- Ensure `compute_eval_fingerprint` always returns a hash (has fallback to default config)
- If either can return `None`, update to return empty string or default hash

**Action:**
- ✅ Verified: `compute_data_fingerprint` always returns (has semantic fallback)
- ✅ Verified: `compute_eval_fingerprint` always returns (uses defaults)
- ⚠️  **Edge Case:** Both functions expect `Dict[str, Any]`, not `None`
  - If `data_config` is `None`, pass `{}` instead
  - If `eval_config` is `None`, pass `{}` instead
  - Update calling code to handle `None` → `{}` conversion

---

### Task 5: Ensure Refit Linking Tag is Set

**File:** `src/training/hpo/execution/local/refit.py`

**Status:** Already implemented (`_link_refit_to_trial_run`)

**Verification:**
- Ensure `refit.of_trial_run_id` tag is set on refit runs
- Ensure it's called both immediately after run creation and after training
- Verify tag key is correct: `code.refit.of_trial_run_id`

**Action:**
- Test that linking works once hashes match
- Add logging to confirm tag is set
- Verify tag appears in MLflow UI

**Note:** With v2 hashes in place, refit linking remains tag-based and deterministic:
- Trials and refits share the same v2 `study_key_hash` + `trial_key_hash`.
- `refit.of_trial_run_id` continues to be the primary mapping key.

---

### Task 6: Update Checkpoint Acquisition to Use Refit Run

**Files:** 
- `src/evaluation/selection/trial_finder.py`
- `src/evaluation/selection/artifact_acquisition.py`

**Status:** Implemented (deterministic refit-first, no trial fallback)

**Current behavior:**
1. **Selection (`trial_finder.select_champion_per_backbone`):**
   - After selecting the champion **trial** (by CV metric), resolves the **refit run** deterministically:
     - First by `refit.of_trial_run_id` tag (`code.refit.of_trial_run_id`)
     - Fallback by matching `grouping.trial_key_hash` within `stage == hpo_refit`
     - If no refit run is found, it **fails fast** (raises) instead of falling back to trial runs.
   - Returns both `trial_run_id` and `refit_run_id` in the `champion` payload, with `run_id` pointing to the refit run for backward compatibility.
2. **Acquisition (`acquire_best_model_checkpoint`):**
   - **Requires** `refit_run_id` in `best_run_info` and raises if it is missing.
   - Uses only the resolved `refit_run_id` for MLflow artifact download (no search, no trial fallback).
   - Validates `code.artifact.available` (`artifact.available` tag) on the refit run and fails if it is not `true` before attempting download.
   - Local/disk/Drive lookup continues to use `study_key_hash` + `trial_key_hash` as the single source of truth for paths.

**Verification:**
- Ensure `select_champion_per_backbone` always resolves `refit_run_id` or fails fast.
- Ensure `acquire_best_model_checkpoint`:
  - Requires `refit_run_id` and never silently uses trial runs.
  - Only downloads checkpoints from the resolved refit run.
  - Enforces `artifact.available=true` on the refit run before download.
- Confirm behavior via:
  - Integration tests (hash consistency + selection + acquisition).
  - Manual runs where refit is missing or artifact is not uploaded (should fail fast with clear errors).

**Action:**
- ✅ Implementation updated to deterministic refit-first behavior.
- ⏳ Wire end-to-end tests once Tasks 1–3 (v2 hashes everywhere) are completed, then re-run `verify_hash_consistency.py` and champion-selection/benchmarking flows.

---

### Task 8 (Optional but Recommended): Clean Up Legacy Warnings

**Files:**
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py`
- `src/training/hpo/trial/metrics.py`

**Motivation (from logs):**
- `LOG_FINAL_METRICS` warns:
  - “No child runs found for parent … This may indicate: (1) runs haven't been created yet, (2) runs are not direct children of parent, or (3) search filter is incorrect”
  - This happens because HPO trials live in separate experiments / parent chains.
- `training.hpo.trial.metrics` warns:
  - “Could not find v2 trial folder for trial 0 in v2 study folder study-584922ce. Available folders: N/A”
  - This is a side effect of mixing disk `study-712fbee8` paths with v2 `study_key_hash=584922ce...`.

**Changes:**
1. **LOG_FINAL_METRICS child run discovery**
   - Prefer tag-based search (e.g., `tags.code.lineage.hpo_sweep_run_id = <parent_run_id>` or `tags.code.study_key_hash = <parent_study_key_hash>`) instead of only relying on `mlflow.parentRunId`.
   - If no runs are found, downgrade the message to “info” and include explicit explanation about cross-experiment layouts instead of suggesting timing issues.
2. **Trial metrics writer**
   - After Tasks 1–3, ensure disk study folder names are aligned with v2 `study_key_hash`:
     - `outputs/hpo/.../study-<study_key_hash[:8]>` should match `code.study_key_hash`.
   - Once aligned, remove or greatly reduce the “Could not find v2 trial folder…” warning; treat missing folders as genuine exceptional cases (e.g., disk cleanup).

**Goal:**
- Eliminate confusing legacy warnings so logs reflect the intentional design:
  - v2 hashes everywhere.
  - Trials/refits grouped by v2 `study_key_hash`.
  - Deterministic linking and acquisition from refit runs.
---

### Task 7: Add Hash Consistency Tests

**Files Created:**
- `tests/training/hpo/integration/test_hash_consistency.py` - Automated tests
- `tests/training/hpo/scripts/verify_hash_consistency.py` - Manual verification script
- `tests/training/hpo/scripts/README.md` - Documentation

**Tests Added:**
1. ✅ V2 hash computation always succeeds
2. ✅ Fingerprint functions handle None/empty configs
3. ✅ Trial key hash consistency with same study key hash
4. ✅ Hash mismatch detection (different configs = different hashes)
5. ✅ Parent run v2 tag setting
6. ✅ Parent vs trial hash mismatch detection
7. ✅ Deterministic v2 hash computation (same inputs = same hash)

**Verification Script:**
- Checks existing MLflow runs for hash consistency
- Detects parent vs trial hash mismatches
- Verifies refit linking tags
- Provides detailed reporting

**Action:**
- ✅ Tests created
- ✅ Script created
- Run tests after implementation to verify fixes

---

## Testing Strategy

### Automated Tests

**Unit Tests** (`tests/training/hpo/integration/test_hash_consistency.py`):
1. ✅ Test v2 hash computation always succeeds
2. ✅ Test fingerprint functions always return values (handle None/empty configs)
3. ✅ Test trial_key_hash consistency with same study_key_hash
4. ✅ Test hash mismatch detection (different configs produce different hashes)
5. ✅ Test parent run v2 tag setting
6. ✅ Test refit linking tag format

**Integration Tests:**
1. Run HPO with v2 hashes
2. Verify trial runs have v2 `study_key_hash`
3. Verify refit runs have matching v2 `study_key_hash`
4. Verify `refit.of_trial_run_id` tag is set
5. Verify checkpoint acquisition finds refit run

### Manual Verification Script

**Script:** `tests/training/hpo/scripts/verify_hash_consistency.py`

**Usage:**
```bash
# Check specific parent run
python tests/training/hpo/scripts/verify_hash_consistency.py \
    --experiment-name "resume_ner_baseline-hpo-distilbert" \
    --parent-run-id "abc123..."

# Check all runs in experiment
python tests/training/hpo/scripts/verify_hash_consistency.py \
    --experiment-name "resume_ner_baseline-hpo-distilbert" \
    --check-all
```

**What it verifies:**
1. ✅ Parent runs have v2 `study_key_hash` tags (with fingerprints)
2. ✅ Trial runs have matching `study_key_hash` as parent
3. ✅ Refit runs have matching `study_key_hash` as parent
4. ✅ Refit runs have `refit.of_trial_run_id` linking tag
5. ✅ All hashes are consistent across run types

**Output:**
- Summary statistics
- List of issues found (if any)
- Detailed breakdown of parent/trial/refit runs
- Exit code 1 if issues found, 0 if all good

### Manual Verification Steps
1. Run verification script after HPO completes
2. Check MLflow UI for tags on trial/refit runs
3. Verify hashes match between trial and refit
4. Test champion selection finds refit runs
5. Test checkpoint acquisition from refit runs

---

## Migration Considerations

### Backward Compatibility

**Existing Runs (v1 hashes):**
- Old trial runs will have v1 `study_key_hash`
- New trial runs will have v2 `study_key_hash`
- Selection code should handle both (already does via fallback)

**Mixed Environments:**
- Parent run may have v2 hash (from Phase 2 tags)
- Trial runs will now also have v2 hash (after this change)
- Refit runs will use parent's v2 hash (already implemented)

**No Breaking Changes:**
- Selection code already handles missing/mismatched hashes
- Fallback to trial number/name pattern exists
- Checkpoint acquisition has multiple strategies

---

## Implementation Order

1. **Task 4** - Verify fingerprint functions (foundation)
2. **Task 7** - Add hash consistency tests (verify before/after) ✅ **DONE**
3. **Task 1** - Update trial run creation (most critical)
4. **Task 2** - Update early computation (consistency)
5. **Task 3** - Update refit computation (already mostly done, just ensure v2)
6. **Task 5** - Verify refit linking (should work once hashes match)
7. **Task 6** - Verify checkpoint acquisition (should work once linking works)
8. **Task 7** - Run verification script to confirm fixes

---

## Success Criteria

✅ All trial runs have v2 `study_key_hash` tag
✅ All refit runs have matching v2 `study_key_hash` tag
✅ `refit.of_trial_run_id` tag is set on all refit runs
✅ Champion selection can find refit runs via linking tag
✅ Checkpoint acquisition successfully downloads from refit runs
✅ No regression in existing functionality

---

## Notes

- **Single Source of Truth:** Parent run tags are authoritative
- **Always v2:** No conditional computation - fingerprints have fallbacks
- **Explicit Linking:** `refit.of_trial_run_id` tag provides deterministic mapping
- **Backward Compatible:** Old runs still work via fallback strategies


# Unify Checkpoint Upload Consistency Across All Stages

## Overview

This plan addresses the inconsistency in checkpoint upload methods across different stages:
- **HPO**: Creates tar.gz archive (6 files → 1 archive) using `create_checkpoint_archive()` + `upload_checkpoint_archive()`
- **Training**: Uploads directory directly (6 files individually) using `log_artifacts_safe()`

**Goal**: Unify all checkpoint uploads to use the archive approach consistently, remove redundant logic, and follow DRY principles.

## Current State Analysis

### Checkpoint Upload Methods by Stage

1. **HPO (sweep_tracker.py)**
   - Location: `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py`
   - Method: Direct calls to `create_checkpoint_archive()` + `upload_checkpoint_archive()`
   - Usage: 2 locations (lines ~895, ~1048)
   - Artifact path: `"best_trial_checkpoint.tar.gz"`

2. **Training (stage_helpers.py)**
   - Location: `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py`
   - Method: `uploader.upload_checkpoint()` → `log_artifacts_safe()` (direct directory)
   - Usage: `upload_training_artifacts()` function
   - Artifact path: `"checkpoint"` (directory)

3. **HPO Helper (stage_helpers.py)**
   - Location: `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py`
   - Method: `uploader.upload_checkpoint_archive()` (takes pre-created archive)
   - Usage: `upload_hpo_artifacts()` function
   - Note: Requires archive to be created externally

4. **Benchmark/Conversion Trackers**
   - Status: Import `create_checkpoint_archive` but **never use it** (unused imports)

### Redundant Code Identified

1. **Direct archive creation in HPO**: `sweep_tracker.py` manually creates archives instead of using `ArtifactUploader`
2. **Unused imports**: `benchmark_tracker.py`, `training_tracker.py`, `conversion_tracker.py` import `create_checkpoint_archive` but don't use it
3. **Dual upload methods**: `upload_checkpoint()` and `upload_checkpoint_archive()` serve similar purposes
4. **HPO helper redundancy**: `upload_hpo_artifacts()` requires external archive creation, duplicating logic

## Proposed Solution

### Core Principle: Archive-First Approach

All checkpoint uploads should:
1. Create a tar.gz archive automatically
2. Include manifest metadata (file count, sizes, trial number)
3. Upload as a single compressed file
4. Use consistent artifact paths

### Unified API Design

**Primary Method**: `ArtifactUploader.upload_checkpoint()`
- **Default behavior**: Create archive automatically
- **Parameters**:
  - `checkpoint_dir`: Path to checkpoint directory
  - `artifact_path`: Artifact path (default: `"checkpoint.tar.gz"` or `"best_trial_checkpoint.tar.gz"`)
  - `trial_number`: Optional trial number for manifest (default: 0)
  - `skip_if_disabled`: Skip when tracking disabled (default: True)

**Secondary Method**: `ArtifactUploader.upload_checkpoint_archive()` (for edge cases)
- Keep for scenarios where archive is pre-created externally
- Mark as deprecated/internal use only

## Implementation Plan

### Phase 1: Update ArtifactUploader Core Logic

#### 1.1 Modify `upload_checkpoint()` to Create Archives by Default

**File**: `src/infrastructure/tracking/mlflow/artifacts/uploader.py`

**Changes**:
- Import `create_checkpoint_archive` from `manager.py`
- Update `upload_checkpoint()` to:
  1. Create archive using `create_checkpoint_archive()`
  2. Upload archive using `upload_checkpoint_archive()`
  3. Clean up temp archive file after upload
  4. Handle `trial_number` parameter for manifest metadata
  5. Auto-append `.tar.gz` to artifact_path if not present

**New Signature**:
```python
def upload_checkpoint(
    self,
    checkpoint_dir: Path,
    artifact_path: str = "checkpoint.tar.gz",
    trial_number: Optional[int] = None,
    skip_if_disabled: bool = True,
) -> bool:
```

**Benefits**:
- Single method handles all checkpoint uploads
- Consistent archive creation across all stages
- Automatic manifest generation
- Cleaner API surface

#### 1.2 Update Method Documentation

- Document archive-first approach
- Explain manifest metadata
- Note compression benefits
- Update examples

### Phase 2: Refactor HPO to Use Unified Method

#### 2.1 Update `sweep_tracker.py`

**File**: `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py`

**Changes**:
- Remove direct calls to `create_checkpoint_archive()` (2 locations)
- Replace with `ArtifactUploader.upload_checkpoint()`
- Remove `create_checkpoint_archive` import (no longer needed)
- Update artifact paths to use consistent naming

**Before**:
```python
archive_path, manifest = create_checkpoint_archive(
    checkpoint_dir, best_trial_number
)
artifact_logged = upload_checkpoint_archive(
    archive_path=archive_path,
    manifest=manifest,
    artifact_path="best_trial_checkpoint.tar.gz",
    run_id=None,
    max_retries=5,
    base_delay=2.0,
    cleanup_on_failure=False,
)
```

**After**:
```python
uploader = ArtifactUploader(
    run_id=None,  # Use active run
    stage="hpo",
    config_dir=config_dir,
)
artifact_logged = uploader.upload_checkpoint(
    checkpoint_dir=checkpoint_dir,
    artifact_path="best_trial_checkpoint.tar.gz",
    trial_number=best_trial_number,
)
```

**Locations to Update**:
1. `_log_best_trial_checkpoint()` method (~line 895)
2. `_upload_best_trial_checkpoint()` method (~line 1048)

#### 2.2 Simplify `upload_hpo_artifacts()` Helper

**File**: `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py`

**Changes**:
- Option A: Update to accept `checkpoint_dir` instead of `archive_path`
- Option B: Keep as-is but mark for deprecation
- **Recommendation**: Option A - make it consistent with other stage helpers

**New Signature**:
```python
def upload_hpo_artifacts(
    checkpoint_dir: Path,
    trial_number: int,
    run_id: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> bool:
```

### Phase 3: Update Training Stage

#### 3.1 Update `upload_training_artifacts()`

**File**: `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py`

**Changes**:
- No code changes needed! `uploader.upload_checkpoint()` will now create archives automatically
- Update artifact path from `"checkpoint"` to `"checkpoint.tar.gz"` for clarity
- Update documentation to reflect archive behavior

**Impact**:
- Training checkpoints will now be uploaded as `checkpoint.tar.gz` (consistent with HPO)
- Automatic manifest generation
- Compression benefits

### Phase 4: Clean Up Unused Code

#### 4.1 Remove Unused Imports

**Files to Update**:
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py`
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py`
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py`

**Action**: Remove `from infrastructure.tracking.mlflow.artifacts.manager import create_checkpoint_archive`

#### 4.2 Consider Deprecating `upload_checkpoint_archive()`

**Decision Point**: Keep for edge cases or remove entirely?

**Recommendation**: Keep but mark as internal/deprecated
- Some edge cases may need pre-created archives
- Internal use only (not exported in public API)
- Document as "advanced use only"

### Phase 5: Update Documentation

#### 5.1 Update ArtifactUploader README

**File**: `src/infrastructure/tracking/mlflow/artifacts/README.md`

**Changes**:
- Update examples to show archive-first approach
- Document `trial_number` parameter
- Explain manifest metadata
- Show consistency across stages

#### 5.2 Update Stage Helper Documentation

**Changes**:
- Document that all checkpoint uploads create archives
- Update examples
- Note compression and manifest benefits

## Migration Checklist

### Code Changes

- [ ] **Phase 1.1**: Update `ArtifactUploader.upload_checkpoint()` to create archives
- [ ] **Phase 1.2**: Update method documentation
- [ ] **Phase 2.1**: Refactor `sweep_tracker.py` to use `ArtifactUploader`
- [ ] **Phase 2.2**: Simplify `upload_hpo_artifacts()` helper
- [ ] **Phase 3.1**: Update `upload_training_artifacts()` artifact path
- [ ] **Phase 4.1**: Remove unused `create_checkpoint_archive` imports
- [ ] **Phase 4.2**: Mark `upload_checkpoint_archive()` as internal/deprecated
- [ ] **Phase 5.1**: Update README documentation
- [ ] **Phase 5.2**: Update stage helper documentation

### Testing

- [ ] **Unit Tests**: Test `upload_checkpoint()` archive creation
- [ ] **Integration Tests**: Test HPO checkpoint upload via `ArtifactUploader`
- [ ] **Integration Tests**: Test training checkpoint upload (verify archive creation)
- [ ] **Regression Tests**: Verify existing functionality still works
- [ ] **Edge Cases**: Test with missing checkpoints, disabled tracking, etc.

### Validation

- [ ] **HPO**: Verify checkpoints upload as `best_trial_checkpoint.tar.gz` with manifest
- [ ] **Training**: Verify checkpoints upload as `checkpoint.tar.gz` with manifest
- [ ] **Consistency**: Verify both stages use same archive format and manifest structure
- [ ] **Performance**: Verify compression reduces upload size and time
- [ ] **Cleanup**: Verify temp archive files are cleaned up after upload

## Benefits

### Consistency
- ✅ All stages use same archive approach
- ✅ Unified artifact paths (`.tar.gz` extension)
- ✅ Consistent manifest metadata

### Efficiency
- ✅ Compression reduces upload size
- ✅ Single file upload (faster, more reliable)
- ✅ Reduced network overhead

### Maintainability
- ✅ Single code path for checkpoint uploads
- ✅ DRY principle: no duplicate archive creation logic
- ✅ Easier to test and debug
- ✅ Centralized error handling

### Metadata
- ✅ Automatic manifest generation
- ✅ File count and size tracking
- ✅ Trial number tracking (for HPO)
- ✅ Timestamp information

## Risks and Mitigation

### Risk 1: Breaking Changes
**Risk**: Existing code expecting directory uploads may break
**Mitigation**: 
- Archive approach is transparent to consumers
- Artifact paths remain similar (just add `.tar.gz`)
- Test thoroughly before deployment

### Risk 2: Temp File Cleanup
**Risk**: Temp archive files may not be cleaned up properly
**Mitigation**:
- Use context managers or try/finally blocks
- Test cleanup in all scenarios
- Add logging for temp file creation/deletion

### Risk 3: Archive Creation Failures
**Risk**: Archive creation may fail, blocking upload
**Mitigation**:
- Add proper error handling
- Log detailed error messages
- Consider fallback to direct upload (if needed)

## Rollout Strategy

1. **Development**: Implement changes in feature branch
2. **Testing**: Run full test suite, verify all stages
3. **Code Review**: Review for consistency and DRY compliance
4. **Staging**: Test in staging environment
5. **Production**: Deploy with monitoring

## Success Criteria

- ✅ All checkpoint uploads create archives consistently
- ✅ No duplicate archive creation logic
- ✅ All unused imports removed
- ✅ All tests pass
- ✅ Documentation updated
- ✅ HPO and Training use same upload method
- ✅ Manifest metadata present in all checkpoints

## Open Questions

1. **Q**: Should we keep `upload_checkpoint_archive()` for edge cases?
   **A**: Yes, but mark as internal/deprecated

2. **Q**: What artifact path naming convention?
   **A**: 
   - Training: `checkpoint.tar.gz`
   - HPO: `best_trial_checkpoint.tar.gz`
   - Benchmark: `benchmark_checkpoint.tar.gz` (if needed)

3. **Q**: Should `trial_number` be required for HPO?
   **A**: Yes, it's essential for manifest metadata

4. **Q**: Fallback to direct upload if archive creation fails?
   **A**: No, fail fast with clear error message (archive creation should be reliable)

## Related Files

### Core Files
- `src/infrastructure/tracking/mlflow/artifacts/uploader.py` - Main implementation
- `src/infrastructure/tracking/mlflow/artifacts/stage_helpers.py` - Stage helpers
- `src/infrastructure/tracking/mlflow/artifacts/manager.py` - Archive creation
- `src/infrastructure/tracking/mlflow/artifacts.py` - Safe upload utilities

### Tracker Files
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - HPO tracker
- `src/infrastructure/tracking/mlflow/trackers/training_tracker.py` - Training tracker
- `src/infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` - Benchmark tracker
- `src/infrastructure/tracking/mlflow/trackers/conversion_tracker.py` - Conversion tracker

### Documentation
- `src/infrastructure/tracking/mlflow/artifacts/README.md` - Artifact upload docs

## Notes

- This plan follows DRY principles by consolidating all checkpoint upload logic
- Archive approach is more efficient and provides better metadata
- Changes are backward compatible (artifact paths just get `.tar.gz` extension)
- All stages benefit from compression and manifest metadata


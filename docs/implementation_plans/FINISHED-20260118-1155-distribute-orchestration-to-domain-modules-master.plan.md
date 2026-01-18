# Distribute Orchestration to Domain Modules - Master Plan

## Goal

Eliminate the `orchestration` module by distributing its functionality to domain modules:
1. Move AzureML job creation to respective domains (training, deployment)
2. Move shared utilities to infrastructure/common
3. Move MLflow indexing to infrastructure
4. Update all imports across codebase (~40-50 Python imports + documentation references)
5. Delete orchestration module entirely

This reorganization aligns with the "big modules" architecture where each domain is self-contained.

## Status

**Last Updated**: 2026-01-18

**Phase 1 (File Moves) Status**: ✅ Complete (Steps 1-7)
**Phase 2 (Import Updates) Status**: ✅ Complete (Steps 8-13)
**Phase 3 (Cleanup) Status**: ✅ Complete (Steps 14-15)

### Completed Steps
- ✅ Step 1: Create new directory structure
- ✅ Step 2: Move training AzureML jobs
- ✅ Step 3: Move HPO AzureML sweeps
- ✅ Step 4: Move conversion AzureML jobs
- ✅ Step 5: Move AzureML runtime utilities
- ✅ Step 6: Move shared backup utilities
- ✅ Step 7: Move MLflow indexing
- ✅ Step 8: Handle local_selection_v2.py
- ✅ Step 9: Update all imports - Training domain
- ✅ Step 10: Update all imports - Conversion domain
- ✅ Step 11: Update all imports - Runtime
- ✅ Step 12: Update all imports - Backup utilities
- ✅ Step 13: Update all imports - MLflow indexing
- ✅ Step 14: Remove deprecated compatibility layers
- ✅ Step 15: Delete orchestration module
- ✅ Step 16: Update documentation
- ✅ Step 17: Verify tests and type checking (import errors fixed, test structure updated)

### Pending Steps
- ⏳ All steps pending

## Preconditions

- All existing tests must pass before starting: `uvx pytest tests/`
- Mypy must pass: `uvx mypy src --show-error-codes`
- No active PRs that would conflict with these changes
- Backup of current state (git commit before starting)
- Understanding that this is a **breaking change** requiring import updates across codebase
- **Recommended**: Create a feature branch for this work: `git checkout -b refactor/distribute-orchestration`

## Execution Order Recommendation

**Phase 1: Move files (Steps 1-8)**
- Move files in dependency order: dependencies first, dependents later
- Suggested order: Index → Runtime → Backup → Training → HPO → Conversion → Selection
- Verify each move works before proceeding
- Run mypy after each move to catch import errors early

**Phase 2: Update imports (Steps 9-13)**
- Update imports domain by domain
- Run mypy after each domain to catch errors early
- Update tests alongside source files

**Phase 3: Cleanup and verify (Steps 14-17)**
- Remove deprecated layers
- Final verification before deletion
- Delete orchestration module
- Update documentation

## Analysis Summary

### Current Structure Issues

#### 1. Orchestration Module Contains Mixed Concerns

| Component | Current Location | Issue |
|-----------|-----------------|-------|
| Training AzureML jobs | `orchestration/jobs/training.py` | Should be in training domain |
| HPO AzureML sweeps | `orchestration/jobs/hpo/azureml/sweeps.py` | Should be in training domain (HPO is part of training) |
| Duplicate sweeps file | `orchestration/jobs/sweeps.py` | Duplicate of `hpo/azureml/sweeps.py`, should be deleted |
| Conversion AzureML jobs | `orchestration/jobs/conversion.py` | Should be in deployment domain |
| Conversion backward compat | `orchestration/jobs/conversion/__init__.py` | Backward compat wrapper, should be removed |
| AzureML runtime | `orchestration/jobs/runtime.py` | Should be in infrastructure |
| Shared backup utilities | `orchestration/jobs/hpo/local/backup.py` | Used by multiple domains, should be in infrastructure |
| MLflow indexing | `orchestration/jobs/tracking/index/` | Already used by infrastructure, should be in infrastructure |
| Selection logic | `orchestration/jobs/local_selection_v2.py` | Should be in evaluation domain (likely duplicate/wrapper) |

#### 2. Import Usage Analysis

Based on grep analysis, found **~40-50 import statements** from orchestration in Python files:
- Training domain: ~10 imports
- Infrastructure domain: ~6 imports
- Deployment domain: ~2 imports
- Evaluation domain: ~1 import
- Orchestration internal: ~4 files (will be moved/deleted)
- Documentation/READMEs: ~30+ references (not counted in import statements)
- Tests: ~5+ imports

**Note**: The original estimate of 134+ was likely including documentation references and multiple matches per file. Actual Python import statements are fewer but still require systematic updates.

#### 3. Deprecated Compatibility Layers to Remove

| File/Directory | Status | Replacement |
|----------------|--------|-------------|
| `orchestration/jobs/tracking/config/` | Deprecated wrapper | `infrastructure.naming.mlflow.config` |
| `orchestration/jobs/tracking/mlflow_config_loader.py` | Deprecated wrapper | `infrastructure.naming.mlflow.config` |
| `orchestration/jobs/tracking/mlflow_naming.py` | Backward compat re-export | `infrastructure.naming.mlflow.*` |
| `orchestration/jobs/tracking/mlflow_run_finder.py` | Backward compat re-export | `infrastructure.tracking.mlflow.finder` |
| `orchestration/jobs/tracking/mlflow_index.py` | Backward compat re-export | `infrastructure.tracking.mlflow.index` |
| `orchestration/jobs/tracking/mlflow_tracker.py` | Backward compat re-export | `infrastructure.tracking.mlflow.trackers.*` |
| `orchestration/jobs/tracking/artifact_manager.py` | Backward compat re-export | `infrastructure.tracking.mlflow.artifacts` |
| `orchestration/jobs/tracking/finder/` | Backward compat re-export | `infrastructure.tracking.mlflow.finder` |
| `orchestration/jobs/tracking/utils/` | Backward compat re-export | `infrastructure.tracking.mlflow.*` |
| `orchestration/jobs/tracking/trackers/` | Backward compat re-export | `infrastructure.tracking.mlflow.trackers.*` |
| `orchestration/jobs/tracking/artifacts/` | Backward compat re-export | `infrastructure.tracking.mlflow.artifacts` |
| `orchestration/jobs/conversion/__init__.py` | Backward compat alias | Direct import from `deployment.conversion.orchestration` |
| `orchestration/jobs/benchmarking/__init__.py` | Broken (non-existent import) | Remove entirely |
| `orchestration/jobs/sweeps.py` | Duplicate of `hpo/azureml/sweeps.py` | Remove (not imported anywhere) |

### Target Structure

```
src/
├── training/
│   ├── azureml/                    # NEW: AzureML job creation
│   │   ├── __init__.py
│   │   └── jobs.py                 # create_final_training_job()
│   └── hpo/
│       └── azureml/                # NEW: AzureML HPO sweeps
│           ├── __init__.py
│           └── sweeps.py           # create_hpo_sweep_job_for_backbone()
│
├── deployment/
│   └── conversion/
│       └── azureml/                # NEW: AzureML conversion jobs
│           ├── __init__.py
│           └── jobs.py             # create_conversion_job()
│
├── infrastructure/
│   ├── azureml/                    # NEW: AzureML runtime utilities
│   │   ├── __init__.py
│   │   └── runtime.py               # submit_and_wait_for_job()
│   ├── shared/                     # NEW: Shared cross-domain utilities
│   │   ├── __init__.py
│   │   └── backup.py                # immediate_backup_if_needed()
│   └── tracking/
│       └── mlflow/
│           └── index/               # NEW: MLflow indexing
│               ├── __init__.py
│               ├── run_index.py
│               ├── version_counter.py
│               └── file_locking.py
│
└── [orchestration/ DELETED]
```

### File Moves Summary

| From | To | Reason |
|------|-----|--------|
| `orchestration/jobs/training.py` | `training/azureml/jobs.py` | Training domain |
| `orchestration/jobs/hpo/azureml/sweeps.py` | `training/hpo/azureml/sweeps.py` | HPO is part of training (canonical location) |
| `orchestration/jobs/sweeps.py` | **DELETE** (duplicate of hpo/azureml/sweeps.py) | Duplicate - verify identical before deletion |
| `orchestration/jobs/conversion.py` | `deployment/conversion/azureml/jobs.py` | Conversion domain |
| `orchestration/jobs/runtime.py` | `infrastructure/azureml/runtime.py` | AzureML infrastructure |
| `orchestration/jobs/hpo/local/backup.py` | `infrastructure/shared/backup.py` | Shared utility |
| `orchestration/jobs/tracking/index/` (3 files) | `infrastructure/tracking/mlflow/index/` | MLflow infrastructure |
| `orchestration/jobs/local_selection_v2.py` | `evaluation/selection/local_selection_v2.py` | Selection logic (if not duplicate) |

## Steps

### Step 1: Create New Directory Structure

**Goal**: Create all new directories needed for the reorganization.

**Tasks**:
1. Check if `training/hpo/azureml/` already exists:
   ```bash
   test -d src/training/hpo/azureml && echo "EXISTS" || echo "NOT_EXISTS"
   ```
2. Create `training/azureml/` directory (if not exists)
3. Create `training/hpo/azureml/` directory (if not exists)
4. Create `deployment/conversion/azureml/` directory
5. Create `infrastructure/azureml/` directory
6. Create `infrastructure/shared/` directory
7. Create `infrastructure/tracking/mlflow/index/` directory (if not exists)
8. Create `__init__.py` files in each new directory (empty for now, will be populated in later steps)

**Success criteria**:
- All directories exist
- `__init__.py` files created in each directory

**Verification**:
```bash
# Verify all directories exist
test -d src/training/azureml && echo "✓ training/azureml exists"
test -d src/training/hpo/azureml && echo "✓ training/hpo/azureml exists"
test -d src/deployment/conversion/azureml && echo "✓ deployment/conversion/azureml exists"
test -d src/infrastructure/azureml && echo "✓ infrastructure/azureml exists"
test -d src/infrastructure/shared && echo "✓ infrastructure/shared exists"
test -d src/infrastructure/tracking/mlflow/index && echo "✓ infrastructure/tracking/mlflow/index exists"

# Verify __init__.py files exist
test -f src/training/azureml/__init__.py && echo "✓ training/azureml/__init__.py exists"
test -f src/training/hpo/azureml/__init__.py && echo "✓ training/hpo/azureml/__init__.py exists"
test -f src/deployment/conversion/azureml/__init__.py && echo "✓ deployment/conversion/azureml/__init__.py exists"
test -f src/infrastructure/azureml/__init__.py && echo "✓ infrastructure/azureml/__init__.py exists"
test -f src/infrastructure/shared/__init__.py && echo "✓ infrastructure/shared/__init__.py exists"
test -f src/infrastructure/tracking/mlflow/index/__init__.py && echo "✓ infrastructure/tracking/mlflow/index/__init__.py exists"
```

### Step 2: Move Training AzureML Jobs

**Goal**: Move training job creation to training domain.

**Tasks**:
1. **First, verify function names** in `orchestration/jobs/training.py`:
   ```bash
   grep "^def " src/orchestration/jobs/training.py
   ```
   Expected: `build_final_training_config`, `create_final_training_job`, `validate_final_training_job`
2. Move `orchestration/jobs/training.py` → `training/azureml/jobs.py`
3. Update imports in moved file:
   - Remove any `orchestration.jobs` references
   - Update relative imports if needed
   - Check for imports from `orchestration.jobs.runtime` → update to `infrastructure.azureml`
4. Update file metadata block:
   - Change `domain: orchestration` → `domain: training`
   - Update `tags` to remove `orchestration` tag
5. **Verify all functions exist** in moved file before creating `__init__.py`:
   ```bash
   grep "^def " src/training/azureml/jobs.py | grep -E "(build_final_training_config|create_final_training_job|validate_final_training_job)"
   ```
6. Create `training/azureml/__init__.py`:
   ```python
   from .jobs import (
       build_final_training_config,
       create_final_training_job,
       validate_final_training_job,
   )
   __all__ = [
       "build_final_training_config",
       "create_final_training_job",
       "validate_final_training_job",
   ]
   ```

**Success criteria**:
- File moved to `training/azureml/jobs.py`
- Imports in moved file updated (including any orchestration.jobs.runtime references)
- File metadata block updated (domain: training)
- All exported functions exist in moved file
- `__init__.py` exports functions correctly

**Verification**:
```bash
test -f src/training/azureml/jobs.py && echo "✓ File moved"
test -f src/training/azureml/__init__.py && echo "✓ __init__.py created"
grep -q "domain: training" src/training/azureml/jobs.py && echo "✓ Metadata updated"
python -c "from training.azureml import build_final_training_config, create_final_training_job, validate_final_training_job; print('✓ All imports work')"
```

### Step 3: Move HPO AzureML Sweeps

**Goal**: Move HPO sweep job creation to training domain (HPO is part of training).

**Tasks**:
1. **First, verify function names** in `orchestration/jobs/hpo/azureml/sweeps.py`:
   ```bash
   grep "^def " src/orchestration/jobs/hpo/azureml/sweeps.py
   ```
   Expected: `create_dry_run_sweep_job_for_backbone`, `create_hpo_sweep_job_for_backbone`, `validate_sweep_job`
2. **Verify duplicate**: Confirm that `orchestration/jobs/sweeps.py` is a duplicate of `orchestration/jobs/hpo/azureml/sweeps.py`:
   ```bash
   diff src/orchestration/jobs/sweeps.py src/orchestration/jobs/hpo/azureml/sweeps.py
   ```
   - Both files should contain the same functions
   - The canonical version is in `hpo/azureml/` (exported via `__init__.py`)
   - **Verified**: No imports reference `orchestration.jobs.sweeps` (grep found 0 matches)
3. Move `orchestration/jobs/hpo/azureml/sweeps.py` → `training/hpo/azureml/sweeps.py`
4. Update imports in moved file:
   - Remove any `orchestration.jobs` references
   - Update relative imports if needed
   - Check for imports from `orchestration.jobs.runtime` → update to `infrastructure.azureml`
5. Update file metadata block:
   - Change `domain: orchestration` → `domain: training`
   - Update `tags` to remove `orchestration` tag
6. **Verify all functions exist** in moved file before creating `__init__.py`:
   ```bash
   grep "^def " src/training/hpo/azureml/sweeps.py | grep -E "(create_dry_run_sweep_job_for_backbone|create_hpo_sweep_job_for_backbone|validate_sweep_job)"
   ```
7. Create `training/hpo/azureml/__init__.py`:
   ```python
   from .sweeps import (
       create_dry_run_sweep_job_for_backbone,
       create_hpo_sweep_job_for_backbone,
       validate_sweep_job,
   )
   __all__ = [
       "create_dry_run_sweep_job_for_backbone",
       "create_hpo_sweep_job_for_backbone",
       "validate_sweep_job",
   ]
   ```
8. **Delete duplicate**: Remove `orchestration/jobs/sweeps.py` (confirmed duplicate, not used)

**Success criteria**:
- File moved to `training/hpo/azureml/sweeps.py`
- Imports in moved file updated (including any orchestration.jobs.runtime references)
- File metadata block updated (domain: training)
- All exported functions exist in moved file
- `__init__.py` exports functions correctly
- Duplicate `orchestration/jobs/sweeps.py` removed

**Verification**:
```bash
test -f src/training/hpo/azureml/sweeps.py && echo "✓ File moved"
test -f src/training/hpo/azureml/__init__.py && echo "✓ __init__.py created"
grep -q "domain: training" src/training/hpo/azureml/sweeps.py && echo "✓ Metadata updated"
python -c "from training.hpo.azureml import create_dry_run_sweep_job_for_backbone, create_hpo_sweep_job_for_backbone, validate_sweep_job; print('✓ All imports work')"
test ! -f src/orchestration/jobs/sweeps.py && echo "✓ Duplicate removed"
```

### Step 4: Move Conversion AzureML Jobs

**Goal**: Move conversion job creation to deployment domain.

**Tasks**:
1. Move `orchestration/jobs/conversion.py` → `deployment/conversion/azureml/jobs.py`
2. Update imports in moved file:
   - Remove any `orchestration.jobs` references
   - Update relative imports if needed
   - Check for imports from `orchestration.jobs.runtime` → update to `infrastructure.azureml`
3. Update file metadata block if present:
   - Change `domain: orchestration` → `domain: deployment`
   - Update `tags` to remove `orchestration` tag
4. **Verify all functions exist** in moved file before creating `__init__.py`:
   ```bash
   grep "^def " src/deployment/conversion/azureml/jobs.py | grep -E "(create_conversion_job|get_checkpoint_output_from_training_job|validate_conversion_job)"
   ```
5. Create `deployment/conversion/azureml/__init__.py`:
   ```python
   from .jobs import (
       create_conversion_job,
       get_checkpoint_output_from_training_job,
       validate_conversion_job,
   )
   __all__ = [
       "create_conversion_job",
       "get_checkpoint_output_from_training_job",
       "validate_conversion_job",
   ]
   ```
6. **Remove backward compatibility directory**: Delete `orchestration/jobs/conversion/` directory (contains only backward compat `__init__.py`)
7. Check `deployment/conversion/__init__.py`:
   - If it has backward compatibility alias to orchestration, remove it
   - Keep only direct exports from `deployment.conversion.orchestration` (if it exists)

**Success criteria**:
- File moved to `deployment/conversion/azureml/jobs.py`
- Imports in moved file updated (including any orchestration.jobs.runtime references)
- File metadata block updated if present (domain: deployment)
- All exported functions exist in moved file
- `__init__.py` exports functions correctly
- `orchestration/jobs/conversion/` directory removed
- No backward compatibility layers

**Verification**:
```bash
test -f src/deployment/conversion/azureml/jobs.py && echo "✓ File moved"
test -f src/deployment/conversion/azureml/__init__.py && echo "✓ __init__.py created"
python -c "from deployment.conversion.azureml import create_conversion_job, get_checkpoint_output_from_training_job, validate_conversion_job; print('✓ All imports work')"
test ! -d src/orchestration/jobs/conversion && echo "✓ Backward compat directory removed"
```

### Step 5: Move AzureML Runtime Utilities

**Goal**: Move job submission utilities to infrastructure.

**Tasks**:
1. Move `orchestration/jobs/runtime.py` → `infrastructure/azureml/runtime.py`
2. Update imports in moved file:
   - Remove any `orchestration.jobs` references
   - Update relative imports if needed
3. Update file metadata block if present:
   - Change `domain: orchestration` → `domain: infrastructure`
   - Update `tags` to remove `orchestration` tag
4. **Verify function exists** in moved file before creating `__init__.py`:
   ```bash
   grep "^def submit_and_wait_for_job" src/infrastructure/azureml/runtime.py
   ```
5. Create `infrastructure/azureml/__init__.py`:
   ```python
   from .runtime import submit_and_wait_for_job
   __all__ = ["submit_and_wait_for_job"]
   ```

**Success criteria**:
- File moved to `infrastructure/azureml/runtime.py`
- Imports in moved file updated
- File metadata block updated if present (domain: infrastructure)
- Exported function exists in moved file
- `__init__.py` exports function correctly

**Verification**:
```bash
test -f src/infrastructure/azureml/runtime.py && echo "✓ File moved"
test -f src/infrastructure/azureml/__init__.py && echo "✓ __init__.py created"
python -c "from infrastructure.azureml import submit_and_wait_for_job; print('✓ Import works')"
```

### Step 6: Move Shared Backup Utilities

**Goal**: Move backup utilities to infrastructure (used by multiple domains).

**Tasks**:
1. Move `orchestration/jobs/hpo/local/backup.py` → `infrastructure/shared/backup.py`
2. Update imports in moved file:
   - Remove any `orchestration.jobs` references
   - Update relative imports if needed
   - Check for `training.hpo.core.optuna_integration` import (should stay - this is a valid cross-domain dependency)
3. Update file metadata block:
   - Change `domain: hpo` → `domain: infrastructure`
   - Update `tags` to reflect shared utility nature
4. **Verify all functions exist** in moved file before creating `__init__.py`:
   ```bash
   grep "^def " src/infrastructure/shared/backup.py | grep -E "(immediate_backup_if_needed|backup_hpo_study_to_drive|create_incremental_backup_callback|create_study_db_backup_callback)"
   ```
5. Create `infrastructure/shared/__init__.py`:
   ```python
   from .backup import (
       immediate_backup_if_needed,
       backup_hpo_study_to_drive,
       create_incremental_backup_callback,
       create_study_db_backup_callback,
   )
   __all__ = [
       "immediate_backup_if_needed",
       "backup_hpo_study_to_drive",
       "create_incremental_backup_callback",
       "create_study_db_backup_callback",
   ]
   ```

**Success criteria**:
- File moved to `infrastructure/shared/backup.py`
- Imports in moved file updated (keep training.hpo.core.optuna_integration)
- File metadata block updated (domain: infrastructure)
- All exported functions exist in moved file
- `__init__.py` exports all backup functions correctly

**Verification**:
```bash
test -f src/infrastructure/shared/backup.py && echo "✓ File moved"
test -f src/infrastructure/shared/__init__.py && echo "✓ __init__.py created"
grep -q "domain: infrastructure" src/infrastructure/shared/backup.py && echo "✓ Metadata updated"
python -c "from infrastructure.shared.backup import immediate_backup_if_needed; print('✓ Import works')"
```

### Step 7: Move MLflow Indexing

**Goal**: Move MLflow indexing to infrastructure (already used by infrastructure.tracking).

**Tasks**:
1. **Fix duplicate imports** in `orchestration/jobs/tracking/index/__init__.py` first (if moving the __init__.py):
   - Remove duplicate import blocks (lines 26-46 are duplicates of 3-23)
   - Keep only one set of imports
   - **Note**: We're creating a new `__init__.py`, so this is just for reference
2. Move `orchestration/jobs/tracking/index/run_index.py` → `infrastructure/tracking/mlflow/index/run_index.py`
3. Move `orchestration/jobs/tracking/index/version_counter.py` → `infrastructure/tracking/mlflow/index/version_counter.py`
4. Move `orchestration/jobs/tracking/index/file_locking.py` → `infrastructure/tracking/mlflow/index/file_locking.py`
5. Update imports in moved files:
   - `run_index.py`: Change `from orchestration.jobs.tracking.index.file_locking` → `from infrastructure.tracking.mlflow.index.file_locking`
   - `version_counter.py`: Change `from orchestration.jobs.tracking.index.file_locking` → `from infrastructure.tracking.mlflow.index.file_locking`
   - Update any other internal imports
6. Update file metadata blocks in moved files if present:
   - Change `domain: orchestration` → `domain: infrastructure`
   - Update `tags` to remove `orchestration` tag
7. **Verify functions exist** in moved files:
   - Check `run_index.py` for: `get_mlflow_index_path`, `update_mlflow_index`, `find_in_mlflow_index`
   - Check `version_counter.py` for: `get_run_name_counter_path`, `reserve_run_name_version`, `commit_run_name_version`, `cleanup_stale_reservations`
   - Check `file_locking.py` for: `acquire_lock`, `release_lock` (if exported)
8. Create `infrastructure/tracking/mlflow/index/__init__.py`:
   ```python
   from .run_index import (
       get_mlflow_index_path,
       update_mlflow_index,
       find_in_mlflow_index,
   )
   from .version_counter import (
       get_run_name_counter_path,
       reserve_run_name_version,
       commit_run_name_version,
       cleanup_stale_reservations,
   )
   from .file_locking import (
       acquire_lock,
       release_lock,
   )
   __all__ = [
       "get_mlflow_index_path",
       "update_mlflow_index",
       "find_in_mlflow_index",
       "get_run_name_counter_path",
       "reserve_run_name_version",
       "commit_run_name_version",
       "cleanup_stale_reservations",
       "acquire_lock",
       "release_lock",
   ]
   ```
   **Note**: The old `orchestration/jobs/tracking/index/__init__.py` has duplicate imports (lines 3-23 and 26-46). The new file should NOT have duplicates. Include `file_locking` exports if they're used elsewhere.

**Success criteria**:
- All three files moved to `infrastructure/tracking/mlflow/index/`
- Imports in moved files updated
- File metadata blocks updated if present (domain: infrastructure)
- All exported functions exist in moved files
- `__init__.py` exports all index functions correctly (no duplicates, includes file_locking if needed)

**Verification**:
```bash
test -f src/infrastructure/tracking/mlflow/index/run_index.py && echo "✓ run_index.py moved"
test -f src/infrastructure/tracking/mlflow/index/version_counter.py && echo "✓ version_counter.py moved"
test -f src/infrastructure/tracking/mlflow/index/file_locking.py && echo "✓ file_locking.py moved"
test -f src/infrastructure/tracking/mlflow/index/__init__.py && echo "✓ __init__.py created"
# Check for duplicate imports in __init__.py
grep -c "^from \\.run_index import" src/infrastructure/tracking/mlflow/index/__init__.py | grep -q "^1$" && echo "✓ No duplicate imports"
python -c "from infrastructure.tracking.mlflow.index import update_mlflow_index, reserve_run_name_version; print('✓ Imports work')"
```

### Step 8: Handle local_selection_v2.py

**Goal**: Handle selection logic (file likely already exists in evaluation domain).

**Tasks**:
1. Check if `evaluation/selection/local_selection_v2.py` already exists:
   ```bash
   test -f src/evaluation/selection/local_selection_v2.py && echo "EXISTS" || echo "NOT_EXISTS"
   ```
2. **Analysis**: Check if `orchestration/jobs/local_selection_v2.py` imports from `evaluation.selection.local_selection_v2`:
   ```bash
   grep "from.*evaluation\.selection\.local_selection_v2\|import.*evaluation\.selection\.local_selection_v2" src/orchestration/jobs/local_selection_v2.py
   ```
   - If it imports from evaluation, it's likely a duplicate or wrapper
3. Verify no imports reference `orchestration.jobs.local_selection_v2`:
   ```bash
   grep -r "from.*orchestration\.jobs\.local_selection_v2\|import.*orchestration\.jobs\.local_selection_v2" --include="*.py" src/ tests/
   ```
4. If `evaluation/selection/local_selection_v2.py` exists:
   - Compare with `orchestration/jobs/local_selection_v2.py`:
     ```bash
     diff src/orchestration/jobs/local_selection_v2.py src/evaluation/selection/local_selection_v2.py
     ```
   - If identical: Delete `orchestration/jobs/local_selection_v2.py` (duplicate)
   - If different: Review differences carefully
     - If orchestration version has unique functionality, merge into `evaluation/selection/local_selection_v2.py`
     - If evaluation version is canonical, delete orchestration version
5. If `evaluation/selection/local_selection_v2.py` doesn't exist:
   - Move `orchestration/jobs/local_selection_v2.py` → `evaluation/selection/local_selection_v2.py`
   - Update imports in moved file
   - Remove any import from `evaluation.selection.local_selection_v2` (line 50) and inline the function if needed
6. Check `evaluation/selection/__init__.py` and add export if needed

**Success criteria**:
- File in correct location (`evaluation/selection/local_selection_v2.py`)
- No duplicates (orchestration version removed)
- No imports reference orchestration version
- Imports updated if file was moved

**Verification**:
```bash
test -f src/evaluation/selection/local_selection_v2.py && echo "✓ File in correct location"
test ! -f src/orchestration/jobs/local_selection_v2.py && echo "✓ Old file removed"
```

### Step 9: Update All Imports - Training Domain

**Goal**: Update all imports from `orchestration.jobs.training` and `orchestration.jobs.hpo.azureml` to new locations.

**Tasks**:
1. Find all imports (comprehensive search):
   ```bash
   # Direct imports
   grep -r "from.*orchestration\.jobs\.training\|from.*orchestration\.jobs\.hpo\.azureml" --include="*.py" src/ tests/ notebooks/
   # Import statements
   grep -r "import.*orchestration\.jobs\.training\|import.*orchestration\.jobs\.hpo\.azureml" --include="*.py" src/ tests/ notebooks/
   # Also check for imports from sweeps.py (if it exists)
   grep -r "from.*orchestration\.jobs\.sweeps\|import.*orchestration\.jobs\.sweeps" --include="*.py" src/ tests/ notebooks/
   # String references in comments/docs
   grep -r "orchestration\.jobs\.training\|orchestration\.jobs\.hpo\.azureml" --include="*.md" --include="*.ipynb" docs/ notebooks/
   ```
2. Replace imports:
   ```python
   # OLD
   from orchestration.jobs.training import build_final_training_config, create_final_training_job
   from orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone
   from orchestration.jobs.hpo.azureml import create_hpo_sweep_job_for_backbone
   from orchestration.jobs.sweeps import create_hpo_sweep_job_for_backbone  # if exists
   
   # NEW
   from training.azureml import build_final_training_config, create_final_training_job
   from training.hpo.azureml import create_hpo_sweep_job_for_backbone
   ```
3. Update files:
   - All Python files in `src/` (prioritize source files over tests)
   - All test files in `tests/`
   - All notebooks in `notebooks/`
   - All README files with import examples
   - All documentation files
4. **After each file update, verify import works**:
   ```bash
   python -c "from training.azureml import build_final_training_config; print('✓ Import works')"
   ```
5. After updating all files, run mypy to catch any import-related type errors:
   ```bash
   uvx mypy src/training --show-error-codes
   ```

**Success criteria**:
- All training-related imports updated
- No references to `orchestration.jobs.training` or `orchestration.jobs.hpo.azureml` in code
- No references to `orchestration.jobs.sweeps` (if it was deleted)
- All imports use new paths
- Mypy passes for training domain

**Verification**:
```bash
# Should return 0 results
grep -r "from.*orchestration\.jobs\.training\|from.*orchestration\.jobs\.hpo\.azureml\|import.*orchestration\.jobs\.training\|import.*orchestration\.jobs\.hpo\.azureml" --include="*.py" src/ tests/ notebooks/ | wc -l

# Also check for sweeps.py imports (should be 0 if deleted)
grep -r "from.*orchestration\.jobs\.sweeps\|import.*orchestration\.jobs\.sweeps" --include="*.py" src/ tests/ notebooks/ | wc -l

# Verify new imports work
python -c "from training.azureml import build_final_training_config; from training.hpo.azureml import create_hpo_sweep_job_for_backbone; print('✓ Imports work')"

# Check mypy
uvx mypy src/training --show-error-codes | grep -q "Success" && echo "✓ Mypy passes"
```

### Step 10: Update All Imports - Conversion Domain

**Goal**: Update all imports from `orchestration.jobs.conversion` to new location.

**Tasks**:
1. Find all imports (comprehensive search):
   ```bash
   # Direct imports
   grep -r "from.*orchestration\.jobs\.conversion\|import.*orchestration\.jobs\.conversion" --include="*.py" src/ tests/ notebooks/
   # String references in comments/docs
   grep -r "orchestration\.jobs\.conversion" --include="*.md" --include="*.ipynb" docs/ notebooks/
   ```
2. Replace imports:
   ```python
   # OLD
   from orchestration.jobs.conversion import create_conversion_job
   from orchestration.jobs.conversion import get_checkpoint_output_from_training_job
   
   # NEW
   from deployment.conversion.azureml import create_conversion_job
   from deployment.conversion.azureml import get_checkpoint_output_from_training_job
   ```
3. Update files (Python files, tests, notebooks, READMEs, docs)
4. After updating, run mypy to catch any import-related type errors:
   ```bash
   uvx mypy src/deployment --show-error-codes
   ```

**Success criteria**:
- All conversion-related imports updated
- No references to `orchestration.jobs.conversion`
- Mypy passes for deployment domain

**Verification**:
```bash
# Should return 0 results
grep -r "from.*orchestration\.jobs\.conversion\|import.*orchestration\.jobs\.conversion" --include="*.py" src/ tests/ notebooks/ | wc -l

# Verify new imports work
python -c "from deployment.conversion.azureml import create_conversion_job; print('✓ Import works')"

# Check mypy
uvx mypy src/deployment --show-error-codes | grep -q "Success" && echo "✓ Mypy passes"
```

### Step 11: Update All Imports - Runtime

**Goal**: Update all imports from `orchestration.jobs.runtime` to new location.

**Tasks**:
1. Find all imports (comprehensive search):
   ```bash
   # Direct imports
   grep -r "from.*orchestration\.jobs\.runtime\|import.*orchestration\.jobs\.runtime" --include="*.py" src/ tests/ notebooks/
   # String references in comments/docs
   grep -r "orchestration\.jobs\.runtime" --include="*.md" --include="*.ipynb" docs/ notebooks/
   ```
2. Replace imports:
   ```python
   # OLD
   from orchestration.jobs.runtime import submit_and_wait_for_job
   
   # NEW
   from infrastructure.azureml import submit_and_wait_for_job
   ```
3. Update files (Python files, tests, notebooks, READMEs, docs)
4. After updating, run mypy to catch any import-related type errors:
   ```bash
   uvx mypy src/infrastructure/azureml --show-error-codes
   ```

**Success criteria**:
- All runtime imports updated
- No references to `orchestration.jobs.runtime`
- Mypy passes for infrastructure.azureml

**Verification**:
```bash
# Should return 0 results
grep -r "from.*orchestration\.jobs\.runtime\|import.*orchestration\.jobs\.runtime" --include="*.py" src/ tests/ notebooks/ | wc -l

# Verify new imports work
python -c "from infrastructure.azureml import submit_and_wait_for_job; print('✓ Import works')"

# Check mypy
uvx mypy src/infrastructure/azureml --show-error-codes | grep -q "Success" && echo "✓ Mypy passes"
```

### Step 12: Update All Imports - Backup Utilities

**Goal**: Update all imports from `orchestration.jobs.hpo.local.backup` to new location.

**Tasks**:
1. Find all imports (comprehensive search):
   ```bash
   # Direct imports
   grep -r "from.*orchestration\.jobs\.hpo\.local\.backup\|import.*orchestration\.jobs\.hpo\.local\.backup" --include="*.py" src/ tests/ notebooks/
   # String references in comments/docs
   grep -r "orchestration\.jobs\.hpo\.local\.backup" --include="*.md" --include="*.ipynb" docs/ notebooks/
   ```
2. Replace imports:
   ```python
   # OLD
   from orchestration.jobs.hpo.local.backup import immediate_backup_if_needed
   from orchestration.jobs.hpo.local.backup import create_incremental_backup_callback
   from orchestration.jobs.hpo.local.backup import backup_hpo_study_to_drive
   from orchestration.jobs.hpo.local.backup import create_study_db_backup_callback
   
   # NEW
   from infrastructure.shared.backup import immediate_backup_if_needed
   from infrastructure.shared.backup import create_incremental_backup_callback
   from infrastructure.shared.backup import backup_hpo_study_to_drive
   from infrastructure.shared.backup import create_study_db_backup_callback
   ```
3. Update files (11+ files found):
   - `training/execution/executor.py`
   - `training/hpo/execution/local/sweep.py`
   - `deployment/conversion/orchestration.py`
   - `evaluation/benchmarking/orchestrator.py`
   - And others
4. After updating, run mypy to catch any import-related type errors:
   ```bash
   uvx mypy src/infrastructure/shared --show-error-codes
   ```

**Success criteria**:
- All backup utility imports updated
- No references to `orchestration.jobs.hpo.local.backup`
- Mypy passes for infrastructure.shared

**Verification**:
```bash
# Should return 0 results
grep -r "from.*orchestration\.jobs\.hpo\.local\.backup\|import.*orchestration\.jobs\.hpo\.local\.backup" --include="*.py" src/ tests/ notebooks/ | wc -l

# Verify new imports work
python -c "from infrastructure.shared.backup import immediate_backup_if_needed; print('✓ Import works')"

# Check mypy
uvx mypy src/infrastructure/shared --show-error-codes | grep -q "Success" && echo "✓ Mypy passes"
```

### Step 13: Update All Imports - MLflow Indexing

**Goal**: Update all imports from `orchestration.jobs.tracking.index` to new location.

**Tasks**:
1. Find all imports (comprehensive search):
   ```bash
   # Direct imports
   grep -r "from.*orchestration\.jobs\.tracking\.index\|import.*orchestration\.jobs\.tracking\.index" --include="*.py" src/ tests/ notebooks/
   # Also check for imports from the __init__.py
   grep -r "from.*orchestration\.jobs\.tracking\.index import\|from orchestration.jobs.tracking.index import" --include="*.py" src/ tests/ notebooks/
   # String references in comments/docs
   grep -r "orchestration\.jobs\.tracking\.index" --include="*.md" --include="*.ipynb" docs/ notebooks/
   ```
2. Replace imports:
   ```python
   # OLD
   from orchestration.jobs.tracking.index.run_index import update_mlflow_index
   from orchestration.jobs.tracking.index.version_counter import reserve_run_name_version
   from orchestration.jobs.tracking.index.file_locking import acquire_lock
   from orchestration.jobs.tracking.index import update_mlflow_index, reserve_run_name_version
   
   # NEW
   from infrastructure.tracking.mlflow.index import update_mlflow_index
   from infrastructure.tracking.mlflow.index import reserve_run_name_version
   # Note: file_locking functions may need direct import if not exported in __init__.py
   from infrastructure.tracking.mlflow.index.file_locking import acquire_lock
   # Or use the __init__.py exports (if file_locking is exported):
   from infrastructure.tracking.mlflow.index import acquire_lock, release_lock
   ```
   **Note**: If `file_locking` functions are not exported in the `__init__.py`, they may need to be imported directly from the module. Verify the actual export structure after Step 7.
3. Update files (15+ files found):
   - `infrastructure/tracking/mlflow/finder.py`
   - `infrastructure/tracking/mlflow/trackers/*.py` (all tracker files)
   - `training/execution/executor.py`
   - `training/execution/mlflow_setup.py`
   - `training/hpo/tracking/setup.py`
   - `training/hpo/execution/local/sweep.py`
   - `deployment/conversion/orchestration.py`
   - `infrastructure/naming/mlflow/run_names.py`
   - And others
4. After updating, run mypy to catch any import-related type errors:
   ```bash
   uvx mypy src/infrastructure/tracking/mlflow/index --show-error-codes
   ```

**Success criteria**:
- All MLflow indexing imports updated
- No references to `orchestration.jobs.tracking.index`
- Mypy passes for infrastructure.tracking.mlflow.index

**Verification**:
```bash
# Should return 0 results
grep -r "from.*orchestration\.jobs\.tracking\.index\|import.*orchestration\.jobs\.tracking\.index" --include="*.py" src/ tests/ notebooks/ | wc -l

# Verify new imports work
python -c "from infrastructure.tracking.mlflow.index import update_mlflow_index; print('✓ Import works')"

# Check mypy
uvx mypy src/infrastructure/tracking/mlflow/index --show-error-codes | grep -q "Success" && echo "✓ Mypy passes"
```

### Step 14: Remove Deprecated Compatibility Layers

**Goal**: Delete all deprecated compatibility wrapper files.

**Tasks**:
1. **Before deleting, verify each file/directory is actually deprecated**:
   - Check if files are re-exports or have actual implementations
   - Use `grep` to find any remaining imports:
     ```bash
     grep -r "orchestration\.jobs\.tracking\.config\|orchestration\.jobs\.tracking\.mlflow_" --include="*.py" src/ tests/ | wc -l
     ```
     Should return 0. If not, update those imports first.
2. Delete deprecated files/directories (only after verification):
   - `orchestration/jobs/tracking/config/` (entire directory) - confirmed deprecated wrapper
   - `orchestration/jobs/tracking/mlflow_config_loader.py` - confirmed deprecated wrapper
   - `orchestration/jobs/tracking/mlflow_naming.py` - backward compat re-export
   - `orchestration/jobs/tracking/mlflow_run_finder.py` - backward compat re-export
   - `orchestration/jobs/tracking/mlflow_index.py` - backward compat re-export
   - `orchestration/jobs/tracking/mlflow_tracker.py` - backward compat re-export
   - `orchestration/jobs/tracking/artifact_manager.py` - backward compat re-export
   - `orchestration/jobs/tracking/finder/` (if only re-exports - verify first)
   - `orchestration/jobs/tracking/utils/` (if only re-exports - verify first)
   - `orchestration/jobs/tracking/trackers/` (if only re-exports - verify first)
   - `orchestration/jobs/tracking/artifacts/` (if only re-exports - verify first)
   - `orchestration/jobs/benchmarking/` (broken, non-existent import)
   - `orchestration/jobs/conversion/` (if not already removed in Step 4)
   - `orchestration/jobs/sweeps.py` (if confirmed duplicate from Step 3)
   - `orchestration/jobs/local_selection_v2.py` (if confirmed duplicate/wrapper from Step 8)
3. Verify no remaining imports from these deprecated modules

**Success criteria**:
- All deprecated files removed
- No compatibility layers remain
- No broken imports
- No remaining references to deleted modules

**Verification**:
```bash
test ! -d src/orchestration/jobs/tracking/config && echo "✓ Config directory removed"
test ! -f src/orchestration/jobs/tracking/mlflow_config_loader.py && echo "✓ Config loader removed"
test ! -f src/orchestration/jobs/tracking/mlflow_naming.py && echo "✓ Naming wrapper removed"
test ! -d src/orchestration/jobs/benchmarking && echo "✓ Benchmarking directory removed"
test ! -d src/orchestration/jobs/conversion && echo "✓ Conversion directory removed"
test ! -f src/orchestration/jobs/sweeps.py && echo "✓ Duplicate sweeps.py removed"
test ! -f src/orchestration/jobs/local_selection_v2.py && echo "✓ Duplicate local_selection_v2.py removed"

# Should return 0 results
grep -r "orchestration\.jobs\.tracking\.config\|orchestration\.jobs\.tracking\.mlflow_" --include="*.py" src/ tests/ | wc -l
```

### Step 15: Delete Orchestration Module

**Goal**: Delete the entire orchestration module after all moves and import updates.

**Tasks**:
1. **Final verification** - Comprehensive check for remaining imports from orchestration:
   ```bash
   # Check Python files
   grep -r "from.*orchestration\|import.*orchestration" --include="*.py" src/ tests/ notebooks/ | grep -v "implementation_plans\|audits\|README\|\.md\|\.plan\.md" | wc -l
   
   # Check for string references (comments, docstrings)
   grep -r "orchestration\.jobs\." --include="*.py" src/ tests/ | grep -v "#\|'''\|'''" | wc -l
   
   # Check for any remaining orchestration module references
   grep -r "\borchestration\b" --include="*.py" src/ tests/ | grep -v "implementation_plans\|audits" | grep -v "^#" | wc -l
   ```
   Should return 0 (excluding documentation/audit files and comments)
2. **Check for any remaining orchestration files**:
   ```bash
   find src/orchestration -name "*.py" -type f | grep -v "__pycache__" | wc -l
   ```
   Should only show deprecated compatibility layers (if any remain)
3. If any imports remain, identify and update them before proceeding
4. **Verify all moved files are in their new locations**:
   ```bash
   test -f src/training/azureml/jobs.py && echo "✓ Training jobs moved"
   test -f src/training/hpo/azureml/sweeps.py && echo "✓ HPO sweeps moved"
   test -f src/deployment/conversion/azureml/jobs.py && echo "✓ Conversion jobs moved"
   test -f src/infrastructure/azureml/runtime.py && echo "✓ Runtime moved"
   test -f src/infrastructure/shared/backup.py && echo "✓ Backup moved"
   test -f src/infrastructure/tracking/mlflow/index/run_index.py && echo "✓ MLflow index moved"
   ```
5. Delete entire `orchestration/` directory:
   ```bash
   rm -rf src/orchestration/
   ```
6. Check `src/__init__.py`:
   - If it exports anything from orchestration, remove those exports
   - Check: `grep -i "orchestration" src/__init__.py 2>/dev/null && echo "⚠️  Found orchestration exports" || echo "✓ No orchestration exports"`
7. Update `.gitignore` if needed (unlikely, but check)
8. **Verify tests still pass** after deletion:
   ```bash
   uvx pytest tests/ -x --tb=short -k "not slow"  # Quick smoke test
   ```

**Success criteria**:
- No imports reference orchestration (except in docs/audits/comments)
- All moved files verified in new locations
- Directory deleted
- Tests still pass

**Verification**:
```bash
# Should return 0 (excluding docs and comments)
grep -r "from.*orchestration\|import.*orchestration" --include="*.py" src/ tests/ notebooks/ | grep -v "implementation_plans\|audits\|\.md\|\.plan\.md\|^#" | wc -l

# Verify directory deleted
test ! -d src/orchestration && echo "✓ Orchestration directory deleted"

# Verify all files moved
test -f src/training/azureml/jobs.py && test -f src/training/hpo/azureml/sweeps.py && test -f src/deployment/conversion/azureml/jobs.py && echo "✓ All files moved"

# Check src/__init__.py for any orchestration exports
grep -i "orchestration" src/__init__.py 2>/dev/null && echo "⚠️  Found orchestration exports in src/__init__.py" || echo "✓ No orchestration exports in src/__init__.py"

# Run tests to verify nothing broke
uvx pytest tests/ -x --tb=short
```

### Step 16: Update Documentation

**Goal**: Update all documentation to reflect new structure.

**Tasks**:
1. Update `training/README.md`:
   - Add section for AzureML job creation
   - Update import examples
   - Document `training/azureml/` and `training/hpo/azureml/` modules
2. Update `deployment/conversion/README.md`:
   - Add section for AzureML job creation
   - Update import examples
   - Document `deployment/conversion/azureml/` module
3. Update `infrastructure/README.md`:
   - Add section for AzureML runtime utilities
   - Add section for shared utilities (backup)
   - Add section for MLflow indexing
   - Update import examples
4. Update any notebooks that reference orchestration:
   - Find notebooks: `grep -r "orchestration" notebooks/ --include="*.ipynb"`
   - Update import statements in notebooks
5. Update implementation plan documentation:
   - Update any references to orchestration structure
6. Delete or archive `orchestration/README.md` (if still exists)

**Success criteria**:
- All READMEs reflect new structure
- All import examples work
- No references to orchestration module (except historical context)

**Verification**:
```bash
# Check READMEs for old imports
grep -i "orchestration\.jobs" src/*/README.md src/*/*/README.md | wc -l

# Verify import examples in READMEs work
python -c "$(grep -A 5 '^```python' src/training/README.md | grep -v '^```' | head -10)"
```

### Step 17: Verify Tests and Type Checking

**Goal**: Ensure all tests pass and type checking is clean.

**Tasks**:
1. **Check for circular imports**:
   ```bash
   python -c "
   import sys
   sys.path.insert(0, 'src')
   try:
       from training.azureml import build_final_training_config
       from training.hpo.azureml import create_hpo_sweep_job_for_backbone
       from deployment.conversion.azureml import create_conversion_job
       from infrastructure.azureml import submit_and_wait_for_job
       from infrastructure.shared.backup import immediate_backup_if_needed
       from infrastructure.tracking.mlflow.index import update_mlflow_index
       print('✓ No circular imports detected')
   except ImportError as e:
       print(f'✗ Import error: {e}')
       sys.exit(1)
   "
   ```
2. Run mypy first (faster feedback):
   ```bash
   uvx mypy src --show-error-codes
   ```
   Fix any type errors before running tests
3. Run full test suite:
   ```bash
   uvx pytest tests/ -v --tb=short
   ```
4. Fix any test failures:
   - Update test imports if needed
   - Fix any broken test logic
   - Verify test files were updated in Steps 9-13
5. Fix any type errors:
   - Update type hints if needed
   - Fix import-related type errors
6. Run tests again to verify fixes:
   ```bash
   uvx pytest tests/ -v --tb=short
   uvx mypy src --show-error-codes
   ```

**Success criteria**:
- All tests pass
- Mypy passes with 0 errors
- No import errors
- No broken functionality
- No circular imports

**Verification**:
```bash
# Run tests
uvx pytest tests/ -v --tb=short

# Run mypy
uvx mypy src --show-error-codes

# Check for import errors
python -c "
from training.azureml import build_final_training_config, create_final_training_job
from training.hpo.azureml import create_hpo_sweep_job_for_backbone
from deployment.conversion.azureml import create_conversion_job
from infrastructure.azureml import submit_and_wait_for_job
from infrastructure.shared.backup import immediate_backup_if_needed
from infrastructure.tracking.mlflow.index import update_mlflow_index
print('✓ All imports work')
"
```

## Import Migration Map

| Old Import | New Import |
|------------|------------|
| `orchestration.jobs.training` | `training.azureml` |
| `orchestration.jobs.hpo.azureml.sweeps` | `training.hpo.azureml` |
| `orchestration.jobs.sweeps` | **DELETE** (duplicate) |
| `orchestration.jobs.conversion` | `deployment.conversion.azureml` |
| `orchestration.jobs.runtime` | `infrastructure.azureml` |
| `orchestration.jobs.hpo.local.backup` | `infrastructure.shared.backup` |
| `orchestration.jobs.tracking.index.*` | `infrastructure.tracking.mlflow.index.*` |

## Success Criteria (Overall)

- ✅ All AzureML job creation in domain modules
- ✅ All shared utilities in infrastructure
- ✅ All MLflow indexing in infrastructure
- ✅ No orchestration module remains
- ✅ All imports updated (~40-50 Python imports + documentation references)
- ✅ All tests pass
- ✅ Mypy passes with 0 errors
- ✅ Documentation updated
- ✅ Clean module structure following domain organization

## Estimated Impact

- **Files to move**: ~10 files (training.py, sweeps.py, conversion.py, runtime.py, backup.py, 3 index files, local_selection_v2.py)
- **Files to delete**: ~15+ (deprecated layers + orchestration module)
- **Python files importing orchestration**: 28 files (based on grep results)
- **Import statements to update**: ~40-50 actual Python imports (rest are in docs/READMEs)
- **Test files to update**: Multiple (verify with `grep -r "orchestration" tests/`)
- **Documentation files to update**: ~9 README files
- **Breaking changes**: Yes - all imports from orchestration will break
- **Risk level**: Medium-High (requires careful import updates across codebase)

## Migration Guide for Users

### Import Changes

#### Training Jobs
```python
# OLD
from orchestration.jobs.training import build_final_training_config, create_final_training_job
from orchestration.jobs.hpo.azureml.sweeps import create_hpo_sweep_job_for_backbone

# NEW
from training.azureml import build_final_training_config, create_final_training_job
from training.hpo.azureml import create_hpo_sweep_job_for_backbone
```

#### Conversion Jobs
```python
# OLD
from orchestration.jobs.conversion import create_conversion_job

# NEW
from deployment.conversion.azureml import create_conversion_job
```

#### Runtime Utilities
```python
# OLD
from orchestration.jobs.runtime import submit_and_wait_for_job

# NEW
from infrastructure.azureml import submit_and_wait_for_job
```

#### Backup Utilities
```python
# OLD
from orchestration.jobs.hpo.local.backup import immediate_backup_if_needed

# NEW
from infrastructure.shared.backup import immediate_backup_if_needed
```

#### MLflow Indexing
```python
# OLD
from orchestration.jobs.tracking.index.run_index import update_mlflow_index

# NEW
from infrastructure.tracking.mlflow.index import update_mlflow_index
```

## Notes

- This is a **breaking change** - all imports from orchestration will need to be updated
- **Execution strategy**: Consider doing this incrementally:
  1. Move files first (Steps 1-8) - verify each move works before proceeding
  2. Update imports in batches (Steps 9-13) - update one domain at a time
  3. Clean up and verify (Steps 14-17) - final verification before deletion
- **Dependency order**: Move dependencies first (index, runtime, backup) before dependents (training, conversion jobs)
- All active code (index, runtime, backup) remains unchanged - only locations change
- This aligns with "big modules" architecture where each domain is self-contained
- The orchestration module served as a cross-cutting concern, but with domain-based organization, each domain should own its AzureML job creation
- **Verification after each step**: Run `uvx mypy src --show-error-codes` after each major step to catch import errors early
- **Duplicate sweeps.py**: There are two sweeps.py files - verify they're identical before deleting the top-level one

## Known Issues to Address

1. **Duplicate imports in `orchestration/jobs/tracking/index/__init__.py`**: The file has duplicate import blocks (lines 3-23 and 26-46). The new `infrastructure/tracking/mlflow/index/__init__.py` should NOT have duplicates.

2. **File metadata blocks**: All moved files should have their metadata blocks updated to reflect the new domain (training, deployment, infrastructure).

3. **Import patterns**: Some files may use string-based imports or dynamic imports. These need to be found and updated manually.

4. **Notebook cells**: Notebooks may have import statements in code cells that need updating. Use `grep` to find them, then update manually.

5. **file_locking exports**: Verify if `acquire_lock` and `release_lock` need to be exported in the new `__init__.py` or imported directly from the module.

6. **local_selection_v2.py**: This file may import from `evaluation.selection.local_selection_v2`, indicating it's a duplicate/wrapper. Verify and handle accordingly.

## Risk Mitigation

- **Incremental approach**: Move files first, then update imports in batches to minimize risk
- **Test after each batch**: Run tests after each import update step (Steps 9-13) to catch issues early
- **Git commits**: Consider committing after each major step (file moves, import batches) for easier rollback
- **Type checking**: Run mypy after each import update to catch type-related issues early
- **Function verification**: Verify all functions exist before creating `__init__.py` files
- **Dependency order**: Move dependencies first (index, runtime, backup) before dependents

## Out of Scope

The following files/directories in `orchestration/jobs/hpo/local/` are **NOT** part of this migration:
- `orchestration/jobs/hpo/local/checkpoint/` - Local checkpoint management (stays in training domain or separate migration)
- `orchestration/jobs/hpo/local/trial/` - Local trial execution (stays in training domain)
- `orchestration/jobs/hpo/local/optuna/` - Optuna integration (stays in training domain)
- `orchestration/jobs/hpo/local/cv/` - Cross-validation orchestration (stays in training domain)
- `orchestration/jobs/hpo/local/study/` - Study management (stays in training domain)
- `orchestration/jobs/hpo/local/mlflow/` - MLflow cleanup (stays in training domain)
- `orchestration/jobs/hpo/local/refit/` - Refit execution (stays in training domain)

These are **local execution** files, not AzureML job creation, and should be handled separately if needed. This plan focuses only on **AzureML job orchestration** and **shared infrastructure utilities**.

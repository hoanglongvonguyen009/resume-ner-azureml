# Consolidate Remaining DRY Violations in src/ - Unified Master Plan

## Goal

Systematically identify and consolidate overlapping responsibilities, duplicated logic, and near-duplicate patterns across modules in the `src/` directory. This unified plan consolidates insights from multiple analyses to eliminate DRY violations while maintaining backward compatibility and following reuse-first principles.

**Key Objectives:**
1. Consolidate duplicate Azure ML job creation functions (sweep jobs and training jobs)
2. Extract shared Azure ML helper functions to common utilities
3. Remove or migrate legacy code patterns (sweep_original, sweep_tracker_original)
4. Clarify MLflow setup responsibilities and eliminate overlap
5. Consolidate exact duplicate functions (build_final_training_config, resolve_dataset_path)
6. Review and document path resolution, config loading, and hash computation patterns

## Status

**Last Updated**: 2026-01-18

### Completed Steps
- ✅ Step 1: Analyze and catalog all duplicate functions
- ✅ Step 2: Consolidate Azure ML sweep job creation functions
- ✅ Step 3: Consolidate Azure ML training job creation functions
- ✅ Step 4: Extract shared Azure ML helper functions
- ✅ Step 5: Consolidate build_final_training_config duplicate
- ✅ Step 6: Consolidate resolve_dataset_path duplicate
- ✅ Step 7: Migrate or remove legacy sweep_original code
- ✅ Step 8: Migrate or remove legacy sweep_tracker_original code
- ✅ Step 9: Clarify MLflow setup responsibilities
- ✅ Step 10: Review and document path resolution patterns
- ✅ Step 11: Review and document config loading patterns
- ✅ Step 12: Update all call sites to use consolidated functions
- ✅ Step 13: Remove dead code and verify tests pass

### Pending Steps
- ✅ All steps completed

## Preconditions

- All existing tests must pass: `uvx pytest tests/`
- Mypy baseline established: `uvx mypy src --show-error-codes`
- Git commit created for current state
- No active PRs that would conflict with consolidation changes
- Review existing consolidation work: `FINISHED-MASTER-20260118-1700-consolidate-scripts-utilities-dry-violations-unified.plan.md`

## Identified DRY Violations

### Category 1: Duplicate Azure ML Sweep Job Creation Functions (HIGH PRIORITY)

**Violation**: Two nearly identical modules with same functions:
- `src/training/hpo/execution/azureml/sweeps.py`
- `src/training/hpo/azureml/sweeps.py`

**Duplicate Functions**:
1. `create_dry_run_sweep_job_for_backbone()` - Near-identical implementations (lines 56-152 vs 57-149)
2. `create_hpo_sweep_job_for_backbone()` - Near-identical implementations (lines 154-264 vs 152-258)
3. `validate_sweep_job()` - Near-identical implementations (lines 306-343 vs 304-341)
4. `_build_data_input_from_asset()` - Identical implementations (lines 40-54 vs 40-54)
5. `_validate_job_status()` - Identical implementations (lines 266-279 vs 261-275)
6. `_get_trial_count()` - Identical implementations (lines 281-304 vs 278-301)

**Minor Differences**:
- `src/training/hpo/execution/azureml/sweeps.py` uses `direction` from config with fallback (line 127, 222)
- `src/training/hpo/azureml/sweeps.py` uses `goal` directly from config (line 127, 219)
- Metadata blocks differ slightly (domain: hpo vs domain: training)

**Impact**: HIGH - Two identical modules maintained separately increases maintenance burden and risk of divergence.

**Recommendation**: Keep `src/training/hpo/execution/azureml/sweeps.py` (better location in execution module) and remove `src/training/hpo/azureml/sweeps.py` after updating all imports. Standardize on `direction` pattern with fallback.

### Category 2: Duplicate Azure ML Training Job Creation Functions (HIGH PRIORITY)

**Violation**: Two identical modules with same functions:
- `src/training/execution/jobs.py`
- `src/training/azureml/jobs.py`

**Duplicate Functions**:
1. `build_final_training_config()` - Identical implementations (lines 35-70 vs 36-71)
2. `validate_final_training_job()` - Identical implementations (lines 72-83 vs 73-84)
3. `create_final_training_job()` - Identical implementations (lines 101-167 vs 102-168)
4. `_build_data_input_from_asset()` - Identical implementations (lines 85-99 vs 86-100)

**Differences**: None - files are completely identical except metadata blocks.

**Impact**: HIGH - Two identical modules maintained separately increases maintenance burden.

**Recommendation**: Keep `src/training/execution/jobs.py` (better location in execution module) and remove `src/training/azureml/jobs.py` after updating all imports.

### Category 3: Duplicate Helper Function `_build_data_input_from_asset()` (MEDIUM PRIORITY)

**Violation**: Same helper function duplicated across 4 files:
- `src/training/hpo/execution/azureml/sweeps.py:40-54`
- `src/training/hpo/azureml/sweeps.py:40-54`
- `src/training/execution/jobs.py:85-99`
- `src/training/azureml/jobs.py:86-100`

**Function Signature**:
```python
def _build_data_input_from_asset(data_asset: Data) -> Input:
    """Build a standard Azure ML Input for a uri_folder data asset."""
    return Input(
        type="uri_folder",
        path=f"azureml:{data_asset.name}:{data_asset.version}",
        mode="mount",
    )
```

**Impact**: MEDIUM - Helper function duplicated 4 times, should be extracted to shared utility.

**Recommendation**: Extract to `src/infrastructure/azureml/helpers.py` or `src/common/azureml/utils.py` as `build_data_input_from_asset()` (public function).

### Category 4: Duplicate `build_final_training_config` Function (HIGH PRIORITY)

**Violation**: Exact duplicate function exists in two files:
- `src/training/execution/jobs.py:35-71`
- `src/training/azureml/jobs.py:36-71`

**Status**: ✅ **IDENTICAL** - Exact duplicate (37 lines identical)

**Impact**: HIGH - Exact code duplication, maintenance burden, risk of divergence.

**Recommendation**: Consolidate into single function. Since this overlaps with Category 2, will be handled together in Step 3.

### Category 5: Duplicate `resolve_dataset_path` Function (MEDIUM PRIORITY)

**Violation**: Exact duplicate function exists in two files:
- `src/training/execution/executor.py:57-69` (fallback implementation)
- `src/infrastructure/platform/azureml/data_assets.py:37-70`

**Status**: ✅ **IDENTICAL** - Exact duplicate logic (handles seed-based dataset structure)

**Impact**: MEDIUM - Exact code duplication.

**Recommendation**: Keep in `src/infrastructure/platform/azureml/data_assets.py` (more specific location) and update `src/training/execution/executor.py` to import from there.

### Category 6: Legacy Sweep Implementation Pattern (MEDIUM PRIORITY)

**Violation**: Two implementations of same functionality:
- `src/training/hpo/execution/local/sweep_original.py` (1672 lines, original implementation)
- `src/training/hpo/execution/local/sweep/sweep.py` (88 lines, wrapper around original)
- `src/training/hpo/execution/local/sweep.py` (may be duplicate wrapper)

**Pattern**: The new `sweep.py` just wraps `sweep_original.py`:
```python
from training.hpo.execution.local.sweep_original import (
    create_local_hpo_objective as _create_local_hpo_objective_original,
    run_local_hpo_sweep as _run_local_hpo_sweep_original,
)
```

**Impact**: MEDIUM - Indicates incomplete refactoring. The `_original` suffix suggests migration in progress.

**Recommendation**: 
- Verify which files are actively used (check imports)
- If refactoring is complete: Remove `sweep_original.py` and move implementation to `sweep/sweep.py`
- If refactoring is in progress: Document migration status and timeline

### Category 7: Legacy Sweep Tracker Pattern (MEDIUM PRIORITY)

**Violation**: Two implementations of sweep tracker:
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker_original.py` (1054+ lines)
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker/` (modular implementation)
- `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` (may be another version)

**Pattern**: Similar to sweep implementation - `_original` suffix suggests migration in progress.

**Impact**: MEDIUM - Indicates incomplete refactoring.

**Recommendation**:
- Check if `sweep_tracker_original.py` is still used
- Identify which is the active version
- If migration complete: Remove `sweep_tracker_original.py`
- If migration in progress: Document migration status

### Category 8: Overlapping MLflow Setup Responsibilities (LOW-MEDIUM PRIORITY)

**Potential Overlap**: Multiple modules handle MLflow setup/run creation:
- `src/infrastructure/tracking/mlflow/setup.py` - SSOT for MLflow setup (setup_mlflow)
- `src/training/execution/mlflow_setup.py` - Training-specific MLflow run creation
- `src/training/hpo/tracking/setup.py` - HPO-specific MLflow run setup
- `src/common/shared/mlflow_setup.py` - Cross-platform MLflow setup (low-level)
- `src/testing/setup/environment_setup.py` - Testing-specific MLflow initialization

**Analysis Needed**: 
- Verify these have clear separation of concerns
- `infrastructure.tracking.mlflow.setup` = SSOT for configuration
- `training.execution.mlflow_setup` = Run lifecycle for training
- `training.hpo.tracking.setup` = Run naming/context for HPO
- `common.shared.mlflow_setup` = Low-level cross-platform setup
- Verify no actual duplication, just overlapping concerns

**Impact**: LOW-MEDIUM - Need to verify no actual duplication, just overlapping concerns.

**Recommendation**: Document clear boundaries and verify no duplicate logic. Ensure all orchestration scripts use SSOT.

### Category 9: Path Resolution Patterns (LOW PRIORITY - VERIFICATION)

**Status**: Previous consolidation work exists. Need to verify no new violations.

**Files Involved**:
- `src/infrastructure/paths/utils.py` - SSOT for path resolution
- `src/infrastructure/paths/repo.py` - Repository root detection
- Various modules that may re-infer `config_dir` independently

**Recommendation**: Verify all call sites use SSOT functions. Document clear usage patterns.

### Category 10: Config Loading Patterns (LOW PRIORITY - VERIFICATION)

**Status**: Domain-specific loaders may be appropriate. Need to verify no duplication.

**Files Involved**:
- `src/common/shared/yaml_utils.py` - SSOT for YAML loading
- `src/infrastructure/config/loader.py` - Domain-specific config loaders
- `src/training/config.py` - Training-specific config builder

**Recommendation**: Verify all YAML loading uses SSOT. Document when domain-specific loaders are appropriate.

## Steps

### Step 1: Analyze and Catalog All Duplicate Functions

**Objective**: Create detailed comparison of duplicate functions to identify exact differences and usage patterns.

**Tasks**:
1. Compare `src/training/hpo/execution/azureml/sweeps.py` vs `src/training/hpo/azureml/sweeps.py` line-by-line
2. Compare `src/training/execution/jobs.py` vs `src/training/azureml/jobs.py` line-by-line
3. Compare `src/training/execution/executor.py` vs `src/infrastructure/platform/azureml/data_assets.py` for `resolve_dataset_path`
4. Document any differences (even minor ones)
5. Check all import sites to understand usage patterns:
   ```bash
   grep -r "from training.hpo.azureml.sweeps\|from training.hpo.execution.azureml.sweeps" src/ tests/
   grep -r "from training.azureml.jobs\|from training.execution.jobs" src/ tests/
   grep -r "resolve_dataset_path" src/ tests/
   ```
6. Verify which file is more actively used/maintained
7. Check for legacy file usage:
   ```bash
   grep -r "sweep_original\|sweep_tracker_original" src/ tests/ --include="*.py" | grep -v "test\|#"
   ```

**Success criteria**:
- Detailed comparison document created
- All import sites identified
- Usage patterns documented
- Decision made on which file to keep for each duplicate
- Legacy file usage status determined

**Verification**:
- Review catalog for completeness
- Verify no major patterns missed

### Step 2: Consolidate Azure ML Sweep Job Creation Functions

**Objective**: Remove duplicate `src/training/hpo/azureml/sweeps.py` and update all imports to use `src/training/hpo/execution/azureml/sweeps.py`.

**Tasks**:
1. Update all imports from `training.hpo.azureml.sweeps` to `training.hpo.execution.azureml.sweeps`
2. Verify the kept file (`execution/azureml/sweeps.py`) handles both `direction` and `goal` config patterns
3. Standardize on `objective_config.get("direction", "maximize")` pattern (more defensive)
4. Ensure `validate_sweep_job` has all features from both implementations
5. Update `src/training/README.md` if it references old import path
6. Remove `src/training/hpo/azureml/sweeps.py`
7. Run tests to verify no regressions

**Success criteria**:
- All imports updated
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- File `src/training/hpo/azureml/sweeps.py` removed
- No remaining references to old import path

**Verification**:
```bash
# Verify no remaining imports
grep -r "from training.hpo.azureml.sweeps\|import.*training.hpo.azureml.sweeps" src/ tests/
# Verify file removed
test ! -f src/training/hpo/azureml/sweeps.py
# Verify new imports work
python -c "from training.hpo.execution.azureml.sweeps import create_dry_run_sweep_job_for_backbone; print('OK')"
```

### Step 3: Consolidate Azure ML Training Job Creation Functions

**Objective**: Remove duplicate `src/training/azureml/jobs.py` and update all imports to use `src/training/execution/jobs.py`.

**Tasks**:
1. Update all imports from `training.azureml.jobs` to `training.execution.jobs`
2. Update `__init__.py` files if they export these functions
3. Remove `src/training/azureml/jobs.py`
4. Run tests to verify no regressions

**Success criteria**:
- All imports updated
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- File `src/training/azureml/jobs.py` removed
- No remaining references to old import path

**Verification**:
```bash
# Verify no remaining imports
grep -r "from training.azureml.jobs\|import.*training.azureml.jobs" src/ tests/
# Verify file removed
test ! -f src/training/azureml/jobs.py
# Verify new imports work
python -c "from training.execution.jobs import build_final_training_config; print('OK')"
```

### Step 4: Extract Shared Azure ML Helper Functions

**Objective**: Extract `_build_data_input_from_asset()` to shared utility module.

**Tasks**:
1. Create `src/infrastructure/azureml/helpers.py` (or use existing if present)
2. Move `_build_data_input_from_asset()` to shared module as `build_data_input_from_asset()` (public function)
3. Update all 4 call sites to import from shared module:
   - `src/training/hpo/execution/azureml/sweeps.py`
   - `src/training/execution/jobs.py`
4. Remove private implementations from consolidated files
5. Add proper type hints and docstring
6. Run tests to verify no regressions

**Success criteria**:
- Function extracted to `src/infrastructure/azureml/helpers.py`
- All call sites updated
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No duplicate implementations remain

**Verification**:
```bash
# Verify function exists in shared location
grep -r "def build_data_input_from_asset\|def _build_data_input_from_asset" src/
# Should show only one definition in infrastructure/azureml/helpers.py
# Verify all imports updated
grep -r "_build_data_input_from_asset" src/ | grep -v "infrastructure/azureml/helpers"
# Should show no matches
```

### Step 5: Consolidate `resolve_dataset_path` Duplicate

**Objective**: Remove duplicate `resolve_dataset_path` from `src/training/execution/executor.py` and use shared implementation.

**Tasks**:
1. Update `src/training/execution/executor.py` to import `resolve_dataset_path` from `infrastructure.platform.azureml.data_assets`
2. Remove fallback implementation from `src/training/execution/executor.py`
3. Verify the shared implementation handles the fallback case correctly
4. Run tests to verify no regressions

**Success criteria**:
- `src/training/execution/executor.py` imports from shared location
- Fallback implementation removed
- Tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Check import
grep -n "from.*resolve_dataset_path\|import.*resolve_dataset_path" src/training/execution/executor.py
# Verify no duplicate
grep -n "def resolve_dataset_path" src/training/execution/executor.py
# Should return nothing (or only import statement)
# Verify only one implementation exists
grep -r "def resolve_dataset_path" src/ --include="*.py" | wc -l
# Should be 1
```

### Step 6: Migrate or Remove Legacy sweep_original Code

**Objective**: Determine status of sweep refactoring and complete migration or document status.

**Tasks**:
1. Check if `sweep_original.py` is still imported anywhere (besides `sweep/sweep.py` and `sweep.py`):
   ```bash
   grep -r "sweep_original\|from.*sweep_original" src/ tests/ --include="*.py" | grep -v "test\|#"
   ```
2. Determine if `sweep.py` (non-directory) and `sweep/sweep.py` serve different purposes or are duplicates
3. If migration complete:
   - Move implementation from `sweep_original.py` to `sweep/sweep.py`
   - Remove wrapper pattern
   - Delete `sweep_original.py` and duplicate `sweep.py` if it exists
4. If migration in progress:
   - Document migration status in `sweep/sweep.py`
   - Add TODO comment with migration plan
   - Create separate plan for completing migration
5. Run tests to verify no regressions

**Success criteria**:
- Migration status determined and documented
- If complete: `sweep_original.py` removed, implementation in `sweep/sweep.py`
- If in progress: Status documented, separate plan created
- Tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check imports of sweep_original
grep -r "sweep_original\|from.*sweep_original" src/ tests/ --include="*.py" | grep -v "test\|#"
# If migration complete, should show no imports
```

### Step 7: Migrate or Remove Legacy sweep_tracker_original Code

**Objective**: Determine status of sweep tracker refactoring and complete migration or document status.

**Tasks**:
1. Check if `sweep_tracker_original.py` is still imported anywhere:
   ```bash
   grep -r "sweep_tracker_original\|from.*sweep_tracker_original" src/ tests/ --include="*.py" | grep -v "test\|#"
   ```
2. Compare functionality between `sweep_tracker_original.py`, `sweep_tracker.py`, and `sweep_tracker/sweep_tracker.py`
3. Identify which is the active version:
   - Check `__init__.py` exports
   - Check imports across codebase (grep for `MLflowSweepTracker`, `SweepTracker`)
   - Check test files for which version they use
4. If migration complete:
   - Verify `sweep_tracker/` module is used everywhere
   - Delete `sweep_tracker_original.py` and `sweep_tracker.py` if duplicate
5. If migration in progress:
   - Document migration status
   - Add TODO comment with migration plan
   - Create separate plan for completing migration
6. Run tests to verify no regressions

**Success criteria**:
- Migration status determined and documented
- If complete: `sweep_tracker_original.py` removed
- If in progress: Status documented, separate plan created
- Tests pass: `uvx pytest tests/`

**Verification**:
```bash
# Check imports of sweep_tracker_original
grep -r "sweep_tracker_original\|from.*sweep_tracker_original" src/ tests/ --include="*.py" | grep -v "test\|#"
# If migration complete, should show no imports
```

### Step 8: Clarify MLflow Setup Responsibilities

**Objective**: Verify no duplication in MLflow setup modules and document clear boundaries.

**Tasks**:
1. Review `src/infrastructure/tracking/mlflow/setup.py` (SSOT for setup)
2. Review `src/training/execution/mlflow_setup.py` (training run lifecycle)
3. Review `src/training/hpo/tracking/setup.py` (HPO run naming/context)
4. Review `src/common/shared/mlflow_setup.py` (low-level cross-platform setup)
5. Review `src/testing/setup/environment_setup.py` (testing-specific setup)
6. Verify no duplicate logic (setup vs run creation vs naming)
7. Check for direct calls to `common/shared/mlflow_setup` that should use SSOT:
   ```bash
   grep -r "from common.shared.mlflow_setup import setup_mlflow" src/ --include="*.py" | grep -v "infrastructure/tracking/mlflow/setup.py\|test"
   ```
8. Document clear boundaries in module docstrings
9. Add cross-references between modules for clarity
10. Update any direct calls to use SSOT

**Success criteria**:
- No duplicate logic found
- Clear boundaries documented in docstrings
- Cross-references added
- All orchestration scripts use SSOT function
- All modules follow single responsibility principle

**Verification**:
```bash
# Check for duplicate MLflow setup patterns
grep -r "mlflow.set_tracking_uri\|mlflow.set_experiment" src/ | grep -v "infrastructure/tracking/mlflow/setup.py\|test\|#"
# Should show only in SSOT module or test files
# Verify all setup goes through SSOT
grep -r "from common.shared.mlflow_setup import setup_mlflow" src/ --include="*.py" | grep -v "infrastructure/tracking/mlflow/setup.py\|test"
# Should show no matches (or only infrastructure/tracking/mlflow/setup.py)
```

### Step 9: Review and Document Path Resolution Patterns

**Objective**: Verify previous consolidation work is complete and document usage patterns.

**Tasks**:
1. Verify all call sites use `infrastructure/paths/utils.py` SSOT functions:
   ```bash
   grep -r "config_dir.*=.*Path\|infer.*config_dir" src/ --include="*.py" | grep -v "test\|infrastructure/paths" | head -20
   ```
2. Document the purpose of each path resolution function:
   - `detect_repo_root()` - Repository root detection
   - `resolve_project_paths()` - Direct resolution without fallback
   - `resolve_project_paths_with_fallback()` - Resolution with standardized fallback
   - `infer_config_dir()` - Config directory inference
3. Create decision tree: "When to use which path function"
4. Update docstrings with cross-references
5. Fix any remaining violations found

**Success criteria**:
- All call sites verified to use SSOT functions
- Clear documentation of each function's purpose
- Decision tree document created (optional, in docstrings)
- All functions have updated docstrings with cross-references
- Any remaining violations fixed

**Verification**:
- Review grep results for any violations
- Verify documentation is clear

### Step 10: Review and Document Config Loading Patterns

**Objective**: Verify all YAML loading uses SSOT and document when domain-specific loaders are appropriate.

**Tasks**:
1. Verify all YAML loading uses `common/shared/yaml_utils.load_yaml()`:
   ```bash
   grep -r "yaml\.load\|yaml\.safe_load\|import yaml" src/ --include="*.py" | grep -v "test\|common/shared/yaml_utils\|#"
   ```
2. Document the purpose of each config loader:
   - `common/shared/yaml_utils.py` - SSOT for YAML loading
   - `infrastructure/config/loader.py` - Domain-specific config loaders
   - `training/config.py` - Training-specific config builder
3. Verify domain-specific loaders use SSOT internally
4. Document when domain-specific loaders are appropriate vs violations

**Success criteria**:
- All YAML loading uses SSOT
- Domain-specific loaders documented
- No duplicate YAML loading logic
- Clear documentation of when domain-specific loaders are acceptable

**Verification**:
- Review grep results for any violations
- Verify domain-specific loaders use SSOT internally

### Step 11: Update All Call Sites to Use Consolidated Functions

**Objective**: Ensure all code uses consolidated functions after Steps 2-6.

**Tasks**:
1. Run full test suite: `uvx pytest tests/`
2. Fix any import errors
3. Fix any test failures
4. Run mypy: `uvx mypy src --show-error-codes`
5. Fix any type errors
6. Update documentation (README files) if they reference old import paths

**Success criteria**:
- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No import errors
- No runtime errors
- Documentation updated

**Verification**:
```bash
uvx pytest tests/ -v
uvx mypy src --show-error-codes
# Check for any remaining old import paths in docs
grep -r "training.hpo.azureml\|training.azureml.jobs" docs/ README.md 2>/dev/null || true
```

### Step 12: Remove Dead Code and Verify Tests Pass

**Objective**: Clean up any remaining dead code and ensure everything works.

**Tasks**:
1. Search for unused imports
2. Remove any dead code paths
3. Run full test suite: `uvx pytest tests/`
4. Run mypy: `uvx mypy src --show-error-codes`
5. Create summary of changes

**Success criteria**:
- All tests pass: `uvx pytest tests/`
- Mypy passes: `uvx mypy src --show-error-codes`
- No dead code remaining
- Summary document created

**Verification**:
```bash
uvx pytest tests/ -v
uvx mypy src --show-error-codes
# Check for unused imports (manual review)
```

## Success Criteria (Overall)

- ✅ All duplicate Azure ML job creation functions consolidated
- ✅ Shared helper functions extracted to common utilities
- ✅ Exact duplicate functions (`build_final_training_config`, `resolve_dataset_path`) consolidated
- ✅ Legacy code patterns (sweep_original, sweep_tracker_original) migrated or documented
- ✅ MLflow setup responsibilities clearly documented
- ✅ Path resolution and config loading patterns verified and documented
- ✅ All tests pass: `uvx pytest tests/`
- ✅ Mypy passes: `uvx mypy src --show-error-codes`
- ✅ No breaking changes introduced
- ✅ All imports updated to use consolidated modules

## Risk Assessment

**Low Risk**:
- Steps 2-3: Removing duplicate files (straightforward import updates)
- Step 4: Extracting helper function (simple refactoring)
- Step 5: Consolidating `resolve_dataset_path` (identical implementations)

**Medium Risk**:
- Steps 6-7: Legacy code migration (may have hidden dependencies)
- Step 8: MLflow setup clarification (need careful review)

**High Risk**:
- None identified - all changes are internal refactoring

**Mitigation**:
- Run tests after each step
- Keep git commits per step for easy rollback
- Document any deviations from plan
- Verify backward compatibility where possible

## Notes

- This unified plan consolidates insights from multiple analyses
- Follow reuse-first principles: prefer extending existing modules over creating new ones
- Maintain backward compatibility where possible
- Document any breaking changes clearly
- Previous consolidation work: `FINISHED-MASTER-20260118-1700-consolidate-scripts-utilities-dry-violations-unified.plan.md`
- This plan focuses on remaining violations not addressed in previous work

## Related Plans

- `FINISHED-MASTER-20260118-1700-consolidate-scripts-utilities-dry-violations-unified.plan.md` - Previous consolidation work for scripts and utilities
- `FINISHED-20260118-1200-consolidate-mlflow-scripts-dry-violations-unified.plan.md` - MLflow-specific consolidation


# Remove Deprecated/Compatibility Layers - Master Plan

## Goal

Remove all deprecated code paths, backward compatibility layers, and legacy fallbacks from the codebase to:
1. Simplify codebase maintenance
2. Reduce technical debt
3. Eliminate confusion about which APIs to use
4. Improve type safety by removing deprecated code paths
5. Reduce test complexity by removing compatibility test cases

This includes:

1. Remove `objective.goal` → `objective.direction` legacy config key support
2. Remove backward compatibility aliases (`execute_final_training`, `mock_trial_run`)
3. Remove legacy path resolution functions and fallbacks
4. Remove v1 study key hash fallback logic
5. Remove legacy study folder format support
6. Remove backward compatibility wrappers and convenience functions
7. Remove legacy tag registry support and legacy tag keys
8. Remove legacy run name building functions
9. Remove schema version 1.0 backward compatibility
10. Evaluate and remove MLflow Azure ML compatibility patch (if no longer needed)
11. Remove deprecated function wrappers
12. Remove legacy checkpoint path fallbacks
13. Remove backward compatibility defaults
14. Clean up deprecated attributes and internal compatibility code

## Status

**Last Updated**: 2026-01-18

### Completed Steps
- ✅ Step 1: Audit and catalog all deprecated/compatibility code
- ✅ Step 2: Remove `objective.goal` legacy config key support
- ✅ Step 3: Remove backward compatibility aliases
- ✅ Step 4: Evaluate and remove MLflow Azure ML compatibility patch (documented with TODO)
- ✅ Step 5: Remove legacy path resolution functions and fallbacks (marked as deprecated with migration path)
- ✅ Step 6: Remove v1 study key hash fallback logic (documented where v1 still needed)
- ✅ Step 7: Remove legacy study folder format support
- ✅ Step 8: Remove legacy run name building functions
- ✅ Step 9: Remove legacy tag keys and tag registry support
- ✅ Step 10: Remove schema version 1.0 backward compatibility
- ✅ Step 11: Remove backward compatibility wrappers and convenience functions
- ✅ Step 12: Remove deprecated function wrappers
- ✅ Step 13: Remove legacy checkpoint path fallbacks (documented with TODOs where needed)
- ✅ Step 14: Remove backward compatibility defaults
- ✅ Step 15: Clean up deprecated attributes and internal compatibility code

### Pending Steps
- ✅ Step 16: Update tests to remove legacy test cases
- ✅ Step 17: Update documentation
- ✅ Step 18: Final verification and cleanup

## Preconditions

- All existing tests must pass before starting: `uvx pytest tests/`
- Mypy must pass: `uvx mypy src --show-error-codes`
- No active PRs that would conflict with these changes
- Backup of current state (git commit before starting)
- **Verification**: Confirm no production code/configs use deprecated patterns:
  ```bash
  # Check for objective.goal usage in config files
  grep -r "goal:" config/ --include="*.yaml" --include="*.yml" | grep -v "direction:" | grep -v "#" | wc -l
  # Should return 0
  ```

## Analysis Summary

### Deprecated/Compatibility Layers Identified

| Layer | Location | Status | Replacement | Priority |
|-------|----------|--------|-------------|----------|
| `objective.goal` config key | `src/infrastructure/config/selection.py` | Deprecated with warning | `objective.direction` | High |
| `execute_final_training` alias | `src/training/execution/__init__.py` | Backward compat alias | `run_final_training_workflow` | Medium |
| `mock_trial_run` alias | `tests/selection/conftest.py` | Backward compat alias | `mock_hpo_trial_run` | Low |
| `resolve_output_path()` | `src/infrastructure/paths/resolve.py` | Legacy function | Use `resolve_storage_path()` or domain-specific resolvers | Medium |
| v1 study key hash fallback | `src/training/hpo/tracking/setup.py` | Fallback logic | Use v2 hash only | High |
| Legacy study folder format | `src/training/hpo/checkpoint/storage.py` | Fallback support | Use v2 hash-based paths only | High |
| `self.goal` attribute | `src/training/hpo/core/study.py` | Internal compat | Use `self.direction` only | Medium |
| `translate_search_space_to_optuna()` | `src/training/hpo/core/search_space.py` | Backward compat wrapper | Use `SearchSpaceTranslator.to_optuna()` | Medium |
| `create_search_space()` | `src/training/hpo/core/search_space.py` | Backward compat wrapper | Use `SearchSpaceTranslator.to_azure_ml()` | Medium |
| Legacy tag registry | `tests/tracking/unit/test_tags_comprehensive.py` | Test-only | Remove test cases | Low |
| `get_legacy_trial_number()` | `src/infrastructure/naming/mlflow/tag_keys.py` | Legacy function | Use modern tag keys | Medium |
| `_build_legacy_run_name()` | `src/infrastructure/naming/mlflow/run_names.py` | Legacy function | Use modern naming policy | Medium |
| `create_mlflow_run_name()` | `src/training/hpo/utils/helpers.py` | Legacy fallback | Use `build_mlflow_run_name()` | Medium |
| Schema version 1.0 support | Multiple files | Backward compat | Use schema version 2.0 only | High |
| MLflow compatibility patch | `src/infrastructure/tracking/mlflow/compatibility.py` | May still be needed | Verify if still needed | Low |
| `find_repository_root()` wrapper | `src/common/shared/notebook_setup.py` | Deprecated wrapper | Use `detect_repo_root()` | Low |
| Legacy checkpoint paths | Multiple files | Fallback support | Use modern checkpoint paths | Medium |
| Backward compatibility defaults | Multiple files | Silent fallbacks | Fail fast with clear errors | Medium |

### Impact Assessment

**Files to Modify**: ~25-30 files
- Source files: ~15 files
- Test files: ~12-15 files
- Documentation: ~8-10 files
- Notebooks: ~2-3 files

**Breaking Changes**: 
- ⚠️ **Config files**: Any configs using `objective.goal` will break (verify none exist first)
- ⚠️ **Test code**: Tests using `mock_trial_run` will need to use `mock_hpo_trial_run`
- ⚠️ **Import code**: Code using `execute_final_training` will need to use `run_final_training_workflow`
- ⚠️ **Schema version**: Code expecting schema version 1.0 will break (should use 2.0)

**Risk Level**: Medium-High (requires careful verification that no production code uses deprecated patterns)

## Steps

### Step 1: Audit and Catalog All Deprecated/Compatibility Code

**Goal**: Create comprehensive inventory of all deprecated code and compatibility layers.

**Tasks**:
1. Search codebase for all deprecated markers, compatibility comments, and legacy fallbacks:
   ```bash
   grep -r "deprecated\|DEPRECATED\|legacy\|LEGACY\|compatibility\|COMPATIBILITY\|fallback\|FALLBACK\|backward.*compat" --include="*.py" src/ tests/ | grep -v "#.*historical\|#.*removed" | sort | uniq
   ```
2. Search for specific deprecated patterns:
   - `objective.goal` usage
   - Compatibility module imports
   - Legacy function calls (`_build_legacy_run_name`, `get_legacy_trial_number`, `create_mlflow_run_name`)
   - Schema version 1.0 defaults
   - Legacy path fallbacks
   - Backward compatibility comments/defaults
3. Document each deprecated item with:
   - File path and line numbers
   - Purpose and reason for deprecation
   - Current usage count (grep results)
   - Dependencies and callers
   - Migration path
   - Test cases that test deprecated functionality
4. Categorize by removal priority (High/Medium/Low)
5. Create inventory document: `docs/implementation_plans/audits/deprecated-compatibility-inventory.md`

**Success criteria**:
- Complete inventory document created
- All deprecated code items categorized and prioritized
- Usage counts verified with grep/codebase search
- Test cases identified for each deprecated feature
- Migration paths documented

**Verification**:
```bash
# Verify comprehensive search
grep -r "deprecated\|DEPRECATED\|legacy\|LEGACY\|compatibility\|COMPATIBILITY\|fallback\|FALLBACK" --include="*.py" src/ tests/ | wc -l

# Check for TODO/FIXME markers
grep -r "TODO.*deprecat\|FIXME.*deprecat\|XXX.*deprecat" --include="*.py" src/ tests/

# Verify inventory document exists
test -f docs/implementation_plans/audits/deprecated-compatibility-inventory.md && echo "✓ Inventory created"
```

### Step 2: Remove `objective.goal` Legacy Config Key Support

**Goal**: Remove support for deprecated `objective.goal` config key, requiring all configs to use `objective.direction`.

**Tasks**:
1. **Verify no config files use `objective.goal`**:
   ```bash
   grep -r "goal:" config/ --include="*.yaml" --include="*.yml" | grep -v "direction:" | grep -v "#" | wc -l
   ```
   Should return 0. If not, update configs first.
2. **Remove deprecation warning and legacy support** from `src/infrastructure/config/selection.py`:
   - Remove `objective.get("goal")` fallback logic
   - Remove deprecation warning code
   - Keep only `objective.get("direction", "maximize")`
3. **Remove legacy goal support** from `src/training/hpo/core/study.py`:
   - Remove `self.goal = self.direction` line (line 170)
   - Remove any references to `self.goal` attribute
4. **Update tests** that test legacy goal key migration:
   - Remove `test_legacy_goal_key_migration` from `tests/training/hpo/unit/test_phase2_tags.py`
   - Remove tests for `objective.goal` extraction from selection config tests:
     - `tests/selection/unit/test_best_model_selection_config_comprehensive.py`
     - `tests/selection/unit/test_best_model_selection_config.py`
     - `tests/selection/integration/test_best_model_selection_config_integration.py`
     - `tests/selection/unit/test_best_model_selection_options.py`
   - Update any tests that verify goal/direction compatibility

**Success criteria**:
- No code supports `objective.goal` config key
- All configs use `objective.direction`
- Tests updated to remove legacy goal tests
- Mypy passes: `uvx mypy src/infrastructure/config src/training/hpo/core --show-error-codes`

**Verification**:
```bash
# Should return 0
grep -r "objective\.goal\|\.get\(\"goal\"\)" src/ --include="*.py" | grep -v "#\|test" | wc -l

# Verify no goal attribute in Study class
grep -n "self\.goal\|\.goal\s*=" src/training/hpo/core/study.py | wc -l

# Check tests
grep -r "legacy.*goal\|goal.*legacy" tests/ --include="*.py" | wc -l

# Run config tests
uvx pytest tests/infrastructure/config/ tests/selection/ -v
```

### Step 3: Remove Backward Compatibility Aliases

**Goal**: Remove backward compatibility aliases that are no longer needed.

**Tasks**:
1. **Remove `execute_final_training` alias** from `src/training/execution/__init__.py`:
   - Remove the `__getattr__` handler for `execute_final_training` (lines 64-67)
   - Remove from `__all__` list (line 54)
   - Remove from `src/training/__init__.py` `__all__` list if present
2. **Remove `mock_trial_run` alias** from `tests/selection/conftest.py`:
   - Remove line: `mock_trial_run = mock_hpo_trial_run` (line 125)
   - Remove comment about backward compatibility
3. **Find and update all usages**:
   ```bash
   # Find usages of execute_final_training
   grep -r "execute_final_training" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb"
   
   # Find usages of mock_trial_run
   grep -r "mock_trial_run" tests/ --include="*.py"
   ```
4. **Update all usages**:
   - Replace `execute_final_training` → `run_final_training_workflow`
   - Replace `mock_trial_run` → `mock_hpo_trial_run` (in test fixtures)
5. **Check for other aliases**:
   - Review `src/training/execution/__init__.py` for other backward compat aliases
   - Review `src/training/__init__.py` for other backward compat aliases
   - Review test conftest files (`tests/hpo/conftest.py`, `tests/hpo/integration/conftest.py`) for other aliases

**Success criteria**:
- No backward compatibility aliases remain
- All usages updated to use canonical names
- Tests updated to use canonical fixture names
- Mypy passes: `uvx mypy src/training --show-error-codes`

**Verification**:
```bash
# Should return 0
grep -r "execute_final_training\|mock_trial_run" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb" | grep -v "#\|test.*execute\|test.*mock" | wc -l

# Verify aliases removed
grep -n "execute_final_training\|mock_trial_run" src/training/execution/__init__.py tests/selection/conftest.py | wc -l

# Find other aliases
grep -r "Alias for backward compatibility\|backward compatibility\|=.*#.*alias" --include="conftest.py" tests/
```

### Step 4: Evaluate and Remove MLflow Azure ML Compatibility Patch

**Goal**: Determine if Azure ML compatibility patch is still needed, remove if not.

**Tasks**:
1. **Check Azure ML and MLflow versions** in `pyproject.toml` or requirements
2. **Find all imports** of compatibility module:
   ```bash
   grep -r "from.*compatibility\|import.*compatibility" src/ tests/ notebooks/
   ```
3. **Test if patch is still needed**:
   - Temporarily comment out patch application in `src/infrastructure/tracking/mlflow/compatibility.py`
   - Run tests that use Azure ML artifacts: `uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py -v`
   - Check if errors occur without patch
4. **If patch is still needed**:
   - Document why it's needed and when it can be removed
   - Add TODO with version requirements
   - Skip removal for now
5. **If patch is not needed**:
   - Remove `src/infrastructure/tracking/mlflow/compatibility.py`
   - Remove import from `src/infrastructure/tracking/mlflow/__init__.py` if present
   - Remove import from `src/deployment/conversion/execution.py` if present
   - Remove `_ensure_azureml_compatibility` calls from `src/infrastructure/tracking/mlflow/setup.py` if present
   - Update any tests that reference compatibility module

**Success criteria**:
- Decision documented (keep or remove)
- If removed: file deleted, imports updated, tests pass
- If kept: TODO added with removal criteria

**Verification**:
```bash
# Check if compatibility module exists (if removed)
test -f src/infrastructure/tracking/mlflow/compatibility.py && echo "Still exists" || echo "Removed"

# Check imports
grep -r "from.*compatibility import\|import.*compatibility" --include="*.py" src/ tests/

# Run MLflow artifact tests
uvx pytest tests/tracking/unit/test_azureml_artifact_upload.py -v
```

### Step 5: Remove Legacy Path Resolution Functions and Fallbacks

**Goal**: Remove legacy path resolution functions and fallback logic.

**Tasks**:
1. **Identify legacy path functions**:
   - `resolve_output_path()` in `src/infrastructure/paths/resolve.py` (marked as legacy)
   - Check for other legacy path resolution functions
2. **Find all usages**:
   ```bash
   grep -r "resolve_output_path" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb"
   ```
3. **Update usages** to use modern path resolution:
   - Replace with `resolve_storage_path()` or domain-specific resolvers
   - Update imports if needed
4. **Remove legacy function**:
   - Remove `resolve_output_path()` function from `src/infrastructure/paths/resolve.py`
   - Remove from `__all__` if exported
   - Update module docstring if it references the function
5. **Remove legacy `resolve_storage_path` fallback** from `src/training/hpo/utils/helpers.py`:
   - Remove fallback to legacy path resolution
   - Update callers to use v2 paths only
6. **Check for other legacy path functions**:
   - Review `src/infrastructure/paths/` for other legacy functions
   - Check for "legacy" or "backward compatibility" comments

**Success criteria**:
- No legacy path resolution functions remain
- All usages updated to modern path resolution
- No legacy path fallbacks
- Mypy passes: `uvx mypy src/infrastructure/paths --show-error-codes`

**Verification**:
```bash
# Should return 0
grep -r "resolve_output_path" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb" | wc -l

# Verify function removed
grep -n "def resolve_output_path" src/infrastructure/paths/resolve.py | wc -l

# Verify no legacy fallbacks
grep -r "legacy.*path\|fallback.*legacy.*path" src/infrastructure/paths/ src/training/hpo/utils/helpers.py
```

### Step 6: Remove v1 Study Key Hash Fallback Logic

**Goal**: Remove fallback to v1 study key hash computation, requiring all code to use v2 hash.

**Tasks**:
1. **Identify v1 hash fallback locations**:
   - `src/training/hpo/tracking/setup.py` - Falls back to v1 hash computation
   - `src/training/hpo/execution/local/sweep.py` - May have v1 fallback logic
   - `src/training/hpo/trial/meta.py` - Uses v1 hash computation
   - `src/evaluation/selection/trial_finder.py` - May have v1 hash support
   - `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - May have v1 hash fallback
2. **Find all usages of `build_hpo_study_key()` (v1)**:
   ```bash
   grep -r "build_hpo_study_key(" src/ tests/ --include="*.py" | grep -v "build_hpo_study_key_v2\|build_hpo_study_key_hash"
   ```
3. **Update to use v2 hash only**:
   - Replace `build_hpo_study_key()` → `build_hpo_study_key_v2()`
   - Remove fallback logic that uses v1 hash
   - Update comments that mention v1 fallback
4. **Remove v1 hash computation function** (if safe):
   - Check if `build_hpo_study_key()` is still needed for migration/backward compat
   - If not needed, consider deprecating or removing (may need separate step)
   - **Note**: This may be kept for migration purposes - verify first
5. **Update tests**:
   - Remove tests that verify v1 fallback behavior
   - Update tests to use v2 hash only
   - Remove v1 hash computation tests if no longer relevant

**Success criteria**:
- No fallback to v1 hash computation
- All code uses v2 hash (`build_hpo_study_key_v2()`)
- Tests updated to use v2 hash only
- Mypy passes: `uvx mypy src/training/hpo src/evaluation/selection --show-error-codes`

**Verification**:
```bash
# Should return 0 (or only in migration/backward compat code)
grep -r "build_hpo_study_key(" src/ --include="*.py" | grep -v "build_hpo_study_key_v2\|build_hpo_study_key_hash\|#\|def build_hpo_study_key" | wc -l

# Verify fallback logic removed
grep -n "v1\|fallback.*v1\|legacy.*hash" src/training/hpo/tracking/setup.py | wc -l

# Run HPO tests
uvx pytest tests/training/hpo/ tests/infrastructure/paths/ -v
```

### Step 7: Remove Legacy Study Folder Format Support

**Goal**: Remove support for legacy study folder formats, requiring v2 hash-based paths only.

**Tasks**:
1. **Identify legacy folder format support**:
   - `src/training/hpo/checkpoint/storage.py` - Falls back to legacy study_name format
   - `src/training/hpo/execution/local/sweep.py` - May have legacy folder support
   - `src/training/hpo/checkpoint/cleanup.py` - Checks old structure (backward compatibility)
2. **Find all legacy folder references**:
   ```bash
   grep -r "legacy.*folder\|legacy.*study\|study_name.*format\|old.*structure" src/training/hpo/ --include="*.py" -i
   ```
3. **Remove legacy folder format support**:
   - Remove fallback to `study_name` format in `resolve_storage_path()` calls
   - Remove checks for old folder structures
   - Remove backward compatibility comments
4. **Update path resolution**:
   - Ensure all path resolution uses v2 hash-based paths only
   - Remove `study_name` parameter support if it's only for backward compat
5. **Update tests**:
   - Remove tests that verify legacy folder format fallback
   - Update tests to use v2 hash-based paths only
   - Remove `test_checkpoint_path_fallback_to_legacy_when_no_hash` from `tests/hpo/integration/test_hpo_sweep_setup.py` if present

**Success criteria**:
- No legacy folder format support
- All paths use v2 hash-based format
- Tests updated to remove legacy folder tests
- Mypy passes: `uvx mypy src/training/hpo/checkpoint --show-error-codes`

**Verification**:
```bash
# Should return 0 (or only in comments/docs)
grep -r "legacy.*study.*folder\|study_name.*format\|old.*structure" src/training/hpo/ --include="*.py" -i | grep -v "#\|'''\|'''" | wc -l

# Verify fallback removed
grep -n "fallback.*legacy\|legacy.*fallback" src/training/hpo/checkpoint/storage.py | wc -l

# Run HPO path tests
uvx pytest tests/hpo/integration/test_hpo_sweep_setup.py -v
```

### Step 8: Remove Legacy Run Name Building Functions

**Goal**: Remove legacy run name building functions and ensure all code uses modern naming policy.

**Tasks**:
1. **Find all legacy run name functions**:
   - `_build_legacy_run_name()` in `src/infrastructure/naming/mlflow/run_names.py`
   - `create_mlflow_run_name()` in `src/training/hpo/utils/helpers.py` (legacy fallback)
2. **Find all usages**:
   ```bash
   grep -r "_build_legacy_run_name\|create_mlflow_run_name" src/ tests/ --include="*.py"
   ```
3. **Update callers** to use modern naming:
   - Replace `_build_legacy_run_name()` → Use modern naming policy
   - Replace `create_mlflow_run_name()` → `infrastructure.naming.mlflow.run_names.build_mlflow_run_name()`
   - Update `setup_hpo_mlflow_run()` to remove fallback to legacy function
4. **Remove legacy functions**:
   - Remove `_build_legacy_run_name()` function
   - Remove `create_mlflow_run_name()` function
   - Remove fallback logic that calls legacy function when policy unavailable
   - Ensure naming policy is always available (no fallback needed)
5. **Update tests**:
   - Remove tests for legacy run name building
   - Update tests to use modern naming policy

**Success criteria**:
- `_build_legacy_run_name()` function removed
- `create_mlflow_run_name()` function removed
- No calls to legacy run name building remain
- All run names use modern naming policy
- Tests pass: `uvx pytest tests/tracking/unit/test_naming_*.py`

**Verification**:
```bash
# Verify functions removed
grep -r "_build_legacy_run_name\|def create_mlflow_run_name" src/ tests/

# Verify no fallback logic
grep -r "legacy.*run.*name\|fallback.*legacy\|last.*resort" src/infrastructure/naming/ src/training/hpo/tracking/setup.py

# Run naming tests
uvx pytest tests/tracking/unit/test_naming_*.py -v
```

### Step 9: Remove Legacy Tag Keys and Tag Registry Support

**Goal**: Remove legacy tag key functions and tag registry support.

**Tasks**:
1. **Find legacy tag key functions**:
   - `get_legacy_trial_number()` in `src/infrastructure/naming/mlflow/tag_keys.py`
   - `LEGACY_TRIAL_NUMBER` mapping if present
   - Legacy tag registry in `tests/tracking/unit/test_tags_comprehensive.py`
2. **Find all usages**:
   ```bash
   grep -r "get_legacy_trial_number\|LEGACY_TRIAL_NUMBER\|legacy.*tag\|tag.*legacy\|registry\.key\(\"legacy\"" src/ tests/ --include="*.py" -i
   ```
3. **Remove legacy tag key functions**:
   - Remove `get_legacy_trial_number()` function
   - Remove `LEGACY_TRIAL_NUMBER` mapping if present
   - Remove from `__all__` exports
4. **Remove legacy tag registry tests**:
   - Remove test cases for "legacy" tag registry from `test_tags_comprehensive.py`
   - Remove any other tests that verify legacy tag behavior
5. **Check for legacy tag registry in code**:
   - Review `src/infrastructure/naming/mlflow/tags_registry.py` for legacy registry support
   - Remove if present and no longer needed

**Success criteria**:
- `get_legacy_trial_number()` function removed
- `LEGACY_TRIAL_NUMBER` mapping removed (if exists)
- No references to legacy tag keys remain
- Legacy tag registry tests removed
- Tests pass: `uvx pytest tests/tracking/unit/test_tags_*.py`

**Verification**:
```bash
# Verify function removed
grep -r "get_legacy_trial_number\|LEGACY_TRIAL_NUMBER" src/ tests/

# Verify legacy tag registry tests removed
grep -n "legacy" tests/tracking/unit/test_tags_comprehensive.py | wc -l

# Run tag tests
uvx pytest tests/tracking/unit/test_tags_*.py -v
```

### Step 10: Remove Schema Version 1.0 Backward Compatibility

**Goal**: Remove support for schema version 1.0, enforce schema version 2.0 only.

**Tasks**:
1. **Find all schema version 1.0 defaults**:
   ```bash
   grep -r 'schema_version.*"1\.0"\|default.*"1\.0".*backward\|backward.*compat.*"1\.0"' src/ tests/
   ```
2. **Update files** to remove schema_version "1.0" defaults:
   - `src/training/hpo/execution/local/sweep.py` - Remove schema_version "1.0" default
   - `src/evaluation/selection/trial_finder.py` - Remove schema_version "1.0" default
   - `src/infrastructure/naming/mlflow/hpo_keys.py` - Remove schema_version "1.0" defaults
   - `src/infrastructure/naming/mlflow/refit_keys.py` - Remove schema_version "1.0" default
3. **Update config handling**:
   - Update `src/infrastructure/config/selection.py` to remove "1.0" from `prefer_schema_version` options
   - Update config files to remove `prefer_schema_version: "1.0"` option
   - `prefer_schema_version` should only accept "2.0" or "auto" (auto prefers 2.0)
4. **Remove logic** that handles schema_version "1.0" vs "2.0" differences
5. **Update all tests** that use schema_version "1.0" to use "2.0"

**Success criteria**:
- All schema_version defaults changed to "2.0"
- `prefer_schema_version` only accepts "2.0" or "auto" (auto prefers 2.0)
- No code handles schema_version "1.0" differences
- All tests updated to use schema_version "2.0"
- Config files updated to remove "1.0" option

**Verification**:
```bash
# Verify no schema_version "1.0" defaults
grep -r 'schema_version.*"1\.0"\|default.*"1\.0"' src/

# Verify prefer_schema_version updated
grep -r "prefer_schema_version" src/infrastructure/config/selection.py

# Verify config files updated
grep -r 'prefer_schema_version.*"1\.0"' config/

# Run selection tests
uvx pytest tests/selection/ tests/evaluation/selection/ -v
```

### Step 11: Remove Backward Compatibility Wrappers and Convenience Functions

**Goal**: Remove convenience wrapper functions that are marked for backward compatibility.

**Tasks**:
1. **Identify backward compatibility wrappers**:
   - `translate_search_space_to_optuna()` in `src/training/hpo/core/search_space.py`
   - `create_search_space()` in `src/training/hpo/core/search_space.py`
   - Check for other wrappers marked "for backward compatibility"
2. **Find all usages**:
   ```bash
   grep -r "translate_search_space_to_optuna\|create_search_space" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb"
   ```
3. **Update usages** to use canonical implementations:
   - Replace `translate_search_space_to_optuna()` → `SearchSpaceTranslator.to_optuna()`
   - Replace `create_search_space()` → `SearchSpaceTranslator.to_azure_ml()`
   - Update imports
4. **Remove wrapper functions**:
   - Remove `translate_search_space_to_optuna()` function
   - Remove `create_search_space()` function
   - Remove "Convenience functions for backward compatibility" comment block
   - Remove from `__all__` if exported
5. **Check for other wrappers**:
   - Review codebase for other "backward compatibility" wrappers
   - Check `src/infrastructure/storage/drive.py` for backward compat callbacks
   - Check `src/infrastructure/paths/drive.py` for backward compat functions

**Success criteria**:
- No backward compatibility wrapper functions remain
- All usages updated to use canonical implementations
- Mypy passes: `uvx mypy src/training/hpo/core --show-error-codes`

**Verification**:
```bash
# Should return 0
grep -r "translate_search_space_to_optuna\|create_search_space" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb" | grep -v "#\|def\|class" | wc -l

# Verify wrappers removed
grep -n "def translate_search_space_to_optuna\|def create_search_space" src/training/hpo/core/search_space.py | wc -l
```

### Step 12: Remove Deprecated Function Wrappers

**Goal**: Remove deprecated function wrappers and update callers.

**Tasks**:
1. **Identify deprecated function wrappers**:
   - `find_repository_root()` in `src/common/shared/notebook_setup.py` (wrapper for `detect_repo_root()`)
   - Check for other deprecated wrappers
2. **Find all usages**:
   ```bash
   grep -r "find_repository_root" src/ tests/ notebooks/ --include="*.py" --include="*.ipynb"
   ```
3. **Update callers** to use canonical functions:
   - Replace `find_repository_root()` → `infrastructure.paths.repo.detect_repo_root()`
   - Update notebooks:
     - `notebooks/01_orchestrate_training_colab.ipynb`
     - Any other notebooks using the function
4. **Remove wrapper functions**:
   - Remove `find_repository_root()` function from `src/common/shared/notebook_setup.py`
   - Update `setup_notebook_paths()` if it uses the wrapper
   - Remove from `__all__` if exported

**Success criteria**:
- `find_repository_root()` wrapper removed
- Notebooks updated to use canonical function
- Notebooks execute successfully
- Mypy passes: `uvx mypy src/common/shared/notebook_setup.py --show-error-codes`

**Verification**:
```bash
# Verify wrapper removed
grep -r "def find_repository_root" --include="*.py" src/common/shared/notebook_setup.py

# Check notebook usage
grep -r "find_repository_root" --include="*.ipynb" notebooks/

# Verify canonical function used
grep -r "from infrastructure.paths.repo import detect_repo_root" --include="*.ipynb" notebooks/
```

### Step 13: Remove Legacy Checkpoint Path Fallbacks

**Goal**: Remove legacy checkpoint path fallback logic, document migration path if needed.

**Tasks**:
1. **Review legacy checkpoint path fallbacks**:
   - `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - Legacy checkpoint structure fallback
   - `src/evaluation/selection/trial_finder.py` - Legacy checkpoint path fallbacks
   - `src/common/shared/platform_detection.py` - Legacy checkpoint directory
   - `src/training/hpo/checkpoint/cleanup.py` - Checks old structure (backward compatibility)
2. **Find all legacy checkpoint references**:
   ```bash
   grep -r "legacy.*checkpoint\|checkpoint.*legacy\|Strategy.*Legacy\|Legacy.*structure\|trial_N_foldK\|legacy.*pattern" --include="*.py" src/
   ```
3. **Determine if fallbacks are still needed**:
   - Check if old runs still exist that need these fallbacks
   - Document migration path if removal would break old runs
4. **If safe to remove**:
   - Remove fallback logic from all locations
   - Update tests that test legacy checkpoint paths
   - Update documentation
5. **If not safe to remove**:
   - Document why fallbacks are needed
   - Add TODO with removal criteria
   - Skip removal for now

**Success criteria**:
- Decision documented (remove or keep with TODO)
- If removed: fallback logic removed, tests updated, documentation updated
- If kept: TODO added with removal criteria

**Verification**:
```bash
# Check for legacy checkpoint fallbacks
grep -r "legacy.*checkpoint\|checkpoint.*legacy\|Strategy.*Legacy\|Legacy.*structure" --include="*.py" src/

# Check for old checkpoint patterns
grep -r "trial_N_foldK\|legacy.*pattern" --include="*.py" src/
```

### Step 14: Remove Backward Compatibility Defaults

**Goal**: Remove backward compatibility defaults and comments throughout codebase.

**Tasks**:
1. **Search for backward compatibility defaults**:
   ```bash
   grep -r "backward.*compat.*default\|default.*backward\|backward.*compat" src/ --include="*.py" -i | grep -v "#.*historical\|#.*removed"
   ```
2. **Remove backward compatibility defaults** from:
   - `src/infrastructure/paths/config.py` (line 82: "Return defaults if config doesn't exist (backward compatibility)")
   - `src/infrastructure/naming/mlflow/tags_registry.py` (line 184: backward compatibility fallback)
   - Any other files with backward compatibility defaults
3. **Update error handling** to fail fast instead of using backward compatibility defaults
4. **Remove backward compatibility comments** (except in historical context)

**Success criteria**:
- No "backward compatibility" comments remain (except in historical context)
- No backward compatibility defaults remain
- Code fails fast with clear errors instead of silent fallbacks
- Tests updated to handle new error behavior

**Verification**:
```bash
# Verify no backward compatibility defaults
grep -r "backward.*compat\|backward compat" src/ --include="*.py" | grep -v "#.*historical\|#.*removed"

# Verify error handling updated
grep -r "backward.*compat.*default\|default.*backward" src/
```

### Step 15: Clean Up Deprecated Attributes and Internal Compatibility Code

**Goal**: Remove deprecated internal attributes and compatibility code that's no longer needed.

**Tasks**:
1. **Identify deprecated internal attributes**:
   - `self.goal` in `Study` class (already handled in Step 2, verify removed)
   - Check for other deprecated attributes with compatibility assignments
2. **Find compatibility code patterns**:
   ```bash
   grep -r "for backward compatibility\|backward compat\|deprecated.*but\|keep.*for.*compat" src/ --include="*.py" -i
   ```
3. **Review and remove**:
   - Remove deprecated attribute assignments
   - Remove compatibility code comments
   - Remove "kept for backward compatibility" code blocks
4. **Check for re-exports**:
   - Review `src/infrastructure/tracking/mlflow/artifacts/__init__.py` for backward compat re-exports
   - Review `src/training/execution/__init__.py` for other backward compat code
   - Review `src/training/__init__.py` for backward compat exports
5. **Clean up compatibility imports**:
   - Check for compatibility module imports (already handled in Step 4)
   - Remove any remaining compatibility-related code

**Success criteria**:
- No deprecated internal attributes
- No unnecessary compatibility code
- Code is cleaner and easier to maintain
- Mypy passes: `uvx mypy src --show-error-codes`

**Verification**:
```bash
# Should return 0 (or only in comments/docs)
grep -r "for backward compatibility\|backward compat\|deprecated.*but\|keep.*for.*compat" src/ --include="*.py" -i | grep -v "#\|'''\|'''" | wc -l

# Verify deprecated attributes removed
grep -n "self\.goal\|\.goal\s*=" src/training/hpo/core/study.py | wc -l
```

### Step 16: Update Tests to Remove Legacy Test Cases

**Goal**: Remove all test cases that verify legacy/deprecated behavior.

**Tasks**:
1. **Find legacy test cases**:
   ```bash
   grep -r "test.*legacy\|legacy.*test\|test.*deprecated\|deprecated.*test\|test.*compatibility\|test.*fallback" tests/ --include="*.py" -i
   ```
2. **Review and remove**:
   - Remove `test_legacy_goal_key_migration` (from Step 2)
   - Remove `test_checkpoint_path_fallback_to_legacy_when_no_hash` (from Step 7)
   - Remove tests for v1 hash fallback (from Step 6)
   - Remove tests for legacy tag registry (from Step 9)
   - Remove tests for backward compatibility wrappers (from Step 11)
   - Remove tests for schema version 1.0 handling (from Step 10)
   - Remove tests for legacy run name building (from Step 8)
   - Remove tests for legacy checkpoint paths (from Step 13)
3. **Update test fixtures**:
   - Remove `mock_trial_run` alias (from Step 3)
   - Update test imports to use canonical names
4. **Update test documentation**:
   - Remove references to legacy behavior from test READMEs
   - Update test examples to use canonical APIs
5. **Run tests** to verify:
   ```bash
   uvx pytest tests/ -v --tb=short
   ```

**Success criteria**:
- No legacy test cases remain
- All tests use canonical APIs
- Tests pass: `uvx pytest tests/`
- Test documentation updated

**Verification**:
```bash
# Should return 0
grep -r "test.*legacy\|legacy.*test\|test.*deprecated\|deprecated.*test" tests/ --include="*.py" -i | grep -v "#" | wc -l

# Run tests
uvx pytest tests/ -v --tb=short
```

### Step 17: Update Documentation

**Goal**: Update all documentation to remove references to deprecated/compatibility layers.

**Tasks**:
1. **Find documentation references**:
   ```bash
   grep -r "backward compatibility\|backward compat\|legacy\|deprecated" docs/ README.md src/*/README.md --include="*.md" -i
   ```
2. **Update README files**:
   - Remove references to `objective.goal` (use `objective.direction` only)
   - Remove references to `execute_final_training` (use `run_final_training_workflow`)
   - Remove references to legacy path resolution
   - Remove references to v1 hash fallback
   - Remove references to legacy folder formats
   - Remove references to schema version 1.0
   - Update import examples to use canonical names
3. **Update code comments**:
   - Remove "backward compatibility" comments from code
   - Update docstrings to remove deprecated parameter references
   - Update function documentation
4. **Update implementation plan summaries**:
   - Update any summaries that reference deprecated code
   - Mark deprecated code removal as complete

**Success criteria**:
- Documentation updated to reflect current APIs
- No references to deprecated patterns
- Import examples use canonical names
- Code comments cleaned up

**Verification**:
```bash
# Should return 0 (or only in historical context)
grep -r "objective\.goal\|execute_final_training\|backward compatibility\|legacy.*format\|schema.*version.*1\.0" docs/ README.md src/*/README.md --include="*.md" -i | grep -v "deprecated\|removed\|historical" | wc -l
```

### Step 18: Final Verification and Cleanup

**Goal**: Ensure all deprecated code removed, tests pass, and codebase is clean.

**Tasks**:
1. **Run comprehensive search** for any remaining deprecated/compatibility code:
   ```bash
   grep -r "deprecated\|DEPRECATED\|legacy\|LEGACY\|compatibility\|COMPATIBILITY\|backward.*compat\|fallback\|FALLBACK" src/ tests/ | grep -v "#.*historical\|#.*removed\|#.*deprecated\|test.*deprecated\|deprecated.*test" | head -50
   ```
2. **Run full test suite**:
   ```bash
   uvx pytest tests/ -v --tb=short
   ```
   Fix any test failures
3. **Run mypy**:
   ```bash
   uvx mypy src --show-error-codes
   ```
   Fix any type errors
4. **Check for import errors**:
   ```bash
   python -c "
   from training.execution import run_final_training_workflow
   from training.hpo.core.search_space import SearchSpaceTranslator
   from infrastructure.naming.mlflow.hpo_keys import build_hpo_study_key_v2
   print('✓ All imports work')
   "
   ```
5. **Verify no deprecated code remains**:
   ```bash
   # Should return 0 or very few (only in comments/docs)
   grep -r "objective\.goal\|execute_final_training\|mock_trial_run\|resolve_output_path\|build_hpo_study_key(\|_build_legacy_run_name\|get_legacy_trial_number\|create_mlflow_run_name\|schema_version.*\"1\.0\"" src/ --include="*.py" | grep -v "#\|test\|def\|class" | wc -l
   ```
6. **Check notebooks** for any deprecated imports/comments
7. **Create summary document** of what was removed

**Success criteria**:
- All tests pass
- Mypy passes with 0 errors
- No import errors
- No deprecated code remains (except in comments/docs)
- Summary document created

**Verification**:
```bash
# Run tests
uvx pytest tests/ -v --tb=short

# Run mypy
uvx mypy src --show-error-codes

# Check for deprecated code
grep -r "objective\.goal\|execute_final_training\|mock_trial_run\|resolve_output_path\|build_hpo_study_key(\|_build_legacy_run_name\|get_legacy_trial_number\|create_mlflow_run_name\|schema_version.*\"1\.0\"" src/ --include="*.py" | grep -v "#\|test\|def\|class" | wc -l

# Check notebooks
grep -r "deprecated\|legacy\|compatibility" notebooks/ --include="*.ipynb"
```

## Success Criteria (Overall)

- ✅ All deprecated/compatibility layers removed from codebase
- ✅ All code uses modern patterns (no fallbacks to deprecated behavior)
- ✅ All tests updated and passing
- ✅ No broken imports or references
- ✅ Mypy passes with no new errors
- ✅ Documentation updated
- ✅ Codebase simplified and maintainability improved

## Estimated Impact

- **Files to modify**: ~25-30 files
  - Source files: ~15 files
  - Test files: ~12-15 files
  - Documentation: ~8-10 files
  - Notebooks: ~2-3 files
- **Breaking changes**: 
  - Config files using `objective.goal` (verify none exist)
  - Code using `execute_final_training` (update to `run_final_training_workflow`)
  - Tests using `mock_trial_run` (update to `mock_hpo_trial_run`)
  - Code expecting schema version 1.0 (should use 2.0)
- **Risk level**: Medium-High (requires careful verification that no production code uses deprecated patterns)

## Migration Guide for Users

### Config Changes

#### Remove `objective.goal` Key
```yaml
# OLD (deprecated)
objective:
  metric: macro-f1
  goal: maximize  # ❌ Deprecated

# NEW (required)
objective:
  metric: macro-f1
  direction: maximize  # ✅ Required
```

#### Remove Schema Version 1.0
```yaml
# OLD (deprecated)
selection:
  prefer_schema_version: "1.0"  # ❌ Deprecated

# NEW (required)
selection:
  prefer_schema_version: "2.0"  # ✅ Required
  # Or use "auto" which prefers 2.0
```

### Code Changes

#### Update Function Imports
```python
# OLD (deprecated)
from training.execution import execute_final_training
from training.hpo.core.search_space import translate_search_space_to_optuna, create_search_space

# NEW (canonical)
from training.execution import run_final_training_workflow
from training.hpo.core.search_space import SearchSpaceTranslator
```

#### Update Test Fixtures
```python
# OLD (deprecated)
def test_something(mock_trial_run):
    run = mock_trial_run

# NEW (canonical)
def test_something(mock_hpo_trial_run):
    run = mock_hpo_trial_run
```

#### Update Path Resolution
```python
# OLD (deprecated)
from infrastructure.paths.resolve import resolve_output_path
path = resolve_output_path(root_dir, config_dir, "hpo")

# NEW (canonical)
from infrastructure.paths.resolve import resolve_storage_path
path = resolve_storage_path(...)  # Use domain-specific resolver
```

#### Update Naming Functions
```python
# OLD (deprecated)
from training.hpo.utils.helpers import create_mlflow_run_name
name = create_mlflow_run_name(...)

# NEW (canonical)
from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
name = build_mlflow_run_name(...)
```

## Notes

- **Verification first**: Always verify no production code/configs use deprecated patterns before removing
- **Incremental approach**: Remove deprecated layers step by step, running tests after each step
- **Git commits**: Consider committing after each major step for easier rollback
- **MLflow compatibility**: The `infrastructure.tracking.mlflow.compatibility` module may still be needed for Azure ML artifact compatibility - verify before removing
- **v1 hash function**: `build_hpo_study_key()` may be kept for migration purposes - verify if it's still needed before removing
- **Gradual removal**: Some deprecated code may need to be kept temporarily if it's still needed for old runs/data. Document these cases with TODOs.

## Known Issues to Address

1. **MLflow compatibility patch**: The `infrastructure.tracking.mlflow.compatibility` module provides a monkey-patch for Azure ML artifacts. This may still be needed - verify before removing.

2. **v1 hash function**: `build_hpo_study_key()` may be kept for migration/backward compat purposes. Verify if it's still needed before removing entirely.

3. **Legacy checkpoint paths**: Some fallback logic may need to be kept if old runs still exist. Document migration path if removal would break old runs.

4. **Legacy test data**: Some tests may use legacy data formats. Update test fixtures to use modern formats.

5. **Documentation references**: Some documentation may reference deprecated patterns in historical context. Update to clarify these are no longer supported.

## Risk Mitigation

- **Verification before removal**: Always verify no production code uses deprecated patterns before removing
- **Incremental removal**: Remove deprecated layers step by step, running tests after each step
- **Git commits**: Commit after each major step for easier rollback
- **Test coverage**: Ensure test coverage doesn't decrease when removing deprecated code tests
- **Documentation**: Update documentation alongside code changes
- **Breaking changes**: Document breaking changes clearly in migration guide

## Related Plans

- `FINISHED-20260118-1131-consolidate-path-config-naming-utilities-comprehensive-master.plan.md` - Already removed some deprecated layers
- `20260118-1155-distribute-orchestration-to-domain-modules-master.plan.md` - Handles orchestration module compatibility layers separately
- Previous consolidation plans may have identified additional deprecated code

## Out of Scope

The following are **NOT** part of this plan:

- **Orchestration module compatibility layers**: Handled in separate plan (`20260118-1155-distribute-orchestration-to-domain-modules-master.plan.md`)
- **Major refactoring**: This plan focuses on removing deprecated code, not major architectural changes

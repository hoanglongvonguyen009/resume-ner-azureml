# Master Plan: Consolidate Test Fixtures and Helpers

## Goal

Remove DRY violations in the test suite by consolidating overlapping responsibilities, duplicated logic, and near-duplicate patterns across test modules. This plan focuses on creating shared, reusable fixtures and helpers that eliminate duplication while maintaining test clarity and maintainability.

## Status

**Last Updated**: 2026-01-20

### Completed Steps
- ✅ Step 1: Consolidate config directory creation fixtures
- ✅ Step 2: Consolidate HPO config fixtures
- ✅ Step 3: Consolidate MLflow mocking patterns
- ✅ Step 4: Consolidate mock MLflow run creation
- ✅ Step 5: Consolidate minimal config creation helpers
- ✅ Step 6: Update all test modules to use consolidated fixtures
- ✅ Step 7: Remove duplicate fixture definitions
- ✅ Step 8: Update test documentation

### Pending Steps
- ⏳ None - all steps completed!


## Preconditions

- All existing tests pass: `uvx pytest tests/ -v`
- Mypy passes: `uvx mypy src --show-error-codes`
- Test fixtures module structure exists: `tests/fixtures/`

## DRY Violations Identified

### Category 1: Config Directory Creation

**Problem**: Multiple test files create `config_dir` fixtures with similar logic for creating temporary config directories with YAML files (paths.yaml, naming.yaml, tags.yaml, mlflow.yaml).

**Locations**:
- `tests/hpo/conftest.py` - `tmp_config_dir` fixture (lines 17-39)
- `tests/config/unit/test_naming_yaml.py` - `config_dir` fixture (lines 19-28)
- `tests/tracking/unit/test_naming_policy_details.py` - `config_dir` fixture (lines 16-25)
- `tests/tracking/unit/test_tags_comprehensive.py` - `config_dir` fixture (lines 21-30)
- `tests/config/integration/test_config_integration.py` - `config_dir` fixture (lines 15-100+)
- `tests/tracking/unit/test_mlflow_config_comprehensive.py` - `config_dir` fixture (lines 18-27)
- `tests/config/unit/test_mlflow_yaml.py` - `config_dir` fixture (lines 20-29)
- `tests/training/hpo/integration/test_hash_consistency.py` - `config_dir` fixture (lines 61-62)
- And potentially more...

**Pattern**: Each creates a `tmp_path / "config"` directory and writes similar YAML files with varying levels of completeness.

### Category 2: HPO Config Fixtures

**Problem**: HPO config fixtures (`hpo_config_smoke`, `hpo_config_minimal`) are duplicated in multiple locations.

**Locations**:
- `tests/fixtures/configs.py` - `hpo_config_smoke` (lines 7-50), `hpo_config_minimal` (lines 54-72)
- `tests/hpo/conftest.py` - `hpo_config_smoke` (lines 108-151), `hpo_config_minimal` (lines 155-173)
- `tests/hpo/integration/conftest.py` - `hpo_config_smoke` (lines 119+), `hpo_config_minimal` (lines 166+)

**Pattern**: Identical or near-identical fixture definitions across multiple conftest files.

### Category 3: MLflow Mocking Patterns

**Problem**: Multiple different patterns for mocking MLflow, with some duplication and inconsistency.

**Locations**:
- `tests/fixtures/mlflow.py` - `mock_mlflow_tracking`, `mock_mlflow_client()`, `mock_mlflow_run()`
- `tests/hpo/conftest.py` - `mock_mlflow_client` fixture (lines 66-91), `mock_mlflow_setup` fixture (lines 95-104)
- `tests/workflows/conftest.py` - `mock_mlflow` fixture (lines 24-28)
- `tests/selection/conftest.py` - `mock_mlflow_run` fixture (lines 111-139), `mock_mlflow_client` fixture (lines 245-248)
- Many test files create inline MLflow mocks

**Pattern**: 
- Some use fixtures from `tests/fixtures/mlflow.py`
- Some create module-specific fixtures that duplicate functionality
- Some create inline mocks in test methods

### Category 4: Mock MLflow Run Creation

**Problem**: Similar patterns for creating mock MLflow runs with tags, metrics, and params across multiple test files.

**Locations**:
- `tests/fixtures/mlflow.py` - `mock_mlflow_run()` helper function (lines 91-118)
- `tests/selection/conftest.py` - `mock_mlflow_run` fixture (lines 111-139), `mock_benchmark_run` (lines 143-162), `mock_trial_run` (lines 166-189), `mock_refit_run` (lines 193-214)
- Many test files create inline mock runs

**Pattern**: Similar structure for creating Mock objects with `run.info`, `run.data.tags`, `run.data.metrics`, `run.data.params`.

### Category 5: Minimal Config Creation Helpers

**Problem**: Helper functions for creating minimal config files are duplicated across test files.

**Locations**:
- `tests/hpo/integration/test_error_handling.py` - `_create_minimal_training_config()` function (lines 30+)
- Similar patterns in other test files

**Pattern**: Functions that create minimal YAML config files for testing.

## Steps

### Step 1: Consolidate Config Directory Creation Fixtures

**Goal**: Create a unified, flexible fixture for creating temporary config directories with required YAML files.

**Actions**:

1. **Create `tests/fixtures/config_dirs.py`**:
   - Add `config_dir` fixture that creates a minimal config directory with all required YAML files
   - Add `config_dir_minimal` fixture for tests that only need basic structure
   - Add `config_dir_full` fixture for tests that need complete config structure
   - Add helper function `create_config_dir_files(config_dir, files_dict)` to programmatically create config files

2. **Update `tests/fixtures/__init__.py`**:
   - Export new config directory fixtures

3. **Update `tests/fixtures/README.md`**:
   - Document new config directory fixtures and usage examples

**Success criteria**:
- `tests/fixtures/config_dirs.py` exists with `config_dir`, `config_dir_minimal`, `config_dir_full` fixtures
- Helper function `create_config_dir_files()` exists and is documented
- `uvx mypy tests/fixtures/config_dirs.py` passes with 0 errors
- All fixtures have type hints and docstrings

**Files to create/modify**:
- `tests/fixtures/config_dirs.py` (new)
- `tests/fixtures/__init__.py` (modify)
- `tests/fixtures/README.md` (modify)

### Step 2: Consolidate HPO Config Fixtures

**Goal**: Remove duplicate HPO config fixtures and ensure all tests use the shared fixtures from `tests/fixtures/configs.py`.

**Actions**:

1. **Verify `tests/fixtures/configs.py` has complete fixtures**:
   - Ensure `hpo_config_smoke` and `hpo_config_minimal` are complete and match all use cases

2. **Update `tests/hpo/conftest.py`**:
   - Remove duplicate `hpo_config_smoke` and `hpo_config_minimal` fixtures
   - Import from `fixtures.configs` instead

3. **Update `tests/hpo/integration/conftest.py`**:
   - Remove duplicate `hpo_config_smoke` and `hpo_config_minimal` fixtures
   - Import from `fixtures.configs` instead

4. **Search for other duplicate HPO config fixtures**:
   - Use grep to find any other files defining `hpo_config_smoke` or `hpo_config_minimal`
   - Update to import from `fixtures.configs`

**Success criteria**:
- No duplicate `hpo_config_smoke` or `hpo_config_minimal` fixtures exist in conftest files
- All HPO tests import from `fixtures.configs`
- `uvx pytest tests/hpo/ -v` passes (all HPO tests still work)
- `uvx mypy tests/hpo/` passes with 0 errors

**Files to modify**:
- `tests/hpo/conftest.py`
- `tests/hpo/integration/conftest.py`
- Any other files with duplicate HPO config fixtures

### Step 3: Consolidate MLflow Mocking Patterns

**Goal**: Standardize MLflow mocking across all tests, ensuring consistent use of shared fixtures.

**Actions**:

1. **Enhance `tests/fixtures/mlflow.py`**:
   - Review existing fixtures: `mock_mlflow_tracking`, `mock_mlflow_client()`, `mock_mlflow_run()`
   - Add `mock_mlflow_client` as a pytest fixture (not just a function)
   - Add `mock_mlflow_setup` fixture that combines tracking URI setup and client creation
   - Ensure all fixtures are well-documented with usage examples

2. **Update `tests/hpo/conftest.py`**:
   - Remove `mock_mlflow_client` fixture (lines 66-91)
   - Remove `mock_mlflow_setup` fixture (lines 95-104)
   - Import from `fixtures.mlflow` instead

3. **Update `tests/workflows/conftest.py`**:
   - Review `mock_mlflow` fixture (lines 24-28) - determine if it's needed or can use shared fixtures
   - If needed, ensure it doesn't duplicate functionality from `fixtures.mlflow`

4. **Update `tests/selection/conftest.py`**:
   - Review `mock_mlflow_client` fixture (lines 245-248)
   - If it's a simple Mock(), consider using shared fixture or documenting why it's different

5. **Search for inline MLflow mocks**:
   - Use grep to find test files that create MLflow mocks inline
   - Document patterns and determine if they should use shared fixtures

**Success criteria**:
- `tests/fixtures/mlflow.py` has comprehensive MLflow mocking fixtures
- No duplicate MLflow mocking fixtures in conftest files (unless justified)
- All tests that can use shared fixtures do so
- `uvx pytest tests/ -v` passes (all tests still work)
- `uvx mypy tests/fixtures/mlflow.py` passes with 0 errors

**Files to modify**:
- `tests/fixtures/mlflow.py`
- `tests/hpo/conftest.py`
- `tests/workflows/conftest.py`
- `tests/selection/conftest.py`
- Any other files with duplicate MLflow mocking

### Step 4: Consolidate Mock MLflow Run Creation

**Goal**: Create reusable fixtures and helpers for creating mock MLflow runs with common patterns.

**Actions**:

1. **Enhance `tests/fixtures/mlflow.py`**:
   - Review existing `mock_mlflow_run()` helper function
   - Add pytest fixtures for common run types:
     - `mock_hpo_trial_run` - HPO trial run with tags and metrics
     - `mock_benchmark_run` - Benchmark run with latency metrics
     - `mock_refit_run` - Refit run with checkpoint tags
     - `mock_final_training_run` - Final training run
   - Add helper function `create_mock_run(run_id, tags, metrics, params)` for custom runs

2. **Update `tests/selection/conftest.py`**:
   - Remove `mock_mlflow_run`, `mock_benchmark_run`, `mock_trial_run`, `mock_refit_run` fixtures
   - Import from `fixtures.mlflow` instead

3. **Search for inline mock run creation**:
   - Use grep to find test files that create mock runs inline
   - Update to use shared fixtures where possible

**Success criteria**:
- `tests/fixtures/mlflow.py` has fixtures for common run types
- No duplicate mock run fixtures in conftest files
- Tests use shared fixtures for common run patterns
- `uvx pytest tests/ -v` passes (all tests still work)
- `uvx mypy tests/fixtures/mlflow.py` passes with 0 errors

**Files to modify**:
- `tests/fixtures/mlflow.py`
- `tests/selection/conftest.py`
- Any other files with duplicate mock run creation

### Step 5: Consolidate Minimal Config Creation Helpers

**Goal**: Create shared helpers for creating minimal config files used across tests.

**Actions**:

1. **Create `tests/fixtures/config_helpers.py`**:
   - Add `create_minimal_training_config(config_dir)` helper function
   - Add `create_minimal_data_config(config_dir)` helper function
   - Add `create_minimal_experiment_config(config_dir)` helper function
   - Add `create_minimal_model_config(config_dir)` helper function
   - Document each helper with examples

2. **Update `tests/hpo/integration/test_error_handling.py`**:
   - Remove `_create_minimal_training_config()` function
   - Import and use shared helper from `fixtures.config_helpers`

3. **Search for other minimal config creation helpers**:
   - Use grep to find similar helper functions
   - Update to use shared helpers

**Success criteria**:
- `tests/fixtures/config_helpers.py` exists with helper functions
- No duplicate minimal config creation helpers in test files
- Tests use shared helpers
- `uvx pytest tests/ -v` passes (all tests still work)
- `uvx mypy tests/fixtures/config_helpers.py` passes with 0 errors

**Files to create/modify**:
- `tests/fixtures/config_helpers.py` (new)
- `tests/fixtures/__init__.py` (modify)
- `tests/fixtures/README.md` (modify)
- `tests/hpo/integration/test_error_handling.py` (modify)
- Any other files with duplicate helpers

### Step 6: Update All Test Modules to Use Consolidated Fixtures

**Goal**: Update all test files to use the consolidated fixtures and helpers.

**Actions**:

1. **Update config directory usage**:
   - Find all test files using local `config_dir` fixtures
   - Update to use `fixtures.config_dirs.config_dir` or appropriate variant
   - Remove local `config_dir` fixture definitions

2. **Update HPO config usage**:
   - Verify all HPO tests use `fixtures.configs.hpo_config_smoke` and `hpo_config_minimal`
   - Fix any imports that reference local fixtures

3. **Update MLflow mocking usage**:
   - Verify all tests use `fixtures.mlflow` fixtures where appropriate
   - Update inline mocks to use shared fixtures where possible

4. **Update mock run usage**:
   - Update tests to use shared mock run fixtures from `fixtures.mlflow`
   - Remove duplicate mock run creation code

5. **Update minimal config helpers usage**:
   - Update tests to use shared helpers from `fixtures.config_helpers`
   - Remove duplicate helper functions

**Success criteria**:
- All test files use consolidated fixtures where applicable
- No duplicate fixture definitions in test files (except module-specific ones that are justified)
- `uvx pytest tests/ -v` passes (all tests still work)
- `uvx mypy tests/` passes with 0 errors

**Files to modify**:
- All test files that currently define duplicate fixtures
- All conftest.py files with duplicate fixtures

### Step 7: Remove Duplicate Fixture Definitions

**Goal**: Clean up all duplicate fixture definitions that have been replaced by shared fixtures.

**Actions**:

1. **Remove duplicate config directory fixtures**:
   - Remove `tmp_config_dir` from `tests/hpo/conftest.py`
   - Remove `config_dir` fixtures from test files (use shared fixture instead)
   - Keep only module-specific variants if they serve a unique purpose

2. **Remove duplicate HPO config fixtures**:
   - Already removed in Step 2, verify no remaining duplicates

3. **Remove duplicate MLflow mocking fixtures**:
   - Already removed in Step 3, verify no remaining duplicates

4. **Remove duplicate mock run fixtures**:
   - Already removed in Step 4, verify no remaining duplicates

5. **Remove duplicate minimal config helpers**:
   - Already removed in Step 5, verify no remaining duplicates

**Success criteria**:
- No duplicate fixture definitions exist (verified by grep)
- All tests still pass: `uvx pytest tests/ -v`
- All imports are correct: `uvx mypy tests/` passes

**Files to modify**:
- All conftest.py files with removed fixtures
- All test files with removed helpers

### Step 8: Update Test Documentation

**Goal**: Update test documentation to reflect consolidated fixtures and helpers.

**Actions**:

1. **Update `tests/fixtures/README.md`**:
   - Document new config directory fixtures
   - Document enhanced MLflow fixtures
   - Document config helper functions
   - Add usage examples for all new fixtures

2. **Update test module READMEs**:
   - Update `tests/hpo/README.md` to reference shared fixtures
   - Update `tests/workflows/README.md` to reference shared fixtures
   - Update `tests/selection/README.md` to reference shared fixtures
   - Update any other test module READMEs that reference removed fixtures

3. **Update `tests/README.md`**:
   - Update fixture documentation section if needed
   - Ensure all examples use consolidated fixtures

**Success criteria**:
- `tests/fixtures/README.md` documents all consolidated fixtures
- All test module READMEs reference shared fixtures correctly
- Documentation examples use consolidated fixtures
- All cross-references are accurate

**Files to modify**:
- `tests/fixtures/README.md`
- `tests/hpo/README.md`
- `tests/workflows/README.md`
- `tests/selection/README.md`
- `tests/README.md`
- Any other test module READMEs

## Success Criteria (Overall)

- ✅ All DRY violations identified in this plan are resolved
- ✅ All tests pass: `uvx pytest tests/ -v`
- ✅ Mypy passes: `uvx mypy tests/ --show-error-codes`
- ✅ No duplicate fixture definitions exist (verified by grep)
- ✅ All test files use consolidated fixtures where applicable
- ✅ Test documentation is updated and accurate
- ✅ Code follows reuse-first principles (shared fixtures used across modules)

## Notes

### Justified Duplications

Some fixture duplications may be justified if they:
- Serve a module-specific purpose that can't be generalized
- Have significantly different behavior that would make a shared fixture too complex
- Are performance-critical and need to be inlined

In these cases, document why the duplication is necessary.

### Migration Strategy

When updating tests to use consolidated fixtures:
1. Update one test module at a time
2. Run tests after each module update to catch issues early
3. Keep old fixtures temporarily if needed for gradual migration
4. Remove old fixtures only after all tests are updated

### Testing Strategy

After each step:
1. Run all tests: `uvx pytest tests/ -v`
2. Run mypy: `uvx mypy tests/ --show-error-codes`
3. Verify no new errors introduced
4. Check that fixture usage is consistent

## Related Plans

- `FINISHED-MASTER-test-documentation.plan.md` - Test documentation was created, now needs updates for consolidated fixtures


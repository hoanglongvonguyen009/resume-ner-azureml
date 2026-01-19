# Refactor API Testing Notebooks - Consolidate Duplication

## Goal

Refactor `notebooks/api_testing.ipynb` and `notebooks/docker_testing.ipynb` to eliminate code duplication, extract reusable utilities to `src/deployment/api/tools/`, and improve maintainability while keeping notebooks focused on orchestration and visualization.

## Status

**Last Updated**: 2026-01-19

### Completed Steps
- ✅ Step 1: Extract shared utilities to src/deployment/api/tools/
- ✅ Step 2: Refactor api_testing.ipynb to use extracted utilities
- ✅ Step 3: Refactor docker_testing.ipynb to use extracted utilities
- ✅ Step 4: Consolidate duplicate helper functions
- ✅ Step 5: Update notebook imports and verify functionality
- ✅ Step 6: Run tests and verify notebooks still work

## Preconditions

- Both notebooks are functional
- Understanding of existing `src/deployment/api/tools/` structure
- Tests exist for API functionality (to verify no regressions)

## Existing Code Analysis

**Note**: After analysis, found:
- `src/testing/` is focused on **HPO pipeline testing**, not API testing utilities
- `tests/integration/api/test_helpers.py` contains `APIClient` class with `_make_request()` method, but it's in `tests/` directory (not `src/`)
- No existing utilities in `src/` for API testing, entity display, or notebook helpers
- Decision: Extract new utilities to `src/deployment/api/tools/` for reuse by notebooks and potentially by tests

## Code Smells Identified

### 1. Duplicated Code (DRY Violation) - HIGH PRIORITY

**Issue**: Same functions duplicated in both notebooks:
- `display_entities()` - Identical implementation in both notebooks
- `make_request()` - Identical implementation in both notebooks
- Path setup code - Similar pattern in both notebooks

**Root Cause**: Notebooks contain reusable logic that should be in `src/` for reuse

**Impact**: 
- Changes need to be made in 2 places
- Risk of divergence between implementations
- Violates reuse-first principle

### 2. Long Helper Functions in Notebooks - MEDIUM PRIORITY

**Issue**: Some helper functions are getting long (30+ lines):
- `start_api_server_interactive()` in api_testing.ipynb
- `start_docker_container()` in docker_testing.ipynb
- Docker helper functions could be better organized

**Root Cause**: Functions doing multiple things (validation, execution, error handling)

**Impact**: Harder to maintain and test

### 3. Primitive Obsession - LOW PRIORITY

**Issue**: Configuration values scattered across notebooks:
- API_BASE_URL, API_TIMEOUT defined in multiple places
- Docker configuration variables could be grouped

**Root Cause**: No configuration object/class

**Impact**: Minor - but could be improved with TypedDict/dataclass

## Steps

### Step 1: Extract shared utilities to src/deployment/api/tools/

1. Create `src/deployment/api/tools/notebook_helpers.py` with:
   - `display_entities()` - Entity visualization function
   - `make_request()` - HTTP request wrapper with latency tracking
   - `setup_notebook_paths()` - Common path setup logic
   - Type hints and docstrings for all functions

2. Create `src/deployment/api/tools/notebook_config.py` with:
   - `NotebookConfig` TypedDict for API configuration
   - Default configuration values
   - Helper to create config from environment

3. Update `src/deployment/api/tools/__init__.py` to export new functions

**Success criteria**:
- `src/deployment/api/tools/notebook_helpers.py` exists with all functions
- `src/deployment/api/tools/notebook_config.py` exists with TypedDict
- `uvx mypy src/deployment/api/tools/notebook_helpers.py` passes with 0 errors
- Functions are typed and documented
- `__init__.py` exports new functions

### Step 2: Refactor api_testing.ipynb to use extracted utilities

1. Update imports to use `from src.deployment.api.tools.notebook_helpers import display_entities, make_request`
2. Update imports to use `from src.deployment.api.tools.notebook_config import NotebookConfig`
3. Remove duplicate `display_entities()` function definition
4. Remove duplicate `make_request()` function definition
5. Replace path setup code with `setup_notebook_paths()` call
6. Update configuration to use `NotebookConfig` TypedDict
7. Keep notebook-specific functions (`find_and_display_models()`, `start_api_server_interactive()`, `verify_server_running()`) in notebook (they're notebook-specific orchestration)

**Success criteria**:
- `api_testing.ipynb` imports from `notebook_helpers`
- No duplicate function definitions in notebook
- All cells execute without errors
- Entity display and API requests work correctly
- Notebook-specific orchestration functions remain

### Step 3: Refactor docker_testing.ipynb to use extracted utilities

1. Update imports to use `from src.deployment.api.tools.notebook_helpers import display_entities, make_request`
2. Update imports to use `from src.deployment.api.tools.notebook_config import NotebookConfig`
3. Remove duplicate `display_entities()` function definition
4. Remove duplicate `make_request()` function definition
5. Replace path setup code with `setup_notebook_paths()` call
6. Update configuration to use `NotebookConfig` TypedDict
7. Keep Docker-specific functions in notebook (they're Docker-specific)

**Success criteria**:
- `docker_testing.ipynb` imports from `notebook_helpers`
- No duplicate function definitions in notebook
- All cells execute without errors
- Entity display and API requests work correctly
- Docker-specific functions remain

### Step 4: Consolidate duplicate helper functions

1. Review `find_and_display_models()` in api_testing.ipynb - consider if it should be in `model_finder.py` or kept notebook-specific
2. Review Docker helper functions in docker_testing.ipynb - extract any truly reusable ones
3. Identify any other duplicated patterns between notebooks
4. Extract common patterns to shared utilities where appropriate

**Success criteria**:
- No duplicated logic between notebooks
- Reusable functions are in `src/`
- Notebook-specific orchestration remains in notebooks
- Functions follow SRP (Single Responsibility Principle)

### Step 5: Update notebook imports and verify functionality

1. Test `api_testing.ipynb`:
   - Run all cells
   - Verify entity display works
   - Verify API requests work
   - Verify server management functions work

2. Test `docker_testing.ipynb`:
   - Run all cells
   - Verify entity display works
   - Verify API requests work
   - Verify Docker operations work

3. Check for any import errors or missing dependencies

**Success criteria**:
- Both notebooks execute all cells without errors
- All functionality works as before
- No import errors
- Entity visualization works correctly
- API requests work correctly

### Step 6: Run tests and verify notebooks still work

1. Run existing API tests: `uvx pytest tests/integration/api/`
2. Run mypy on new code: `uvx mypy src/deployment/api/tools/notebook_helpers.py`
3. Manually verify notebooks in Jupyter environment
4. Check that extracted functions have proper type hints

**Success criteria**:
- All existing tests pass
- Mypy passes with 0 errors on new code
- Notebooks work correctly in Jupyter
- No regressions in functionality

## Success Criteria (Overall)

- ✅ No duplicated code between `api_testing.ipynb` and `docker_testing.ipynb`
- ✅ Shared utilities extracted to `src/deployment/api/tools/notebook_helpers.py`
- ✅ Configuration extracted to `src/deployment/api/tools/notebook_config.py`
- ✅ Both notebooks use extracted utilities via imports
- ✅ Notebooks remain focused on orchestration and visualization
- ✅ All tests pass
- ✅ Mypy passes on new code
- ✅ No functionality regressions
- ✅ Code follows reuse-first principles
- ✅ Functions are properly typed and documented

## Refactoring Techniques Applied

1. **Extract Method** - Move `display_entities()` and `make_request()` to shared module
2. **Extract Class/Module** - Create `notebook_helpers.py` for shared utilities
3. **Replace Data Value with Object** - Use `NotebookConfig` TypedDict for configuration
4. **Move Method** - Move reusable functions from notebooks to `src/`
5. **Eliminate Duplication** - Remove duplicate code between notebooks

## Notes

- Keep notebook-specific orchestration functions in notebooks (they're part of the notebook's purpose)
- Only extract truly reusable utilities to `src/`
- Maintain backward compatibility - notebooks should work the same way from user perspective
- Follow notebook rules: keep notebooks thin, extract reusable logic to `src/`
- Ensure all extracted functions have proper type hints for mypy compliance


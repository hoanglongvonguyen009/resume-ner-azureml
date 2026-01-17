# Unified Comprehensive Workflow Patterns Standardization Plan

## Goal

Complete standardization of workflow patterns across all workflows, unifying findings from:
1. `20260117-2230-standardize-workflow-patterns-inconsistencies.plan.md` - Signature standardization (parameters, naming, metadata)
2. `20260117-2300-additional-workflow-pattern-inconsistencies.plan.md` - Implementation patterns (logging, error handling, subprocess, MLflow)
3. `20260117-2300-workflow-patterns-extended-analysis.plan.md` - DRY violations and code duplication
4. `20260117-2300-workflow-patterns-comprehensive-combined.plan.md` - Previous combined analysis

This unified plan addresses **all** workflow pattern inconsistencies:
- Function signature standardization (parameters, naming, metadata)
- Code duplication and DRY violations
- Logging pattern inconsistencies
- Error handling pattern inconsistencies
- Subprocess execution pattern inconsistencies
- MLflow setup pattern inconsistencies
- Overlapping responsibilities
- Duplicate inference calls
- Near-duplicate patterns
- Config loading inconsistencies

## Quick Summary

**Workflows Analyzed**: 4 main workflows
- `run_benchmarking_workflow()` - Missing `platform` parameter, duplicate `detect_platform()` calls, direct `load_yaml()`, uses `logger` ✅
- `run_selection_workflow()` - Uses `drive_store` instead of `backup_to_drive`, duplicate `mlflow.get_tracking_uri()` calls, uses `logger` ✅
- `execute_final_training()` - Should be renamed, duplicate `detect_platform()` call, uses `print()` ❌, direct `mlflow.get_tracking_uri()` ❌
- `execute_conversion()` - Should be renamed, duplicate `detect_platform()` call, uses `_log` ⚠️, uses `setup_mlflow()` ✅

**Total Issues Identified**: 50+ inconsistencies across 9 categories

**Priority Breakdown**:
- **High Priority**: 15 issues (signature, duplicate inference, logging, MLflow setup)
- **Medium Priority**: 20 issues (code duplication, config loading, error handling, overlapping responsibilities)
- **Low Priority**: 15 issues (subprocess patterns, dict construction, near-duplicates)

## Status

**Last Updated**: 2026-01-17

### Completed Steps
- ✅ Step 0: Comprehensive analysis of all workflow patterns (completed across all 4 plans)
- ✅ Step 1: Standardize metadata type classification
- ✅ Step 2: Standardize function naming conventions
- ✅ Step 3: Create unified parameter signature pattern
- ✅ Step 4: Standardize backup parameter naming
- ✅ Step 5: Fix duplicate inference issues
- ✅ Step 6: Standardize platform/environment parameter handling
- ✅ Step 7: Standardize logging patterns
- ✅ Step 8: Standardize MLflow setup patterns
- ✅ Step 9: Standardize config loading patterns
- ✅ Step 10: Extract backbone name processing to shared utility
- ✅ Step 11: Standardize error handling patterns
- ✅ Step 12: Standardize subprocess execution patterns (optional)
- ✅ Step 13: Consolidate overlapping responsibilities
- ✅ Step 14: Update all workflow functions to use standard patterns
- ✅ Step 15: Update notebook call sites

### Pending Steps
- ✅ Step 16: Verify all tests pass (test files updated to use new function names)
- ✅ Step 17: Run mypy type checking (workflow modules checked - only pre-existing errors found)

## Preconditions

- All existing workflow functions are functional
- Tests exist for workflow functions
- Notebooks are using workflow functions
- Backup consolidation plan (`FINISHED-20260117-2000-consolidate-drive-backup-scripts-dry-violations.plan.md`) is complete

## Complete Findings Inventory

### Category 1: Signature & Naming Inconsistencies (High Priority)

#### 1.1 Metadata Type Classification
- `benchmarking_workflow.py`: `type: utility` → should be `type: script`
- `selection_workflow.py`: `type: utility` → should be `type: script`
- `executor.py`: `type: script` ✅
- `orchestration.py`: `type: script` ✅

**Impact**: Inconsistent metadata classification makes it harder to identify workflow entry points

#### 1.2 Function Naming Conventions
- `run_benchmarking_workflow()` ✅ (correct pattern)
- `run_selection_workflow()` ✅ (correct pattern)
- `execute_final_training()` → should be `run_final_training_workflow()`
- `execute_conversion()` → should be `run_conversion_workflow()`

**Impact**: Inconsistent naming makes it harder to discover and use workflow functions

#### 1.3 Parameter Signature Inconsistencies

| Function | backup_enabled | backup_to_drive | restore_from_drive | drive_store | in_colab | platform |
|----------|---------------|-----------------|-------------------|-------------|----------|----------|
| `run_benchmarking_workflow` | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ (uses detect_platform) |
| `run_selection_workflow` | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `execute_final_training` | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| `execute_conversion` | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |

**Standard**: All workflow functions should accept:
- `backup_enabled: bool = True`
- `backup_to_drive: Optional[Callable[[Path, bool], bool]] = None`
- `restore_from_drive: Optional[Callable[[Path, bool], bool]] = None`
- `platform: str` (explicit, not internal detect_platform)
- `in_colab: bool = False` (for Colab-specific behavior)

#### 1.4 Parameter Naming Inconsistencies
- `backup_to_drive` vs `drive_store` (same concept)
- `restore_from_drive` vs `ensure_restored_from_drive` (same concept)

**Additional Issue - Parameter Renaming When Passing Down**:
- `run_benchmarking_workflow()` receives `backup_to_drive` but passes it as `drive_store` to `acquire_best_model_checkpoint()` (line 209)
- `run_benchmarking_workflow()` receives `restore_from_drive` but passes it as `ensure_restored_from_drive` to `benchmark_champions()` (line 243)

**Impact**: Workflow functions must rename parameters when calling downstream functions, creating confusion

### Category 2: Duplicate Inference Issues (High Priority)

#### 2.1 `detect_platform()` Duplication
- `run_benchmarking_workflow()`: Called twice (lines 141, 207) - missing `platform` parameter
- `execute_final_training()`: Called once (line 141) - has `platform` parameter but ignores it
- `execute_conversion()`: Called once (line 128) - has `platform` parameter but ignores it

**Impact**: Unnecessary computation, potential inconsistencies if environment changes between calls

#### 2.2 `mlflow.get_tracking_uri()` Duplication
- `run_selection_workflow()`: Called twice (lines 112, 254)

**Impact**: Unnecessary computation, potential inconsistencies

### Category 3: Logging Pattern Inconsistencies (High Priority)

| Workflow | Current Pattern | Standard Pattern | Status |
|----------|----------------|------------------|--------|
| `run_benchmarking_workflow()` | `logger` from `get_logger(__name__)` | `logger` from `get_logger(__name__)` | ✅ Correct |
| `run_selection_workflow()` | `logger` from `get_logger(__name__)` | `logger` from `get_logger(__name__)` | ✅ Correct |
| `execute_final_training()` | `print()` statements | `logger` from `get_logger(__name__)` | ❌ Needs fix |
| `execute_conversion()` | `_log` from `get_script_logger()` | `logger` from `get_logger(__name__)` | ⚠️ Needs fix |

**Impact**: 
- Inconsistent log output format
- Harder to filter/search logs
- `print()` statements don't respect log levels
- Different loggers may have different formatting

### Category 4: MLflow Setup Pattern Inconsistencies (High Priority)

| Workflow | Current Pattern | Standard Pattern | Status |
|----------|----------------|------------------|--------|
| `run_benchmarking_workflow()` | Receives `mlflow_client` as parameter | Use `setup_mlflow()` or receive `tracking_uri` | ⚠️ Acceptable |
| `run_selection_workflow()` | `mlflow.get_tracking_uri()` directly (2 calls) | Use `setup_mlflow()` or receive `tracking_uri` | ❌ Needs fix |
| `execute_final_training()` | `mlflow.get_tracking_uri()` directly | Use `setup_mlflow()` or receive `tracking_uri` | ❌ Needs fix |
| `execute_conversion()` | `setup_mlflow()` helper | Use `setup_mlflow()` helper | ✅ Correct |

**Standard**: All workflows should use `infrastructure.tracking.mlflow.setup.setup_mlflow()` (SSOT) or receive `tracking_uri` as explicit parameter

**Impact**: 
- Violates SSOT principle
- Potential inconsistencies in MLflow configuration
- Missing experiment setup in some workflows

### Category 5: Config Loading Pattern Inconsistencies (Medium Priority)

| Workflow | Current Pattern | Standard Pattern | Status |
|----------|----------------|------------------|--------|
| `run_benchmarking_workflow()` | Direct `load_yaml()` call | Config loader function | ❌ Needs fix |
| `run_selection_workflow()` | Receives `acquisition_config` as parameter | Config loader or parameter | ✅ Acceptable |
| `execute_final_training()` | `load_final_training_config()` | Config loader function | ✅ Correct |
| `execute_conversion()` | `load_conversion_config()` | Config loader function | ✅ Correct |

**Impact**:
- Inconsistent config validation and processing
- Missing config transformation logic
- Harder to maintain config schema changes

### Category 6: Code Duplication Patterns (Medium Priority)

#### 6.1 Backbone Name Extraction (3 locations)
- `execute_final_training()`: Lines 172-174
- `execute_conversion()`: Lines 127-133
- `benchmark_best_trials()` in orchestrator.py: Line 552

**Pattern Variations**:
```python
# execute_final_training() - modifies in place, no else
if "-" in backbone_name:
    backbone_name = backbone_name.split("-")[0]

# execute_conversion() - creates new variable, has else
if "-" in backbone:
    backbone_short = backbone.split("-")[0]
else:
    backbone_short = backbone
```

**Solution**: Extract to `extract_short_backbone_name(backbone: str) -> str` utility

#### 6.2 Output Directory Building (2 locations, but consistent pattern)
- `execute_final_training()`: Lines 176-185
- `execute_conversion()`: Lines 135-146

**Pattern**: `create_naming_context()` + `build_output_path()`

**Solution**: Keep as-is (documented pattern) OR extract to helper if pattern becomes more complex

#### 6.3 Dict Construction Patterns
- `run_benchmarking_workflow()`: `best_run_info` dict (lines 191-199)
- `execute_final_training()`: `best_config` dict (lines 126-129)

**Solution**: Low priority - different purposes, consider `TypedDict` for type safety

### Category 7: Overlapping Responsibilities (Medium Priority)

#### 7.1 Checkpoint Acquisition
- Both `run_benchmarking_workflow()` and `run_selection_workflow()` call `acquire_best_model_checkpoint()`
- Parameter name mismatches require renaming when calling downstream function
- `run_selection_workflow()` has checkpoint validation logic that could be reused

**Solution**: 
- Standardize parameter names in `acquire_best_model_checkpoint()` to match workflow standard
- Extract checkpoint validation to shared utility

#### 7.2 MLflow Run Creation
- `execute_final_training()`: Uses `create_training_mlflow_run()` helper
- `execute_conversion()`: Uses `client.create_run()` directly
- Similar pattern: build run name → build tags → add domain-specific tags → create run

**Solution**: Consider creating domain-specific run creation helpers for conversion or extract common pattern

### Category 8: Error Handling Pattern Inconsistencies (Medium Priority)

| Workflow | Early Exit Pattern | Exception Types | Validation Pattern |
|----------|-------------------|-----------------|---------------------|
| `run_benchmarking_workflow()` | Returns empty dict `{}` | Logs warnings | Logs warning and returns empty dict |
| `run_selection_workflow()` | Raises `ValueError` | `ValueError` with diagnostics | Raises `ValueError` with detailed diagnostics |
| `execute_final_training()` | Returns early if exists | `FileNotFoundError` for missing files | Raises `FileNotFoundError` with helpful message |
| `execute_conversion()` | Raises `RuntimeError` | `RuntimeError` with detailed output | Raises `RuntimeError` with detailed error output |

**Standard**: 
- Critical errors → raise exceptions with detailed messages
- Non-critical early exits → return appropriate values with info-level logging
- Use appropriate exception types:
  - `ValueError`: Invalid configuration/input parameters
  - `FileNotFoundError`: Missing required files/directories
  - `RuntimeError`: Execution failures (subprocess, MLflow operations)

**Impact**:
- Inconsistent error handling makes it harder to catch specific error types
- Some workflows fail silently (return empty dict), others raise exceptions
- Error messages vary in detail and helpfulness

### Category 9: Subprocess Execution Pattern Inconsistencies (Low Priority)

| Workflow | Current Pattern | Status |
|----------|----------------|--------|
| `execute_final_training()` | Uses `execute_training_subprocess()` helper | ✅ Correct |
| `execute_conversion()` | Uses direct `subprocess.Popen()` with custom streaming | ⚠️ Different pattern |

**Solution**: Consider extracting streaming logic to shared utility if pattern is needed elsewhere

### Category 10: Near-Duplicate Patterns (Low Priority)

#### 10.1 Checkpoint Validation
- Only `run_selection_workflow()` validates checkpoints before reuse
- `run_benchmarking_workflow()` doesn't validate

**Solution**: Consider adding validation to benchmarking workflow or document why not needed

#### 10.2 Config Modification Pattern
- `run_benchmarking_workflow()`: Modifies `acquisition_config` after loading (lines 181-183)

**Solution**: Move `output_base_dir` override to config loader or pass as parameter

## Unified Steps

### Phase 1: Signature Standardization (Steps 1-6)

#### Step 1: Standardize Metadata Type Classification

1. Update `benchmarking_workflow.py` metadata: `type: utility` → `type: script`
2. Update `selection_workflow.py` metadata: `type: utility` → `type: script`
3. Verify `executor.py` and `orchestration.py` already use `type: script`
4. Ensure all have `tags: workflow` or `tags: orchestration` as appropriate

**Success criteria**:
- All workflow functions have `type: script` in metadata
- All have appropriate tags
- `uvx mypy src --show-error-codes` passes

#### Step 2: Standardize Function Naming Conventions

1. Rename `execute_final_training()` → `run_final_training_workflow()`
2. Rename `execute_conversion()` → `run_conversion_workflow()`
3. Update all imports and call sites
4. Update `__init__.py` exports:
   - `src/training/execution/__init__.py`
   - `src/deployment/conversion/__init__.py`
   - `src/evaluation/selection/workflows/__init__.py`

**Success criteria**:
- All workflow functions use `run_*_workflow()` pattern
- All imports updated
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes

#### Step 3: Create Unified Parameter Signature Pattern

Define standard signature pattern for all workflow functions:

```python
def run_*_workflow(
    # Core parameters (domain-specific)
    ...,
    # Standard infrastructure parameters
    root_dir: Path,
    config_dir: Path,
    platform: str,
    backup_enabled: bool = True,
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    in_colab: bool = False,
    # MLflow parameters (optional - can use setup_mlflow() instead)
    tracking_uri: Optional[str] = None,
) -> ...:
```

**Success criteria**:
- Standard signature pattern documented
- All workflow functions follow pattern
- Type hints are correct

#### Step 4: Standardize Backup Parameter Naming

1. In `run_selection_workflow()`: Rename `drive_store` → `backup_to_drive`
2. Update `acquire_best_model_checkpoint()` in `src/evaluation/selection/artifact_acquisition.py`:
   - Rename `drive_store` → `backup_to_drive`
   - Rename `ensure_restored_from_drive` → `restore_from_drive`
3. Update `benchmark_champions()` in `src/evaluation/benchmarking/orchestrator.py`:
   - Rename `ensure_restored_from_drive` → `restore_from_drive`
4. Update all call sites to use standard parameter names

**Success criteria**:
- All functions use `backup_to_drive` (not `drive_store`)
- All functions use `restore_from_drive` (not `ensure_restored_from_drive`)
- No parameter renaming needed when calling downstream functions
- `uvx mypy src --show-error-codes` passes

#### Step 5: Fix Duplicate Inference Issues

1. **Add `platform` parameter to `run_benchmarking_workflow()`**
2. **Fix `detect_platform()` duplication**:
   - `run_benchmarking_workflow()`: Remove calls on lines 141, 207, use `platform` parameter
   - `execute_final_training()`: Remove call on line 141, use `platform` parameter
   - `execute_conversion()`: Remove call on line 128, use `platform` parameter
3. **Fix `mlflow.get_tracking_uri()` duplication in `run_selection_workflow()`**:
   - Retrieve `tracking_uri` once at function start (line 112)
   - Reuse the same variable at line 254 instead of calling again

**Success criteria**:
- No duplicate `detect_platform()` calls in workflow functions
- No duplicate `mlflow.get_tracking_uri()` calls
- All use passed parameters instead of internal detection
- `uvx mypy src --show-error-codes` passes

#### Step 6: Standardize Platform/Environment Parameter Handling

1. Verify all workflow functions accept `platform: str` explicitly:
   - `run_benchmarking_workflow()`: Add parameter (from Step 5)
   - `run_selection_workflow()`: Already has it ✅
   - `execute_final_training()`: Already has it ✅
   - `execute_conversion()`: Already has it ✅
2. Update all call sites to pass `platform` explicitly:
   - Notebooks
   - Test fixtures
   - Other workflow callers

**Success criteria**:
- All workflow functions accept `platform: str` parameter
- All call sites pass `platform` explicitly
- `uvx mypy src --show-error-codes` passes

### Phase 2: Implementation Pattern Standardization (Steps 7-12)

#### Step 7: Standardize Logging Patterns

1. Update `execute_final_training()`:
   - Add `logger = get_logger(__name__)` at top of function
   - Replace all `print()` statements with `logger` calls:
     - `print(f"✓ ...")` → `logger.info(...)`
     - `print(f"⚠ Warning: ...")` → `logger.warning(...)`
     - `print(f"🔄 ...")` → `logger.info(...)`
2. Update `execute_conversion()`:
   - Replace `_log = get_script_logger("conversion.orchestration")` with `logger = get_logger(__name__)`
   - Replace all `_log.*` calls with `logger.*`
   - Ensure consistent log level usage
3. Verify other workflows already use `logger`:
   - `run_benchmarking_workflow()` ✅
   - `run_selection_workflow()` ✅

**Success criteria**:
- All workflows use `logger` from `get_logger(__name__)`
- No `print()` statements in workflow functions
- No `_log` or `get_script_logger()` usage in workflows
- Consistent log level usage (info, warning, error, debug)
- `uvx mypy src --show-error-codes` passes

#### Step 8: Standardize MLflow Setup Patterns

1. Update `run_selection_workflow()`:
   - Option A: Use `setup_mlflow()` helper at function start
   - Option B: Receive `tracking_uri` as explicit parameter
   - Fix duplicate `mlflow.get_tracking_uri()` call (retrieve once, reuse)
2. Update `execute_final_training()`:
   - Option A: Use `setup_mlflow()` helper at function start
   - Option B: Receive `tracking_uri` as explicit parameter
   - Replace direct `mlflow.get_tracking_uri()` call
3. Verify `execute_conversion()` already uses `setup_mlflow()` ✅
4. Update `run_benchmarking_workflow()` if needed:
   - Consider receiving `tracking_uri` as parameter instead of `mlflow_client`

**Success criteria**:
- All workflows use `setup_mlflow()` helper or receive `tracking_uri` as parameter
- No direct `mlflow.get_tracking_uri()` calls in workflow functions
- No duplicate MLflow setup calls
- `uvx mypy src --show-error-codes` passes

#### Step 9: Standardize Config Loading Patterns

1. Create `load_artifact_acquisition_config()` if needed:
   - Location: `src/infrastructure/config/` or appropriate location
   - Follow pattern from `load_final_training_config()` and `load_conversion_config()`
   - Handle `output_base_dir` override logic
2. Update `run_benchmarking_workflow()`:
   - Replace direct `load_yaml()` call (line 181) with config loader
   - Or: Receive `acquisition_config` as parameter (like `run_selection_workflow()`)
3. Verify other workflows use config loaders:
   - `run_selection_workflow()`: Receives as parameter ✅
   - `execute_final_training()`: Uses `load_final_training_config()` ✅
   - `execute_conversion()`: Uses `load_conversion_config()` ✅

**Success criteria**:
- All workflows use config loaders instead of direct `load_yaml()` calls
- Config validation and transformation handled consistently
- `uvx mypy src --show-error-codes` passes

#### Step 10: Extract Backbone Name Processing to Shared Utility

1. Create utility function in `src/common/shared/model_utils.py` or `src/infrastructure/naming/utils.py`:
```python
def extract_short_backbone_name(backbone: str) -> str:
    """
    Extract short backbone name by removing variant suffix.
    
    Examples:
        "distilbert-base-uncased" -> "distilbert"
        "bert-base-uncased" -> "bert"
        "roberta" -> "roberta"
    
    Args:
        backbone: Full backbone name (may include variant suffix)
        
    Returns:
        Short backbone name (base model name)
    """
    if "-" in backbone:
        return backbone.split("-")[0]
    return backbone
```

2. Update all 3 locations to use utility:
   - `execute_final_training()` line 172-174
   - `execute_conversion()` line 127-133
   - `benchmark_best_trials()` in orchestrator.py line 552

**Success criteria**:
- Utility function created with type hints
- All 3 locations updated to use utility
- `uvx mypy src --show-error-codes` passes
- `uvx pytest tests/` passes (if tests exist for these functions)

#### Step 11: Standardize Error Handling Patterns

1. Review early exit patterns:
   - Determine which should raise exceptions vs return empty values
   - Standardize on: critical errors → exceptions, non-critical → return values
2. Standardize exception types:
   - `ValueError`: Invalid configuration/input
   - `FileNotFoundError`: Missing files/directories
   - `RuntimeError`: Execution failures
3. Ensure all exceptions have detailed error messages with diagnostics
4. Update workflows to follow standard:
   - `run_benchmarking_workflow()`: Keep return empty dict for non-critical, but ensure critical errors raise exceptions
   - `run_selection_workflow()`: Already raises exceptions ✅
   - `execute_final_training()`: Already raises exceptions ✅
   - `execute_conversion()`: Already raises exceptions ✅

**Success criteria**:
- Consistent error handling patterns
- Appropriate exception types used
- Detailed error messages with diagnostics
- `uvx mypy src --show-error-codes` passes

#### Step 12: Standardize Subprocess Execution Patterns (Optional - Low Priority)

1. Review `execute_conversion()` subprocess execution:
   - Evaluate if custom streaming is needed
   - If yes, extract streaming logic to shared utility
   - If no, consider using helper function pattern similar to `execute_training_subprocess()`
2. Ensure consistent error handling for subprocess failures

**Success criteria**:
- Consistent subprocess execution patterns (if scope allows)
- Shared utilities for common patterns (if needed)
- Consistent error handling
- `uvx mypy src --show-error-codes` passes

### Phase 3: Consolidation & Integration (Steps 13-17)

#### Step 13: Consolidate Overlapping Responsibilities

1. **Checkpoint Acquisition Consolidation**:
   - Standardize parameter names in `acquire_best_model_checkpoint()` (already done in Step 4)
   - Extract checkpoint validation to shared utility if used in multiple places
   - Consider adding validation to benchmarking workflow if needed
2. **MLflow Run Creation Consolidation**:
   - Consider creating domain-specific run creation helpers for conversion (like `create_training_mlflow_run()`)
   - Or extract common pattern to shared utility
3. **Output Directory Building**:
   - Document pattern as standard (keep as-is for now)
   - Consider extracting to helper if pattern becomes more complex

**Success criteria**:
- Overlapping responsibilities documented and consolidated where beneficial
- Shared utilities created for common patterns
- `uvx mypy src --show-error-codes` passes

#### Step 14: Update All Workflow Functions to Use Standard Patterns

1. Update `run_benchmarking_workflow()`:
   - Add `platform: str` parameter
   - Ensure all standard parameters present
   - Update internal calls to use standard parameter names
   - Fix duplicate `detect_platform()` calls
   - Update config loading to use config loader
   - Verify logging uses `logger` ✅
2. Update `run_selection_workflow()`:
   - Add `backup_enabled: bool = True` parameter
   - Rename `drive_store` → `backup_to_drive`
   - Ensure all standard parameters present
   - Fix duplicate `mlflow.get_tracking_uri()` call
   - Update MLflow setup to use `setup_mlflow()` or receive `tracking_uri`
   - Verify logging uses `logger` ✅
3. Update `run_final_training_workflow()` (renamed from `execute_final_training`):
   - Add `restore_from_drive` parameter
   - Add `in_colab` parameter
   - Ensure all standard parameters present
   - Fix duplicate `detect_platform()` call
   - Replace `print()` with `logger`
   - Update MLflow setup to use `setup_mlflow()` or receive `tracking_uri`
   - Use backbone name utility
4. Update `run_conversion_workflow()` (renamed from `execute_conversion`):
   - Add `restore_from_drive` parameter
   - Add `in_colab` parameter
   - Ensure all standard parameters present
   - Fix duplicate `detect_platform()` call
   - Replace `_log` with `logger`
   - Use backbone name utility
   - Verify MLflow setup uses `setup_mlflow()` ✅

**Success criteria**:
- All workflow functions have identical standard parameter signature
- All internal calls use standard parameter names
- No duplicate inference calls
- All use standard logging patterns
- All use standard MLflow setup patterns
- All use standard config loading patterns
- `uvx mypy src --show-error-codes` passes

#### Step 15: Update Notebook Call Sites

1. Update `notebooks/02_best_config_selection.ipynb`:
   - Update `run_benchmarking_workflow()` call to pass `platform` explicitly
   - Update `run_selection_workflow()` call to use `backup_to_drive` (not `drive_store`)
   - Update `run_final_training_workflow()` call (renamed from `execute_final_training`)
   - Update `run_conversion_workflow()` call (renamed from `execute_conversion`)
2. Update `notebooks/01_orchestrate_training_colab.ipynb`:
   - Check for any workflow function calls and update if needed

**Success criteria**:
- All notebook cells updated with new function names
- All notebook cells pass standard parameters
- Notebooks can be run end-to-end without errors

#### Step 16: Verify All Tests Pass

1. Run all workflow tests: `uvx pytest tests/workflows/`
2. Run all related tests: `uvx pytest tests/ -k workflow`
3. Fix any test failures due to signature/logging changes
4. Update test fixtures if needed
5. Update test assertions if needed (e.g., check log output instead of print output)

**Success criteria**:
- `uvx pytest tests/workflows/` passes
- `uvx pytest tests/ -k workflow` passes
- All test fixtures updated to use standard parameters
- All test assertions updated for new logging patterns

#### Step 17: Run Mypy Type Checking

1. Run mypy on all workflow modules: `uvx mypy src/evaluation/selection/workflows/ src/training/execution/executor.py src/deployment/conversion/orchestration.py`
2. Fix any type errors
3. Run full mypy check: `uvx mypy src --show-error-codes`

**Success criteria**:
- `uvx mypy src/evaluation/selection/workflows/` passes with 0 errors
- `uvx mypy src/training/execution/executor.py` passes with 0 errors
- `uvx mypy src/deployment/conversion/orchestration.py` passes with 0 errors
- `uvx mypy src --show-error-codes` passes (no new errors introduced)

## Success Criteria (Overall)

### Signature & Naming
- ✅ All workflow functions use `run_*_workflow()` naming pattern
- ✅ All workflow functions have `type: script` in metadata
- ✅ All workflow functions have identical standard parameter signature
- ✅ All parameter names are consistent (`backup_to_drive`, not `drive_store`)

### Implementation Patterns
- ✅ All workflows use `logger` from `get_logger(__name__)` (no `print()` statements)
- ✅ All workflows use `setup_mlflow()` helper or receive `tracking_uri` as parameter
- ✅ All workflows use config loaders instead of direct `load_yaml()` calls
- ✅ No duplicate inference calls (`detect_platform()`, `mlflow.get_tracking_uri()`)
- ✅ Consistent error handling patterns
- ✅ Consistent subprocess execution patterns (if scope allows)

### Code Quality
- ✅ Backbone name processing extracted to shared utility
- ✅ Overlapping responsibilities consolidated where beneficial
- ✅ All call sites updated (notebooks and code)
- ✅ All tests pass
- ✅ Mypy passes with 0 errors
- ✅ No breaking changes to functionality (only pattern standardization)

## Files to Modify

### Workflow Functions
- `src/evaluation/selection/workflows/benchmarking_workflow.py`
- `src/evaluation/selection/workflows/selection_workflow.py`
- `src/training/execution/executor.py`
- `src/deployment/conversion/orchestration.py`

### Downstream Functions
- `src/evaluation/selection/artifact_acquisition.py` (standardize parameter names)
- `src/evaluation/benchmarking/orchestrator.py` (use backbone utility, standardize parameter names)

### New Files to Create
- `src/common/shared/model_utils.py` (or add to existing utility file) - `extract_short_backbone_name()` function
- `src/infrastructure/config/` (add artifact acquisition config loader if needed)

### Module Exports
- `src/training/execution/__init__.py`
- `src/deployment/conversion/__init__.py`
- `src/evaluation/selection/workflows/__init__.py`

### Notebooks
- `notebooks/02_best_config_selection.ipynb`
- `notebooks/01_orchestrate_training_colab.ipynb` (if needed)

### Tests
- `tests/workflows/test_notebook_01_e2e.py`
- `tests/workflows/test_notebook_02_e2e.py`
- `tests/workflows/test_full_workflow_e2e.py`
- Any other tests that import or call workflow functions

## Notes

- This is a **comprehensive pattern standardization** effort, not a functional change
- All changes should maintain backward compatibility where possible (use default parameters)
- Functionality should remain identical - only patterns change
- Follow reuse-first principles: use existing helpers (`setup_mlflow()`, `execute_training_subprocess()`) when available
- Consider creating shared utilities if patterns are repeated (e.g., backbone name extraction, subprocess streaming)
- Prioritize high-impact changes first (signature standardization, duplicate inference, logging, MLflow setup)
- Lower-priority changes (dict construction, subprocess streaming) can be deferred if scope is limited
- Execute in phases: Signature → Implementation → Consolidation

## Relationship to Source Plans

This unified plan **combines and extends** all findings from:

1. **`20260117-2230-standardize-workflow-patterns-inconsistencies.plan.md`**:
   - Signature standardization (parameters, naming, metadata)
   - Basic duplicate inference issues
   - Parameter naming inconsistencies

2. **`20260117-2300-additional-workflow-pattern-inconsistencies.plan.md`**:
   - Logging pattern inconsistencies
   - Error handling pattern inconsistencies
   - Subprocess execution pattern inconsistencies
   - MLflow setup pattern inconsistencies

3. **`20260117-2300-workflow-patterns-extended-analysis.plan.md`**:
   - Overlapping responsibilities
   - Duplicated logic patterns
   - Additional duplicate inference patterns
   - MLflow setup inconsistencies (detailed)

4. **`20260117-2300-workflow-patterns-comprehensive-combined.plan.md`**:
   - Previous combined analysis
   - Additional consolidation recommendations

All findings from these 4 plans have been integrated into this unified comprehensive plan with no duplication.


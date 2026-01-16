# Code Quality Verification Plan: src/ Module Compliance

## Goal

Systematically verify and fix all Python modules in `src/` against three rule sets:
1. **File Metadata** (`@python-file-metadata.mdc`) - Required metadata blocks for files with behavioral weight
2. **Code Quality** (`@python-code-quality.mdc`) - Naming, structure, error handling, comments
3. **Type Safety** (`@python-type-safety.mdc`) - Type hints, Mypy compliance, precise types

Each verification step includes immediate remediation of identified issues.

## Status

**Last Updated**: 2025-01-27

### Completed Steps
- ✅ Step 1: Inventory and categorize all modules
- ✅ Step 2: Verify and fix `src/api/` module (empty directory, skipped)
- ✅ Step 3: Verify and fix `src/benchmarking/` module (added metadata to cli.py)
- ✅ Step 4: Verify and fix `src/common/` module (added metadata to json_cache.py, yaml_utils.py, performance.py)
- ✅ Step 5: Verify and fix `src/conversion/` module (empty directory, skipped)

### Completed Steps
- ✅ Step 1: Inventory and categorize all modules
- ✅ Step 2: Verify and fix `src/api/` module (empty directory, skipped)
- ✅ Step 3: Verify and fix `src/benchmarking/` module (added metadata to cli.py)
- ✅ Step 4: Verify and fix `src/common/` module (added metadata to json_cache.py, yaml_utils.py, performance.py)
- ✅ Step 5: Verify and fix `src/conversion/` module (empty directory, skipped)
- ✅ Step 6: Verify and fix `src/core/` module (all files have metadata, no issues)
- ✅ Step 7: Verify and fix `src/data/` module (added metadata to dataset_loader.py, data_combiner.py)
- ✅ Step 8: Verify and fix `src/deployment/` module (all required files have metadata, no issues)
- ✅ Step 9: Verify and fix `src/evaluation/` module (added metadata to experiment_discovery.py, workflows/utils.py)
- ✅ Step 10: Verify and fix `src/infrastructure/` module (60/76 files have metadata, no issues)
- ✅ Step 11: Verify and fix `src/orchestration/` module (added metadata to 7 files: runtime.py, optuna/integration.py, study/manager.py, file_locking.py, version_counter.py, azureml/sweeps.py, trial/callback.py)
- ✅ Step 12: Verify and fix `src/selection/` module (2/4 files have metadata, types.py is just type definitions, no issues)
- ✅ Step 13: Verify and fix `src/testing/` module (12/22 files have metadata, mostly __init__.py files missing, no issues)
- ✅ Step 14: Verify and fix `src/training/` module (added metadata to 8 files: logging.py, config.py, data_combiner.py, hpo/trial/metrics.py, hpo/trial/meta.py, hpo/trial/callback.py, hpo/utils/helpers.py, hpo/utils/paths.py)
- ✅ Step 15: Generate overall compliance report (report created at `docs/compliance-report.md`)

### Pending Steps

NONE

## Preconditions

- Access to `src/` directory
- Ability to run `uvx mypy` for type checking
- Understanding of module structure and responsibilities

## Check Order

Follow this module-by-module approach:

1. **Inventory Phase** - Understand what we're checking
2. **Module-by-Module Verification & Fix** - For each module:
   - Verify file metadata compliance (fastest, surface-level) → Fix issues
   - Verify code quality compliance (naming, structure, patterns) → Fix issues
   - Verify type safety compliance (type hints, Mypy) → Fix issues
   - Run tests and Mypy to confirm fixes
3. **Report** - Generate final compliance report

## Verification Steps

### Step 1: Inventory and Categorize All Modules

**Purpose**: Understand the scope and categorize files by type (script, utility, test, etc.)

**Actions**:
1. List all Python files in `src/` recursively
2. Categorize each file:
   - **Entry-point scripts**: Files with `if __name__ == "__main__"` or CLI entry points
   - **Workflow files**: Files in `**/workflows/` directories
   - **Test modules**: Files in `tests/` (if any in src)
   - **Shared utilities**: Files in `common/` or files with "utils" in name
   - **Core logic**: Business logic, training, evaluation modules
   - **Infrastructure**: Setup, tracking, config modules
   - **Small pure helpers**: Simple functions with no side effects

**Detection Criteria**:
```bash
# Find all Python files
find src/ -name "*.py" -type f | sort

# Find entry points
grep -r "if __name__ == \"__main__\"" src/ --include="*.py" -l

# Find workflow files
find src/ -path "*/workflows/*.py" -type f

# Find utility files
find src/ -name "*utils*.py" -o -name "*helper*.py" | grep -v __pycache__

# Find CLI files
find src/ -name "cli.py" -o -name "*_cli.py"
```

**Success Criteria**:
- Complete inventory of all Python files in `src/`
- Each file categorized by type
- Inventory saved to `docs/compliance-inventory.md` (or similar)

---

## Module Verification Template

Each module verification step (Steps 2-14) follows this pattern:

### For Module `src/[module_name]/`

**Purpose**: Verify compliance for all Python files in `src/[module_name]/` across all three rule sets.

**Actions**:

1. **2.1 File Metadata Compliance** (for `src/[module_name]/`)
   - Check all files that require metadata (entry-points, workflows, utilities with side effects)
   - Verify metadata presence, completeness, and format
   - Document exceptions (small pure helpers)

2. **2.2 Code Quality Compliance** (for `src/[module_name]/`)
   - Check naming conventions (snake_case, PascalCase, SCREAMING_SNAKE_CASE)
   - Check function structure (length, parameters, nesting)
   - Check for magic numbers
   - Check error handling patterns
   - Check comment quality

3. **2.3 Type Safety Compliance** (for `src/[module_name]/`)
   - Check type hint presence
   - Run Mypy: `uvx mypy src/[module_name]/ --show-error-codes`
   - Check for `Any` usage
   - Check for imprecise types (`dict[str, Any]`, `list[Any]`)

**Verification Commands** (replace `[module_name]` with actual module):
```bash
MODULE="src/[module_name]"

# 1. Metadata check
for file in $(find "$MODULE" -name "*.py" -type f); do
  if grep -q "if __name__ == \"__main__\"" "$file" || \
     [[ "$file" == *"/workflows/"* ]] || \
     [[ "$file" == *"cli.py" ]] || \
     [[ "$file" == *"_cli.py" ]]; then
    if ! grep -q "@meta" "$file"; then
      echo "MISSING METADATA: $file"
    fi
  fi
done

# 2. Code quality checks
grep -rn "^[[:space:]]*def [a-z][a-zA-Z]*[A-Z]" "$MODULE" --include="*.py"  # Naming violations
grep -rn "^class [a-z]" "$MODULE" --include="*.py"  # Class naming
grep -rn "except:" "$MODULE" --include="*.py"  # Bare except
grep -rn "[^a-zA-Z_][0-9]\{2,\}[^0-9a-zA-Z_]" "$MODULE" --include="*.py" | grep -v "#"  # Magic numbers

# 3. Type safety check
uvx mypy "$MODULE" --show-error-codes
grep -rn "\bAny\b" "$MODULE" --include="*.py" | grep -v "from typing import"
grep -rn "dict\[str, Any\]\|Dict\[str, Any\]" "$MODULE" --include="*.py"
```

**Success Criteria**:
- All required files have metadata
- All code follows naming conventions
- Functions are well-structured
- No magic numbers
- Proper error handling
- All functions have type hints
- Mypy passes for this module: `uvx mypy src/[module_name]/ --show-error-codes`
- No `Any` types (or justified)

**Remediation Process**:
1. **Prioritize by severity**:
   - **Critical**: Type safety violations, error handling bugs → Fix immediately
   - **High**: Missing metadata on entry points, naming violations → Fix immediately
   - **Medium**: Long functions, magic numbers → Fix if straightforward
   - **Low**: Comment quality, minor style issues → Fix if time permits
2. **Fix incrementally**: Address issues as found, verify with tests and Mypy
3. **Verify fixes**: Run `uvx pytest tests/` and `uvx mypy src/[module_name]/ --show-error-codes` after fixes

**Documentation**: Record findings and fixes in module-specific section of compliance report.

---

### Step 2: Verify and Fix `src/api/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `api`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and Mypy to confirm.

**Module-specific notes**:
- API modules typically require metadata (entry points, handlers)
- Check for proper error handling in API endpoints
- Verify type hints for request/response types

---

### Step 3: Verify and Fix `src/benchmarking/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `benchmarking`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and Mypy to confirm.

**Module-specific notes**:
- Check CLI entry points for metadata
- Verify benchmarking workflow files have metadata
- Check for proper logging in benchmark execution

---

### Step 4: Verify and Fix `src/common/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `common`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and Mypy to confirm.

**Module-specific notes**:
- Shared utilities may not all need metadata (pure helpers)
- Document which utilities are pure helpers vs. utilities with side effects
- Verify shared types are in `src/common/types.py` (if exists)

---

### Step 5: Verify and Fix `src/conversion/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `conversion`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and Mypy to confirm.

**Module-specific notes**:
- Check conversion workflow files for metadata
- Verify proper error handling for file conversion operations
- Check type hints for conversion data structures

---

### Step 6: Verify `src/core/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `core`.

**Module-specific notes**:
- Core logic modules may be pure helpers or have side effects
- Document which files need metadata based on behavioral weight
- Verify core data structures have proper type definitions

---

### Step 7: Verify `src/data/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `data`.

**Module-specific notes**:
- Data processing modules may have side effects (file I/O)
- Check for proper error handling in data loading/processing
- Verify type hints for data structures

---

### Step 8: Verify `src/deployment/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `deployment`.

**Module-specific notes**:
- Deployment modules typically require metadata (entry points, workflows)
- Check for proper error handling in deployment operations
- Verify API inference types are properly typed

---

### Step 9: Verify `src/evaluation/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `evaluation`.

**Module-specific notes**:
- Evaluation workflows require metadata
- Check selection logic for proper type hints
- Verify benchmarking CLI has metadata

---

### Step 10: Verify `src/infrastructure/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `infrastructure`.

**Module-specific notes**:
- Infrastructure modules (tracking, paths, config) typically require metadata
- Check MLflow setup and tracking modules for metadata
- Verify path resolution utilities have proper error handling
- Check config modules for proper type definitions

---

### Step 11: Verify `src/orchestration/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `orchestration`.

**Module-specific notes**:
- Orchestration jobs require metadata (entry points, workflows)
- Check HPO, selection, and conversion job modules
- Verify tracking and artifact management modules have metadata
- Check for proper error handling in job execution

---

### Step 12: Verify `src/selection/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `selection`.

**Module-specific notes**:
- Selection logic modules may be utilities or workflows
- Document which files need metadata
- Verify selection types are properly defined

---

### Step 13: Verify `src/testing/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `testing`.

**Module-specific notes**:
- Testing utilities may not all need metadata
- Document which testing helpers are pure vs. have side effects
- Verify test utilities have proper type hints

---

### Step 14: Verify `src/training/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `training`.

**Module-specific notes**:
- Training workflows and orchestrators require metadata
- Check HPO execution modules for metadata
- Verify training core modules have proper type hints
- Check for proper error handling in training execution

---

### Step 15: Generate Overall Compliance Report

**Purpose**: Document findings, create actionable remediation list

**Actions**:
1. Compile findings from Steps 2-14 (all module verifications) into structured report
2. Categorize issues by:
   - **Severity**: Critical, High, Medium, Low
   - **Category**: Metadata, Naming, Structure, Types, Error Handling
   - **Module**: Group by module/package (api, benchmarking, common, etc.)
3. Create remediation checklist with file paths and line numbers
4. Generate summary statistics:
   - Total files checked (across all modules)
   - Files with issues (per module and overall)
   - Issues by category (per module and overall)
   - Compliance percentage (per module and overall)

**Report Format**:
```markdown
# Code Quality Compliance Report

**Generated**: YYYY-MM-DD
**Scope**: All Python files in `src/`

## Summary Statistics
- Total files: X
- Files checked: X
- Files with issues: X
- Compliance rate: X%

## Issues by Category

### File Metadata
- Missing metadata: X files
- Incomplete metadata: X files
- Format issues: X files

### Code Quality
- Naming violations: X issues
- Long functions: X functions
- Magic numbers: X instances
- Error handling issues: X instances

### Type Safety
- Missing type hints: X functions
- Mypy errors: X errors
- Any usage: X instances
- Imprecise types: X instances

## Detailed Findings

[Per-module breakdown with file paths and line numbers]
```

**Success Criteria**:
- Comprehensive report generated
- All findings documented with file paths
- Issues prioritized by severity
- Remediation checklist created

---


## Success Criteria (Overall)

- ✅ Complete inventory of all `src/` modules
- ✅ All entry-point scripts have proper metadata
- ✅ All workflow files have proper metadata
- ✅ All code follows naming conventions
- ✅ Functions are well-structured (length, parameters)
- ✅ No magic numbers (use named constants)
- ✅ Proper error handling (no bare except, errors logged)
- ✅ All functions have type hints
- ✅ Mypy passes with 0 errors: `uvx mypy src --show-error-codes`
- ✅ No `Any` types (or justified)
- ✅ Comprehensive compliance report generated
- ✅ All critical/high issues remediated

## Detailed Detection Criteria and Remediation Guidance

### File Metadata Compliance

**Detection Criteria**:

For each file that requires metadata (entry-points, workflows, tests, utilities with side effects):

1. **Metadata Presence Check**:
   - File starts with docstring containing `@meta` marker
   - Metadata block is comment-only (no executable code)

2. **Metadata Completeness Check**:
   - Required fields present based on file type:
     - **Scripts**: `name`, `type: script`, `domain`, `responsibility`, `inputs`, `outputs`, `tags`
     - **Workflows**: `name`, `type: script`, `domain`, `responsibility`, `tags`
     - **Tests**: `type: test`, `scope` (unit/integration/e2e), `domain`, `covers`, `excludes`, `tags`
     - **Utilities**: `name`, `type: utility`, `domain`, `responsibility`, `tags`

3. **Metadata Format Check**:
   - Uses YAML-like structure within docstring
   - Field names match expected format (snake_case)
   - Values are appropriate for field type

**Remediation Guidance**:
- **Missing metadata**: Add metadata block following format from `@python-file-metadata.mdc`
- **Incomplete metadata**: Add missing required fields
- **Wrong format**: Fix YAML structure, ensure comment-only docstring
- **Small pure helpers**: Document decision to skip metadata (add comment: `# No metadata: pure helper function`)

---

### Code Quality Compliance

**Detection Criteria**:

#### Naming Conventions
- **Variables/Functions**: `snake_case` (not `camelCase` or `PascalCase`)
- **Classes**: `PascalCase` (not `snake_case`)
- **Constants**: `SCREAMING_SNAKE_CASE` (not `snake_case`)
- **Booleans**: Prefixed with `is_`, `has_`, `can_`, `should_`
- **Language**: 100% English (no non-English names)

#### Function Structure
- **Function length**: ≤ 50 lines (recommended, flag if > 80)
- **Parameter count**: ≤ 3 parameters (flag if > 5)
- **Early returns**: Prefer early returns over deep nesting
- **Single responsibility**: One function = one task

#### Magic Numbers
- **No magic numbers**: Use named constants
- **Detection**: Numbers > 1 digit not in variable names or comments

#### Error Handling
- **No bare `except:`**: Must catch specific exceptions
- **Error logging**: Errors should be logged, not swallowed
- **Structured logging**: Use structured logging with context

#### Comments
- **Why > What**: Comments explain reason, not obvious behavior
- **No obvious comments**: Flag comments that just restate code

**Remediation Guidance**:
- **Naming violations**: Rename to follow conventions (use IDE refactoring)
- **Long functions**: Extract methods, split responsibilities
- **Many parameters**: Use `TypedDict` or `dataclass` for parameter objects
- **Deep nesting**: Extract to helper functions, use early returns
- **Magic numbers**: Extract to named constants at module/class level
- **Bare except**: Catch specific exceptions (`ValueError`, `FileNotFoundError`, etc.)
- **Swallowed errors**: Add logging, re-raise, or handle appropriately
- **Bad comments**: Remove obvious comments, add context to TODO/FIXME

---

### Type Safety Compliance

**Detection Criteria**:

#### Type Hint Presence
- **All functions**: Have type hints for parameters and return types
- **All classes**: Methods have type hints
- **No `Any` types**: Prefer precise types (`TypedDict`, `dataclass`, `Protocol`, `Literal`)

#### Mypy Compliance
- **Zero Mypy errors**: All modules pass Mypy strict checking
- **Error codes**: Use `# type: ignore[error-code]` with comments if suppression needed

#### Precise Types
- **No `dict[str, Any]`**: Use `TypedDict` or `Mapping[str, object]`
- **No `list[Any]`**: Use specific types or generics
- **Use narrow types**: `Literal`, `Protocol`, `TypedDict` where appropriate

**Remediation Guidance**:
- **Missing type hints**: Add type hints to all function signatures
- **Mypy errors**: Fix type errors, use precise types
- **Any usage**: Replace with `TypedDict`, `dataclass`, `Protocol`, or `Literal`
- **dict[str, Any]**: Create `TypedDict` or use `Mapping[str, object]` and tighten later
- **Type ignores**: Add error codes: `# type: ignore[error-code]` with explanation comment
- **Shared types**: Move common types to `src/common/types.py` to avoid duplication

---

## Tools and Commands Reference

### Quick Verification Commands

```bash
# 1. Inventory
find src/ -name "*.py" -type f | wc -l

# 2. Metadata check
grep -r "@meta" src/ --include="*.py" | wc -l

# 3. Type safety check
uvx mypy src --show-error-codes

# 4. Find entry points
grep -r "if __name__ == \"__main__\"" src/ --include="*.py" -l

# 5. Find bare except
grep -rn "except:" src/ --include="*.py"

# 6. Find Any usage
grep -rn "\bAny\b" src/ --include="*.py" | grep -v "from typing import"
```

## Notes

- **Module-by-module approach**: Each module is fully verified (metadata, code quality, type safety) before moving to the next.
- **Incremental remediation**: Fix issues module-by-module, not all at once.
- **Test after changes**: Always run tests and Mypy after making changes to a module.
- **Document decisions**: If skipping metadata for a file, document why in the compliance report.
- **Reuse-first**: When fixing issues, check for existing patterns/utilities to reuse.
- **Module independence**: Each module verification can be done independently, allowing parallel work if needed.

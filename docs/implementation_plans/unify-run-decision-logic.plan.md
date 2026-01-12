# Unify Run Decision Logic - Single Source of Truth

<!-- Implementation plan for creating a unified run decision utility that determines whether to reuse existing or create new runs across all process types (HPO, final training, selection, benchmarking) -->

## Overview

### Purpose

This plan introduces a **single source of truth for run decision logic** to eliminate code duplication and ensure consistent behavior when determining whether to reuse existing runs or create new ones across all process types:
- **HPO (Hyperparameter Optimization)**: Study reuse vs. new study creation
- **Final Training**: Checkpoint reuse vs. new training run
- **Best Model Selection**: Cache reuse vs. new selection
- **Benchmarking**: Inherits from HPO

**Why it matters**: Currently, the logic for "should I reuse existing or create new?" is duplicated and inconsistent:
- HPO: Uses `should_resume` boolean with `force_new` override scattered across multiple methods
- Final Training: Uses `is_reuse_if_exists()` check with manual completeness validation
- Both have similar logic but implemented differently, making it hard to maintain and extend

### Scope

**In scope**
- Create unified `run_decision.py` utility module
- Refactor HPO to use unified decision logic
- Refactor final training to use unified decision logic
- Ensure consistent behavior: `force_new` always creates new, `reuse_if_exists` reuses if exists (and complete), creates new if not
- Add support for `resume_if_incomplete` mode (future-ready)
- Maintain backward compatibility (default behavior unchanged)

**Out of scope**
- Changing the actual behavior of `run.mode` values (only unifying decision logic)
- Refactoring Optuna-specific or filesystem-specific implementation details
- Changing how completeness is checked (only unifying when to check)

### Guiding Principles

- **DRY (Don't Repeat Yourself)**: Single function for reuse decision
- **Backward Compatibility**: Default behavior unchanged
- **Type Safety**: Use type hints for better IDE support
- **Consistent Logic**: Same decision rules everywhere
- **Separation of Concerns**: Decision logic separate from existence/completeness checks

## Goals & Success Criteria

### Goals

- **G1**: Single source of truth for "should reuse or create new?" decision
- **G2**: Consistent behavior across HPO and final training
- **G3**: Zero code duplication for run decision logic
- **G4**: Easy to extend with new run modes or process types
- **G5**: Clear, testable decision logic

### Success Criteria

- [ ] All process types use `should_reuse_existing()` utility function
- [ ] No duplicate `force_new` override logic remains
- [ ] No duplicate `reuse_if_exists` check logic remains
- [ ] All existing tests pass
- [ ] New tests added for unified decision logic
- [ ] Type hints added for better IDE support
- [ ] Documentation updated

## Current State Analysis

### Existing Behavior

**HPO Decision Logic** (`src/training/hpo/core/study.py`):

1. **Initial decision** (lines 202-206):
   ```python
   should_resume = (
       self.checkpoint_config.get("auto_resume", True)
       and storage_path.exists()
   )
   ```

2. **Force new override** (lines 227-235):
   ```python
   from infrastructure.config.run_mode import is_force_new
   if is_force_new(combined_config):
       should_resume = False
       logger.info(f"[HPO] run.mode=force_new: Creating new study...")
   ```

3. **Load if exists flag** (lines 332-336):
   ```python
   force_new = is_force_new(combined_config)
   load_if_exists = self.checkpoint_enabled and not force_new
   ```

**Final Training Decision Logic** (`src/training/execution/executor.py`):

1. **Reuse if exists check** (lines 193-269):
   ```python
   from infrastructure.config.run_mode import is_reuse_if_exists
   if is_reuse_if_exists(final_training_yaml):
       # Check if checkpoint is complete
       if is_checkpoint_complete(final_checkpoint_dir, metadata_file):
           return final_checkpoint_dir  # Reuse
       # Otherwise continue (create new)
   ```

**Problems:**
- Logic duplicated: `force_new` override appears in multiple places
- Inconsistent: HPO uses `should_resume`, final training uses early return pattern
- Hard to extend: Adding new run mode requires changes in multiple places
- Hard to test: Decision logic scattered across multiple methods

### Current Run Mode Support

- ✅ `run_mode.py`: Already exists with `get_run_mode()`, `is_force_new()`, `is_reuse_if_exists()`
- ✅ HPO: Uses `is_force_new()` to override `should_resume`
- ✅ Final Training: Uses `is_reuse_if_exists()` to check before training
- ❌ **Missing**: Unified decision function that combines run mode + existence + completeness

## Proposed Solution

### Architecture

Create `src/infrastructure/config/run_decision.py` with:

1. **`should_reuse_existing()`**: Main decision function
   - Takes: config, exists flag, optional completeness flag, process type
   - Returns: boolean (True = reuse, False = create new)
   - Logic:
     - `force_new` → Always False (create new)
     - `reuse_if_exists` → True if exists (and complete if applicable)
     - `resume_if_incomplete` → True if exists and not complete
     - Default → `reuse_if_exists` behavior

2. **`get_load_if_exists_flag()`**: Helper for Optuna/other libraries
   - Takes: config, checkpoint_enabled, process_type
   - Returns: boolean for `load_if_exists` parameter
   - Used by HPO's Optuna `create_study(load_if_exists=...)`

### Decision Logic Flow

```
┌─────────────────────────────────────┐
│ should_reuse_existing()             │
├─────────────────────────────────────┤
│ 1. Check run.mode                   │
│    ├─ force_new → return False      │
│    ├─ reuse_if_exists → continue    │
│    └─ resume_if_incomplete → continue│
│                                     │
│ 2. Check if exists                  │
│    ├─ Not exists → return False     │
│    └─ Exists → continue             │
│                                     │
│ 3. Check completeness (if applicable)│
│    ├─ HPO: Not applicable           │
│    ├─ Final Training:               │
│    │  ├─ Complete → return True     │
│    │  └─ Incomplete → return False  │
│    └─ resume_if_incomplete:         │
│       ├─ Complete → return False    │
│       └─ Incomplete → return True  │
│                                     │
│ 4. Default: return True (reuse)     │
└─────────────────────────────────────┘
```

### File Structure

```
src/infrastructure/config/
├── run_mode.py          # Already exists: extraction utilities
└── run_decision.py      # NEW: Decision logic utilities
```

## Implementation Plan

### Phase 1: Create Unified Module

**Step 1.1: Create `run_decision.py`**
- [ ] Create `src/infrastructure/config/run_decision.py`
- [ ] Implement `should_reuse_existing()` function
- [ ] Implement `get_load_if_exists_flag()` function
- [ ] Add type hints and docstrings
- [ ] Add process type enum/literal

**Step 1.2: Add Tests**
- [ ] Create `tests/infrastructure/config/unit/test_run_decision.py`
- [ ] Test `force_new` mode (always False)
- [ ] Test `reuse_if_exists` mode (True if exists, False if not)
- [ ] Test `reuse_if_exists` with completeness (final training)
- [ ] Test `resume_if_incomplete` mode (future)
- [ ] Test default behavior
- [ ] Test `get_load_if_exists_flag()` for HPO

**Step 1.3: Export from `__init__.py`**
- [ ] Update `src/infrastructure/config/__init__.py`
- [ ] Export `should_reuse_existing`, `get_load_if_exists_flag`
- [ ] Export `ProcessType` if using enum

### Phase 2: Refactor HPO

**Step 2.1: Update `study.py` - `create_or_load_study()`**
- [ ] Replace `should_resume` calculation with `should_reuse_existing()`
- [ ] Remove duplicate `is_force_new()` check (now in unified function)
- [ ] Update logging to use unified decision
- [ ] Keep Optuna-specific logic (storage_path, etc.)

**Step 2.2: Update `study.py` - `_create_new_study()`**
- [ ] Replace `load_if_exists` calculation with `get_load_if_exists_flag()`
- [ ] Remove duplicate `is_force_new()` check
- [ ] Keep Optuna-specific logic

**Step 2.3: Update Tests**
- [ ] Update HPO tests to verify unified decision logic
- [ ] Ensure all existing HPO tests still pass
- [ ] Add tests for edge cases (no study, force_new, etc.)

### Phase 3: Refactor Final Training

**Step 3.1: Update `executor.py`**
- [ ] Replace `is_reuse_if_exists()` check with `should_reuse_existing()`
- [ ] Pass completeness check result to unified function
- [ ] Simplify early return logic
- [ ] Keep filesystem-specific completeness check logic

**Step 3.2: Update Tests**
- [ ] Update final training tests to verify unified decision logic
- [ ] Ensure all existing final training tests still pass
- [ ] Add tests for edge cases (no checkpoint, incomplete checkpoint, etc.)

### Phase 4: Cleanup & Documentation

**Step 4.1: Remove Duplicate Logic**
- [ ] Search for remaining `is_force_new()` checks that duplicate decision logic
- [ ] Search for remaining `is_reuse_if_exists()` checks that duplicate decision logic
- [ ] Refactor to use unified functions where appropriate

**Step 4.2: Update Documentation**
- [ ] Update docstrings in `run_mode.py` to reference `run_decision.py`
- [ ] Add examples in `run_decision.py` docstrings
- [ ] Update any architecture docs that mention run mode logic

**Step 4.3: Verify Integration**
- [ ] Run all tests
- [ ] Verify HPO smoke tests
- [ ] Verify final training smoke tests
- [ ] Check for any regressions

## Detailed Implementation

### `run_decision.py` Implementation

```python
"""Unified run decision logic for all process types.

Single source of truth for determining whether to reuse existing
or create new runs based on run.mode configuration.

Used by:
- HPO: Study reuse vs. new study creation
- Final Training: Checkpoint reuse vs. new training run
- Best Model Selection: Cache reuse
- Benchmarking: Inherits from HPO
"""

from typing import Any, Dict, Optional, Literal
from infrastructure.config.run_mode import RunMode, get_run_mode, is_force_new, is_reuse_if_exists

ProcessType = Literal["hpo", "final_training", "selection", "benchmarking"]


def should_reuse_existing(
    config: Dict[str, Any],
    exists: bool,
    is_complete: Optional[bool] = None,
    process_type: ProcessType = "hpo",
) -> bool:
    """
    Unified decision: Should we reuse existing or create new?
    
    Logic:
    - force_new: Always False (create new, ignore existing)
    - reuse_if_exists: True if exists (and complete if applicable)
    - resume_if_incomplete: True if exists and not complete
    
    Args:
        config: Configuration dict with run.mode
        exists: Whether the existing run/checkpoint/study exists
        is_complete: Optional completeness check (for final training)
                    None = not applicable (HPO), True/False = complete/incomplete
        process_type: Type of process (for logging/context)
    
    Returns:
        True if should reuse existing, False if should create new
    
    Examples:
        >>> # HPO: force_new → always create new
        >>> should_reuse_existing({"run": {"mode": "force_new"}}, exists=True)
        False
        
        >>> # Final Training: reuse_if_exists with complete checkpoint → reuse
        >>> should_reuse_existing({"run": {"mode": "reuse_if_exists"}}, exists=True, is_complete=True)
        True
        
        >>> # Final Training: reuse_if_exists but incomplete → create new
        >>> should_reuse_existing({"run": {"mode": "reuse_if_exists"}}, exists=True, is_complete=False)
        False
    """
    run_mode = get_run_mode(config)
    
    # force_new: Always create new (highest priority)
    if is_force_new(config):
        return False
    
    # If doesn't exist, can't reuse
    if not exists:
        return False
    
    # reuse_if_exists: Reuse if exists (and complete if applicable)
    if is_reuse_if_exists(config):
        # For final training, only reuse if complete
        if process_type == "final_training" and is_complete is not None:
            return is_complete
        # For HPO and others, reuse if exists
        return True
    
    # resume_if_incomplete: Reuse if exists and NOT complete
    if run_mode == "resume_if_incomplete":
        if is_complete is not None:
            return not is_complete
        # If completeness not applicable, treat as reuse_if_exists
        return True
    
    # Default: reuse_if_exists behavior
    return True


def get_load_if_exists_flag(
    config: Dict[str, Any],
    checkpoint_enabled: bool,
    process_type: ProcessType = "hpo",
) -> bool:
    """
    Determine load_if_exists flag for Optuna/other libraries.
    
    For HPO: Used in Optuna's create_study(load_if_exists=...)
    For other processes: May be used in similar contexts
    
    Args:
        config: Configuration dict with run.mode
        checkpoint_enabled: Whether checkpointing is enabled
        process_type: Type of process
    
    Returns:
        True if should load existing if exists, False if always create new
    """
    # If checkpointing disabled, can't load existing
    if not checkpoint_enabled:
        return False
    
    # force_new: Never load existing
    if is_force_new(config):
        return False
    
    # reuse_if_exists or default: Load if exists
    return True
```

### HPO Refactoring Example

**Before:**
```python
# In create_or_load_study()
should_resume = (
    self.checkpoint_config.get("auto_resume", True)
    and storage_path.exists()
)

from infrastructure.config.run_mode import is_force_new
if is_force_new(combined_config):
    should_resume = False
    logger.info(f"[HPO] run.mode=force_new: Creating new study...")

if should_resume:
    return self._load_existing_study(...)
else:
    return self._create_new_study(...)
```

**After:**
```python
# In create_or_load_study()
from infrastructure.config.run_decision import should_reuse_existing

should_resume = should_reuse_existing(
    config=combined_config,
    exists=storage_path.exists(),
    process_type="hpo"
)

if should_resume:
    return self._load_existing_study(...)
else:
    return self._create_new_study(...)
```

### Final Training Refactoring Example

**Before:**
```python
from infrastructure.config.run_mode import is_reuse_if_exists
if is_reuse_if_exists(final_training_yaml):
    if is_checkpoint_complete(final_checkpoint_dir, metadata_file):
        return final_checkpoint_dir  # Reuse
    # Otherwise continue (create new)
```

**After:**
```python
from infrastructure.config.run_decision import should_reuse_existing

is_complete = is_checkpoint_complete(final_checkpoint_dir, metadata_file)
should_reuse = should_reuse_existing(
    config=final_training_yaml,
    exists=final_checkpoint_dir.exists(),
    is_complete=is_complete,
    process_type="final_training"
)

if should_reuse:
    return final_checkpoint_dir  # Reuse
# Otherwise continue (create new)
```

## Testing Strategy

### Unit Tests

**Test File**: `tests/infrastructure/config/unit/test_run_decision.py`

**Test Cases:**

1. **`should_reuse_existing()` - force_new mode**
   - [ ] `force_new` + exists → False
   - [ ] `force_new` + not exists → False
   - [ ] `force_new` + exists + complete → False
   - [ ] `force_new` + exists + incomplete → False

2. **`should_reuse_existing()` - reuse_if_exists mode (HPO)**
   - [ ] `reuse_if_exists` + exists → True
   - [ ] `reuse_if_exists` + not exists → False

3. **`should_reuse_existing()` - reuse_if_exists mode (Final Training)**
   - [ ] `reuse_if_exists` + exists + complete → True
   - [ ] `reuse_if_exists` + exists + incomplete → False
   - [ ] `reuse_if_exists` + not exists → False

4. **`should_reuse_existing()` - resume_if_incomplete mode**
   - [ ] `resume_if_incomplete` + exists + incomplete → True
   - [ ] `resume_if_incomplete` + exists + complete → False
   - [ ] `resume_if_incomplete` + not exists → False

5. **`should_reuse_existing()` - default behavior**
   - [ ] No run.mode + exists → True (defaults to reuse_if_exists)
   - [ ] No run.mode + not exists → False

6. **`get_load_if_exists_flag()`**
   - [ ] `force_new` + checkpoint_enabled → False
   - [ ] `reuse_if_exists` + checkpoint_enabled → True
   - [ ] `reuse_if_exists` + checkpoint_disabled → False
   - [ ] No run.mode + checkpoint_enabled → True

### Integration Tests

- [ ] HPO with `force_new` creates new study
- [ ] HPO with `reuse_if_exists` reuses existing study
- [ ] HPO with `reuse_if_exists` creates new if no study exists
- [ ] Final training with `force_new` creates new checkpoint
- [ ] Final training with `reuse_if_exists` reuses complete checkpoint
- [ ] Final training with `reuse_if_exists` creates new if incomplete

## Migration Checklist

### Pre-Migration
- [ ] All existing tests pass
- [ ] Document current behavior for comparison
- [ ] Create backup branch

### Migration Steps
- [ ] Phase 1: Create unified module + tests
- [ ] Phase 2: Refactor HPO
- [ ] Phase 3: Refactor final training
- [ ] Phase 4: Cleanup & documentation

### Post-Migration
- [ ] All tests pass
- [ ] No regressions in behavior
- [ ] Code review
- [ ] Update documentation

## Risks & Mitigation

### Risk 1: Behavior Change
**Risk**: Unified logic might change behavior unintentionally
**Mitigation**: 
- Comprehensive test coverage
- Compare behavior before/after
- Gradual migration (one process type at a time)

### Risk 2: Breaking Changes
**Risk**: Refactoring might break existing functionality
**Mitigation**:
- Keep existing tests passing
- Add new tests before refactoring
- Test in isolation first

### Risk 3: Performance Impact
**Risk**: Additional function call overhead
**Mitigation**:
- Minimal overhead (simple boolean logic)
- Profile if needed (unlikely to be significant)

## Future Enhancements

### Potential Additions
- [ ] Support for `resume_if_incomplete` mode (currently stubbed)
- [ ] Process-specific decision rules (if needed)
- [ ] Caching of decisions (if performance becomes issue)
- [ ] More granular logging of decisions

### Related Work
- This builds on `run_mode.py` (already unified extraction)
- Could be extended for other process types (selection, benchmarking)
- Could inform future run mode values

## References

- `src/infrastructure/config/run_mode.py` - Run mode extraction utilities
- `src/training/hpo/core/study.py` - Current HPO decision logic
- `src/training/execution/executor.py` - Current final training decision logic
- `docs/implementation_plans/unify-run-mode-logic.plan.md` - Related plan for run mode extraction

## Timeline Estimate

- **Phase 1**: 2-3 hours (create module + tests)
- **Phase 2**: 2-3 hours (refactor HPO)
- **Phase 3**: 2-3 hours (refactor final training)
- **Phase 4**: 1-2 hours (cleanup + docs)

**Total**: ~8-11 hours

## Notes

- This plan focuses on unifying decision logic, not changing behavior
- Backward compatibility is critical
- Tests are essential to ensure no regressions
- Can be done incrementally (one phase at a time)


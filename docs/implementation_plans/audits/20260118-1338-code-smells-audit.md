# Code Smells Audit - 2026-01-18

## Summary

This audit catalogs all code smells identified in the codebase for systematic refactoring.

**Date**: 2026-01-18  
**Scope**: `src/` directory  
**Total Files Analyzed**: ~200 Python files  
**Total Lines**: ~51,444 lines

## Metrics Overview

- **Large Files (>200 lines)**: 30+ files
- **Long Methods (>50 lines)**: 30+ functions
- **Long Parameter Lists (>5 params)**: 20+ functions
- **Type Safety Issues (`Any` usage)**: 743 instances
- **Deep Nesting (3+ levels)**: 846 instances
- **Complex Conditionals**: 50 instances
- **Magic Numbers**: ~687 instances (estimated)

---

## Category 1: Large Files (>200 lines)

### Critical Priority (🔴)

| File | Lines | Functions | Issues |
|------|-------|-----------|--------|
| `src/evaluation/selection/trial_finder.py` | 1753 | 20 | Multiple responsibilities: MLflow queries, directory ops, champion selection, trial discovery |
| `src/training/hpo/execution/local/sweep.py` | 1510 | 3 | Massive functions: `run_local_hpo_sweep` (922 lines), `create_local_hpo_objective` (351 lines), nested `objective` (239 lines) |

### High Priority (🟠)

| File | Lines | Functions | Issues |
|------|-------|-----------|--------|
| `src/evaluation/benchmarking/orchestrator.py` | 1068 | 19 | Complex orchestration, multiple concerns mixed |
| `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` | 1049 | 9 | Long methods: `start_sweep_run` (157 lines), `log_final_metrics` (175 lines), `_log_best_trial_checkpoint` (223 lines) |

### Medium Priority (🟡)

| File | Lines | Functions | Issues |
|------|-------|-----------|--------|
| `src/infrastructure/config/training.py` | 881 | - | Config parsing + validation |
| `src/evaluation/selection/artifact_unified/acquisition.py` | 784 | - | Multiple acquisition strategies |
| `src/infrastructure/metadata/training.py` | 743 | - | Metadata handling |
| `src/common/shared/mlflow_setup.py` | 738 | - | Setup + configuration |
| `src/training/hpo/execution/local/refit.py` | 737 | - | Refit orchestration |

---

## Category 2: Long Methods (>50 lines)

### Critical Priority (🔴)

| Function | File | Lines | Params | Nesting | Priority |
|----------|------|-------|--------|---------|----------|
| `run_local_hpo_sweep` | `sweep.py` | 922 | 15 | 57 | 🔴 CRITICAL |
| `select_champion_per_backbone` | `trial_finder.py` | 372 | 6 | - | 🔴 HIGH |
| `create_local_hpo_objective` | `sweep.py` | 351 | 13 | 6 | 🔴 HIGH |
| `objective` (nested) | `sweep.py` | 239 | - | - | 🔴 HIGH |

### High Priority (🟠)

| Function | File | Lines | Params | Nesting | Priority |
|----------|------|-------|--------|---------|----------|
| `_log_best_trial_checkpoint` | `sweep_tracker.py` | 223 | - | - | 🟠 HIGH |
| `log_final_metrics` | `sweep_tracker.py` | 175 | 15 | - | 🟠 HIGH |
| `start_sweep_run` | `sweep_tracker.py` | 157 | 15 | - | 🟠 HIGH |
| `_set_phase2_hpo_tags` | `sweep.py` | 143 | 6 | 15 | 🟠 HIGH |
| `benchmark_best_trials` | `orchestrator.py` | 187 | 16 | - | 🟠 HIGH |
| `_benchmark_exists_in_mlflow` | `orchestrator.py` | 77 | 6 | 4 | 🟠 MEDIUM |
| `filter_missing_benchmarks` | `orchestrator.py` | 78 | 9 | - | 🟠 MEDIUM |

---

## Category 3: Long Parameter Lists (>5 parameters)

### Critical Priority (🔴)

| Function | File | Params | Priority |
|----------|------|--------|----------|
| `run_local_hpo_sweep` | `sweep.py` | 15 | 🔴 CRITICAL |
| `benchmark_best_trials` | `orchestrator.py` | 16 | 🔴 HIGH |
| `start_sweep_run` | `sweep_tracker.py` | 15 | 🔴 HIGH |
| `log_final_metrics` | `sweep_tracker.py` | 15 | 🔴 HIGH |

### High Priority (🟠)

| Function | File | Params | Priority |
|----------|------|--------|----------|
| `create_local_hpo_objective` | `sweep.py` | 13 | 🟠 MEDIUM |
| `filter_missing_benchmarks` | `orchestrator.py` | 9 | 🟠 MEDIUM |
| `benchmark_already_exists` | `orchestrator.py` | 8 | 🟠 MEDIUM |
| `select_champion_per_backbone` | `trial_finder.py` | 6 | 🟠 MEDIUM |
| `_set_phase2_hpo_tags` | `sweep.py` | 6 | 🟠 MEDIUM |
| `_log_sweep_metadata` | `sweep_tracker.py` | 8 | 🟠 MEDIUM |

---

## Category 4: Type Safety Issues

### Current State

- **Total `Any` usage**: 743 instances across ~110 files
- **Common patterns**:
  - `Dict[str, Any]` for config dictionaries
  - `Any` for MLflow run objects
  - `dict[str, Any]` for trial metadata
  - Missing type hints in function signatures

### Files with Most `Any` Usage

1. `src/training/hpo/execution/local/sweep.py` - ~50+ instances
2. `src/evaluation/selection/trial_finder.py` - ~40+ instances
3. `src/infrastructure/tracking/mlflow/trackers/sweep_tracker.py` - ~35+ instances
4. `src/evaluation/benchmarking/orchestrator.py` - ~30+ instances

### Refactoring Targets

- Replace `Dict[str, Any]` configs with `TypedDict` or `dataclass`
- Create `MLflowRunDict` TypedDict for MLflow run data
- Create `TrialMetadataDict` TypedDict for trial metadata
- Add type hints to all function signatures

---

## Category 5: Complex Conditionals and Deep Nesting

### Current State

- **Deep nesting (3+ levels)**: 846 instances across 149 files
- **Complex conditionals**: 50 instances (`if ... and ... or`)
- **Deepest nesting**: `sweep.py` has 57 levels of nesting in `run_local_hpo_sweep`

### Critical Issues

| File | Function | Nesting Depth | Issue |
|------|----------|---------------|-------|
| `sweep.py` | `run_local_hpo_sweep` | 57 | Excessive nesting, needs guard clauses |
| `sweep.py` | `_set_phase2_hpo_tags` | 15 | Deep nesting, complex conditionals |
| `orchestrator.py` | `_benchmark_exists_in_mlflow` | 4 | Nested conditionals |

### Refactoring Targets

1. Extract guard clauses for early returns
2. Extract complex conditionals into named predicate functions
3. Use `match/case` for long if/elif chains (Python 3.10+)
4. Reduce nesting depth to max 2-3 levels

---

## Category 6: Magic Numbers

### Current State

- **Estimated magic numbers**: ~687 instances across 123 files
- **Common patterns**:
  - MLflow query limits: `1000`, `5000`, `10`, `5`
  - Batch sizes: `32`, `16`, `64`
  - Retry counts: `3`, `5`, `10`
  - Timeout values: `30`, `60`, `300`
  - Hash truncation: `[:12]`, `[:16]`, `[:8]`

### Refactoring Targets

- Extract MLflow query limits to constants
- Extract batch sizes to named constants
- Extract retry/timeout values to constants
- Extract hash display lengths to constants

---

## Category 7: Code Duplication

### Common Duplication Patterns

1. **MLflow client creation** - Found in multiple files
2. **Path resolution patterns** - Repeated across modules
3. **Error handling patterns** - Similar try/except blocks
4. **Validation patterns** - Repeated validation logic

### Refactoring Targets

- Consolidate MLflow client creation in `infrastructure.tracking.mlflow.client`
- Consolidate path resolution in `infrastructure.paths.resolve`
- Extract common error handling to shared utilities
- Extract validation patterns to shared utilities

---

## Refactoring Priority Order

### Phase 1: Critical Files (Steps 2-5)

1. ✅ **Step 2**: `trial_finder.py` (1753 → 113 lines, 93% reduction) - COMPLETE
   - Extracted 6 focused modules
   - Some modules still need further breakdown (champion_selection.py: 606 lines, discovery.py: 523 lines)
2. ⏳ **Step 3**: `sweep.py` (1510 lines) - Extract orchestration
3. ⏳ **Step 4**: `orchestrator.py` (1068 lines) - Extract benchmarking
4. ⏳ **Step 5**: `sweep_tracker.py` (1049 lines) - Extract tracking

### Phase 2: Long Methods (Step 6)

- Extract long methods from critical files
- Create Parameter Objects for functions with >5 params

### Phase 3: Type Safety (Step 8)

- Replace `Any` types with precise types
- Create shared type definitions

### Phase 4: Conditionals & Constants (Steps 9-10)

- Simplify complex conditionals
- Extract magic numbers to constants

### Phase 5: Consolidation (Step 11)

- Consolidate duplicate code patterns

---

## Baseline Metrics

**Recorded**: 2026-01-18

- Files >200 lines: 30+
- Functions >50 lines: 30+
- Functions with >5 params: 20+
- `Any` usage: 743 instances
- Deep nesting: 846 instances
- Complex conditionals: 50 instances
- Magic numbers: ~687 instances

---

## Success Criteria

After refactoring:

- ✅ Files <200 lines (except justified cases)
- ✅ Functions <50 lines (except justified cases)
- ✅ Functions with >5 params use Parameter Objects
- ✅ `Any` usage reduced by 80%+ (<150 instances)
- ✅ Deep nesting reduced by 50%+ (<425 instances)
- ✅ Complex conditionals reduced by 70%+ (<15 instances)
- ✅ Magic numbers reduced by 80%+ (<140 instances)
- ✅ All tests pass
- ✅ Mypy passes


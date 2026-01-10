# DRY Violations Analysis

## Critical: Triple Duplicate Functions (HIGH PRIORITY)

1. **Sweep Job Creation Functions (3 copies):**
   - `create_hpo_sweep_job_for_backbone()` exists in:
     - `src/hpo/execution/azureml/sweeps.py`
     - `src/orchestration/jobs/hpo/azureml/sweeps.py`
     - `src/orchestration/jobs/sweeps.py`
   - `create_dry_run_sweep_job_for_backbone()` exists in same 3 files
   - **Action:** Merge all 3 versions, keep single source in `src/hpo/execution/azureml/sweeps.py`

2. **Load Functions (2+ copies):**
   - `load_best_trial_from_disk()` exists in:
     - `src/orchestration/jobs/local_selection.py`
     - `src/orchestration/jobs/selection/disk_loader.py`
   - `load_benchmark_speed_score()` exists in:
     - `src/orchestration/jobs/selection/disk_loader.py`
     - `src/selection/disk_loader.py`
   - **Action:** Consolidate to single location in `src/selection/`

## Circular Dependencies (174 imports found)

1. **Orchestration Jobs importing from Orchestration:**
   - 174 imports from `orchestration.*` within `orchestration/jobs/` files
   - Creates circular dependencies and tight coupling
   - **Action:** Replace with direct imports from consolidated `src/` modules
   - Examples:
     - `from orchestration.final_training_config import ...` → `from config.training import ...`
     - `from orchestration.jobs.tracking.naming.tags import ...` → `from naming.mlflow.tags import ...`
     - `from orchestration.jobs.local_selection_v2 import ...` → `from selection.local_selection_v2 import ...`

## Redundant Logic Patterns (288 conditionals found)

1. **Path/File Existence Checks:**
   - 288 instances of `if Path(...).exists()`, `if isinstance(..., str)`, `if hasattr(...)` patterns
   - Many could be consolidated into utility functions
   - **Action:** Review and consolidate common patterns into `src/core/` or `src/paths/` utilities

2. **Repeated Import Patterns:**
   - Multiple files have similar import structures for MLflow, tracking, naming
   - **Action:** Create common import helpers or consolidate imports

## Unused Fallback Logic

1. **Facade Files:**
   - Many `orchestration/*.py` files are facades that may contain unused fallback logic
   - **Action:** Verify facades only re-export, remove any redundant validation/transformation logic

2. **Import Fallbacks:**
   - Check for `try/except ImportError` patterns that try multiple import paths
   - **Action:** Remove fallbacks after consolidation, use single import path


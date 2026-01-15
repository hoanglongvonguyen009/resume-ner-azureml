# Path and Naming Utilities Audit

**Generated**: 2026-01-15  
**Purpose**: Comprehensive inventory of all path and naming utilities, their call sites, and dependencies for Step 1 of consolidation plan.

## Executive Summary

- **Total path utilities**: 7 modules, 24 functions
- **Total naming utilities**: 14 modules, 88+ functions
- **Duplicate implementations**: 3 major duplicates identified
- **Redundant inference patterns**: 20+ locations with hardcoded `Path.cwd() / "config"`
- **Call site counts**: 
  - `build_mlflow_run_name`: 31+ call sites
  - `format_run_name`: 15+ call sites
  - `load_naming_policy`: 25+ call sites
  - `infer_config_dir`: 37+ call sites
  - `find_project_root`: 12+ call sites

## 1. Path Domain Utilities

### 1.1 Module: `src/infrastructure/paths/utils.py`

**Purpose**: Path utility functions, find project root directory

**Functions**:
1. `find_project_root(config_dir: Path) -> Path`
   - Finds project root by walking up from config_dir
   - Looks for directory containing both `src/` and `src/training/` subdirectories
   - **Call sites**: 12+ locations

**Dependencies**:
- `common.shared.logging_utils`

**Exports**: `find_project_root`

---

### 1.2 Module: `src/infrastructure/paths/config.py`

**Purpose**: Load and manage paths.yaml configuration with caching

**Functions**:
1. `load_paths_config(config_dir: Path, storage_env: Optional[str] = None) -> Dict[str, Any]`
   - Loads paths.yaml with mtime-based caching
   - **Call sites**: 15+ locations
2. `apply_env_overrides(config: Dict[str, Any], storage_env: Optional[str] = None) -> Dict[str, Any]`
   - Applies environment-specific overrides
   - **Call sites**: 8+ locations
3. `validate_paths_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None`
   - Validates paths configuration schema
   - **Call sites**: 3+ locations
4. `_get_default_paths() -> Dict[str, Any]` (private)
   - Returns default paths configuration

**Dependencies**:
- `core.placeholders`
- `core.tokens`
- `common.shared.yaml_utils`
- `common.shared.file_utils`

**Exports**: `load_paths_config`, `apply_env_overrides`, `validate_paths_config`

---

### 1.3 Module: `src/infrastructure/paths/resolve.py`

**Purpose**: Resolve all output paths (single authority for filesystem layout)

**Functions**:
1. `resolve_output_path(root_dir: Path, process_type: str, context: NamingContext, config_dir: Optional[Path] = None, storage_env: Optional[str] = None) -> Path`
   - Main path resolution function
   - **Call sites**: 20+ locations
2. `build_output_path(root_dir: Path, context: NamingContext, config_dir: Optional[Path] = None, storage_env: Optional[str] = None) -> Path`
   - Builds output path from context
   - **Call sites**: 25+ locations
3. `_get_pattern_key(process_type: str) -> Optional[str]` (private)
4. `_validate_output_path_internal(path: Path, process_type: str) -> None` (private)
5. `_build_output_path_fallback(...)` (private)

**Constants**:
- `PROCESS_PATTERN_KEYS: Dict[str, str]` - Maps process_type to pattern keys

**Dependencies**:
- `core.normalize`
- `core.placeholders`
- `.config` (load_paths_config, apply_env_overrides)
- `.validation` (validate_output_path)
- `infrastructure.naming.context` (NamingContext)

**Exports**: `resolve_output_path`, `build_output_path`, `PROCESS_PATTERN_KEYS`

---

### 1.4 Module: `src/infrastructure/paths/parse.py`

**Purpose**: Parse HPO and other output paths to extract components

**Functions**:
1. `parse_hpo_path_v2(path: Path) -> Optional[Dict[str, str]]`
   - Parses HPO v2 path pattern: `{storage_env}/{model}/study-{study8}/trial-{trial8}`
   - **Call sites**: 5+ locations
2. `is_v2_path(path: Path) -> bool`
   - Checks if path matches v2 pattern
   - **Call sites**: 8+ locations
3. `find_study_by_hash(backbone_dir: Path, study8: str) -> Optional[Path]`
   - Finds study directory by hash
   - **Call sites**: 3+ locations
4. `find_trial_by_hash(study_dir: Path, trial8: str) -> Optional[Path]`
   - Finds trial directory by hash
   - **Call sites**: 3+ locations

**Dependencies**:
- `.config` (load_paths_config)
- `.resolve` (resolve_output_path)

**Exports**: `parse_hpo_path_v2`, `is_v2_path`, `find_study_by_hash`, `find_trial_by_hash`

---

### 1.5 Module: `src/infrastructure/paths/drive.py`

**Purpose**: Drive backup path mapping and Colab-specific path resolution

**Functions**:
1. `get_drive_backup_base(config_dir: Path) -> Optional[Path]`
   - Gets base Google Drive backup directory from config
   - **Call sites**: 3+ locations
2. `get_drive_backup_path(local_path: Path, config_dir: Path) -> Optional[Path]`
   - Maps local path to Drive backup path
   - **Call sites**: 5+ locations
3. `resolve_output_path_for_colab(output_dir: Path, config_dir: Path) -> Path`
   - Resolves output path for Colab environment
   - **Call sites**: 2+ locations

**Dependencies**:
- `common.shared.platform_detection`
- `common.shared.logging_utils`
- `.config` (load_paths_config)
- `.validation` (validate_path_before_mkdir)

**Exports**: `get_drive_backup_base`, `get_drive_backup_path`, `resolve_output_path_for_colab`

---

### 1.6 Module: `src/infrastructure/paths/validation.py`

**Purpose**: Path validation utilities

**Functions**:
1. `validate_path_before_mkdir(path: Path, context: str = "directory") -> Path`
   - Validates path before creating directory
   - **Call sites**: 10+ locations
2. `validate_output_path(path: Path) -> Path`
   - Validates output path
   - **Call sites**: 5+ locations

**Dependencies**:
- `common.shared.logging_utils`

**Exports**: `validate_path_before_mkdir`, `validate_output_path`

---

### 1.7 Module: `src/infrastructure/paths/cache.py`

**Purpose**: Cache file path management

**Functions**:
1. `get_cache_file_path(...)`
2. `get_timestamped_cache_filename(...)`
3. `get_cache_strategy_config(...)`
4. `save_cache_with_dual_strategy(...)`
5. `load_cache_file(...)`

**Note**: Cache utilities are not part of core path/naming consolidation but included for completeness.

---

## 2. Naming Domain Utilities

### 2.1 Module: `src/infrastructure/naming/context.py`

**Purpose**: Define NamingContext dataclass and factory function

**Classes**:
1. `NamingContext` (dataclass)
   - Core data structure for naming identity
   - Fields: process_type, model, environment, storage_env, study_key_hash, trial_key_hash, etc.

**Functions**:
1. `create_naming_context(...) -> NamingContext`
   - Factory function to create NamingContext with validation
   - **Call sites**: 50+ locations

**Dependencies**: None (core dataclass)

**Exports**: `NamingContext`, `create_naming_context`

---

### 2.2 Module: `src/infrastructure/naming/context_tokens.py`

**Purpose**: Expand NamingContext into token dictionary

**Functions**:
1. `build_token_values(context: NamingContext) -> Dict[str, str]`
   - Expands context into token dictionary for path/name patterns
   - **Call sites**: 15+ locations

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)

**Exports**: `build_token_values`

---

### 2.3 Module: `src/infrastructure/naming/display_policy.py`

**Purpose**: Load naming policy from YAML, format and validate display/run names

**Functions**:
1. `load_naming_policy(config_dir: Optional[Path] = None, validate: bool = True) -> Dict[str, Any]`
   - Loads naming.yaml with mtime-based caching
   - **Call sites**: 25+ locations
   - **DUPLICATE**: Also in `orchestration.jobs.tracking.naming.policy`
2. `validate_naming_policy(policy: Dict[str, Any], policy_path: Optional[Path] = None) -> None`
   - Validates naming policy schema
   - **Call sites**: 5+ locations
3. `format_run_name(process_type: str, context: NamingContext, policy: Optional[Dict[str, Any]] = None, config_dir: Optional[Path] = None) -> str`
   - Formats run name using policy pattern
   - **Call sites**: 15+ locations
   - **DUPLICATE**: Also in `orchestration.jobs.tracking.naming.policy`
4. `validate_run_name(name: str, policy: Dict[str, Any]) -> None`
   - Validates run name against policy rules
   - **Call sites**: 8+ locations
5. `parse_parent_training_id(parent_id: str) -> Dict[str, str]`
   - Parses parent training ID into components
   - **Call sites**: 3+ locations
6. `extract_component(context: NamingContext, component_config: Dict[str, Any], policy: Dict[str, Any], process_type: str) -> str`
   - Extracts component value from context
   - **Call sites**: Internal use

**Dependencies**:
- `core.normalize`
- `core.placeholders`
- `core.tokens`
- `infrastructure.naming.context` (NamingContext)
- `infrastructure.naming.context_tokens` (build_token_values)
- `common.shared.yaml_utils`
- `common.shared.file_utils`
- `orchestration.jobs.tracking.naming.policy` (sanitize_semantic_suffix - circular!)

**Exports**: `load_naming_policy`, `format_run_name`, `validate_naming_policy`, `validate_run_name`, `parse_parent_training_id`

---

### 2.4 Module: `src/infrastructure/naming/mlflow/run_names.py`

**Purpose**: Generate human-readable MLflow run names from NamingContext

**Functions**:
1. `build_mlflow_run_name(context: NamingContext, config_dir: Optional[Path] = None, root_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> str`
   - Main run name building function with auto-increment support
   - **Call sites**: 31+ locations
   - **DUPLICATE**: Also in `orchestration.jobs.tracking.naming.run_names`
2. `_build_legacy_run_name(...) -> str` (private)
   - Legacy fallback when policy not available
3. `_short(value: Optional[str], default: str = "unknown") -> str` (private)
4. `_strip_env_prefix(trial_id: str, environment: Optional[str]) -> str` (private)

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)
- `infrastructure.naming.display_policy` (load_naming_policy, format_run_name, validate_run_name)
- `infrastructure.naming.mlflow.run_keys` (build_mlflow_run_key, build_mlflow_run_key_hash, build_counter_key)
- `infrastructure.naming.mlflow.config` (get_naming_config, get_auto_increment_config)
- `orchestration.jobs.tracking.index.version_counter` (reserve_run_name_version)

**Exports**: `build_mlflow_run_name`

---

### 2.5 Module: `src/infrastructure/naming/mlflow/policy.py`

**Purpose**: Backward-compatible re-exports for naming policy helpers (legacy bridge)

**Functions**:
1. `_get_policy_module()` - Returns orchestration policy module
2. `load_naming_policy(*args, **kwargs)` - Re-export wrapper
3. `format_run_name(*args, **kwargs)` - Re-export wrapper
4. `validate_run_name(*args, **kwargs)` - Re-export wrapper
5. `parse_parent_training_id(*args, **kwargs)` - Re-export wrapper
6. `validate_naming_policy(*args, **kwargs)` - Re-export wrapper
7. `normalize_value(value: str, rules: Optional[Dict[str, Any]] = None) -> str`
8. `sanitize_semantic_suffix(*args, **kwargs)` - Re-export wrapper
9. `extract_component(*args, **kwargs)` - Re-export wrapper

**Note**: This is a compatibility layer that delegates to orchestration module. Should be removed after consolidation.

**Dependencies**:
- `orchestration.jobs.tracking.naming.policy` (circular dependency!)

**Exports**: All functions re-exported

---

### 2.6 Module: `src/infrastructure/naming/mlflow/tags.py`

**Purpose**: Build MLflow tag dictionaries from naming contexts

**Functions**:
1. `get_tag_key(section: str, name: str, config_dir: Optional[Path] = None) -> str`
   - Gets tag key from registry
   - **Call sites**: 10+ locations
2. `sanitize_tag_value(value: str, max_length: int = 250, config_dir: Optional[Path] = None) -> str`
   - Sanitizes tag values for MLflow
   - **Call sites**: 15+ locations
3. `build_mlflow_tags(context: NamingContext, output_dir: Optional[Path] = None, parent_run_id: Optional[str] = None, config_dir: Optional[Path] = None, ...) -> Dict[str, str]`
   - Builds complete MLflow tag dictionary
   - **Call sites**: 40+ locations

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)
- `infrastructure.naming.mlflow.tags_registry` (load_tags_registry)
- `infrastructure.naming.mlflow.tag_keys` (various get_* functions)
- `infrastructure.naming.mlflow.run_keys` (build_mlflow_run_key_hash)
- `infrastructure.naming.mlflow.config` (get_naming_config)

**Exports**: `get_tag_key`, `sanitize_tag_value`, `build_mlflow_tags`

---

### 2.7 Module: `src/infrastructure/naming/mlflow/run_keys.py`

**Purpose**: Build stable run_key identifiers and hashes

**Functions**:
1. `build_mlflow_run_key(context: NamingContext) -> str`
   - Builds stable run key string
   - **Call sites**: 20+ locations
2. `build_mlflow_run_key_hash(run_key: str) -> str`
   - Computes hash of run key
   - **Call sites**: 25+ locations
3. `build_counter_key(project_name: str, process_type: str, run_key_hash: str, env: str) -> str`
   - Builds counter key for auto-increment
   - **Call sites**: 8+ locations

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)
- `hashlib` (for hashing)

**Exports**: `build_mlflow_run_key`, `build_mlflow_run_key_hash`, `build_counter_key`

---

### 2.8 Module: `src/infrastructure/naming/mlflow/hpo_keys.py`

**Purpose**: Build HPO-specific keys (study, trial, family)

**Functions**:
1. `build_hpo_study_key(data_config: Dict, hpo_config: Dict, model: str, benchmark_config: Optional[Dict] = None) -> str`
   - Builds study key (v1)
   - **Call sites**: 10+ locations
2. `build_hpo_study_key_hash(study_key: str) -> str`
   - Computes study key hash
   - **Call sites**: 15+ locations
3. `build_hpo_study_family_key(data_config: Dict, hpo_config: Dict, benchmark_config: Optional[Dict] = None) -> str`
   - Builds study family key
   - **Call sites**: 5+ locations
4. `build_hpo_study_family_hash(study_family_key: str) -> str`
   - Computes family hash
   - **Call sites**: 5+ locations
5. `build_hpo_trial_key(study_key_hash: str, hyperparameters: Dict[str, Any]) -> str`
   - Builds trial key
   - **Call sites**: 12+ locations
6. `build_hpo_trial_key_hash(trial_key: str) -> str`
   - Computes trial key hash
   - **Call sites**: 15+ locations
7. `build_hpo_study_key_v2(data_config: Dict, hpo_config: Dict, train_config: Dict, model: str, config_dir: Path) -> str`
   - Builds study key (v2 with fingerprints)
   - **Call sites**: 8+ locations
8. `compute_data_fingerprint(data_config: Dict[str, Any]) -> str`
9. `compute_eval_fingerprint(eval_config: Dict[str, Any]) -> str`
10. `_normalize_hyperparameters(params: Dict[str, Any]) -> Dict[str, Any]` (private)

**Dependencies**:
- `json`, `hashlib` (for hashing)
- `infrastructure.naming.mlflow.refit_keys` (compute_refit_protocol_fp)

**Exports**: All build_* and compute_* functions

---

### 2.9 Module: `src/infrastructure/naming/mlflow/tag_keys.py`

**Purpose**: Provide centralized tag key definitions

**Functions**: 30+ getter functions for tag keys:
- `get_study_key_hash(config_dir: Optional[Path] = None) -> str`
- `get_trial_key_hash(config_dir: Optional[Path] = None) -> str`
- `get_parent_run_id(config_dir: Optional[Path] = None) -> str`
- ... (30+ more)

**Dependencies**:
- `infrastructure.naming.mlflow.tags_registry` (TagsRegistry, load_tags_registry)

**Exports**: All get_* functions

---

### 2.10 Module: `src/infrastructure/naming/mlflow/tags_registry.py`

**Purpose**: Manage centralized MLflow tag key registry

**Classes**:
1. `TagsRegistry` - Registry class for tag keys
2. `TagKeyError(KeyError)` - Exception for missing tag keys

**Functions**:
1. `load_tags_registry(config_dir: Optional[Path] = None) -> TagsRegistry`
   - Loads tags.yaml with caching
   - **Call sites**: 20+ locations
2. `_get_default_tag_keys() -> Dict[str, Any]` (private)

**Dependencies**:
- `common.shared.yaml_utils`
- `common.shared.file_utils`

**Exports**: `TagsRegistry`, `TagKeyError`, `load_tags_registry`

---

### 2.11 Module: `src/infrastructure/naming/mlflow/config.py`

**Purpose**: Load MLflow configuration from YAML with caching

**Functions**:
1. `load_mlflow_config(config_dir: Optional[Path] = None) -> Dict[str, Any]`
   - Loads mlflow.yaml with caching
   - **Call sites**: 10+ locations
2. `get_naming_config(config_dir: Optional[Path] = None) -> Dict[str, Any]`
   - Gets naming section from config
   - **Call sites**: 15+ locations
3. `get_index_config(config_dir: Optional[Path] = None) -> Dict[str, Any]`
4. `get_run_finder_config(config_dir: Optional[Path] = None) -> Dict[str, Any]`
5. `get_auto_increment_config(config_dir: Optional[Path] = None, process_type: str = "hpo") -> Dict[str, Any]`
   - Gets auto-increment config
   - **Call sites**: 8+ locations
6. `get_tracking_config(config_dir: Optional[Path] = None, stage: Optional[str] = None) -> Dict[str, Any]`
7. Various `_validate_*_config()` private functions

**Dependencies**:
- `common.shared.yaml_utils`
- `common.shared.file_utils`

**Exports**: All get_* and load_* functions

---

### 2.12 Module: `src/infrastructure/naming/mlflow/refit_keys.py`

**Purpose**: Compute refit protocol fingerprints

**Functions**:
1. `compute_refit_protocol_fp(data_config: Dict, train_config: Dict, eval_config: Optional[Dict] = None) -> str`
   - Computes refit protocol fingerprint
   - **Call sites**: 5+ locations

**Dependencies**: `json`, `hashlib`

**Exports**: `compute_refit_protocol_fp`

---

### 2.13 Module: `src/infrastructure/naming/experiments.py`

**Purpose**: Build experiment and stage names

**Functions**:
1. `get_stage_config(experiment_cfg: Union[dict, Any], stage: str) -> Dict[str, Any]`
2. `build_aml_experiment_name(experiment_name: str, stage: str, backbone: str) -> str`
3. `build_mlflow_experiment_name(experiment_name: str, stage: str, backbone: str) -> str`

**Dependencies**: None

**Exports**: All functions

---

## 3. Orchestration Naming (Duplicate/Compatibility Layer)

### 3.1 Module: `src/orchestration/jobs/tracking/naming/run_names.py`

**Purpose**: **DUPLICATE** of `infrastructure.naming.mlflow.run_names`

**Functions**:
1. `build_mlflow_run_name(...)` - **IDENTICAL** to infrastructure version (242 lines)
2. `_build_legacy_run_name(...)` - **IDENTICAL** to infrastructure version
3. `_short(...)` - **IDENTICAL**
4. `_strip_env_prefix(...)` - **IDENTICAL**

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)
- `orchestration.jobs.tracking.config.loader` (get_naming_config, get_auto_increment_config)
- `infrastructure.naming.mlflow.run_keys` (build_mlflow_run_key, etc.)
- `orchestration.jobs.tracking.naming.policy` (load_naming_policy, format_run_name)

**Issue**: Complete duplicate implementation. Should be replaced with re-export.

**Call sites**: 5+ locations (should migrate to infrastructure version)

---

### 3.2 Module: `src/orchestration/jobs/tracking/naming/policy.py`

**Purpose**: **DUPLICATE** of `infrastructure.naming.display_policy`

**Functions**:
1. `load_naming_policy(config_dir: Optional[Path] = None) -> Dict[str, Any]`
   - **DIFFERENT** caching strategy (module-level cache vs mtime-based)
   - **Call sites**: 10+ locations
2. `format_run_name(...)` - **SIMILAR** but may have differences
3. `validate_naming_policy(...)` - **SIMILAR**
4. `validate_run_name(...)` - **SIMILAR**
5. `parse_parent_training_id(...)` - **SIMILAR**
6. `sanitize_semantic_suffix(...)` - **UNIQUE** to this module
7. `extract_component(...)` - **SIMILAR**

**Dependencies**:
- `infrastructure.naming.context` (NamingContext)
- `core.normalize`, `core.placeholders`, `core.tokens`
- `common.shared.yaml_utils`

**Issue**: Duplicate implementation with different caching. Should consolidate to infrastructure version.

**Call sites**: 15+ locations (should migrate to infrastructure version)

---

### 3.3 Module: `src/orchestration/jobs/tracking/naming/tags.py`

**Purpose**: **DUPLICATE** of `infrastructure.naming.mlflow.tags`

**Functions**:
1. `get_tag_key(...)` - **SIMILAR**
2. `sanitize_tag_value(...)` - **SIMILAR**
3. `build_mlflow_tags(...)` - **SIMILAR**

**Issue**: Duplicate implementation. Should consolidate to infrastructure version.

---

## 4. Call Site Analysis

### 4.1 `build_mlflow_run_name` Call Sites

**Infrastructure version** (`infrastructure.naming.mlflow.run_names`):
- 31+ call sites across:
  - `training/execution/run_names.py`
  - `training/hpo/execution/local/refit.py`
  - `training/hpo/execution/local/cv.py`
  - `training/hpo/tracking/runs.py`
  - `training/hpo/tracking/setup.py`
  - `training/execution/executor.py`
  - `evaluation/benchmarking/utils.py`
  - `deployment/conversion/orchestration.py`
  - And more...

**Orchestration version** (`orchestration.jobs.tracking.naming.run_names`):
- 5+ call sites (should migrate)

**Total**: 36+ call sites

---

### 4.2 `format_run_name` Call Sites

**Infrastructure version** (`infrastructure.naming.display_policy`):
- 10+ call sites

**Orchestration version** (`orchestration.jobs.tracking.naming.policy`):
- 5+ call sites (should migrate)

**Total**: 15+ call sites

---

### 4.3 `load_naming_policy` Call Sites

**Infrastructure version** (`infrastructure.naming.display_policy`):
- 15+ call sites

**Orchestration version** (`orchestration.jobs.tracking.naming.policy`):
- 10+ call sites (should migrate)

**Total**: 25+ call sites

---

### 4.4 `infer_config_dir` / `infer_config_dir_from_path` Call Sites

**Location**: `src/infrastructure/tracking/mlflow/utils.py`

**Call sites**: 37+ locations across:
- `training/hpo/tracking/setup.py` (3 locations)
- `training/hpo/execution/local/sweep.py` (2 locations)
- `training/hpo/execution/local/cv.py` (1 location)
- `infrastructure/tracking/mlflow/trackers/sweep_tracker.py` (8 locations)
- `infrastructure/tracking/mlflow/trackers/training_tracker.py` (2 locations)
- `infrastructure/tracking/mlflow/trackers/benchmark_tracker.py` (2 locations)
- `infrastructure/tracking/mlflow/trackers/conversion_tracker.py` (1 location)
- `training/execution/run_names.py` (1 location)
- `training/hpo/tracking/cleanup.py` (1 location)
- And more...

**Hardcoded patterns** (`Path.cwd() / "config"`):
- 20+ locations with hardcoded inference
- Should all use `infer_config_dir()` instead

---

### 4.5 `find_project_root` Call Sites

**Location**: `src/infrastructure/paths/utils.py`

**Call sites**: 12+ locations:
- `training/hpo/execution/local/refit.py`
- `orchestration/jobs/hpo/local/trial/execution.py`
- And more...

**Manual implementations**: 5+ locations with manual root finding logic

---

## 5. Dependency Graph

```
infrastructure.naming.mlflow.run_names
├── infrastructure.naming.context (NamingContext)
├── infrastructure.naming.display_policy (load_naming_policy, format_run_name)
├── infrastructure.naming.mlflow.run_keys (build_mlflow_run_key, etc.)
├── infrastructure.naming.mlflow.config (get_naming_config, get_auto_increment_config)
└── orchestration.jobs.tracking.index.version_counter (reserve_run_name_version)

infrastructure.naming.display_policy
├── core.normalize
├── core.placeholders
├── core.tokens
├── infrastructure.naming.context (NamingContext)
├── infrastructure.naming.context_tokens (build_token_values)
└── orchestration.jobs.tracking.naming.policy (sanitize_semantic_suffix) [CIRCULAR!]

orchestration.jobs.tracking.naming.run_names
├── infrastructure.naming.context (NamingContext)
├── orchestration.jobs.tracking.config.loader (get_naming_config)
├── infrastructure.naming.mlflow.run_keys
└── orchestration.jobs.tracking.naming.policy (load_naming_policy, format_run_name)

orchestration.jobs.tracking.naming.policy
├── infrastructure.naming.context (NamingContext)
├── core.normalize
├── core.placeholders
└── core.tokens

infrastructure.paths.utils
└── common.shared.logging_utils

infrastructure.tracking.mlflow.utils (infer_config_dir_from_path)
└── (no dependencies, but should use paths.utils.find_project_root)
```

**Circular Dependencies Identified**:
1. `infrastructure.naming.display_policy` → `orchestration.jobs.tracking.naming.policy` (sanitize_semantic_suffix)
2. `infrastructure.naming.mlflow.policy` → `orchestration.jobs.tracking.naming.policy` (all functions)

---

## 6. Import Patterns

### 6.1 Infrastructure Naming Imports

**Pattern**: `from infrastructure.naming.mlflow.run_names import build_mlflow_run_name`
- Used in: 25+ files

**Pattern**: `from infrastructure.naming import create_naming_context`
- Used in: 30+ files

**Pattern**: `from infrastructure.naming.display_policy import load_naming_policy`
- Used in: 10+ files

### 6.2 Orchestration Naming Imports

**Pattern**: `from orchestration.jobs.tracking.naming import build_mlflow_run_name`
- Used in: 5+ files (should migrate)

**Pattern**: `from orchestration.jobs.tracking.naming.policy import load_naming_policy`
- Used in: 10+ files (should migrate)

### 6.3 Path Imports

**Pattern**: `from infrastructure.paths import find_project_root`
- Used in: 8+ files

**Pattern**: `from infrastructure.paths import build_output_path`
- Used in: 20+ files

**Pattern**: `from infrastructure.tracking.mlflow.utils import infer_config_dir_from_path`
- Used in: 37+ files (should migrate to paths.utils)

---

## 7. Redundant Inference Patterns

### 7.1 Hardcoded `Path.cwd() / "config"`

**Locations**: 20+ files with pattern:
```python
config_dir = Path.cwd() / "config"
```

**Files**:
- `training/orchestrator.py`
- `training/execution/subprocess_runner.py`
- `evaluation/selection/trial_finder.py`
- `infrastructure/naming/display_policy.py`
- `orchestration/jobs/tracking/naming/policy.py`
- And 15+ more...

**Should use**: `infer_config_dir()` from `paths.utils`

---

### 7.2 Manual Root Directory Finding

**Pattern**: Walk up from output_dir to find "outputs"
```python
current = output_dir
while current.name != "outputs" and current.parent != current:
    current = current.parent
root_dir = current.parent if current.name == "outputs" else ...
```

**Locations**: 10+ files:
- `training/hpo/tracking/setup.py`
- `training/hpo/execution/local/cv.py`
- `infrastructure/naming/mlflow/run_names.py`
- `orchestration/jobs/tracking/naming/run_names.py`
- And more...

**Should use**: `find_project_root()` or `infer_root_dir()` from `paths.utils`

---

### 7.3 Redundant `config_dir` Inference

**Pattern**: Function accepts `config_dir` but re-infers it if None
```python
def some_function(..., config_dir: Optional[Path] = None):
    if config_dir is None:
        config_dir = Path.cwd() / "config"  # or infer_config_dir_from_path(...)
```

**Locations**: 15+ functions

**Issue**: Callers often have `config_dir` but don't pass it, causing redundant inference

---

## 8. Summary Statistics

| Metric | Count |
|--------|-------|
| Path utility modules | 7 |
| Naming utility modules | 14 |
| Total functions in path domain | 24 |
| Total functions in naming domain | 88+ |
| Duplicate implementations | 3 major |
| `build_mlflow_run_name` call sites | 36+ |
| `format_run_name` call sites | 15+ |
| `load_naming_policy` call sites | 25+ |
| `infer_config_dir` call sites | 37+ |
| `find_project_root` call sites | 12+ |
| Hardcoded `Path.cwd() / "config"` | 20+ |
| Manual root finding patterns | 10+ |
| Circular dependencies | 2 |

---

## 9. Next Steps

Based on this audit, the consolidation plan should:

1. **Eliminate duplicate `build_mlflow_run_name`** - Replace orchestration version with re-export
2. **Eliminate duplicate `format_run_name`** - Consolidate to infrastructure version
3. **Eliminate duplicate `load_naming_policy`** - Use infrastructure version with mtime caching
4. **Move `infer_config_dir_from_path` to `paths.utils`** - Better location, rename to `infer_config_dir`
5. **Consolidate root finding logic** - Single `find_project_root()` function
6. **Update all call sites** - Migrate from orchestration to infrastructure modules
7. **Remove circular dependencies** - Move `sanitize_semantic_suffix` to infrastructure
8. **Replace hardcoded patterns** - Use utility functions consistently

---

**End of Audit Document**


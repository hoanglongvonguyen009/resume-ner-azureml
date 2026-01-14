# DRY Violations Analysis: Caching-Related Scripts

## Files with "caching" tag

### 1. `src/evaluation/selection/cache.py`
- **Tag**: `caching`
- **Type**: utility
- **Purpose**: Cache management for best model selection

## Files implementing caching (without explicit "caching" tag)

### 2. `src/infrastructure/paths/config.py`
- **Tags**: `utility`, `paths`, `config`
- **Caching**: Module-level mtime-based cache

### 3. `src/infrastructure/naming/mlflow/config.py`
- **Tags**: `utility`, `naming`, `mlflow`, `config`
- **Caching**: Module-level path-based cache

### 4. `src/infrastructure/naming/mlflow/tags_registry.py`
- **Tags**: `utility`, `naming`, `mlflow`, `tags`
- **Caching**: Module-level path-based cache

### 5. `src/infrastructure/naming/display_policy.py`
- **Tags**: `utility`, `naming`, `policy`
- **Caching**: Module-level mtime-based cache

### 6. `src/orchestration/jobs/tracking/naming/tags_registry.py`
- **Caching**: Module-level path-based cache
- **Note**: No metadata block found

### 7. `src/orchestration/jobs/tracking/config/loader.py`
- **Caching**: Module-level cache

### 8. `src/orchestration/jobs/tracking/naming/policy.py`
- **Caching**: Module-level path-based cache

---

## DRY Violations Identified

### 🔴 **Critical: Duplicate `tags_registry.py` Files**

**Violation**: Two nearly identical implementations of tags registry:

1. `src/infrastructure/naming/mlflow/tags_registry.py` (258 lines)
2. `src/orchestration/jobs/tracking/naming/tags_registry.py` (243 lines)

**Duplicated Code**:
- `TagsRegistry` dataclass (identical)
- `TagKeyError` exception (identical)
- `_get_default_tag_keys()` function (identical - 73 lines)
- `_deep_merge()` function (identical - 18 lines)
- `load_tags_registry()` function (nearly identical - 64 lines)

**Impact**: High - ~200+ lines of duplicated code

**Recommendation**: 
- Consolidate into a single implementation in `infrastructure/naming/mlflow/tags_registry.py`
- Update imports in `orchestration/jobs/tracking/naming/` to use the shared module
- **Usage**: Only 2 files import from orchestration version:
  - `orchestration/jobs/tracking/naming/tag_keys.py`
  - `orchestration/jobs/tracking/naming/tags.py`
- **Impact**: Low risk - easy to refactor (just update 2 import statements)

---

### 🟡 **High: Duplicate mtime Helper Functions**

**Violation**: Three identical implementations of mtime retrieval:

1. `src/infrastructure/paths/config.py`:
```python
def _get_config_mtime(config_path: Path) -> float:
    """Get modification time of config file, or 0 if doesn't exist."""
    try:
        return config_path.stat().st_mtime
    except (OSError, FileNotFoundError):
        return 0.0
```

2. `src/infrastructure/naming/mlflow/config.py`:
```python
def _get_config_mtime(config_path: Path) -> float:
    """Get modification time of config file, or 0 if doesn't exist."""
    try:
        return config_path.stat().st_mtime
    except (OSError, FileNotFoundError):
        return 0.0
```

3. `src/infrastructure/naming/display_policy.py`:
```python
def _get_policy_mtime(policy_path: Path) -> float:
    """Get modification time of policy file, or 0 if doesn't exist."""
    try:
        return policy_path.stat().st_mtime
    except (OSError, FileNotFoundError):
        return 0.0
```

**Impact**: Medium - 3 identical functions

**Recommendation**:
- Extract to `common/shared/file_utils.py` or similar
- Function name: `get_file_mtime(path: Path) -> float`

---

### 🟡 **High: Duplicate `_deep_merge()` Function**

**Violation**: Identical `_deep_merge()` implementation in both tags_registry files:

1. `src/infrastructure/naming/mlflow/tags_registry.py` (lines 174-191)
2. `src/orchestration/jobs/tracking/naming/tags_registry.py` (lines 153-170)

**Code**:
```python
def _deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries, with overrides taking precedence.
    """
    result = defaults.copy()
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
```

**Impact**: Medium - 18 lines duplicated

**Recommendation**:
- Extract to `common/shared/dict_utils.py` or similar
- Reuse in both locations

---

### 🟠 **Medium: Similar Caching Patterns**

**Violation**: Multiple files implement similar mtime-based caching with slight variations:

**Pattern 1: mtime-based cache (dict with tuple keys)**
- `src/infrastructure/paths/config.py`:
  - Cache: `_config_cache: Dict[tuple, tuple] = {}`  # (key, mtime) -> config
  - Key: `(str(config_dir), storage_env or "")`
  - Value: `(mtime, config)`

- `src/infrastructure/naming/display_policy.py`:
  - Cache: `_policy_cache: Dict[tuple, tuple] = {}`  # (key, mtime) -> policy
  - Key: `str(config_dir)`
  - Value: `(mtime, policy)`

**Pattern 2: Path-based cache (global variables)**
- `src/infrastructure/naming/mlflow/config.py`:
  - Cache: `_config_cache: Optional[Dict[str, Any]] = None`
  - Path: `_config_cache_path: Optional[Path] = None`

- `src/infrastructure/naming/mlflow/tags_registry.py`:
  - Cache: `_registry_cache: Optional[TagsRegistry] = None`
  - Path: `_registry_cache_path: Optional[Path] = None`

- `src/orchestration/jobs/tracking/naming/tags_registry.py`:
  - Cache: `_registry_cache: Optional[TagsRegistry] = None`
  - Path: `_registry_cache_path: Optional[Path] = None`

**Impact**: Medium - Similar patterns but different implementations

**Recommendation**:
- Consider creating a generic caching utility:
  - `common/shared/config_cache.py` with decorators or context managers
  - Support both mtime-based and path-based invalidation
  - Example: `@cached_config(mtime_based=True)` or `@cached_config(path_based=True)`

---

### 🟢 **Low: Inconsistent Cache Invalidation Logic**

**Violation**: Different approaches to cache invalidation:

1. **mtime-based**: Check file modification time, invalidate if changed
2. **path-based**: Check if path changed, no mtime check
3. **No invalidation**: Some caches never invalidate (only check path)

**Impact**: Low - Functional but inconsistent

**Recommendation**:
- Standardize on mtime-based invalidation for config files
- Document caching strategy in shared utility

---

## Summary Statistics

- **Total files analyzed**: 8
- **Files with "caching" tag**: 1
- **Critical violations**: 1 (duplicate tags_registry files)
- **High violations**: 2 (mtime helpers, deep_merge)
- **Medium violations**: 1 (caching patterns)
- **Low violations**: 1 (invalidation logic)

## Recommended Actions

1. **Immediate**: Consolidate duplicate `tags_registry.py` files
2. **High Priority**: Extract `_get_config_mtime()` to shared utility
3. **High Priority**: Extract `_deep_merge()` to shared utility
4. **Medium Priority**: Create generic config caching utility
5. **Low Priority**: Standardize cache invalidation strategy

## Estimated Refactoring Impact

- **Lines of code to remove**: ~250+ (duplicates)
- **New shared utilities**: ~100-150 lines
- **Net reduction**: ~100-150 lines
- **Maintainability**: Significantly improved


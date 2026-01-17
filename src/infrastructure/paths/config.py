"""
@meta
name: paths_config
type: utility
domain: paths
responsibility:
  - Load and manage paths.yaml configuration with caching
  - Apply environment-specific overrides
inputs:
  - Configuration directories
  - Storage environment identifiers
outputs:
  - Paths configuration dictionaries
tags:
  - utility
  - paths
  - config
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Load and manage paths.yaml configuration with caching."""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from core.placeholders import extract_placeholders
from core.tokens import is_token_allowed, is_token_known
from common.shared.yaml_utils import load_yaml
from common.shared.file_utils import get_file_mtime

logger = logging.getLogger(__name__)

# Cache for loaded configs: (config_dir, storage_env, mtime) -> config
_config_cache: Dict[tuple, tuple] = {}  # (key, mtime) -> config


def load_paths_config(config_dir: Path, storage_env: Optional[str] = None) -> Dict[str, Any]:
    """
    Load paths configuration from config/paths.yaml with caching.

    Cache is invalidated when the file modification time changes.

    Args:
        config_dir: Configuration directory (ROOT_DIR / "config").
        storage_env: Optional storage environment for cache key (used for env_overrides).

    Returns:
        Dictionary containing paths configuration, or defaults if file doesn't exist.
    """
    paths_config_path = config_dir / "paths.yaml"
    mtime = get_file_mtime(paths_config_path)
    
    # Create cache key
    cache_key = (str(config_dir), storage_env or "")
    
    # Check cache
    if cache_key in _config_cache:
        cached_mtime, cached_config = _config_cache[cache_key]
        if cached_mtime == mtime:
            return cached_config
        # Cache invalid, remove it
        del _config_cache[cache_key]
    
    # Load config
    if paths_config_path.exists():
        config = load_yaml(paths_config_path)
        try:
            validate_paths_config(config, paths_config_path)
        except Exception as e:
            raise RuntimeError(
                f"Invalid paths configuration in {paths_config_path}: {e}"
            ) from e
    else:
        # Return defaults if config doesn't exist (backward compatibility)
        config = _get_default_paths()
    
    # Apply env overrides if storage_env provided
    if storage_env:
        config = apply_env_overrides(config, storage_env)
    
    # Cache the result
    _config_cache[cache_key] = (mtime, config)
    
    return config


def apply_env_overrides(
    paths_config: Dict[str, Any], storage_env: Optional[str]
) -> Dict[str, Any]:
    """
    Apply shallow env overrides (keyed by storage_env) to a paths config.

    Only whitelisted sections are merged (currently: base, outputs).
    Does not mutate the original config; returns a merged copy.
    """
    if not storage_env:
        return paths_config

    overrides = paths_config.get("env_overrides", {}).get(storage_env)
    if not overrides:
        return paths_config

    merged = dict(paths_config)

    if "base" in overrides and isinstance(overrides["base"], dict):
        merged_base = dict(paths_config.get("base", {}))
        merged_base.update(overrides["base"])
        merged["base"] = merged_base

    if "outputs" in overrides and isinstance(overrides["outputs"], dict):
        merged_outputs = dict(paths_config.get("outputs", {}))
        merged_outputs.update(overrides["outputs"])
        merged["outputs"] = merged_outputs

    return merged


def validate_paths_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Basic schema validation for paths.yaml.

    - v1 (no or schema_version=1): minimal checks.
    - v2 and above: fail fast on core keys and required patterns.
    """
    location = f" ({config_path})" if config_path is not None else ""
    schema_version_raw = config.get("schema_version", 1)

    try:
        schema_version = int(schema_version_raw)
    except (TypeError, ValueError):
        raise ValueError(
            f"schema_version must be an integer, got {schema_version_raw!r}{location}"
        )

    if schema_version < 1:
        logger.warning(
            f"[paths.yaml] Unsupported schema_version={schema_version}{location}, "
            f"treating as v1 with minimal validation."
        )
        schema_version = 1

    # Core requirement: base.outputs must exist and be non-empty
    base = config.get("base")
    if not isinstance(base, dict):
        raise ValueError(
            f"[paths.yaml] 'base' section must be a mapping{location}")
    outputs_base = base.get("outputs")
    if not outputs_base or not isinstance(outputs_base, str):
        raise ValueError(
            f"[paths.yaml] 'base.outputs' must be a non-empty string{location}"
        )

    # v1: lenient beyond this
    if schema_version == 1:
        return

    # v2+: stricter checks for patterns
    patterns = config.get("patterns")
    if not isinstance(patterns, dict):
        raise ValueError(
            f"[paths.yaml] 'patterns' section must be a mapping for schema_version>=2{location}"
        )

    # Required pattern keys for schema v2 (matches PROCESS_PATTERN_KEYS in resolve.py)
    # Note: We define this here to avoid circular import with resolve.py
    required_pattern_keys = [
        "final_training_v2",
        "conversion_v2",
        "best_config_v2",
        "hpo_v2",
        "benchmarking_v2",
    ]
    
    missing = [key for key in required_pattern_keys if key not in patterns]
    if missing:
        raise ValueError(
            f"[paths.yaml] Missing required pattern keys for schema_version>=2{location}: "
            f"{', '.join(missing)}"
        )

    # Validate placeholders for all string patterns (cache + v2)
    for pattern_name, pattern_value in patterns.items():
        if not isinstance(pattern_value, str):
            continue
        placeholders = extract_placeholders(pattern_value)
        for token in placeholders:
            if not is_token_known(token):
                if schema_version >= 2:
                    raise ValueError(
                        f"[paths.yaml] Unknown placeholder '{{{token}}}' in pattern '{pattern_name}'{location}"
                    )
                logger.warning(
                    f"[paths.yaml] Unknown placeholder '{{{token}}}' in pattern '{pattern_name}'{location}"
                )
                continue
            if not is_token_allowed(token, "path"):
                raise ValueError(
                    f"[paths.yaml] Placeholder '{{{token}}}' in pattern '{pattern_name}' "
                    f"is not allowed for path scope{location}"
                )


def load_repository_root_config(config_dir: Path) -> Dict[str, Any]:
    """
    Load and validate repository root detection configuration.
    
    Loads the `repository_root` section from paths.yaml and derives markers
    from the `base.*` section (single source of truth).
    
    Args:
        config_dir: Config directory path.
    
    Returns:
        Dictionary with repository root config (validated).
    
    Raises:
        FileNotFoundError: If config/paths.yaml not found.
        ValueError: If config is invalid.
    """
    paths_config = load_paths_config(config_dir)
    repo_config = paths_config.get("repository_root", {})
    
    # Get base section to derive markers
    base = paths_config.get("base", {})
    if not isinstance(base, dict):
        raise ValueError(
            f"[paths.yaml] 'base' section must be a mapping (config_dir: {config_dir})"
        )
    
    # Derive markers from base.* section
    config_marker = base.get("config", "config")
    src_marker = base.get("src", "src")
    
    # Build markers list
    required_markers = [config_marker, src_marker]
    extra_markers = repo_config.get("extra_markers", [".git", "pyproject.toml"])
    
    # Validate config structure
    if not isinstance(repo_config, dict):
        raise ValueError(
            f"[paths.yaml] 'repository_root' section must be a mapping (config_dir: {config_dir})"
        )
    
    # Build validated config
    validated_config: Dict[str, Any] = {
        "markers_from_base": repo_config.get("markers_from_base", True),
        "required_markers": required_markers,
        "extra_markers": extra_markers if isinstance(extra_markers, list) else [],
        "workspace_candidates": repo_config.get("workspace_candidates", []),
        "platform_candidates": repo_config.get("platform_candidates", {}),
        "search": {
            "max_depth": repo_config.get("search", {}).get("max_depth", 10),
            "fallback_to_cwd": repo_config.get("search", {}).get("fallback_to_cwd", True),
            "warn_on_fallback": repo_config.get("search", {}).get("warn_on_fallback", True),
        },
        "cache": {
            "enabled": repo_config.get("cache", {}).get("enabled", True),
        },
    }
    
    # Validate platform candidates structure
    platform_candidates = validated_config["platform_candidates"]
    if not isinstance(platform_candidates, dict):
        raise ValueError(
            f"[paths.yaml] 'repository_root.platform_candidates' must be a mapping (config_dir: {config_dir})"
        )
    
    # Validate each platform's candidate list
    for platform, candidates in platform_candidates.items():
        if not isinstance(candidates, list):
            raise ValueError(
                f"[paths.yaml] 'repository_root.platform_candidates.{platform}' must be a list (config_dir: {config_dir})"
            )
        # Validate each candidate is a string
        for candidate in candidates:
            if not isinstance(candidate, str):
                raise ValueError(
                    f"[paths.yaml] 'repository_root.platform_candidates.{platform}' must contain strings (config_dir: {config_dir})"
                )
    
    # Validate workspace candidates
    workspace_candidates = validated_config["workspace_candidates"]
    if not isinstance(workspace_candidates, list):
        raise ValueError(
            f"[paths.yaml] 'repository_root.workspace_candidates' must be a list (config_dir: {config_dir})"
        )
    for candidate in workspace_candidates:
        if not isinstance(candidate, str):
            raise ValueError(
                f"[paths.yaml] 'repository_root.workspace_candidates' must contain strings (config_dir: {config_dir})"
            )
    
    return validated_config


def _get_default_paths() -> Dict[str, Any]:
    """Default paths (backward compatible)."""
    return {
        "base": {"outputs": "outputs"},
        "outputs": {
            "hpo": "hpo",
            "benchmarking": "benchmarking",
            "final_training": "final_training",
            "conversion": "conversion",
            "best_model_selection": "best_model_selection",
            "cache": "cache",
        },
        "cache": {
            "best_configurations": "best_configurations",
            "final_training": "final_training",
            "best_model_selection": "best_model_selection",
        },
        "files": {
            "metrics": "metrics.json",
            "benchmark": "benchmark.json",
            "checkpoint_dir": "checkpoint",
            "cache": {
                "best_config_latest": "latest_best_configuration.json",
                "best_config_index": "index.json",
                "final_training_latest": "latest_final_training_cache.json",
                "final_training_index": "final_training_index.json",
            },
        },
        "patterns": {
            "best_config_file": "best_config_{backbone}_{trial}_{timestamp}.json",
            "final_training_cache_file": "final_training_{backbone}_{run_id}_{timestamp}.json",
        },
        "cache_strategies": {
            "best_configurations": {
                "strategy": "dual",
                "timestamped": {"enabled": True},
                "latest": {"enabled": True, "filename": "latest_best_configuration.json"},
                "index": {"enabled": True, "filename": "index.json", "max_entries": 20},
            },
            "final_training": {
                "strategy": "dual",
                "timestamped": {"enabled": True},
                "latest": {"enabled": True, "filename": "latest_final_training_cache.json"},
                "index": {"enabled": True, "filename": "final_training_index.json", "max_entries": 20},
            },
        },
    }


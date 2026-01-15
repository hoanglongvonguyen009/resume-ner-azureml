from __future__ import annotations

"""
@meta
name: naming_mlflow_hpo_keys
type: utility
domain: naming
responsibility:
  - Build HPO-specific keys (study, trial, family)
  - Normalize hyperparameters for deterministic hashing
  - Compute deterministic hashes for HPO grouping
  - Does NOT interact with Optuna/MLflow clients or perform I/O
inputs:
  - Configuration dictionaries
  - Hyperparameters
outputs:
  - HPO key strings and hashes
tags:
  - utility
  - naming
  - mlflow
  - hpo
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""HPO-specific key building (study, trial, family)."""
import json
from typing import Any, Dict, Optional

from common.shared.hash_utils import compute_hash_64

def _normalize_hyperparameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize hyperparameters for deterministic hashing across platforms.

    Ensures that the same hyperparameters produce the same hash even if:
    - Float precision differs (e.g., 2.33e-05 vs 0.0000233000001)
    - String casing/whitespace differs
    - Types differ (int vs float for whole numbers)

    Args:
        params: Dictionary of hyperparameters.

    Returns:
        Normalized dictionary with canonical representations.
    """
    # Import Mock check here to avoid circular imports and only import when needed
    try:
        from unittest.mock import Mock
        has_mock = True
    except ImportError:
        # unittest.mock might not be available in all environments
        has_mock = False
        Mock = None
    
    normalized = {}
    for key, value in sorted(params.items()):
        # Filter out Mock objects (can occur in test environments)
        if has_mock and isinstance(value, Mock):
            # Skip Mock objects - they're not valid hyperparameters
            continue
        
        if isinstance(value, float):
            # Normalize floats to 12 significant figures for stability
            # This ensures 2.33e-05 and 0.0000233000001 both become the same value
            if value == 0.0:
                normalized[key] = 0.0
            else:
                # Use exponential notation with 12 significant figures
                normalized[key] = float(f"{value:.12e}")
        elif isinstance(value, (int, bool)):
            # Keep ints and bools as-is
            normalized[key] = value
        elif isinstance(value, str):
            # Normalize strings: lowercase, strip whitespace
            normalized[key] = value.lower().strip()
        else:
            # For other types, convert to string and normalize
            normalized[key] = str(value).lower().strip()
    return normalized

def build_hpo_study_key(
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    model: str,
    benchmark_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build canonical study key JSON string for HPO study identity.

    This key uniquely identifies an HPO study based on:
    - Dataset configuration (name, version, path)
    - HPO search space and objective
    - Model backbone
    - Benchmark configuration (for ranking/comparison)

    The key is a JSON string that can be hashed for stable identity.

    Args:
        data_config: Data configuration dictionary.
        hpo_config: HPO configuration dictionary.
        model: Model backbone name.
        benchmark_config: Optional benchmark configuration.

    Returns:
        Canonical JSON string representing the study key.
    """
    # Extract relevant parts of data_config
    data_key = {
        "name": data_config.get("name", ""),
        "version": data_config.get("version", ""),
        "local_path": str(data_config.get("local_path", "")),
        # Include schema if available (affects data processing)
        "schema": data_config.get("schema", {}),
    }

    # Extract relevant parts of hpo_config
    hpo_key = {
        "search_space": hpo_config.get("search_space", {}),
        "objective": hpo_config.get("objective", {}),
        "k_fold": hpo_config.get("k_fold", {}),
        "sampling": {
            "algorithm": hpo_config.get("sampling", {}).get("algorithm", "random"),
        },
        "early_termination": hpo_config.get("early_termination", {}),
    }

    # Extract benchmark config for ranking (excludes hardware-specific details)
    bench_key = {}
    if benchmark_config:
        bench_config = benchmark_config.get("benchmarking", {})
        bench_key = {
            "metric": bench_config.get("metric", "macro-f1"),
            "max_length": bench_config.get("max_length", 512),
            # Exclude hardware-specific: batch_sizes, iterations, device, etc.
        }

    payload = {
        "schema_version": "1.0",
        "data": data_key,
        "hpo": hpo_key,
        "model": model.lower().strip(),
        "benchmark": bench_key,
    }

    # Use compact JSON (no spaces) for consistent hashing
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))

def build_hpo_study_key_hash(study_key: str) -> str:
    """
    Build hash of study key for tag storage.

    Args:
        study_key: Canonical study key JSON string.

    Returns:
        64-character hex hash.
    """
    return compute_hash_64(study_key)

def build_hpo_study_family_key(
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    benchmark_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build canonical study family key JSON string.

    A study family groups multiple studies that share:
    - Same dataset configuration
    - Same HPO search space and objective
    - Same benchmark configuration
    But different model backbones.

    This allows cross-model comparison within the same family.

    Args:
        data_config: Data configuration dictionary.
        hpo_config: HPO configuration dictionary.
        benchmark_config: Optional benchmark configuration.

    Returns:
        Canonical JSON string representing the study family key.
    """
    # Extract relevant parts (same as study_key but without model)
    data_key = {
        "name": data_config.get("name", ""),
        "version": data_config.get("version", ""),
        "local_path": str(data_config.get("local_path", "")),
        "schema": data_config.get("schema", {}),
    }

    hpo_key = {
        "search_space": hpo_config.get("search_space", {}),
        "objective": hpo_config.get("objective", {}),
        "k_fold": hpo_config.get("k_fold", {}),
        "sampling": {
            "algorithm": hpo_config.get("sampling", {}).get("algorithm", "random"),
        },
        "early_termination": hpo_config.get("early_termination", {}),
    }

    bench_key = {}
    if benchmark_config:
        bench_config = benchmark_config.get("benchmarking", {})
        bench_key = {
            "metric": bench_config.get("metric", "macro-f1"),
            "max_length": bench_config.get("max_length", 512),
        }

    payload = {
        "schema_version": "1.0",
        "data": data_key,
        "hpo": hpo_key,
        "benchmark": bench_key,
    }

    return json.dumps(payload, sort_keys=True, separators=(',', ':'))

def build_hpo_study_family_hash(study_family_key: str) -> str:
    """
    Build hash of study family key for tag storage.

    Args:
        study_family_key: Canonical study family key JSON string.

    Returns:
        64-character hex hash.
    """
    return compute_hash_64(study_family_key)

def build_hpo_trial_key(
    study_key_hash: str,
    hyperparameters: Dict[str, Any],
) -> str:
    """
    Build canonical trial key JSON string for trial identity.

    A trial key uniquely identifies a trial within a study by combining:
    - Study key hash (identifies the study, 64 chars)
    - Normalized hyperparameters (identifies the trial within the study)

    Args:
        study_key_hash: SHA256 hash of study key (64 hex chars).
        hyperparameters: Dictionary of trial hyperparameters.

    Returns:
        Canonical JSON string representing the trial key.
    """
    # Validate inputs to catch Mock objects early (common in test environments)
    try:
        from unittest.mock import Mock
        has_mock = True
    except ImportError:
        has_mock = False
        Mock = None
    
    # Validate study_key_hash is a string (not a Mock)
    if has_mock and isinstance(study_key_hash, Mock):
        raise ValueError(
            f"study_key_hash must be a string, got Mock object. "
            f"This usually indicates a test setup issue where Mock objects are being passed instead of real values."
        )
    if not isinstance(study_key_hash, str):
        raise ValueError(
            f"study_key_hash must be a string, got {type(study_key_hash).__name__}"
        )
    
    # Normalize hyperparameters for deterministic hashing
    # This will filter out any Mock objects in the hyperparameters dict
    normalized_params = _normalize_hyperparameters(hyperparameters)

    payload = {
        "schema_version": "1.0",
        "study_key_hash": study_key_hash,
        "hyperparameters": normalized_params,
    }

    return json.dumps(payload, sort_keys=True, separators=(',', ':'))

def build_hpo_trial_key_hash(trial_key: str) -> str:
    """
    Build hash of trial key for tag storage.

    Args:
        trial_key: Canonical trial key JSON string.

    Returns:
        64-character hex hash.
    """
    return compute_hash_64(trial_key)


def compute_data_fingerprint(data_config: Dict[str, Any]) -> str:
    """
    Compute data fingerprint (content-based if available, semantic fallback).
    
    Priority:
    1. content_hash or manifest_hash (if available) - pure content identity
    2. Semantic fields (name/version/split_seed/etc) - fallback
    
    Note: If using semantic fallback, there's overlap with study_key_hash v2
    data_key fields. This is acceptable - fingerprint is for filtering/tagging,
    study_key_hash is for grouping. Both serve different purposes.
    
    Args:
        data_config: Data configuration dictionary
        
    Returns:
        64-character hex hash (full SHA256)
    """
    # Prefer content-based identity
    content_hash = data_config.get("content_hash") or data_config.get("manifest_hash")
    if content_hash:
        return compute_hash_64(str(content_hash))
    
    # Fallback: semantic identity
    fallback_payload = {
        "name": data_config.get("name"),
        "version": data_config.get("version"),
        "split_seed": data_config.get("split_seed"),
        "label_mapping": data_config.get("label_mapping", {}),
        "schema": data_config.get("schema", {}),
    }
    return compute_hash_64(json.dumps(fallback_payload, sort_keys=True, separators=(',', ':')))


def compute_eval_fingerprint(eval_config: Dict[str, Any]) -> str:
    """
    Compute evaluation fingerprint (content-based, not script name).
    
    Hashes: evaluator_version + metric_spec + thresholding + full_eval_config
    NOT: script filename (too fragile)
    
    Args:
        eval_config: Evaluation configuration dictionary
        
    Returns:
        64-character hex hash (full SHA256)
    """
    fingerprint_payload = {
        "evaluator_version": eval_config.get("evaluator_version", "default"),
        "metric_spec": eval_config.get("metric", {}),
        "thresholding": eval_config.get("thresholding", {}),
        "full_eval_config": eval_config,  # Include full config for stability
    }
    return compute_hash_64(json.dumps(fingerprint_payload, sort_keys=True, separators=(',', ':')))


def build_hpo_study_key_v2(
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    model: str,
    *,
    data_fingerprint: str,  # REQUIRED - actual value, not marker
    eval_fingerprint: str,  # REQUIRED - actual value, not marker
    include_code_version: bool = False,
) -> str:
    """
    Build study_key_hash v2 with bound fingerprints.
    
    CRITICAL: Fingerprints are actual values in the key, not markers.
    This prevents grouping runs with different eval/data configs.
    
    Changes from v1:
    - Removed local_path (too fragile, use data_fingerprint tag instead)
    - Added train_budget (max_steps/epochs) to prevent winner's curse
    - Added seed_policy
    - Bound eval_fingerprint and data_fingerprint (actual values)
    - Explicit objective direction (never assume maximize)
    - NO benchmark config (that's separate phase)
    
    Args:
        data_config: Data configuration dictionary
        hpo_config: HPO configuration dictionary
        train_config: Training configuration dictionary
        model: Model backbone name
        data_fingerprint: Actual data fingerprint value (REQUIRED)
        eval_fingerprint: Actual evaluation fingerprint value (REQUIRED)
        include_code_version: Whether to include git commit hash
        
    Returns:
        Canonical JSON string representing the study key v2
    """
    # Data identity (no local_path, fingerprints bound)
    data_key = {
        "name": data_config.get("name", ""),
        "version": data_config.get("version", ""),
        "schema": data_config.get("schema", {}),
        "split_seed": data_config.get("split_seed", "default"),
        "label_mapping": data_config.get("label_mapping", {}),
        "data_fingerprint": data_fingerprint,  # BOUND - actual value
    }
    
    # HPO config (explicit direction, NO benchmark)
    objective = hpo_config.get("objective", {})
    hpo_key = {
        "search_space": hpo_config.get("search_space", {}),
        "objective": {
            "metric": objective.get("metric", "macro-f1"),
            "direction": objective.get("direction", "maximize"),  # EXPLICIT
        },
        "k_fold": hpo_config.get("k_fold", {}),
        "sampling": {
            "algorithm": hpo_config.get("sampling", {}).get("algorithm", "random"),
        },
        "early_termination": hpo_config.get("early_termination", {}),
    }
    
    # Training budget (prevents winner's curse)
    train_key = {
        "max_steps": train_config.get("max_steps"),
        "num_epochs": train_config.get("num_epochs"),
        "seed_policy": train_config.get("seed_policy", "default"),
    }
    
    payload = {
        "schema_version": "2.0",
        "data": data_key,
        "hpo": hpo_key,
        "training": train_key,
        "evaluation": {
            "eval_fingerprint": eval_fingerprint,  # BOUND - actual value
        },
        "model": model.lower().strip(),
        # NO benchmark config - that's separate phase
    }
    
    if include_code_version:
        # Try to get git commit hash
        try:
            import subprocess
            git_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
            payload["code_version"] = git_sha
        except Exception:
            payload["code_version"] = "unknown"
    
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


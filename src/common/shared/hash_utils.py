from __future__ import annotations

"""Hash computation utilities."""

import hashlib
import json
from typing import Any, Dict, Optional


def compute_hash_64(data: str) -> str:
    """
    Compute full SHA256 hash (64 hex characters).
    
    Args:
        data: String to hash.
    
    Returns:
        64-character hex hash.
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_hash_16(data: str) -> str:
    """
    Compute truncated SHA256 hash (16 hex characters).
    
    Args:
        data: String to hash.
    
    Returns:
        16-character hex hash (first 16 chars of SHA256).
    """
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]


def compute_json_hash(data: Dict[str, Any], length: int = 64) -> str:
    """
    Compute hash of JSON-serialized dictionary.
    
    Args:
        data: Dictionary to hash.
        length: Length of hash to return (16 or 64).
    
    Returns:
        Hex hash of specified length.
    """
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'), default=str)
    hash_full = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    return hash_full[:length] if length < 64 else hash_full


def compute_selection_cache_key(
    experiment_name: str,
    selection_config: Dict[str, Any],
    tags_config: Dict[str, Any],
    benchmark_experiment_id: str,
    tracking_uri: Optional[str] = None,
) -> str:
    """
    Compute cache key for best model selection.
    
    Includes all factors that affect selection result:
    - experiment_name
    - selection_config (weights, metrics, filters)
    - tags_config (tag keys)
    - benchmark_experiment_id
    - tracking_uri (optional, for workspace isolation)
    
    Args:
        experiment_name: Name of the experiment.
        selection_config: Selection configuration dict.
        tags_config: Tags configuration dict.
        benchmark_experiment_id: MLflow experiment ID for benchmark runs.
        tracking_uri: Optional MLflow tracking URI.
    
    Returns:
        16-character hex hash.
    """
    cache_data = {
        "experiment_name": experiment_name,
        "selection_config": selection_config,
        "tags_config": tags_config,
        "benchmark_experiment_id": benchmark_experiment_id,
    }
    if tracking_uri:
        cache_data["tracking_uri"] = tracking_uri
    
    return compute_json_hash(cache_data, length=16)


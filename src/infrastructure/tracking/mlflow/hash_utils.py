from __future__ import annotations

"""
@meta
name: hash_utils
type: utility
domain: tracking
responsibility:
  - Centralized hash retrieval and computation utilities
  - Single source of truth for hash retrieval and computation
  - Retrieve hashes from tags (SSOT) or compute from configs
inputs:
  - MLflow run IDs
  - MLflow client
  - Configuration dictionaries
outputs:
  - Study and trial key hashes
tags:
  - utility
  - tracking
  - mlflow
  - hashing
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Centralized hash retrieval and computation utilities.

This module provides a single source of truth for hash retrieval and computation,
following the principle that tags are the source of truth (SSOT).

Priority order:
1. Retrieve from tags (highest priority - tags are SSOT)
2. Compute from configs (when tags don't exist)
3. Fallback (warn and continue if both fail)
"""
from pathlib import Path
from typing import Any, Dict, Optional

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def get_study_key_hash_from_run(
    run_id: str,
    mlflow_client: MlflowClient,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Retrieve study_key_hash from MLflow run tags (SSOT).
    
    Priority:
    1. code.study_key_hash
    2. code.grouping.study_key_hash (legacy)
    
    Args:
        run_id: MLflow run ID
        mlflow_client: MLflow client instance
        config_dir: Optional config directory for tag registry
        
    Returns:
        study_key_hash if found, None otherwise
    """
    try:
        run = mlflow_client.get_run(run_id)
        tags = run.data.tags
        
        # Priority 1: code.study_key_hash
        study_key_hash = tags.get("code.study_key_hash")
        if study_key_hash:
            logger.debug(f"Retrieved study_key_hash from code.study_key_hash tag: {study_key_hash[:16]}...")
            return study_key_hash
        
        # Priority 2: code.grouping.study_key_hash (legacy)
        study_key_hash = tags.get("code.grouping.study_key_hash")
        if study_key_hash:
            logger.debug(f"Retrieved study_key_hash from code.grouping.study_key_hash tag (legacy): {study_key_hash[:16]}...")
            return study_key_hash
        
        # Try tag registry if config_dir provided
        if config_dir:
            try:
                from infrastructure.naming.mlflow.tags_registry import load_tags_registry
                tags_registry = load_tags_registry(config_dir)
                study_key_tag = tags_registry.key("grouping", "study_key_hash")
                study_key_hash = tags.get(study_key_tag)
                if study_key_hash:
                    logger.debug(f"Retrieved study_key_hash from registry tag {study_key_tag}: {study_key_hash[:16]}...")
                    return study_key_hash
            except Exception as e:
                logger.debug(f"Could not use tag registry: {e}")
        
        return None
    except Exception as e:
        logger.debug(f"Could not retrieve study_key_hash from run {run_id[:12]}...: {e}")
        return None


def get_trial_key_hash_from_run(
    run_id: str,
    mlflow_client: MlflowClient,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Retrieve trial_key_hash from MLflow run tags (SSOT).
    
    Priority:
    1. code.trial_key_hash
    2. code.grouping.trial_key_hash
    
    Args:
        run_id: MLflow run ID
        mlflow_client: MLflow client instance
        config_dir: Optional config directory for tag registry
        
    Returns:
        trial_key_hash if found, None otherwise
    """
    try:
        run = mlflow_client.get_run(run_id)
        tags = run.data.tags
        
        # Priority 1: code.trial_key_hash
        trial_key_hash = tags.get("code.trial_key_hash")
        if trial_key_hash:
            logger.debug(f"Retrieved trial_key_hash from code.trial_key_hash tag: {trial_key_hash[:16]}...")
            return trial_key_hash
        
        # Priority 2: code.grouping.trial_key_hash
        trial_key_hash = tags.get("code.grouping.trial_key_hash")
        if trial_key_hash:
            logger.debug(f"Retrieved trial_key_hash from code.grouping.trial_key_hash tag: {trial_key_hash[:16]}...")
            return trial_key_hash
        
        # Try tag registry if config_dir provided
        if config_dir:
            try:
                from infrastructure.naming.mlflow.tags_registry import load_tags_registry
                tags_registry = load_tags_registry(config_dir)
                trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
                trial_key_hash = tags.get(trial_key_tag)
                if trial_key_hash:
                    logger.debug(f"Retrieved trial_key_hash from registry tag {trial_key_tag}: {trial_key_hash[:16]}...")
                    return trial_key_hash
            except Exception as e:
                logger.debug(f"Could not use tag registry: {e}")
        
        return None
    except Exception as e:
        logger.debug(f"Could not retrieve trial_key_hash from run {run_id[:12]}...: {e}")
        return None


def get_study_family_hash_from_run(
    run_id: str,
    mlflow_client: MlflowClient,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Retrieve study_family_hash from MLflow run tags (SSOT).
    
    Priority:
    1. code.study_family_hash
    2. code.grouping.study_family_hash (legacy)
    
    Args:
        run_id: MLflow run ID
        mlflow_client: MLflow client instance
        config_dir: Optional config directory for tag registry
        
    Returns:
        study_family_hash if found, None otherwise
    """
    try:
        run = mlflow_client.get_run(run_id)
        tags = run.data.tags
        
        # Priority 1: code.study_family_hash
        study_family_hash = tags.get("code.study_family_hash")
        if study_family_hash:
            logger.debug(f"Retrieved study_family_hash from code.study_family_hash tag: {study_family_hash[:16]}...")
            return study_family_hash
        
        # Priority 2: code.grouping.study_family_hash (legacy)
        study_family_hash = tags.get("code.grouping.study_family_hash")
        if study_family_hash:
            logger.debug(f"Retrieved study_family_hash from code.grouping.study_family_hash tag (legacy): {study_family_hash[:16]}...")
            return study_family_hash
        
        # Try tag registry if config_dir provided
        if config_dir:
            try:
                from infrastructure.naming.mlflow.tags_registry import load_tags_registry
                tags_registry = load_tags_registry(config_dir)
                study_family_tag = tags_registry.key("grouping", "study_family_hash")
                study_family_hash = tags.get(study_family_tag)
                if study_family_hash:
                    logger.debug(f"Retrieved study_family_hash from registry tag {study_family_tag}: {study_family_hash[:16]}...")
                    return study_family_hash
            except Exception as e:
                logger.debug(f"Could not use tag registry: {e}")
        
        return None
    except Exception as e:
        logger.debug(f"Could not retrieve study_family_hash from run {run_id[:12]}...: {e}")
        return None


def derive_eval_config(
    train_config: Optional[Dict[str, Any]],
    hpo_config: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Derive eval_config consistently across all hash computation.
    
    Priority:
    1. train_config.get("eval", {})
    2. hpo_config.get("evaluation", {})
    3. Create from hpo_config.get("objective", {}) with evaluator_version: "default"
    
    Args:
        train_config: Training configuration dictionary
        hpo_config: HPO configuration dictionary
        
    Returns:
        Non-empty dict (at minimum: {"evaluator_version": "default"}).
    """
    eval_config = {}
    
    # Priority 1: train_config.get("eval", {})
    if train_config:
        eval_config = train_config.get("eval", {}) or {}
    
    # Priority 2: hpo_config.get("evaluation", {})
    if not eval_config and hpo_config:
        eval_config = hpo_config.get("evaluation", {}) or {}
    
    # Priority 3: Create from objective
    if not eval_config and hpo_config:
        objective = hpo_config.get("objective", {})
        eval_config = {
            "evaluator_version": "default",
            "metric": objective,
        }
    
    # Ensure at minimum we have evaluator_version
    if not eval_config:
        eval_config = {"evaluator_version": "default"}
    
    return eval_config


def compute_study_key_hash_v2(
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    train_config: Dict[str, Any],
    model: str,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Compute v2 study_key_hash from configs (when tags unavailable).
    
    Args:
        data_config: Data configuration dictionary
        hpo_config: HPO configuration dictionary
        train_config: Training configuration dictionary
        model: Model backbone name
        config_dir: Optional config directory
        
    Returns:
        study_key_hash if computation succeeds, None otherwise
    """
    try:
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_study_key_v2,
            build_hpo_study_key_hash,
            compute_data_fingerprint,
            compute_eval_fingerprint,
        )
        
        # Always compute fingerprints (they handle empty dicts)
        data_fp = compute_data_fingerprint(data_config or {})
        
        # Derive eval_config consistently
        eval_config = derive_eval_config(train_config, hpo_config)
        eval_fp = compute_eval_fingerprint(eval_config)
        
        # Only build v2 if both fingerprints are available
        if data_fp and eval_fp:
            study_key_v2 = build_hpo_study_key_v2(
                data_config=data_config,
                hpo_config=hpo_config,
                train_config=train_config,
                model=model,
                data_fingerprint=data_fp,
                eval_fingerprint=eval_fp,
            )
            study_key_hash = build_hpo_study_key_hash(study_key_v2)
            logger.debug(f"Computed v2 study_key_hash from configs: {study_key_hash[:16]}...")
            return study_key_hash
        
        logger.warning(
            f"Cannot compute v2 study_key_hash - missing fingerprints: "
            f"data_fp={'present' if data_fp else 'missing'}, "
            f"eval_fp={'present' if eval_fp else 'missing'}"
        )
        return None
    except Exception as e:
        logger.warning(f"Could not compute v2 study_key_hash: {e}", exc_info=True)
        return None


def compute_trial_key_hash_from_trial_run(
    trial_run_id: str,
    mlflow_client: MlflowClient,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Get trial_key_hash from trial run tags (SSOT for refit runs).
    
    This is the primary way refit runs should get their trial_key_hash.
    
    Args:
        trial_run_id: Trial run ID
        mlflow_client: MLflow client instance
        config_dir: Optional config directory
        
    Returns:
        trial_key_hash if found, None otherwise
    """
    return get_trial_key_hash_from_run(trial_run_id, mlflow_client, config_dir)


def compute_trial_key_hash_from_configs(
    study_key_hash: str,
    hyperparameters: Dict[str, Any],
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Compute trial_key_hash from study_key_hash + hyperparameters (fallback only).
    
    Only use when trial run tags are unavailable.
    
    Args:
        study_key_hash: Study key hash
        hyperparameters: Dictionary of hyperparameters (will be normalized)
        config_dir: Optional config directory
        
    Returns:
        trial_key_hash if computation succeeds, None otherwise
    """
    try:
        from infrastructure.naming.mlflow.hpo_keys import (
            build_hpo_trial_key,
            build_hpo_trial_key_hash,
        )
        
        # Normalize hyperparameters (exclude metadata fields)
        normalized_hyperparameters = {
            k: v for k, v in hyperparameters.items()
            if k not in ("backbone", "trial_number", "run_id")
        }
        
        trial_key = build_hpo_trial_key(study_key_hash, normalized_hyperparameters)
        trial_key_hash = build_hpo_trial_key_hash(trial_key)
        logger.debug(f"Computed trial_key_hash from configs: {trial_key_hash[:16]}...")
        return trial_key_hash
    except Exception as e:
        logger.warning(f"Could not compute trial_key_hash from configs: {e}", exc_info=True)
        return None


def get_or_compute_study_key_hash(
    study_key_hash: Optional[str] = None,
    hpo_parent_run_id: Optional[str] = None,
    data_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    train_config: Optional[Dict[str, Any]] = None,
    backbone: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Get or compute study_key_hash using fallback hierarchy.
    
    Priority order:
    1. Use provided study_key_hash (if available)
    2. Retrieve from MLflow run tags (SSOT) - if hpo_parent_run_id provided
    3. Compute from configs (fallback) - if data_config, hpo_config, train_config, backbone available
    
    This function consolidates the common pattern used across HPO and training execution scripts.
    
    Args:
        study_key_hash: Optional pre-computed study key hash (highest priority).
        hpo_parent_run_id: Optional HPO parent run ID to retrieve hash from tags (SSOT).
        data_config: Optional data configuration dictionary (for computation fallback).
        hpo_config: Optional HPO configuration dictionary (for computation fallback).
        train_config: Optional training configuration dictionary (for computation fallback).
        backbone: Optional model backbone name (for computation fallback).
        config_dir: Optional config directory for tag registry and hash computation.
        
    Returns:
        study_key_hash if found/computed, None otherwise.
    """
    # Priority 1: Use provided study_key_hash
    if study_key_hash:
        logger.debug(f"Using provided study_key_hash: {study_key_hash[:16]}...")
        return study_key_hash
    
    # Priority 2: Retrieve from MLflow run tags (SSOT)
    if hpo_parent_run_id:
        try:
            client = MlflowClient()
            retrieved_hash = get_study_key_hash_from_run(
                hpo_parent_run_id, client, config_dir
            )
            if retrieved_hash:
                logger.debug(
                    f"Retrieved study_key_hash from parent run tags (SSOT): {retrieved_hash[:16]}..."
                )
                return retrieved_hash
        except Exception as e:
            logger.debug(f"Could not retrieve study_key_hash from parent run: {e}")
    
    # Priority 3: Compute from configs (fallback)
    if data_config and hpo_config and train_config and backbone:
        try:
            computed_hash = compute_study_key_hash_v2(
                data_config, hpo_config, train_config, backbone, config_dir
            )
            if computed_hash:
                logger.debug(
                    f"Computed study_key_hash from configs (fallback): {computed_hash[:16]}..."
                )
                return computed_hash
        except Exception as e:
            logger.debug(f"Could not compute study_key_hash from configs: {e}")
    
    logger.warning(
        f"Could not get or compute study_key_hash. "
        f"study_key_hash={'provided' if study_key_hash else 'missing'}, "
        f"hpo_parent_run_id={'provided' if hpo_parent_run_id else 'missing'}, "
        f"configs={'available' if (data_config and hpo_config and train_config and backbone) else 'missing'}"
    )
    return None


def get_or_compute_trial_key_hash(
    trial_key_hash: Optional[str] = None,
    trial_run_id: Optional[str] = None,
    study_key_hash: Optional[str] = None,
    hyperparameters: Optional[Dict[str, Any]] = None,
    config_dir: Optional[Path] = None,
) -> Optional[str]:
    """
    Get or compute trial_key_hash using fallback hierarchy.
    
    Priority order:
    1. Use provided trial_key_hash (if available)
    2. Retrieve from trial run tags (SSOT) - if trial_run_id provided
    3. Compute from study_key_hash + hyperparameters (fallback) - if both available
    
    This function consolidates the common pattern used across HPO and training execution scripts.
    
    Args:
        trial_key_hash: Optional pre-computed trial key hash (highest priority).
        trial_run_id: Optional trial run ID to retrieve hash from tags (SSOT).
        study_key_hash: Optional study key hash (for computation fallback).
        hyperparameters: Optional hyperparameters dictionary (for computation fallback).
        config_dir: Optional config directory for tag registry and hash computation.
        
    Returns:
        trial_key_hash if found/computed, None otherwise.
    """
    # Priority 1: Use provided trial_key_hash
    if trial_key_hash:
        logger.debug(f"Using provided trial_key_hash: {trial_key_hash[:16]}...")
        return trial_key_hash
    
    # Priority 2: Retrieve from trial run tags (SSOT)
    if trial_run_id:
        try:
            client = MlflowClient()
            retrieved_hash = get_trial_key_hash_from_run(
                trial_run_id, client, config_dir
            )
            if retrieved_hash:
                logger.debug(
                    f"Retrieved trial_key_hash from trial run tags (SSOT): {retrieved_hash[:16]}..."
                )
                return retrieved_hash
        except Exception as e:
            logger.debug(f"Could not retrieve trial_key_hash from trial run: {e}")
    
    # Priority 3: Compute from study_key_hash + hyperparameters (fallback)
    if study_key_hash and hyperparameters:
        try:
            computed_hash = compute_trial_key_hash_from_configs(
                study_key_hash, hyperparameters, config_dir
            )
            if computed_hash:
                logger.debug(
                    f"Computed trial_key_hash from configs (fallback): {computed_hash[:16]}..."
                )
                return computed_hash
        except Exception as e:
            logger.debug(f"Could not compute trial_key_hash from configs: {e}")
    
    logger.warning(
        f"Could not get or compute trial_key_hash. "
        f"trial_key_hash={'provided' if trial_key_hash else 'missing'}, "
        f"trial_run_id={'provided' if trial_run_id else 'missing'}, "
        f"study_key_hash={'available' if study_key_hash else 'missing'}, "
        f"hyperparameters={'available' if hyperparameters else 'missing'}"
    )
    return None



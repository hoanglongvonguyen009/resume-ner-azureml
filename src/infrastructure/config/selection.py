"""
@meta
name: selection_config
type: utility
domain: config
responsibility:
  - Centralized selection config utilities
  - Extract and validate selection configuration
  - Champion selection settings and objective direction (with migration support)
inputs:
  - Selection configuration dictionaries
outputs:
  - Extracted configuration values
  - Validated settings
tags:
  - utility
  - config
  - selection
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""Centralized selection config utilities.

Provides utilities for extracting and validating selection configuration,
including champion selection settings and objective direction (with migration support).
"""

from __future__ import annotations

import warnings
from typing import Any, Dict

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def get_objective_direction(selection_config: Dict[str, Any]) -> str:
    """
    Get objective direction with migration support for goal→direction.
    
    Accepts both "goal" and "direction" keys during migration period.
    
    Args:
        selection_config: Selection configuration dictionary
        
    Returns:
        Objective direction: "maximize" or "minimize"
        
    Examples:
        >>> config = {"objective": {"direction": "maximize"}}
        >>> get_objective_direction(config)
        'maximize'
        
        >>> config = {"objective": {"goal": "max"}}  # Legacy
        >>> get_objective_direction(config)
        'maximize'
    """
    objective = selection_config.get("objective", {})
    
    # Prefer new "direction" key
    if "direction" in objective:
        return objective["direction"]
    
    # Fallback to legacy "goal" key (with warning)
    if "goal" in objective:
        warnings.warn(
            "Using deprecated 'objective.goal' key. "
            "Please update config to use 'objective.direction' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        goal = objective["goal"]
        # Map goal values to direction
        if goal.lower() in ["maximize", "max"]:
            return "maximize"
        elif goal.lower() in ["minimize", "min"]:
            return "minimize"
        else:
            return goal  # Pass through if already correct format
    
    # Default
    return "maximize"


def get_champion_selection_config(selection_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract champion selection config with defaults and constraint validation.
    
    Returns validated config with constraints enforced (e.g., top_k <= min_trials).
    
    Args:
        selection_config: Selection configuration dictionary
        
    Returns:
        Validated champion selection config dictionary with:
        - min_trials_per_group: int
        - top_k_for_stable_score: int (clamped to <= min_trials_per_group)
        - require_artifact_available: bool
        - artifact_check_source: str ("tag" or "disk")
        - prefer_schema_version: str ("2.0", "1.0", or "auto")
        - allow_mixed_schema_groups: bool
    """
    champion_config = selection_config.get("champion_selection", {})
    
    min_trials = champion_config.get("min_trials_per_group", 3)
    top_k = champion_config.get("top_k_for_stable_score", 3)
    
    # ENFORCE CONSTRAINT: top_k <= min_trials
    if top_k > min_trials:
        logger.warning(
            f"top_k_for_stable_score ({top_k}) > min_trials_per_group ({min_trials}). "
            f"Clamping top_k to {min_trials}."
        )
        top_k = min_trials
    
    return {
        "min_trials_per_group": min_trials,
        "top_k_for_stable_score": top_k,
        "require_artifact_available": champion_config.get("require_artifact_available", True),
        "artifact_check_source": champion_config.get("artifact_check_source", "tag"),
        "prefer_schema_version": champion_config.get("prefer_schema_version", "auto"),
        "allow_mixed_schema_groups": champion_config.get("allow_mixed_schema_groups", False),
    }


"""Trial finding utilities for sweep tracker."""

import re
from typing import Any, Optional

import mlflow

from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def extract_trial_number(run: Any) -> Optional[int]:
    """
    Extract trial number from a run using multiple strategies.

    Tries:
    1. trial_number tag (primary)
    2. code.trial_number tag (alternative)
    3. code.trial tag (alternative)
    4. Parse from run name (e.g., "trial_0_..." -> 0)

    Args:
        run: MLflow Run object

    Returns:
        Trial number as int, or None if not found
    """
    # Strategy 1: Check primary trial_number tag
    trial_num_tag = run.data.tags.get("trial_number")
    if trial_num_tag:
        try:
            return int(trial_num_tag)
        except (ValueError, TypeError):
            pass

    # Strategy 2: Check alternative tag keys
    config_dir = None  # Could be inferred from context if available
    from infrastructure.naming.mlflow.tag_keys import (
        get_hpo_trial_number,
    )
    hpo_trial_number_tag = get_hpo_trial_number(config_dir)
    for tag_key in [hpo_trial_number_tag, "code.trial"]:
        tag_value = run.data.tags.get(tag_key)
        if tag_value:
            try:
                return int(tag_value)
            except (ValueError, TypeError):
                pass

    # Strategy 3: Parse from run name (fallback)
    run_name = run.data.tags.get(
        "mlflow.runName") or run.info.run_name or ""
    match = re.search(r"trial[_-](\d+)", run_name)
    if match:
        try:
            return int(match.group(1))
        except (ValueError, TypeError):
            pass

    return None


def find_best_trial_run_id(
    study: Any,
    parent_run_id: str,
    experiment_id: str,
    output_dir: Optional[Any] = None,
) -> Optional[str]:
    """
    Find best trial's MLflow run ID.
    
    Returns:
        Best trial run ID if found, None otherwise
    """
    try:
        from infrastructure.paths.utils import infer_config_dir
        from infrastructure.naming.mlflow.tag_keys import (
            get_hpo_best_trial_number,
            get_hpo_best_trial_run_id,
        )
        
        from infrastructure.tracking.mlflow.client import create_mlflow_client
        client = create_mlflow_client()
        parent_run = client.get_run(parent_run_id)
        study_key_hash = parent_run.data.tags.get("code.study_key_hash")
        
        if not study_key_hash:
            logger.warning(
                f"Could not find MLflow run ID for best trial. "
                f"Parent run {parent_run_id[:12]}... missing study_key_hash tag."
            )
            return None
        
        best_trial_number = study.best_trial.number
        
        # Search for runs with matching study_key_hash and trial_number
        filter_str = (
            f"tags.code.study_key_hash = '{study_key_hash}' AND "
            f"tags.trial_number = '{best_trial_number}'"
        )
        candidate_runs = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string=filter_str,
            max_results=100,
        )
        
        # Filter results to only include runs that belong to this parent
        matching_runs = []
        for run in candidate_runs:
            run_parent_id = run.data.tags.get("mlflow.parentRunId")
            if run_parent_id == parent_run_id:
                trial_num = extract_trial_number(run)
                if trial_num == best_trial_number:
                    matching_runs.append(run)
        
        if len(matching_runs) > 0:
            best_run = matching_runs[0]
            best_run_id = best_run.info.run_id
            logger.info(
                f"Found best trial {best_trial_number} "
                f"(study_key_hash + trial_number + parentRunId): {best_run_id[:12]}..."
            )
            
            # Log it
            config_dir = infer_config_dir(path=output_dir)
            best_trial_run_id_tag = get_hpo_best_trial_run_id(config_dir)
            best_trial_number_tag = get_hpo_best_trial_number(config_dir)
            mlflow.log_param("best_trial_run_id", best_run_id)
            mlflow.set_tag(best_trial_run_id_tag, best_run_id)
            mlflow.set_tag(best_trial_number_tag, str(best_trial_number))
            
            return best_run_id
        else:
            logger.warning(
                f"Could not find MLflow run ID for best trial {best_trial_number}. "
                f"Found {len(candidate_runs)} runs with matching study_key_hash and trial_number, "
                f"but none belong to parent {parent_run_id[:12]}..."
            )
            return None
    except Exception as search_error:
        logger.warning(
            f"Could not find MLflow run ID for best trial: {search_error}"
        )
        return None


from __future__ import annotations

"""Interrupted run cleanup utilities for HPO.

Handles tagging of interrupted runs from previous sessions.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, TypedDict

import mlflow
from typing import Any, Dict, Optional, TypedDict

from mlflow.tracking import MlflowClient

from common.constants.mlflow import (
    SAFETY_MLFLOW_MAX_RESULTS,
    HASH_DISPLAY_LENGTH_MEDIUM,
)
from common.shared.logging_utils import get_logger
from common.types import MLflowRun, HPOConfigDict
from infrastructure.tracking.mlflow.client import create_mlflow_client
from training.hpo.core.types import HPOParentContext
# Tag key imports moved to local scope where needed

logger = get_logger(__name__)


class CleanupConfig(TypedDict):
    """Configuration for interrupted run cleanup."""
    parent_run_id: str
    hpo_parent_context: HPOParentContext
    mlflow_experiment_name: str
    mlflow_run_name: str
    output_dir: Path
    hpo_config: HPOConfigDict
    config_dir: Optional[Path]


def should_skip_cleanup(hpo_config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Check if cleanup should be skipped based on config or environment variable.

    Args:
        hpo_config: HPO configuration dictionary.

    Returns:
        Tuple of (should_skip, source) where source indicates why cleanup is skipped.
    """
    cleanup_config = hpo_config.get("cleanup", {})
    skip_cleanup_config = cleanup_config.get(
        "disable_auto_cleanup", True)  # Default: true (disabled)
    skip_cleanup_env = os.environ.get(
        "DISABLE_AUTO_CLEANUP", "").lower() == "true"

    # Env var overrides config: if env var is set, use it; otherwise use config
    if "DISABLE_AUTO_CLEANUP" in os.environ:
        skip_cleanup = skip_cleanup_env
        source = "environment variable"
    else:
        skip_cleanup = skip_cleanup_config
        source = "config"

    return skip_cleanup, source


def strip_child_suffix(name: str) -> str:
    """
    Recursively strip child count suffixes (_N or (N)) from the end.

    Examples:
        "local_hpo_distilbert_smoke_test_3.27_3" -> "local_hpo_distilbert_smoke_test_3.27"
        "local_hpo_distilbert_smoke_test_3.27 (1)" -> "local_hpo_distilbert_smoke_test_3.27"
    """
    while True:
        new = re.sub(r"(?:\s*\(\d+\)\s*|_\d+)\s*$", "", name).strip()
        if new == name:
            return name
        name = new


def should_tag_as_interrupted(run_data: MLflowRun, current_run_id: str) -> tuple[bool, str]:
    """
    Check if a run should be tagged as interrupted using cached run data.

    Args:
        run_data: MLflow run data object.
        current_run_id: Current run ID to exclude.

    Returns:
        Tuple of (should_tag, reason).
    """
    run_id = run_data.info.run_id
    if run_id == current_run_id:
        return False, "is_current_run"

    if run_data.data.tags.get("code.interrupted") == "true":
        return False, "already_tagged_interrupted"

    # Only tag runs that have project identity tags
    if run_data.data.tags.get("code.project") is None:
        return False, "no_project_identity"

    return True, "ok"


def _setup_cleanup_context(
    config: CleanupConfig,
) -> tuple[MlflowClient, str, Optional[str], Dict[str, Any], Optional[int]]:
    """
    Setup MLflow client and context for cleanup.

    Returns:
        Tuple of (client, current_env, run_key_hash, naming_config, current_start_time).
    """
    from common.shared.platform_detection import detect_platform
    from infrastructure.naming.mlflow.run_keys import (
        build_mlflow_run_key_hash,
        build_mlflow_run_key,
    )
    from infrastructure.naming.mlflow.config import get_naming_config
    from infrastructure.paths.utils import resolve_project_paths_with_fallback
    from infrastructure.paths.repo import detect_repo_root

    client = create_mlflow_client()
    current_env = detect_platform()

    run_key = build_mlflow_run_key(config["hpo_parent_context"])
    run_key_hash = build_mlflow_run_key_hash(run_key) if run_key else None

    # Resolve config_dir
    if config["config_dir"] is not None:
        root_dir = detect_repo_root(config_dir=config["config_dir"])
        config_dir = config["config_dir"]
    else:
        root_dir, config_dir = resolve_project_paths_with_fallback(
            output_dir=config["output_dir"],
            config_dir=None,
        )
    naming_config = get_naming_config(config_dir)

    # Get current run start_time for legacy run validation
    current_start_time = None
    try:
        current_run_info = client.get_run(config["parent_run_id"])
        current_start_time = current_run_info.info.start_time
    except Exception as e:
        logger.warning(
            f"[CLEANUP] Could not get current run start_time: {e}. "
            f"Legacy run validation will be skipped."
        )

    return client, current_env, run_key_hash, naming_config, current_start_time


def _fetch_all_runs(
    client: MlflowClient, experiment_id: str
) -> list[MLflowRun]:
    """
    Fetch all runs from experiment.

    Args:
        client: MLflow client.
        experiment_id: Experiment ID.

    Returns:
        List of runs.
    """
    try:
        all_runs = client.search_runs(
            experiment_ids=[experiment_id],
            filter_string="",
            max_results=SAFETY_MLFLOW_MAX_RESULTS,
            order_by=["attributes.start_time DESC"],
        )

        if len(all_runs) >= SAFETY_MLFLOW_MAX_RESULTS:
            logger.warning(
                f"[CLEANUP] Fetched {len(all_runs)} runs (safety limit reached). "
                f"Some older runs may not be processed."
            )
        return all_runs
    except Exception as e:
        logger.warning(
            f"[CLEANUP] Error fetching runs: {e}. Cleanup may be incomplete.")
        return []


def _build_parent_to_children_map(all_runs: list[MLflowRun]) -> Dict[str, list[MLflowRun]]:
    """
    Build parent→children map from all runs.

    Args:
        all_runs: List of all runs.

    Returns:
        Dictionary mapping parent_run_id to list of child runs.
    """
    parent_to_children = {}
    for run in all_runs:
        parent_id = run.data.tags.get("mlflow.parentRunId")
        if parent_id:
            if parent_id not in parent_to_children:
                parent_to_children[parent_id] = []
            parent_to_children[parent_id].append(run)
    return parent_to_children


def _is_hpo_or_sweep_run(run_stage: Optional[str], run_run_type: Optional[str]) -> bool:
    """Check if run is an HPO or sweep run."""
    return run_stage in ["hpo", "sweep"] or run_run_type == "sweep"


def _matches_environment_and_project(
    run_project: Optional[str],
    run_env: Optional[str],
    expected_project: str,
    current_env: str,
) -> bool:
    """Check if run matches expected project and environment."""
    return run_project == expected_project and run_env == current_env


def _is_tag_based_match(
    run: MLflowRun,
    run_key_hash: Optional[str],
    current_env: str,
    expected_project: str,
    client: MlflowClient,
    parent_run_id: str,
) -> bool:
    """
    Check if run matches by tag-based filtering.

    Args:
        run: MLflow run object.
        run_key_hash: Current run key hash.
        current_env: Current environment.
        expected_project: Expected project name.
        client: MLflow client.
        parent_run_id: Parent run ID.

    Returns:
        True if run matches tag-based criteria.
    """
    run_hash = run.data.tags.get("code.run_key_hash")
    run_study_key_hash = run.data.tags.get("code.study_key_hash")
    run_project = run.data.tags.get("code.project")
    run_env = run.data.tags.get("code.env")
    run_stage = run.data.tags.get("code.stage")
    run_run_type = run.data.tags.get("mlflow.runType")
    run_parent_run_id = run.data.tags.get("mlflow.parentRunId")

    # Strategy 1: Match by code.run_key_hash (best - exact identity match)
    if run_hash and run_project and run_env:
        if (
            run_hash == run_key_hash
            and _matches_environment_and_project(run_project, run_env, expected_project, current_env)
            and _is_hpo_or_sweep_run(run_stage, run_run_type)
            and not run_parent_run_id
        ):
            logger.info(
                f"[CLEANUP] Tag-based match (run_key_hash): {run.info.run_name} "
                f"(run_id: {run.info.run_id[:HASH_DISPLAY_LENGTH_MEDIUM]}..., hash: {run_hash[:HASH_DISPLAY_LENGTH_MEDIUM]}...)"
            )
            return True

    # Strategy 2: Match by code.study_key_hash (if run_key_hash not available)
    if not run_study_key_hash:
        return False

    current_study_key_hash = None
    try:
        current_run_info = client.get_run(parent_run_id)
        current_study_key_hash = current_run_info.data.tags.get(
            "code.study_key_hash"
        )
    except Exception:
        pass

    if (
        current_study_key_hash
        and run_study_key_hash == current_study_key_hash
        and _matches_environment_and_project(run_project, run_env, expected_project, current_env)
        and _is_hpo_or_sweep_run(run_stage, run_run_type)
        and not run_parent_run_id
    ):
        logger.info(
            f"[CLEANUP] Tag-based match (study_key_hash): {run.info.run_name} "
            f"(run_id: {run.info.run_id[:HASH_DISPLAY_LENGTH_MEDIUM]}..., study_hash: {run_study_key_hash[:HASH_DISPLAY_LENGTH_MEDIUM]}...)"
        )
        return True

    return False


def _is_name_fallback_match(
    run: MLflowRun,
    base_run_name: str,
    current_env: str,
    expected_project: str,
    current_start_time: Optional[int],
) -> bool:
    """
    Check if run matches by name-based fallback (legacy runs).

    Args:
        run: MLflow run object.
        base_run_name: Base run name (without version suffix).
        current_env: Current environment.
        expected_project: Expected project name.
        current_start_time: Current run start time.

    Returns:
        True if run matches name-based criteria.
    """
    run_hash = run.data.tags.get("code.run_key_hash")
    run_study_key_hash = run.data.tags.get("code.study_key_hash")
    run_project = run.data.tags.get("code.project")
    run_env = run.data.tags.get("code.env")
    run_stage = run.data.tags.get("code.stage")
    run_parent_run_id = run.data.tags.get("mlflow.parentRunId")

    # Only use name fallback if run is missing critical identity tags (legacy run)
    if run_hash or run_study_key_hash or not run_project or not run_env:
        return False

    run_name = run.info.run_name
    if not run_name.startswith(base_run_name):
        return False

    # Strict safety checks for legacy runs
    if not _matches_environment_and_project(run_project, run_env, expected_project, current_env):
        return False

    if run_stage and run_stage not in ["hpo", "sweep"]:
        return False

    if run_parent_run_id:
        return False

    # Additional check: run must be older than current run
    if current_start_time is not None:
        run_start_time = run.info.start_time
        if run_start_time >= current_start_time:
            return False

    # All checks passed
    logger.info(
        f"[CLEANUP] Name-based fallback match: {run.info.run_name} "
        f"(run_id: {run.info.run_id[:HASH_DISPLAY_LENGTH_MEDIUM]}...)"
    )
    return True


def _find_interrupted_parent_runs(
    all_runs: list[MLflowRun],
    run_key_hash: Optional[str],
    current_env: str,
    expected_project: str,
    client: MlflowClient,
    parent_run_id: str,
    base_run_name: str,
    current_start_time: Optional[int],
) -> tuple[list[MLflowRun], Dict[str, int], int, int]:
    """
    Find interrupted parent runs using tag-based and name-based filtering.

    Returns:
        Tuple of (interrupted_parents, status_counts, tag_based_matches, name_fallback_matches).
    """
    interrupted_parents = []
    status_counts = {}
    tag_based_matches = 0
    name_fallback_matches = 0

    for run in all_runs:
        # Track status breakdown
        status = run.info.status
        status_counts[status] = status_counts.get(status, 0) + 1

        # Skip if not RUNNING
        if status != "RUNNING":
            continue

        # Skip if already tagged
        if run.data.tags.get("code.interrupted") == "true":
            continue

        # Skip if current run
        if run.info.run_id == parent_run_id:
            continue

        # Check tag-based match
        if _is_tag_based_match(
            run, run_key_hash, current_env, expected_project, client, parent_run_id
        ):
            interrupted_parents.append(run)
            tag_based_matches += 1
            logger.info(
                f"[CLEANUP] Found interrupted parent run: {run.info.run_name} "
                f"(run_id: {run.info.run_id[:12]}..., strategy: tag-based)"
            )
            continue

        # Check name-based fallback match
        if _is_name_fallback_match(
            run, base_run_name, current_env, expected_project, current_start_time
        ):
            interrupted_parents.append(run)
            name_fallback_matches += 1
            logger.info(
                f"[CLEANUP] Found interrupted parent run: {run.info.run_name} "
                f"(run_id: {run.info.run_id[:12]}..., strategy: name-fallback)"
            )

    logger.info(f"[CLEANUP] Status breakdown: {status_counts}")
    logger.info(
        f"[CLEANUP] Found {tag_based_matches} tag-based matches, "
        f"{name_fallback_matches} name-fallback matches (legacy), "
        f"{len(interrupted_parents)} total eligible for tagging"
    )

    return interrupted_parents, status_counts, tag_based_matches, name_fallback_matches


def _find_orphaned_children(
    all_runs: list[MLflowRun],
) -> list[MLflowRun]:
    """
    Find orphaned child runs (RUNNING children with terminal parents).

    Args:
        all_runs: List of all runs.

    Returns:
        List of orphaned child runs.
    """
    orphaned_children = []
    run_id_map = {run.info.run_id: run for run in all_runs}

    for run in all_runs:
        parent_id = run.data.tags.get("mlflow.parentRunId")
        if not parent_id:
            continue  # Not a child run

        # Only consider RUNNING child runs
        if run.info.status != "RUNNING":
            continue

        # Skip if already tagged
        if run.data.tags.get("code.interrupted") == "true":
            continue

        # Check if parent exists and is in terminal state
        parent_run = run_id_map.get(parent_id)
        if parent_run:
            parent_status = parent_run.info.status
            # If parent is in terminal state, child is orphaned
            if parent_status in ["FINISHED", "FAILED", "KILLED"]:
                # Verify it's a project run (has code.project tag)
                if run.data.tags.get("code.project"):
                    orphaned_children.append(run)
                    logger.info(
                        f"[CLEANUP] Found orphaned child run: {run.info.run_name} "
                        f"(run_id: {run.info.run_id[:12]}..., parent_status: {parent_status})"
                    )

    logger.info(
        f"[CLEANUP] Found {len(orphaned_children)} orphaned child runs "
        f"(RUNNING children with terminal parents)"
    )
    return orphaned_children


def _tag_interrupted_parent_and_children(
    client: MlflowClient,
    interrupted_parents: list[MLflowRun],
    parent_to_children: Dict[str, list[MLflowRun]],
    parent_run_id: str,
) -> tuple[int, int]:
    """
    Tag interrupted parent runs and their children.

    Returns:
        Tuple of (total_tagged_parents, total_tagged_children).
    """
    from infrastructure.naming.mlflow.tag_keys import get_interrupted

    total_tagged_parents = 0
    total_tagged_children = 0

    for run in interrupted_parents:
        run_id_to_mark = run.info.run_id
        run_name = run.info.run_name

        should_tag, reason = should_tag_as_interrupted(run, parent_run_id)
        if not should_tag:
            logger.debug(
                f"[CLEANUP] Skipping parent run {run_id_to_mark[:12]}... (reason: {reason})"
            )
            continue

        logger.info(
            f"[CLEANUP] Tagging interrupted parent run {run_id_to_mark[:12]}... "
            f"(name: {run_name}, status: {run.info.status})"
        )

        try:
            interrupted_tag = get_interrupted(None)
            client.set_tag(run_id_to_mark, interrupted_tag, "true")
            total_tagged_parents += 1
            logger.info(
                f"[CLEANUP] Successfully tagged interrupted parent run {run_id_to_mark[:12]}... as interrupted"
            )

            # Get child runs from pre-built map
            child_runs = parent_to_children.get(run_id_to_mark, [])
            logger.info(
                f"[CLEANUP] Found {len(child_runs)} child runs for parent {run_id_to_mark[:12]}... "
                f"(from pre-built map, no API call)"
            )

            # Tag non-terminal child runs
            tagged_children = 0
            skipped_children = 0

            for child_run in child_runs:
                child_run_id = child_run.info.run_id
                child_status = child_run.info.status
                child_name = child_run.info.run_name

                # Skip if already tagged
                if child_run.data.tags.get("code.interrupted") == "true":
                    skipped_children += 1
                    continue

                # Only tag non-terminal runs
                if child_status not in ["RUNNING", "SCHEDULED", "QUEUED"]:
                    skipped_children += 1
                    continue

                # Check project identity
                if child_run.data.tags.get("code.project") is None:
                    skipped_children += 1
                    logger.debug(
                        f"[CLEANUP] Skipping child run {child_run_id[:12]}... "
                        f"(name: {child_name}, reason: no_project_identity)"
                    )
                    continue

                # Tag the child run
                logger.info(
                    f"[CLEANUP] Tagging interrupted child run {child_run_id[:12]}... "
                    f"(name: {child_name}, status: {child_status})"
                )
                try:
                    client.set_tag(child_run_id, interrupted_tag, "true")
                    tagged_children += 1
                    total_tagged_children += 1
                    logger.info(
                        f"[CLEANUP] Successfully tagged interrupted child run {child_run_id[:12]}... as interrupted"
                    )
                except Exception as e:
                    logger.warning(
                        f"[CLEANUP] Could not tag child run {child_run_id[:12]}... as interrupted: {e}"
                    )
                    skipped_children += 1

            logger.info(
                f"[CLEANUP] Tagged {tagged_children} interrupted child runs, "
                f"skipped {skipped_children} child runs (terminal or filtered) "
                f"for parent {run_id_to_mark[:12]}..."
            )

        except Exception as e:
            logger.warning(
                f"[CLEANUP] Could not tag parent run {run_id_to_mark[:12]}... as interrupted: {e}"
            )

    return total_tagged_parents, total_tagged_children


def _tag_orphaned_children(
    client: MlflowClient,
    orphaned_children: list[MLflowRun],
    parent_run_id: str,
) -> int:
    """
    Tag orphaned child runs.

    Returns:
        Number of tagged orphaned children.
    """
    from infrastructure.naming.mlflow.tag_keys import get_interrupted

    total_tagged_orphaned = 0

    for child_run in orphaned_children:
        child_run_id = child_run.info.run_id
        child_name = child_run.info.run_name
        parent_id = child_run.data.tags.get("mlflow.parentRunId")

        should_tag, reason = should_tag_as_interrupted(child_run, parent_run_id)
        if not should_tag:
            logger.debug(
                f"[CLEANUP] Skipping orphaned child run {child_run_id[:12]}... (reason: {reason})"
            )
            continue

        logger.info(
            f"[CLEANUP] Tagging orphaned child run {child_run_id[:12]}... "
            f"(name: {child_name}, parent_id: {parent_id[:12] if parent_id else 'None'}...)"
        )
        try:
            interrupted_tag = get_interrupted(None)
            client.set_tag(child_run_id, interrupted_tag, "true")
            total_tagged_orphaned += 1
            logger.info(
                f"[CLEANUP] Successfully tagged orphaned child run {child_run_id[:12]}... as interrupted"
            )
        except Exception as e:
            logger.warning(
                f"[CLEANUP] Could not tag orphaned child run {child_run_id[:12]}... as interrupted: {e}"
            )

    return total_tagged_orphaned


def cleanup_interrupted_runs(
    parent_run_id: str,
    hpo_parent_context: Any,
    mlflow_experiment_name: str,
    mlflow_run_name: str,
    output_dir: Path,
    hpo_config: Dict[str, Any],
    config_dir: Optional[Path] = None,
) -> Optional[Dict[str, list]]:
    """
    Clean up interrupted runs from previous sessions by tagging them.

    Args:
        parent_run_id: Current parent run ID.
        hpo_parent_context: Naming context for HPO parent run.
        mlflow_experiment_name: MLflow experiment name.
        mlflow_run_name: Generated MLflow run name.
        output_dir: Base output directory.
        hpo_config: HPO configuration dictionary.
        config_dir: Optional config directory path. If provided, used directly without inference.

    Returns:
        Dictionary mapping parent_run_id to list of child runs, or None if cleanup skipped.
    """
    # Check if cleanup should be skipped
    skip_cleanup, source = should_skip_cleanup(hpo_config)
    cleanup_config_dict = hpo_config.get('cleanup', {})
    logger.debug(
        f"[CLEANUP] Config check: skip_cleanup={skip_cleanup}, source={source}, "
        f"cleanup_config={cleanup_config_dict}"
    )

    if skip_cleanup:
        logger.info(
            f"[CLEANUP] Automatic interrupted-run cleanup disabled "
            f"(via {source}). Clean up via UI if needed."
        )
        return None

    # Early return if skip - don't proceed with cleanup logic
    if not (parent_run_id and hpo_parent_context):
        return None

    try:
        logger.info(
            f"[CLEANUP] Starting cleanup check: parent_run_id={parent_run_id[:12]}..."
        )

        # Build config object
        config: CleanupConfig = {
            "parent_run_id": parent_run_id,
            "hpo_parent_context": hpo_parent_context,
            "mlflow_experiment_name": mlflow_experiment_name,
            "mlflow_run_name": mlflow_run_name,
            "output_dir": output_dir,
            "hpo_config": hpo_config,
            "config_dir": config_dir,
        }

        # Setup context
        client, current_env, run_key_hash, naming_config, current_start_time = _setup_cleanup_context(config)

        logger.info(
            f"[CLEANUP] MLflow imported successfully. Current env: {current_env}, "
            f"run_key_hash: {run_key_hash[:12] if run_key_hash else 'None'}..."
        )

        # Get experiment
        experiment = mlflow.get_experiment_by_name(mlflow_experiment_name)
        if not experiment:
            logger.warning(
                f"[CLEANUP] Could not retrieve experiment: {mlflow_experiment_name}")
            return None

        logger.info(f"[CLEANUP] Retrieved experiment: {experiment.experiment_id}")

        # Extract base name by removing version suffix
        base_run_name = strip_child_suffix(mlflow_run_name)

        # Fetch all runs
        logger.info(
            f"[CLEANUP] Fetching all runs in experiment (may paginate for large experiments)..."
        )
        all_runs = _fetch_all_runs(client, experiment.experiment_id)
        logger.info(f"[CLEANUP] Fetched {len(all_runs)} total runs from experiment")

        # Build parent→children map
        parent_to_children = _build_parent_to_children_map(all_runs)
        logger.info(
            f"[CLEANUP] Built parent→children map: {len(parent_to_children)} parents have children"
        )

        # Find interrupted parent runs
        expected_project = naming_config.get("project_name", "resume-ner")
        interrupted_parents, status_counts, tag_based_matches, name_fallback_matches = _find_interrupted_parent_runs(
            all_runs,
            run_key_hash,
            current_env,
            expected_project,
            client,
            parent_run_id,
            base_run_name,
            current_start_time,
        )

        # Find orphaned child runs
        orphaned_children = _find_orphaned_children(all_runs)

        # Tag interrupted parent runs and their children
        total_tagged_parents, total_tagged_children = _tag_interrupted_parent_and_children(
            client, interrupted_parents, parent_to_children, parent_run_id
        )

        if interrupted_parents:
            logger.info(
                f"[CLEANUP] Completed cleanup: tagged {total_tagged_parents} parent runs "
                f"and {total_tagged_children} child runs"
            )
        else:
            logger.info("[CLEANUP] No interrupted parent runs found to tag")

        # Tag orphaned child runs
        total_tagged_orphaned = _tag_orphaned_children(client, orphaned_children, parent_run_id)

        if orphaned_children:
            logger.info(
                f"[CLEANUP] Tagged {total_tagged_orphaned} orphaned child runs "
                f"(RUNNING children with terminal parents)"
            )
        else:
            logger.info("[CLEANUP] No orphaned child runs found to tag")

        # Return parent_to_children map for reuse in log_final_metrics
        return parent_to_children

    except Exception as e:
        logger.warning(
            f"[CLEANUP] Error during cleanup of interrupted runs: {e}")
        import traceback

        logger.debug(f"[CLEANUP] Cleanup traceback: {traceback.format_exc()}")
        return None

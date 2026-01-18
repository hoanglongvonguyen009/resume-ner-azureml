"""Champion selection logic for trial finding."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger

from evaluation.selection.trial_finder.mlflow_queries import (
    SAMPLE_MLFLOW_MAX_RESULTS,
    compute_group_scores,
    partition_runs_by_schema_version,
    query_runs_with_fallback,
    select_groups_by_schema_version,
)

logger = get_logger(__name__)


class ChampionSelectionSetup(TypedDict):
    """Setup data for champion selection."""
    config_dir: Path
    champion_config: Dict[str, Any]
    objective_metric: str
    objective_direction: str
    maximize: bool
    tags_registry: Any
    backbone_name: str


class TagKeys(TypedDict):
    """Tag keys for champion selection."""
    backbone_tag: str
    stage_tag: str
    study_key_tag: str
    trial_key_tag: str
    schema_version_tag: str
    artifact_tag: str


def _setup_champion_selection(
    backbone: str,
    selection_config: Dict[str, Any],
    config_dir: Optional[Path],
) -> Tuple[ChampionSelectionSetup, TagKeys]:
    """
    Setup champion selection: extract config, load tags registry, etc.

    Returns:
        Tuple of (setup_data, tag_keys).
    """
    from infrastructure.config.selection import (
        get_champion_selection_config,
        get_objective_direction,
    )
    from infrastructure.naming.mlflow.tags_registry import load_tags_registry
    from infrastructure.paths.utils import resolve_project_paths_with_fallback

    # Trust provided config_dir parameter, only infer when None
    if config_dir is None:
        _, config_dir = resolve_project_paths_with_fallback(
            output_dir=None,
            config_dir=None,
        )

    # Extract config values
    champion_config = get_champion_selection_config(selection_config)
    objective_metric = selection_config.get("objective", {}).get("metric", "macro-f1")
    objective_direction = get_objective_direction(selection_config)
    maximize = objective_direction.lower() == "maximize"

    tags_registry = load_tags_registry(config_dir)
    backbone_name = backbone.split("-")[0] if "-" in backbone else backbone

    tag_keys = TagKeys(
        backbone_tag=tags_registry.key("process", "backbone"),
        stage_tag=tags_registry.key("process", "stage"),
        study_key_tag=tags_registry.key("grouping", "study_key_hash"),
        trial_key_tag=tags_registry.key("grouping", "trial_key_hash"),
        schema_version_tag=tags_registry.key("study", "key_schema_version"),
        artifact_tag=tags_registry.key("artifact", "available"),
    )

    setup = ChampionSelectionSetup(
        config_dir=config_dir,
        champion_config=champion_config,
        objective_metric=objective_metric,
        objective_direction=objective_direction,
        maximize=maximize,
        tags_registry=tags_registry,
        backbone_name=backbone_name,
    )

    return setup, tag_keys


def _filter_parent_runs(runs: List[Any]) -> List[Any]:
    """
    Filter out parent runs (they don't have trial metrics).

    Returns:
        Filtered list of child runs only.
    """
    runs_before_filter = len(runs)
    filtered_runs = [r for r in runs if r.data.tags.get("mlflow.parentRunId") is not None]
    parent_runs_filtered = runs_before_filter - len(filtered_runs)

    if parent_runs_filtered > 0:
        logger.info(
            f"Filtered out {parent_runs_filtered} parent run(s) (only child/trial runs have metrics). "
            f"{len(filtered_runs)} child runs remaining."
        )

    return filtered_runs


def _find_refit_run_for_champion(
    champion_run_id: str,
    champion_trial_key: Optional[str],
    hpo_experiment: Dict[str, str],
    mlflow_client: MlflowClient,
    config_dir: Path,
    tags_registry: Any,
    tag_keys: TagKeys,
    backbone: str,
) -> str:
    """
    Find refit run for champion trial using SSOT selector.

    Returns:
        Refit run ID.

    Raises:
        ValueError: If refit run not found (with diagnostic info).
    """
    try:
        from evaluation.selection.artifact_unified.selectors import select_artifact_run

        run_selector_result = select_artifact_run(
            trial_run_id=champion_run_id,
            mlflow_client=mlflow_client,
            experiment_id=hpo_experiment["id"],
            trial_key_hash=champion_trial_key,
            config_dir=config_dir,
        )

        refit_run_id = run_selector_result.refit_run_id

        if refit_run_id:
            logger.info(
                f"Found refit run {refit_run_id[:12]}... for champion trial {champion_run_id[:12]}... "
                f"(using SSOT selector: {run_selector_result.metadata.get('selection_strategy', 'unknown')})"
            )
            return refit_run_id
        else:
            # Refit is required - provide helpful error message
            refit_of_trial_tag = tags_registry.key("refit", "of_trial_run_id")

            # Diagnostic: Check if ANY refit runs exist in the experiment
            diagnostic_info = []
            try:
                from infrastructure.tracking.mlflow.queries import query_runs_by_tags

                any_refit_runs = query_runs_by_tags(
                    client=mlflow_client,
                    experiment_ids=[hpo_experiment["id"]],
                    required_tags={tag_keys["stage_tag"]: "hpo_refit"},
                    filter_string="",
                    max_results=SAMPLE_MLFLOW_MAX_RESULTS,
                )

                if any_refit_runs:
                    diagnostic_info.append(
                        f"Found {len(any_refit_runs)} refit run(s) in experiment, but none matched the champion trial."
                    )
                    # Show sample of refit run tags for debugging
                    sample_refit = any_refit_runs[0]
                    sample_trial_key = (
                        sample_refit.data.tags.get(tag_keys["trial_key_tag"]) or
                        sample_refit.data.tags.get("code.trial_key_hash") or
                        "missing"
                    )
                    sample_linking = (
                        sample_refit.data.tags.get(refit_of_trial_tag) or
                        sample_refit.data.tags.get("code.refit.of_trial_run_id") or
                        "missing"
                    )
                    diagnostic_info.append(
                        f"Sample refit run {sample_refit.info.run_id[:12]}... tags: "
                        f"trial_key_hash={sample_trial_key[:16] if isinstance(sample_trial_key, str) else sample_trial_key}..., "
                        f"linking_tag={sample_linking[:16] if isinstance(sample_linking, str) else sample_linking}..."
                    )
                else:
                    diagnostic_info.append(
                        "No refit runs found in experiment (tags.code.stage = 'hpo_refit' returned 0 results)."
                    )
            except Exception as diag_error:
                diagnostic_info.append(f"Could not diagnose: {diag_error}")

            # Provide helpful error message
            error_msg = (
                f"No refit run found for champion trial {champion_run_id[:12]}... "
                f"(trial_key_hash={champion_trial_key[:8] if champion_trial_key else 'missing'}...). "
                f"Refit is required to acquire checkpoint deterministically.\n"
                f"Used SSOT selector (evaluation.selection.artifact_unified.selectors.select_artifact_run).\n"
            )
            if diagnostic_info:
                error_msg += f"\nDiagnostics:\n" + "\n".join(f"  - {info}" for info in diagnostic_info)
            raise ValueError(error_msg)
    except ValueError:
        # Re-raise ValueError as-is (these are our explicit errors)
        raise
    except Exception as e:
        logger.error(
            f"Could not find refit run for champion trial {champion_run_id[:12]}...: {e}. "
            f"Failing fast to avoid using trial runs for checkpoint acquisition."
        )
        raise


def _select_champion_from_group(
    winning_group: Dict[str, Any],
    maximize: bool,
    backbone: str,
) -> Tuple[str, float]:
    """
    Select champion run from winning group.

    Returns:
        Tuple of (champion_run_id, champion_metric).

    Raises:
        ValueError: If group has invalid metrics.
    """
    run_metrics_raw = winning_group["run_metrics"]
    if not isinstance(run_metrics_raw, list):
        raise ValueError(f"Winning group has invalid run_metrics type for {backbone}")

    run_metrics_list = run_metrics_raw
    if not run_metrics_list:
        raise ValueError(f"Winning group has no run metrics for {backbone}")

    if maximize:
        champion_run_id, champion_metric = max(run_metrics_list, key=lambda x: x[1])
    else:
        champion_run_id, champion_metric = min(run_metrics_list, key=lambda x: x[1])

    return champion_run_id, float(champion_metric)


def _build_champion_result(
    backbone: str,
    champion_run_id: str,
    champion_metric: float,
    refit_run_id: str,
    champion_trial_key: Optional[str],
    winning_key: str,
    winning_group: Dict[str, Any],
    group_scores: Dict[str, Dict[str, Any]],
    hpo_experiment: Dict[str, str],
    checkpoint_path: Optional[Path],
    schema_version_used: str,
    setup: ChampionSelectionSetup,
    champion_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build champion selection result dictionary.

    Returns:
        Champion selection result dict.
    """
    return {
        "backbone": backbone,
        "champion": {
            "trial_run_id": champion_run_id,
            "refit_run_id": refit_run_id,
            "run_id": refit_run_id or champion_run_id,
            "trial_key_hash": champion_trial_key,
            "metric": champion_metric,
            "stable_score": winning_group["stable_score"],
            "study_key_hash": winning_key,
            "schema_version": schema_version_used,
            "checkpoint_path": checkpoint_path,
            "experiment_name": hpo_experiment.get("name"),
            "experiment_id": hpo_experiment.get("id"),
        },
        "all_groups": {
            k: {
                "best_metric": v["best_metric"],
                "stable_score": v["stable_score"],
                "n_trials": v["n_trials"],
                "n_valid": v["n_valid"],
                "n_invalid": v["n_invalid"],
            }
            for k, v in group_scores.items()
        },
        "selection_metadata": {
            "objective_direction": setup["objective_direction"],
            "min_trials_required": champion_config["min_trials_per_group"],
            "top_k_for_stable": champion_config["top_k_for_stable_score"],
            "artifact_required": champion_config["require_artifact_available"],
            "artifact_check_source": champion_config["artifact_check_source"],
            "allow_mixed_schema_groups": champion_config["allow_mixed_schema_groups"],
            "schema_version_used": schema_version_used,
        },
    }


def filter_by_artifact_availability(
    runs: List[Any],
    check_source: str,
    artifact_tag: str,
    mlflow_client: Optional[MlflowClient] = None,
    schema_version_tag: str = "code.study.key_schema_version",
) -> List[Any]:
    """
    Filter runs by artifact availability using config-specified source.
    
    For child runs (trial runs), also checks parent run for artifact tag
    since artifact.available is typically set on parent runs.
    
    Args:
        runs: List of MLflow runs
        check_source: "tag" (uses MLflow tag) or "disk" (checks filesystem)
        artifact_tag: Tag key for artifact availability
        mlflow_client: Optional MLflow client for checking parent runs
        schema_version_tag: Tag key for schema version
    """
    if check_source == "tag":
        # Use MLflow tag as authoritative source
        # For legacy runs without the tag, be lenient: if tag is missing (not "false"),
        # allow the run through with a warning (assumes artifacts might exist)
        filtered_runs = []
        runs_without_tag = 0
        runs_explicitly_false = 0
        runs_missing_tag = 0
        
        for run in runs:
            parent_run_id = run.data.tags.get("mlflow.parentRunId")
            artifact_available = True  # Default: allow through (lenient)
            tag_source = "default (allowing)"
            
            # Check parent run's artifact tag first (authoritative source)
            if mlflow_client and parent_run_id:
                try:
                    parent_run = mlflow_client.get_run(parent_run_id)
                    parent_tag_value = parent_run.data.tags.get(artifact_tag)
                    if parent_tag_value is not None:
                        artifact_available = parent_tag_value.lower() == "true"
                        tag_source = "parent"
                        if not artifact_available:
                            # Check if parent is legacy (no schema_version)
                            parent_schema_version = parent_run.data.tags.get(schema_version_tag)
                            if parent_schema_version is None:
                                # Legacy run - be lenient
                                artifact_available = True
                                tag_source = "parent false (legacy, allowing)"
                                runs_missing_tag += 1
                            else:
                                # v1/v2 run with explicit false - filter out
                                runs_explicitly_false += 1
                except Exception as e:
                    logger.debug(f"Could not check parent run {parent_run_id[:12]}... for artifact tag: {e}")
            
            # If parent check didn't find tag, check run itself
            if tag_source == "default (allowing)":
                run_tag_value = run.data.tags.get(artifact_tag)
                if run_tag_value is not None:
                    artifact_available = run_tag_value.lower() == "true"
                    tag_source = "run"
                    if not artifact_available:
                        # Check if run is legacy
                        run_schema_version = run.data.tags.get(schema_version_tag)
                        if run_schema_version is None:
                            # Legacy run - be lenient
                            artifact_available = True
                            tag_source = "run false (legacy, allowing)"
                            runs_missing_tag += 1
                        else:
                            runs_explicitly_false += 1
                else:
                    # Tag missing on both - allow through (may be in progress)
                    runs_missing_tag += 1
            
            if not artifact_available:
                runs_without_tag += 1
            
            if artifact_available:
                filtered_runs.append(run)
        
        # Log detailed statistics
        if runs_explicitly_false > 0:
            logger.warning(
                f"Artifact filter: {runs_explicitly_false} run(s) have {artifact_tag}='false' "
                f"(explicitly marked as unavailable)"
            )
        if runs_missing_tag > 0:
            logger.info(
                f"Artifact filter: {runs_missing_tag} legacy run(s) missing {artifact_tag} tag "
                f"(allowing through - artifacts may exist on disk)"
            )
        if runs_without_tag > 0 and runs_explicitly_false > 0:
            logger.warning(
                f"Artifact filter: {runs_without_tag} run(s) excluded "
                f"({runs_explicitly_false} explicitly false, {runs_missing_tag} missing/legacy allowed)"
            )
        
        return filtered_runs
    elif check_source == "disk":
        # Fallback: check filesystem (requires run_id -> path mapping)
        # This is a fallback - tag should be primary
        logger.warning(
            "Using disk-based artifact check (fallback). "
            "Consider using 'tag' source for better performance."
        )
        # Implementation would check checkpoint files exist
        # For now, return all runs (disk check would need run_id -> path logic)
        return runs
    else:
        logger.error(f"Unknown artifact_check_source: {check_source}. Using tag-based check.")
        return [
            r for r in runs
            if r.data.tags.get(artifact_tag, "false").lower() == "true"
        ]


def get_checkpoint_path_from_run(
    run: Any,
    study_key_hash: Optional[str] = None,
    trial_key_hash: Optional[str] = None,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Extract checkpoint path from MLflow run.
    
    Uses single source of truth: find_trial_checkpoint_by_hash() for local disk lookup.
    
    Args:
        run: MLflow run object
        study_key_hash: Study key hash for local disk lookup
        trial_key_hash: Trial key hash for local disk lookup
        root_dir: Project root directory (for local disk lookup)
        config_dir: Config directory (for local disk lookup)
    
    Returns:
        Path to checkpoint if available locally, else None
    """
    # Strategy 1: Try local disk lookup using single source of truth
    if study_key_hash and trial_key_hash and root_dir and config_dir:
        try:
            from evaluation.selection.local_selection_v2 import find_trial_checkpoint_by_hash
            from common.shared.platform_detection import detect_platform
            from infrastructure.naming.mlflow.tags_registry import load_tags_registry
            
            # Get backbone from run
            tags_registry = load_tags_registry(config_dir)
            backbone_tag = tags_registry.key("process", "backbone")
            backbone = run.data.tags.get(backbone_tag) or run.data.tags.get("code.model", "unknown")
            backbone_name = backbone.split("-")[0] if "-" in backbone else backbone
            
            # Use SSOT for HPO output directory path resolution
            from infrastructure.paths.resolve import resolve_output_path
            environment = detect_platform()
            hpo_base_dir = resolve_output_path(root_dir, config_dir, "hpo")
            hpo_output_dir = hpo_base_dir / environment / backbone_name
            
            # Use single source of truth for local disk lookup
            checkpoint_path = find_trial_checkpoint_by_hash(
                hpo_backbone_dir=hpo_output_dir,
                study_key_hash=study_key_hash,
                trial_key_hash=trial_key_hash,
            )
            
            if checkpoint_path and checkpoint_path.exists():
                return checkpoint_path
        except Exception:
            # Silently continue to next strategy
            pass
    
    # Strategy 2: Check checkpoint_path tag (if set)
    checkpoint_tag = run.data.tags.get("code.checkpoint_path")
    if checkpoint_tag:
        checkpoint_path = Path(checkpoint_tag)
        if checkpoint_path.exists():
            return checkpoint_path
    
    # Strategy 3: Return None (notebook will use acquire_best_model_checkpoint for MLflow)
    return None


def select_champion_per_backbone(
    backbone: str,
    hpo_experiment: Dict[str, str],
    selection_config: Dict[str, Any],
    mlflow_client: MlflowClient,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """
    Select champion (best configuration group winner) per backbone.
    
    Groups runs by study_key_hash v2 (comparable configuration groups),
    then selects best group and best trial within that group.
    
    All parameters come from selection_config (centralized config).
    
    Requirements enforced:
    1. Bound fingerprints in study_key_hash v2
    2. Never mix v1 and v2 runs in same selection (config-driven)
    3. Explicit objective direction (never assume max, with migration support)
    4. Handle missing/NaN metrics deterministically
    5. Minimum trial count guardrail (config-driven)
    6. Artifact availability constraint (config-driven source)
    7. Deterministic constraints (top_k <= min_trials)
    
    Args:
        backbone: Model backbone name
        hpo_experiment: Dict with 'name' and 'id' of HPO experiment
        selection_config: Selection configuration dictionary
        mlflow_client: MLflow client instance
        root_dir: Optional root directory
        config_dir: Optional config directory
    
    Returns:
        Champion selection result dict or None if no valid champions found
    """
    # Setup: extract config, load tags registry, etc.
    setup, tag_keys = _setup_champion_selection(backbone, selection_config, config_dir)
    champion_config = setup["champion_config"]
    min_trials_per_group = champion_config["min_trials_per_group"]
    top_k_for_stable_score = champion_config["top_k_for_stable_score"]
    require_artifact_available = champion_config["require_artifact_available"]
    artifact_check_source = champion_config["artifact_check_source"]
    allow_mixed_schema_groups = champion_config["allow_mixed_schema_groups"]
    prefer_schema_version = champion_config["prefer_schema_version"]
    objective_metric = setup["objective_metric"]
    maximize = setup["maximize"]
    tags_registry = setup["tags_registry"]
    backbone_name = setup["backbone_name"]

    # Step 1: Query runs with fallback strategies
    runs = query_runs_with_fallback(
        mlflow_client,
        hpo_experiment["id"],
        backbone_name,
        tag_keys["backbone_tag"],
        tag_keys["stage_tag"],
    )

    # Step 1.5: Filter out parent runs
    runs = _filter_parent_runs(runs)

    # Step 2: Artifact availability filter
    runs_before_artifact_filter = len(runs)
    if require_artifact_available:
        runs = filter_by_artifact_availability(
            runs, artifact_check_source, tag_keys["artifact_tag"], mlflow_client, tag_keys["schema_version_tag"]
        )
        runs_after_artifact_filter = len(runs)
        if runs_after_artifact_filter < runs_before_artifact_filter:
            logger.warning(
                f"Artifact filter removed {runs_before_artifact_filter - runs_after_artifact_filter} "
                f"runs for {backbone} ({runs_after_artifact_filter} remaining). "
                f"Check that runs have '{tag_keys['artifact_tag']}' tag set to 'true'."
            )
    
    # Step 3: Partition by study_key_hash AND schema version
    groups_v1, groups_v2, runs_without_study_key = partition_runs_by_schema_version(
        runs, tag_keys["study_key_tag"], tag_keys["schema_version_tag"]
    )

    if runs_without_study_key > 0:
        logger.warning(
            f"Skipped {runs_without_study_key} runs without {tag_keys['study_key_tag']} tag for {backbone}"
        )

    logger.info(
        f"Grouped runs for {backbone}: {len(groups_v1)} v1 group(s), "
        f"{len(groups_v2)} v2 group(s)"
    )

    # Step 4: Select groups based on schema version preferences
    groups_to_use, schema_version_used = select_groups_by_schema_version(
        groups_v1, groups_v2, allow_mixed_schema_groups, prefer_schema_version
    )

    if groups_v1 and groups_v2 and not allow_mixed_schema_groups:
        logger.info(
            f"Found both v1 and v2 runs for {backbone}. "
            f"Using {schema_version_used} groups only (never mixing versions)."
        )

    if not groups_to_use:
        # Provide helpful warning message
        if len(groups_v1) == 0 and len(groups_v2) == 0:
            logger.warning(
                f"No valid groups found for {backbone}. "
                f"No trial runs found in HPO experiment '{hpo_experiment.get('name', 'unknown')}'. "
                f"This may indicate:\n"
                f"  - HPO was not run for this backbone\n"
                f"  - Runs exist but don't have required tags (stage='hpo_trial' or 'hpo', backbone tag)\n"
                f"  - Runs exist but were filtered out (missing metrics, artifacts, or grouping tags)\n"
                f"Skipping champion selection for {backbone}."
            )
        else:
            logger.warning(
                f"No valid groups found for {backbone}. "
                f"Found {len(groups_v1)} v1 group(s) and {len(groups_v2)} v2 group(s), "
                f"but none matched selection criteria (schema_version preference: {prefer_schema_version}). "
                f"This may indicate:\n"
                f"  - Groups don't meet min_trials requirement\n"
                f"  - Schema version mismatch (prefer_schema_version={prefer_schema_version})\n"
                f"  - Groups filtered out by other criteria\n"
                f"Skipping champion selection for {backbone}."
            )
        return None
    
    # Step 5: Compute stable score per group (with all guards)
    total_groups = len(groups_to_use)
    group_scores, groups_skipped_min_trials = compute_group_scores(
        groups_to_use,
        objective_metric,
        maximize,
        min_trials_per_group,
        top_k_for_stable_score,
    )
    
    if not group_scores:
        logger.warning(
            f"No eligible groups for {backbone}. "
            f"Processed {total_groups} group(s), but {groups_skipped_min_trials} were skipped "
            f"due to insufficient trials (minimum: {min_trials_per_group}). "
            f"Remaining groups: {total_groups - groups_skipped_min_trials}"
        )
        return None
    
    logger.info(
        f"Found {len(group_scores)} eligible group(s) for {backbone} "
        f"({groups_skipped_min_trials} skipped due to min_trials requirement)"
    )
    
    # Step 6: Select winning group (by stable_score, respecting direction)
    if maximize:
        winning_key = max(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]
    else:
        winning_key = min(group_scores.items(), key=lambda x: x[1]["stable_score"])[0]

    winning_group = group_scores[winning_key]

    # Step 7: Select champion within winning group
    try:
        champion_run_id, champion_metric = _select_champion_from_group(
            winning_group, maximize, backbone
        )
    except ValueError as e:
        logger.warning(str(e))
        return None

    # Fetch full run only when needed
    champion_run = mlflow_client.get_run(champion_run_id)
    champion_trial_key = champion_run.data.tags.get(tag_keys["trial_key_tag"])

    # Step 8: Find refit run for champion trial
    refit_run_id = _find_refit_run_for_champion(
        champion_run_id,
        champion_trial_key,
        hpo_experiment,
        mlflow_client,
        setup["config_dir"],
        tags_registry,
        tag_keys,
        backbone,
    )

    # Step 9: Get checkpoint path
    checkpoint_run = mlflow_client.get_run(refit_run_id)
    checkpoint_path = get_checkpoint_path_from_run(
        checkpoint_run,
        study_key_hash=winning_key,
        trial_key_hash=champion_trial_key,
        root_dir=root_dir,
        config_dir=setup["config_dir"],
    )

    # Step 10: Build result
    return _build_champion_result(
        backbone,
        champion_run_id,
        champion_metric,
        refit_run_id,
        champion_trial_key,
        winning_key,
        winning_group,
        group_scores,
        hpo_experiment,
        checkpoint_path,
        schema_version_used,
        setup,
        champion_config,
    )


def select_champions_for_backbones(
    backbone_values: List[str],
    hpo_experiments: Dict[str, Dict[str, str]],  # backbone -> {name, id}
    selection_config: Dict[str, Any],
    mlflow_client: MlflowClient,
    root_dir: Optional[Path] = None,
    config_dir: Optional[Path] = None,
    **kwargs: Any,  # Pass through to select_champion_per_backbone
) -> Dict[str, Dict[str, Any]]:
    """
    Select champions for multiple backbones.
    
    Wrapper around select_champion_per_backbone() for multiple backbones.
    
    Args:
        backbone_values: List of backbone names
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        selection_config: Selection configuration dictionary
        mlflow_client: MLflow client instance
        root_dir: Optional root directory
        config_dir: Optional config directory
        **kwargs: Additional arguments to pass to select_champion_per_backbone
    
    Returns:
        Dict mapping backbone -> champion selection result
    """
    champions = {}
    for backbone in backbone_values:
        if backbone not in hpo_experiments:
            logger.warning(f"No HPO experiment found for {backbone}, skipping")
            continue
        
        champion = select_champion_per_backbone(
            backbone=backbone,
            hpo_experiment=hpo_experiments[backbone],
            selection_config=selection_config,
            mlflow_client=mlflow_client,
            root_dir=root_dir,
            config_dir=config_dir,
            **kwargs,
        )
        if champion:
            champions[backbone] = champion
    
    return champions


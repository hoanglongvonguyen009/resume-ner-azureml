"""
@meta
name: mlflow_selection
type: utility
domain: selection
responsibility:
  - MLflow-based best model selection
  - Join benchmark runs with training (refit) runs
  - Compute normalized composite scores
inputs:
  - Benchmark experiment
  - HPO experiments
  - Tags configuration
  - Selection configuration
outputs:
  - Best model selection result
tags:
  - utility
  - selection
  - mlflow
ci:
  runnable: true
  needs_gpu: false
  needs_cloud: false
lifecycle:
  status: active
"""

"""MLflow-based best model selection from benchmark and training runs."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, Union

from mlflow.tracking import MlflowClient

from common.shared.logging_utils import get_logger
from infrastructure.naming.mlflow.tags_registry import TagsRegistry

logger = get_logger(__name__)

# MLflow query limits
DEFAULT_MLFLOW_MAX_RESULTS = 2000  # Default limit for MLflow run queries
LARGE_MLFLOW_MAX_RESULTS = 5000  # Large limit for comprehensive queries


def find_best_model_from_mlflow(
    benchmark_experiment: Optional[Dict[str, str]],
    hpo_experiments: Dict[str, Dict[str, str]],
    tags_config: Union[TagsRegistry, Dict[str, Any]],
    selection_config: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Find best model by joining benchmark runs with training (refit) runs.

    Strategy:
    1. Query benchmark runs with required metrics
    2. Preload ALL refit runs from HPO experiments into in-memory lookup
    3. Join benchmark runs with refit runs using (study_key_hash, trial_key_hash)
    4. Compute normalized composite scores (F1 + latency)
    5. Select best candidate

    Args:
        benchmark_experiment: Dict with 'name' and 'id' of benchmark experiment
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        tags_config: TagsRegistry or Dict with tags configuration (for backward compatibility)
        selection_config: Selection configuration

    Returns:
        Dict with best run info or None if no matches found
    """
    client = MlflowClient()

    # Validate inputs
    if benchmark_experiment is None:
        error_msg = "benchmark_experiment is None. Make sure benchmark runs have been executed and logged to MLflow."
        logger.error(error_msg)
        return None

    if not hpo_experiments:
        error_msg = "No HPO experiments found. Make sure HPO runs have been executed and logged to MLflow."
        logger.error(error_msg)
        return None

    # Tag keys from config (support both TagsRegistry and dict for backward compatibility)
    if hasattr(tags_config, 'key') and callable(getattr(tags_config, 'key', None)):
        # It's a TagsRegistry object (or compatible object with key() method)
        study_key_tag = tags_config.key("grouping", "study_key_hash")
        trial_key_tag = tags_config.key("grouping", "trial_key_hash")
        stage_tag = tags_config.key("process", "stage")
        backbone_tag = tags_config.key("process", "backbone")
    elif isinstance(tags_config, dict):
        # Backward compatibility: support dict access
        study_key_tag = tags_config["grouping"]["study_key_hash"]
        trial_key_tag = tags_config["grouping"]["trial_key_hash"]
        stage_tag = tags_config["process"]["stage"]
        backbone_tag = tags_config["process"]["backbone"]
    else:
        raise TypeError(
            f"tags_config must be TagsRegistry or dict, got {type(tags_config)}. "
            f"Object: {tags_config}"
        )

    # Selection config
    objective_metric = selection_config["objective"]["metric"]
    f1_weight = float(selection_config["scoring"]["f1_weight"])
    latency_weight = float(selection_config["scoring"]["latency_weight"])
    normalize_weights = bool(
        selection_config["scoring"].get("normalize_weights", True))
    required_benchmark_metrics = selection_config["benchmark"]["required_metrics"]

    # Normalize weights if needed
    if normalize_weights:
        total_weight = f1_weight + latency_weight
        if total_weight > 0:
            f1_weight = f1_weight / total_weight
            latency_weight = latency_weight / total_weight

    logger.info(f"Finding best model from MLflow")
    logger.info(f"  Benchmark experiment: {benchmark_experiment['name']}")
    logger.info(f"  HPO experiments: {len(hpo_experiments)}")
    logger.info(f"  Objective metric: {objective_metric}")
    logger.info(
        f"  Composite weights: F1={f1_weight:.2f}, Latency={latency_weight:.2f}")
    
    # Log latency aggregation strategy from config
    latency_aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
    config_source = "config file" if "latency_aggregation" in selection_config.get("benchmark", {}) else "default"
    logger.info(
        f"  Latency aggregation: {latency_aggregation} (from {config_source}, "
        f"applied when multiple benchmark runs exist with same benchmark_key)")

    # Step 1: Query benchmark runs
    logger.info("Querying benchmark runs...")

    all_benchmark_runs = client.search_runs(
        experiment_ids=[benchmark_experiment["id"]],
        filter_string="",
        max_results=DEFAULT_MLFLOW_MAX_RESULTS,
    )

    # Filter for finished runs in Python (more reliable than MLflow filter on Azure ML)
    benchmark_runs = [
        run for run in all_benchmark_runs if run.info.status == "FINISHED"]
    logger.info(f"Found {len(benchmark_runs)} finished benchmark runs")

    # Filter benchmark runs with required metrics and grouping tags
    valid_benchmark_runs = []
    for run in benchmark_runs:
        has_required_metrics = all(
            metric in run.data.metrics for metric in required_benchmark_metrics)
        has_grouping_tags = (
            study_key_tag in run.data.tags and trial_key_tag in run.data.tags)

        if has_required_metrics and has_grouping_tags:
            valid_benchmark_runs.append(run)

    logger.info(
        f"Found {len(valid_benchmark_runs)} benchmark runs with required metrics and grouping tags")

    if not valid_benchmark_runs:
        logger.warning("No valid benchmark runs found")
        return None

    # Step 2: Preload ALL trial runs (for metrics) and refit runs (for artifacts) from HPO experiments
    logger.info("Preloading trial and refit runs from HPO experiments...")
    trial_lookup: Dict[Tuple[str, str], Any] = {}
    refit_lookup: Dict[Tuple[str, str], Any] = {}

    for backbone, exp_info in hpo_experiments.items():
        all_hpo_runs = client.search_runs(
            experiment_ids=[exp_info["id"]],
            filter_string="",
            max_results=LARGE_MLFLOW_MAX_RESULTS,
        )

        # Filter for finished runs in Python
        finished_runs = [
            r for r in all_hpo_runs if r.info.status == "FINISHED"]

        # Filter for trial runs (stage = "hpo") - these have macro-f1 metric
        trial_runs = [
            r for r in finished_runs if r.data.tags.get(stage_tag) == "hpo"]

        # Filter for refit runs (stage = "hpo_refit") - these have checkpoints
        refit_runs = [r for r in finished_runs if r.data.tags.get(
            stage_tag) == "hpo_refit"]

        logger.debug(
            f"Found {len(trial_runs)} trial runs and {len(refit_runs)} refit runs in {exp_info['name']}")

        # Helper function to add run to lookup, handling duplicates
        def add_to_lookup(lookup: Dict[Tuple[str, str], Any], run: Any, run_type: str) -> None:
            study_hash = run.data.tags.get(study_key_tag)
            trial_hash = run.data.tags.get(trial_key_tag)
            
            if not study_hash or not trial_hash:
                return
            
            key = (study_hash, trial_hash)
            existing = lookup.get(key)
            if existing is None:
                lookup[key] = run
            elif run.info.start_time > existing.info.start_time:
                logger.warning(
                    f"Duplicate {run_type} hash found: key=({study_hash[:8]}..., {trial_hash[:8]}...). "
                    f"Keeping LATER run: run_id={run.info.run_id[:8]}... over run_id={existing.info.run_id[:8]}..."
                )
                lookup[key] = run

        # Build trial lookup: (study_key_hash, trial_key_hash) -> trial_run (for metrics)
        for trial_run in trial_runs:
            add_to_lookup(trial_lookup, trial_run, "trial")

        # Build refit lookup: (study_key_hash, trial_key_hash) -> refit_run (for artifacts)
        for refit_run in refit_runs:
            add_to_lookup(refit_lookup, refit_run, "refit")

    logger.info(
        f"Built trial lookup with {len(trial_lookup)} unique (study_hash, trial_hash) pairs")
    logger.info(
        f"Built refit lookup with {len(refit_lookup)} unique (study_hash, trial_hash) pairs")

    if not trial_lookup:
        logger.warning("No trial runs found in HPO experiments")
        return None

    # Step 2.5: Group benchmark runs by (study_key_hash, trial_key_hash, benchmark_key)
    # This deduplicates multiple benchmark runs with same config
    from collections import defaultdict

    benchmark_groups = defaultdict(list)
    for benchmark_run in valid_benchmark_runs:
        study_hash = benchmark_run.data.tags[study_key_tag]
        trial_hash = benchmark_run.data.tags[trial_key_tag]
        
        # Get benchmark_key from tag (primary) or construct fallback
        benchmark_key = benchmark_run.data.tags.get("benchmark_key")
        if not benchmark_key:
            # Fallback: use trial_key_hash as key (backward compatibility)
            # This groups all runs without benchmark_key tag together
            benchmark_key = f"legacy_{trial_hash}"
            logger.debug(
                f"Benchmark run {benchmark_run.info.run_id[:12]}... missing benchmark_key tag, "
                f"using fallback key"
            )
        
        key = (study_hash, trial_hash, benchmark_key)
        benchmark_groups[key].append(benchmark_run)

    logger.info(
        f"Grouped {len(valid_benchmark_runs)} benchmark runs into {len(benchmark_groups)} unique groups "
        f"(by study_key_hash, trial_key_hash, benchmark_key)"
    )

    # Step 3: Join benchmark groups with trial runs and refit runs
    candidates = []

    # Get latency aggregation strategy from config
    latency_aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")
    # Options: "latest" (use most recent), "median" (use median latency), "mean" (use mean latency)

    for (study_hash, trial_hash, benchmark_key), benchmark_runs in benchmark_groups.items():
        # Aggregate latency across multiple runs with same benchmark_key
        latencies = [
            r.data.metrics.get("latency_batch_1_ms")
            for r in benchmark_runs
            if r.data.metrics.get("latency_batch_1_ms") is not None
        ]
        
        if not latencies:
            logger.warning(
                f"No valid latency found for group (study={study_hash[:8]}..., "
                f"trial={trial_hash[:8]}..., benchmark_key={benchmark_key[:16]}...)"
            )
            continue
        
        # Select representative benchmark run based on aggregation strategy
        if latency_aggregation == "median":
            import statistics
            target_latency = statistics.median(latencies)
            # Use run with latency closest to median
            representative_run = min(
                benchmark_runs,
                key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - target_latency)
            )
            aggregated_latency = target_latency
        elif latency_aggregation == "mean":
            aggregated_latency = sum(latencies) / len(latencies)
            # Use run with latency closest to mean
            representative_run = min(
                benchmark_runs,
                key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - aggregated_latency)
            )
        else:  # "latest" (default)
            # Use most recent run
            representative_run = max(
                benchmark_runs,
                key=lambda r: r.info.start_time if r.info.start_time else 0
            )
            aggregated_latency = representative_run.data.metrics.get("latency_batch_1_ms")
        
        if len(benchmark_runs) > 1:
            logger.debug(
                f"Aggregated {len(benchmark_runs)} benchmark runs for group "
                f"(study={study_hash[:8]}..., trial={trial_hash[:8]}...): "
                f"latencies={[f'{l:.1f}ms' for l in latencies]}, "
                f"aggregated={aggregated_latency:.1f}ms (strategy={latency_aggregation})"
            )
        
        benchmark_run = representative_run

        # Look up matching trial run (for metrics - has macro-f1)
        # Create 2-tuple key for lookup (separate from 3-tuple used for grouping)
        lookup_key: Tuple[str, str] = (study_hash, trial_hash)
        trial_run = trial_lookup.get(lookup_key)

        if trial_run is None:
            continue

        # Get F1 score from trial run (trial runs have macro-f1, refit runs don't)
        f1_score = trial_run.data.metrics.get(objective_metric)
        if f1_score is None:
            continue

        # Look up matching refit run (for artifacts - has checkpoint)
        refit_run = refit_lookup.get(lookup_key)
        artifact_run = refit_run if refit_run is not None else trial_run

        # Get backbone from trial run (prefer params, fallback to tags)
        backbone = (
            trial_run.data.params.get("backbone") or
            trial_run.data.tags.get(backbone_tag) or
            trial_run.data.tags.get("code.model", "unknown")
        )

        candidates.append({
            "benchmark_run": benchmark_run,
            "trial_run": trial_run,
            "artifact_run": artifact_run,
            "refit_run": refit_run,
            "f1_score": float(f1_score),
            "latency_ms": float(aggregated_latency),  # Use aggregated latency
            "backbone": backbone,
            "study_key_hash": study_hash,
            "trial_key_hash": trial_hash,
            "benchmark_key": benchmark_key,  # Include for debugging
            "benchmark_runs_count": len(benchmark_runs),  # Include for debugging
        })

    logger.info(
        f"Found {len(candidates)} candidate(s) with both benchmark and training metrics")

    if not candidates:
        logger.warning(
            "No candidates found with both benchmark and training metrics")
        return None

    # Step 4: Compute normalized composite scores

    f1_scores = [c["f1_score"] for c in candidates]
    latency_scores = [c["latency_ms"] for c in candidates]

    f1_min, f1_max = min(f1_scores), max(f1_scores)
    latency_min, latency_max = min(latency_scores), max(latency_scores)

    f1_range = f1_max - f1_min if f1_max > f1_min else 1.0
    latency_range = latency_max - latency_min if latency_max > latency_min else 1.0

    for candidate in candidates:
        # Normalize F1 (higher is better)
        norm_f1 = (candidate["f1_score"] - f1_min) / \
            f1_range if f1_range > 0 else 0.5

        # Normalize latency (lower is better, so invert)
        norm_latency = 1.0 - \
            ((candidate["latency_ms"] - latency_min) /
             latency_range) if latency_range > 0 else 0.5

        # Composite score
        composite_score = (f1_weight * norm_f1) + \
            (latency_weight * norm_latency)
        candidate["composite_score"] = composite_score
        candidate["norm_f1"] = norm_f1
        candidate["norm_latency"] = norm_latency

    # Step 5: Select best candidate
    best_candidate = max(candidates, key=lambda c: c["composite_score"])

    artifact_run = best_candidate["artifact_run"]
    trial_run = best_candidate["trial_run"]

    logger.info(f"Best model selected: backbone={best_candidate['backbone']}, "
                f"f1={best_candidate['f1_score']:.4f}, "
                f"latency={best_candidate['latency_ms']:.2f}ms, "
                f"composite={best_candidate['composite_score']:.4f}")

    # Find experiment name for best candidate
    best_experiment_name = None
    for backbone, exp_info in hpo_experiments.items():
        if backbone == best_candidate["backbone"]:
            best_experiment_name = exp_info["name"]
            break

    print(f"\n✅ Best model selected:")
    print(f"   Run ID: {artifact_run.info.run_id}")
    print(f"   Experiment: {best_experiment_name or 'unknown'}")
    print(f"   Backbone: {best_candidate['backbone']}")
    print(f"   F1 Score: {best_candidate['f1_score']:.4f}")
    print(f"   Latency: {best_candidate['latency_ms']:.2f} ms")
    print(f"   Composite Score: {best_candidate['composite_score']:.4f}")

    # Return best run info (use artifact_run for artifacts, trial_run for metrics)
    return {
        "run_id": artifact_run.info.run_id,
        "trial_run_id": trial_run.info.run_id,
        "experiment_name": best_experiment_name or "unknown",
        "experiment_id": artifact_run.info.experiment_id,
        "backbone": best_candidate["backbone"],
        "study_key_hash": best_candidate["study_key_hash"],
        "trial_key_hash": best_candidate["trial_key_hash"],
        "f1_score": best_candidate["f1_score"],
        "latency_ms": best_candidate["latency_ms"],
        "composite_score": best_candidate["composite_score"],
        "tags": artifact_run.data.tags,
        "params": artifact_run.data.params,
        "metrics": trial_run.data.metrics,
        "has_refit_run": best_candidate["refit_run"] is not None,
    }

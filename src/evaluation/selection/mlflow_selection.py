from __future__ import annotations

"""
@meta
name: mlflow_selection
type: utility
domain: selection
responsibility:
  - MLflow-based best model selection (SSOT for local selection)
  - Join benchmark runs with training (refit) runs
  - Compute normalized composite scores
  - Uses infrastructure.tracking.mlflow.queries for all MLflow queries
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

"""MLflow-based best model selection from benchmark and training runs.

**Single Source of Truth (SSOT)** for local MLflow-based best model selection.
This module provides the core selection logic that joins benchmark runs with
training (refit) runs and computes composite scores.

**Layering**:
- This module uses `infrastructure.tracking.mlflow.queries` for all MLflow queries (SSOT for query patterns).
- AzureML-focused selection modules (`selection.selection`, `evaluation.selection.selection`)
  are thin wrappers that translate AzureML sweep jobs into normalized inputs for this core.
- Workflows (`evaluation.selection.workflows.selection_workflow`) orchestrate caching and
  artifact acquisition around this core selection function.
"""

from typing import Any, Dict, List, Optional, Tuple, Union, TypedDict
from collections import defaultdict

from typing import Any, Dict, List, Optional, Tuple, Union, TypedDict
from collections import defaultdict

from mlflow.tracking import MlflowClient

from common.constants.mlflow import (
    MEDIUM_MLFLOW_MAX_RESULTS,
    LARGE_MLFLOW_MAX_RESULTS,
)
from common.shared.logging_utils import get_logger
from common.types import MLflowRun
from infrastructure.naming.mlflow.tags_registry import TagsRegistry
from infrastructure.tracking.mlflow.client import create_mlflow_client
from infrastructure.tracking.mlflow.queries import query_runs_by_tags

logger = get_logger(__name__)

# Use constants from common.constants.mlflow
DEFAULT_MLFLOW_MAX_RESULTS = MEDIUM_MLFLOW_MAX_RESULTS  # Backward compatibility alias


class TagKeys(TypedDict):
    """Tag keys extracted from config."""
    study_key_tag: str
    trial_key_tag: str
    stage_tag: str
    backbone_tag: str


class SelectionWeights(TypedDict):
    """Normalized selection weights."""
    f1_weight: float
    latency_weight: float


class CandidateInfo(TypedDict):
    """Information about a candidate model."""
    benchmark_run: MLflowRun
    trial_run: MLflowRun
    artifact_run: MLflowRun
    refit_run: Optional[MLflowRun]
    f1_score: float
    latency_ms: float
    backbone: str
    study_key_hash: str
    trial_key_hash: str
    benchmark_key: str
    benchmark_runs_count: int
    composite_score: Optional[float]
    norm_f1: Optional[float]
    norm_latency: Optional[float]


def _extract_tag_keys(
    tags_config: Union[TagsRegistry, Dict[str, Any]]
) -> TagKeys:
    """
    Extract tag keys from tags_config (supports both TagsRegistry and dict).

    Returns:
        TagKeys dictionary with extracted tag keys.
    """
    if hasattr(tags_config, 'key') and callable(getattr(tags_config, 'key', None)):
        # It's a TagsRegistry object
        return TagKeys(
            study_key_tag=tags_config.key("grouping", "study_key_hash"),
            trial_key_tag=tags_config.key("grouping", "trial_key_hash"),
            stage_tag=tags_config.key("process", "stage"),
            backbone_tag=tags_config.key("process", "backbone"),
        )
    elif isinstance(tags_config, dict):
        # Backward compatibility: support dict access
        return TagKeys(
            study_key_tag=tags_config["grouping"]["study_key_hash"],
            trial_key_tag=tags_config["grouping"]["trial_key_hash"],
            stage_tag=tags_config["process"]["stage"],
            backbone_tag=tags_config["process"]["backbone"],
        )
    else:
        raise TypeError(
            f"tags_config must be TagsRegistry or dict, got {type(tags_config)}. "
            f"Object: {tags_config}"
        )


def _normalize_selection_weights(
    f1_weight: float,
    latency_weight: float,
    normalize_weights: bool,
) -> SelectionWeights:
    """
    Normalize selection weights if needed.

    Returns:
        SelectionWeights dictionary with normalized weights.
    """
    if normalize_weights:
        total_weight = f1_weight + latency_weight
        if total_weight > 0:
            f1_weight = f1_weight / total_weight
            latency_weight = latency_weight / total_weight

    return SelectionWeights(
        f1_weight=f1_weight,
        latency_weight=latency_weight,
    )


def _query_and_filter_benchmark_runs(
    client: MlflowClient,
    benchmark_experiment: Dict[str, str],
    required_benchmark_metrics: List[str],
    tag_keys: TagKeys,
) -> List[MLflowRun]:
    """
    Query and filter benchmark runs with required metrics and grouping tags.

    Returns:
        List of valid benchmark runs.
    """
    logger.info("Querying benchmark runs...")

    benchmark_runs = query_runs_by_tags(
        client=client,
        experiment_ids=[benchmark_experiment["id"]],
        required_tags={},
        filter_string="",
        max_results=MEDIUM_MLFLOW_MAX_RESULTS,
    )
    logger.info(f"Found {len(benchmark_runs)} finished benchmark runs")

    # Filter benchmark runs with required metrics and grouping tags
    valid_benchmark_runs = []
    for run in benchmark_runs:
        has_required_metrics = all(
            metric in run.data.metrics for metric in required_benchmark_metrics)
        has_grouping_tags = (
            tag_keys["study_key_tag"] in run.data.tags and
            tag_keys["trial_key_tag"] in run.data.tags
        )

        if has_required_metrics and has_grouping_tags:
            valid_benchmark_runs.append(run)

    logger.info(
        f"Found {len(valid_benchmark_runs)} benchmark runs with required metrics and grouping tags")

    return valid_benchmark_runs


def _add_to_lookup(
    lookup: Dict[Tuple[str, str], MLflowRun],
    run: MLflowRun,
    run_type: str,
    tag_keys: TagKeys,
) -> None:
    """
    Add run to lookup dictionary, handling duplicates by keeping the latest run.

    Args:
        lookup: Dictionary to add to.
        run: MLflow run to add.
        run_type: Type of run (for logging).
        tag_keys: Tag keys dictionary.
    """
    study_hash = run.data.tags.get(tag_keys["study_key_tag"])
    trial_hash = run.data.tags.get(tag_keys["trial_key_tag"])

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


def _preload_trial_and_refit_runs(
    client: MlflowClient,
    hpo_experiments: Dict[str, Dict[str, str]],
    tag_keys: TagKeys,
) -> Tuple[Dict[Tuple[str, str], MLflowRun], Dict[Tuple[str, str], MLflowRun]]:
    """
    Preload ALL trial runs and refit runs from HPO experiments into lookup dictionaries.

    Returns:
        Tuple of (trial_lookup, refit_lookup) dictionaries.
    """
    logger.info("Preloading trial and refit runs from HPO experiments...")
    trial_lookup: Dict[Tuple[str, str], MLflowRun] = {}
    refit_lookup: Dict[Tuple[str, str], MLflowRun] = {}

    for backbone, exp_info in hpo_experiments.items():
        finished_runs = query_runs_by_tags(
            client=client,
            experiment_ids=[exp_info["id"]],
            required_tags={},
            filter_string="",
            max_results=LARGE_MLFLOW_MAX_RESULTS,
        )

        # Filter for trial runs (stage = "hpo")
        trial_runs = [
            r for r in finished_runs if r.data.tags.get(tag_keys["stage_tag"]) == "hpo"]

        # Filter for refit runs (stage = "hpo_refit")
        refit_runs = [
            r for r in finished_runs if r.data.tags.get(tag_keys["stage_tag"]) == "hpo_refit"]

        logger.debug(
            f"Found {len(trial_runs)} trial runs and {len(refit_runs)} refit runs in {exp_info['name']}")

        # Build trial lookup
        for trial_run in trial_runs:
            _add_to_lookup(trial_lookup, trial_run, "trial", tag_keys)

        # Build refit lookup
        for refit_run in refit_runs:
            _add_to_lookup(refit_lookup, refit_run, "refit", tag_keys)

    logger.info(
        f"Built trial lookup with {len(trial_lookup)} unique (study_hash, trial_hash) pairs")
    logger.info(
        f"Built refit lookup with {len(refit_lookup)} unique (study_hash, trial_hash) pairs")

    return trial_lookup, refit_lookup


def _group_benchmark_runs(
    valid_benchmark_runs: List[MLflowRun],
    tag_keys: TagKeys,
) -> Dict[Tuple[str, str, str], List[MLflowRun]]:
    """
    Group benchmark runs by (study_key_hash, trial_key_hash, benchmark_key).

    Returns:
        Dictionary mapping (study_hash, trial_hash, benchmark_key) -> list of runs.
    """
    benchmark_groups = defaultdict(list)
    for benchmark_run in valid_benchmark_runs:
        study_hash = benchmark_run.data.tags[tag_keys["study_key_tag"]]
        trial_hash = benchmark_run.data.tags[tag_keys["trial_key_tag"]]

        # Get benchmark_key from tag (primary) or construct fallback
        benchmark_key = benchmark_run.data.tags.get("benchmark_key")
        if not benchmark_key:
            # Fallback: use trial_key_hash as key (backward compatibility)
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

    return benchmark_groups


def _aggregate_latency(
    benchmark_runs: List[MLflowRun],
    latency_aggregation: str,
) -> Tuple[Optional[float], Optional[MLflowRun]]:
    """
    Aggregate latency across multiple benchmark runs using specified strategy.

    Returns:
        Tuple of (aggregated_latency, representative_run).
    """
    latencies = [
        r.data.metrics.get("latency_batch_1_ms")
        for r in benchmark_runs
        if r.data.metrics.get("latency_batch_1_ms") is not None
    ]

    if not latencies:
        return None, None

    if latency_aggregation == "median":
        import statistics
        target_latency = statistics.median(latencies)
        representative_run = min(
            benchmark_runs,
            key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - target_latency)
        )
        aggregated_latency = target_latency
    elif latency_aggregation == "mean":
        aggregated_latency = sum(latencies) / len(latencies)
        representative_run = min(
            benchmark_runs,
            key=lambda r: abs(r.data.metrics.get("latency_batch_1_ms", float('inf')) - aggregated_latency)
        )
    else:  # "latest" (default)
        representative_run = max(
            benchmark_runs,
            key=lambda r: r.info.start_time if r.info.start_time else 0
        )
        aggregated_latency = representative_run.data.metrics.get("latency_batch_1_ms")

    return aggregated_latency, representative_run


def _build_candidates(
    benchmark_groups: Dict[Tuple[str, str, str], List[MLflowRun]],
    trial_lookup: Dict[Tuple[str, str], MLflowRun],
    refit_lookup: Dict[Tuple[str, str], MLflowRun],
    tag_keys: TagKeys,
    objective_metric: str,
    latency_aggregation: str,
) -> List[CandidateInfo]:
    """
    Join benchmark groups with trial runs and refit runs to build candidate list.

    Returns:
        List of candidate dictionaries.
    """
    candidates = []

    for (study_hash, trial_hash, benchmark_key), benchmark_runs in benchmark_groups.items():
        # Aggregate latency across multiple runs with same benchmark_key
        aggregated_latency, representative_run = _aggregate_latency(
            benchmark_runs, latency_aggregation
        )

        if aggregated_latency is None or representative_run is None:
            logger.warning(
                f"No valid latency found for group (study={study_hash[:8]}..., "
                f"trial={trial_hash[:8]}..., benchmark_key={benchmark_key[:16]}...)"
            )
            continue

        if len(benchmark_runs) > 1:
            latencies = [
                r.data.metrics.get("latency_batch_1_ms")
                for r in benchmark_runs
                if r.data.metrics.get("latency_batch_1_ms") is not None
            ]
            logger.debug(
                f"Aggregated {len(benchmark_runs)} benchmark runs for group "
                f"(study={study_hash[:8]}..., trial={trial_hash[:8]}...): "
                f"latencies={[f'{l:.1f}ms' for l in latencies]}, "
                f"aggregated={aggregated_latency:.1f}ms (strategy={latency_aggregation})"
            )

        benchmark_run = representative_run

        # Look up matching trial run
        lookup_key: Tuple[str, str] = (study_hash, trial_hash)
        trial_run = trial_lookup.get(lookup_key)

        if trial_run is None:
            continue

        # Get F1 score from trial run
        f1_score = trial_run.data.metrics.get(objective_metric)
        if f1_score is None:
            continue

        # Look up matching refit run
        refit_run = refit_lookup.get(lookup_key)
        artifact_run = refit_run if refit_run is not None else trial_run

        # Get backbone from trial run
        backbone = (
            trial_run.data.params.get("backbone") or
            trial_run.data.tags.get(tag_keys["backbone_tag"]) or
            trial_run.data.tags.get("code.model", "unknown")
        )

        candidates.append(CandidateInfo(
            benchmark_run=benchmark_run,
            trial_run=trial_run,
            artifact_run=artifact_run,
            refit_run=refit_run,
            f1_score=float(f1_score),
            latency_ms=float(aggregated_latency),
            backbone=backbone,
            study_key_hash=study_hash,
            trial_key_hash=trial_hash,
            benchmark_key=benchmark_key,
            benchmark_runs_count=len(benchmark_runs),
            composite_score=None,
            norm_f1=None,
            norm_latency=None,
        ))

    logger.info(
        f"Found {len(candidates)} candidate(s) with both benchmark and training metrics")

    return candidates


def _compute_composite_scores(
    candidates: List[CandidateInfo],
    weights: SelectionWeights,
) -> None:
    """
    Compute normalized composite scores for all candidates (in-place).

    Args:
        candidates: List of candidate dictionaries (modified in-place).
        weights: Selection weights dictionary.
    """
    f1_scores = [c["f1_score"] for c in candidates]
    latency_scores = [c["latency_ms"] for c in candidates]

    f1_min, f1_max = min(f1_scores), max(f1_scores)
    latency_min, latency_max = min(latency_scores), max(latency_scores)

    f1_range = f1_max - f1_min if f1_max > f1_min else 1.0
    latency_range = latency_max - latency_min if latency_max > latency_min else 1.0

    for candidate in candidates:
        # Normalize F1 (higher is better)
        norm_f1 = (candidate["f1_score"] - f1_min) / f1_range if f1_range > 0 else 0.5

        # Normalize latency (lower is better, so invert)
        norm_latency = 1.0 - (
            (candidate["latency_ms"] - latency_min) / latency_range
        ) if latency_range > 0 else 0.5

        # Composite score
        composite_score = (weights["f1_weight"] * norm_f1) + (weights["latency_weight"] * norm_latency)
        candidate["composite_score"] = composite_score
        candidate["norm_f1"] = norm_f1
        candidate["norm_latency"] = norm_latency


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
    client = create_mlflow_client()

    # Validate inputs
    if benchmark_experiment is None:
        error_msg = "benchmark_experiment is None. Make sure benchmark runs have been executed and logged to MLflow."
        logger.error(error_msg)
        return None

    if not hpo_experiments:
        error_msg = "No HPO experiments found. Make sure HPO runs have been executed and logged to MLflow."
        logger.error(error_msg)
        return None

    # Extract tag keys from config
    tag_keys = _extract_tag_keys(tags_config)

    # Extract selection config
    objective_metric = selection_config["objective"]["metric"]
    f1_weight = float(selection_config["scoring"]["f1_weight"])
    latency_weight = float(selection_config["scoring"]["latency_weight"])
    normalize_weights = bool(selection_config["scoring"].get("normalize_weights", True))
    required_benchmark_metrics = selection_config["benchmark"]["required_metrics"]
    latency_aggregation = selection_config.get("benchmark", {}).get("latency_aggregation", "latest")

    # Normalize weights if needed
    weights = _normalize_selection_weights(f1_weight, latency_weight, normalize_weights)

    logger.info(f"Finding best model from MLflow")
    logger.info(f"  Benchmark experiment: {benchmark_experiment['name']}")
    logger.info(f"  HPO experiments: {len(hpo_experiments)}")
    logger.info(f"  Objective metric: {objective_metric}")
    logger.info(
        f"  Composite weights: F1={weights['f1_weight']:.2f}, Latency={weights['latency_weight']:.2f}")
    
    # Log latency aggregation strategy from config (already extracted above)
    config_source = "config file" if "latency_aggregation" in selection_config.get("benchmark", {}) else "default"
    logger.info(
        f"  Latency aggregation: {latency_aggregation} (from {config_source}, "
        f"applied when multiple benchmark runs exist with same benchmark_key)")

    # Step 1: Query and filter benchmark runs
    valid_benchmark_runs = _query_and_filter_benchmark_runs(
        client, benchmark_experiment, required_benchmark_metrics, tag_keys
    )

    if not valid_benchmark_runs:
        logger.warning("No valid benchmark runs found")
        return None

    # Step 2: Preload trial and refit runs
    trial_lookup, refit_lookup = _preload_trial_and_refit_runs(
        client, hpo_experiments, tag_keys
    )

    if not trial_lookup:
        logger.warning("No trial runs found in HPO experiments")
        return None

    # Step 2.5: Group benchmark runs by (study_key_hash, trial_key_hash, benchmark_key)
    # This deduplicates multiple benchmark runs with same config
    from collections import defaultdict

    benchmark_groups = defaultdict(list)
    for benchmark_run in valid_benchmark_runs:
        study_hash = benchmark_run.data.tags[tag_keys["study_key_tag"]]
        trial_hash = benchmark_run.data.tags[tag_keys["trial_key_tag"]]
        
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

    # Step 3: Build candidates
    candidates = _build_candidates(
        benchmark_groups, trial_lookup, refit_lookup, tag_keys, objective_metric, latency_aggregation
    )

    if not candidates:
        logger.warning("No candidates found with both benchmark and training metrics")
        return None

    # Step 4: Compute composite scores
    _compute_composite_scores(candidates, weights)

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

"""
@meta
name: benchmarking_workflow
type: utility
domain: benchmarking
responsibility:
  - Orchestrate benchmarking of champion models
  - Select champions from HPO experiments
  - Coordinate artifact acquisition and benchmark execution
inputs:
  - HPO experiments
  - Selection and benchmark configuration
  - Data configuration
outputs:
  - Benchmark results per champion
  - MLflow benchmark runs
tags:
  - workflow
  - benchmarking
  - mlflow
ci:
  runnable: false
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Benchmarking workflow for champions."""

from pathlib import Path
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from mlflow.tracking import MlflowClient

from evaluation.selection.trial_finder import select_champions_for_backbones
from evaluation.benchmarking.orchestrator import (
    benchmark_champions,
    filter_missing_benchmarks,
    get_benchmark_run_mode,
)
from evaluation.selection.experiment_discovery import discover_benchmark_experiment
from evaluation.selection.artifact_acquisition import acquire_best_model_checkpoint
from evaluation.selection.workflows.utils import resolve_test_data_path
from infrastructure.naming.mlflow.hpo_keys import (
    compute_data_fingerprint,
    compute_eval_fingerprint,
)
from infrastructure.tracking.mlflow.hash_utils import derive_eval_config
from common.shared.platform_detection import detect_platform
from common.shared.yaml_utils import load_yaml
from common.shared.logging_utils import get_logger

logger = get_logger(__name__)


def run_benchmarking_workflow(
    hpo_experiments: Dict[str, Dict[str, str]],
    selection_config: Dict[str, Any],
    benchmark_config: Dict[str, Any],
    data_config: Dict[str, Any],
    hpo_config: Dict[str, Any],
    root_dir: Path,
    config_dir: Path,
    experiment_name: str,
    mlflow_client: "MlflowClient",
    benchmark_experiment: Optional[Dict[str, str]] = None,
    benchmark_tracker: Optional[Any] = None,  # Type depends on tracker implementation
    backup_enabled: bool = True,
    backup_to_drive: Optional[Callable[[Path, bool], bool]] = None,
    restore_from_drive: Optional[Callable[[Path, bool], bool]] = None,
    in_colab: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Run complete benchmarking workflow for champions.
    
    Steps:
    1. Select champions per backbone
    2. Filter missing benchmarks (idempotency)
    3. Resolve test data path
    4. Acquire checkpoints for champions
    5. Run benchmarking
    6. Return benchmarked champions with checkpoint paths for reuse
    
    Args:
        hpo_experiments: Dict mapping backbone -> experiment info (name, id)
        selection_config: Selection configuration dict
        benchmark_config: Benchmark configuration dict
        data_config: Data configuration dict
        hpo_config: HPO configuration dict
        root_dir: Project root directory
        config_dir: Config directory
        experiment_name: Experiment name
        mlflow_client: MLflow client instance
        benchmark_experiment: Optional benchmark experiment (will discover if None)
        benchmark_tracker: Optional MLflowBenchmarkTracker instance
        backup_enabled: Whether backup is enabled
        backup_to_drive: Function to backup files to Drive
        restore_from_drive: Function to restore files from Drive
        in_colab: Whether running in Colab
        
    Returns:
        Dict mapping backbone -> champion data with checkpoint_path for reuse
    """
    logger.info("Running benchmarking workflow on champions")
    
    # Step 1: Select champions per backbone
    backbone_values = list(hpo_experiments.keys())
    logger.info(f"Selecting champions for {len(hpo_experiments)} backbone(s)")
    
    champions = select_champions_for_backbones(
        backbone_values=backbone_values,
        hpo_experiments=hpo_experiments,
        selection_config=selection_config,
        mlflow_client=mlflow_client,
    )
    
    if not champions:
        logger.warning("No champions found - skipping benchmarking")
        return {}
    
    # Step 2: Extract fingerprints for benchmark key building
    data_fp = compute_data_fingerprint(data_config)
    train_config = hpo_config.get("train", {})
    eval_config = derive_eval_config(train_config, hpo_config)
    eval_fp = compute_eval_fingerprint(eval_config)
    
    # Step 3: Discover or use provided benchmark experiment
    if benchmark_experiment is None:
        benchmark_experiment = discover_benchmark_experiment(
            experiment_name=experiment_name,
            mlflow_client=mlflow_client,
            create_if_missing=True,
        )
    
    # Step 4: Filter missing benchmarks
    run_mode = get_benchmark_run_mode(benchmark_config, hpo_config)
    environment = detect_platform()
    
    # benchmark_experiment is guaranteed to be set at this point
    assert benchmark_experiment is not None, "benchmark_experiment should be set by now"
    
    champions_to_benchmark = filter_missing_benchmarks(
        champions=champions,
        benchmark_experiment=benchmark_experiment,
        benchmark_config=benchmark_config,
        data_fingerprint=data_fp,
        eval_fingerprint=eval_fp,
        root_dir=root_dir,
        environment=environment,
        mlflow_client=mlflow_client,
        run_mode=run_mode,
    )
    
    skipped_count = len(champions) - len(champions_to_benchmark)
    if skipped_count > 0:
        logger.info(f"Skipping {skipped_count} already-benchmarked champion(s)")
    
    if not champions_to_benchmark:
        logger.info("All champions already benchmarked")
        return {}
    
    # Step 5: Resolve test data path
    test_data_path = resolve_test_data_path(benchmark_config, data_config, config_dir)
    if not test_data_path or not test_data_path.exists():
        logger.warning("Test data not found - skipping benchmarking")
        return {}
    
    # Step 6: Extract benchmark parameters
    benchmark_params = benchmark_config.get("benchmarking", {})
    benchmark_batch_sizes = benchmark_params.get("batch_sizes", [1])
    benchmark_iterations = benchmark_params.get("iterations", 10)
    benchmark_warmup = benchmark_params.get("warmup_iterations", 10)
    benchmark_max_length = benchmark_params.get("max_length", 512)
    benchmark_device = benchmark_params.get("device")
    
    # Step 7: Acquire checkpoints for champions
    acquisition_config = load_yaml(config_dir / "artifact_acquisition.yaml")
    acquisition_config = acquisition_config.copy()
    acquisition_config["output_base_dir"] = "artifacts"
    
    for backbone, champion_data in champions_to_benchmark.items():
        champion = champion_data["champion"]
        run_id = champion.get("run_id")
        if not run_id:
            continue
        
        best_run_info = {
            "run_id": champion.get("refit_run_id") or run_id,
            "refit_run_id": champion.get("refit_run_id"),
            "trial_run_id": champion.get("trial_run_id"),
            "sweep_run_id": champion.get("sweep_run_id"),
            "study_key_hash": champion.get("study_key_hash"),
            "trial_key_hash": champion.get("trial_key_hash"),
            "backbone": backbone,
        }
        
        checkpoint_dir = acquire_best_model_checkpoint(
            best_run_info=best_run_info,
            root_dir=root_dir,
            config_dir=config_dir,
            acquisition_config=acquisition_config,
            selection_config=selection_config,
            platform=detect_platform(),
            restore_from_drive=restore_from_drive,
            drive_store=backup_to_drive,
            in_colab=in_colab,
        )
        
        champion["checkpoint_path"] = Path(checkpoint_dir) if checkpoint_dir else None
    
    # Step 8: Filter out champions without checkpoints
    champions_to_benchmark = {
        k: v for k, v in champions_to_benchmark.items()
        if v["champion"].get("checkpoint_path")
    }
    
    if not champions_to_benchmark:
        logger.warning("No champions with checkpoints available for benchmarking")
        return {}
    
    # Step 9: Run benchmarking
    benchmark_results = benchmark_champions(
        champions=champions_to_benchmark,
        test_data_path=test_data_path,
        root_dir=root_dir,
        environment=environment,
        data_config=data_config,
        hpo_config=hpo_config,
        benchmark_config=benchmark_config,
        benchmark_experiment=benchmark_experiment,
        benchmark_batch_sizes=benchmark_batch_sizes,
        benchmark_iterations=benchmark_iterations,
        benchmark_warmup=benchmark_warmup,
        benchmark_max_length=benchmark_max_length,
        benchmark_device=benchmark_device,
        benchmark_tracker=benchmark_tracker,
        backup_enabled=backup_enabled,
        backup_to_drive=backup_to_drive,
        ensure_restored_from_drive=restore_from_drive,
        mlflow_client=mlflow_client,
    )
    
    logger.info(f"Benchmarking complete for {len(champions_to_benchmark)} champion(s)")
    
    # Step 10: Return champions with checkpoint paths for reuse
    return champions_to_benchmark



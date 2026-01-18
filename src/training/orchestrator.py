"""
@meta
name: training_orchestrator
type: script
domain: training
responsibility:
  - Orchestrate training execution
  - Set up MLflow tracking
  - Handle distributed training context
  - Manage training run lifecycle
inputs:
  - Training configuration
  - Training arguments
outputs:
  - Trained model checkpoint
  - Training metrics (via MLflow)
tags:
  - orchestration
  - training
  - mlflow
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Training orchestration logic."""

import os
import argparse
from pathlib import Path

from training.config import build_training_config, resolve_distributed_config
from data.loaders import load_dataset
from training.core.trainer import train_model
from training.logging import log_metrics
from training.core.utils import set_seed
from training.execution.distributed import (
    create_run_context,
    init_process_group_if_needed,
)
from infrastructure.platform.adapters import get_platform_adapter
from common.shared.argument_parsing import validate_config_dir


def log_training_parameters(config: dict, logging_adapter) -> None:
    """Log training parameters using platform adapter."""
    params = {
        "learning_rate": config["training"].get("learning_rate"),
        "batch_size": config["training"].get("batch_size"),
        "dropout": config["model"].get("dropout"),
        "weight_decay": config["training"].get("weight_decay"),
        "epochs": config["training"].get("epochs"),
        "backbone": config["model"].get("backbone"),
    }
    logging_adapter.log_params(
        {k: v for k, v in params.items() if v is not None})


def run_training(args: argparse.Namespace, prebuilt_config: dict | None = None) -> None:
    """
    Run a single training process (rank-agnostic).

    This function is used for both single-process training and each rank in
    a DDP run. It is intentionally unaware of world_size; DDP setup is
    handled via `training.distributed`.

    Args:
        args: Parsed command-line arguments.
        prebuilt_config: Optional pre-built configuration dictionary.
    """
    config_dir = validate_config_dir(args.config_dir)

    config = prebuilt_config or build_training_config(args, config_dir)

    # Optionally offset random seed by rank in distributed runs.
    rank_env = os.getenv("RANK")
    if rank_env is not None and "training" in config:
        try:
            rank = int(rank_env)
        except ValueError:
            rank = 0
        base_seed = config["training"].get("random_seed")
        if base_seed is not None:
            config["training"]["random_seed"] = int(base_seed) + rank

    # Resolve distributed config, create run context, and initialize process
    # group if needed (DDP). Single-process runs will get a SingleProcessContext.
    dist_cfg = resolve_distributed_config(config)
    context = create_run_context(dist_cfg)
    init_process_group_if_needed(context)

    seed = config["training"].get("random_seed")
    set_seed(seed)

    dataset = load_dataset(args.data_asset)

    # Get platform adapter for output paths, logging, and MLflow context
    platform_adapter = get_platform_adapter(
        default_output_dir=Path("./outputs"))
    output_resolver = platform_adapter.get_output_path_resolver()
    logging_adapter = platform_adapter.get_logging_adapter()
    mlflow_context = platform_adapter.get_mlflow_context_manager()

    # Resolve output directory using platform adapter
    output_dir = output_resolver.resolve_output_path(
        "checkpoint", default=Path("./outputs")
    )
    output_dir = output_resolver.ensure_output_directory(output_dir)

    # CRITICAL: Set up MLflow BEFORE using context manager
    # This ensures tracking URI and experiment are set, and child runs are created correctly
    import sys

    # Use SSOT for MLflow setup (handles Azure ML compatibility, fallback, timeout)
    from infrastructure.tracking.mlflow.setup import setup_mlflow
    import mlflow

    experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME")
    if experiment_name:
        tracking_uri = setup_mlflow(
            experiment_name=experiment_name,
            fallback_to_local=True,
        )
        print(
            f"  [Training] Set MLflow tracking URI: {tracking_uri[:50]}...",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"  [Training] Set MLflow experiment: {experiment_name}",
            file=sys.stderr,
            flush=True,
        )

    # Check if we should use an existing run (for refit) or create a child run (for HPO trials)
    use_run_id = os.environ.get(
        "MLFLOW_RUN_ID") or os.environ.get("MLFLOW_USE_RUN_ID")
    parent_run_id = os.environ.get("MLFLOW_PARENT_RUN_ID")
    trial_number = os.environ.get("MLFLOW_TRIAL_NUMBER", "unknown")
    
    # DEBUG: Log environment variables for troubleshooting
    print(f"  [Training Orchestrator] MLflow environment check:", file=sys.stderr, flush=True)
    print(f"    MLFLOW_RUN_ID: {use_run_id[:12] if use_run_id else 'None'}...", file=sys.stderr, flush=True)
    print(f"    MLFLOW_PARENT_RUN_ID: {parent_run_id[:12] if parent_run_id else 'None'}...", file=sys.stderr, flush=True)
    print(f"    MLFLOW_CHILD_RUN_ID: {os.environ.get('MLFLOW_CHILD_RUN_ID', 'None')[:12] if os.environ.get('MLFLOW_CHILD_RUN_ID') else 'None'}...", file=sys.stderr, flush=True)
    print(f"    MLFLOW_TRIAL_NUMBER: {trial_number}", file=sys.stderr, flush=True)
    fold_idx = os.environ.get("MLFLOW_FOLD_IDX")

    # Track whether we started a run directly (needed for cleanup)
    started_run_directly = False
    # Track if we started an existing run (refit mode) - don't end it here
    started_existing = False

    if use_run_id:
        # Check if this is final training (no parent_run_id) vs refit mode (has parent_run_id)
        # For final training: start run actively so artifacts can be logged
        # For refit mode: don't start run (keep it RUNNING for parent to manage)
        is_final_training = parent_run_id is None

        if is_final_training:
            # Final training: start the run actively so artifacts can be logged
            print(
                f"  [Training] Using existing run: {use_run_id[:12]}... (final training)",
                file=sys.stderr,
                flush=True,
            )
            mlflow.start_run(run_id=use_run_id)
            started_run_directly = True
            started_existing = False  # Not refit mode - we'll end the run normally
            print(
                "  [Training] ✓ Started run for artifact logging",
                file=sys.stderr,
                flush=True,
            )
        else:
            # Refit mode: don't start an active run context - use client API instead
            # This prevents MLflow from auto-ending the run when subprocess exits
            print(
                f"  [Training] Using existing run: {use_run_id[:12]}... (refit mode)",
                file=sys.stderr,
                flush=True,
            )
            # Don't start an active run - we'll log via client API instead
            # This keeps the run RUNNING until parent process explicitly terminates it
            started_run_directly = False  # Not using active run
            started_existing = True       # Mark as existing run (refit mode)
            print(
                "  [Training] ✓ Will log to existing run via client API (run stays RUNNING)",
                file=sys.stderr,
                flush=True,
            )

    elif parent_run_id:
        # Try to build systematic run name using naming policy
        run_name = None
        trial_display = f"trial {trial_number}"
        if fold_idx is not None:
            trial_display = f"trial {trial_number}, fold {fold_idx}"

        # Set environment variables for potential use by mlflow_context fallback
        os.environ["MLFLOW_TRIAL_NUMBER"] = str(trial_number)
        if fold_idx is not None:
            os.environ["MLFLOW_FOLD_IDX"] = str(fold_idx)

        # Use consolidated run name building with fallback
        from training.execution.run_names import build_training_run_name_with_fallback

        # Determine process type: hpo_trial_fold if fold_idx, otherwise hpo_trial
        process_type = "hpo_trial_fold" if fold_idx is not None else "hpo_trial"

        # Use resolve_project_paths_with_fallback() to consolidate path resolution
        # Check environment variable first, then use consolidated helper
        if os.environ.get("CONFIG_DIR"):
            config_dir = Path(os.environ.get("CONFIG_DIR"))
        else:
            # Use resolve_project_paths_with_fallback() for standardized fallback logic
            from infrastructure.paths.utils import resolve_project_paths_with_fallback
            _, config_dir = resolve_project_paths_with_fallback(config_dir=None)

        run_name = build_training_run_name_with_fallback(
            process_type=process_type,
            trial_number=trial_number,
            fold_idx=fold_idx,
            parent_run_id=parent_run_id,
            config_dir=config_dir,
        )

        print(
            f"  [Training] Creating child run with parent: {parent_run_id[:12]}... ({trial_display})",
            file=sys.stderr,
            flush=True,
        )

        # Use consolidated child run creation
        from training.execution.mlflow_setup import create_training_child_run

        experiment_name = os.environ.get("MLFLOW_EXPERIMENT_NAME", "default")
        try:
            child_run_id, _ = create_training_child_run(
                experiment_name=experiment_name,
                run_name=run_name,
                parent_run_id=parent_run_id,
                trial_number=trial_number,
                fold_idx=fold_idx,
            )
            # Start the child run
            mlflow.start_run(run_id=child_run_id)
            started_run_directly = True
            print(
                f"  [Training] ✓ Started child run",
                file=sys.stderr,
                flush=True,
            )
        except Exception as e:
            print(
                f"  [Training] Error creating child run: {e}",
                file=sys.stderr,
                flush=True,
            )
            import traceback
            traceback.print_exc()
            # Fallback to independent run only if run_name is available
            # If run_name is None/empty, MLflow will auto-generate a name (e.g., bright_peach_xxx)
            # This should be avoided - raise error instead
            if not run_name:
                error_msg = (
                    f"  [Training] Cannot create fallback run: run_name is None/empty. "
                    f"Parent run ID was: {parent_run_id[:12] if parent_run_id else 'None'}..."
                )
                print(error_msg, file=sys.stderr, flush=True)
                raise RuntimeError(
                    f"Failed to create child run and cannot create fallback: "
                    f"run_name is None/empty. Original error: {e}"
                ) from e
            # Fallback to independent run with explicit name
            print(
                f"  [Training] WARNING: Creating independent run as fallback "
                f"(parent was: {parent_run_id[:12] if parent_run_id else 'None'}...)",
                file=sys.stderr,
                flush=True,
            )
            # CRITICAL: Double-check run_name before calling mlflow.start_run()
            # Even though we validated earlier, be extra defensive here
            if not run_name or not run_name.strip():
                error_msg = (
                    f"CRITICAL: Cannot create fallback run: run_name became None/empty. "
                    f"This would cause MLflow to auto-generate a name like 'sad_toe_8qbllbws'. "
                    f"run_name={run_name}, MLFLOW_RUN_NAME={os.environ.get('MLFLOW_RUN_NAME')}"
                )
                print(error_msg, file=sys.stderr, flush=True)
                import traceback
                print(f"Call stack:\n{''.join(traceback.format_stack()[-10:-1])}", file=sys.stderr, flush=True)
                raise RuntimeError(
                    f"Cannot create fallback run: run_name is None or empty. "
                    f"This would cause MLflow to auto-generate a name."
                )
            print(f"  [Training] Fallback: About to call mlflow.start_run(run_name='{run_name}')", file=sys.stderr, flush=True)
            mlflow.start_run(run_name=run_name)
            started_run_directly = True
            print(f"  [Training] Fallback: ✓ Successfully created run with name '{run_name}'", file=sys.stderr, flush=True)
    else:
        # No parent run ID - check if we're in HPO context
        # In HPO, we should ALWAYS have a parent run ID set via MLFLOW_PARENT_RUN_ID
        # If it's missing, this is an error condition, not a normal case
        mlflow_parent_env = os.environ.get("MLFLOW_PARENT_RUN_ID")
        mlflow_child_env = os.environ.get("MLFLOW_CHILD_RUN_ID")
        
        print(f"  [Training Orchestrator] No use_run_id or parent_run_id parameter - checking environment", file=sys.stderr, flush=True)
        print(f"    MLFLOW_PARENT_RUN_ID from env: {mlflow_parent_env[:12] if mlflow_parent_env else 'None'}...", file=sys.stderr, flush=True)
        print(f"    MLFLOW_CHILD_RUN_ID from env: {mlflow_child_env[:12] if mlflow_child_env else 'None'}...", file=sys.stderr, flush=True)
        
        if not mlflow_parent_env and not mlflow_child_env:
            # This should not happen in HPO - raise error instead of creating auto-generated run
            import traceback
            error_msg = (
                f"  [Training] CRITICAL: No parent run ID found. "
                f"This will cause MLflow to auto-generate a run name like 'dynamic_duck_32f4qb48'. "
                f"MLFLOW_PARENT_RUN_ID={mlflow_parent_env}, "
                f"MLFLOW_CHILD_RUN_ID={mlflow_child_env}, "
                f"parent_run_id parameter={parent_run_id}"
            )
            print(error_msg, file=sys.stderr, flush=True)
            print("  [Training Orchestrator] Call stack:", file=sys.stderr, flush=True)
            for line in traceback.format_stack()[-10:-1]:
                print(f"    {line.rstrip()}", file=sys.stderr, flush=True)
            raise RuntimeError(
                f"Cannot create MLflow run: No parent run ID found. "
                f"In HPO context, MLFLOW_PARENT_RUN_ID or MLFLOW_CHILD_RUN_ID must be set. "
                f"This prevents auto-generated run names like 'dynamic_duck_32f4qb48'."
            )
        
        # Use context manager as normal (should find existing run via env vars)
        print(f"  [Training Orchestrator] Calling mlflow_context.get_context()", file=sys.stderr, flush=True)
        context_mgr = mlflow_context.get_context()
        print(f"  [Training Orchestrator] Entering context manager", file=sys.stderr, flush=True)
        context_mgr.__enter__()

    try:
        if context.is_main_process():
            log_training_parameters(config, logging_adapter)
        metrics = train_model(config, dataset, output_dir, context=context)
        if context.is_main_process():
            log_metrics(output_dir, metrics, logging_adapter)
    finally:
        # End the run if we started it directly
        # EXCEPTION: For refit runs (started_existing=True), we don't have an active run
        # so there's nothing to end - the parent process will mark it FINISHED after artifact upload
        if started_existing:
            # Refit mode: No active run to end - run stays RUNNING until parent terminates it
            print(f"  [Training] Refit run remains RUNNING (will be marked FINISHED after artifacts)",
                  file=sys.stderr, flush=True)
        elif started_run_directly:
            # Non-refit mode: End the run normally
            mlflow.end_run()
            if parent_run_id:
                print(f"  [Training] Ended child run",
                      file=sys.stderr, flush=True)
            else:
                print(f"  [Training] Ended independent run",
                      file=sys.stderr, flush=True)
        else:
            # Use context manager's exit
            context_mgr.__exit__(None, None, None)

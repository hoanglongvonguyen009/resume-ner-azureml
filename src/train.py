"""
Training script for Resume NER model.

Implements a minimal token-classification training/eval loop using transformers.

This module also acts as the central launcher for single- and multi-GPU
training. It decides whether to run in:

- single-process mode (CPU or single GPU), or
- multi-process DDP mode (one process per GPU)

based on `config/train.yaml` and the available hardware. Notebooks and higher-
level orchestration only ever call this entrypoint; they do not manage ranks.
"""

import argparse
import os
from pathlib import Path

import torch.multiprocessing as mp

from platform_adapters import get_platform_adapter
from training.config import build_training_config, resolve_distributed_config
from training.data import load_dataset
from training.trainer import train_model
from training.logging import log_metrics
from training.utils import set_seed
from training.distributed import (
    detect_hardware,
    should_use_ddp,
    create_run_context,
    init_process_group_if_needed,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Train Resume NER model")
    parser.add_argument(
        "--data-asset",
        type=str,
        required=True,
        help="Azure ML data asset path or local dataset path",
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        required=True,
        help="Path to configuration directory",
    )
    parser.add_argument(
        "--backbone",
        type=str,
        required=True,
        help="Model backbone name (e.g., 'distilbert')",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        help="Learning rate override",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size override",
    )
    parser.add_argument(
        "--dropout",
        type=float,
        default=None,
        help="Dropout override",
    )
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=None,
        help="Weight decay override",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Epochs override",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed",
    )
    parser.add_argument(
        "--early-stopping-enabled",
        type=str,
        default=None,
        help="Enable early stopping ('true'/'false')",
    )
    parser.add_argument(
        "--use-combined-data",
        type=str,
        default=None,
        help="Use combined train+validation ('true'/'false')",
    )
    parser.add_argument(
        "--fold-idx",
        type=int,
        default=None,
        help="Fold index (0 to k-1) for cross-validation training",
    )
    parser.add_argument(
        "--fold-splits-file",
        type=str,
        default=None,
        help="Path to JSON file containing fold splits",
    )
    parser.add_argument(
        "--k-folds",
        type=int,
        default=None,
        help="Number of folds for cross-validation",
    )
    parser.add_argument(
        "--use-all-data",
        type=str,
        default=None,
        help="Use all data for training without validation split ('true'/'false')",
    )
    return parser.parse_args()


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
    logging_adapter.log_params({k: v for k, v in params.items() if v is not None})


def _run_training(args: argparse.Namespace, prebuilt_config: dict | None = None) -> None:
    """Run a single training process (rank-agnostic).

    This function is used for both single-process training and each rank in
    a DDP run. It is intentionally unaware of world_size; DDP setup is
    handled via `training.distributed`.
    """
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

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
    platform_adapter = get_platform_adapter(default_output_dir=Path("./outputs"))
    output_resolver = platform_adapter.get_output_path_resolver()
    logging_adapter = platform_adapter.get_logging_adapter()
    mlflow_context = platform_adapter.get_mlflow_context_manager()

    # Resolve output directory using platform adapter
    output_dir = output_resolver.resolve_output_path(
        "checkpoint", default=Path("./outputs")
    )
    output_dir = output_resolver.ensure_output_directory(output_dir)

    # Use platform-appropriate MLflow context manager
    with mlflow_context.get_context():
        if context.is_main_process():
            log_training_parameters(config, logging_adapter)
        metrics = train_model(config, dataset, output_dir, context=context)
        if context.is_main_process():
            log_metrics(output_dir, metrics, logging_adapter)


def _ddp_worker(local_rank: int, world_size: int, args: argparse.Namespace) -> None:
    """DDP worker entrypoint used with torch.multiprocessing.spawn.

    This sets rank-related environment variables and then delegates to
    `_run_training`, which performs DDP initialization and training.
    """
    os.environ.setdefault("WORLD_SIZE", str(world_size))
    os.environ.setdefault("RANK", str(local_rank))
    os.environ.setdefault("LOCAL_RANK", str(local_rank))
    # Ensure env:// rendezvous has required address/port when using spawn.
    os.environ.setdefault("MASTER_ADDR", "127.0.0.1")
    os.environ.setdefault("MASTER_PORT", "29500")

    _run_training(args)


def main() -> None:
    """Main training entry point."""
    args = parse_arguments()

    # Build config once here to decide between single-process and DDP modes.
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    config = build_training_config(args, config_dir)
    dist_cfg = resolve_distributed_config(config)
    _, device_count = detect_hardware()

    # If already running under torchrun (WORLD_SIZE set), do not spawn again.
    world_size_env = os.getenv("WORLD_SIZE")

    if world_size_env is None and should_use_ddp(dist_cfg, device_count):
        # Decide world_size: explicit integer from config or all visible GPUs.
        world_size = dist_cfg.world_size or device_count
        if world_size < 2:
            # Fallback to single-process if config/hardware are inconsistent.
            _run_training(args, prebuilt_config=config)
            return

        mp.spawn(
            _ddp_worker,
            nprocs=world_size,
            args=(world_size, args),
        )
    else:
        # Single-process path (CPU, single GPU, or torchrun-managed ranks).
        _run_training(args, prebuilt_config=config)


if __name__ == "__main__":
    main()

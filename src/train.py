"""
Training script for Resume NER model.

Implements a minimal token-classification training/eval loop using transformers.
"""

import argparse
from pathlib import Path

from platform_adapters import get_platform_adapter
from training.config import build_training_config
from training.data import load_dataset
from training.trainer import train_model
from training.logging import log_metrics
from training.utils import set_seed


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
    logging_adapter.log_params(
        {k: v for k, v in params.items() if v is not None})


def main() -> None:
    """Main training entry point."""
    args = parse_arguments()

    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")

    config = build_training_config(args, config_dir)

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
        "checkpoint", default=Path("./outputs"))
    output_dir = output_resolver.ensure_output_directory(output_dir)

    # Use platform-appropriate MLflow context manager
    with mlflow_context.get_context():
        log_training_parameters(config, logging_adapter)
        metrics = train_model(config, dataset, output_dir)
        log_metrics(output_dir, metrics, logging_adapter)


if __name__ == "__main__":
    main()

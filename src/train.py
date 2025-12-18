"""
Training script for Resume NER model.

Implements a minimal token-classification training/eval loop using transformers.
"""

import argparse
import os
from pathlib import Path

import mlflow

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


def log_training_parameters(config: dict) -> None:
    """Log training parameters to MLflow."""
    params = {
        "learning_rate": config["training"].get("learning_rate"),
        "batch_size": config["training"].get("batch_size"),
        "dropout": config["model"].get("dropout"),
        "weight_decay": config["training"].get("weight_decay"),
        "epochs": config["training"].get("epochs"),
        "backbone": config["model"].get("backbone"),
    }
    mlflow.log_params({k: v for k, v in params.items() if v is not None})


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

    # Azure ML automatically sets AZURE_ML_OUTPUT_<output_name> for each named output.
    # For a named output called "checkpoint", it sets AZURE_ML_OUTPUT_checkpoint.
    # Fall back to AZURE_ML_OUTPUT_DIR for backward compatibility when running locally.
    output_dir = Path(
        os.getenv("AZURE_ML_OUTPUT_checkpoint")
        or os.getenv("AZURE_ML_OUTPUT_DIR", "./outputs")
    )
    # Ensure the output directory exists and always contains at least one file so that
    # Azure ML materialises the named output in the datastore. Without this, an
    # otherwise successful training run that never writes artefacts would result in
    # the `checkpoint` output not existing at all, leading to
    # ScriptExecution.StreamAccess.NotFound when downstream jobs try to mount it.
    output_dir.mkdir(parents=True, exist_ok=True)
    placeholder = output_dir / "checkpoint_placeholder.txt"
    if not placeholder.exists():
        placeholder.write_text(
            "This file ensures the Azure ML 'checkpoint' output is materialised. "
            "Real model weights are saved under the 'checkpoint/' subdirectory."
        )

    # Azure ML automatically creates an MLflow run context for each job.
    # We should NOT call mlflow.start_run() when running in Azure ML, as it creates
    # a nested/separate run, causing metrics to be logged to the wrong run.
    # Detect Azure ML execution by checking for AZURE_ML_* environment variables.
    is_azure_ml_job = any(key.startswith("AZURE_ML_") for key in os.environ.keys())

    if is_azure_ml_job:
        # Running in Azure ML - use the automatically created MLflow run context
        # Do NOT start a new run, just log directly
        log_training_parameters(config)
        metrics = train_model(config, dataset, output_dir)
        log_metrics(output_dir, metrics)
    else:
        # Local execution - start our own MLflow run
        with mlflow.start_run():
            log_training_parameters(config)
            metrics = train_model(config, dataset, output_dir)
            log_metrics(output_dir, metrics)


if __name__ == "__main__":
    main()
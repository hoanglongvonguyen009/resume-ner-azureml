"""
Training script for Resume NER model.

This script trains a Named Entity Recognition model on resume data.
It is designed to run as an Azure ML job and accepts hyperparameters
via command-line arguments.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for training.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
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
        help="Model backbone name (e.g., 'distilbert', 'deberta')",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=None,
        help="Learning rate (overrides config if provided)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size (overrides config if provided)",
    )
    parser.add_argument(
        "--dropout",
        type=float,
        default=None,
        help="Dropout rate (overrides config if provided)",
    )
    parser.add_argument(
        "--weight-decay",
        type=float,
        default=None,
        help="Weight decay (overrides config if provided)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Number of training epochs (overrides config if provided)",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--early-stopping-enabled",
        type=str,
        default=None,
        help="Enable early stopping ('true' or 'false')",
    )
    parser.add_argument(
        "--use-combined-data",
        type=str,
        default=None,
        help="Use combined train+validation data ('true' or 'false')",
    )
    
    return parser.parse_args()


def load_config_file(config_dir: Path, filename: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_dir: Configuration directory path
        filename: Configuration file name
        
    Returns:
        dict: Parsed configuration dictionary
        
    Raises:
        FileNotFoundError: If config file does not exist
    """
    config_path = config_dir / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def build_training_config(args: argparse.Namespace, config_dir: Path) -> Dict[str, Any]:
    """
    Build training configuration from config files and command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        config_dir: Configuration directory path
        
    Returns:
        dict: Complete training configuration
    """
    train_config = load_config_file(config_dir, "train.yaml")
    model_config = load_config_file(config_dir, f"model/{args.backbone}.yaml")
    data_config = load_config_file(config_dir, "data/resume_v1.yaml")
    
    config = {
        "data": data_config,
        "model": model_config,
        "training": train_config["training"].copy(),
    }
    
    if args.learning_rate is not None:
        config["training"]["learning_rate"] = args.learning_rate
    
    if args.batch_size is not None:
        config["training"]["batch_size"] = args.batch_size
    
    if args.dropout is not None:
        config["model"]["dropout"] = args.dropout
    
    if args.weight_decay is not None:
        config["training"]["weight_decay"] = args.weight_decay
    
    if args.epochs is not None:
        config["training"]["epochs"] = args.epochs
    
    if args.random_seed is not None:
        config["training"]["random_seed"] = args.random_seed
    
    if args.early_stopping_enabled is not None:
        enabled = args.early_stopping_enabled.lower() == "true"
        config["training"]["early_stopping"]["enabled"] = enabled
    
    if args.use_combined_data is not None:
        config["data"]["use_combined_data"] = args.use_combined_data.lower() == "true"
    
    return config


def load_dataset(data_path: str) -> Dict[str, Any]:
    """
    Load dataset from Azure ML data asset or local path.
    
    Args:
        data_path: Path to dataset (Azure ML datastore URI or local path)
        
    Returns:
        dict: Dataset dictionary with 'train' and 'validation' keys
        
    Raises:
        FileNotFoundError: If dataset files not found
    """
    data_path_obj = Path(data_path)
    
    if data_path_obj.exists():
        train_file = data_path_obj / "train.json"
        val_file = data_path_obj / "validation.json"
        
        if not train_file.exists():
            raise FileNotFoundError(f"Training file not found: {train_file}")
        
        with open(train_file, "r", encoding="utf-8") as f:
            train_data = json.load(f)
        
        val_data = []
        if val_file.exists():
            with open(val_file, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        
        return {
            "train": train_data,
            "validation": val_data,
        }
    
    raise FileNotFoundError(f"Dataset path not found: {data_path}")


def train_model(config: Dict[str, Any], dataset: Dict[str, Any], output_dir: Path) -> None:
    """
    Train the NER model with given configuration and dataset.
    
    Args:
        config: Training configuration dictionary
        dataset: Dataset dictionary
        output_dir: Output directory for checkpoints and logs
        
    Raises:
        NotImplementedError: Training logic to be implemented
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    checkpoint_path = output_dir / "checkpoint"
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    
    placeholder_file = checkpoint_path / "model.pt"
    placeholder_file.write_text("Placeholder checkpoint")


def main() -> None:
    """
    Main training entry point.
    """
    args = parse_arguments()
    
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    config = build_training_config(args, config_dir)
    
    dataset = load_dataset(args.data_asset)
    
    output_dir = Path(os.getenv("AZURE_ML_OUTPUT_DIR", "./outputs"))
    checkpoint_dir = output_dir / "checkpoint"
    
    train_model(config, dataset, checkpoint_dir)


if __name__ == "__main__":
    main()


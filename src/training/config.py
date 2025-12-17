"""Configuration loading and building utilities."""

from pathlib import Path
from typing import Dict, Any
import argparse

from shared.yaml_utils import load_yaml


def load_config_file(config_dir: Path, filename: str) -> Dict[str, Any]:
    """
    Load configuration file from directory.

    Args:
        config_dir: Directory containing configuration files.
        filename: Name of the configuration file.

    Returns:
        Dictionary containing configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    config_path = config_dir / filename
    return load_yaml(config_path)


def build_training_config(args: argparse.Namespace, config_dir: Path) -> Dict[str, Any]:
    """
    Build training configuration from files and command-line arguments.

    Args:
        args: Parsed command-line arguments.
        config_dir: Directory containing configuration files.

    Returns:
        Dictionary containing merged configuration.
    """
    train_config = load_config_file(config_dir, "train.yaml")
    model_config = load_config_file(config_dir, f"model/{args.backbone}.yaml")
    data_config = load_config_file(config_dir, "data/resume_v1.yaml")
    
    config = {
        "data": data_config,
        "model": model_config,
        "training": train_config["training"].copy(),
    }
    
    _apply_argument_overrides(args, config)
    
    return config


def _apply_argument_overrides(args: argparse.Namespace, config: Dict[str, Any]) -> None:
    """Apply command-line argument overrides to configuration."""
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


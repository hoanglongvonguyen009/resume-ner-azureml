"""Shared helper functions for creating minimal config files in tests.

This module provides reusable helper functions for creating minimal configuration
files used across tests, eliminating duplication.
"""

from pathlib import Path
from typing import Optional


def create_minimal_training_config(config_dir: Path) -> None:
    """Create minimal training config files needed for training subprocess to start.
    
    Creates:
    - train.yaml with basic training config and early_stopping disabled
    - model/distilbert.yaml with basic model config
    - data/resume_v1.yaml with basic data config
    
    Args:
        config_dir: Directory where config files should be created
        
    Example:
        ```python
        from fixtures.config_helpers import create_minimal_training_config
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        create_minimal_training_config(config_dir)
        ```
    """
    # train.yaml - needs early_stopping section
    train_yaml = config_dir / "train.yaml"
    train_yaml.write_text("""training:
  epochs: 1
  early_stopping:
    enabled: false
""")
    # model/distilbert.yaml
    model_dir = config_dir / "model"
    model_dir.mkdir(exist_ok=True)
    model_yaml = model_dir / "distilbert.yaml"
    model_yaml.write_text("model:\n  name: distilbert\n")
    # data/resume_v1.yaml
    data_dir = config_dir / "data"
    data_dir.mkdir(exist_ok=True)
    data_yaml = data_dir / "resume_v1.yaml"
    data_yaml.write_text("data:\n  name: resume_v1\n")


def create_minimal_data_config(config_dir: Path, dataset_name: str = "test_data", dataset_version: str = "v1") -> None:
    """Create minimal data config file.
    
    Args:
        config_dir: Directory where config file should be created
        dataset_name: Name of the dataset (default: "test_data")
        dataset_version: Version of the dataset (default: "v1")
        
    Example:
        ```python
        from fixtures.config_helpers import create_minimal_data_config
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        create_minimal_data_config(config_dir, dataset_name="my_dataset", dataset_version="v2")
        ```
    """
    data_yaml = config_dir / "data.yaml"
    data_yaml.write_text(f"""dataset_name: {dataset_name}
dataset_version: {dataset_version}
""")


def create_minimal_experiment_config(config_dir: Path, experiment_name: str = "test_experiment") -> None:
    """Create minimal experiment config file.
    
    Args:
        config_dir: Directory where config file should be created
        experiment_name: Name of the experiment (default: "test_experiment")
        
    Example:
        ```python
        from fixtures.config_helpers import create_minimal_experiment_config
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        create_minimal_experiment_config(config_dir, experiment_name="my_experiment")
        ```
    """
    experiment_yaml = config_dir / "experiment.yaml"
    experiment_yaml.write_text(f"""experiment_name: {experiment_name}
""")


def create_minimal_model_config(config_dir: Path, model_name: str = "distilbert") -> None:
    """Create minimal model config file.
    
    Args:
        config_dir: Directory where config file should be created
        model_name: Name of the model (default: "distilbert")
        
    Example:
        ```python
        from fixtures.config_helpers import create_minimal_model_config
        
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        model_dir = config_dir / "model"
        model_dir.mkdir()
        create_minimal_model_config(model_dir, model_name="bert")
        ```
    """
    model_yaml = config_dir / f"{model_name}.yaml"
    model_yaml.write_text(f"""model:
  name: {model_name}
""")


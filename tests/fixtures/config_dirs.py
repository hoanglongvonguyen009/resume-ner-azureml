"""Shared fixtures for creating temporary config directories with YAML files.

This module provides reusable fixtures for creating config directories with
various levels of completeness, eliminating duplication across test modules.
"""

from pathlib import Path
from typing import Dict, Optional

import pytest


def create_config_dir_files(config_dir: Path, files_dict: Dict[str, str]) -> None:
    """Create config files in a directory from a dictionary mapping.
    
    Args:
        config_dir: Directory where config files should be created
        files_dict: Dictionary mapping filenames to YAML content strings
        
    Example:
        ```python
        create_config_dir_files(
            config_dir,
            {
                "paths.yaml": "schema_version: 2\\nbase:\\n  outputs: outputs",
                "naming.yaml": "schema_version: 1\\nseparators:\\n  field: _"
            }
        )
        ```
    """
    config_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files_dict.items():
        (config_dir / filename).write_text(content)


@pytest.fixture
def config_dir_minimal(tmp_path: Path) -> Path:
    """Create a minimal config directory with only essential files.
    
    This fixture creates the most basic config structure needed for tests
    that don't require full configuration. Only includes:
    - paths.yaml (minimal)
    - naming.yaml (minimal)
    - tags.yaml (minimal)
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path to the config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Minimal paths.yaml
    (config_dir / "paths.yaml").write_text("""schema_version: 2
base:
  outputs: "outputs"
outputs:
  hpo: "hpo"
patterns:
  hpo_v2: '{storage_env}/{model}/study-{study8}'
""")
    
    # Minimal naming.yaml
    (config_dir / "naming.yaml").write_text("""schema_version: 1
run_name_templates:
  hpo: 'hpo_{model}_{stage}'
""")
    
    # Minimal tags.yaml
    (config_dir / "tags.yaml").write_text("""project_name: test_project
""")
    
    return config_dir


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a config directory with all commonly required YAML files.
    
    This fixture creates a config directory with files needed for most tests:
    - paths.yaml (with common patterns)
    - naming.yaml (with common templates)
    - tags.yaml (with common tags)
    - mlflow.yaml (minimal)
    - data.yaml (minimal)
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path to the config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # paths.yaml with common patterns
    (config_dir / "paths.yaml").write_text("""schema_version: 2
base:
  outputs: "outputs"
outputs:
  hpo: "hpo"
  benchmarking: "benchmarking"
  final_training: "final_training"
  conversion: "conversion"
patterns:
  hpo_v2: '{storage_env}/{model}/study-{study8}/trial-{trial8}'
  benchmarking_v2: '{storage_env}/{model}/study-{study8}/trial-{trial8}/bench-{bench8}'
  final_training_v2: '{storage_env}/{model}/spec-{spec8}_exec-{exec8}/v{variant}'
  conversion_v2: '{storage_env}/{model}/spec-{spec8}_exec-{exec8}/v{variant}/conv-{conv8}'
  best_config_v2: '{model}/spec-{spec8}'
""")
    
    # naming.yaml with common templates
    (config_dir / "naming.yaml").write_text("""schema_version: 1
separators:
  field: "_"
  component: "-"
  version: "_"
run_name_templates:
  hpo: 'hpo_{model}_{stage}'
  benchmarking: 'benchmarking_{model}_{stage}'
  final_training: 'final_training_{model}_{stage}'
  conversion: 'conversion_{model}_{stage}'
""")
    
    # tags.yaml with common tags
    (config_dir / "tags.yaml").write_text("""schema_version: 1
project_name: test_project
grouping:
  study_key_hash: "code.study_key_hash"
  trial_key_hash: "code.trial_key_hash"
process:
  stage: "code.stage"
  model: "code.model"
  project: "code.project"
""")
    
    # Minimal mlflow.yaml
    (config_dir / "mlflow.yaml").write_text("""experiment_name: test_exp
naming:
  project_name: "resume-ner"
""")
    
    # Minimal data.yaml
    (config_dir / "data.yaml").write_text("""dataset_name: test_data
dataset_version: v1
""")
    
    return config_dir


@pytest.fixture
def config_dir_full(tmp_path: Path) -> Path:
    """Create a full config directory with complete configuration structure.
    
    This fixture creates a config directory with comprehensive YAML files
    including all options and detailed configurations. Use this for tests
    that need complete config validation or integration testing.
    
    Args:
        tmp_path: Pytest temporary directory fixture
        
    Returns:
        Path to the config directory
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Full paths.yaml
    (config_dir / "paths.yaml").write_text("""schema_version: 2
base:
  outputs: "outputs"
outputs:
  hpo: "hpo"
  benchmarking: "benchmarking"
  final_training: "final_training"
  conversion: "conversion"
patterns:
  hpo_v2: "{storage_env}/{model}/study-{study8}/trial-{trial8}"
  benchmarking_v2: "{storage_env}/{model}/study-{study8}/trial-{trial8}/bench-{bench8}"
  final_training_v2: "{storage_env}/{model}/spec-{spec8}_exec-{exec8}/v{variant}"
  conversion_v2: "{storage_env}/{model}/spec-{spec8}_exec-{exec8}/v{variant}/conv-{conv8}"
  best_config_v2: "{model}/spec-{spec8}"
""")
    
    # Full naming.yaml
    (config_dir / "naming.yaml").write_text("""schema_version: 1
separators:
  field: "_"
  component: "-"
  version: "_"
run_names:
  hpo_trial:
    pattern: "{env}_{model}_hpo_trial_study-{study_hash}_t{trial_number}{version}"
    components:
      study_hash:
        length: 8
        source: "study_key_hash"
        default: "unknown"
      trial_number:
        format: "{number}"
        zero_pad: 2
        source: "trial_number"
        default: "unknown"
  final_training:
    pattern: "{env}_{model}_final_training_spec-{spec_hash}_exec-{exec_hash}_v{variant}{version}"
    components:
      spec_hash:
        length: 8
        source: "spec_fp"
        default: "unknown"
      exec_hash:
        length: 8
        source: "exec_fp"
        default: "unknown"
      variant:
        format: "{number}"
        source: "variant"
        default: "1"
version:
  format: "{separator}{number}"
  separator: "_"
""")
    
    # Full mlflow.yaml
    (config_dir / "mlflow.yaml").write_text("""experiment_name: test_exp
naming:
  project_name: "resume-ner"
  tags:
    max_length: 250
    sanitize: true
  run_name:
    max_length: 100
    shorten_fingerprints: true
    auto_increment:
      enabled: true
      processes:
        hpo: true
        benchmarking: true
      format: "{base}.{version}"
""")
    
    # Full tags.yaml
    (config_dir / "tags.yaml").write_text("""schema_version: 1
project_name: test_project
grouping:
  study_key_hash: "code.study_key_hash"
  trial_key_hash: "code.trial_key_hash"
process:
  stage: "code.stage"
  model: "code.model"
  project: "code.project"
""")
    
    # Full data.yaml
    (config_dir / "data.yaml").write_text("""dataset_name: test_data
dataset_version: v1
""")
    
    return config_dir


from __future__ import annotations

"""
@meta
name: shared_yaml_utils
type: utility
domain: shared
responsibility:
  - YAML file loading utilities
  - Parse YAML files with error handling
tags:
  - utility
  - shared
  - file-io
lifecycle:
  status: active
"""

from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(path: Path) -> Dict[str, Any]:
    """
    Load a YAML file from disk.

    Args:
        path: Absolute or relative path to a YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file cannot be parsed as valid YAML.
    """
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)



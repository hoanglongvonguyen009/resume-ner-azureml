"""Shared variant computation for both final_training and hpo.

Generalizes existing variant logic from training.py to support:
- final_training: Uses spec_fp and exec_fp for variant resolution
- hpo: Uses base_name (e.g., "hpo_distilbert") for variant scanning

This module follows DRY principles by reusing existing code patterns.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from common.shared.platform_detection import detect_platform
from infrastructure.paths import build_output_path


def compute_next_variant(
    root_dir: Path,
    config_dir: Path,
    process_type: str,  # "final_training" or "hpo"
    model: str,
    spec_fp: Optional[str] = None,  # Required for final_training
    exec_fp: Optional[str] = None,  # Required for final_training
    base_name: Optional[str] = None,  # For HPO: "hpo_distilbert"
) -> int:
    """
    Compute next available variant number for any process type.
    
    Generalizes existing _compute_next_variant() from training.py
    to support both final_training and hpo.
    
    Args:
        root_dir: Project root directory
        config_dir: Config directory (root_dir / "config")
        process_type: "final_training" or "hpo"
        model: Model backbone name
        spec_fp: Specification fingerprint (final_training only)
        exec_fp: Execution fingerprint (final_training only)
        base_name: Base study name (hpo only, e.g., "hpo_distilbert")
    
    Returns:
        Next available variant number (starts at 1 if none exist)
    """
    existing = find_existing_variants(
        root_dir, config_dir, process_type, model, spec_fp, exec_fp, base_name
    )
    if not existing:
        return 1
    return max(existing) + 1


def find_existing_variants(
    root_dir: Path,
    config_dir: Path,
    process_type: str,
    model: str,
    spec_fp: Optional[str] = None,
    exec_fp: Optional[str] = None,
    base_name: Optional[str] = None,
) -> List[int]:
    """
    Find all existing variant numbers for a process type.
    
    Generalizes existing _find_existing_variant() from training.py.
    
    Args:
        root_dir: Project root directory
        config_dir: Config directory
        process_type: "final_training" or "hpo"
        model: Model backbone name
        spec_fp: Specification fingerprint (final_training only)
        exec_fp: Execution fingerprint (final_training only)
        base_name: Base study name (hpo only)
    
    Returns:
        List of existing variant numbers (sorted)
    """
    if process_type == "final_training":
        # Reuse existing logic from training.py
        return _find_final_training_variants(
            root_dir, config_dir, spec_fp, exec_fp, model
        )
    elif process_type == "hpo":
        # New logic: scan HPO output directories
        return _find_hpo_variants(root_dir, config_dir, model, base_name)
    
    return []


def _find_final_training_variants(
    root_dir: Path,
    config_dir: Path,
    spec_fp: str,
    exec_fp: str,
    model: str,
) -> List[int]:
    """
    Find existing final_training variants using metadata and filesystem scanning.
    
    Reuses existing logic from training.py::_find_existing_variant().
    """
    environment = detect_platform()
    backbone_name = model.split("-")[0] if "-" in model else model
    
    # Try metadata lookup first
    try:
        from infrastructure.metadata.training import find_by_spec_and_env
        
        entries = find_by_spec_and_env(
            root_dir, spec_fp, environment, "final_training"
        )
        if entries:
            variants = [
                e.get("variant", 1)
                for e in entries
                if e.get("exec_fp") == exec_fp
            ]
            if variants:
                return sorted(set(variants))
    except ImportError:
        pass
    
    # Fallback: scan filesystem
    return _scan_final_training_variants(root_dir, config_dir, spec_fp, exec_fp, model)


def _scan_final_training_variants(
    root_dir: Path,
    config_dir: Path,
    spec_fp: str,
    exec_fp: str,
    model: str,
) -> List[int]:
    """
    Scan filesystem for final_training variants.
    
    Reuses existing filesystem scanning logic from training.py.
    """
    environment = detect_platform()
    backbone_name = model.split("-")[0] if "-" in model else model
    
    try:
        from infrastructure.naming import create_naming_context
        
        variants = []
        for variant_num in range(1, 100):  # Reasonable limit
            context = create_naming_context(
                process_type="final_training",
                model=backbone_name,
                spec_fp=spec_fp,
                exec_fp=exec_fp,
                environment=environment,
                variant=variant_num,
            )
            output_dir = build_output_path(root_dir, context, config_dir=config_dir)
            if output_dir.exists():
                variants.append(variant_num)
        
        return sorted(set(variants))
    except Exception:
        pass
    
    return []


def _find_hpo_variants(
    root_dir: Path,
    config_dir: Path,
    model: str,
    base_name: Optional[str],
) -> List[int]:
    """
    Find existing HPO variants by scanning output directories.
    
    Looks for study folders matching:
    - {base_name} (variant 1, implicit)
    - {base_name}_v1, {base_name}_v2, etc.
    
    Args:
        root_dir: Project root directory
        config_dir: Config directory
        model: Model backbone name
        base_name: Base study name (e.g., "hpo_distilbert")
    
    Returns:
        List of existing variant numbers
    """
    if not base_name:
        # If no base_name provided, use default pattern
        backbone_name = model.split("-")[0] if "-" in model else model
        base_name = f"hpo_{backbone_name}"
    
    environment = detect_platform()
    backbone_name = model.split("-")[0] if "-" in model else model
    
    # Build HPO backbone output directory (where study folders are located)
    # HPO structure: outputs/hpo/{environment}/{backbone}/study-{hash} or {study_name}
    try:
        from infrastructure.paths import resolve_output_path
        
        hpo_base_dir = resolve_output_path(root_dir, config_dir, "hpo")
        backbone_dir = hpo_base_dir / environment / backbone_name
        
        if not backbone_dir.exists():
            return []
        
        variants = []
        for item in backbone_dir.iterdir():
            if not item.is_dir():
                continue
            
            folder_name = item.name
            
            # Check for base name (variant 1, implicit)
            # This matches both legacy folders (hpo_distilbert) and v2 folders (study-{hash})
            # but we only count explicit variant suffixes
            if folder_name == base_name:
                variants.append(1)
            # Check for explicit variant suffix (_v1, _v2, etc.)
            elif folder_name.startswith(f"{base_name}_v"):
                try:
                    variant_num = int(folder_name.split("_v")[-1])
                    variants.append(variant_num)
                except ValueError:
                    pass
        
        return sorted(set(variants))
    except Exception:
        # Fallback: return empty list if scanning fails
        return []




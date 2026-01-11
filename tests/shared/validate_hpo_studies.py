"""Shared utility functions for validating hpo_studies dictionary.

These utilities help prevent the indentation bug where only the last backbone's
study was stored in the hpo_studies dictionary.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path


def validate_hpo_studies_dict(
    hpo_studies: Dict[str, Any],
    backbone_values: List[str],
    strict: bool = True,
) -> tuple[bool, Optional[str]]:
    """Validate that hpo_studies dict contains all expected backbones.
    
    Args:
        hpo_studies: Dictionary mapping backbone -> Optuna study.
        backbone_values: List of backbone names that should be in hpo_studies.
        strict: If True, require exact match. If False, allow missing backbones.
    
    Returns:
        Tuple of (is_valid, error_message). is_valid is True if valid, False otherwise.
        error_message is None if valid, otherwise contains error description.
    """
    if not isinstance(hpo_studies, dict):
        return False, f"hpo_studies must be a dict, got {type(hpo_studies)}"
    
    if not isinstance(backbone_values, list):
        return False, f"backbone_values must be a list, got {type(backbone_values)}"
    
    # Check that all backbone_values are in hpo_studies
    missing_backbones = set(backbone_values) - set(hpo_studies.keys())
    if missing_backbones:
        return False, (
            f"Missing backbones in hpo_studies: {missing_backbones}. "
            f"Expected {len(backbone_values)} backbones ({backbone_values}), "
            f"but hpo_studies has {len(hpo_studies)} entries ({list(hpo_studies.keys())}). "
            f"This may indicate the assignment 'hpo_studies[backbone] = study' is outside the loop."
        )
    
    # Check that all studies are not None
    none_studies = [k for k, v in hpo_studies.items() if v is None]
    if none_studies:
        return False, f"Studies are None for backbones: {none_studies}"
    
    # Check for extra backbones (if strict)
    if strict:
        extra_backbones = set(hpo_studies.keys()) - set(backbone_values)
        if extra_backbones:
            return False, f"Unexpected backbones in hpo_studies: {extra_backbones}"
    
    return True, None


def check_notebook_indentation(notebook_path: Path) -> tuple[bool, Optional[str]]:
    """Check notebook for correct indentation of hpo_studies[backbone] = study.
    
    Args:
        notebook_path: Path to notebook file.
    
    Returns:
        Tuple of (is_correct, error_message). is_correct is True if indentation is correct.
    """
    import json
    
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = json.load(f)
    except Exception as e:
        return False, f"Error reading notebook: {e}"
    
    # Find the cell with the loop
    for cell_idx, cell in enumerate(nb['cells']):
        if cell.get('cell_type') != 'code':
            continue
        
        source = ''.join(cell['source'])
        if 'for backbone in backbone_values:' in source and 'hpo_studies[backbone] = study' in source:
            lines = cell['source']
            
            # Find the assignment line
            for i, line in enumerate(lines):
                if 'hpo_studies[backbone] = study' in line:
                    # Check indentation (should be 4 spaces, inside the loop)
                    indent = len(line) - len(line.lstrip())
                    if indent != 4:
                        return False, (
                            f"Cell {cell_idx+1}, line {i+1}: "
                            f"hpo_studies[backbone] = study has incorrect indentation "
                            f"({indent} spaces, expected 4). "
                            f"This will cause only the last backbone's study to be stored."
                        )
                    
                    # Check that it's after the loop starts
                    loop_found = False
                    for j in range(i):
                        if 'for backbone in backbone_values:' in lines[j]:
                            loop_found = True
                            break
                    
                    if not loop_found:
                        return False, (
                            f"Cell {cell_idx+1}, line {i+1}: "
                            f"hpo_studies[backbone] = study found before loop starts."
                        )
                    
                    return True, None
    
    return False, "Could not find cell with 'for backbone in backbone_values:' and 'hpo_studies[backbone] = study'"


"""Naming utility functions for model and backbone names."""

from __future__ import annotations


def extract_short_backbone_name(backbone: str) -> str:
    """
    Extract short backbone name by removing variant suffix.
    
    Examples:
        "distilbert-base-uncased" -> "distilbert"
        "bert-base-uncased" -> "bert"
        "roberta" -> "roberta"
    
    Args:
        backbone: Full backbone name (may include variant suffix)
        
    Returns:
        Short backbone name (base model name)
    """
    if "-" in backbone:
        return backbone.split("-")[0]
    return backbone


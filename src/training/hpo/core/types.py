"""Shared HPO type definitions."""

from typing import Optional, TypedDict


class HPOParentContext(TypedDict):
    """HPO parent run context."""
    hpo_parent_run_id: Optional[str]
    study_key_hash: Optional[str]
    study_family_hash: Optional[str]


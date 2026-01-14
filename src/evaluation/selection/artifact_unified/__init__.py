"""Unified artifact acquisition system.

This package provides a single source of truth for artifact acquisition across all stages.
"""
from evaluation.selection.artifact_unified.acquisition import acquire_artifact
from evaluation.selection.artifact_unified.selectors import (
    select_artifact_run,
    select_artifact_run_from_request,
)
from evaluation.selection.artifact_unified.types import (
    ArtifactKind,
    ArtifactLocation,
    ArtifactRequest,
    ArtifactResult,
    ArtifactSource,
    AvailabilityStatus,
    RunSelectorResult,
)
from evaluation.selection.artifact_unified.validation import validate_artifact

__all__ = [
    "acquire_artifact",
    "select_artifact_run",
    "select_artifact_run_from_request",
    "ArtifactKind",
    "ArtifactLocation",
    "ArtifactRequest",
    "ArtifactResult",
    "ArtifactSource",
    "AvailabilityStatus",
    "RunSelectorResult",
    "validate_artifact",
]


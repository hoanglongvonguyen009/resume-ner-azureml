from __future__ import annotations

"""Artifact types and request/result dataclasses for unified artifact acquisition.

This module defines the core types used throughout the unified artifact acquisition system.
"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class ArtifactKind(str, Enum):
    """Artifact kind identifiers (artifact-identity-driven, not stage-driven)."""
    
    CHECKPOINT = "checkpoint"  # Model checkpoint (PyTorch/HuggingFace)
    METADATA = "metadata"  # Trial/run metadata JSON
    CONFIG = "config"  # Training configuration
    LOGS = "logs"  # Training logs
    METRICS = "metrics"  # Evaluation metrics


class ArtifactSource(str, Enum):
    """Source where artifact was found/acquired."""
    
    LOCAL = "local"  # Local disk
    DRIVE = "drive"  # Google Drive (Colab)
    MLFLOW = "mlflow"  # MLflow tracking server


class AvailabilityStatus(str, Enum):
    """Artifact availability status."""
    
    DECLARED = "declared"  # Tag says available (not verified)
    VERIFIED = "verified"  # Actually exists and validated
    MISSING = "missing"  # Not found
    INVALID = "invalid"  # Found but validation failed


@dataclass
class ArtifactRequest:
    """Request for artifact acquisition.
    
    This is the primary input to the unified acquisition system.
    All artifact requests are artifact-identity-driven (not stage-driven).
    """
    artifact_kind: ArtifactKind
    run_id: str  # MLflow run ID (trial or refit)
    backbone: str
    study_key_hash: Optional[str] = None
    trial_key_hash: Optional[str] = None
    refit_run_id: Optional[str] = None  # If provided, prefer refit run for acquisition
    experiment_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional context


@dataclass
class ArtifactLocation:
    """Location where artifact was found (before acquisition)."""
    source: ArtifactSource
    path: Path
    status: AvailabilityStatus
    metadata: Dict[str, Any] = field(default_factory=dict)  # Source-specific metadata


@dataclass
class ArtifactResult:
    """Result of artifact acquisition."""
    request: ArtifactRequest
    success: bool
    path: Optional[Path] = None  # Local path after acquisition
    source: Optional[ArtifactSource] = None  # Where it was acquired from
    status: Optional[AvailabilityStatus] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # Acquisition metadata
    
    def __post_init__(self) -> None:
        """Validate result consistency."""
        if self.success and not self.path:
            raise ValueError("Successful result must have a path")
        if self.success and not self.source:
            raise ValueError("Successful result must have a source")
        if not self.success and not self.error:
            raise ValueError("Failed result must have an error message")


@dataclass
class RunSelectorResult:
    """Result of run selection (trial→refit mapping).
    
    This is the SSOT for trial→refit mapping.
    """
    trial_run_id: str
    refit_run_id: Optional[str] = None
    artifact_run_id: Optional[str] = None  # Which run to use for artifact acquisition (refit if available, else trial)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Selection metadata
    
    def __post_init__(self) -> None:
        """Set artifact_run_id based on refit availability."""
        if not self.artifact_run_id:
            # Default: prefer refit, fallback to trial
            self.artifact_run_id = self.refit_run_id or self.trial_run_id


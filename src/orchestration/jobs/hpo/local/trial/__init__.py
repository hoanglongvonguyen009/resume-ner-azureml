"""Trial execution and management for local HPO."""

from __future__ import annotations

# Import execution first (it uses lazy import for metrics internally)
from .execution import TrialExecutor, run_training_trial

# Don't import metrics here to avoid circular import
# Import directly from .metrics when needed: from .metrics import read_trial_metrics

# Import other modules if they exist
try:
    from .run_manager import create_trial_run_no_cv, finalize_trial_run_no_cv
except ImportError:
    # run_manager may have been moved - create stubs
    def create_trial_run_no_cv(*args, **kwargs):
        raise ImportError("create_trial_run_no_cv has been moved. Please import from training.hpo.trial.run_manager")
    def finalize_trial_run_no_cv(*args, **kwargs):
        raise ImportError("finalize_trial_run_no_cv has been moved. Please import from training.hpo.trial.run_manager")

try:
    from .callback import create_trial_callback
except ImportError:
    def create_trial_callback(*args, **kwargs):
        raise ImportError("create_trial_callback has been moved. Please check new location")

__all__ = [
    "TrialExecutor",
    "run_training_trial",
    "create_trial_run_no_cv",
    "finalize_trial_run_no_cv",
    "create_trial_callback",
]

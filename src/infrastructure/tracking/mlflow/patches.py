"""
MLflow patches to add validation and logging.

This module patches mlflow.start_run() to add validation that prevents
auto-generated run names (e.g., 'gray_boniato_9qndy2l2', 'sad_toe_8qbllbws').

The patch is applied automatically when this module is imported.
"""

import sys
import traceback
from typing import Any, Optional

# Store original function before patching
_original_start_run = None


def _validate_run_name(run_name: Optional[str], call_site: str) -> None:
    """
    Validate run_name before creating MLflow run.
    
    Args:
        run_name: The run name to validate
        call_site: Description of where this is being called from
        
    Raises:
        ValueError: If run_name is None or empty
    """
    if not run_name or not run_name.strip():
        error_msg = (
            f"CRITICAL: Cannot create MLflow run: run_name is None or empty. "
            f"This would cause MLflow to auto-generate a name like 'gray_boniato_9qndy2l2'. "
            f"Call site: {call_site}, run_name={run_name}"
        )
        print("=" * 80, file=sys.stderr, flush=True)
        print(error_msg, file=sys.stderr, flush=True)
        print("Call stack:", file=sys.stderr, flush=True)
        for line in traceback.format_stack()[-15:-1]:
            print(f"  {line.rstrip()}", file=sys.stderr, flush=True)
        print("=" * 80, file=sys.stderr, flush=True)
        raise ValueError(
            f"Cannot create MLflow run: run_name is None or empty. "
            f"This would cause MLflow to auto-generate a name. "
            f"Call site: {call_site}"
        )


def _patched_start_run(run_name: Optional[str] = None, run_id: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Patched version of mlflow.start_run() with validation.
    
    This wrapper adds validation to prevent auto-generated run names.
    """
    # Only validate if run_name is provided (run_id doesn't need validation)
    if run_name is not None:
        _validate_run_name(run_name, "mlflow.start_run()")
        print(f"  [MLflow Patch] mlflow.start_run() called with run_name='{run_name}'", file=sys.stderr, flush=True)
    
    # Call original function
    if _original_start_run is None:
        import mlflow
        return mlflow.start_run(run_name=run_name, run_id=run_id, **kwargs)
    else:
        return _original_start_run(run_name=run_name, run_id=run_id, **kwargs)


def apply_patch() -> None:
    """
    Apply patch to mlflow.start_run() to add validation.
    
    This should be called early in the application lifecycle, ideally
    before any mlflow.start_run() calls are made.
    """
    global _original_start_run
    
    try:
        import mlflow
        
        # Only patch if not already patched
        if not hasattr(mlflow, '_original_start_run_patched'):
            _original_start_run = mlflow.start_run
            mlflow.start_run = _patched_start_run
            mlflow._original_start_run_patched = True
            print("  [MLflow Patch] ✓ Applied patch to mlflow.start_run()", file=sys.stderr, flush=True)
        else:
            print("  [MLflow Patch] Patch already applied", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"  [MLflow Patch] WARNING: Could not apply patch: {e}", file=sys.stderr, flush=True)


# Auto-apply patch when module is imported
apply_patch()


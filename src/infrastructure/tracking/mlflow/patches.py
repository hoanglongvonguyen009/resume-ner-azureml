"""
MLflow patches to add validation and logging.

This module patches mlflow.start_run() and MlflowClient.create_run() to add 
validation that prevents auto-generated run names (e.g., 'gray_boniato_9qndy2l2', 
'brave_shoe_fcqs83bv', 'sad_toe_8qbllbws').

The patch is applied automatically when this module is imported.
"""

import sys
import traceback
from typing import Any, Optional

# Store original functions before patching
_original_start_run = None
_original_client_create_run = None


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
            f"This would cause MLflow to auto-generate a name like 'brave_shoe_fcqs83bv'. "
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
    # If run_id is provided, we're resuming an existing run - no validation needed
    if run_id is not None:
        if _original_start_run is None:
            import mlflow
            return mlflow.start_run(run_id=run_id, **kwargs)
        else:
            return _original_start_run(run_id=run_id, **kwargs)
    
    # If run_id is not provided, run_name MUST be provided and valid
    # This prevents MLflow from auto-generating names like 'purple_jackal_l95cs465a'
    _validate_run_name(run_name, "mlflow.start_run()")
    
    # Call original function
    if _original_start_run is None:
        import mlflow
        return mlflow.start_run(run_name=run_name, **kwargs)
    else:
        return _original_start_run(run_name=run_name, **kwargs)


def _patched_client_create_run(self: Any, experiment_id: str, run_name: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Patched version of MlflowClient.create_run() with validation.
    
    This wrapper adds validation to prevent auto-generated run names.
    """
    # run_name MUST be provided and valid - client.create_run() always creates a new run
    # This prevents MLflow from auto-generating names like 'purple_jackal_l95cs465a'
    _validate_run_name(run_name, "MlflowClient.create_run()")
    
    # Call original function (should always be set after apply_patch() runs)
    if _original_client_create_run is None:
        # This should never happen if patch was applied correctly
        error_msg = "CRITICAL: MlflowClient.create_run() patch not properly initialized"
        print(error_msg, file=sys.stderr, flush=True)
        raise RuntimeError(error_msg)
    
    return _original_client_create_run(self, experiment_id=experiment_id, run_name=run_name, **kwargs)


def apply_patch() -> None:
    """
    Apply patches to mlflow.start_run() and MlflowClient.create_run() to add validation.
    
    This should be called early in the application lifecycle, ideally
    before any mlflow.start_run() or client.create_run() calls are made.
    """
    global _original_start_run, _original_client_create_run
    
    try:
        import mlflow
        
        # Patch mlflow.start_run()
        if not hasattr(mlflow, '_original_start_run_patched'):
            _original_start_run = mlflow.start_run
            mlflow.start_run = _patched_start_run
            mlflow._original_start_run_patched = True
    except Exception as e:
        print(f"  [MLflow Patch] WARNING: Could not apply mlflow.start_run() patch: {e}", file=sys.stderr, flush=True)
    
    try:
        from mlflow.tracking import MlflowClient
        
        # Patch MlflowClient.create_run()
        if not hasattr(MlflowClient, '_create_run_patched'):
            _original_client_create_run = MlflowClient.create_run
            MlflowClient.create_run = _patched_client_create_run
            MlflowClient._create_run_patched = True
    except Exception as e:
        print(f"  [MLflow Patch] WARNING: Could not apply MlflowClient.create_run() patch: {e}", file=sys.stderr, flush=True)


# Auto-apply patch when module is imported
apply_patch()


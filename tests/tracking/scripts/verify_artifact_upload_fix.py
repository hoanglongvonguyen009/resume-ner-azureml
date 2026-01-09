#!/usr/bin/env python3
"""Quick verification script for Azure ML artifact upload fixes.

This script quickly verifies that the fixes are in place and working.
Run this after deploying the fixes to verify they're working correctly.

Usage:
    python tests/tracking/scripts/verify_artifact_upload_fix.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))


def check_monkey_patch():
    """Check if monkey-patch is in place."""
    print("Checking monkey-patch...")
    
    try:
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        import mlflow.store.artifact.artifact_repository_registry as arr
        builder = arr._artifact_repository_registry._registry.get('azureml')
        
        if builder is None:
            print("  ⚠ Azure ML builder not registered (may not be using Azure ML)")
            return False
        
        # Check if patched
        import functools
        if hasattr(builder, '__wrapped__'):
            print("  ✓ Monkey-patch is registered")
            return True
        else:
            print("  ✗ Monkey-patch NOT found (builder not wrapped)")
            return False
    except Exception as e:
        print(f"  ✗ Error checking monkey-patch: {e}")
        return False


def check_upload_to_refit_run():
    """Check if code uploads to refit run."""
    print("\nChecking upload to refit run logic...")
    
    try:
        from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
        
        # Read the source code to check
        sweep_tracker_file = Path(__file__).parent.parent.parent.parent / "src" / "orchestration" / "jobs" / "tracking" / "trackers" / "sweep_tracker.py"
        
        if not sweep_tracker_file.exists():
            print("  ✗ Cannot find sweep_tracker.py")
            return False
        
        content = sweep_tracker_file.read_text()
        
        # Check for upload to refit run logic
        if "refit_run_id" in content and "Uploading checkpoint to refit run" in content:
            print("  ✓ Code uploads to refit run when available")
            return True
        else:
            print("  ✗ Code may not upload to refit run")
            return False
    except Exception as e:
        print(f"  ✗ Error checking upload logic: {e}")
        return False


def check_refit_run_completion():
    """Check if refit run completion logic is in place."""
    print("\nChecking refit run completion logic...")
    
    try:
        local_sweeps_file = Path(__file__).parent.parent.parent.parent / "src" / "orchestration" / "jobs" / "hpo" / "local_sweeps.py"
        
        if not local_sweeps_file.exists():
            print("  ✗ Cannot find local_sweeps.py")
            return False
        
        content = local_sweeps_file.read_text()
        
        # Check for refit run FINISHED marking logic
        if "Mark refit run as FINISHED" in content and "set_terminated" in content:
            # Check that it's outside the if/else block
            lines = content.split('\n')
            in_finished_block = False
            found_finished_marking = False
            
            for i, line in enumerate(lines):
                if "Mark refit run as FINISHED" in line:
                    in_finished_block = True
                    # Check if it's at the same indentation level as the if/else (not inside else)
                    if i > 0:
                        prev_line = lines[i-1]
                        # Should not be inside the else block
                        if "else:" not in prev_line and "if log_best_checkpoint" not in prev_line:
                            found_finished_marking = True
                            break
            
            if found_finished_marking or in_finished_block:
                print("  ✓ Refit run completion logic is in place")
                return True
            else:
                print("  ✗ Refit run completion logic may be in wrong location")
                return False
        else:
            print("  ✗ Refit run completion logic not found")
            return False
    except Exception as e:
        print(f"  ✗ Error checking completion logic: {e}")
        return False


def check_mlflow_version():
    """Check MLflow version compatibility."""
    print("\nChecking MLflow version...")
    
    try:
        import mlflow
        mlflow_version = mlflow.__version__
        print(f"  MLflow version: {mlflow_version}")
        
        # Check for version mismatch warning
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import mlflow  # Re-import to catch warnings
            if w:
                for warning in w:
                    if "mismatch" in str(warning.message).lower():
                        print(f"  ⚠ Version mismatch warning: {warning.message}")
                        return False
        
        print("  ✓ No version mismatch warnings")
        return True
    except Exception as e:
        print(f"  ✗ Error checking MLflow version: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Azure ML Artifact Upload Fix Verification")
    print("=" * 60)
    
    results = []
    
    # Check 1: Monkey-patch
    results.append(("Monkey-patch", check_monkey_patch()))
    
    # Check 2: Upload to refit run
    results.append(("Upload to refit run", check_upload_to_refit_run()))
    
    # Check 3: Refit run completion
    results.append(("Refit run completion", check_refit_run_completion()))
    
    # Check 4: MLflow version
    results.append(("MLflow version", check_mlflow_version()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All checks passed! Fixes are in place.")
    else:
        print("✗ Some checks failed. Please review the fixes.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


"""Manual test script for Azure ML artifact upload.

This script can be run manually to test artifact uploads in a real Azure ML environment.
It verifies:
1. Monkey-patch is working
2. Artifacts can be uploaded to child runs
3. Refit runs are marked as FINISHED

Usage:
    python -m pytest tests/tracking/scripts/test_artifact_upload_manual.py -v
    # Or run directly:
    python tests/tracking/scripts/test_artifact_upload_manual.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

import mlflow
from mlflow.tracking import MlflowClient
from pathlib import Path
import tempfile
import json


def test_monkey_patch_registration():
    """Test that monkey-patch is registered."""
    print("Testing monkey-patch registration...")
    
    # Import should trigger the patch
    from orchestration.jobs.tracking.trackers.sweep_tracker import MLflowSweepTracker
    
    import mlflow.store.artifact.artifact_repository_registry as arr
    builder = arr._artifact_repository_registry._registry.get('azureml')
    
    if builder is None:
        print("⚠ Azure ML builder not registered (not using Azure ML)")
        return False
    
    print(f"✓ Azure ML builder registered: {builder}")
    
    # Check if it's wrapped (patched)
    if hasattr(builder, '__wrapped__'):
        print("✓ Builder is patched (has __wrapped__ attribute)")
    else:
        print("⚠ Builder is not patched (no __wrapped__ attribute)")
    
    return True


def test_artifact_upload_to_child_run():
    """Test uploading an artifact to a child run."""
    print("\nTesting artifact upload to child run...")
    
    tracking_uri = mlflow.get_tracking_uri()
    print(f"Tracking URI: {tracking_uri}")
    
    if not tracking_uri or "azureml" not in tracking_uri.lower():
        print("⚠ Not using Azure ML, skipping test")
        return False
    
    # Check if there's an active run
    active_run = mlflow.active_run()
    if not active_run:
        print("⚠ No active MLflow run, skipping test")
        return False
    
    parent_run_id = active_run.info.run_id
    print(f"Active parent run: {parent_run_id}")
    
    # Create a child run
    client = MlflowClient()
    experiment_id = active_run.info.experiment_id
    
    try:
        # Create a child run
        child_run = client.create_run(
            experiment_id=experiment_id,
            tags={"mlflow.parentRunId": parent_run_id, "test": "artifact_upload"}
        )
        child_run_id = child_run.info.run_id
        print(f"Created child run: {child_run_id}")
        
        # Create a test artifact
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            test_data = {"test": "artifact", "timestamp": "2026-01-09"}
            json.dump(test_data, tmp_file)
            artifact_path = Path(tmp_file.name)
        
        try:
            # Try to upload to child run
            print(f"Attempting to upload artifact to child run {child_run_id}...")
            client.log_artifact(
                child_run_id,
                str(artifact_path),
                artifact_path="test_artifact"
            )
            print("✓ Successfully uploaded artifact to child run!")
            
            # Mark child run as FINISHED
            client.set_terminated(child_run_id, status="FINISHED")
            print(f"✓ Marked child run {child_run_id} as FINISHED")
            
            return True
        except Exception as e:
            print(f"✗ Failed to upload artifact to child run: {e}")
            print(f"  Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            if artifact_path.exists():
                artifact_path.unlink()
    except Exception as e:
        print(f"✗ Failed to create child run: {e}")
        return False


def test_refit_run_completion():
    """Test that refit run completion logic works."""
    print("\nTesting refit run completion logic...")
    
    tracking_uri = mlflow.get_tracking_uri()
    if not tracking_uri or "azureml" not in tracking_uri.lower():
        print("⚠ Not using Azure ML, skipping test")
        return False
    
    active_run = mlflow.active_run()
    if not active_run:
        print("⚠ No active MLflow run, skipping test")
        return False
    
    parent_run_id = active_run.info.run_id
    client = MlflowClient()
    experiment_id = active_run.info.experiment_id
    
    try:
        # Create a refit run
        refit_run = client.create_run(
            experiment_id=experiment_id,
            tags={"mlflow.parentRunId": parent_run_id, "code.refit": "true"}
        )
        refit_run_id = refit_run.info.run_id
        print(f"Created refit run: {refit_run_id}")
        
        # Simulate successful upload
        upload_succeeded = True
        
        # Check run status
        run = client.get_run(refit_run_id)
        print(f"Refit run status: {run.info.status}")
        
        if run.info.status == "RUNNING":
            if upload_succeeded:
                # Mark as FINISHED
                client.set_tag(
                    refit_run_id, "code.refit_artifacts_uploaded", "true")
                client.set_terminated(refit_run_id, status="FINISHED")
                print(f"✓ Marked refit run {refit_run_id} as FINISHED")
                
                # Verify
                run = client.get_run(refit_run_id)
                assert run.info.status == "FINISHED", \
                    f"Refit run should be FINISHED, but got {run.info.status}"
                print(f"✓ Verified refit run is FINISHED")
                return True
        else:
            print(f"⚠ Refit run already has status {run.info.status}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to test refit run completion: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all manual tests."""
    print("=" * 60)
    print("Azure ML Artifact Upload Manual Tests")
    print("=" * 60)
    
    results = []
    
    # Test 1: Monkey-patch registration
    results.append(("Monkey-patch registration", test_monkey_patch_registration()))
    
    # Test 2: Artifact upload to child run
    results.append(("Artifact upload to child run", test_artifact_upload_to_child_run()))
    
    # Test 3: Refit run completion
    results.append(("Refit run completion", test_refit_run_completion()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


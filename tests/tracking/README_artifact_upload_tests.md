# Azure ML Artifact Upload Tests

This directory contains tests for the Azure ML artifact upload fixes, including:

1. **Monkey-patch for `azureml_artifacts_builder`**: Fixes compatibility issue between MLflow 3.5.0 and azureml-mlflow 1.61.0.post1
2. **Artifact upload to child runs**: Verifies artifacts can be uploaded to refit runs (child runs) instead of parent runs
3. **Refit run completion**: Ensures refit runs are marked as FINISHED after artifact upload

## Test Files

### Unit Tests
- **`unit/test_azureml_artifact_upload.py`**: Unit tests for the monkey-patch and artifact upload logic
  - Tests monkey-patch registration
  - Tests artifact upload to refit runs
  - Tests artifact upload to parent runs (fallback)
  - Tests refit run FINISHED status marking

### Integration Tests
- **`integration/test_azureml_artifact_upload_integration.py`**: Integration tests for end-to-end behavior
  - Requires Azure ML workspace configuration
  - Tests full artifact upload workflow
  - Tests refit run completion logic

### Manual Test Script
- **`scripts/test_artifact_upload_manual.py`**: Manual test script for real Azure ML environments
  - Can be run directly to verify fixes in a real environment
  - Tests monkey-patch registration
  - Tests artifact upload to child runs
  - Tests refit run completion

## Running the Tests

### Unit Tests (No Azure ML Required)
```bash
# Run all unit tests
pytest tests/tracking/unit/test_azureml_artifact_upload.py -v

# Run specific test class
pytest tests/tracking/unit/test_azureml_artifact_upload.py::TestAzureMLArtifactBuilderPatch -v

# Run specific test
pytest tests/tracking/unit/test_azureml_artifact_upload.py::TestAzureMLArtifactBuilderPatch::test_patch_registered_on_import -v
```

### Integration Tests (Requires Azure ML)
```bash
# Run integration tests (requires --run-azureml-tests flag)
pytest tests/tracking/integration/test_azureml_artifact_upload_integration.py -v --run-azureml-tests

# Or set environment variable
export RUN_AZUREML_TESTS=1
pytest tests/tracking/integration/test_azureml_artifact_upload_integration.py -v
```

### Manual Test Script
```bash
# Run directly (requires active MLflow run in Azure ML)
python tests/tracking/scripts/test_artifact_upload_manual.py

# Or via pytest
pytest tests/tracking/scripts/test_artifact_upload_manual.py -v
```

## What the Tests Verify

### 1. Monkey-Patch Registration
- Verifies that `azureml.mlflow` is imported when `sweep_tracker` is imported
- Verifies that the monkey-patch is registered in the artifact repository registry
- Verifies that the patched builder handles `tracking_uri` parameter gracefully

### 2. Artifact Upload to Child Runs
- Verifies that artifacts are uploaded to refit runs (child runs) when available
- Verifies that artifacts fall back to parent runs when refit run is not available
- Verifies that the correct `artifact_path` is used

### 3. Refit Run Completion
- Verifies that refit runs are marked as FINISHED after successful artifact upload
- Verifies that refit runs are marked as FAILED after failed artifact upload
- Verifies that already-terminated runs are not modified

## Known Issues Tested

### Issue 1: `tracking_uri` TypeError
**Problem**: `azureml_artifacts_builder() got an unexpected keyword argument 'tracking_uri'`

**Fix**: Monkey-patch that catches the TypeError and retries without `tracking_uri` parameter

**Test**: `TestAzureMLArtifactBuilderPatch::test_patch_handles_tracking_uri_parameter`

### Issue 2: Artifacts Uploaded to Parent Instead of Child
**Problem**: Artifacts were being uploaded to parent run instead of refit run (child run)

**Fix**: Always use `client.log_artifact()` with explicit `refit_run_id` when available

**Test**: `TestArtifactUploadToChildRun::test_upload_to_refit_run_when_available`

### Issue 3: Refit Run Not Marked as FINISHED
**Problem**: Refit runs stayed in RUNNING status after artifact upload

**Fix**: Moved refit run FINISHED marking logic outside if/else block so it always runs

**Test**: `TestRefitRunFinishedStatus::test_refit_run_marked_finished_after_successful_upload`

## Troubleshooting

### Tests Fail with "Azure ML builder not registered"
- **Cause**: Not using Azure ML workspace
- **Solution**: Set up Azure ML workspace or skip Azure ML-specific tests

### Tests Fail with "No active MLflow run"
- **Cause**: No active MLflow run context
- **Solution**: Start an MLflow run before running tests, or use mocked tests

### Integration Tests Timeout
- **Cause**: Network issues or Azure ML service unavailable
- **Solution**: Check Azure ML workspace connectivity, or skip integration tests

## Related Code

- **Monkey-patch**: `src/orchestration/jobs/tracking/trackers/sweep_tracker.py` (lines 21-42)
- **Artifact upload**: `src/orchestration/jobs/tracking/trackers/sweep_tracker.py` (lines 1098-1121)
- **Refit run completion**: `src/orchestration/jobs/hpo/local_sweeps.py` (lines 997-1042)


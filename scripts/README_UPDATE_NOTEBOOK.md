# Update Notebook with MLflow Run Finder

This script updates the notebook to use the new systematic MLflow run finder instead of the old manual search logic.

## Usage

Run the script from the project root:

```bash
py scripts/update_notebook_mlflow_finder.py
```

Or specify the notebook path:

```bash
py scripts/update_notebook_mlflow_finder.py notebooks/01_orchestrate_training_colab.ipynb
```

## What it does

The script:
1. Finds the cell containing the old MLflow run search logic (using `MlflowClient` and `search_runs`)
2. Replaces it with the new `find_mlflow_run()` function
3. Updates the artifact upload code to use the `RunLookupReport`

## Manual Update (if script doesn't work)

If the script can't find the section automatically, you can manually replace the MLflow search code (around line 2815-2879) with:

```python
# Use new systematic MLflow run finder
from orchestration.jobs.tracking.mlflow_run_finder import find_mlflow_run

# Find MLflow run using new finder
report = find_mlflow_run(
    experiment_name=mlflow_experiment_name,
    context=training_context if 'training_context' in locals() else None,
    output_dir=final_output_dir if 'final_output_dir' in locals() else None,
    strict=True,  # Default: fail loud instead of attaching to wrong run
    root_dir=ROOT_DIR,
)

if report.found and report.run_id:
    with mlflow.start_run(run_id=report.run_id):
        training_tracker.log_training_artifacts(
            checkpoint_dir=checkpoint_dir
            if checkpoint_dir.exists()
            else None,
            metrics_json_path=metrics_json_path
            if metrics_json_path.exists()
            else None,
        )
        print(f"✓ Logged training artifacts to MLflow run {report.run_id}")
        print(f"  Strategy used: {report.strategy_used}")
else:
    print(f"⚠ Could not find MLflow run for artifact upload")
    print(f"  Experiment: {mlflow_experiment_name}")
    if report.error:
        print(f"  Error: {report.error}")
    if report.strategies_attempted:
        print(f"  Attempted strategies: {', '.join(report.strategies_attempted)}")
    print(f"  Try checking the MLflow UI for the most recent run")
```

## Backup

The script modifies the notebook in place. Make sure to:
- Commit your changes before running
- Or create a backup: `cp notebooks/01_orchestrate_training_colab.ipynb notebooks/01_orchestrate_training_colab.ipynb.backup`

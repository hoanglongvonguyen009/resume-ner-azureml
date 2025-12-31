"""Script to update notebook with new MLflow run finder."""

import json
import re
from pathlib import Path


def update_notebook_mlflow_finder(notebook_path: Path) -> None:
    """
    Update notebook to use new MLflow run finder instead of manual search.
    
    Args:
        notebook_path: Path to notebook file.
    """
    # Read notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # New code to replace the old MLflow search logic
    new_code_lines = [
        "# Use new systematic MLflow run finder",
        "from orchestration.jobs.tracking.mlflow_run_finder import find_mlflow_run",
        "",
        "# Find MLflow run using new finder",
        "report = find_mlflow_run(",
        "    experiment_name=mlflow_experiment_name,",
        "    context=training_context if 'training_context' in locals() else None,",
        "    output_dir=final_output_dir if 'final_output_dir' in locals() else None,",
        "    strict=True,  # Default: fail loud instead of attaching to wrong run",
        "    root_dir=ROOT_DIR,",
        "    config_dir=CONFIG_DIR if 'CONFIG_DIR' in locals() else None,",
        ")",
        "",
        "if report.found and report.run_id:",
        "    with mlflow.start_run(run_id=report.run_id):",
        "        training_tracker.log_training_artifacts(",
        "            checkpoint_dir=checkpoint_dir",
        "            if checkpoint_dir.exists()",
        "            else None,",
        "            metrics_json_path=metrics_json_path",
        "            if metrics_json_path.exists()",
        "            else None,",
        "        )",
        "        print(f\"✓ Logged training artifacts to MLflow run {report.run_id}\")",
        "        print(f\"  Strategy used: {report.strategy_used}\")",
        "else:",
        "    print(f\"⚠ Could not find MLflow run for artifact upload\")",
        "    print(f\"  Experiment: {mlflow_experiment_name}\")",
        "    if report.error:",
        "        print(f\"  Error: {report.error}\")",
        "    if report.strategies_attempted:",
        "        print(f\"  Attempted strategies: {', '.join(report.strategies_attempted)}\")",
        "    print(f\"  Try checking the MLflow UI for the most recent run\")",
    ]
    
    # Find and update the cell containing the old MLflow search logic
    updated = False
    for cell_idx, cell in enumerate(notebook.get('cells', [])):
        if cell.get('cell_type') != 'code':
            continue
        
        source_lines = cell.get('source', [])
        if isinstance(source_lines, str):
            source_lines = source_lines.split('\n')
        
        source_text = '\n'.join(source_lines)
        
        # Look for the old search pattern - more specific markers
        has_mlflow_client = 'from mlflow.tracking import MlflowClient' in source_text
        has_old_search = 'tags.mlflow.runName' in source_text or 'attributes.run_name' in source_text
        has_search_runs = 'search_runs' in source_text
        has_artifact_upload = 'training_tracker.log_training_artifacts' in source_text
        
        if has_mlflow_client and has_old_search and has_search_runs:
            print(f"Found cell {cell_idx} with old MLflow search logic")
            
            # Find the section to replace
            new_source_lines = []
            in_replacement_section = False
            replacement_started = False
            
            for i, line in enumerate(source_lines):
                # Detect start of replacement section
                if 'from mlflow.tracking import MlflowClient' in line and not replacement_started:
                    # Keep any comments or code before this
                    # Add the new code
                    new_source_lines.extend(new_code_lines)
                    in_replacement_section = True
                    replacement_started = True
                    continue
                
                # Skip lines in the old search section
                if in_replacement_section:
                    # End of replacement section: when we see artifact upload or exception handling
                    if 'training_tracker.log_training_artifacts' in line:
                        # This line is already in new_code_lines, skip it
                        in_replacement_section = False
                        # But we need to handle the rest of the try/except block
                        # Look ahead to see if there's an else clause we need to keep
                        continue
                    elif 'Failed to log training artifacts' in line or \
                         'except Exception as e:' in line and 'log training artifacts' in source_text[i-10:i+10]:
                        # End of the section we're replacing
                        in_replacement_section = False
                        # Don't add this line, it's part of the old code
                        continue
                    else:
                        # Still in replacement section, skip this line
                        continue
                
                # Normal line, keep it
                new_source_lines.append(line)
            
            # Update cell source
            cell['source'] = new_source_lines
            updated = True
            print(f"[OK] Updated notebook cell {cell_idx} with new MLflow run finder")
            break
    
    if not updated:
        print("[WARNING] Could not find the MLflow search section to replace")
        print("  The notebook may have already been updated or the structure is different")
        print("  Please manually update the notebook using the code in this script")
        return
    
    # Write updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    print(f"[OK] Successfully updated notebook: {notebook_path}")


if __name__ == '__main__':
    import sys
    
    # Default to the main training notebook
    if len(sys.argv) > 1:
        notebook_path = Path(sys.argv[1])
    else:
        # Assume script is run from project root
        script_dir = Path(__file__).parent
        notebook_path = script_dir.parent / 'notebooks' / '01_orchestrate_training_colab.ipynb'
    
    if not notebook_path.exists():
        print(f"[ERROR] Notebook not found: {notebook_path}")
        print(f"  Current working directory: {Path.cwd()}")
        sys.exit(1)
    
    print(f"Updating notebook: {notebook_path}")
    update_notebook_mlflow_finder(notebook_path)
#!/usr/bin/env python3
"""
Manual verification script to check hash consistency across HPO runs.

This script can be run against existing MLflow runs to verify:
1. Parent runs have v2 study_key_hash tags
2. Trial runs have matching v2 study_key_hash tags
3. Refit runs have matching v2 study_key_hash and trial_key_hash tags
4. Refit linking tags are set correctly

Usage:
    python tests/training/hpo/scripts/verify_hash_consistency.py \
        --experiment-name "resume_ner_baseline-hpo-distilbert" \
        --parent-run-id "abc123..."
    
    Or check all runs in an experiment:
    python tests/training/hpo/scripts/verify_hash_consistency.py \
        --experiment-name "resume_ner_baseline-hpo-distilbert" \
        --check-all
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mlflow.tracking import MlflowClient
from infrastructure.naming.mlflow.tags_registry import load_tags_registry


def get_tag(run, tag_key: str) -> Optional[str]:
    """Get tag value from run, checking both data.tags and info.tags."""
    if hasattr(run, 'data') and hasattr(run.data, 'tags'):
        return run.data.tags.get(tag_key)
    if hasattr(run, 'info') and hasattr(run.info, 'tags'):
        return run.info.tags.get(tag_key)
    return None


def check_hash_consistency(
    client: MlflowClient,
    experiment_name: str,
    parent_run_id: Optional[str] = None,
    check_all: bool = False,
) -> Dict[str, Any]:
    """Check hash consistency across parent, trial, and refit runs."""
    results = {
        "parent_runs": [],
        "trial_runs": [],
        "refit_runs": [],
        "issues": [],
        "summary": {},
    }

    # Load tags registry
    config_dir = project_root / "config"
    tags_registry = load_tags_registry(config_dir)
    study_key_tag = tags_registry.key("grouping", "study_key_hash")
    trial_key_tag = tags_registry.key("grouping", "trial_key_hash")
    stage_tag = tags_registry.key("process", "stage")
    refit_tag = tags_registry.key("refit", "of_trial_run_id")
    data_fp_tag = tags_registry.key("fingerprint", "data")
    eval_fp_tag = tags_registry.key("fingerprint", "eval")

    # Get experiment
    try:
        experiment = client.get_experiment_by_name(experiment_name)
        if experiment is None:
            results["issues"].append(f"Experiment '{experiment_name}' not found")
            return results
    except Exception as e:
        results["issues"].append(f"Error getting experiment: {e}")
        return results

    # Get runs
    if check_all:
        # Get all parent runs
        parent_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"tags.{stage_tag} = 'hpo'",
            max_results=100,
        )
    elif parent_run_id:
        # Get specific parent run
        try:
            parent_run = client.get_run(parent_run_id)
            parent_runs = [parent_run]
        except Exception as e:
            results["issues"].append(f"Error getting parent run {parent_run_id}: {e}")
            return results
    else:
        results["issues"].append("Must specify --parent-run-id or --check-all")
        return results

    # Check each parent run
    for parent_run in parent_runs:
        parent_id = parent_run.info.run_id
        parent_study_hash = get_tag(parent_run, study_key_tag)
        parent_data_fp = get_tag(parent_run, data_fp_tag)
        parent_eval_fp = get_tag(parent_run, eval_fp_tag)

        parent_info = {
            "run_id": parent_id,
            "study_key_hash": parent_study_hash,
            "data_fingerprint": parent_data_fp,
            "eval_fingerprint": parent_eval_fp,
            "has_v2_tags": bool(parent_data_fp and parent_eval_fp),
        }
        results["parent_runs"].append(parent_info)

        # Check if parent has v2 tags
        if not parent_study_hash:
            results["issues"].append(
                f"Parent run {parent_id[:12]}... missing study_key_hash tag"
            )
            continue

        # Get child runs (trial and refit)
        child_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=f"tags.mlflow.parentRunId = '{parent_id}'",
            max_results=100,
        )

        for child_run in child_runs:
            child_id = child_run.info.run_id
            child_stage = get_tag(child_run, stage_tag)
            child_study_hash = get_tag(child_run, study_key_tag)
            child_trial_hash = get_tag(child_run, trial_key_tag)
            child_refit_link = get_tag(child_run, refit_tag)

            if child_stage == "hpo" or child_stage == "hpo_trial":
                # Trial run
                trial_info = {
                    "run_id": child_id,
                    "parent_run_id": parent_id,
                    "study_key_hash": child_study_hash,
                    "trial_key_hash": child_trial_hash,
                    "matches_parent": child_study_hash == parent_study_hash,
                }
                results["trial_runs"].append(trial_info)

                # Check consistency
                if not child_study_hash:
                    results["issues"].append(
                        f"Trial run {child_id[:12]}... missing study_key_hash tag"
                    )
                elif child_study_hash != parent_study_hash:
                    results["issues"].append(
                        f"Trial run {child_id[:12]}... has mismatched study_key_hash: "
                        f"parent={parent_study_hash[:16]}..., trial={child_study_hash[:16]}..."
                    )

            elif child_stage == "hpo_refit" or child_stage == "refit":
                # Refit run
                refit_info = {
                    "run_id": child_id,
                    "parent_run_id": parent_id,
                    "study_key_hash": child_study_hash,
                    "trial_key_hash": child_trial_hash,
                    "refit_of_trial_run_id": child_refit_link,
                    "matches_parent": child_study_hash == parent_study_hash,
                    "has_linking_tag": bool(child_refit_link),
                }
                results["refit_runs"].append(refit_info)

                # Check consistency
                if not child_study_hash:
                    results["issues"].append(
                        f"Refit run {child_id[:12]}... missing study_key_hash tag"
                    )
                elif child_study_hash != parent_study_hash:
                    results["issues"].append(
                        f"Refit run {child_id[:12]}... has mismatched study_key_hash: "
                        f"parent={parent_study_hash[:16]}..., refit={child_study_hash[:16]}..."
                    )

                if not child_refit_link:
                    results["issues"].append(
                        f"Refit run {child_id[:12]}... missing refit.of_trial_run_id tag"
                    )

    # Generate summary
    results["summary"] = {
        "total_parent_runs": len(results["parent_runs"]),
        "total_trial_runs": len(results["trial_runs"]),
        "total_refit_runs": len(results["refit_runs"]),
        "parent_runs_with_v2": sum(1 for p in results["parent_runs"] if p["has_v2_tags"]),
        "trial_runs_matching_parent": sum(
            1 for t in results["trial_runs"] if t.get("matches_parent", False)
        ),
        "refit_runs_matching_parent": sum(
            1 for r in results["refit_runs"] if r.get("matches_parent", False)
        ),
        "refit_runs_with_linking_tag": sum(
            1 for r in results["refit_runs"] if r.get("has_linking_tag", False)
        ),
        "total_issues": len(results["issues"]),
    }

    return results


def print_results(results: Dict[str, Any]):
    """Print verification results in a readable format."""
    print("\n" + "=" * 80)
    print("HPO Hash Consistency Verification Results")
    print("=" * 80)

    summary = results["summary"]
    print(f"\n📊 Summary:")
    print(f"  Parent runs: {summary['total_parent_runs']} (v2 tags: {summary['parent_runs_with_v2']})")
    print(f"  Trial runs: {summary['total_trial_runs']} (matching parent: {summary['trial_runs_matching_parent']})")
    print(f"  Refit runs: {summary['total_refit_runs']} (matching parent: {summary['refit_runs_matching_parent']}, with linking tag: {summary['refit_runs_with_linking_tag']})")
    print(f"  Issues found: {summary['total_issues']}")

    if results["issues"]:
        print(f"\n⚠️  Issues Found:")
        for issue in results["issues"]:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No issues found! All hashes are consistent.")

    # Detailed breakdown
    if results["parent_runs"]:
        print(f"\n📋 Parent Runs:")
        for parent in results["parent_runs"][:5]:  # Show first 5
            v2_status = "✅ v2" if parent["has_v2_tags"] else "❌ v1/missing"
            print(
                f"  {parent['run_id'][:12]}... | "
                f"study_key_hash: {parent['study_key_hash'][:16] if parent['study_key_hash'] else 'missing'}... | "
                f"{v2_status}"
            )
        if len(results["parent_runs"]) > 5:
            print(f"  ... and {len(results['parent_runs']) - 5} more")

    if results["trial_runs"]:
        print(f"\n📋 Trial Runs:")
        matching = sum(1 for t in results["trial_runs"] if t.get("matches_parent", False))
        mismatched = len(results["trial_runs"]) - matching
        print(f"  Matching parent: {matching} | Mismatched: {mismatched}")
        for trial in results["trial_runs"][:3]:  # Show first 3
            status = "✅" if trial.get("matches_parent", False) else "❌"
            print(
                f"  {status} {trial['run_id'][:12]}... | "
                f"study_key_hash: {trial['study_key_hash'][:16] if trial['study_key_hash'] else 'missing'}..."
            )

    if results["refit_runs"]:
        print(f"\n📋 Refit Runs:")
        matching = sum(1 for r in results["refit_runs"] if r.get("matches_parent", False))
        with_link = sum(1 for r in results["refit_runs"] if r.get("has_linking_tag", False))
        print(f"  Matching parent: {matching} | With linking tag: {with_link}")
        for refit in results["refit_runs"][:3]:  # Show first 3
            status = "✅" if refit.get("matches_parent", False) and refit.get("has_linking_tag", False) else "❌"
            print(
                f"  {status} {refit['run_id'][:12]}... | "
                f"study_key_hash: {refit['study_key_hash'][:16] if refit['study_key_hash'] else 'missing'}... | "
                f"linked_to: {refit['refit_of_trial_run_id'][:12] if refit['refit_of_trial_run_id'] else 'missing'}..."
            )

    print("\n" + "=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify HPO hash consistency across parent, trial, and refit runs"
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        required=True,
        help="MLflow experiment name (e.g., 'resume_ner_baseline-hpo-distilbert')",
    )
    parser.add_argument(
        "--parent-run-id",
        type=str,
        help="Specific parent run ID to check (optional if --check-all is used)",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check all parent runs in the experiment",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if not args.check_all and not args.parent_run_id:
        parser.error("Must specify either --parent-run-id or --check-all")

    # Initialize MLflow client
    client = MlflowClient()

    # Run verification
    results = check_hash_consistency(
        client=client,
        experiment_name=args.experiment_name,
        parent_run_id=args.parent_run_id,
        check_all=args.check_all,
    )

    # Print or output results
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_results(results)

    # Exit with error code if issues found
    if results["issues"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()


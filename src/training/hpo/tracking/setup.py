from __future__ import annotations

"""MLflow run setup utilities for HPO.

Handles MLflow run name creation, context setup, and version commit.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger
from training.hpo.utils.helpers import create_mlflow_run_name

logger = get_logger(__name__)


def setup_hpo_mlflow_run(
    backbone: str,
    study_name: str,
    output_dir: Path,
    run_id: str,
    should_resume: bool,
    checkpoint_enabled: bool,
    data_config: Optional[Dict[str, Any]] = None,
    hpo_config: Optional[Dict[str, Any]] = None,
    benchmark_config: Optional[Dict[str, Any]] = None,
    study_key_hash: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Tuple[Any, str]:
    """
    Set up MLflow run name and context for HPO parent run.
    
    **Important**: This function trusts the provided `config_dir` parameter if not None.
    It does NOT re-infer `config_dir` when the caller provides it, following DRY principles.
    Only infers `config_dir` when it's explicitly None and cannot be derived from other parameters.
    
    Args:
        backbone: Model backbone name (e.g., "distilbert-base-uncased").
        study_name: Optuna study name.
        output_dir: HPO output directory path.
        run_id: Unique run identifier.
        should_resume: Whether to resume existing study.
        checkpoint_enabled: Whether checkpointing is enabled.
        data_config: Optional data configuration dictionary.
        hpo_config: Optional HPO configuration dictionary.
        benchmark_config: Optional benchmark configuration dictionary.
        study_key_hash: Optional pre-computed study key hash.
        config_dir: Optional config directory path. If provided, used directly without inference.
                    If None, inferred from output_dir or current working directory.
    
    Returns:
        Tuple of (hpo_parent_context, mlflow_run_name).
    """
    try:
        from infrastructure.naming import create_naming_context
        from infrastructure.naming.mlflow.run_names import build_mlflow_run_name
        from infrastructure.naming.mlflow.tags import build_mlflow_tags
        from common.shared.platform_detection import detect_platform


        # Compute study_key_hash if missing
        # Note: setup_hpo_mlflow_run() doesn't have train_config parameter, so we use
        # the legacy build_hpo_study_key approach for backward compatibility.
        # The caller should pass pre-computed study_key_hash when available.
        if study_key_hash is None and data_config and hpo_config:
            try:
                from infrastructure.naming.mlflow.hpo_keys import (
                    build_hpo_study_key,
                    build_hpo_study_key_hash,
                )
                # Use resolve_project_paths() to get config_dir if not provided
                # Standardized pattern: only resolve if config_dir is None
                if config_dir is None:
                    from infrastructure.paths.utils import resolve_project_paths
                    _, resolved_config_dir = resolve_project_paths(output_dir=output_dir, config_dir=None)
                    # Standardized fallback: use resolved value, or infer as last resort
                    config_dir = resolved_config_dir
                    if config_dir is None:
                        from infrastructure.paths.utils import infer_config_dir
                        config_dir = infer_config_dir()
                
                # Legacy approach: build_hpo_study_key (v1) since we don't have train_config
                # This is acceptable as a fallback when study_key_hash is not pre-computed
                study_key = build_hpo_study_key(
                    data_config=data_config,
                    hpo_config=hpo_config,
                    model=backbone,
                    benchmark_config=benchmark_config,
                )
                study_key_hash = build_hpo_study_key_hash(study_key)
            except Exception as e:
                logger.warning(
                    f"Could not compute study_key_hash for naming: {e}"
                )
        elif not study_key_hash:
            logger.warning(
                "study_key_hash is None and cannot be computed "
                f"(data_config={'present' if data_config else 'missing'}, "
                f"hpo_config={'present' if hpo_config else 'missing'})"
            )

        if study_key_hash:
            os.environ["HPO_STUDY_KEY_HASH"] = study_key_hash

        try:
            env = detect_platform()
            storage_env_val = detect_platform()
        except Exception as env_error:
            logger.warning(
                f"Error detecting platform: {env_error}, using defaults"
            )
            env = "local"
            storage_env_val = "local"

        # With simplified approach, study_name is always explicit (user-specified)
        # Only filter out the base default pattern to avoid redundancy
        # Variants like hpo_distilbert_v2 should be included as semantic suffix
        study_name_for_context = None
        if study_name:
            # Check if study_name is exactly the auto-generated default pattern (no variant)
            model_short = backbone.split("-")[0] if "-" in backbone else backbone
            default_pattern = f"hpo_{model_short}"
            
            if study_name == default_pattern:
                # Auto-generated default (no variant) - pass None to avoid redundancy
                study_name_for_context = None
            else:
                # Custom study_name (including variants like hpo_distilbert_v2) - use it
                study_name_for_context = study_name
        
        try:
            hpo_parent_context = create_naming_context(
                process_type="hpo",
                model=backbone,
                environment=env,
                storage_env=storage_env_val,
                stage="hpo_sweep",
                study_name=study_name_for_context,
                trial_id=None,
                study_key_hash=study_key_hash,
            )
        except Exception as ctx_error:
            logger.error(
                f"CRITICAL: Failed to create NamingContext: {ctx_error}"
            )
            import traceback
            logger.error(traceback.format_exc())
            raise

        # Use resolve_project_paths() to consolidate path resolution
        # This trusts provided config_dir and only infers when necessary
        from infrastructure.paths.utils import resolve_project_paths
        
        root_dir, resolved_config_dir = resolve_project_paths(
            output_dir=output_dir,
            config_dir=config_dir,
        )
        
        # Standardized fallback: use resolved value, or provided parameter, or infer
        if root_dir is None:
            root_dir = Path.cwd()
        # Use resolved config_dir, or provided config_dir, or infer as last resort
        config_dir = resolved_config_dir or config_dir
        if config_dir is None:
            from infrastructure.paths.utils import infer_config_dir
            config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()

        mlflow_run_name = build_mlflow_run_name(
            hpo_parent_context,
            config_dir,
            root_dir=root_dir,
            output_dir=output_dir,
        )


        return hpo_parent_context, mlflow_run_name

    except Exception as e:
        logger.warning(
            f"Exception during context creation: {e}, trying policy fallback"
        )
        hpo_parent_context = None

        try:
            from infrastructure.naming.mlflow.policy import (
                load_naming_policy,
                format_run_name,
            )
            from infrastructure.naming import create_naming_context
            from common.shared.platform_detection import detect_platform

            # In fallback path, try to infer config_dir if not already resolved
            if config_dir is None:
                from infrastructure.paths.utils import infer_config_dir
                config_dir = infer_config_dir()

            if config_dir and config_dir.exists():
                policy = load_naming_policy(config_dir)
                if policy and "run_names" in policy:
                    # Use same logic for fallback context
                    model_short = backbone.split("-")[0] if "-" in backbone else backbone
                    default_pattern = f"hpo_{model_short}"
                    study_name_for_fallback = None
                    if study_name and study_name != default_pattern:
                        # Include all custom study names (including variants)
                        study_name_for_fallback = study_name
                    
                    minimal_context = create_naming_context(
                        process_type="hpo",
                        model=model_short,
                        environment=detect_platform(),
                        study_name=study_name_for_fallback,
                        study_key_hash=study_key_hash,
                    )
                    mlflow_run_name = format_run_name(
                        "hpo_sweep", minimal_context, policy, config_dir
                    )
                    return minimal_context, mlflow_run_name
        except Exception:
            pass

        mlflow_run_name = create_mlflow_run_name(
            backbone,
            run_id,
            study_name,
            should_resume,
            checkpoint_enabled,
        )
        logger.warning(
            f"Using legacy create_mlflow_run_name: {mlflow_run_name}"
        )
        return hpo_parent_context, mlflow_run_name


def commit_run_name_version(
    parent_run_id: str,
    hpo_parent_context: Any,
    mlflow_run_name: str,
    output_dir: Path,
    config_dir: Optional[Path] = None,
) -> None:
    """
    Commit reserved version if auto-increment was used.
    
    Args:
        parent_run_id: MLflow parent run ID
        hpo_parent_context: Naming context for HPO parent run
        mlflow_run_name: Generated MLflow run name
        output_dir: Base output directory
        config_dir: Optional config directory path. If provided, used directly without inference.
    """
    if not (parent_run_id and hpo_parent_context and mlflow_run_name):
        return

    try:
        import re
        from infrastructure.naming.mlflow.run_keys import (
            build_mlflow_run_key,
            build_mlflow_run_key_hash,
            build_counter_key,
        )
        from orchestration.jobs.tracking.config.loader import (
            get_naming_config,
            get_auto_increment_config,
        )
        from orchestration.jobs.tracking.index.version_counter import (
            commit_run_name_version as commit_version_internal,
        )

        # Use resolve_project_paths() to consolidate path resolution
        # Trust provided config_dir parameter if available
        from infrastructure.paths.utils import resolve_project_paths
        
        root_dir, resolved_config_dir = resolve_project_paths(
            output_dir=output_dir,
            config_dir=config_dir,  # Use provided config_dir if available
        )
        
        # Standardized fallback: use resolved value, or provided parameter, or infer
        if root_dir is None:
            root_dir = Path.cwd()
        # Use resolved config_dir, or provided config_dir, or infer as last resort
        config_dir = resolved_config_dir or config_dir
        if config_dir is None:
            from infrastructure.paths.utils import infer_config_dir
            config_dir = infer_config_dir(path=root_dir) if root_dir else infer_config_dir()

        # Check if auto-increment was used (suffix _1, _2, ...)
        version_match = re.search(r"_(\d+)$", mlflow_run_name)
        if version_match:
            version = int(version_match.group(1))
            logger.info(
                f"[HPO Commit] Found version {version} in run name '{mlflow_run_name}'"
            )

            auto_inc_config = get_auto_increment_config(config_dir, "hpo")
            if auto_inc_config.get("enabled_for_process", False):
                run_key = build_mlflow_run_key(hpo_parent_context)
                run_key_hash = build_mlflow_run_key_hash(run_key)

                naming_config = get_naming_config(config_dir)
                counter_key = build_counter_key(
                    naming_config.get("project_name", "resume-ner"),
                    "hpo",
                    run_key_hash,
                    hpo_parent_context.environment or "",
                )

                logger.info(
                    f"[HPO Commit] Committing version {version} for run {parent_run_id[:12]}..., "
                    f"counter_key={counter_key[:50]}..."
                )

                commit_success = commit_version_internal(
                    counter_key,
                    parent_run_id,
                    version,
                    root_dir,
                    config_dir,
                )

                if commit_success:
                    logger.info(
                        f"[HPO Commit] ✓ Successfully committed version {version} "
                        f"for HPO parent run {parent_run_id[:12]}..."
                    )
                else:
                    logger.warning(
                        f"[HPO Commit] ⚠ Version {version} commit completed but reservation was not found. "
                        f"Run ID: {parent_run_id[:12]}..."
                    )
            else:
                logger.debug(
                    "[HPO Commit] Auto-increment not enabled for HPO, skipping commit."
                )
        else:
            logger.debug(
                "[HPO Commit] Run name does not contain version suffix, skipping commit."
            )

    except Exception as e:
        logger.warning(
            f"[HPO Commit] Could not commit run name version: {e}",
            exc_info=True,
        )

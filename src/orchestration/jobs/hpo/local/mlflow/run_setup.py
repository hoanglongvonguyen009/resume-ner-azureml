"""MLflow run setup utilities for HPO.

Handles MLflow run name creation, context setup, and version commit.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from shared.logging_utils import get_logger
from ...hpo_helpers import create_mlflow_run_name

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
) -> Tuple[Any, str]:
    """
    Set up MLflow run name and context for HPO parent run.

    Args:
        mlflow_experiment_name: MLflow experiment name.
        output_dir: Base output directory.
        backbone: Model backbone name.
        run_id: Unique run ID.
        study_name: Optuna study name.
        should_resume: Whether this is a resume operation.
        checkpoint_enabled: Whether checkpointing is enabled.
        hpo_config: HPO configuration dictionary.
        checkpoint_config: Optional checkpoint configuration.
        storage_path: Optional checkpoint storage path.
        data_config: Optional data configuration (for grouping tags).
        benchmark_config: Optional benchmark configuration (for grouping tags).

    Returns:
        Tuple of (mlflow_run_name, hpo_parent_context, parent_run_id, parent_run_handle).
    """
    try:
        from orchestration.naming_centralized import create_naming_context
        from orchestration.jobs.tracking.mlflow_naming import build_mlflow_run_name, build_mlflow_tags
        from orchestration.jobs.tracking.naming.hpo_keys import (
            build_hpo_study_key,
            build_hpo_study_key_hash,
        )
        from shared.platform_detection import detect_platform

        logger.info(
            f"[HPO Parent Run] Received study_key_hash parameter: "
            f"{study_key_hash[:16] + '...' if study_key_hash else 'None'}"
        )

        # Compute stable study_key_hash for parent run naming if not provided and configs are available.
        if study_key_hash is None and data_config and hpo_config:
            logger.info("[HPO Parent Run] study_key_hash is None, attempting to compute from configs...")
            try:
                study_key = build_hpo_study_key(
                    data_config=data_config,
                    hpo_config=hpo_config,
                    model=backbone,
                    benchmark_config=benchmark_config,
                )
                study_key_hash = build_hpo_study_key_hash(study_key)
                logger.info(f"[HPO Parent Run] ✓ Computed study_key_hash: {study_key_hash[:16]}...")
            except Exception as e:
                logger.warning(f"[HPO Parent Run] ✗ Could not compute study_key_hash for naming: {e}")
                import traceback
                logger.debug(f"Traceback: {traceback.format_exc()}")
        elif study_key_hash:
            logger.info(f"[HPO Parent Run] Using provided study_key_hash: {study_key_hash[:16]}...")
        else:
            logger.warning(
                f"[HPO Parent Run] study_key_hash is None and cannot be computed "
                f"(data_config={'present' if data_config else 'missing'}, "
                f"hpo_config={'present' if hpo_config else 'missing'})"
            )
        
        # Expose via env for subprocesses / notebooks that may not reconstruct context.
        if study_key_hash:
            os.environ["HPO_STUDY_KEY_HASH"] = study_key_hash
            logger.debug(f"[HPO Parent Run] Set HPO_STUDY_KEY_HASH env var: {study_key_hash[:16]}...")
        else:
            logger.warning("[HPO Parent Run] study_key_hash is None, NOT setting env var")

        logger.info(
            f"[HPO Parent Run] STEP 1: About to create context. study_key_hash value: "
            f"{study_key_hash[:16] + '...' if study_key_hash else 'None'} "
            f"(type: {type(study_key_hash).__name__}, is None: {study_key_hash is None})"
        )
        try:
            env = detect_platform()
            storage_env_val = detect_platform()
            logger.debug(f"[HPO Parent Run] Detected environment: {env}, storage_env: {storage_env_val}")
        except Exception as env_error:
            logger.warning(f"[HPO Parent Run] Error detecting platform: {env_error}, using defaults")
            env = "local"
            storage_env_val = "local"
        
        logger.info(
            f"[HPO Parent Run] STEP 2: Calling create_naming_context with study_key_hash: "
            f"{study_key_hash[:16] + '...' if study_key_hash else 'None'}"
        )
        try:
            hpo_parent_context = create_naming_context(
                process_type="hpo",
                model=backbone,
                environment=env,
                storage_env=storage_env_val,
                stage="hpo_sweep",
                study_name=study_name,
                trial_id=None,
                study_key_hash=study_key_hash,
            )
            logger.info(
                f"[HPO Parent Run] STEP 3: create_naming_context returned. "
                f"Context type: {type(hpo_parent_context).__name__}, "
                f"context.study_key_hash: {getattr(hpo_parent_context, 'study_key_hash', 'MISSING')}"
            )
        except Exception as ctx_error:
            logger.error(
                f"[HPO Parent Run] CRITICAL: Failed to create NamingContext: {ctx_error}. "
                f"study_key_hash={'preserved' if study_key_hash else 'lost'}"
            )
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise  # Re-raise to trigger the outer exception handler
        
        # Verify study_key_hash is set in context
        context_hash = getattr(hpo_parent_context, "study_key_hash", None)
        logger.info(
            f"[HPO Parent Run] Context created. study_key_hash in context: "
            f"{context_hash[:16] + '...' if context_hash else 'None'} "
            f"(passed: {study_key_hash[:16] + '...' if study_key_hash else 'None'})"
        )
        if study_key_hash:
            if context_hash != study_key_hash:
                logger.error(
                    f"[HPO Parent Run] CRITICAL: study_key_hash mismatch! "
                    f"passed={study_key_hash[:16]}..., "
                    f"context={context_hash[:16] if context_hash else 'None'}..."
                )
            else:
                logger.info(
                    f"[HPO Parent Run] ✓ study_key_hash verified in context: {study_key_hash[:16]}..."
                )
        else:
            logger.warning(
                f"[HPO Parent Run] study_key_hash is None when creating context. "
                f"This will result in 'unknown' in run name."
            )

        # Infer root_dir from output_dir by finding the "outputs" directory
        root_dir = None
        if output_dir:
            current = output_dir
            while current.name != "outputs" and current.parent != current:
                current = current.parent
            root_dir = (
                current.parent
                if current.name == "outputs"
                else output_dir.parent.parent.parent
            )

        if root_dir is None:
            root_dir = Path.cwd()

        # config_dir is inferred in build_mlflow_run_name, but we can set it explicitly here
        config_dir = root_dir / "config" if root_dir else None

        logger.info(
            f"[HPO Parent Run] Building MLflow run name: "
            f"output_dir={output_dir}, inferred_root_dir={root_dir}, config_dir={config_dir}, "
            f"study_name={hpo_parent_context.study_name if hpo_parent_context else None}, "
            f"study_key_hash={study_key_hash[:16] + '...' if study_key_hash else None}"
        )

        mlflow_run_name = build_mlflow_run_name(
            hpo_parent_context, config_dir, root_dir=root_dir, output_dir=output_dir
        )

        logger.info(
            f"[HPO Parent Run] Generated MLflow run name: {mlflow_run_name}"
        )

        return hpo_parent_context, mlflow_run_name
    except Exception as e:
        logger.warning(
            f"[HPO Parent Run] Exception during context creation: {e}, trying policy fallback"
        )
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        hpo_parent_context = None
        
        # Try to use naming policy even without full context
        try:
            from orchestration.jobs.tracking.naming.policy import load_naming_policy, format_run_name
            from orchestration.naming_centralized import create_naming_context
            from shared.platform_detection import detect_platform
            from pathlib import Path
            
            # Try to infer config_dir
            config_dir = Path.cwd() / "config"
            if not config_dir.exists():
                # Try parent directory
                config_dir = Path.cwd().parent / "config"
            
            if config_dir.exists():
                policy = load_naming_policy(config_dir)
                if policy and "run_names" in policy:
                    # Create minimal context for hpo_sweep - BUT PRESERVE study_key_hash if available!
                    logger.warning(
                        f"[HPO Parent Run] Creating minimal context in fallback. "
                        f"study_key_hash={'preserved' if study_key_hash else 'lost'}"
                    )
                    minimal_context = create_naming_context(
                        process_type="hpo",
                        model=backbone.split("-")[0] if "-" in backbone else backbone,
                        environment=detect_platform(),
                        study_name=study_name,
                        study_key_hash=study_key_hash,  # PRESERVE the hash in fallback!
                    )
                    mlflow_run_name = format_run_name("hpo_sweep", minimal_context, policy, config_dir)
                    logger.debug(f"Built run name using policy fallback: {mlflow_run_name}")
                    return minimal_context, mlflow_run_name  # Return minimal_context, not None
        except Exception as policy_error:
            logger.debug(f"Policy fallback also failed: {policy_error}, using legacy create_mlflow_run_name")
        
        # Last resort: use legacy function
        mlflow_run_name = create_mlflow_run_name(
            backbone,
            run_id,
            study_name,
            should_resume,
            checkpoint_enabled,
        )
        logger.warning(f"Using legacy create_mlflow_run_name (non-policy fallback): {mlflow_run_name}")
        return hpo_parent_context, mlflow_run_name


def commit_run_name_version(
    parent_run_id: str,
    hpo_parent_context: Any,
    mlflow_run_name: str,
    output_dir: Path,
) -> None:
    """
    Commit reserved version if auto-increment was used.

    Args:
        parent_run_id: MLflow parent run ID.
        hpo_parent_context: Naming context for HPO parent run.
        mlflow_run_name: Generated MLflow run name.
        output_dir: Output directory (used to infer root_dir and config_dir).
    """
    if not (parent_run_id and hpo_parent_context and mlflow_run_name):
        return

    try:
        from orchestration.jobs.tracking.mlflow_naming import (
            build_mlflow_run_key,
            build_mlflow_run_key_hash,
            build_counter_key,
        )
        from orchestration.jobs.tracking.config.loader import (
            get_naming_config,
            get_auto_increment_config,
        )
        from orchestration.jobs.tracking.mlflow_index import commit_run_name_version

        # Infer root_dir and config_dir from output_dir
        root_dir = None
        if output_dir:
            current = output_dir
            while current.name != "outputs" and current.parent != current:
                current = current.parent
            root_dir = (
                current.parent
                if current.name == "outputs"
                else output_dir.parent.parent.parent
            )
        if root_dir is None:
            root_dir = Path.cwd()
        config_dir = root_dir / "config" if root_dir else None

        # Check if auto-increment was used (run name has version suffix like _1, _2, etc.)
        version_match = re.search(r"_(\d+)$", mlflow_run_name)
        if version_match:
            version = int(version_match.group(1))
            logger.info(
                f"[HPO Commit] Found version {version} in run name '{mlflow_run_name}'"
            )

            # Check if auto-increment is enabled for HPO
            auto_inc_config = get_auto_increment_config(config_dir, "hpo")
            if auto_inc_config.get("enabled_for_process", False):
                # Rebuild counter_key from context
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

                # Commit the reserved version
                commit_run_name_version(
                    counter_key, parent_run_id, version, root_dir, config_dir
                )
                logger.info(
                    f"[HPO Commit] ✓ Successfully committed version {version} for HPO parent run {parent_run_id[:12]}..."
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
            f"[HPO Commit] Could not commit run name version: {e}", exc_info=True
        )

from __future__ import annotations

"""MLflow run setup utilities for HPO.

Handles MLflow run name creation, context setup, and version commit for HPO sweeps.

**Layering**:
- **MLflow setup/configuration** is handled by `infrastructure.tracking.mlflow.setup.setup_mlflow()`
  (SSOT). HPO orchestrators MUST call this before using functions in this module.
- **This module** focuses on HPO-specific naming context creation and run name generation.
  It does NOT handle MLflow setup/configuration (tracking URI, experiment setup).
- All functions in this module assume MLflow has already been configured via infrastructure setup.

**Related Modules**:
- `infrastructure.tracking.mlflow.setup` - SSOT for MLflow configuration (call this first)
- `training.execution.mlflow_setup` - Training run lifecycle (different domain)
- `infrastructure.naming.mlflow.run_names` - Run name generation utilities (used internally)

**Usage Pattern**:
    1. Call `infrastructure.tracking.mlflow.setup.setup_mlflow()` first (in HPO orchestrator)
    2. Then use `setup_hpo_mlflow_run()` to create naming context and run names
    3. Use `commit_run_name_version()` to commit reserved versions if auto-increment was used

**Boundaries**:
- **This module**: HPO naming context and run name generation (assumes MLflow configured)
- **infrastructure.tracking.mlflow.setup**: MLflow configuration (tracking URI, experiment) - SSOT
- **training.execution.mlflow_setup**: Training run lifecycle (different domain)

**Naming**:
- Uses systematic naming via `infrastructure.naming.mlflow.run_names.build_mlflow_run_name()`
- Naming policy must be available - no fallback to legacy naming

**Path Resolution**:
- This module trusts the provided `config_dir` parameter (DRY principle).
- Uses `infrastructure.paths.utils.resolve_project_paths_with_fallback()` (SSOT) for path resolution.
- Only infers `config_dir` when explicitly None and cannot be derived from other parameters.

**Hash Computation**:
- Uses v2 hash computation (`compute_study_key_hash_v2()`) when `train_config` is available.
- Callers should pass pre-computed `study_key_hash` when available to avoid recomputation.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from common.shared.logging_utils import get_logger

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
    train_config: Optional[Dict[str, Any]] = None,
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
        train_config: Optional training configuration dictionary. Required for v2 hash computation.
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
        # Use centralized hash utilities with proper fallback hierarchy.
        # The caller should pass pre-computed study_key_hash when available.
        if study_key_hash is None and data_config and hpo_config:
            try:
                # Use centralized hash utilities (SSOT) - trusts provided config_dir
                from infrastructure.tracking.mlflow.hash_utils import (
                    get_or_compute_study_key_hash,
                )
                
                # Resolve config_dir early if needed for hash computation
                # Trust provided config_dir parameter (DRY principle)
                resolved_config_dir = config_dir
                if resolved_config_dir is None:
                    # Only infer when truly None - use minimal resolution for hash computation
                    from infrastructure.paths.utils import resolve_project_paths_with_fallback
                    _, resolved_config_dir = resolve_project_paths_with_fallback(
                        output_dir=output_dir,
                        config_dir=None,
                    )
                
                # Use centralized utility with proper fallback hierarchy
                study_key_hash = get_or_compute_study_key_hash(
                    study_key_hash=None,  # Not provided yet
                    hpo_parent_run_id=None,  # Not available at this point
                    data_config=data_config,
                    hpo_config=hpo_config,
                    train_config=train_config,
                    backbone=backbone,
                    config_dir=resolved_config_dir,
                )
                if study_key_hash:
                    logger.debug("Computed study_key_hash using centralized utilities")
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

        # Trust provided config_dir parameter (DRY principle)
        # Only infer when explicitly None
        if config_dir is not None:
            # Derive root_dir from config_dir directly (trust provided value)
            from infrastructure.paths.repo import detect_repo_root
            root_dir = detect_repo_root(config_dir=config_dir)
        else:
            # Only infer when explicitly None
            from infrastructure.paths.utils import resolve_project_paths_with_fallback
            root_dir, config_dir = resolve_project_paths_with_fallback(
                output_dir=output_dir,
                config_dir=None,
            )

        mlflow_run_name = build_mlflow_run_name(
            hpo_parent_context,
            config_dir,
            root_dir=root_dir,
            output_dir=output_dir,
        )

        # Validate run_name is not None or empty
        # MLflow will auto-generate names (e.g., wheat_wheel_rr4dykvx) if run_name is None/empty
        if not mlflow_run_name or not mlflow_run_name.strip():
            error_msg = (
                f"CRITICAL: build_mlflow_run_name returned None or empty string. "
                f"hpo_parent_context={hpo_parent_context}, config_dir={config_dir}, "
                f"root_dir={root_dir}, output_dir={output_dir}"
            )
            logger.error(error_msg)
            raise ValueError(
                f"Cannot create HPO sweep run: run_name is None or empty. "
                f"This would cause MLflow to auto-generate a name. "
                f"Check naming policy configuration."
            )

        return hpo_parent_context, mlflow_run_name

    except Exception as e:
        # No fallback to legacy naming - raise error
        logger.error(
            f"Failed to create HPO MLflow run name: {e}. "
            "Naming policy must be available - no legacy fallback."
        )
        raise


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
        from infrastructure.naming.mlflow.config import (
            get_naming_config,
            get_auto_increment_config,
        )
        from infrastructure.tracking.mlflow.index import (
            commit_run_name_version as commit_version_internal,
        )

        # Trust provided config_dir parameter (DRY principle)
        # Only infer when explicitly None
        if config_dir is not None:
            # Derive root_dir from config_dir directly (trust provided value)
            from infrastructure.paths.repo import detect_repo_root
            root_dir = detect_repo_root(config_dir=config_dir)
        else:
            # Only infer when explicitly None
            from infrastructure.paths.utils import resolve_project_paths_with_fallback
            root_dir, config_dir = resolve_project_paths_with_fallback(
                output_dir=output_dir,
                config_dir=None,
            )

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

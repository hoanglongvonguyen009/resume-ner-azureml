"""Human-readable run name generation."""

from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Optional

from orchestration.naming_centralized import NamingContext
from orchestration.jobs.tracking.config.loader import (
    get_naming_config,
    get_auto_increment_config,
)
from orchestration.jobs.tracking.naming.run_keys import (
    build_mlflow_run_key,
    build_mlflow_run_key_hash,
    build_counter_key,
)


def _short(value: Optional[str], default: str = "unknown") -> str:
    """Return an 8-char short hash or a default if missing."""
    if not value:
        return default
    return value[:8]


def _strip_env_prefix(trial_id: str, environment: Optional[str]) -> str:
    """
    Strip environment prefix from trial_id if present.

    Args:
        trial_id: Trial ID string (may have env prefix like "local_hpo_...").
        environment: Environment name to strip.

    Returns:
        Trial ID without environment prefix.
    """
    if not environment or not trial_id:
        return trial_id

    prefix = f"{environment}_"
    if trial_id.startswith(prefix):
        return trial_id[len(prefix):]
    return trial_id


def build_mlflow_run_name(
    context: NamingContext,
    config_dir: Optional[Path] = None,
    root_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> str:
    """
    Build human-readable run name from context (may be overridden by Azure ML).

    Uses systematic naming with optional auto-increment versioning.

    Args:
        context: NamingContext with process type, model, etc.
        config_dir: Configuration directory (for loading naming config).
        root_dir: Project root directory (for counter storage).
        output_dir: Output directory (for inferring root_dir if not provided).

    Returns:
        Human-readable run name string.
    """
    # Infer root_dir from output_dir if not provided
    if root_dir is None and output_dir is not None:
        root_dir = output_dir.parent.parent if output_dir else None

    # Fallback to current directory if still None
    if root_dir is None:
        root_dir = Path.cwd()

    naming_config = get_naming_config(config_dir)
    run_name_config = naming_config.get("run_name", {})

    if context.process_type == "hpo":
        # Prefer hashed study/trial identities; fall back to legacy trial_id or env hints.
        env = context.storage_env if hasattr(context, "storage_env") else context.environment

        # 1) Use study_key_hash from context if present.
        study_hash = getattr(context, "study_key_hash", None)
        # 2) Else fall back to env var (allows passing through subprocesses/notebooks).
        if not study_hash:
            study_hash = os.environ.get("HPO_STUDY_KEY_HASH")

        # Avoid "study-study-unknown" by keeping the fallback bare.
        study_part = _short(study_hash, "unknown")

        # Detect if this is a trial run (not parent sweep)
        # Robust detection: if trial_id exists, it's a trial run
        is_trial_run = context.trial_id is not None
        stage = getattr(context, "stage", None)
        # Also check stage for explicit classification
        if stage == "hpo_trial":
            is_trial_run = True
        elif stage == "hpo_sweep":
            is_trial_run = False

        # Optional trial hash segment (mainly for trial-level runs, not the sweep parent).
        trial_hash = getattr(context, "trial_key_hash", None)
        trial_segment = f"_trial-{_short(trial_hash)}" if trial_hash else ""

        # Include trial number in name for trial runs (use explicit trial_number, not parsed string)
        trial_number_segment = ""
        if is_trial_run:
            trial_number = getattr(context, "trial_number", None)
            if trial_number is not None:
                # Use explicit trial_number from Optuna (robust, no string parsing)
                trial_number_segment = f"_t{int(trial_number)}"
            elif trial_hash:
                # Fallback: use short trial_key_hash if trial_number not available
                trial_number_segment = f"_trial-{_short(trial_hash)}"
            # If neither available, leave empty (will rely on trial_segment or fallback)

        # Optional semantic suffix from study_name (for parent runs only, not trials).
        # Keep trial names minimal and hash-driven.
        semantic_suffix = ""
        if not is_trial_run:
            study_name = getattr(context, "study_name", None)
            if study_name:
                label = study_name
                if label.startswith("hpo_"):
                    label = label[len("hpo_") :]
                label = label.replace(" ", "").replace("/", "-")
                semantic_suffix = f"_{label}"

        # Build base name
        # For trials: minimal hash-driven name with trial number
        # For parent: includes semantic suffix for UX
        if is_trial_run:
            base_name = f"{env}_{context.model}_hpo_trial_study-{study_part}{trial_number_segment}"
        else:
            base_name = f"{env}_{context.model}_hpo_study-{study_part}{semantic_suffix}"

        # For trials, enforce strict identity when study_hash is missing.
        if stage == "hpo_trial" and study_hash is None:
            raise ValueError(
                "HPO trial run name built without study_key_hash; "
                "check study identity propagation."
            )

        auto_inc_config = get_auto_increment_config(config_dir, "hpo")
        if auto_inc_config.get("enabled") and auto_inc_config.get("processes", {}).get("hpo"):
            try:
                run_key = build_mlflow_run_key(context)
                run_key_hash = build_mlflow_run_key_hash(run_key)

                counter_key = build_counter_key(
                    naming_config.get("project_name", "resume-ner"),
                    "hpo",
                    run_key_hash,
                    env or "",
                )

                from orchestration.jobs.tracking.mlflow_index import reserve_run_name_version

                temp_run_id = f"pending_{datetime.now().isoformat()}"
                version = reserve_run_name_version(
                    counter_key,
                    temp_run_id,
                    root_dir,
                    config_dir,
                )
                return f"{base_name}_{version}"
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not reserve version for HPO run name: {e}, using fallback"
                )

        # Fallback: include legacy trial_id if hashes missing
        if not getattr(context, "study_key_hash", None) or not getattr(context, "trial_key_hash", None):
            if context.trial_id:
                return f"{env}_{context.trial_id}"
        return base_name

    elif context.process_type == "hpo_refit":
        # Refit run name: use hash-driven pattern like trials for consistency
        env = context.storage_env if hasattr(context, "storage_env") else context.environment
        
        # Use study_key_hash and trial_key_hash if available (hash-driven)
        study_hash = getattr(context, "study_key_hash", None)
        trial_hash = getattr(context, "trial_key_hash", None)
        trial_number = getattr(context, "trial_number", None)
        
        if study_hash:
            study_part = _short(study_hash, "unknown")
            if trial_hash:
                trial_hash_part = f"_trial-{_short(trial_hash)}"
            else:
                trial_hash_part = ""
            
            # Include trial_number for readability (e.g., _t1)
            trial_num_part = f"_t{int(trial_number)}" if trial_number is not None else ""
            
            base_name = f"{env}_{context.model}_hpo_refit_study-{study_part}{trial_hash_part}{trial_num_part}"
            
            # Apply auto-increment versioning if enabled (use "hpo" since refit is part of HPO workflow)
            auto_inc_config = get_auto_increment_config(config_dir, "hpo")
            if auto_inc_config.get("enabled") and auto_inc_config.get("processes", {}).get("hpo"):
                try:
                    run_key = build_mlflow_run_key(context)
                    run_key_hash = build_mlflow_run_key_hash(run_key)
                    
                    counter_key = build_counter_key(
                        naming_config.get("project_name", "resume-ner"),
                        "hpo_refit",
                        run_key_hash,
                        env or "",
                    )
                    
                    from orchestration.jobs.tracking.mlflow_index import reserve_run_name_version
                    
                    temp_run_id = f"pending_{datetime.now().isoformat()}"
                    version = reserve_run_name_version(
                        counter_key,
                        temp_run_id,
                        root_dir,
                        config_dir,
                    )
                    return f"{base_name}_{version}"
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Could not reserve version for refit run name: {e}, using fallback"
                    )
            
            return base_name
        else:
            # Fallback to legacy pattern if hashes not available
            env_prefix = f"{env}_" if env else ""
            trial_short = (
                context.trial_id[:30]
                if context.trial_id and len(context.trial_id) > 30
                else (context.trial_id or "unknown")
            )
            return f"{env_prefix}hpo_refit_{context.model}_{trial_short}"

    elif context.process_type == "benchmarking":
        env = context.storage_env if hasattr(context, "storage_env") else context.environment
        study_part = _short(getattr(context, "study_key_hash", None), "study-unknown")
        trial_part = _short(getattr(context, "trial_key_hash", None), "trial-unknown")
        bench_part = _short(getattr(context, "benchmark_config_hash", None), "bench-unknown")

        base_name = f"{env}_{context.model}_benchmark_study-{study_part}_trial-{trial_part}_bench-{bench_part}"

        auto_inc_config = get_auto_increment_config(config_dir, "benchmarking")
        if auto_inc_config.get("enabled") and auto_inc_config.get("processes", {}).get("benchmarking"):
            try:
                run_key = build_mlflow_run_key(context)
                run_key_hash = build_mlflow_run_key_hash(run_key)

                counter_key = build_counter_key(
                    naming_config.get("project_name", "resume-ner"),
                    "benchmarking",
                    run_key_hash,
                    env or "",
                )

                from orchestration.jobs.tracking.mlflow_index import reserve_run_name_version

                temp_run_id = f"pending_{datetime.now().isoformat()}"
                version = reserve_run_name_version(
                    counter_key,
                    temp_run_id,
                    root_dir,
                    config_dir,
                )

                return f"{base_name}_{version}"
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not reserve version for benchmarking run name: {e}, using fallback"
                )

        # Fallback to legacy trial_id if hashes missing
        if context.trial_id:
            return f"{env}_{context.trial_id}"
        return base_name

    elif context.process_type == "final_training":
        env = context.storage_env if hasattr(context, "storage_env") else context.environment
        shorten_fingerprints = run_name_config.get("shorten_fingerprints", True)
        max_length = run_name_config.get("max_length", 100)

        spec_short = _short(context.spec_fp, "spec-unknown") if shorten_fingerprints else (context.spec_fp or "unknown")
        exec_short = _short(context.exec_fp, "exec-unknown") if shorten_fingerprints else (context.exec_fp or "unknown")

        name = f"{env}_{context.model}_final_training_spec-{spec_short}_exec-{exec_short}_v{context.variant}"
        if len(name) > max_length:
            # Truncate model name if needed
            model_max_len = max_length - len(name) + len(context.model)
            model_short = context.model[:model_max_len] if model_max_len > 0 else context.model[:10]
            name = f"{env}_{model_short}_final_training_spec-{spec_short}_exec-{exec_short}_v{context.variant}"
        return name

    elif context.process_type == "conversion":
        env = context.storage_env if hasattr(context, "storage_env") else context.environment
        shorten_fingerprints = run_name_config.get("shorten_fingerprints", True)
        conv_short = _short(context.conv_fp, "conv-unknown") if shorten_fingerprints else (context.conv_fp or "unknown")
        parent_id = context.parent_training_id or "parent-unknown"
        return f"{env}_{context.model}_conversion_{parent_id}_conv-{conv_short}"

    else:
        return f"{context.process_type}_{context.model}_unknown"


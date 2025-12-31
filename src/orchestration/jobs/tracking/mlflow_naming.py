"""MLflow naming utilities: run keys, hashing, tag building, and sanitization."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from orchestration.naming_centralized import NamingContext
from orchestration.jobs.tracking.mlflow_config_loader import get_naming_config, get_auto_increment_config


def build_mlflow_run_key(context: NamingContext) -> str:
    """
    Build stable run_key identifier from context using stage-specific templates.

    Templates:
    - HPO: "hpo:{model}:{trial_id}"
    - Benchmarking: "benchmark:{model}:{trial_id}"
    - Final Training: "final_training:{model}:spec_{spec_fp}:exec_{exec_fp}:v{variant}"
    - Conversion: "conversion:{model}:{parent_training_id}:conv_{conv_fp}"

    Args:
        context: NamingContext with all required information.

    Returns:
        Canonical run_key string.

    Raises:
        ValueError: If required fields are missing for the process type.
    """
    if context.process_type == "hpo":
        if not context.trial_id:
            raise ValueError("HPO requires trial_id for run_key")
        return f"hpo:{context.model}:{context.trial_id}"

    elif context.process_type == "benchmarking":
        if not context.trial_id:
            raise ValueError("Benchmarking requires trial_id for run_key")
        return f"benchmark:{context.model}:{context.trial_id}"

    elif context.process_type == "final_training":
        if not context.spec_fp or not context.exec_fp:
            raise ValueError(
                "Final training requires spec_fp and exec_fp for run_key")
        return f"final_training:{context.model}:spec_{context.spec_fp}:exec_{context.exec_fp}:v{context.variant}"

    elif context.process_type == "conversion":
        if not context.parent_training_id or not context.conv_fp:
            raise ValueError(
                "Conversion requires parent_training_id and conv_fp for run_key")
        return f"conversion:{context.model}:{context.parent_training_id}:conv_{context.conv_fp}"

    else:
        # Fallback for unknown process types
        return f"{context.process_type}:{context.model}:unknown"


def build_mlflow_run_key_hash(run_key: str) -> str:
    """
    Build SHA256 hash of run_key for tag storage.

    MLflow tags have length limits (typically 250 chars), so we hash
    long run_keys to ensure they fit in tags.

    Args:
        run_key: Canonical run_key string.

    Returns:
        SHA256 hash hex string (always 64 characters).
    """
    return hashlib.sha256(run_key.encode('utf-8')).hexdigest()


def _extract_base_name_from_study_name(study_name: str) -> str:
    """
    Extract base name from HPO study_name (remove version suffix if present).

    Removes trailing version patterns like .{digits} or _{digits}.
    Used for display name generation only, NOT for counter key.

    Args:
        study_name: Study name that may contain version suffix (e.g., "hpo_distilbert_smoke_test_3.23").

    Returns:
        Base name without version suffix (e.g., "hpo_distilbert_smoke_test_3").
    """
    if not study_name:
        return study_name

    # Remove trailing .{digits} pattern
    base = re.sub(r'\.\d+$', '', study_name)
    # Remove trailing _{digits} pattern
    base = re.sub(r'_\d+$', '', base)

    return base


def _strip_env_prefix(run_name: str, env: str) -> str:
    """
    Remove environment prefix for consistent base name extraction.

    Used for display name generation only, NOT for counter key.

    Args:
        run_name: Run name that may have environment prefix (e.g., "local_hpo_distilbert_smoke_test_3").
        env: Environment name to strip (e.g., "local").

    Returns:
        Run name without environment prefix (e.g., "hpo_distilbert_smoke_test_3").
    """
    if not run_name or not env:
        return run_name

    prefix = f"{env}_"
    if run_name.startswith(prefix):
        return run_name[len(prefix):]

    return run_name


def build_counter_key(project: str, process_type: str, run_key_hash: str, env: str) -> str:
    """
    Build counter key using stable identity hash (not base_name).

    Counter keys use run_key_hash to ensure numbering never mixes unrelated studies
    that share similar display names.

    Args:
        project: Project name (e.g., "resume-ner").
        process_type: Process type (e.g., "hpo" or "benchmarking").
        run_key_hash: SHA256 hash of run_key (stable identity).
        env: Environment name (e.g., "local", "colab", "kaggle").

    Returns:
        Counter key string (format: "{project}:{process_type}:{run_key_hash}:{env}").
        Example: "resume-ner:hpo:abc123def456...:local"
    """
    return f"{project}:{process_type}:{run_key_hash}:{env}"


def build_mlflow_run_name(
    context: NamingContext,
    config_dir: Optional[Path] = None,
    root_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> str:
    """
    Build human-readable run name from context (may be overridden by Azure ML).
    """
    # Infer root_dir from output_dir if not provided
    if root_dir is None and output_dir is not None:
        root_dir = output_dir.parent.parent if output_dir else None

    # Fallback to current directory if still None
    if root_dir is None:
        root_dir = Path.cwd()

    naming_config = get_naming_config(config_dir)
    run_name_config = naming_config.get("run_name", {})
    shorten_fingerprints = run_name_config.get("shorten_fingerprints", True)

    if context.process_type == "hpo":
        env_prefix = f"{context.environment}_" if context.environment else ""

        if context.trial_id and context.trial_id.startswith("hpo_"):
            base_without_env = _strip_env_prefix(
                context.trial_id, context.environment
            )

            auto_inc_config = get_auto_increment_config(config_dir, "hpo")
            if (
                auto_inc_config.get("enabled")
                and auto_inc_config.get("processes", {}).get("hpo")
            ):
                try:
                    run_key = build_mlflow_run_key(context)
                    run_key_hash = build_mlflow_run_key_hash(run_key)

                    counter_key = build_counter_key(
                        naming_config.get("project_name", "resume-ner"),
                        "hpo",
                        run_key_hash,
                        context.environment or "",
                    )

                    from orchestration.jobs.tracking.mlflow_index import (
                        reserve_run_name_version,
                    )

                    temp_run_id = f"pending_{datetime.now().isoformat()}"
                    version = reserve_run_name_version(
                        counter_key,
                        temp_run_id,
                        root_dir,
                        config_dir,
                    )
                    return f"{env_prefix}{base_without_env}_{version}"
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Could not reserve version for HPO run name: {e}, using fallback"
                    )
                    return f"{env_prefix}{context.trial_id}"
            else:
                return f"{env_prefix}{context.trial_id}"
        else:
            trial_short = (
                context.trial_id[:20]
                if context.trial_id and len(context.trial_id) > 20
                else (context.trial_id or "unknown")
            )
            return f"{env_prefix}hpo_{context.model}_{trial_short}"

    elif context.process_type == "benchmarking":
        base_name = f"benchmark_{context.model}"

        auto_inc_config = get_auto_increment_config(
            config_dir, "benchmarking"
        )
        if (
            auto_inc_config.get("enabled")
            and auto_inc_config.get("processes", {}).get("benchmarking")
        ):
            try:
                run_key = build_mlflow_run_key(context)
                run_key_hash = build_mlflow_run_key_hash(run_key)

                counter_key = build_counter_key(
                    naming_config.get("project_name", "resume-ner"),
                    "benchmarking",
                    run_key_hash,
                    context.environment or "",
                )

                from orchestration.jobs.tracking.mlflow_index import (
                    reserve_run_name_version,
                )

                temp_run_id = f"pending_{datetime.now().isoformat()}"
                version = reserve_run_name_version(
                    counter_key,
                    temp_run_id,
                    root_dir,
                    config_dir,
                )

                if context.trial_id:
                    return f"{base_name}_{context.trial_id}_{version}"
                else:
                    return f"{base_name}_{version}"
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Could not reserve version for benchmarking run name: {e}, using fallback"
                )
                trial_short = (
                    context.trial_id[:20]
                    if context.trial_id and len(context.trial_id) > 20
                    else (context.trial_id or "unknown")
                )
                return f"{base_name}_{trial_short}"
        else:
            trial_short = (
                context.trial_id[:20]
                if context.trial_id and len(context.trial_id) > 20
                else (context.trial_id or "unknown")
            )
            return f"{base_name}_{trial_short}"

    elif context.process_type == "final_training":
        if shorten_fingerprints:
            spec_short = (
                context.spec_fp[:8]
                if context.spec_fp
                else "unknown"
            )


def sanitize_tag_value(
    value: str,
    max_length: Optional[int] = None,
    config_dir: Optional[Path] = None,
) -> str:
    """
    Sanitize tag value for MLflow backend compatibility.

    MLflow tags have restrictions:
    - ASCII characters only (some backends)
    - Maximum length (typically 250 chars)
    - No control characters
    - Trimmed whitespace

    Args:
        value: Original tag value.
        max_length: Maximum allowed length (if None, reads from config, default 250).
        config_dir: Optional config directory for reading max_length from config.

    Returns:
        Sanitized tag value safe for MLflow backends.
    """
    # Get max_length from config if not provided
    if max_length is None:
        naming_config = get_naming_config(config_dir)
        max_length = naming_config.get("tags", {}).get("max_length", 250)
    if not value:
        return ""

    # Convert to string if not already
    value = str(value)

    # Remove control characters (keep printable ASCII)
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    # Try to keep ASCII, replace non-ASCII with safe alternatives
    try:
        value = value.encode('ascii', errors='replace').decode('ascii')
        # Replace replacement characters with underscore
        value = value.replace('\ufffd', '_')
    except (UnicodeEncodeError, UnicodeDecodeError):
        # If encoding fails, use a hash of the value
        value = hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]

    # Trim whitespace
    value = value.strip()

    # Enforce max length
    if len(value) > max_length:
        # Truncate, but try to preserve meaningful part
        value = value[:max_length]

    return value


def build_mlflow_tags(
    context: Optional[NamingContext] = None,
    output_dir: Optional[Path] = None,
    parent_run_id: Optional[str] = None,
    group_id: Optional[str] = None,
    project_name: Optional[str] = None,
    config_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """
    Build code.* tags dictionary for MLflow runs.

    Always sets minimal tags (even without context):
    - code.stage: Process type or "unknown"
    - code.model: Model name or "unknown"
    - code.env: Environment or detected
    - code.created_by: User/system identifier
    - code.project: Project name or default

    If context provided, also sets:
    - code.run_key: Sanitized run_key (if short enough, <= 200 chars)
    - code.run_key_hash: SHA256 hash of run_key (always)
    - code.spec_fp, code.exec_fp, code.variant, code.trial_id (if available)
    - code.output_dir: Output directory path (if provided)
    - code.parent_run_id: Parent run ID (if provided)
    - code.group_id: Group/session identifier (if provided)

    Args:
        context: Optional NamingContext with full information.
        output_dir: Optional output directory path.
        parent_run_id: Optional parent MLflow run ID.
        group_id: Optional group/session identifier.
        project_name: Optional project name (overrides config if provided).
        config_dir: Optional config directory for reading project_name and tag settings.

    Returns:
        Dictionary of sanitized tag key-value pairs.
    """
    import os
    from shared.platform_detection import detect_platform

    # Get config for project_name and tag settings
    naming_config = get_naming_config(config_dir)
    tag_max_length = naming_config.get("tags", {}).get("max_length", 250)
    sanitize_tags = naming_config.get("tags", {}).get("sanitize", True)

    tags: Dict[str, str] = {}

    # Always set minimal tags
    if context:
        if sanitize_tags:
            tags["code.stage"] = sanitize_tag_value(
                context.process_type, max_length=tag_max_length, config_dir=config_dir)
            tags["code.model"] = sanitize_tag_value(
                context.model, max_length=tag_max_length, config_dir=config_dir)
            tags["code.env"] = sanitize_tag_value(
                context.environment, max_length=tag_max_length, config_dir=config_dir)
        else:
            tags["code.stage"] = context.process_type
            tags["code.model"] = context.model
            tags["code.env"] = context.environment
    else:
        env = detect_platform()
        if sanitize_tags:
            tags["code.stage"] = "unknown"
            tags["code.model"] = "unknown"
            tags["code.env"] = sanitize_tag_value(
                env, max_length=tag_max_length, config_dir=config_dir)
        else:
            tags["code.stage"] = "unknown"
            tags["code.model"] = "unknown"
            tags["code.env"] = env

    # Created by (user or system)
    created_by = os.environ.get("USER", os.environ.get("USERNAME", "system"))
    if sanitize_tags:
        tags["code.created_by"] = sanitize_tag_value(
            created_by, max_length=tag_max_length, config_dir=config_dir)
    else:
        tags["code.created_by"] = created_by

    # Project name (use parameter if provided, otherwise from config)
    if project_name is None:
        project_name = naming_config.get("project_name", "resume-ner")

    if sanitize_tags:
        tags["code.project"] = sanitize_tag_value(
            project_name, max_length=tag_max_length, config_dir=config_dir)
    else:
        tags["code.project"] = project_name

    # If context provided, add full tags
    if context:
        # Build run_key and hash
        try:
            run_key = build_mlflow_run_key(context)
            run_key_hash = build_mlflow_run_key_hash(run_key)

            # Store run_key_hash always (64 chars, safe)
            tags["code.run_key_hash"] = run_key_hash

            # Store run_key only if short enough (leave room for other tags)
            if len(run_key) <= 200:
                if sanitize_tags:
                    tags["code.run_key"] = sanitize_tag_value(
                        run_key, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.run_key"] = run_key

            # Add context-specific fields
            if context.spec_fp:
                if sanitize_tags:
                    tags["code.spec_fp"] = sanitize_tag_value(
                        context.spec_fp, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.spec_fp"] = context.spec_fp
            if context.exec_fp:
                if sanitize_tags:
                    tags["code.exec_fp"] = sanitize_tag_value(
                        context.exec_fp, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.exec_fp"] = context.exec_fp
            if context.variant:
                if sanitize_tags:
                    tags["code.variant"] = sanitize_tag_value(
                        str(context.variant), max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.variant"] = str(context.variant)
            if context.trial_id:
                if sanitize_tags:
                    tags["code.trial_id"] = sanitize_tag_value(
                        context.trial_id, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.trial_id"] = context.trial_id
            if context.parent_training_id:
                if sanitize_tags:
                    tags["code.parent_training_id"] = sanitize_tag_value(
                        context.parent_training_id, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.parent_training_id"] = context.parent_training_id
            if context.conv_fp:
                if sanitize_tags:
                    tags["code.conv_fp"] = sanitize_tag_value(
                        context.conv_fp, max_length=tag_max_length, config_dir=config_dir)
                else:
                    tags["code.conv_fp"] = context.conv_fp
        except ValueError:
            # If run_key can't be built, at least we have minimal tags
            pass

    # Add optional fields
    if output_dir:
        if sanitize_tags:
            tags["code.output_dir"] = sanitize_tag_value(
                str(output_dir), max_length=tag_max_length, config_dir=config_dir)
        else:
            tags["code.output_dir"] = str(output_dir)

    if parent_run_id:
        if sanitize_tags:
            tags["code.parent_run_id"] = sanitize_tag_value(
                parent_run_id, max_length=tag_max_length, config_dir=config_dir)
        else:
            tags["code.parent_run_id"] = parent_run_id

    if group_id:
        if sanitize_tags:
            tags["code.group_id"] = sanitize_tag_value(
                group_id, max_length=tag_max_length, config_dir=config_dir)
        else:
            tags["code.group_id"] = group_id

    return tags

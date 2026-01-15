"""MLflow naming utilities: run keys, names, tags, and hashing.

DEPRECATED: This package is deprecated. Please import directly from infrastructure.naming modules:
- infrastructure.naming.mlflow.run_names
- infrastructure.naming.display_policy
- infrastructure.naming.mlflow.run_keys
- infrastructure.naming.mlflow.tags
"""

import warnings

# Issue deprecation warning when package is imported
warnings.warn(
    "orchestration.jobs.tracking.naming is deprecated. "
    "Please import directly from infrastructure.naming modules instead. "
    "This package will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from infrastructure.naming.mlflow.run_keys import (
    build_mlflow_run_key,
    build_mlflow_run_key_hash,
    build_counter_key,
)
from infrastructure.naming.mlflow.run_names import (
    build_mlflow_run_name,
)
from orchestration.jobs.tracking.naming.tags import (
    build_mlflow_tags,
    sanitize_tag_value,
)
from infrastructure.naming.mlflow.hpo_keys import (
    build_hpo_study_key,
    build_hpo_study_key_hash,
    build_hpo_study_family_key,
    build_hpo_study_family_hash,
    build_hpo_trial_key,
    build_hpo_trial_key_hash,
)
from infrastructure.naming.mlflow.refit_keys import (
    compute_refit_protocol_fp,
)
from orchestration.jobs.tracking.naming.policy import (
    load_naming_policy,
    format_run_name,
    parse_parent_training_id,
)

__all__ = [
    "build_mlflow_run_key",
    "build_mlflow_run_key_hash",
    "build_counter_key",
    "build_mlflow_run_name",
    "build_mlflow_tags",
    "sanitize_tag_value",
    "build_hpo_study_key",
    "build_hpo_study_key_hash",
    "build_hpo_study_family_key",
    "build_hpo_study_family_hash",
    "build_hpo_trial_key",
    "build_hpo_trial_key_hash",
    "compute_refit_protocol_fp",
    "load_naming_policy",
    "format_run_name",
    "parse_parent_training_id",
]

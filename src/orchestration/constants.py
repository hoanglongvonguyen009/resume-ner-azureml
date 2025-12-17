"""Stable orchestration identifiers shared across notebooks and scripts.

These are *not* behaviour knobs (those live in YAML), but naming/selection
constants that rarely change and are used in multiple places.
"""

# Stage names (must match keys under `stages:` in experiment config YAML)
STAGE_SMOKE = "smoke"
STAGE_HPO = "hpo"
STAGE_TRAINING = "training"

# Experiment selection (maps to config/experiment/<name>.yaml)
EXPERIMENT_NAME = "resume_ner_baseline"

# Model & registry naming
MODEL_NAME = "resume-ner-onnx"
PROD_STAGE = "prod"

# Job / display names
CONVERSION_JOB_NAME = "model-conversion"

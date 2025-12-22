from __future__ import annotations

# NOTE:
# Azure-dependent modules (sweeps, training, conversion, runtime, selection)
# can trigger ImportError in environments without the Azure ML SDK (e.g., Colab).
# To keep local utilities usable, we lazily import these modules and ignore
# ImportError so that local_* helpers continue to work.

# Azure ML-dependent imports (optional)
try:
    from .sweeps import (
        create_search_space,
        create_dry_run_sweep_job_for_backbone,
        create_hpo_sweep_job_for_backbone,
        validate_sweep_job,
    )
    from .training import (
        build_final_training_config,
        create_final_training_job,
        validate_final_training_job,
    )
    from .runtime import submit_and_wait_for_job
    from .selection import select_best_configuration
    from .conversion import (
        get_checkpoint_output_from_training_job,
        create_conversion_job,
        validate_conversion_job,
    )
except ImportError:
    # Azure ML SDK not available; skip Azure-specific helpers.
    create_search_space = None
    create_dry_run_sweep_job_for_backbone = None
    create_hpo_sweep_job_for_backbone = None
    validate_sweep_job = None
    build_final_training_config = None
    create_final_training_job = None
    validate_final_training_job = None
    submit_and_wait_for_job = None
    select_best_configuration = None
    get_checkpoint_output_from_training_job = None
    create_conversion_job = None
    validate_conversion_job = None

# Local-only utilities (always available)
from .local_sweeps import (
    run_local_hpo_sweep,
    translate_search_space_to_optuna,
)
from .local_selection import (
    select_best_configuration_across_studies,
    extract_best_config_from_study,
    load_best_trial_from_disk,
)

__all__ = [
    # Azure helpers (may be None if Azure SDK missing)
    "create_search_space",
    "create_dry_run_sweep_job_for_backbone",
    "create_hpo_sweep_job_for_backbone",
    "validate_sweep_job",
    "build_final_training_config",
    "create_final_training_job",
    "validate_final_training_job",
    "submit_and_wait_for_job",
    "select_best_configuration",
    "get_checkpoint_output_from_training_job",
    "create_conversion_job",
    "validate_conversion_job",
    # Local helpers (always available)
    "run_local_hpo_sweep",
    "translate_search_space_to_optuna",
    "select_best_configuration_across_studies",
    "extract_best_config_from_study",
    "load_best_trial_from_disk",
]

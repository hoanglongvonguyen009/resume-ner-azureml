"""Configuration loading, validation, and domain-specific config building."""

from .merging import (
    merge_configs_with_precedence,
    apply_argument_overrides,
)
from .run_mode import (
    RunMode,
    get_run_mode,
    is_force_new,
    is_reuse_if_exists,
    is_resume_if_incomplete,
)
from .variants import (
    compute_next_variant,
    find_existing_variants,
)

__all__ = [
    "merge_configs_with_precedence",
    "apply_argument_overrides",
    # Run mode utilities
    "RunMode",
    "get_run_mode",
    "is_force_new",
    "is_reuse_if_exists",
    "is_resume_if_incomplete",
    # Variant utilities
    "compute_next_variant",
    "find_existing_variants",
]


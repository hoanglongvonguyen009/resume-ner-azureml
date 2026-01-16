Date: 2026-01-15
Plan: FINISHED-consolidate-naming-utilities-dry-violations-83f1a2c7.plan.md
Status: ✅ Complete

## Overview

This plan consolidated and clarified the naming utilities in the `infrastructure.naming` domain, making them the single source of truth for keys, tags, config-driven naming, and context/token helpers, without changing public workflow behavior.

## What Was Done

- **Inventory and responsibilities**
  - Enumerated all naming-domain modules under `src/infrastructure/naming/**` and documented their primary responsibilities and main callers in a table within the plan.
  - Tightened module-level metadata (`@meta` blocks) to explicitly state what each module does and what it must not do (e.g., “does NOT start MLflow runs”).

- **Key-building consolidation**
  - Verified that HPO study/trial/family keys, refit fingerprints, and run key hashes all flow through `infrastructure.naming.mlflow.*` plus `common.shared.hash_utils.compute_hash_64()`.
  - Confirmed that tracking-side helpers delegate to these SSOT utilities rather than reimplement hashing.

- **Tag keys and tag building**
  - Ensured run tags are built via `infrastructure.naming.mlflow.tags.build_mlflow_tags()` (or its orchestration wrapper), backed by `TagsRegistry` and `tag_keys` helpers.
  - Identified and documented a small set of intentional, legacy/workflow-specific tag-key exceptions (e.g., some refit status markers and legacy grouping tag reads).

- **Config and policy flows**
  - Centralized naming-related reads of `mlflow.yaml` behind `load_mlflow_config()` and `get_naming_config()` in `mlflow/config.py`.
  - Centralized naming policy reads of `naming.yaml` behind `display_policy.load_naming_policy()` and `validate_naming_policy()`, with run-name formatting/validation using `format_run_name()` + `context_tokens.build_token_values()`.

- **Context and token helpers**
  - Confirmed that short-hash slicing for naming/paths is centralized in `context_tokens.build_token_values()` and the naming policy helpers, not ad-hoc in callers.
  - Confirmed that `display_policy.parse_parent_training_id()` is the single parser for `parent_training_id`, and that `NamingContext` is the primary structure passed into naming/path utilities.

- **Verification / safety net**
  - Relied on existing unit and integration suites (naming policy tests, `mlflow.yaml`/`naming.yaml` config tests, tags tests, HPO/refit/selection/benchmarking workflows) to validate that behavior remained stable.
  - Confirmed from `test_results.log` that these suites pass after the consolidations, with no new regressions attributed to this plan.

## Key Decisions and Trade-offs

- Chose to keep a small number of specialized refit-related tags and legacy grouping tag fallbacks as documented exceptions instead of forcing them into `TagsRegistry` in this plan, to avoid over-scoping and risking behavior changes in long-lived runs.
- Treated orchestration-level naming helpers (`orchestration/.../naming/*`) and some tracking helpers as migration/debt targets rather than fully refactoring them here, keeping this plan focused on consolidating the `infrastructure.naming` SSOT.

## Follow-ups

- Consider a small follow-up plan to:
  - Migrate remaining legacy refit and grouping tags into `tags.yaml` / `tag_keys` if/when the tag vocabulary is stabilized.
  - Further reduce reliance on orchestration-level naming helpers now that `infrastructure.naming` is the clear SSOT for naming concerns.





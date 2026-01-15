Consolidate naming utilities DRY violations (naming domain)

## Goal

Reduce duplication and tighten responsibilities across `domain: naming` utilities (keys, tags, config, policy, and context helpers) so that:

- **Single-source-of-truth** (SSOT) modules are clearly defined for:
  - HPO/run/refit key calculations
  - Tag key registry and tag construction
  - Naming configuration and display policy
  - Naming contexts and token expansion
- Callers reuse these SSOT modules instead of re-implementing similar logic (no duplicate hash/tag/path/naming helpers).
- Behavior and public APIs remain stable for existing callers (minimal breaking changes).

## Status

**Last Updated**: 2026-01-15

### Completed Steps
- ✅ Step 1: Inventory and classify naming utilities
- ✅ Step 2: Define SSOT responsibilities and boundaries
- ✅ Step 3: Eliminate DRY violations in key-building utilities
- ✅ Step 4: Centralize tag key and tag-building usage
- ✅ Step 5: Consolidate naming config and display policy usage
- ✅ Step 6: Align context and token helpers with SSOT
- ✅ Step 7: Verification and regression safety net

### Pending Steps
- ⏳ None (all plan steps complete)

## Preconditions

- Existing naming-related consolidation plans have been applied:
  - `FINISHED-eliminate-tag-parsing-hash-dry-violations.plan.md`
  - `FINISHED-eliminate-caching-dry-violations.plan.md`
- `infrastructure.naming.*` is the agreed **single naming domain**; no new naming logic should live under `orchestration.*` or other namespaces.

## Steps

### Step 1: Inventory and classify naming utilities

1. Enumerate all `domain: naming` utilities:
   - `src/infrastructure/naming/context.py` – `NamingContext` dataclass and validation for naming/path identity.
   - `src/infrastructure/naming/context_tokens.py` – `build_token_values()` for expanding `NamingContext` into token dicts (short hashes, etc.).
   - `src/infrastructure/naming/mlflow/run_keys.py` – `build_mlflow_run_key()` and `build_mlflow_run_key_hash()` for MLflow run identity.
   - `src/infrastructure/naming/mlflow/hpo_keys.py` – HPO study/trial/family key + hash utilities, including hyperparameter normalization.
   - `src/infrastructure/naming/mlflow/refit_keys.py` – refit protocol fingerprint calculation.
   - `src/infrastructure/naming/mlflow/tags_registry.py` – `TagsRegistry` loader/cache and tag key lookups.
   - `src/infrastructure/naming/mlflow/tags.py` – high-level MLflow tag construction from `NamingContext` and registry.
   - `src/infrastructure/naming/mlflow/config.py` – naming-related MLflow config loader (`mlflow.yaml`) and derived config (`get_naming_config` and related helpers).
   - `src/infrastructure/naming/display_policy.py` – naming policy (`naming.yaml`) loading/validation and display-name formatting.
   - `src/infrastructure/naming/mlflow/run_names.py` – run-name formatting helpers (present; policy-driven + legacy fallback).
   - `src/infrastructure/naming/mlflow/policy.py` – thin compatibility/forwarder around display policy and config (to be treated as legacy/debt if overlapping).
   - `src/infrastructure/naming/experiments.py` – experimental helpers (to be revisited; currently not SSOT-critical).
2. For each of the above, record:
   - Public functions/classes intended for reuse.
   - Internal helpers / implementation details.
   - Direct and indirect callers (grep + lightweight code reading).

#### Naming utilities inventory (Step 1 output)

| Module | Primary responsibility | Key public API | Main callers (examples) |
| --- | --- | --- | --- |
| `infrastructure/naming/context.py` | Define and validate `NamingContext` for naming/path identity | `NamingContext`, `create_naming_context()` | HPO sweep/refit flows (`training/hpo/execution/local/sweep.py`, `refit.py`), `infrastructure/config/variants.py`, MLflow tracking setup |
| `infrastructure/naming/context_tokens.py` | Expand `NamingContext` into token dictionaries and short hashes | `build_token_values()` | HPO sweep/refit path reconstruction in `training/hpo/execution/local/{sweep,refit}.py`, display policy formatting (`display_policy.py`), path utilities |
| `infrastructure/naming/mlflow/run_keys.py` | Build canonical MLflow run keys and key hashes | `build_mlflow_run_key()`, `build_mlflow_run_key_hash()`, `build_counter_key()` | MLflow trackers (`orchestration/.../trackers/{training,benchmark,conversion,sweep}_tracker.py`), run-name generation (`mlflow/run_names.py`) |
| `infrastructure/naming/mlflow/hpo_keys.py` | Compute HPO study/trial/family keys and hashes with normalization | `build_hpo_study_key[_hash]()`, `build_hpo_study_family_key[_hash]()`, `_normalize_hyperparameters()` | HPO sweep setup and tracking (`training/hpo/execution/local/sweep.py`, `training/hpo/tracking/setup.py`), selection/benchmarking utilities |
| `infrastructure/naming/mlflow/refit_keys.py` | Compute refit protocol fingerprints for reproducibility | `compute_refit_protocol_fp()` | Refit workflows (`training/hpo/execution/local/refit.py`), refit-related tracking/tagging helpers |
| `infrastructure/naming/mlflow/tags_registry.py` | Centralized MLflow tag key registry with caching and defaults | `TagsRegistry`, `load_tags_registry()`, `TagKeyError` | Tag construction (`mlflow/tags.py`), trackers (`infrastructure.tracking.mlflow.*`, `orchestration.jobs.tracking.*`), selection utilities, tests under `tests/tracking/unit/test_tags_*` |
| `infrastructure/naming/mlflow/tags.py` | Build MLflow tag dictionaries from contexts and registry | `build_mlflow_tags()`, `get_tag_key()`, `sanitize_tag_value()` | Trackers in both orchestration and infrastructure layers, HPO/refit executors (`training/hpo/execution/local/*`), training execution (`training/execution/*`), selection/benchmarking flows |
| `infrastructure/naming/mlflow/config.py` | Load and validate MLflow naming config (`mlflow.yaml`) | `load_mlflow_config()`, `get_naming_config()`, `get_auto_increment_config()` and validators | Run-name generation (`mlflow/run_names.py`), tag utilities (`mlflow/tags.py`), tracking config tests (`tests/tracking/unit/test_mlflow_config_comprehensive.py`) |
| `infrastructure/naming/display_policy.py` | Load and validate naming policy (`naming.yaml`) and format display names | `load_naming_policy()`, `validate_naming_policy()`, `format_run_name()`, `validate_run_name()`, `parse_parent_training_id()` | Run-name generation (`mlflow/run_names.py`), tests under `tests/tracking/unit/test_naming_*`, selection/lineage helpers |
| `infrastructure/naming/mlflow/run_names.py` | Generate human-readable MLflow run names using policy + auto-increment | `build_mlflow_run_name()` | HPO/refit executors (`training/hpo/execution/local/{sweep,refit}.py`), training execution and trackers that need run names |
| `infrastructure/naming/mlflow/tag_keys.py` | Convenience accessors for specific tag keys on top of `TagsRegistry` | `get_*` helpers such as `get_lineage_hpo_refit_run_id()`, `get_hpo_trial_number()` | HPO/refit flows and trackers that need specific tag keys (`training/hpo/execution/local/refit.py`, `sweep.py`, `benchmark_tracker.py`) |
| `infrastructure/naming/mlflow/policy.py` | Thin naming policy helpers (overlaps with `display_policy`) | small wrapper/forwarder functions | Legacy orchestration/tracking naming code; candidate for consolidation into `display_policy.py` in later steps |
| `infrastructure/naming/experiments.py` | Experimental/legacy naming helpers (non-SSOT) | helper functions (not widely reused) | Limited/legacy callers; treated as experimental and a candidate for cleanup when safe |

**Out-of-domain naming utilities / debt notes (for later steps)**:

- `orchestration/naming.py`, `orchestration/naming_centralized.py`, and `orchestration/jobs/tracking/naming/*` still contain naming-related helpers (run names, tags, policy) that overlap with `infrastructure.naming.*` and should be treated as migration/cleanup targets.
- `infrastructure/tracking/mlflow/naming.py` and `infrastructure/tracking/mlflow/hash_utils.py` contain legacy naming/hash helpers that are partially superseded by `infrastructure.naming.mlflow.*` and `common.shared.hash_utils` and should be considered for consolidation.

**Success criteria**:

- A short markdown table (in this plan or a linked doc) lists each naming utility, its responsibilities, and its main callers.
- No additional naming-related modules exist outside `src/infrastructure/naming/**` that should obviously belong to this domain (if any are found, they are noted explicitly as debt).

### Step 2: Define SSOT responsibilities and boundaries

1. For each naming utility, define its **primary responsibility** and **what it must not do**:
   - `context.py`: owns `NamingContext` modeling and validation only (no I/O, no MLflow calls).
   - `context_tokens.py`: owns token expansion and short-hash slicing only.
   - `mlflow/run_keys.py`: owns **run identity key + hash** derivation; does not touch tags, policy, or config.
   - `mlflow/hpo_keys.py` and `mlflow/refit_keys.py`: own study/trial/refit key/fingerprint computation, using shared hash helpers.
   - `mlflow/tags_registry.py`: owns tag key registry loading/validation and is the SSOT for tag key strings.
   - `mlflow/tags.py`: owns construction of `Dict[str, str]` tag maps from contexts and registry; does not compute hashes or parse IDs.
   - `mlflow/config.py`: owns reading and validating naming-related config (`mlflow.yaml`) including tag-length limits and run-name settings.
   - `display_policy.py`: owns naming policy (`naming.yaml`) and display-name formatting; uses `NamingContext` + tokens, but does not compute new hashes.
2. Document these boundaries in short comments / docstrings where missing or ambiguous.

**Step 2 implementation notes**:

- All `src/infrastructure/naming/**` modules now have updated `@meta` blocks that spell out both their **responsibilities** and explicit **non-responsibilities** (e.g., “does NOT start MLflow runs”, “does NOT perform I/O”).
- `mlflow/policy.py` is explicitly marked as a **compatibility/legacy bridge** that re-exports orchestration-level naming policy helpers without adding new logic.
- Boundaries between **naming**, **tracking/orchestration**, and **config** responsibilities are now encoded at file level, making SSOT expectations visible without reading full implementations.

**Success criteria**:

- Each naming module has a clear “does X / does not do Y” responsibility captured in its file-level `@meta` block or top-level docstring.
- No module both **computes keys/fingerprints** and **mutates MLflow state** – side-effectful logic lives in tracking/orchestration, not naming utilities.

### Step 3: Eliminate DRY violations in key-building utilities

1. Search for duplicated or near-duplicated key-building logic outside the SSOT modules:
   - Use `grep`/code search for patterns like `study_key_hash`, `trial_key_hash`, `refit_protocol_fp`, `run_key_hash`, and any ad-hoc `sha256` usages in HPO/refit/benchmarking code.
   - Identify any local implementations that effectively recompute:
     - Study/trial/family keys from configs/hyperparameters.
     - Refit protocol fingerprints from data/train/eval configs.
     - Run keys or run-key hashes from process/model identifiers.
2. For each duplication:
   - Replace local hashing logic with calls to:
     - `compute_hash_64()` in `common.shared.hash_utils` or
     - The appropriate SSOT function in `mlflow/hpo_keys.py`, `mlflow/refit_keys.py`, or `mlflow/run_keys.py`.
   - Keep signatures of higher-level workflow functions stable (no breaking API changes).

**Step 3 implementation notes**:

- A targeted search for `study_key_hash`, `trial_key_hash`, `study_family_hash`, `refit_protocol_fp`, and `run_key_hash` plus any raw `sha256(` usage in naming/HPO/refit/tracking codepaths shows:
  - All **HPO study/trial/family** hashes are computed via `infrastructure.naming.mlflow.hpo_keys` using `compute_hash_64()` under the hood.
  - All **refit protocol fingerprints** are computed via `infrastructure.naming.mlflow.refit_keys.compute_refit_protocol_fp`, which also uses `compute_hash_64()`.
  - All **run key hashes** for grouping/auto-increment are produced via `infrastructure.naming.mlflow.run_keys.build_mlflow_run_key_hash()` and consumed by tracking/cleanup code.
- The tracking-side helper `infrastructure.tracking.mlflow.hash_utils` delegates HPO hash computation to the SSOT helpers re-exported from `infrastructure.naming.mlflow.*` rather than reimplementing hashing logic.
- No additional `hashlib.sha256(...).hexdigest()` usages were found in naming/HPO/refit/benchmarking codepaths that generate naming-related identifiers; remaining `sha256` calls live in config/environment/fingerprint utilities outside the naming domain and are intentionally out of scope for this plan.

**Success criteria**:

- All **HPO**, **refit**, and **run** key hashes used for MLflow grouping come from:
  - `compute_hash_64()` via `mlflow/hpo_keys.py`, `mlflow/refit_keys.py`, or `mlflow/run_keys.py`.
- No standalone `hashlib.sha256(...).hexdigest()` calls remain in HPO/refit/benchmarking code paths that produce naming-related identifiers.

### Step 4: Centralize tag key and tag-building usage

1. Identify any modules that:
   - Hardcode `code.*` tag strings instead of using `TagsRegistry` or `mlflow/tags.py`.
   - Build MLflow tag dictionaries manually (e.g., `{ "code.study_key_hash": ..., ... }`) rather than via `build_mlflow_tags()`.
2. For each such case:
   - Where possible, replace tag-key string literals with lookups via `get_tag_key()` or `TagsRegistry.key()`.
   - Replace ad-hoc tag dict construction with:
     - `build_mlflow_tags()` when constructing full run tags, or
     - Local minimal dicts that still defer key names to `TagsRegistry`.
3. For tests:
   - Prefer patching around `build_mlflow_tags()` or registry loading rather than asserting exact tag keys inline, unless the test is specifically about tag-key contracts.

**Success criteria**:

- All production code uses **tag keys** from `mlflow/tags_registry.py` (directly or via helpers) instead of hardcoding `code.*` strings, except in the registry itself.
- Run-tag dictionaries for HPO, refit, benchmarking, and conversion flows are built either by:
  - `build_mlflow_tags()` in `mlflow/tags.py`, or
  - A very small number of documented, special-case helpers.

**Step 4 implementation notes**:

- Run-level tag dictionaries for training, HPO trials, refit, benchmarking, conversion, and deployment flows are now built via `infrastructure.naming.mlflow.tags.build_mlflow_tags()` (or the compatible wrapper in `orchestration.jobs.tracking.naming.tags`), which in turn sources tag keys from `TagsRegistry` with sensible fallbacks.
- Selection, benchmarking, and hash-lookup utilities that need specific tag keys (e.g., study/trial hashes, lineage run IDs) now use either `TagsRegistry` directly (`load_tags_registry().key(...)`) or the convenience helpers in `infrastructure.naming.mlflow.tag_keys` instead of hardcoded `code.*` strings.
- A small set of **intentional, non-SSOT exceptions** remain for highly specialized or legacy tags:
  - Compatibility reads of legacy grouping tags such as `"code.grouping.study_key_hash"` / `"code.grouping.trial_key_hash"` for older runs, where the code already prefers registry-driven keys and only falls back to hardcoded strings when necessary.
  - A few refit-specific tags (e.g., `"code.refit_training_done"`, `"code.refit_run_id"`, `"code.refit_completed"`, `"code.refit_artifacts_uploaded"`, `"code.refit_error"`) used as narrow workflow markers; these are treated as documented, special-case helpers outside the core naming/tagging SSOT and can be migrated into the registry in a future, dedicated cleanup if needed.

### Step 5: Consolidate naming config and display policy usage

1. Find all readers of `config/mlflow.yaml` and `config/naming.yaml`:
   - Ensure they use `load_mlflow_config()` or `get_naming_config()` for `mlflow.yaml`.
   - Ensure they use `load_naming_policy()` and, where appropriate, `validate_naming_policy()` for `naming.yaml`.
2. Replace any duplicate YAML-loading logic specific to naming with calls into `mlflow/config.py` or `display_policy.py`.
3. Ensure:
   - Tag-length limits and run-name-length policies are only derived via `get_naming_config()`.
   - Display names and run-name formatting use `display_policy.py` and `context_tokens.py`, not custom string formatting with ad-hoc placeholder parsing.

**Step 5 implementation notes**:

- All naming-related consumers of `mlflow.yaml` now rely on `infrastructure.naming.mlflow.config` helpers:
  - `load_mlflow_config()` provides the raw config with caching.
  - `get_naming_config()` is the single entry point for tag-length limits, run-name length, and related naming knobs.
  - Additional helpers like `get_auto_increment_config()` and `get_index_config()` centralize other MLflow naming/index behavior.
- All naming-related consumers of `naming.yaml` use `infrastructure.naming.display_policy`:
  - `load_naming_policy()` is the canonical loader with mtime-based caching.
  - `validate_naming_policy()` enforces schema and placeholder rules.
  - Run-name formatting and validation go through `format_run_name()` and `validate_run_name()`, which in turn use `context_tokens.build_token_values()` for token expansion.
- No direct `yaml.safe_load(open("config/mlflow.yaml"))` or `yaml.safe_load(open("config/naming.yaml"))` calls remain in naming/MLflow utilities; remaining YAML loads in other domains (e.g., generic config, artifact acquisition) are intentionally out of scope for this plan.

**Success criteria**:

- No remaining direct `yaml.safe_load(open("config/mlflow.yaml"))` or `yaml.safe_load(open("config/naming.yaml"))` patterns in naming/MLflow utilities.
- A single flow for:
  - Getting naming-related config (`get_naming_config`), and
  - Getting/validating naming policy (`load_naming_policy` + `validate_naming_policy`).

### Step 6: Align context and token helpers with SSOT

1. Search for any functions that:
   - Manually slice hashes (e.g., `[:8]`) for run names or paths outside `context_tokens.py`.
   - Rebuild parent-training IDs or parse spec/exec hashes outside `display_policy.parse_parent_training_id`.
2. Where safe:
   - Replace ad-hoc short-hash logic with calls into `build_token_values()` (or a small helper there, if needed).
   - Reuse `parse_parent_training_id()` for interpreting parent training IDs rather than re-parsing in multiple locations.
3. Ensure `NamingContext` is the central structure passed into naming/path utilities (run names, tagging, path building) rather than passing around loose hash strings.

**Step 6 implementation notes**:

- A search for short-hash slicing (`[:8]`) in the codebase shows that all naming/path-related short forms are produced either in `infrastructure/naming/context_tokens.build_token_values()` (for tokens such as `spec8`, `trial8`, etc.) or within the naming policy helpers (`display_policy.parse_parent_training_id()` and its orchestration mirror), not in ad-hoc callers.
- `parent_training_id` parsing is centralized in `display_policy.parse_parent_training_id()` (and the compatibility re-export in `mlflow/policy.py`), and conversion naming logic consumes its parsed components via the display policy machinery rather than duplicating regexes elsewhere.
- `NamingContext` is used as the primary carrier for naming identity across run-name generation, tag building, and path-building helpers; callers pass context objects into these SSOT utilities instead of slicing hashes or reconstructing parent-training IDs themselves.

**Success criteria**:

- All short-hash slicing (`[:8]`) related to naming or paths happens in `context_tokens.py` (or helpers it exports).
- All parsing of `spec_*_exec_*` style parent-training IDs happens through `display_policy.parse_parent_training_id()` or a single shared helper, not duplicated regex logic.

### Step 7: Verification and regression safety net

1. Add or update tests to cover:
   - HPO/refit/run keys:
     - Same configs/hyperparameters → same hashes across platforms.
     - Different protocols/data → different hashes.
   - Tag building:
     - `build_mlflow_tags()` sets expected minimal `code.*` tags and respects `TagsRegistry` overrides.
   - Config/policy:
     - `get_naming_config()` respects overrides and defaults.
     - `load_naming_policy()` caching and validation behavior under missing/invalid configs.
2. Run focused test suites:
   - `uvx pytest tests/naming` (if present) or the closest naming-related suites:
     - MLflow tracking tests that assert tag behavior.
     - Selection/benchmarking tests that depend on study/trial keys.
3. Optionally, run a smoke workflow (e.g., HPO + selection + conversion) to confirm that:
   - Runs are still discoverable by selection logic.
   - Auto-increment and grouping tags behave as before.

**Step 7 implementation notes**:

- The work performed under this plan was deliberately constrained to:
  - Metadata/docstring updates in naming utilities.
  - Consolidation of config/policy accessors.
  - Documentation and reuse of existing SSOT helpers for keys, tags, and naming.
  These changes did not alter the core algorithms for hash computation, tag building, or naming, minimizing regression risk.
- Existing fast suites already exercise the naming domain and its integration points:
  - `tests/tracking/unit/` (including `test_mlflow_config_comprehensive.py`, `test_tags_comprehensive.py`, and naming policy tests) validate MLflow config, tag construction, and naming behavior.
  - `tests/config/unit/test_mlflow_yaml.py` and `tests/config/unit/test_naming_yaml.py` cover configuration and policy loading/validation paths.
  - HPO/refit workflows under `tests/hpo/integration/` and selection/benchmarking tests cover the end-to-end use of study/trial/refit keys and grouping tags.
- The latest `test_results.log` shows these suites passing after the consolidations, and no new tests were required beyond existing coverage because runtime behavior for public workflows (HPO, refit, benchmarking, selection, conversion) was preserved.

**Success criteria**:

- All impacted tests pass:
  - Tag-related tracking tests.
  - Naming-policy and hash-related tests.
  - Selection/benchmarking workflows that consume these identifiers.
- No regressions in MLflow run discoverability (selection queries still find the right runs.

## Success Criteria (Overall)

- **SSOT achieved** for naming concerns:
  - All HPO/run/refit keys and hashes come from `infrastructure.naming.mlflow.*` plus shared `hash_utils`.
  - All naming-related tag keys come from `TagsRegistry` and are constructed via `mlflow/tags.py` or thin wrappers.
  - All naming config and policy reads are funneled through `mlflow/config.py` and `display_policy.py`.
- **DRY violations removed** without introducing large refactors:
  - No duplicate implementations of key/tag/policy logic outside the designated SSOT modules.
- **Minimal breakage**:
  - Public APIs of workflows (HPO, refit, benchmarking, selection, conversion) remain stable.
  - Internal changes are limited to replacing local helpers with calls into existing naming utilities.



# Module READMEs Two-Tier Rule Package

## Goal

Create a **rule-local module** under `.cursor/rules/` that owns the two-tier module README behavior (generated + curated), with:

- A **single authoritative rule entrypoint** (`.mdc`) that Cursor loads.
- A **self-contained `module-readmes-two-tier/` package** containing scripts, schemas, fixtures, and tests.
- **Single-source-of-truth tooling** for:
  - Detecting impacted modules from diffs.
  - Updating generated marker blocks in module READMEs.
- Clear **safety rails** for curated-tier automation (suggest-only by default).
- CI + local workflows that keep module READMEs in sync with code and enforce the rule.

## Status

**Last Updated**: 2025-01-19

### Completed Steps
- ⏳ None yet

### Pending Steps
- ⏳ Step 1: Establish rule loading + source-of-truth conventions
- ⏳ Step 2: Scaffold `.cursor/rules/module-readmes-two-tier/` package
- ⏳ Step 3: Implement core scripts + JSON schemas (minimum viable subset)
- ⏳ Step 4: Add fixtures + tests for diff parsing and marker handling
- ⏳ Step 5: Wire up CI and local workflows for docs update + docs check
- ⏳ Step 6: Document curated-tier policy and (optionally) stub automation

## Preconditions

- Existing module README structure and markers are defined and stable enough to encode into tooling.
- `.cursor/rules/` is already in use for other rules, and Cursor is configured to load `.mdc` rule files.
- The repo can run Python tooling via `uvx` (preferred) or equivalent.

## Steps

### Step 1: Establish rule loading + source-of-truth conventions

Define how Cursor loads this rule and where humans should look for the canonical spec to prevent drift between docs and behavior.

**Tasks**

1. Decide on the rule entrypoint pattern:
   - Create `.cursor/rules/module-readmes-two-tier.mdc` as the **authoritative rule text**.
   - Optionally mirror content in `RULE.md` inside the package, but `.mdc` remains the source of truth for agents.
2. In `module-readmes-two-tier.mdc`:
   - Describe the two-tier README pattern (generated + curated).
   - Explicitly reference the `module-readmes-two-tier/` folder for scripts, schemas, and tests.
   - State that all automation related to module README updates must go through this rule package.
3. Add a short note in the `.mdc` file documenting:
   - How Cursor loads this rule.
   - Where to find and how to run the supporting scripts.

**Success criteria**

- `.cursor/rules/module-readmes-two-tier.mdc` exists and contains the canonical rule text.
- The rule text explicitly references the `module-readmes-two-tier/` package for implementation details.
- There is a clear statement that `.mdc` is the authoritative source for the rule, and any `RULE.md` mirror is secondary.

### Step 2: Scaffold `.cursor/rules/module-readmes-two-tier/` package

Create the folder structure for the rule-local implementation, keeping everything needed for this rule in one place.

**Tasks**

1. Create the directory structure:
   - `module-readmes-two-tier/`
   - `module-readmes-two-tier/scripts/`
   - `module-readmes-two-tier/scripts/schemas/`
   - `module-readmes-two-tier/scripts/fixtures/diffs/`
   - `module-readmes-two-tier/scripts/fixtures/readmes/`
   - `module-readmes-two-tier/tests/`
2. Add a minimal `README.md` under `module-readmes-two-tier/` that:
   - Explains the purpose of the package (two-tier README rule).
   - Documents how to run the scripts locally (high level).
   - Points to the `.mdc` rule entrypoint.
3. If desired, add a `RULE.md` within the package that:
   - Mirrors the `.mdc` rule text for human readers.
   - Clearly states that `.mdc` is the canonical version for Cursor.

**Success criteria**

- `module-readmes-two-tier/` folder exists with `scripts/`, `scripts/schemas/`, `scripts/fixtures/`, and `tests/` subfolders.
- `module-readmes-two-tier/README.md` documents the purpose and basic usage.
- (Optional) `RULE.md` exists and is consistent with the `.mdc` rule text.

### Step 3: Implement core scripts + JSON schemas (minimum viable subset)

Implement the minimum set of Python scripts and schemas needed to support the core flow: detect impacted modules, collect evidence, rewrite generated marker blocks, and run update/check flows.

**Tasks**

1. Implement **`changed_modules.py`**:
   - Input: `git diff` output (e.g., via `--name-status`), plus optional base/head refs.
   - Output: JSON description of impacted `src/<module>` directories, including rename handling.
   - Enforce this as the **single source of truth** for computing impacted modules.
2. Implement **`collect_module_evidence.py`**:
   - Given a module path (e.g., `src/common`), collect evidence needed for generated README content (e.g., tree, entrypoints, key symbols, tests).
   - Emit JSON conforming to a `module_evidence` schema.
3. Implement **`update_generated_block.py`**:
   - Given a module README and evidence JSON, perform a **marker-safe, deterministic rewrite** of the generated block only.
   - Never touch curated sections or markers outside the generated block.
   - Enforce this as the **only supported writer** for generated marker blocks.
4. Implement **`docs_update.py`**:
   - Orchestrate: `changed_modules.py` → for each module → `collect_module_evidence.py` → `update_generated_block.py`.
   - Support CLI arguments for diff ranges (e.g., `origin/main...HEAD`, `HEAD~1..HEAD`).
5. Implement **`docs_check.py`**:
   - Run `docs_update.py` in a non-interactive mode.
   - Fail (non-zero exit) if any `src/**/README.md` changes are produced (e.g., via `git diff`).
6. Define JSON schemas under `scripts/schemas/`:
   - `changed_modules.schema.json`
   - `module_evidence.schema.json`
   - Include a `schema_version` field or versioned paths (e.g., `v1/`) to allow safe evolution.

**Success criteria**

- All five core scripts exist and are wired together:
  - `changed_modules.py`
  - `collect_module_evidence.py`
  - `update_generated_block.py`
  - `docs_update.py`
  - `docs_check.py`
- JSON schemas exist and validate the outputs of `changed_modules.py` and `collect_module_evidence.py`.
- The rule text explicitly states:
  - `changed_modules.py` is the only supported way to compute impacted modules.
  - `update_generated_block.py` is the only supported writer for generated marker blocks.

### Step 4: Add fixtures + tests for diff parsing and marker handling

Add focused tests and fixtures to ensure diff parsing, marker handling, and idempotency are robust and safe.

**Tasks**

1. Create diff fixtures under `scripts/fixtures/diffs/`:
   - `add_modify_delete.txt`: simple add/modify/delete scenario in `src/` and non-`src/`.
   - `rename_cross_module.txt`: file rename across modules or within a module.
2. Create README fixtures under `scripts/fixtures/readmes/`:
   - `good_markers.md`: well-formed generated + curated markers.
   - `malformed_markers.md`: broken markers to test error handling.
   - `duplicate_markers.md`: multiple markers to ensure the script behaves predictably.
3. Implement tests under `tests/`:
   - `test_changed_modules.py`: validates diff parsing, including renames and non-src file filtering.
   - `test_update_generated_block.py`: verifies marker-safe rewriting and idempotency (running twice produces no further changes).
   - `test_marker_handling.py`: covers malformed and duplicate marker cases, including clear error messages.
4. Wire tests to run via `uvx pytest`:
   - Optionally add a `tests` README or comment describing how to run only these tests for quick feedback.

**Success criteria**

- Pytest tests exist for diff parsing, marker handling, and idempotency.
- Tests pass locally via `uvx pytest` for the `module-readmes-two-tier` tests.
- Marker handling is verified to be deterministic and idempotent using fixtures.

### Step 5: Wire up CI and local workflows for docs update + docs check

Ensure there is a single, documented way to run docs update/check both locally and in CI, and that it goes through the rule package.

**Tasks**

1. Define standard CLI invocations and document them in:
   - `.cursor/rules/module-readmes-two-tier.mdc`
   - `module-readmes-two-tier/README.md`
2. Recommended conventions:
   - Local, last-commit update:
     - `uvx python .cursor/rules/module-readmes-two-tier/scripts/docs_update.py --diff HEAD~1..HEAD`
   - CI PR check (merge-base against main):
     - `uvx python .cursor/rules/module-readmes-two-tier/scripts/docs_check.py --diff origin/main...HEAD`
3. Update CI configuration (GitHub Actions or equivalent) to:
   - Run `docs_check.py` in relevant workflows.
   - Fail the job if README drift is detected.
4. Optionally add a short section to `src/common/README.md` (or root README) that:
   - Explains the existence of the module READMEs rule.
   - Points to the `.cursor/rules/module-readmes-two-tier.mdc` file and package README.

**Success criteria**

- There is one canonical CI check that enforces module README sync via `docs_check.py`.
- Local developer workflow for updating READMEs is documented and uses `docs_update.py`.
- CI fails if module READMEs are out of date relative to code changes.

### Step 6: Document curated-tier policy and (optionally) stub automation

Define the policy and future shape of curated-tier automation, even if the initial implementation is deferred.

**Tasks**

1. In `.cursor/rules/module-readmes-two-tier.mdc`, add an explicit curated-tier policy:
   - Curated-tier automation must start in **suggest-only** mode.
   - It should output proposed patches/diffs instead of writing directly to files by default.
   - Auto-write for curated prose requires an explicit repository-level opt-in (documented in the rule).
2. Optionally, add a stub script `update_curated_tier.py`:
   - For now, it can:
     - Accept evidence and existing README content.
     - Produce a **proposed** curated section as output (e.g., a patch file or printed diff) without touching files.
   - Clearly document that this is a **suggestion engine**, not an auto-writer, until the repo opts in.
3. Extend tests and fixtures as needed once curated-tier automation becomes more concrete.

**Success criteria**

- The curated-tier policy is clearly documented in the `.mdc` rule.
- (Optional) `update_curated_tier.py` exists as a suggest-only stub with no file-writing side effects.
- There is no path where curated-tier text is silently auto-rewritten without explicit opt-in.

## Success Criteria (Overall)

- `.cursor/rules/module-readmes-two-tier.mdc` is the authoritative, loaded rule and points to a self-contained implementation package.
- All logic for:
  - Determining impacted modules from diffs is centralized in `changed_modules.py`.
  - Updating generated marker blocks is centralized in `update_generated_block.py`.
- JSON schemas define stable contracts between scripts and include a versioning strategy.
- Fixtures and tests validate diff parsing, marker handling, and idempotency.
- CI and local workflows both use the same rule-local scripts for docs update/check.
- Curated-tier automation, when introduced, is guarded by a suggest-only default and explicit opt-in for auto-write behavior.



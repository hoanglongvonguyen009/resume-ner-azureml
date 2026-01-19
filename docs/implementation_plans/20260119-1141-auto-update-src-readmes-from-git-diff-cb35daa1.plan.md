# Plan: Auto-update `src/**/README.md` from `git diff` (incremental, deterministic)

## Goal

Automatically keep per-module README files up to date when code changes under `src/`, by:

- Detecting impacted modules from `git diff --name-status <base>...<head>`
- Running a deterministic generator for each impacted module
- Updating only a stable auto-generated section in each README (preserving manual notes)
- Providing local commands (`docs:update`, `docs:check`) and CI enforcement (check-only mode)

**Module definition (for this plan)**:
- A module is a **first-level directory under `src/`** (e.g., `src/training/`, `src/evaluation/`).
- Each module must have `src/<module>/README.md`.

## Status

**Last Updated**: 2026-01-19

### Completed Steps
- ⏳ (none)

### Pending Steps
- ⏳ Step 0: Confirm constraints + reuse-first decision notes
- ⏳ Step 1: Add a deterministic README generator contract (`generate_readme_for_module`)
- ⏳ Step 2: Add incremental updater (parse `git diff --name-status`)
- ⏳ Step 3: Add marker-based README update logic (preserve manual text)
- ⏳ Step 4: Add local commands (`docs:update`, `docs:check`)
- ⏳ Step 5: Add CI workflow (Mode A: check-only) + docs drift messaging
- ⏳ Step 6: Add tests (diff parsing + marker update + idempotency)
- ⏳ Step 7: Rollout markers across existing module READMEs (one-time migration)

## Context / What exists today

- Module READMEs are already a core repo convention (`docs/modules/INDEX.md` links many `src/**/README.md`).
- Documentation standards exist under `docs/templates/`.
- There is an existing “auto-generated” audit report style under `docs/implementation_plans/audits/`.
- **No** existing marker blocks like:
  - `<!-- AUTO-GENERATED:START -->`
  - `<!-- AUTO-GENERATED:END -->`
- **No** GitHub Actions workflows currently exist (no `.github/workflows/` directory in repo).
- **No** existing `docs:update` / `docs:check` command wiring exists (no Makefile / package scripts / console scripts found).

## Design decisions (guardrails)

- **Determinism required**:
  - No timestamps, no environment-specific paths, stable ordering (always sort).
- **Preserve manual docs**:
  - Only content between markers is written.
  - Content outside markers remains unchanged byte-for-byte.
- **Incremental by default**:
  - Operate only on impacted modules derived from diff.
  - Allow override flags for local workflows (`--cached`, `--base-ref`, `--head-ref`).
- **Failure behavior**:
  - If generator fails for a module, fail the whole run with a clear module-specific error.
- **CI mode**:
  - Implement Mode A (check-only) first; Mode B (auto-commit) is explicitly out of scope unless requested.

## Preconditions

- Repo uses `src/` layout and has module-level `README.md` files.
- Developers can run Python tooling locally (repo already uses `uvx` for tests).

## Steps

### Step 0: Confirm constraints + reuse-first decision notes

**Objective**: Lock down scope and identify existing code we should extend rather than reinvent.

**Tasks**:
- Confirm diff base defaults:
  - CI: `origin/main...HEAD` (or merge-base equivalent)
  - Local: allow `--cached`, `--base-ref`, and `--range`
- Confirm module scope:
  - Only top-level `src/<module>/` modules, not nested submodules (nested can be a follow-up).
- Define **trigger file rules** (what counts as “source” for this workflow):
  - **Include** (triggers updates):
    - Files under `src/<module>/**` that are considered code: `.py`, `.ipynb` (if treated as source), and any repo-specific source extensions
  - **Exclude** (must _not_ trigger updates):
    - `src/**/README.md`
    - `src/**/__pycache__/**`
    - `src/**/.venv/**`
    - `src/**/dist/**`, `src/**/build/**`
    - Generated outputs and caches (`mlruns/`, `outputs/`, other repo-specific generated dirs)
    - Any paths already ignored by `.gitignore` that clearly represent build artifacts
- Record reuse-first notes in PR/commit message:
  - Existing options considered: `docs/templates/`, existing module READMEs, existing CLI patterns under `src/**/cli/`.
  - Reason new code is necessary: no README generator or diff-based updater exists yet.

**Success criteria**:
- A clear decision is recorded for:
  - diff range defaults
  - module scope rules
  - where code will live (e.g., `src/docs_tools/` or `src/common/shared/` + a CLI entrypoint)

---

### Step 1: Add a deterministic README generator contract (`generate_readme_for_module`)

**Objective**: Define and implement a generator interface usable by the updater.

**Tasks**:
- Implement a function with a stable signature, e.g.:
  - `generate_readme_for_module(module_path: Path) -> str`
- Decide initial generated content surface (keep minimal at first):
  - Module name + purpose (from existing README where possible)
  - “Module Structure” (tree of key packages/files)
  - “Public entrypoints” (best-effort: known workflows/CLI modules, not full API extraction)
- Ensure stable ordering:
  - Sort paths, symbols, and lists.

**Success criteria**:
- Running generator twice produces identical output.
- Generated output contains no timestamps or absolute machine paths.

---

### Step 2: Add incremental updater (parse `git diff --name-status`)

**Objective**: Compute impacted modules from a diff.

**Tasks**:
- Parse output of: `git diff --name-status <base>...<head>`
  - Expect lines of the form:
    - `A\tpath`
    - `M\tpath`
    - `D\tpath`
    - `R<score>\told_path\tnew_path`
- Apply **trigger file rules** from Step 0:
  - Ignore any paths that are excluded (e.g., `src/**/README.md`, build artifacts, generated outputs).
- Handle statuses precisely:
  - **A/M/D**:
    - If `path` is under `src/<module>/` and passes trigger rules → mark `<module>` as impacted.
  - **R<score>**:
    - For each rename line, parse `old_path` and `new_path`:
      - If `old_path` is under `src/<old_module>/` and passes trigger rules:
        - If `old_module != new_module` and `new_path` is under `src/<new_module>/` → mark **both** `old_module` and `new_module` as impacted.
        - If `new_path` is still under `src/<old_module>/` (rename within same module) → mark only `old_module`.
      - If rename moves a file **into** `src/<module>/` from outside `src/` → mark the new `module` only.
      - If rename moves a file **out of** `src/` → mark only the old `module`.
- Deduplicate module list.
- Exclude non-`src/` files entirely.
- If a module directory no longer exists (deleted), do not create it; skip README generation for that module.

**Success criteria**:
- Given a synthetic diff, impacted module detection matches spec including rename edge cases.
- Output module list is stable-sorted for deterministic execution order.

---

### Step 3: Add marker-based README update logic (preserve manual text)

**Objective**: Update only the generated section between markers.

**Tasks**:
- Define markers exactly (must match _verbatim_):
  - `<!-- AUTO-GENERATED:START -->`
  - `<!-- AUTO-GENERATED:END -->`
- Implement **strict marker validation**:
  - If **more than one** `START` or `END` marker is found → **hard fail** with a clear error (do not attempt to auto-fix).
  - If a `START` marker exists without a matching `END` (or vice versa) → **hard fail**.
  - Do not support nested or overlapping marker blocks.
- Implement README update rules:
  - If README exists **and a valid single marker pair exists**:
    - Replace only the content between `START` and `END` (preserve everything else byte-for-byte).
  - If README exists **and markers are missing**:
    - Insert a generated block **once**, using a consistent insertion rule:
      - Preferred: insert under the `## Module Structure` section if it exists; otherwise, after the title and TL;DR.
  - If README is missing but module exists:
    - Create README using a minimal template (Title, section headings) and include a single marker block in the appropriate section.
- Enforce newline conventions (UTF-8, `\n` line endings).

**Success criteria**:
- Manual text outside markers is unchanged.
- Running updater twice results in no diff (idempotent).

---

### Step 4: Add local commands (`docs:update`, `docs:check`)

**Objective**: Provide developer-friendly entrypoints.

**Tasks**:
- Add `docs:update`:
  - Runs incremental updater and writes README updates.
- Add `docs:check`:
  - Runs updater, then fails if `git diff` shows README drift under `src/**/README.md`.
- Decide how to expose commands (prefer Python-native):
  - Add console scripts in `pyproject.toml`, or
  - Add a thin `python -m ...` CLI + documented shell aliases.

**Success criteria**:
- `docs:update` modifies READMEs when appropriate.
- `docs:check` exits non-zero with clear instructions when drift exists.

---

### Step 5: Add CI workflow (Mode A: check-only) + docs drift messaging

**Objective**: Enforce README freshness in PRs.

**Tasks**:
- Create `.github/workflows/docs-check.yml`:
  - Trigger on PRs and pushes (as desired).
  - Run `docs:check`.
- Add clear failure message:
  - “Run docs:update and commit README changes.”

**Success criteria**:
- CI fails when generated README output differs from committed output.
- CI passes when repository is in-sync.

---

### Step 6: Add tests (diff parsing + marker update + idempotency)

**Objective**: Prevent regressions and validate edge cases.

**Tasks**:
- Unit tests for:
  - diff parsing (A/M/D/R across modules)
  - marker insertion and replacement
  - idempotency behavior
- Avoid over-specific assertions:
  - Assert presence/placement of markers and key generated lines, not entire README text.

**Success criteria**:
- Tests cover rename/move edge cases and manual-text preservation.
- Tests are fast and CI-safe (no AzureML dependency).

---

### Step 7: Rollout markers across existing module READMEs (one-time migration)

**Objective**: Introduce the generated block into each `src/<module>/README.md`.

**Tasks**:
- For each top-level module under `src/`:
  - Ensure README exists
  - Insert markers if missing
  - Populate generated section
- Keep existing manual content and formatting.

**Success criteria**:
- All `src/<module>/README.md` files contain markers exactly once.
- Running `docs:update` after migration produces no diff (clean baseline).

## Success Criteria (Overall)

- If a file changes in `src/foo/**`, then `src/foo/README.md` is updated accordingly.
- Renaming/moving files across modules updates both old and new module READMEs.
- Manual README text outside the markers is preserved byte-for-byte.
- Running the updater twice with no code changes produces no README diff (idempotent).
- In CI check-only mode, README drift causes a clear, actionable failure.

## Out of Scope (for this plan)

- Mode B auto-commit in CI (bot commits)
- Full dependency graph impact detection (indirect imports)
- Scheduled full regeneration (nightly/weekly) — can be follow-up enhancement




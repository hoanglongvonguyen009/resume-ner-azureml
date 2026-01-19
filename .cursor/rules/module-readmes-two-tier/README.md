# Module READMEs Two-Tier Rule Package

This package implements the **two-tier module README rule** for first-level modules under `src/`:

- **Generated tier**: Deterministic auto-generated block between:
  - `<!-- AUTO-GENERATED:START -->`
  - `<!-- AUTO-GENERATED:END -->`
- **Curated tier**: Hand-written content outside the generated block, never auto-overwritten by default.

The **canonical rule definition** lives in:

- `.cursor/rules/module-readmes-two-tier.mdc`

This README is a human-friendly mirror and must stay consistent with the `.mdc` file.

## Layout

All rule-local implementation lives here:

- `scripts/` – Python entrypoints and helpers
- `scripts/schemas/` – JSON schemas for script inputs/outputs
- `scripts/fixtures/diffs/` – Diff fixtures for testing impacted-module detection
- `scripts/fixtures/readmes/` – README fixtures for marker handling tests
- `tests/` – Pytest tests for this rule package
- `templates/` – Curated README template for the human-maintained sections (generated block stays automation-owned)

## Local Usage

Recommended commands (run from repo root):

- **Update module READMEs for the last commit**:
  - `uvx python .cursor/rules/module-readmes-two-tier/scripts/docs_update.py --diff HEAD~1..HEAD`
- **Check for README drift against main (CI-style)**:
  - `uvx python .cursor/rules/module-readmes-two-tier/scripts/docs_check.py --diff origin/main...HEAD`

See `.cursor/rules/module-readmes-two-tier.mdc` for the authoritative description of:

- Two-tier README semantics
- Curated-tier automation policy (suggest-only by default)
- Single-source-of-truth scripts for:
  - impacted module detection (`changed_modules.py`)
  - generated-block updates (`update_generated_block.py`)

## Curated template

Use `templates/module-readme-curated-template.md` when creating or refreshing the human-owned sections of a module README. Leave the generated block (`AUTO-GENERATED:START/END`) to the updater scripts.

## Link checking

To find broken **relative** markdown links (CI-safe, no network):

- Check the curated template and `src/**/README.md` (default targets):
  - `uvx python .cursor/rules/module-readmes-two-tier/scripts/check_markdown_links.py`
- Check a specific file:
  - `uvx python .cursor/rules/module-readmes-two-tier/scripts/check_markdown_links.py path/to/file.md`

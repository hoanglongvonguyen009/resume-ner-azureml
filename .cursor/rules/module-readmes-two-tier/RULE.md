## Module READMEs Two-Tier Rule (Mirror)

> **Note:** This file is a human-friendly mirror of `.cursor/rules/module-readmes-two-tier.mdc`.  
> The `.mdc` file is the **canonical source of truth** for this rule. If there is any discrepancy, the `.mdc` file wins.

This rule defines the **two-tier module README pattern** for first-level modules under `src/`:

- **Generated tier**: Deterministic, auto-updated block between:
  - `<!-- AUTO-GENERATED:START -->`
  - `<!-- AUTO-GENERATED:END -->`
- **Curated tier**: Hand-written content outside the generated block.

Key points:

- Implementation is self-contained under `.cursor/rules/module-readmes-two-tier/`.
- Impacted modules from diffs are computed only by `scripts/changed_modules.py`.
- Generated marker blocks are written only by `scripts/update_generated_block.py`.
- `scripts/docs_update.py` and `scripts/docs_check.py` provide the standard local + CI entrypoints.
- Curated-tier automation must be **suggest-only** by default and requires explicit opt-in for any auto-write behavior.

For full details, see `.cursor/rules/module-readmes-two-tier.mdc`.



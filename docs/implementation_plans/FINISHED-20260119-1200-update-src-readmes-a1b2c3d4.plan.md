# Plan: Update Technical Documentation for Source Modules in `src/`

## Goal

Update and maintain comprehensive technical documentation (`README.md`) for existing source modules in `src/` to:

1. **Keep documentation current**: Ensure all READMEs reflect current module structure, APIs, and usage patterns
2. **Improve consistency**: Standardize documentation format across all modules using latest standards
3. **Fix outdated content**: Update examples, links, and references that are no longer accurate
4. **Enhance completeness**: Add missing sections, improve clarity, and fill documentation gaps

## Status

**Last Updated**: 2026-01-19

**Current State**:

- ✅ Documentation standards template exists (`docs/templates/TEMPLATE-documentation_standards.md`)
- ✅ A previous master plan for source/test documentation exists and is marked finished (`FINISHED-MASTER-20260118-1700-module-documentation-update-plan.plan.md`)
- ⏳ This plan focuses specifically on **current and future updates** to `README.md` files under `src/`
- ⏳ Some `src/` modules have been recently refactored and may need documentation alignment

### Completed Steps

- ✅ Step 0: Identify scope (`src/` only – excludes `tests/`)
- ✅ Step 1 (scoped): Review documentation standards and identify gaps for `src/deployment/api` and `src/deployment/api/tools`
- ✅ Step 2 (scoped): Audit existing documentation for `src/deployment/api` and add new README for `src/deployment/api/tools`
- ✅ Step 3 (scoped): Update high-priority module `src/deployment/api` (structure and usage now reflect current code and tools)

### Completed Steps

- ✅ Step 0: Identify scope (`src/` only – excludes `tests/`)
- ✅ Step 1: Review documentation standards and identify gaps (`src/` modules)
- ✅ Step 2: Audit existing `src` documentation for outdated content
- ✅ Step 3: Update high-priority `src` modules (recently changed, foundational)
- ✅ Step 4: Update medium-priority `src` modules (frequently used, minor updates needed)
- ✅ Step 5: Update lower-priority `src` modules (stable, cosmetic updates)
- ✅ Step 6: Update cross-references and any module index relevant to `src`
- ✅ Step 7: Final review and consistency check

### Notes on Completion

- All `src/*/README.md` files were reviewed against `docs/templates/TEMPLATE-documentation_standards.md`.
- High-, medium-, and low-priority modules listed in this plan already follow the required structure (Title, TL;DR, Overview, Module Structure, Usage, Testing, Related Modules), with tested examples and accurate links.
- Deployment-related docs (`src/deployment/**`) were slightly extended to document the new `api/tools` package; all other READMEs were up to date and required no structural changes.
- Cross-references between `src` module READMEs, the root `README.md`, and the module index are consistent and use valid relative paths.

## Preconditions

- Existing documentation exists for multiple `src/` modules (`README.md` files under `src/`)
- Documentation standards are defined (`docs/templates/TEMPLATE-documentation_standards.md`)
- Module structure is relatively stable (major refactoring should wait)

## Documentation Update Checklist

Each `src` module README should be reviewed against this checklist:

### Content Accuracy

- [ ] **Module Structure**: Lists current entry points and folders (no deleted/renamed files)
- [ ] **API Reference**: Documents current public APIs (removed deprecated, added new)
- [ ] **Code Examples**: All examples work with current codebase
- [ ] **Configuration**: Documents current config options and environment variables
- [ ] **Integration Points**: Reflects current dependencies and usage patterns
- [ ] **CLI Usage**: Documents current CLI commands and options (if applicable)

### Completeness

- [ ] **TL;DR / Quick Start**: Present and includes working example
- [ ] **Overview**: 1–2 paragraphs with focused bullet points (no fluff)
- [ ] **Usage**: At least one working basic example
- [ ] **Testing**: Includes runnable test commands (for that module’s surface)
- [ ] **Related Modules**: Links are valid and current

### Standards Compliance

- [ ] **Format**: Follows current documentation standards template
- [ ] **Structure**: Uses required sections, omits empty optional sections
- [ ] **Examples**: All examples are tested and working
- [ ] **Cross-references**: Uses relative paths, all links valid
- [ ] **API Reference**: Limited to top-level stable surface (max 10 items)

## Documentation Audit Process

Before updating documentation, perform this **repeatable audit** to identify what needs updating for each `src` module:

### 1. Scan Module Changes

```bash
# Check when module files were last modified
find src/module -name "*.py" -type f -exec stat -c "%y %n" {} \; | sort -r | head -20

# Check git history for recent changes (adjust date window as needed)
git log --oneline --since="2025-12-01" -- src/module/ | head -20

# List files that exist in code but not mentioned in README
find src/module -name "*.py" -type f | while read f; do
    basename "$f" | grep -q "$(grep -o '[a-zA-Z_]*\.py' README.md)" || echo "Not in README: $f"
done
```

### 2. Verify Code Examples

```bash
# Test if example imports work (run manually in a Python shell or notebook)
# For each example, verify imports and calls are valid.

# Check if CLI commands still exist
grep -r "CLI Usage\|python -m\|cli\." src/module/README.md | while read line; do
    # Verify command exists in codebase
    echo "Verify: $line"
done
```

### 3. Check Cross-References

```bash
# Find all links in README and verify markdown targets exist
grep -o '\[.*\](.*\.md)' src/module/README.md | while read link; do
    # Extract path and verify file exists
    path=$(echo "$link" | sed 's/.*](\(.*\))/\1/')
    [ -f "$path" ] || echo "Broken link: $link"
done
```

### 4. Compare with Standards

```bash
# Check if README has all required sections (per standards template)
required_sections=("TL;DR" "Overview" "Module Structure" "Usage" "Testing" "Related Modules")
for section in "${required_sections[@]}"; do
    grep -q "## $section" src/module/README.md || echo "Missing: $section"
done
```

### 5. Document Findings

Create an audit report (e.g., under `docs/implementation_plans/audits/`):

- **Outdated content**: [list items that need updating]
- **Missing sections**: [list required sections not present]
- **Broken examples**: [list examples that don't work]
- **Broken links**: [list invalid cross-references]
- **API changes**: [list new/deprecated APIs not documented]
- **Structure changes**: [list module structure changes not reflected]

## Update Process

For each `src` module README that needs updating:

### 1. Review Current State

1. Read existing `README.md` completely
2. Perform documentation audit (see "Documentation Audit Process")
3. Compare with current module code (public API, entry points, workflows)
4. Compare with documentation standards
5. Create a per-module update checklist

### 2. Update Content

1. **Update Module Structure**:
   - Remove references to deleted files/folders
   - Add new entry points and folders
   - Update descriptions for changed components

2. **Update API Reference**:
   - Remove deprecated functions/classes
   - Add new public APIs (if under 10 items)
   - Update function signatures if changed
   - Link to source for detailed APIs

3. **Update Code Examples**:
   - Test all existing examples
   - Fix broken examples
   - Update examples to use current APIs
   - Add examples for new functionality where useful

4. **Update Integration Points**:
   - Update dependency lists
   - Update "Used By" / "Related Modules" sections
   - Fix broken cross-references

5. **Update Configuration**:
   - Document new config options
   - Remove deprecated options
   - Update environment variable docs

6. **Add Missing Sections**:
   - Add TL;DR if missing
   - Add required sections per standards
   - Fill in incomplete sections

### 3. Verify Updates

1. **Test Examples**: Run all code examples
2. **Check Links**: Verify all cross-references work
3. **Review Format**: Ensure it follows standards template
4. **Check Completeness**: Verify all required sections are present
5. **Update Date**: Update any "Last Updated" metadata in the README

### 4. Update Cross-References

1. Update this module in related module READMEs
2. Update any module index or overview documents that reference this module
3. Update root `README.md` if high-level structure changed

## Per-Module Definition of Done (Update)

Each `src` module README update is considered complete when:

- [ ] All outdated content has been updated
- [ ] All code examples have been tested and work
- [ ] All cross-references are valid and current
- [ ] Module Structure reflects current codebase
- [ ] API Reference documents current APIs (or links to source)
- [ ] All required sections are present per standards
- [ ] Documentation follows current standards template
- [ ] Integration Points reflect current dependencies
- [ ] Configuration docs are current
- [ ] Related Modules links are valid

## Steps

### Step 1: Review Documentation Standards and Identify Gaps (for `src/`)

**Objective**: Understand current standards and identify what needs updating specifically for `src` modules.

**Tasks**:

1. Review `docs/templates/TEMPLATE-documentation_standards.md` for current standards.
2. Compare a representative sample of `src` READMEs with the standards template.
3. Identify common gaps across `src` modules:
   - Missing required sections
   - Outdated format/structure
   - Non-standard examples
   - Missing cross-references
4. Create/extend a gap analysis document (e.g., `docs/implementation_plans/gap-analysis-documentation-standards.md`) with a `src`-specific section.

**Success criteria**:

- Gap analysis document updated with `src`-specific findings.
- Common issues identified across `src` modules.
- Update priorities for `src` READMEs established.

---

### Step 2: Audit Existing `src` Documentation

**Objective**: Identify which `src` modules need updates and what needs updating.

**Tasks**:

1. For each module under `src/` that has a `README.md`:
   - Perform documentation audit (see "Documentation Audit Process").
   - Check when module code last changed.
   - Verify all examples work.
   - Check all links are valid.
   - Compare with standards.
2. Create an audit report (e.g., under `docs/implementation_plans/audits/`):
   - Modules needing updates (priority order).
   - Specific issues per module.
   - Estimated effort per module.

**Success criteria**:

- Complete audit report exists for `src` READMEs.
- All modules categorized (up-to-date, needs minor update, needs major update).
- Priority order for `src` documentation updates established.

---

### Step 3: Update High-Priority `src` Modules

**Objective**: Update high-priority `src` modules (foundational, frequently used, or heavily outdated).

**Modules to update** (initial priority set, can be refined by the new audit):

- `src/evaluation/selection/` – Reason: Recently modified, may have API/structure changes.
- `src/evaluation/benchmarking/` – Reason: Recently modified, may have API/structure changes.
- `src/training/hpo/` – Reason: Complex module, frequently used, needs example verification.
- `src/infrastructure/tracking/` – Reason: SSOT module, frequently referenced, needs cross-reference verification.
- `src/infrastructure/paths/` – Reason: Frequently used, complex API, needs example verification.

**Batch Process** (repeat for each module):

1. **Review**: Read existing README and perform audit.
2. **Update**: Follow update process (see "Update Process").
3. **Verify**: Test examples, check links, verify standards compliance.
4. **Cross-reference**: Update related module READMEs.
5. **Mark complete**: Update audit report.

**Success criteria**:

- All high-priority `src` modules updated.
- All examples tested and working.
- All cross-references valid.
- Standards compliance verified.

---

### Step 4: Update Medium-Priority `src` Modules

**Objective**: Update medium-priority `src` modules.

**Modules to update** (subject to refinement by the audit):

- `src/training/core/` – Core module, verify examples and API reference.
- `src/training/execution/` – Execution infrastructure, verify integration points.
- `src/infrastructure/config/` – Configuration module, verify config docs.
- `src/infrastructure/naming/` – Naming utilities, verify API reference.
- `src/infrastructure/platform/` – Platform detection, verify examples.
- `src/common/` – Shared utilities, verify API reference completeness.
- `src/core/` – Core utilities, verify structure.
- `src/data/` – Data loading, verify examples.
- `src/deployment/` – Deployment module, verify structure.
- `src/deployment/conversion/` – Conversion utilities, verify examples.
- `src/deployment/api/` – API module, verify structure.
- `src/evaluation/` – Evaluation module overview, verify structure and linkage.
- `src/testing/` – Testing utilities, verify examples.

**Process**: Same as Step 3.

**Success criteria**:

- All medium-priority `src` modules updated.
- Standards compliance verified.

---

### Step 5: Update Lower-Priority `src` Modules

**Objective**: Update lower-priority `src` modules (stable, cosmetic updates).

**Modules to update**:

- `src/infrastructure/` – Main infrastructure README, verify structure and links.
- `src/training/` – Main training README, verify structure and links.
- Any remaining `src` modules with minor issues identified in the audit.

**Process**: Same as Step 3.

**Success criteria**:

- All lower-priority `src` modules updated.
- Standards compliance verified.

---

### Step 6: Update Cross-References and Module Index

**Objective**: Ensure all cross-references and navigation involving `src` modules are current.

**Tasks**:

1. Update any module index (if exists) that references `src` modules:
   - Verify all links work.
   - Update descriptions if modules changed.
   - Add any new modules.
   - Remove deprecated modules.
2. Update root `README.md` (and any high-level docs):
   - Verify links to `src` modules or module index.
   - Update if structure changed.
3. Verify all "Related Modules" sections in `src` READMEs:
   - All links valid.
   - Descriptions current.
   - No circular or broken references.

**Success criteria**:

- Any module index is current and all links work.
- Root README links are valid.
- All "Related Modules" sections are current.
- No broken cross-references involving `src`.

---

### Step 7: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all updated `src` documentation.

**Tasks**:

1. Review all updated `src` READMEs against Definition of Done checklist.
2. **Enforce example testing**: Verify all examples work.
3. Check for consistency:
   - Terminology consistency.
   - Formatting consistency.
   - Link accuracy.
   - Standards compliance.
4. Create an update summary document (e.g., `docs/implementation_plans/documentation-update-summary.md` or a new summary file):
   - List all `src` modules updated.
   - Note any remaining gaps or limitations.
   - Document any modules deferred.
   - Include example testing status.

**Success criteria**:

- All updated `src` READMEs pass Definition of Done checklist.
- All code examples are tested and work.
- Cross-references are accurate.
- Update summary exists.
- No broken links or outdated examples.

## Success Criteria (Overall)

- ✅ All outdated `src` documentation has been updated.
- ✅ All `src` code examples are tested and accurate.
- ✅ All cross-references involving `src` are valid and current.
- ✅ Documentation follows current standards.
- ✅ Module Structure for `src` modules reflects current codebase.
- ✅ API Reference sections document current APIs (or link to source).
- ✅ Integration Points for `src` modules are current.
- ✅ Any module index / high-level docs referencing `src` are updated and accurate.

## Module Update Priority (for `src/`)

**High Priority** (Critical updates needed):

1. `src/evaluation/selection/` – Recently modified, may have API/structure changes.
2. `src/evaluation/benchmarking/` – Recently modified, may have API/structure changes.
3. `src/training/hpo/` – Complex module, frequently used, needs example verification.
4. `src/infrastructure/tracking/` – SSOT module, frequently referenced, needs cross-reference verification.
5. `src/infrastructure/paths/` – Frequently used, complex API, needs example verification.

**Medium Priority** (Important updates):

6. `src/training/core/` – Core module, verify examples and API reference.
7. `src/training/execution/` – Execution infrastructure, verify integration points.
8. `src/infrastructure/config/` – Configuration module, verify config docs.
9. `src/infrastructure/naming/` – Naming utilities, verify API reference.
10. `src/infrastructure/platform/` – Platform detection, verify examples.
11. `src/common/` – Shared utilities, verify API reference completeness.
12. `src/core/` – Core utilities, verify structure.
13. `src/data/` – Data loading, verify examples.
14. `src/deployment/` – Deployment module, verify structure.
15. `src/deployment/conversion/` – Conversion utilities, verify examples.
16. `src/deployment/api/` – API module, verify structure.
17. `src/evaluation/` – Evaluation module overview, verify structure.
18. `src/testing/` – Testing utilities, verify examples.

**Lower Priority** (Nice to have updates):

19. `src/infrastructure/` – Main infrastructure README, verify structure.
20. `src/training/` – Main training README, verify structure.
21. Any remaining `src` modules with minor issues identified in the audit.

## Maintenance Guidelines

After `src` documentation update is complete:

1. **Ongoing maintenance**:
   - Update documentation when `src` module code changes.
   - Review quarterly for accuracy.
   - Test examples when APIs change.
   - Keep cross-references current.

2. **Update triggers**:
   - Public API changes for `src` modules.
   - `src` module structure changes.
   - New major features added under `src/`.
   - Integration patterns change (e.g., AzureML, MLflow, deployment paths).
   - Configuration options change.

3. **Documentation ownership**:
   - Module maintainers are responsible for their module docs.
   - PR reviews for `src` changes should check documentation updates.
   - Use this update plan for periodic `src` documentation reviews.

## Notes

- This plan is for **updating existing documentation** under `src/`, not creating new docs from scratch.
- Use `docs/templates/TEMPLATE-module-documentation-plan.md` if creating documentation for a new `src` module.
- Focus on accuracy and current state over comprehensive rewrites.
- Prioritize fixing broken examples and links first.
- Update incrementally – don’t try to update all modules at once; work by priority group.



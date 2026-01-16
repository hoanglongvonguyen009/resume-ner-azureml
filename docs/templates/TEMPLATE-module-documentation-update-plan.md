# Master Plan: Update Technical Documentation for [MODULE_TYPE] Modules

## Goal

Update and maintain comprehensive technical documentation (README.md) for existing modules in `[TARGET_DIRECTORY]/` to:
1. **Keep documentation current**: Ensure all READMEs reflect current module structure, APIs, and usage patterns
2. **Improve consistency**: Standardize documentation format across all modules using latest standards
3. **Fix outdated content**: Update examples, links, and references that are no longer accurate
4. **Enhance completeness**: Add missing sections, improve clarity, and fill documentation gaps

## Status

**Last Updated**: [YYYY-MM-DD]

**Current State**:
- ✅ `[TARGET_DIRECTORY]/[module1]/README.md` exists (last updated: [DATE])
- ✅ `[TARGET_DIRECTORY]/[module2]/README.md` exists (last updated: [DATE])
- ⏳ `[TARGET_DIRECTORY]/[module3]/README.md` exists but may be outdated
- ⏳ Documentation standards have been updated since last review

### Completed Steps
- ✅ Step 0: Documentation audit completed

### Pending Steps
- ⏳ Step 1: Review documentation standards and identify gaps
- ⏳ Step 2: Audit existing documentation for outdated content
- ⏳ Step 3: Update [priority_group_1] modules ([list modules])
- ⏳ Step 4: Update [priority_group_2] modules ([list modules])
- ⏳ Step 5: Update [priority_group_3] modules ([list modules])
- ⏳ Step 6: Update cross-references and module index
- ⏳ Step 7: Final review and consistency check

## Preconditions

- Existing documentation exists (use `TEMPLATE-module-documentation-plan.md` if creating from scratch)
- Documentation standards are defined (see `TEMPLATE-documentation_standards.md`)
- Module structure is relatively stable (major refactoring should wait)

## Documentation Update Checklist

Each module README should be reviewed against this checklist:

### Content Accuracy

- [ ] **Module Structure**: Lists current entry points and folders (not outdated files)
- [ ] **API Reference**: Documents current public APIs (removed deprecated, added new)
- [ ] **Code Examples**: All examples work with current codebase
- [ ] **Configuration**: Documents current config options and environment variables
- [ ] **Integration Points**: Reflects current dependencies and usage patterns
- [ ] **CLI Usage**: Documents current CLI commands and options

### Completeness

- [ ] **TL;DR / Quick Start**: Present and includes working example
- [ ] **Overview**: 1-2 paragraphs with bullet points (no fluff)
- [ ] **Usage**: At least one working basic example
- [ ] **Testing**: Includes runnable test commands
- [ ] **Related Modules**: Links are valid and current

### Standards Compliance

- [ ] **Format**: Follows current documentation standards template
- [ ] **Structure**: Uses required sections, omits empty optional sections
- [ ] **Examples**: All examples are tested and working
- [ ] **Cross-references**: Uses relative paths, all links valid
- [ ] **API Reference**: Limited to top-level stable surface (max 10 items)

## Documentation Audit Process

Before updating documentation, perform this **repeatable audit** to identify what needs updating:

### 1. Scan Module Changes

```bash
# Check when module files were last modified
find [TARGET_DIRECTORY]/module -name "*.py" -type f -exec stat -c "%y %n" {} \; | sort -r | head -20

# Check git history for recent changes (if using git)
git log --oneline --since="[DATE]" -- [TARGET_DIRECTORY]/module/ | head -20

# List files that exist in code but not mentioned in README
find [TARGET_DIRECTORY]/module -name "*.py" -type f | while read f; do
    basename "$f" | grep -q "$(grep -o '[a-zA-Z_]*\.py' README.md)" || echo "Not in README: $f"
done
```

### 2. Verify Code Examples

```bash
# Test if example imports work
# (Manually test each code example in README)

# Check if CLI commands still exist
grep -r "CLI Usage\|python -m\|cli\." [TARGET_DIRECTORY]/module/README.md | while read line; do
    # Verify command exists in codebase
    echo "Verify: $line"
done
```

### 3. Check Cross-References

```bash
# Find all links in README
grep -o '\[.*\](.*\.md)' [TARGET_DIRECTORY]/module/README.md | while read link; do
    # Extract path and verify file exists
    path=$(echo "$link" | sed 's/.*](\(.*\))/\1/')
    [ -f "$path" ] || echo "Broken link: $link"
done
```

### 4. Compare with Standards

```bash
# Check if README has all required sections
required_sections=("TL;DR" "Overview" "Module Structure" "Usage" "Testing" "Related Modules")
for section in "${required_sections[@]}"; do
    grep -q "## $section" [TARGET_DIRECTORY]/module/README.md || echo "Missing: $section"
done
```

### 5. Document Findings

Create an audit report:
- **Outdated content**: [list items that need updating]
- **Missing sections**: [list required sections not present]
- **Broken examples**: [list examples that don't work]
- **Broken links**: [list invalid cross-references]
- **API changes**: [list new/deprecated APIs not documented]
- **Structure changes**: [list module structure changes not reflected]

## Update Process

For each module README that needs updating:

### 1. Review Current State

1. Read existing README completely
2. Perform documentation audit (see above)
3. Compare with current module code
4. Compare with documentation standards
5. Create update checklist

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
   - Add examples for new functionality

4. **Update Integration Points**:
   - Update dependency lists
   - Update "Used By" sections
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
3. **Review Format**: Ensure follows standards template
4. **Check Completeness**: Verify all required sections present
5. **Update Date**: Update "Last Updated" if module has one

### 4. Update Cross-References

1. Update this module in related module READMEs
2. Update module index if structure changed
3. Update root README if needed

## Per-Module Definition of Done (Update)

Each module README update is considered complete when:

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

### Step 1: Review Documentation Standards and Identify Gaps

**Objective**: Understand current standards and identify what needs updating

**Tasks**:
1. Review `TEMPLATE-documentation_standards.md` for current standards
2. Compare existing READMEs with current standards template
3. Identify common gaps across modules:
   - Missing required sections
   - Outdated format/structure
   - Non-standard examples
   - Missing cross-references
4. Create gap analysis document

**Success criteria**:
- Gap analysis document created
- Common issues identified across modules
- Update priorities established

---

### Step 2: Audit Existing Documentation

**Objective**: Identify which modules need updates and what needs updating

**Tasks**:
1. For each module with README:
   - Perform documentation audit (see "Documentation Audit Process")
   - Check when module code last changed
   - Verify all examples work
   - Check all links are valid
   - Compare with standards
2. Create audit report:
   - Modules needing updates (priority order)
   - Specific issues per module
   - Estimated effort per module

**Success criteria**:
- Complete audit report exists
- All modules categorized (up-to-date, needs minor update, needs major update)
- Priority order established

---

### Step 3: Update [Priority Group 1] Modules

**Objective**: Update high-priority modules (foundational, frequently used, or heavily outdated)

**Modules to update**:
- `[TARGET_DIRECTORY]/[module1]/` - [Reason: e.g., "API changed significantly"]
- `[TARGET_DIRECTORY]/[module2]/` - [Reason: e.g., "Missing required sections"]

**Batch Process** (repeat for each module):

1. **Review**: Read existing README and perform audit
2. **Update**: Follow update process (see "Update Process" above)
3. **Verify**: Test examples, check links, verify standards compliance
4. **Cross-reference**: Update related module READMEs
5. **Mark complete**: Update audit report

**Success criteria**:
- All priority group 1 modules updated
- All examples tested and working
- All cross-references valid
- Standards compliance verified

---

### Step 4: Update [Priority Group 2] Modules

**Objective**: Update medium-priority modules

**Modules to update**:
- `[TARGET_DIRECTORY]/[module3]/` - [Reason]
- `[TARGET_DIRECTORY]/[module4]/` - [Reason]

**Process**: Same as Step 3

**Success criteria**:
- All priority group 2 modules updated
- Standards compliance verified

---

### Step 5: Update [Priority Group 3] Modules

**Objective**: Update lower-priority modules

**Modules to update**:
- `[TARGET_DIRECTORY]/[module5]/` - [Reason]
- `[TARGET_DIRECTORY]/[module6]/` - [Reason]

**Process**: Same as Step 3

**Success criteria**:
- All priority group 3 modules updated
- Standards compliance verified

---

### Step 6: Update Cross-References and Module Index

**Objective**: Ensure all cross-references and navigation are current

**Tasks**:
1. Update module index (`docs/[index_location]/INDEX.md`):
   - Verify all links work
   - Update descriptions if modules changed
   - Add any new modules
   - Remove deprecated modules
2. Update root `README.md`:
   - Verify links to module index
   - Update if structure changed
3. Verify all "Related Modules" sections:
   - All links valid
   - Descriptions current
   - No circular or broken references

**Success criteria**:
- Module index is current and all links work
- Root README links are valid
- All "Related Modules" sections are current
- No broken cross-references

---

### Step 7: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all updated documentation

**Tasks**:
1. Review all updated READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all examples work
3. Check for consistency:
   - Terminology consistency
   - Formatting consistency
   - Link accuracy
   - Standards compliance
4. Create update summary:
   - List all modules updated
   - Note any remaining gaps or limitations
   - Document any modules deferred
   - Include example testing status

**Success criteria**:
- All updated READMEs pass Definition of Done checklist
- All code examples are tested and work
- Cross-references are accurate
- Update summary exists
- No broken links or outdated examples

## Success Criteria (Overall)

- ✅ All outdated documentation has been updated
- ✅ All code examples are tested and accurate
- ✅ All cross-references are valid and current
- ✅ Documentation follows current standards
- ✅ Module Structure reflects current codebase
- ✅ API Reference documents current APIs
- ✅ Integration Points are current
- ✅ Module index is updated and accurate

## Module Update Priority

**High Priority** (Critical updates needed):
1. `[module1]/` - [Reason: e.g., "API changed, examples broken"]
2. `[module2]/` - [Reason: e.g., "Missing required sections"]
3. `[module3]/` - [Reason: e.g., "Structure changed significantly"]

**Medium Priority** (Important updates):
4. `[module4]/` - [Reason: e.g., "Minor API additions"]
5. `[module5]/` - [Reason: e.g., "Format needs standardization"]

**Lower Priority** (Nice to have updates):
6. `[module6]/` - [Reason: e.g., "Minor improvements"]
7. `[module7]/` - [Reason: e.g., "Cosmetic updates"]

## Maintenance Guidelines

After update is complete:

1. **Ongoing maintenance**:
   - Update documentation when module code changes
   - Review quarterly for accuracy
   - Test examples when APIs change
   - Keep cross-references current

2. **Update triggers**:
   - Public API changes
   - Module structure changes
   - New major features added
   - Integration patterns change
   - Configuration options change

3. **Documentation ownership**:
   - Module maintainers responsible for their module docs
   - PR reviews should check documentation updates
   - Use this update plan for periodic reviews

## Notes

- This plan is for **updating existing documentation**, not creating new docs
- Use `TEMPLATE-module-documentation-plan.md` if creating documentation from scratch
- Focus on accuracy and current state over comprehensive rewrites
- Prioritize fixing broken examples and links
- Update incrementally - don't try to update everything at once

## Template Usage Instructions

When using this template:

1. **Replace placeholders**:
   - `[MODULE_TYPE]` - Type of modules (e.g., "Source", "Infrastructure")
   - `[TARGET_DIRECTORY]` - Directory containing modules (e.g., "src", "lib")
   - `[module1]`, `[module2]` - Actual module names
   - `[Priority Group 1]`, etc. - Priority group names
   - `[DATE]` - Relevant dates
   - `[index_location]` - Where module index is located

2. **Customize audit process**: Adjust audit commands to match your codebase structure

3. **Set priorities**: Define your own priority groups based on:
   - How outdated the documentation is
   - How frequently the module is used
   - How much the module has changed
   - Impact of outdated documentation

4. **Update incrementally**: Don't try to update all modules at once - work in priority groups


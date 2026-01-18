# Gap Analysis: Documentation Standards vs. Current READMEs

**Date**: 2026-01-18  
**Plan**: MASTER-20260118-1700-module-documentation-update-plan.plan.md  
**Step**: Step 1 - Review Documentation Standards and Identify Gaps

## Executive Summary

After reviewing the documentation standards template (`docs/templates/TEMPLATE-documentation_standards.md`) and sampling 8 README files across different modules, I've identified common gaps and inconsistencies. The standards are well-defined, but many existing READMEs deviate from them in specific ways.

## Standards Template Requirements

### Required Sections (All Modules)
1. ✅ **Title** - Module name as H1
2. ✅ **TL;DR / Quick Start** - Required for complex modules, recommended for all
3. ✅ **Overview** - 1-2 paragraphs describing purpose and role (use bullet points)
4. ✅ **Module Structure** - List key entry points and folders only (not every file)
5. ✅ **Usage** - At least one working basic example
6. ✅ **Testing** - Recommended for all, required for complex modules
7. ✅ **Related Modules** - Links to related documentation

### Optional Sections (Include Only When Applicable)
- **Key Concepts** - For modules with domain-specific concepts
- **Advanced Usage** - For complex modules
- **CLI Usage** - For modules with CLI entry points
- **API Reference** - For modules with public APIs (**max 10 top-level items**)
- **Configuration** - For configurable modules
- **Integration Points** - For modules with complex dependencies
- **Examples** - For modules that benefit from multiple examples
- **Best Practices** - For modules with usage guidelines
- **Notes** - For important caveats or limitations

## Common Gaps Identified

### 1. API Reference Violations (HIGH PRIORITY)

**Issue**: Several READMEs exceed the 10-item limit for API Reference sections.

**Examples**:
- `src/evaluation/selection/README.md`: Contains 20+ API items across multiple subsections (Selection Functions, Trial Finding, Artifact Acquisition, Workflows, Study Analysis, Selection Logic, Caching)
- `src/training/hpo/README.md`: Contains 15+ API items across multiple subsections
- `src/infrastructure/tracking/README.md`: Contains 10+ items but properly organized

**Standards Violation**: 
> "API Reference - For modules with public APIs (**max 10 top-level items**)"

**Impact**: Makes documentation harder to scan and maintain. Users may miss important APIs buried in long lists.

**Recommendation**: 
- Limit API Reference to top 10 most important/commonly used APIs
- Move detailed APIs to "For detailed signatures, see source code" with links
- Consider splitting into subsections only if truly necessary (e.g., "Main APIs" + "Utilities")

### 2. Module Structure Over-Detailed (MEDIUM PRIORITY)

**Issue**: Some READMEs list too many individual files instead of focusing on key entry points and folders.

**Examples**:
- `src/evaluation/selection/README.md`: Lists 11 individual files (`selection_logic.py`, `local_selection.py`, `mlflow_selection.py`, etc.) instead of grouping into logical folders
- `src/training/core/README.md`: Lists 7 individual files, but this is acceptable for a simple module
- `src/infrastructure/config/README.md`: Lists 9 individual files

**Standards Violation**:
> "Module Structure - List key entry points and folders only (not every file)"

**Impact**: Makes it harder to understand module organization at a glance. Too much detail obscures the high-level structure.

**Recommendation**:
- Group related files into folders when possible
- List only top-level entry points (main functions/classes) and key folders
- Use format: `folder/`: Purpose description (not exhaustive file lists)

**Good Example** (`src/training/hpo/README.md`):
```markdown
- `core/`: Core HPO functionality
- `execution/`: Trial execution
- `checkpoint/`: Checkpoint storage and cleanup
```

### 3. Example Testing Status Unknown (HIGH PRIORITY)

**Issue**: Standards require examples to be "copy/paste runnable" or verified commands, but there's no indication in READMEs whether examples have been tested.

**Standards Requirement**:
> "Examples must be copy/paste runnable or reference `python -m ...` commands that work"
> "Enforcement: Examples should be tested via: Manual smoke check, doctest/pytest snippet harness, or verified `python -m ...` commands"

**Impact**: Users may encounter broken examples, reducing trust in documentation.

**Recommendation**:
- Add a note in each README indicating example testing status (if not already verified)
- During update process, test all examples and mark them as verified
- Consider adding a "Last Verified" date for examples

### 4. Cross-Reference Verification Needed (MEDIUM PRIORITY)

**Issue**: No systematic verification that all "Related Modules" links are valid.

**Standards Requirement**:
> "Cross-references are accurate and use relative paths"

**Impact**: Broken links reduce usability and trust.

**Recommendation**:
- During Step 2 audit, verify all cross-references
- Use relative paths consistently
- Check that linked READMEs exist

### 5. Format Inconsistencies (LOW PRIORITY)

**Issue**: Minor variations in formatting across READMEs.

**Examples**:
- Some use `## API Reference` while others use `## API Reference` with subsections
- Some use code blocks with `python` tag, others may vary
- Some have "See Also" sections, others don't

**Impact**: Reduces consistency and professional appearance.

**Recommendation**:
- Standardize section headings
- Ensure consistent code block formatting
- Use "See Also" only when referencing external docs (not for internal cross-references)

### 6. Missing Optional Sections (LOW PRIORITY)

**Issue**: Some modules could benefit from optional sections but don't have them.

**Examples**:
- `src/infrastructure/paths/README.md`: Has extensive "Repository Root Detection" section (good) but could benefit from "Best Practices" section
- `src/training/core/README.md`: Could benefit from "Best Practices" section for training workflows

**Impact**: Missing helpful guidance for users.

**Recommendation**:
- Add optional sections when they add value
- Don't create empty sections (per standards)

### 7. Overview Length Variations (LOW PRIORITY)

**Issue**: Some Overview sections are longer than 1-2 paragraphs.

**Examples**:
- `src/evaluation/selection/README.md`: Overview is concise (good)
- `src/infrastructure/tracking/README.md`: Overview includes layering explanation (acceptable for complex module)
- `src/infrastructure/paths/README.md`: Overview is appropriately detailed

**Standards Requirement**:
> "Overview - 1-2 paragraphs describing purpose and role (use bullet points)"

**Impact**: Some Overviews may be too verbose.

**Recommendation**:
- Keep Overview to 1-2 paragraphs with bullet points
- Move detailed explanations to "Key Concepts" or "Notes" sections

## Priority Classification

### 🔴 HIGH PRIORITY (Fix Before Merge)
1. **API Reference violations** - Exceeds 10-item limit
2. **Example testing status** - Need to verify all examples work

### 🟠 MEDIUM PRIORITY (Fix Soon)
1. **Module Structure over-detailed** - Too many individual files listed
2. **Cross-reference verification** - Need to verify all links work

### 🟢 LOW PRIORITY (Fix When Convenient)
1. **Format inconsistencies** - Minor formatting variations
2. **Missing optional sections** - Could add helpful sections
3. **Overview length** - Some may be too verbose

## Module-Specific Findings

### High-Priority Modules (Recently Changed or Complex)

#### `src/evaluation/selection/README.md`
- **API Reference**: 20+ items (violates 10-item limit)
- **Module Structure**: Lists 11 individual files (should group into folders)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/evaluation/benchmarking/README.md`
- **Status**: Not reviewed yet (pending Step 2 audit)

#### `src/training/hpo/README.md`
- **API Reference**: 15+ items (violates 10-item limit)
- **Module Structure**: Good (groups into folders)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/infrastructure/tracking/README.md`
- **API Reference**: ~10 items (borderline, but well-organized)
- **Module Structure**: Good (groups into folders)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/infrastructure/paths/README.md`
- **API Reference**: ~10 items (acceptable)
- **Module Structure**: Good (groups into folders)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

### Medium-Priority Modules

#### `src/training/core/README.md`
- **API Reference**: 8 items (acceptable)
- **Module Structure**: Lists 7 files (acceptable for simple module)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/infrastructure/config/README.md`
- **API Reference**: ~10 items (acceptable)
- **Module Structure**: Lists 9 files (could be grouped better)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/common/README.md`
- **API Reference**: ~15 items (violates 10-item limit)
- **Module Structure**: Good (groups into folders)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

#### `src/core/README.md`
- **API Reference**: ~10 items (acceptable)
- **Module Structure**: Good (lists 3 files, simple module)
- **Examples**: Multiple examples present, need verification
- **Cross-references**: Need verification

## Update Priorities Established

Based on the gap analysis, update priorities are:

### Priority 1: High-Priority Modules (Step 3)
1. `src/evaluation/selection/` - API Reference violation, Module Structure over-detailed
2. `src/evaluation/benchmarking/` - Recently modified, needs audit
3. `src/training/hpo/` - API Reference violation
4. `src/infrastructure/tracking/` - SSOT module, needs example verification
5. `src/infrastructure/paths/` - Complex API, needs example verification

### Priority 2: Medium-Priority Modules (Step 4)
- Modules with minor API Reference violations (`src/common/`)
- Modules with Module Structure issues (`src/infrastructure/config/`)
- Other frequently used modules

### Priority 3: Lower-Priority Modules (Step 5)
- Stable modules with only format inconsistencies
- Modules needing cosmetic updates

## Common Update Patterns

### Pattern 1: Reduce API Reference to Top 10
**Action**: Identify top 10 most important/commonly used APIs, move others to "For detailed signatures, see source code"

### Pattern 2: Group Module Structure
**Action**: Group related files into folders, list only key entry points

### Pattern 3: Verify Examples
**Action**: Test all code examples, mark as verified, fix broken examples

### Pattern 4: Verify Cross-References
**Action**: Check all "Related Modules" links, fix broken links, ensure relative paths

### Pattern 5: Standardize Format
**Action**: Ensure consistent section headings, code block formatting, "See Also" usage

## Success Criteria for Step 1

✅ **Gap analysis document created** - This document  
✅ **Common issues identified** - 7 common gaps identified  
✅ **Update priorities established** - 3 priority levels defined

## Next Steps

Proceed to **Step 2: Audit Existing Documentation** to:
1. Perform detailed audit of all 40 README files
2. Categorize each module (up-to-date, needs minor update, needs major update)
3. Create detailed audit report with specific issues per module
4. Estimate effort per module


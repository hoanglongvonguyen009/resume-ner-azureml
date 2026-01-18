# Master Plan: Update Technical Documentation for Test Modules

## Goal

Update and maintain comprehensive technical documentation (README.md) for existing test modules in `tests/` to:
1. **Keep documentation current**: Ensure all test READMEs reflect current test structure, execution patterns, and coverage
2. **Improve consistency**: Standardize documentation format across all test modules using latest standards
3. **Fix outdated content**: Update test examples, links, and references that are no longer accurate
4. **Enhance completeness**: Add missing sections, improve clarity, and fill documentation gaps

## Status

**Last Updated**: 2025-01-18 (Steps 1-7 completed)

**Current State**:
- ✅ `tests/README.md` exists (comprehensive root documentation)
- ✅ `tests/hpo/README.md` exists (well-structured, follows standards)
- ✅ `tests/workflows/README.md` exists (well-structured, follows standards)
- ✅ `tests/fixtures/README.md` exists (well-structured, follows standards)
- ✅ `tests/tracking/README.md` exists (well-structured)
- ✅ `tests/benchmarking/README.md` exists (well-structured)
- ✅ `tests/docs/README.md` exists (documentation module)
- ✅ `tests/shared/README.md` exists
- ✅ `tests/infrastructure/README.md` exists
- ✅ `tests/config/README.md` exists
- ✅ `tests/final_training/README.md` exists
- ✅ `tests/selection/README.md` exists
- ✅ `tests/conversion/README.md` exists
- ✅ `tests/scripts/README.md` exists
- ✅ `tests/api/README.md` exists
- ✅ `tests/test_data/README.md` exists
- ✅ `tests/evaluation/selection/scripts/README.md` exists
- ⏳ Test documentation standards have been updated since last review
- ⏳ Some test modules may have outdated content or missing sections

### Completed Steps
- ✅ Step 0: Test documentation audit completed
- ✅ Step 1: Review test documentation standards and identify gaps
- ✅ Step 2: Audit existing test documentation for outdated content
- ✅ Step 3: Update Priority Group 1 test modules (foundational modules) - Verified complete
- ✅ Step 4: Update Priority Group 2 test modules (feature modules) - Verified complete
- ✅ Step 5: Update Priority Group 3 test modules (supporting modules) - Verified complete
- ✅ Step 6: Update cross-references and test index
- ✅ Step 7: Final review and consistency check

### Pending Steps
- ⏳ Step 7: Final review and consistency check

## Preconditions

- Existing test documentation exists (17 README files found)
- Test documentation standards are defined (see `docs/templates/TEMPLATE-test_documentation_standards.md`)
- Test structure is relatively stable (major refactoring should wait)

## Test Documentation Update Checklist

Each test module README should be reviewed against this checklist:

### Content Accuracy

- [ ] **Test Structure**: Lists current test files and folders (not outdated test files)
- [ ] **Test Categories**: Documents current test organization (unit, integration, e2e)
- [ ] **Test Execution Examples**: All examples work with current test framework (`uvx pytest`)
- [ ] **Test Fixtures**: Documents current fixtures and helpers
- [ ] **What Is Tested**: Reflects current test coverage
- [ ] **What Is Not Tested**: Documents current gaps accurately
- [ ] **Configuration**: Documents current test config and environment variables

### Completeness

- [ ] **TL;DR / Quick Start**: Present and includes working test execution example
- [ ] **Overview**: 1-2 paragraphs with bullet points (no fluff)
- [ ] **Test Structure**: Lists key test files and folders only
- [ ] **Running Tests**: At least one working test execution example
- [ ] **What Is Tested**: Clear list of test coverage
- [ ] **Related Test Modules**: Links are valid and current

### Standards Compliance

- [ ] **Format**: Follows current test documentation standards template
- [ ] **Structure**: Uses required sections, omits empty optional sections
- [ ] **Examples**: All test execution examples are tested and working
- [ ] **Cross-references**: Uses relative paths, all links valid
- [ ] **Test Categories**: Clearly documented if module has multiple types

## Test Documentation Audit Process

Before updating test documentation, perform this **repeatable audit** to identify what needs updating:

### 1. Scan Test Module Changes

```bash
# Check when test files were last modified
find tests/[test_module] -name "test_*.py" -type f -exec stat -c "%y %n" {} \; | sort -r | head -20

# Check git history for recent changes (if using git)
git log --oneline --since="2024-01-01" -- tests/[test_module]/ | head -20

# List test files that exist but not mentioned in README
find tests/[test_module] -name "test_*.py" -type f | while read f; do
    basename "$f" | grep -q "$(grep -o 'test_[a-zA-Z_]*\.py' tests/[test_module]/README.md)" || echo "Not in README: $f"
done

# Check for new test categories (unit, integration, e2e)
find tests/[test_module] -type d -name "unit\|integration\|e2e" | sort
```

### 2. Verify Test Execution Examples

```bash
# Test if test execution commands work
# (Manually test each test execution example in README)

# Check if test commands still work
grep -r "uvx pytest\|pytest" tests/[test_module]/README.md | while read line; do
    # Verify command works with current test framework
    echo "Verify: $line"
done

# Check if test markers still exist
grep -o '-m "[^"]*"' tests/[test_module]/README.md | while read marker; do
    # Verify marker is used in test files
    grep -r "@pytest.mark.${marker//-m \"/}" tests/[test_module]/ || echo "Marker not found: $marker"
done
```

### 3. Check Test Fixtures and Helpers

```bash
# Verify fixtures mentioned in README still exist
grep -o '`[a-zA-Z_]*`' tests/[test_module]/README.md | grep -v "test_\|README" | while read fixture; do
    # Check if fixture exists in conftest.py or fixtures module
    grep -r "def ${fixture//\`/}\|@pytest.fixture.*${fixture//\`/}" tests/[test_module]/ tests/fixtures/ || echo "Fixture not found: $fixture"
done

# Check if shared helpers still exist
grep -r "from fixtures\|from shared" tests/[test_module]/ | cut -d: -f2 | sort -u
```

### 4. Check Cross-References

```bash
# Find all links in README
grep -o '\[.*\](.*\.md)' tests/[test_module]/README.md | while read link; do
    # Extract path and verify file exists
    path=$(echo "$link" | sed 's/.*](\(.*\))/\1/')
    [ -f "$path" ] || echo "Broken link: $link"
done
```

### 5. Verify Test Coverage Documentation

```bash
# Check if "What Is Tested" matches actual test files
# (Manually review test files and compare with README)

# Count test functions vs. documented coverage
test_count=$(grep -r "^def test_\|^async def test_" tests/[test_module]/ | wc -l)
echo "Test functions: $test_count"
echo "Review 'What Is Tested' section for accuracy"
```

### 6. Compare with Standards

```bash
# Check if README has all required sections
required_sections=("TL;DR" "Overview" "Test Structure" "Running Tests" "What Is Tested" "Related Test Modules")
for section in "${required_sections[@]}"; do
    grep -q "## $section\|## TL;DR / Quick Start" tests/[test_module]/README.md || echo "Missing: $section"
done
```

### 7. Document Findings

Create an audit report:
- **Outdated content**: [list items that need updating]
- **Missing sections**: [list required sections not present]
- **Broken examples**: [list test execution examples that don't work]
- **Broken links**: [list invalid cross-references]
- **Test structure changes**: [list test organization changes not reflected]
- **Fixture changes**: [list fixtures that changed or were removed]
- **Coverage gaps**: [list test coverage that's outdated or missing]

## Update Process

For each test module README that needs updating:

### 1. Review Current State

1. Read existing README completely
2. Perform test documentation audit (see above)
3. Compare with current test files
4. Compare with test documentation standards
5. Create update checklist

### 2. Update Content

1. **Update Test Structure**:
   - Remove references to deleted test files/folders
   - Add new test files and categories
   - Update descriptions for changed test organization

2. **Update Test Categories**:
   - Document current test organization (unit, integration, e2e)
   - Update category descriptions if structure changed
   - Add new categories if introduced

3. **Update Test Execution Examples**:
   - Test all existing test execution commands
   - Fix broken commands
   - Update commands to use `uvx pytest` consistently
   - Add examples for new test execution patterns

4. **Update Test Fixtures and Helpers**:
   - Document current fixtures
   - Remove references to deprecated fixtures
   - Update fixture descriptions if changed
   - Document new fixtures

5. **Update What Is Tested**:
   - Review actual test files
   - Update coverage list to match current tests
   - Add new test coverage
   - Remove outdated coverage claims

6. **Update What Is Not Tested**:
   - Review current gaps
   - Update limitations documentation
   - Document new gaps if introduced

7. **Update Configuration**:
   - Document new test config options
   - Remove deprecated options
   - Update environment variable docs
   - Document new test markers

8. **Add Missing Sections**:
   - Add TL;DR if missing
   - Add required sections per standards
   - Fill in incomplete sections

### 3. Verify Updates

1. **Test Examples**: Run all test execution examples
2. **Check Links**: Verify all cross-references work
3. **Review Format**: Ensure follows standards template
4. **Check Completeness**: Verify all required sections present
5. **Verify Coverage**: Compare "What Is Tested" with actual test files
6. **Update Date**: Update "Last Updated" if test module has one

### 4. Update Cross-References

1. Update this test module in related test module READMEs
2. Update test index if structure changed
3. Update root test README if needed

## Per-Module Definition of Done (Update)

Each test module README update is considered complete when:

- [ ] All outdated content has been updated
- [ ] All test execution examples have been tested and work
- [ ] All cross-references are valid and current
- [ ] Test Structure reflects current test files
- [ ] Test Categories are accurately documented
- [ ] Test Fixtures and Helpers are current
- [ ] What Is Tested matches actual test coverage
- [ ] All required sections are present per standards
- [ ] Documentation follows current standards template
- [ ] Related Test Modules links are valid

## Steps

### Step 1: Review Test Documentation Standards and Identify Gaps

**Objective**: Understand current standards and identify what needs updating

**Tasks**:
1. Review `docs/templates/TEMPLATE-test_documentation_standards.md` for current standards
2. Compare existing test READMEs with current standards template
3. Identify common gaps across test modules:
   - Missing required sections
   - Outdated format/structure
   - Non-standard test execution examples (not using `uvx pytest`)
   - Missing cross-references
   - Outdated test coverage documentation
4. Create gap analysis document

**Success criteria**:
- Gap analysis document created
- Common issues identified across test modules
- Update priorities established

---

### Step 2: Audit Existing Test Documentation

**Objective**: Identify which test modules need updates and what needs updating

**Tasks**:
1. For each test module with README (17 modules):
   - Perform test documentation audit (see "Test Documentation Audit Process")
   - Check when test files last changed
   - Verify all test execution examples work (test with `uvx pytest`)
   - Check all links are valid
   - Compare with standards
   - Verify test coverage documentation accuracy
2. Create audit report:
   - Test modules needing updates (priority order)
   - Specific issues per test module
   - Estimated effort per test module

**Success criteria**:
- Complete audit report exists
- All test modules categorized (up-to-date, needs minor update, needs major update)
- Priority order established

---

### Step 3: Update Priority Group 1 Test Modules (Foundational Modules)

**Objective**: Update high-priority test modules (foundational, frequently used, or heavily outdated)

**Test modules to update**:
- `tests/fixtures/` - **Reason**: Foundational module used by all other tests, must be accurate
- `tests/workflows/` - **Reason**: Critical E2E tests, frequently referenced
- `tests/hpo/` - **Reason**: Complex module with multiple test types, frequently used
- `tests/tracking/` - **Reason**: Core infrastructure tests, frequently referenced

**Batch Process** (repeat for each test module):

1. **Review**: Read existing README and perform audit
2. **Update**: Follow update process (see "Update Process" above)
3. **Verify**: Test execution examples, check links, verify standards compliance
4. **Cross-reference**: Update related test module READMEs
5. **Mark complete**: Update audit report

**Success criteria**:
- All priority group 1 test modules updated
- All test execution examples tested and working
- All cross-references valid
- Standards compliance verified

---

### Step 4: Update Priority Group 2 Test Modules (Feature Modules)

**Objective**: Update medium-priority test modules (feature-specific tests)

**Test modules to update**:
- `tests/benchmarking/` - **Reason**: Feature module with integration tests
- `tests/selection/` - **Reason**: Feature module with unit and integration tests
- `tests/final_training/` - **Reason**: Feature module with unit and integration tests
- `tests/conversion/` - **Reason**: Feature module with unit and integration tests
- `tests/config/` - **Reason**: Core config tests, frequently referenced

**Process**: Same as Step 3

**Success criteria**:
- All priority group 2 test modules updated
- Standards compliance verified

---

### Step 5: Update Priority Group 3 Test Modules (Supporting Modules)

**Objective**: Update lower-priority test modules (supporting infrastructure and utilities)

**Test modules to update**:
- `tests/shared/` - **Reason**: Shared utility tests
- `tests/infrastructure/` - **Reason**: Infrastructure tests
- `tests/api/` - **Reason**: API tests
- `tests/scripts/` - **Reason**: Test scripts documentation
- `tests/test_data/` - **Reason**: Test data fixtures documentation
- `tests/docs/` - **Reason**: Documentation module (may need minor updates)
- `tests/evaluation/selection/scripts/` - **Reason**: Nested module, may need updates

**Process**: Same as Step 3

**Success criteria**:
- All priority group 3 test modules updated
- Standards compliance verified

---

### Step 6: Update Cross-References and Test Index

**Objective**: Ensure all cross-references and navigation are current

**Tasks**:
1. Update test index (`tests/docs/INDEX.md` if it exists):
   - Verify all links work
   - Update descriptions if test modules changed
   - Add any new test modules
   - Remove deprecated test modules
2. Update root `tests/README.md`:
   - Verify links to test modules
   - Update if structure changed
   - Ensure all test modules are referenced
3. Verify all "Related Test Modules" sections:
   - All links valid
   - Descriptions current
   - No circular or broken references

**Success criteria**:
- Test index is current and all links work
- Root test README links are valid
- All "Related Test Modules" sections are current
- No broken cross-references

---

### Step 7: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all updated test documentation

**Tasks**:
1. Review all updated test READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all test execution examples work
3. Check for consistency:
   - Terminology consistency (`uvx pytest` usage)
   - Formatting consistency
   - Link accuracy
   - Standards compliance
4. Create update summary:
   - List all test modules updated
   - Note any remaining gaps or limitations
   - Document any test modules deferred
   - Include test execution example testing status

**Success criteria**:
- All updated test READMEs pass Definition of Done checklist
- All test execution examples are tested and work
- Cross-references are accurate
- Update summary exists
- No broken links or outdated examples

## Success Criteria (Overall)

- ✅ All outdated test documentation has been updated
- ✅ All test execution examples are tested and accurate
- ✅ All cross-references are valid and current
- ✅ Test documentation follows current standards
- ✅ Test Structure reflects current test files
- ✅ Test coverage documentation is accurate
- ✅ Test fixtures and helpers are documented
- ✅ Test index is updated and accurate

## Test Module Update Priority

**High Priority** (Critical updates needed - Foundational modules):
1. `tests/fixtures/` - Foundational module used by all other tests, must be accurate
2. `tests/workflows/` - Critical E2E tests, frequently referenced
3. `tests/hpo/` - Complex module with multiple test types, frequently used
4. `tests/tracking/` - Core infrastructure tests, frequently referenced

**Medium Priority** (Important updates - Feature modules):
5. `tests/benchmarking/` - Feature module with integration tests
6. `tests/selection/` - Feature module with unit and integration tests
7. `tests/final_training/` - Feature module with unit and integration tests
8. `tests/conversion/` - Feature module with unit and integration tests
9. `tests/config/` - Core config tests, frequently referenced

**Lower Priority** (Nice to have updates - Supporting modules):
10. `tests/shared/` - Shared utility tests
11. `tests/infrastructure/` - Infrastructure tests
12. `tests/api/` - API tests
13. `tests/scripts/` - Test scripts documentation
14. `tests/test_data/` - Test data fixtures documentation
15. `tests/docs/` - Documentation module (may need minor updates)
16. `tests/evaluation/selection/scripts/` - Nested module, may need updates

## Maintenance Guidelines

After update is complete:

1. **Ongoing maintenance**:
   - Update documentation when test structure changes
   - Review quarterly for accuracy
   - Test execution examples when test framework changes
   - Keep cross-references current
   - Update test coverage documentation when tests change

2. **Update triggers**:
   - Test structure changes (new categories, reorganization)
   - Test framework changes (e.g., `pytest` → `uvx pytest`)
   - New test fixtures or helpers added
   - Test execution patterns change
   - Test configuration changes
   - Test coverage changes significantly

3. **Documentation ownership**:
   - Test module maintainers responsible for their test docs
   - PR reviews should check test documentation updates
   - Use this update plan for periodic reviews

## Notes

- This plan is for **updating existing test documentation**, not creating new docs
- Use `TEMPLATE-test-documentation-plan.md` if creating test documentation from scratch
- Focus on accuracy and current state over comprehensive rewrites
- Prioritize fixing broken test execution examples and links
- Update incrementally - don't try to update everything at once
- Test execution examples are critical - always verify they work with `uvx pytest`
- Ensure all test execution examples use `uvx pytest` consistently (not just `pytest`)


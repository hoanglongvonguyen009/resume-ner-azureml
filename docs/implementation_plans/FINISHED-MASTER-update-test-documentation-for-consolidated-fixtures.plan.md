# Master Plan: Update Test Documentation for Consolidated Fixtures

## Goal

Update test module documentation (README.md files) to reflect the consolidated fixtures and helpers created in `FINISHED-MASTER-consolidate-test-fixtures-and-helpers.plan.md`. This ensures all test documentation accurately describes current fixture usage, eliminates references to deprecated fixtures, and provides accurate examples for developers.

## Status

**Last Updated**: 2026-01-16

**Current State**:
- ✅ `tests/fixtures/README.md` - Updated with all consolidated fixtures (Step 8 of consolidation plan)
- ✅ `tests/README.md` - Updated with new fixtures list (Step 8 of consolidation plan)
- ✅ `tests/hpo/README.md` - Partially updated (references new fixtures but may need enhancement)
- ⏳ `tests/workflows/README.md` - Needs update (doesn't mention new fixtures)
- ⏳ `tests/selection/README.md` - Needs update (minimal fixture documentation)
- ⏳ `tests/tracking/README.md` - Needs update (doesn't mention new fixtures)
- ⏳ `tests/benchmarking/README.md` - Needs update (minimal fixture documentation)
- ⏳ `tests/config/README.md` - Needs update (doesn't mention config_dir fixtures)
- ⏳ Other test module READMEs - Need audit for fixture usage

### Completed Steps
- ✅ Step 0: Documentation audit completed (consolidation plan Step 8)
- ✅ Step 1: Review test documentation standards and identify gaps
- ✅ Step 2: Audit existing test documentation for outdated content
- ✅ Step 3: Update high-priority test modules (hpo, workflows, selection, tracking)
- ✅ Step 4: Update medium-priority test modules (benchmarking, config)
- ✅ Step 5: Update lower-priority test modules (conversion, final_training, etc.)
- ✅ Step 6: Update cross-references and test index
- ✅ Step 7: Final review and consistency check

### Pending Steps
- ⏳ None - all steps completed!

## Preconditions

- Consolidation plan completed: `FINISHED-MASTER-consolidate-test-fixtures-and-helpers.plan.md`
- New fixtures exist and are documented in `tests/fixtures/README.md`
- Existing test documentation exists (created in `FINISHED-MASTER-test-documentation.plan.md`)
- Test structure is stable (no major refactoring in progress)

## New Fixtures and Helpers to Document

### Config Directory Fixtures (from Step 1)
- `config_dir`: Creates config directory with all commonly required YAML files
- `config_dir_minimal`: Creates minimal config directory with essential files only
- `config_dir_full`: Creates full config directory with complete structure
- `create_config_dir_files()`: Helper function to programmatically create config files

### Config Helper Functions (from Step 5)
- `create_minimal_training_config()`: Creates minimal training config files
- `create_minimal_data_config()`: Creates minimal data.yaml config
- `create_minimal_experiment_config()`: Creates minimal experiment.yaml config
- `create_minimal_model_config()`: Creates minimal model config file

### Enhanced MLflow Fixtures (from Steps 3 & 4)
- `mock_mlflow_client`: Pytest fixture (converted from function)
- `mock_mlflow_setup`: Combined fixture for client and parent run
- `mock_hpo_trial_run`: HPO trial run fixture
- `mock_benchmark_run`: Benchmark run fixture
- `mock_refit_run`: Refit run fixture
- `mock_final_training_run`: Final training run fixture
- `create_mock_run()`: Helper function for custom mock runs
- `clean_mlflow_db`: NEW fixture to clean MLflow database between tests

### Removed/Deprecated Fixtures
- Local `tmp_config_dir` fixtures (replaced by `config_dir` from `fixtures.config_dirs`)
- Local `hpo_config_smoke`/`hpo_config_minimal` (now only in `fixtures.configs`)
- Local `mock_mlflow_client`/`mock_mlflow_setup` (now only in `fixtures.mlflow`)
- Local `mock_mlflow_run`/`mock_benchmark_run`/etc. (replaced by shared fixtures)
- Local `_create_minimal_training_config()` helpers (replaced by `fixtures.config_helpers`)

## Test Documentation Update Checklist

Each test module README should be reviewed against this checklist:

### Content Accuracy

- [ ] **Test Fixtures Section**: Lists current fixtures (not deprecated ones)
- [ ] **Fixture Sources**: Correctly references `fixtures.config_dirs`, `fixtures.mlflow`, `fixtures.configs`, `fixtures.config_helpers`
- [ ] **Fixture Examples**: All examples use consolidated fixtures
- [ ] **Removed Fixtures**: No references to deprecated local fixtures
- [ ] **New Fixtures**: Documents `clean_mlflow_db` if module uses MLflow
- [ ] **Helper Functions**: Documents config helper functions if used

### Completeness

- [ ] **Fixture Imports**: Shows correct import patterns for consolidated fixtures
- [ ] **Usage Examples**: Includes examples using new fixtures
- [ ] **Migration Notes**: Documents any migration from old to new fixtures (if applicable)

### Standards Compliance

- [ ] **Cross-references**: Links to `tests/fixtures/README.md` are valid
- [ ] **Format**: Follows test documentation standards template
- [ ] **Examples**: All fixture usage examples are tested and working

## Test Documentation Audit Process

Before updating test documentation, perform this **repeatable audit** to identify what needs updating:

### 1. Scan Test Module for Fixture Usage

```bash
# Check which consolidated fixtures are used in test files
TEST_MODULE="tests/hpo"
grep -r "from fixtures\|import.*fixtures" "$TEST_MODULE" --include="*.py" | head -20

# Check for deprecated fixture names
grep -r "tmp_config_dir\|_create_minimal" "$TEST_MODULE" --include="*.py" | head -10

# Check for new fixture usage
grep -r "config_dir\|clean_mlflow_db\|create_minimal_training_config" "$TEST_MODULE" --include="*.py" | head -20
```

### 2. Verify Fixture Documentation in README

```bash
# Check if README mentions fixtures
grep -i "fixture\|mock_mlflow\|config_dir" "$TEST_MODULE/README.md" | head -20

# Check if README references deprecated fixtures
grep -i "tmp_config_dir\|local.*fixture" "$TEST_MODULE/README.md" | head -10

# Check if README mentions new fixtures
grep -i "clean_mlflow_db\|config_dir_minimal\|config_helpers" "$TEST_MODULE/README.md" | head -10
```

### 3. Check Cross-References

```bash
# Verify links to fixtures README
grep -o '\[.*\](.*fixtures.*README\.md)' "$TEST_MODULE/README.md"

# Check if links are valid
[ -f "tests/fixtures/README.md" ] && echo "Fixtures README exists"
```

### 4. Document Findings

Create an audit report per test module:
- **Fixtures used**: List of consolidated fixtures actually used in tests
- **Deprecated references**: Any mentions of old fixtures in README
- **Missing documentation**: New fixtures used but not documented
- **Broken examples**: Fixture usage examples that don't work
- **Cross-reference issues**: Invalid or missing links

## Steps

### Step 1: Review Test Documentation Standards and Identify Gaps

**Objective**: Understand current standards and identify what needs updating

**Tasks**:
1. Review `tests/fixtures/README.md` to understand all available consolidated fixtures
2. Review `FINISHED-MASTER-consolidate-test-fixtures-and-helpers.plan.md` to understand what changed
3. Compare existing test READMEs with current fixture availability
4. Identify common gaps:
   - Missing references to new fixtures
   - References to deprecated fixtures
   - Outdated fixture usage examples
   - Missing cross-references to `tests/fixtures/README.md`
5. Create gap analysis document

**Success criteria**:
- Gap analysis document created
- Common issues identified across test modules
- Update priorities established
- List of deprecated fixtures to remove from docs

**Files to review**:
- `tests/fixtures/README.md`
- `FINISHED-MASTER-consolidate-test-fixtures-and-helpers.plan.md`
- All test module READMEs

---

### Step 2: Audit Existing Test Documentation

**Objective**: Identify which test modules need updates and what needs updating

**Tasks**:
1. For each test module with README:
   - Perform test documentation audit (see "Test Documentation Audit Process")
   - Check which consolidated fixtures are actually used in test files
   - Verify README mentions correct fixtures
   - Check for references to deprecated fixtures
   - Verify cross-references to `tests/fixtures/README.md`
   - Compare with standards
2. Create audit report:
   - Test modules needing updates (priority order)
   - Specific issues per test module:
     - Missing new fixture documentation
     - Deprecated fixture references
     - Outdated examples
     - Broken cross-references
   - Estimated effort per test module

**Success criteria**:
- Complete audit report exists
- All test modules categorized (up-to-date, needs minor update, needs major update)
- Priority order established
- Specific issues documented per module

**Files to audit**:
- `tests/hpo/README.md`
- `tests/workflows/README.md`
- `tests/selection/README.md`
- `tests/tracking/README.md`
- `tests/benchmarking/README.md`
- `tests/config/README.md`
- `tests/conversion/README.md`
- `tests/final_training/README.md`
- Other test module READMEs

---

### Step 3: Update High-Priority Test Modules

**Objective**: Update test modules that heavily use consolidated fixtures or are frequently referenced

**Test modules to update**:
- `tests/hpo/README.md` - Uses `config_dir`, `hpo_config_*`, `mock_mlflow_*`, `clean_mlflow_db`
- `tests/workflows/README.md` - Uses `mock_mlflow_tracking`, may use other fixtures
- `tests/selection/README.md` - Uses `mock_mlflow_*` fixtures, `config_dir`
- `tests/tracking/README.md` - Uses MLflow fixtures, should document `clean_mlflow_db`

**Batch Process** (repeat for each test module):

1. **Review**: 
   - Read existing README completely
   - Perform test documentation audit
   - Check actual fixture usage in test files
   - Compare with `tests/fixtures/README.md`

2. **Update Test Fixtures Section**:
   - Remove references to deprecated fixtures (e.g., local `tmp_config_dir`, local `hpo_config_*`)
   - Add references to consolidated fixtures from `fixtures.config_dirs`, `fixtures.mlflow`, `fixtures.configs`
   - Document `clean_mlflow_db` if module uses MLflow
   - Update fixture import examples

3. **Update Usage Examples**:
   - Replace old fixture usage with consolidated fixtures
   - Add examples for new fixtures (e.g., `config_dir_minimal`, `mock_hpo_trial_run`)
   - Test all examples to ensure they work

4. **Update Cross-References**:
   - Ensure link to `tests/fixtures/README.md` is present and valid
   - Update "Related Test Modules" if needed

5. **Verify**:
   - All fixture references are accurate
   - No deprecated fixtures mentioned
   - Examples tested and working
   - Cross-references valid

**Success criteria**:
- All priority group 1 test modules updated
- All fixture references accurate and current
- All examples tested and working
- No deprecated fixture references
- Cross-references valid

**Files to modify**:
- `tests/hpo/README.md`
- `tests/workflows/README.md`
- `tests/selection/README.md`
- `tests/tracking/README.md`

---

### Step 4: Update Medium-Priority Test Modules

**Objective**: Update test modules that use some consolidated fixtures

**Test modules to update**:
- `tests/benchmarking/README.md` - Uses `mock_mlflow_tracking`, may use `config_dir`
- `tests/config/README.md` - Uses `config_dir` fixtures, should document `config_helpers`

**Process**: Same as Step 3

**Success criteria**:
- All priority group 2 test modules updated
- Fixture documentation accurate
- Standards compliance verified

**Files to modify**:
- `tests/benchmarking/README.md`
- `tests/config/README.md`

---

### Step 5: Update Lower-Priority Test Modules

**Objective**: Update remaining test modules that may use fixtures

**Test modules to update**:
- `tests/conversion/README.md` - May use MLflow fixtures
- `tests/final_training/README.md` - May use fixtures
- `tests/training/README.md` - May use fixtures
- `tests/infrastructure/README.md` - May use fixtures
- Other test module READMEs as needed

**Process**: Same as Step 3, but focus on:
- Adding references to `tests/fixtures/README.md` if missing
- Removing any deprecated fixture references
- Adding minimal fixture documentation if fixtures are used

**Success criteria**:
- All priority group 3 test modules reviewed and updated as needed
- At minimum, cross-references to fixtures README added
- No deprecated fixture references

**Files to modify**:
- `tests/conversion/README.md`
- `tests/final_training/README.md`
- `tests/training/README.md`
- `tests/infrastructure/README.md`
- Other test module READMEs as identified

---

### Step 6: Update Cross-References and Test Index

**Objective**: Ensure all cross-references and navigation are current

**Tasks**:
1. Update test index (`tests/docs/INDEX.md` if it exists):
   - Verify all links work
   - Update descriptions if test modules changed
   - Ensure fixture references are current

2. Update root `tests/README.md`:
   - Verify fixture list is complete and accurate
   - Update import examples to show consolidated fixtures
   - Ensure links to `tests/fixtures/README.md` are valid

3. Verify all "Related Test Modules" sections:
   - All links valid
   - Descriptions current
   - No circular or broken references

4. Update `tests/fixtures/README.md` if needed:
   - Ensure all consolidated fixtures are documented
   - Verify usage examples are current
   - Check cross-references to test modules

**Success criteria**:
- Test index is current and all links work
- Root test README fixture documentation is accurate
- All "Related Test Modules" sections are current
- No broken cross-references
- `tests/fixtures/README.md` is complete

**Files to modify**:
- `tests/README.md`
- `tests/docs/INDEX.md` (if exists)
- `tests/fixtures/README.md` (if needed)
- All test module READMEs (Related Test Modules sections)

---

### Step 7: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all updated test documentation

**Tasks**:
1. Review all updated test READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all fixture usage examples work
3. Check for consistency:
   - Terminology consistency (e.g., "from fixtures.config_dirs import config_dir")
   - Formatting consistency
   - Link accuracy
   - Standards compliance
4. Verify no deprecated fixture references remain:
   - Search for `tmp_config_dir` (should only appear as alias in hpo/conftest.py)
   - Search for local `hpo_config_*` definitions
   - Search for local `mock_mlflow_*` definitions
   - Search for `_create_minimal_*` helpers
5. Create update summary:
   - List all test modules updated
   - Note any remaining gaps or limitations
   - Document any test modules deferred
   - Include fixture usage example testing status

**Success criteria**:
- All updated test READMEs pass Definition of Done checklist
- All fixture usage examples are tested and work
- Cross-references are accurate
- Update summary exists
- No broken links or outdated examples
- No deprecated fixture references in documentation

**Files to review**:
- All updated test module READMEs
- `tests/README.md`
- `tests/fixtures/README.md`

## Per-Module Definition of Done (Update)

Each test module README update is considered complete when:

- [ ] All deprecated fixture references removed
- [ ] All new consolidated fixtures documented (if used in module)
- [ ] All fixture usage examples tested and work
- [ ] All cross-references are valid and current
- [ ] Test Fixtures section reflects current fixture usage
- [ ] Import examples show consolidated fixtures
- [ ] Link to `tests/fixtures/README.md` is present and valid
- [ ] No references to local fixture definitions that were consolidated
- [ ] Documentation follows current standards template
- [ ] Related Test Modules links are valid

## Test Module Update Priority

**High Priority** (Critical updates needed - heavily use consolidated fixtures):
1. `tests/hpo/README.md` - Uses `config_dir`, `hpo_config_*`, `mock_mlflow_*`, `clean_mlflow_db`
2. `tests/workflows/README.md` - Uses `mock_mlflow_tracking`, foundational for other tests
3. `tests/selection/README.md` - Uses `mock_mlflow_*` fixtures, `config_dir`
4. `tests/tracking/README.md` - Uses MLflow fixtures, should document `clean_mlflow_db`

**Medium Priority** (Important updates - use some fixtures):
5. `tests/benchmarking/README.md` - Uses `mock_mlflow_tracking`, may use `config_dir`
6. `tests/config/README.md` - Uses `config_dir` fixtures, should document `config_helpers`

**Lower Priority** (Nice to have updates - may use fixtures):
7. `tests/conversion/README.md` - May use MLflow fixtures
8. `tests/final_training/README.md` - May use fixtures
9. `tests/training/README.md` - May use fixtures
10. `tests/infrastructure/README.md` - May use fixtures
11. Other test module READMEs as identified

## Success Criteria (Overall)

- ✅ All test module READMEs reflect consolidated fixtures
- ✅ All deprecated fixture references removed
- ✅ All new fixtures documented where used
- ✅ All fixture usage examples are tested and accurate
- ✅ All cross-references are valid and current
- ✅ Test documentation follows current standards
- ✅ Test Fixtures sections are accurate and complete
- ✅ Links to `tests/fixtures/README.md` are present and valid
- ✅ No broken examples or outdated fixture references

## Maintenance Guidelines

After update is complete:

1. **Ongoing maintenance**:
   - Update documentation when new fixtures are added
   - Review quarterly for accuracy
   - Test fixture usage examples when fixtures change
   - Keep cross-references current
   - Update when fixtures are deprecated

2. **Update triggers**:
   - New fixtures added to `tests/fixtures/`
   - Fixtures deprecated or removed
   - Fixture API changes
   - Test module starts using new fixtures
   - Consolidation of additional fixtures

3. **Documentation ownership**:
   - Test module maintainers responsible for their test docs
   - PR reviews should check test documentation updates when fixtures change
   - Use this update plan for periodic reviews

## Notes

- This plan focuses on **updating existing test documentation** to reflect fixture consolidation
- Primary goal is accuracy - ensure docs match actual fixture usage
- Focus on removing deprecated references and adding new fixture documentation
- Prioritize high-impact modules (hpo, workflows, selection, tracking)
- Test all fixture usage examples - they must work
- Cross-references to `tests/fixtures/README.md` are critical

## Related Plans

- `FINISHED-MASTER-consolidate-test-fixtures-and-helpers.plan.md` - Source of changes to document
- `FINISHED-MASTER-test-documentation.plan.md` - Original test documentation creation
- `TEMPLATE-test-documentation-update-plan.md` - Template used for this plan


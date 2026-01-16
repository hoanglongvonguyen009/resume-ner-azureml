# Master Plan: Technical Documentation for All Test Modules

## Goal

Create comprehensive technical documentation (README.md) for each test module in `tests/` to:
1. **Improve test understanding**: Clear documentation of what each test module covers, test structure, and execution patterns
2. **Enable test maintenance**: Document test fixtures, helpers, and common patterns for easier updates
3. **Support onboarding**: Help new developers understand test organization and how to run/write tests
4. **Document test coverage**: Clearly identify what is tested, what is not, and any limitations

## Status

**Last Updated**: 2026-01-20

**Current State**:
- ✅ `tests/README.md` exists (comprehensive testing guide)
- ✅ `tests/conftest.py` exists (global pytest configuration)
- ⏳ All test modules lack individual README documentation

### Completed Steps
- ✅ Step 0: Existing test infrastructure documented in `tests/README.md`
- ✅ Step 1: Define test documentation template and standards
- ✅ Step 2: Document test fixtures and shared utilities (fixtures, shared, test_data)
- ✅ Step 3: Document workflow tests (workflows)
- ✅ Step 4: Document feature-specific tests (hpo, benchmarking, selection, final_training, conversion)
- ✅ Step 5: Document infrastructure tests (tracking, config, infrastructure)
- ✅ Step 6: Document API tests (api)
- ✅ Step 7: Document training tests (training)
- ✅ Step 8: Document test scripts and utilities (scripts, docs)
- ✅ Step 9: Create test index and cross-references
- ✅ Step 10: Final review and consistency check

### Pending Steps
- ⏳ Step 2: Document test fixtures and shared utilities (fixtures, shared, test_data)
- ⏳ Step 3: Document workflow tests (workflows)
- ⏳ Step 4: Document feature-specific tests (hpo, benchmarking, selection, final_training, conversion)
- ⏳ Step 5: Document infrastructure tests (tracking, config, infrastructure)
- ⏳ Step 6: Document API tests (api)
- ⏳ Step 7: Document training tests (training)
- ⏳ Step 8: Document test scripts and utilities (scripts, docs)
- ⏳ Step 9: Create test index and cross-references
- ⏳ Step 10: Final review and consistency check

## Preconditions

- Test structure is stable (no major refactoring in progress)
- Test organization follows established patterns (unit, integration, e2e)
- Test fixtures and helpers are in place

## Documentation Template

Each test module README.md should follow the **minimum required skeleton** below; include optional sections only when applicable. Do not create empty headings for optional sections.

```markdown
# [Test Module Name] Tests

[One-sentence overview of what this test module covers]

## TL;DR / Quick Start

**[Required for complex test modules, recommended for all]**

[1-2 sentence summary + minimal test execution example]

```bash
# Run all tests in this module
uvx pytest tests/module/ -v

# Run specific test file
uvx pytest tests/module/test_specific.py -v

# Run specific test
uvx pytest tests/module/test_specific.py::test_function_name -v
```

## Overview

[1-2 paragraphs: what this test module covers, its role in the test suite. Use bullet points for clarity. Include non-goals if needed to set boundaries.]

## Test Structure

**[Required]**

List **key test files and folders only**, not every test function. Optionally note "where to add X" for common extension points.

- `test_file.py`: [What this test file covers]
- `subfolder/`: [Purpose of subfolder (unit, integration, e2e)]
- `conftest.py`: [Module-specific fixtures if applicable]

Avoid exhaustive test function dumps that will rot quickly.

## Test Categories

**[Required if module has multiple test types]**

- **Unit Tests** (`unit/`): [What unit tests cover - fast, isolated tests]
- **Integration Tests** (`integration/`): [What integration tests cover - tests with real components]
- **E2E Tests** (`e2e/`): [What E2E tests cover - full workflow tests]

## Running Tests

### Basic Execution

[Common test execution patterns]

```bash
# Run all tests in this module
uvx pytest tests/module/ -v

# Run with coverage
uvx pytest tests/module/ --cov=src.module --cov-report=html

# Run specific category
uvx pytest tests/module/unit/ -v
uvx pytest tests/module/integration/ -v
```

### Advanced Execution

[Complex scenarios, markers, environment variables]

```bash
# Run with specific markers
uvx pytest tests/module/ -m "slow" -v

# Run with environment variables
E2E_USE_REAL_TRAINING=true uvx pytest tests/module/ -v
```

## Test Fixtures and Helpers

**[Required if module uses fixtures or helpers]**

### Available Fixtures

[Document key fixtures used in this module]

- `fixture_name`: [Description of what it provides]
- `another_fixture`: [Description]

### Shared Helpers

[Document helper functions or utilities]

- `helper_function()`: [Description]

See [`../fixtures/README.md`](../fixtures/README.md) for shared fixtures.

## What Is Tested

**[Required]**

[Clear list of what functionality is covered by these tests]

- ✅ [Feature/component 1]
- ✅ [Feature/component 2]
- ✅ [Edge case 1]

## What Is Not Tested

**[Optional but recommended]**

[Explicitly document gaps, limitations, or known untested areas]

- ❌ [Feature not tested - reason]
- ⚠️ [Feature partially tested - limitations]

## Test Examples

**[Optional - include only if module has complex test patterns]**

### Example 1: [Test Scenario Name]

[Complete working test example with explanation]

```python
def test_example():
    # Setup
    fixture = test_fixture()
    
    # Execute
    result = function_under_test(fixture)
    
    # Assert
    assert result == expected
```

## Configuration

**[Optional - include only if tests require configuration]**

[Test configuration files, environment variables, setup requirements]

## Dependencies

**[Optional - include only if tests have special dependencies]**

[External services, data files, environment setup required]

## Troubleshooting

**[Optional - include only if module has known issues or setup complexity]**

[Common issues and solutions]

## Related Test Modules

**[Required]**

[Links to related test modules and their documentation]

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]

```

## Proposed Structure

### Directory Structure

Each test module should have a `README.md` file at its root level:

```text
tests/
├── README.md (already exists)
├── conftest.py (already exists)
├── fixtures/
│   └── README.md
├── shared/
│   └── README.md
├── workflows/
│   └── README.md
├── hpo/
│   └── README.md
├── benchmarking/
│   └── README.md
├── selection/
│   └── README.md
├── final_training/
│   └── README.md
├── conversion/
│   └── README.md
├── tracking/
│   └── README.md
├── config/
│   └── README.md
├── training/
│   └── README.md
├── api/
│   └── README.md
├── infrastructure/
│   └── README.md
├── scripts/
│   └── README.md
└── docs/
    └── README.md
```

### Documentation File Structure

#### For Simple Test Modules (fixtures, shared, test_data)

Simple test modules with focused responsibilities should have concise documentation:

```markdown
# [Module Name] Tests

[One-sentence overview]

## TL;DR / Quick Start

[1-2 sentence summary + minimal test execution example]

## Overview

[1-2 paragraphs: purpose, role. Use bullet points for clarity.]

## Test Structure

- `file.py`: [Main purpose]
- `subfolder/`: [Purpose of folder]

## Running Tests

```bash
uvx pytest tests/module/ -v
```

## What Is Tested

- ✅ [Feature 1]
- ✅ [Feature 2]

## Related Test Modules

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]

```

#### For Complex Test Modules (workflows, hpo, benchmarking)

Complex test modules with multiple test types should have hierarchical documentation:

```markdown
# [Module Name] Tests

[One-sentence overview]

## TL;DR / Quick Start

**[Required for complex test modules]**

[1-2 sentence summary + minimal test execution example]

## Overview

[1-2 paragraphs: purpose, role, test architecture. Use bullet points for clarity.]

## Test Structure

This test module is organized into the following categories:

- `unit/`: [Purpose and responsibility]
- `integration/`: [Purpose and responsibility]
- `e2e/`: [Purpose and responsibility]

## Test Categories

- **Unit Tests** (`unit/`): [What unit tests cover]
- **Integration Tests** (`integration/`): [What integration tests cover]
- **E2E Tests** (`e2e/`): [What E2E tests cover]

## Running Tests

### Basic Execution

[Common patterns]

### Advanced Execution

[Complex scenarios]

## Test Fixtures and Helpers

[Document fixtures and helpers]

## What Is Tested

[Comprehensive list]

## What Is Not Tested

[Gaps and limitations]

## Configuration

[Test configuration if applicable]

## Related Test Modules

[Links to related test modules]
```

### Test Index Structure

Create `tests/docs/INDEX.md` with the following structure:

```markdown
# Test Documentation Index

## Test Infrastructure

### [`tests/fixtures/`](../fixtures/README.md)
Shared test fixtures and helpers.

### [`tests/shared/`](../shared/README.md)
Shared test utilities and common patterns.

### [`tests/test_data/`](../test_data/README.md)
Test data fixtures and datasets.

## Workflow Tests

### [`tests/workflows/`](../workflows/README.md)
End-to-end workflow tests for complete notebook workflows.

## Feature-Specific Tests

### [`tests/hpo/`](../hpo/README.md)
Hyperparameter optimization tests.

### [`tests/benchmarking/`](../benchmarking/README.md)
Benchmarking tests.

### [`tests/selection/`](../selection/README.md)
Model selection tests.

### [`tests/final_training/`](../final_training/README.md)
Final training tests.

### [`tests/conversion/`](../conversion/README.md)
Model conversion tests.

## Infrastructure Tests

### [`tests/tracking/`](../tracking/README.md)
MLflow tracking tests.

### [`tests/config/`](../config/README.md)
Configuration loading tests.

### [`tests/infrastructure/`](../infrastructure/README.md)
Infrastructure component tests.

## Component Tests

### [`tests/training/`](../training/README.md)
Training component tests.

### [`tests/api/`](../api/README.md)
API and inference tests.

## Test Utilities

### [`tests/scripts/`](../scripts/README.md)
Test scripts and manual verification tools.

### [`tests/docs/`](../docs/README.md)
Test coverage analysis and documentation.
```

### Cross-Reference Structure

Each test module README should include a "Related Test Modules" section with links:

```markdown
## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../fixtures/README.md`](../fixtures/README.md) - Shared fixtures used by these tests
  - [`../shared/README.md`](../shared/README.md) - Shared utilities

- **Related test modules** (similar functionality):
  - [`../related_module/README.md`](../related_module/README.md) - Alternative approach for similar use case

- **Downstream consumers** (test modules that use this):
  - [`../workflows/README.md`](../workflows/README.md) - Workflow tests use these fixtures
```

## Test Documentation Intake Process

Before writing a test module README, perform this **repeatable intake** to prevent guessing:

### 1. Scan Test Files

```bash
# List all test files in module
find tests/module -name "test_*.py" | sort

# Count test functions
grep -r "^def test_\|^async def test_" tests/module/ | wc -l

# List test categories (unit, integration, e2e)
find tests/module -type d -name "unit\|integration\|e2e" | sort
```

### 2. Identify Test Patterns

```bash
# List fixtures used
grep -r "@pytest.fixture\|@pytest.mark.fixture" tests/module/ | head -20

# List markers used
grep -r "@pytest.mark\." tests/module/ | cut -d: -f2 | sort -u

# List conftest files
find tests/module -name "conftest.py"
```

### 3. Map Dependencies

**Inbound** (what fixtures/helpers this uses):
```bash
grep -r "from fixtures\|from shared\|from test_data" tests/module/ | cut -d: -f1 | sort -u
```

**Outbound** (what source modules this tests):
```bash
grep -r "^from src\.\|^import src\." tests/module/ | cut -d: -f2 | sort -u
```

### 4. Document Findings

Create a brief intake note:
- Test files: [list]
- Test categories: [unit, integration, e2e]
- Fixtures used: [list]
- Source modules tested: [list]
- Test coverage: [what is tested]

This intake makes "What Is Tested" and "Test Fixtures and Helpers" sections real and accurate.

## Per-Module Definition of Done

Each test module README is considered complete when:

- [ ] Has minimum required sections (Title, TL;DR/Quick Start, Overview, Test Structure, Running Tests, What Is Tested, Related Test Modules)
- [ ] Contains at least one working test execution example (copy/paste runnable)
- [ ] Has Test Categories section (if module has multiple test types)
- [ ] Has Test Fixtures and Helpers section (if module uses fixtures)
- [ ] Has What Is Tested section (clear list of coverage)
- [ ] Has What Is Not Tested section (if there are known gaps)
- [ ] Has Related Test Modules links (all links are valid)
- [ ] Test Structure lists only key test files and folders (not exhaustive function dumps)
- [ ] Overview is 1-2 paragraphs with bullet points (no fluff)
- [ ] All test execution examples have been verified (commands work)
- [ ] Cross-references are accurate and use relative paths

## Steps

### Step 1: Define Test Documentation Template and Standards

**Objective**: Establish test documentation standards and create a reusable template

**Tasks**:
1. Review existing `tests/README.md` as reference
2. Create test documentation template (see template above)
3. Define test documentation standards:
   - Minimum required sections (with TL;DR/Quick Start and What Is Tested)
   - Test execution example format and verification requirements
   - Cross-reference conventions
   - When to include vs. omit sections (no empty headings)
4. Document intake process (see "Test Documentation Intake Process" above)
5. Document per-module Definition of Done (see above)
6. Create `docs/TEMPLATE-test_documentation_standards.md` with all standards

**Success criteria**:
- Test documentation template created and documented
- Standards document exists in `docs/TEMPLATE-test_documentation_standards.md` with intake process
- Per-module Definition of Done documented
- Template validated against existing `tests/README.md`

---

### Step 2: Document Test Fixtures and Shared Utilities

**Objective**: Document foundational test infrastructure that other tests depend on

**Modules to document**:
- `tests/fixtures/` - Shared test fixtures (datasets, MLflow mocking, configs, validators)
- `tests/shared/` - Shared test utilities
- `tests/test_data/` - Test data fixtures

**Batch Process** (repeat for each module):

1. **Intake**: Scan module structure
   - List fixture files and their purposes
   - Identify helper functions
   - Map inbound dependencies (what source modules they use)
   - Map outbound dependencies (what tests use these fixtures)

2. **Write README**: Create `tests/<module>/README.md`
   - Follow minimum required skeleton
   - Include TL;DR/Quick Start with working example
   - Document key fixtures and helpers
   - Add What Is Tested section
   - Add Related Test Modules links

3. **Add cross-links**: Update related test module READMEs
   - Add this module to their "Related Test Modules" sections

4. **Run example checks**: Test all test execution examples
   - Verify `uvx pytest` commands work
   - Fix any broken examples

5. **Verify Definition of Done**: Check against checklist

6. **Mark module done**: Update test index (Step 9)

**Module-Specific Content**:
- `tests/fixtures/README.md`: Dataset fixtures, MLflow mocking, config fixtures, validation helpers
- `tests/shared/README.md`: Shared utilities, common patterns
- `tests/test_data/README.md`: Test data structure, how to create/update test data

**Success criteria**:
- All READMEs exist with all required sections
- Test execution examples are tested and work
- Cross-references are accurate
- Definition of Done checklist completed for each module

---

### Step 3: Document Workflow Tests

**Objective**: Document end-to-end workflow tests

**Modules to document**:
- `tests/workflows/` - E2E workflow tests (notebook 01, notebook 02, full workflow)

**Tasks**:
1. Create `tests/workflows/README.md`
   - Document E2E test structure
   - Explain notebook workflow testing
   - Document test execution modes (mocked vs. real training)
   - Explain environment variables and test scopes
   - Document what workflows are tested

**Success criteria**:
- Workflow README exists with all required sections
- Test execution examples work
- Workflow coverage is clearly documented

---

### Step 4: Document Feature-Specific Tests

**Objective**: Document feature-specific test modules

**Modules to document**:
- `tests/hpo/` - HPO tests (unit, integration, e2e)
- `tests/benchmarking/` - Benchmarking tests
- `tests/selection/` - Model selection tests
- `tests/final_training/` - Final training tests
- `tests/conversion/` - Model conversion tests

**Batch Process** (repeat for each module):

1. **Intake**: Scan test module
   - List test files and categories
   - Identify test patterns and fixtures
   - Map source modules being tested
   - Document test coverage

2. **Write README**: Create `tests/<module>/README.md`
   - Follow template for complex test modules
   - Document test categories (unit, integration, e2e)
   - Document what is tested
   - Document what is not tested (if applicable)
   - Add test execution examples

3. **Add cross-links**: Update related test module READMEs

4. **Run example checks**: Verify test execution examples

5. **Verify Definition of Done**: Check against checklist

**Module-Specific Content**:
- `tests/hpo/README.md`: HPO search space, trial execution, checkpoint resume, sweep setup
- `tests/benchmarking/README.md`: Benchmark workflow, orchestrator, edge cases
- `tests/selection/README.md`: Model selection logic, artifact acquisition, cache tests
- `tests/final_training/README.md`: Final training components, logging intervals
- `tests/conversion/README.md`: Model conversion workflows, config tests

**Success criteria**:
- All feature test READMEs exist
- Test categories are clearly documented
- Test coverage is clearly documented
- Test execution examples work

---

### Step 5: Document Infrastructure Tests

**Objective**: Document infrastructure test modules

**Modules to document**:
- `tests/tracking/` - MLflow tracking tests
- `tests/config/` - Configuration loading tests
- `tests/infrastructure/` - Infrastructure component tests

**Tasks**:
1. Create `tests/tracking/README.md`
   - Document MLflow tracking tests (naming, tags, artifact upload)
   - Document unit vs. integration tests
   - Document Azure ML artifact upload tests
   - Document test scripts

2. Create `tests/config/README.md`
   - Document config loading tests
   - Document YAML config tests
   - Document fingerprint tests

3. Create `tests/infrastructure/README.md`
   - Document infrastructure component tests
   - Document submodule tests

**Success criteria**:
- All infrastructure test READMEs exist
- Test structure is clearly documented
- Test coverage is clearly documented

---

### Step 6: Document API Tests

**Objective**: Document API and inference tests

**Modules to document**:
- `tests/api/` - API tests (unit, integration)

**Tasks**:
1. Create `tests/api/README.md`
   - Document API test structure
   - Document inference tests
   - Document performance tests
   - Document test execution patterns

**Success criteria**:
- API test README exists
- Test categories are clearly documented
- Test execution examples work

---

### Step 7: Document Training Tests

**Objective**: Document training component tests

**Modules to document**:
- `tests/training/` - Training component tests

**Tasks**:
1. Create `tests/training/README.md`
   - Document training component tests
   - Document trainer, evaluator, data combiner tests
   - Document checkpoint loader tests
   - Document CV utils tests

**Success criteria**:
- Training test README exists
- Test coverage is clearly documented

---

### Step 8: Document Test Scripts and Utilities

**Objective**: Document test scripts and documentation utilities

**Modules to document**:
- `tests/scripts/` - Test scripts and manual verification tools
- `tests/docs/` - Test coverage analysis and documentation

**Tasks**:
1. Create `tests/scripts/README.md`
   - Document test scripts purpose
   - Document manual verification tools
   - Document how to use scripts

2. Create `tests/docs/README.md`
   - Document coverage analysis tools
   - Document test documentation structure

**Success criteria**:
- Test scripts README exists
- Test docs README exists
- Script usage is clearly documented

---

### Step 9: Create Test Index and Cross-References

**Objective**: Create navigation and cross-reference system

**Tasks**:
1. Create `tests/docs/INDEX.md`
   - List all test modules with brief descriptions
   - Organize by category (infrastructure, workflows, features, etc.)
   - Include links to test module READMEs
2. Update root `tests/README.md` to link to test index
3. Add "Related Test Modules" sections to each test module README
4. Create test dependency diagram (optional, in tests/docs/)

**Success criteria**:
- Test index exists in `tests/docs/INDEX.md`
- Root `tests/README.md` links to test index
- All test module READMEs have "Related Test Modules" sections
- Cross-references are accurate and helpful

---

### Step 10: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all test documentation

**Tasks**:
1. Review all READMEs against Definition of Done checklist:
   - Minimum required sections present
   - TL;DR/Quick Start included (required for complex, recommended for all)
   - Overview is 1-2 paragraphs (no fluff)
   - Test Structure lists only key items (not exhaustive)
   - At least one working test execution example
   - What Is Tested section present
   - Related Test Modules links present and valid

2. **Enforce example testing**:
   - For each test module, verify test execution examples are:
     - Copy/paste runnable (test manually), OR
     - Verified `uvx pytest` commands work
   - Document any examples that cannot be tested (with reason)
   - Fix or remove broken examples

3. Check for consistency:
   - Terminology consistency
   - Formatting consistency
   - Link accuracy (all relative paths work)
   - Test execution pattern consistency

4. Create test documentation summary:
   - List all documented test modules
   - Note any gaps or limitations
   - Document maintenance guidelines
   - Include example testing status

**Success criteria**:
- All READMEs pass Definition of Done checklist
- All test execution examples are tested and work (or documented why not)
- Cross-references are accurate
- Test documentation summary exists
- No broken links or outdated examples

## Success Criteria (Overall)

- ✅ All major test modules have README.md documentation
- ✅ Documentation follows standardized template
- ✅ Test execution examples are tested and accurate
- ✅ Cross-references between test modules are established
- ✅ Test index exists for navigation
- ✅ Documentation is consistent in style and format
- ✅ Test coverage is clearly documented
- ✅ Test fixtures and helpers are documented
- ✅ What is tested vs. not tested is clearly identified

## Test Module Priority

**High Priority** (Core test infrastructure, frequently used):
1. `fixtures/` - Foundation for other tests
2. `shared/` - Shared utilities (foundational, used across tests)
3. `workflows/` - E2E workflow tests (critical for validation)
4. `hpo/` - HPO tests (core functionality)
5. `tracking/` - MLflow tracking tests (critical infrastructure)

**Medium Priority** (Important but less foundational):
6. `benchmarking/` - Benchmarking tests
7. `selection/` - Model selection tests
8. `config/` - Configuration tests
9. `training/` - Training component tests
10. `api/` - API tests

**Lower Priority** (Supporting test modules):
11. `final_training/` - Final training tests
12. `conversion/` - Conversion tests
13. `infrastructure/` - Infrastructure component tests
14. `scripts/` - Test scripts
15. `docs/` - Test documentation utilities
16. `test_data/` - Test data (if not covered in fixtures)

## Maintenance Guidelines

After initial documentation is complete:

1. **Update documentation when**:
   - Test structure changes significantly
   - New test categories are added
   - Test fixtures change
   - Test coverage changes significantly
   - New test patterns emerge

2. **Review documentation**:
   - Quarterly review for accuracy
   - Update examples when test execution patterns change
   - Keep cross-references current

3. **Documentation ownership**:
   - Test module maintainers responsible for their test docs
   - PR reviews should check test documentation updates

## Notes

- Follow reuse-first principles: reference existing test docs rather than duplicating
- Keep documentation concise but complete
- Focus on "how to run tests" and "what is tested" rather than "how tests work internally"
- Include practical test execution examples over theoretical explanations
- Document test coverage clearly (what is tested, what is not)
- Document test fixtures and helpers for easier maintenance


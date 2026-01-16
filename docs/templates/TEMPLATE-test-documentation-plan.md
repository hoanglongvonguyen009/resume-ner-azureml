# Master Plan: Technical Documentation for All Test Modules

## Goal

Create comprehensive technical documentation (README.md) for each test module in `[TARGET_DIRECTORY]/` to:
1. **Improve test understanding**: Clear documentation of what each test module covers, test structure, and execution patterns
2. **Enable test maintenance**: Document test fixtures, helpers, and common patterns for easier updates
3. **Support onboarding**: Help new developers understand test organization and how to run/write tests
4. **Document test coverage**: Clearly identify what is tested, what is not, and any limitations

## Status

**Last Updated**: [YYYY-MM-DD]

**Current State**:
- ✅ `[TARGET_DIRECTORY]/README.md` exists (comprehensive testing guide)
- ✅ `[TARGET_DIRECTORY]/conftest.py` exists (global test configuration)
- ⏳ All test modules lack individual README documentation

### Completed Steps
- ✅ Step 0: Existing test infrastructure documented

### Pending Steps
- ⏳ Step 1: Define test documentation template and standards
- ⏳ Step 2: Document test fixtures and shared utilities ([list modules])
- ⏳ Step 3: Document [test_category_1] tests ([list modules])
- ⏳ Step 4: Document [test_category_2] tests ([list modules])
- ⏳ Step 5: Document [test_category_3] tests ([list modules])
- ⏳ Step 6: Create test index and cross-references
- ⏳ Step 7: Final review and consistency check

## Preconditions

- Test structure is stable (no major refactoring in progress)
- Test organization follows established patterns ([test_patterns])
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
[TEST_COMMAND] [TARGET_DIRECTORY]/module/ -v

# Run specific test file
[TEST_COMMAND] [TARGET_DIRECTORY]/module/test_specific.py -v

# Run specific test
[TEST_COMMAND] [TARGET_DIRECTORY]/module/test_specific.py::test_function_name -v
```

## Overview

[1-2 paragraphs: what this test module covers, its role in the test suite. Use bullet points for clarity. Include non-goals if needed to set boundaries.]

## Test Structure

**[Required]**

List **key test files and folders only**, not every test function. Optionally note "where to add X" for common extension points.

- `test_file.py`: [What this test file covers]
- `subfolder/`: [Purpose of subfolder ([test_categories])]
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
[TEST_COMMAND] [TARGET_DIRECTORY]/module/ -v

# Run with coverage
[TEST_COMMAND] [TARGET_DIRECTORY]/module/ --cov=[source_module] --cov-report=html

# Run specific category
[TEST_COMMAND] [TARGET_DIRECTORY]/module/unit/ -v
[TEST_COMMAND] [TARGET_DIRECTORY]/module/integration/ -v
```

### Advanced Execution

[Complex scenarios, markers, environment variables]

```bash
# Run with specific markers
[TEST_COMMAND] [TARGET_DIRECTORY]/module/ -m "[marker]" -v

# Run with environment variables
[ENV_VAR]=[value] [TEST_COMMAND] [TARGET_DIRECTORY]/module/ -v
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

```[LANGUAGE]
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
[TARGET_DIRECTORY]/
├── README.md (already exists)
├── conftest.py (already exists)
├── [test_module1]/
│   └── README.md
├── [test_module2]/
│   ├── README.md
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── ...
```

### Documentation File Structure

#### For Simple Test Modules

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
[TEST_COMMAND] [TARGET_DIRECTORY]/module/ -v
```

## What Is Tested

- ✅ [Feature 1]
- ✅ [Feature 2]

## Related Test Modules

- [`../related_module/README.md`](../related_module/README.md) - [Brief description]
```

#### For Complex Test Modules

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

Create `[TARGET_DIRECTORY]/[index_location]/INDEX.md` with the following structure:

```markdown
# Test Documentation Index

## Test Infrastructure

### [`[TARGET_DIRECTORY]/[module1]/`](../[module1]/README.md)
[Brief description]

### [`[TARGET_DIRECTORY]/[module2]/`](../[module2]/README.md)
[Brief description]

## [Category 1] Tests

### [`[TARGET_DIRECTORY]/[module3]/`](../[module3]/README.md)
[Brief description]

## [Category 2] Tests

[Continue pattern...]
```

### Cross-Reference Structure

Each test module README should include a "Related Test Modules" section with links:

```markdown
## Related Test Modules

- **Upstream dependencies** (test modules this depends on):
  - [`../[dependency_module]/README.md`](../[dependency_module]/README.md) - [Description]

- **Related test modules** (similar functionality):
  - [`../[related_module]/README.md`](../[related_module]/README.md) - [Description]

- **Downstream consumers** (test modules that use this):
  - [`../[consumer_module]/README.md`](../[consumer_module]/README.md) - [Description]
```

## Test Documentation Intake Process

Before writing a test module README, perform this **repeatable intake** to prevent guessing:

### 1. Scan Test Files

```bash
# List all test files in module
find [TARGET_DIRECTORY]/module -name "test_*.py" | sort

# Count test functions
grep -r "^def test_\|^async def test_" [TARGET_DIRECTORY]/module/ | wc -l

# List test categories
find [TARGET_DIRECTORY]/module -type d -name "[test_category_pattern]" | sort
```

### 2. Identify Test Patterns

```bash
# List fixtures used
grep -r "@pytest.fixture\|@[TEST_FRAMEWORK].fixture" [TARGET_DIRECTORY]/module/ | head -20

# List markers used
grep -r "@[TEST_FRAMEWORK].mark\." [TARGET_DIRECTORY]/module/ | cut -d: -f2 | sort -u

# List conftest files
find [TARGET_DIRECTORY]/module -name "conftest.py"
```

### 3. Map Dependencies

**Inbound** (what fixtures/helpers this uses):
```bash
grep -r "from fixtures\|from shared\|from test_data" [TARGET_DIRECTORY]/module/ | cut -d: -f1 | sort -u
```

**Outbound** (what source modules this tests):
```bash
grep -r "^from [SOURCE_DIR]\.\|^import [SOURCE_DIR]\." [TARGET_DIRECTORY]/module/ | cut -d: -f2 | sort -u
```

### 4. Document Findings

Create a brief intake note:
- Test files: [list]
- Test categories: [list]
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
1. Review existing `[TARGET_DIRECTORY]/README.md` as reference
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
- Standards document exists with intake process
- Per-module Definition of Done documented
- Template validated against existing test README

---

### Step 2: Document Test Fixtures and Shared Utilities

**Objective**: Document foundational test infrastructure that other tests depend on

**Modules to document**:
- `[TARGET_DIRECTORY]/[module1]/` - [Description]
- `[TARGET_DIRECTORY]/[module2]/` - [Description]

**Batch Process** (repeat for each module):

1. **Intake**: Scan module structure
   - List fixture files and their purposes
   - Identify helper functions
   - Map inbound dependencies (what source modules they use)
   - Map outbound dependencies (what tests use these fixtures)

2. **Write README**: Create `[TARGET_DIRECTORY]/<module>/README.md`
   - Follow minimum required skeleton
   - Include TL;DR/Quick Start with working example
   - Document key fixtures and helpers
   - Add What Is Tested section
   - Add Related Test Modules links

3. **Add cross-links**: Update related test module READMEs
   - Add this module to their "Related Test Modules" sections

4. **Run example checks**: Test all test execution examples
   - Verify test commands work
   - Fix any broken examples

5. **Verify Definition of Done**: Check against checklist

6. **Mark module done**: Update test index (Step N)

**Success criteria**:
- All READMEs exist with all required sections
- Test execution examples are tested and work
- Cross-references are accurate
- Definition of Done checklist completed for each module

---

### Step N: Create Test Index and Cross-References

**Objective**: Create navigation and cross-reference system

**Tasks**:
1. Create `[TARGET_DIRECTORY]/[index_location]/INDEX.md`
   - List all test modules with brief descriptions
   - Organize by category
   - Include links to test module READMEs
2. Update root `[TARGET_DIRECTORY]/README.md` to link to test index
3. Add "Related Test Modules" sections to each test module README
4. Create test dependency diagram (optional)

**Success criteria**:
- Test index exists
- Root test README links to test index
- All test module READMEs have "Related Test Modules" sections
- Cross-references are accurate and helpful

---

### Step N+1: Final Review and Consistency Check

**Objective**: Ensure consistency and completeness across all test documentation

**Tasks**:
1. Review all READMEs against Definition of Done checklist
2. **Enforce example testing**: Verify all test execution examples work
3. Check for consistency: terminology, formatting, links
4. Create test documentation summary

**Success criteria**:
- All READMEs pass Definition of Done checklist
- All test execution examples are tested and work
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
1. `[module1]/` - [Reason]
2. `[module2]/` - [Reason]
3. `[module3]/` - [Reason]

**Medium Priority** (Important but less foundational):
4. `[module4]/` - [Reason]
5. `[module5]/` - [Reason]

**Lower Priority** (Supporting test modules):
6. `[module6]/` - [Reason]
7. `[module7]/` - [Reason]

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

## Template Usage Instructions

When using this template:

1. **Replace placeholders**:
   - `[TARGET_DIRECTORY]` - Directory containing test modules (e.g., "tests")
   - `[TEST_COMMAND]` - Test execution command (e.g., "uvx pytest", "npm test")
   - `[LANGUAGE]` - Programming language (e.g., "python", "javascript")
   - `[test_categories]` - Test category names (e.g., "unit, integration, e2e")
   - `[test_patterns]` - Test organization patterns (e.g., "unit, integration, e2e")
   - `[test_category_pattern]` - Pattern for finding test categories (e.g., "unit\|integration\|e2e")
   - `[TEST_FRAMEWORK]` - Test framework name (e.g., "pytest", "jest")
   - `[SOURCE_DIR]` - Source code directory (e.g., "src")
   - `[index_location]` - Where to create index (e.g., "docs")
   - `[module1]`, `[module2]`, etc. - Actual test module names
   - `[test_category_1]`, etc. - Test category names
   - `[ENV_VAR]` - Environment variable name
   - `[value]` - Environment variable value
   - `[marker]` - Test marker name

2. **Customize steps**: Add or remove steps based on your test structure

3. **Update intake commands**: Adjust grep/find commands to match your test structure

4. **Set priorities**: Define your own priority groups based on test dependencies and usage


# Code Quality Verification Plan: [TARGET_DIRECTORY]/ Module Compliance

## Goal

Systematically verify and fix all [LANGUAGE] modules in `[TARGET_DIRECTORY]/` against [NUMBER] rule sets:
1. **File Metadata** (`@[rule-file-1].mdc`) - [Description of rule set 1]
2. **Code Quality** (`@[rule-file-2].mdc`) - [Description of rule set 2]
3. **Type Safety** (`@[rule-file-3].mdc`) - [Description of rule set 3]
[Add more rule sets as needed]

Each verification step includes immediate remediation of identified issues.

## Status

**Last Updated**: [YYYY-MM-DD]

### Completed Steps
- ⏳ None yet

### Pending Steps
- ⏳ Step 1: Inventory and categorize all modules
- ⏳ Step 2: Verify and fix `[TARGET_DIRECTORY]/[module1]/` module ([rule categories])
- ⏳ Step 3: Verify and fix `[TARGET_DIRECTORY]/[module2]/` module ([rule categories])
[Continue for all modules...]
- ⏳ Step N: Generate overall compliance report

## Preconditions

- Access to `[TARGET_DIRECTORY]/` directory
- Ability to run `[TYPE_CHECKER_COMMAND]` for type checking
- Understanding of module structure and responsibilities
- [Add any project-specific preconditions]

## Check Order

Follow this module-by-module approach:

1. **Inventory Phase** - Understand what we're checking
2. **Module-by-Module Verification & Fix** - For each module:
   - Verify [Rule category 1] compliance (fastest, surface-level) → Fix issues
   - Verify [Rule category 2] compliance (naming, structure, patterns) → Fix issues
   - Verify [Rule category 3] compliance (type hints, type checker) → Fix issues
   - Run tests and type checker to confirm fixes
3. **Report** - Generate final compliance report

## Verification Steps

### Step 1: Inventory and Categorize All Modules

**Purpose**: Understand the scope and categorize files by type (script, utility, test, etc.)

**Actions**:
1. List all [LANGUAGE] files in `[TARGET_DIRECTORY]/` recursively
2. Categorize each file:
   - **Entry-point scripts**: Files with `if __name__ == "__main__"` or CLI entry points
   - **Workflow files**: Files in `**/workflows/` directories
   - **Test modules**: Files in `tests/` (if any in [TARGET_DIRECTORY])
   - **Shared utilities**: Files in `common/` or files with "utils" in name
   - **Core logic**: Business logic, [domain-specific] modules
   - **Infrastructure**: Setup, tracking, config modules
   - **Small pure helpers**: Simple functions with no side effects

**Detection Criteria**:
```bash
# Find all [LANGUAGE] files
find [TARGET_DIRECTORY]/ -name "*.[EXTENSION]" -type f | sort

# Find entry points
grep -r "if __name__ == \"__main__\"" [TARGET_DIRECTORY]/ --include="*.[EXTENSION]" -l

# Find workflow files
find [TARGET_DIRECTORY]/ -path "*/workflows/*.[EXTENSION]" -type f

# Find utility files
find [TARGET_DIRECTORY]/ -name "*utils*.[EXTENSION]" -o -name "*helper*.[EXTENSION]" | grep -v __pycache__

# Find CLI files
find [TARGET_DIRECTORY]/ -name "cli.[EXTENSION]" -o -name "*_cli.[EXTENSION]"
```

**Success Criteria**:
- Complete inventory of all [LANGUAGE] files in `[TARGET_DIRECTORY]/`
- Each file categorized by type
- Inventory saved to `docs/compliance-inventory.md` (or similar)

---

## Module Verification Template

Each module verification step (Steps 2-N) follows this pattern:

### For Module `[TARGET_DIRECTORY]/[module_name]/`

**Purpose**: Verify and fix compliance for all [LANGUAGE] files in `[TARGET_DIRECTORY]/[module_name]/` across all rule sets.

**Actions**:

1. **[Rule Category 1] Compliance** (for `[TARGET_DIRECTORY]/[module_name]/`)
   - [Specific checks for rule category 1]
   - [Verification steps]
   - Fix identified issues immediately
   - [Documentation requirements]

2. **[Rule Category 2] Compliance** (for `[TARGET_DIRECTORY]/[module_name]/`)
   - [Specific checks for rule category 2]
   - [Verification steps]
   - Fix identified issues immediately
   - [Documentation requirements]

3. **[Rule Category 3] Compliance** (for `[TARGET_DIRECTORY]/[module_name]/`)
   - [Specific checks for rule category 3]
   - [Verification steps]
   - Fix identified issues immediately
   - [Documentation requirements]

**Verification Commands** (replace `[module_name]` with actual module):
```bash
MODULE="[TARGET_DIRECTORY]/[module_name]"

# 1. [Rule Category 1] checks
[COMMANDS_FOR_RULE_CATEGORY_1]

# 2. [Rule Category 2] checks
[COMMANDS_FOR_RULE_CATEGORY_2]

# 3. [Rule Category 3] checks
[COMMANDS_FOR_RULE_CATEGORY_3]
```

**Success Criteria**:
- [Success criterion 1]
- [Success criterion 2]
- [Success criterion 3]
- [Add more as needed]

**Remediation Process**:
1. **Prioritize by severity**:
   - **Critical**: [Critical issue types] → Fix immediately
   - **High**: [High priority issue types] → Fix immediately
   - **Medium**: [Medium priority issue types] → Fix if straightforward
   - **Low**: [Low priority issue types] → Fix if time permits
2. **Fix incrementally**: Address issues as found, verify with tests and type checker
3. **Verify fixes**: Run `[TEST_COMMAND]` and `[TYPE_CHECKER_COMMAND] [TARGET_DIRECTORY]/[module_name]/` after fixes

**Documentation**: Record findings and fixes in module-specific section of compliance report.

---

### Step 2: Verify and Fix `[TARGET_DIRECTORY]/[module1]/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `[module1]`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and type checker to confirm.

**Module-specific notes**:
- [Note 1 about this module]
- [Note 2 about this module]
- [Note 3 about this module]

---

### Step 3: Verify and Fix `[TARGET_DIRECTORY]/[module2]/` Module

Follow the **Module Verification Template** above, replacing `[module_name]` with `[module2]`.

**Remediation**: Fix all identified issues immediately after verification, then run tests and type checker to confirm.

**Module-specific notes**:
- [Note 1 about this module]
- [Note 2 about this module]

---

[Continue for all modules...]

---

### Step N: Generate Overall Compliance Report

**Purpose**: Document findings, create actionable remediation list

**Actions**:
1. Compile findings from Steps 2-N (all module verifications) into structured report
2. Categorize issues by:
   - **Severity**: Critical, High, Medium, Low
   - **Category**: [Category 1], [Category 2], [Category 3]
   - **Module**: Group by module/package
3. Create remediation checklist with file paths and line numbers
4. Generate summary statistics:
   - Total files checked (across all modules)
   - Files with issues (per module and overall)
   - Issues by category (per module and overall)
   - Compliance percentage (per module and overall)

**Report Format**:
```markdown
# Code Quality Compliance Report

**Generated**: YYYY-MM-DD
**Scope**: All [LANGUAGE] files in `[TARGET_DIRECTORY]/`

## Summary Statistics
- Total files: X
- Files checked: X
- Files with issues: X
- Compliance rate: X%

## Issues by Category

### [Rule Category 1]
- [Issue type 1]: X files
- [Issue type 2]: X files
- [Issue type 3]: X files

### [Rule Category 2]
- [Issue type 1]: X issues
- [Issue type 2]: X issues
- [Issue type 3]: X instances

### [Rule Category 3]
- [Issue type 1]: X functions
- [Issue type 2]: X errors
- [Issue type 3]: X instances

## Detailed Findings

[Per-module breakdown with file paths and line numbers]
```

**Success Criteria**:
- Comprehensive report generated
- All findings documented with file paths
- Issues prioritized by severity
- Remediation checklist created

## Success Criteria (Overall)

- ✅ Complete inventory of all `[TARGET_DIRECTORY]/` modules
- ✅ All entry-point scripts have proper [rule category 1 compliance]
- ✅ All workflow files have proper [rule category 1 compliance]
- ✅ All code follows [rule category 2] conventions
- ✅ Functions are well-structured ([rule category 2] requirements)
- ✅ [Rule category 2] requirements met
- ✅ Proper error handling ([rule category 2] requirements)
- ✅ All functions have type hints ([rule category 3] requirements)
- ✅ Type checker passes: `[TYPE_CHECKER_COMMAND] [TARGET_DIRECTORY]/`
- ✅ [Rule category 3] requirements met
- ✅ Comprehensive compliance report generated
- ✅ All critical/high issues remediated

## Detailed Detection Criteria and Remediation Guidance

### [Rule Category 1] Compliance

**Detection Criteria**:

[Detailed detection criteria for rule category 1]

**Remediation Guidance**:
- **[Issue type 1]**: [How to fix]
- **[Issue type 2]**: [How to fix]
- **[Issue type 3]**: [How to fix]

---

### [Rule Category 2] Compliance

**Detection Criteria**:

#### [Sub-category 1]
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

#### [Sub-category 2]
- [Criterion 1]
- [Criterion 2]

#### [Sub-category 3]
- [Criterion 1]
- [Criterion 2]

**Remediation Guidance**:
- **[Issue type 1]**: [How to fix]
- **[Issue type 2]**: [How to fix]
- **[Issue type 3]**: [How to fix]

---

### [Rule Category 3] Compliance

**Detection Criteria**:

#### [Sub-category 1]
- [Criterion 1]
- [Criterion 2]
- [Criterion 3]

#### [Sub-category 2]
- [Criterion 1]
- [Criterion 2]

#### [Sub-category 3]
- [Criterion 1]
- [Criterion 2]

**Remediation Guidance**:
- **[Issue type 1]**: [How to fix]
- **[Issue type 2]**: [How to fix]
- **[Issue type 3]**: [How to fix]

---

## Tools and Commands Reference

### Quick Verification Commands

```bash
# 1. Inventory
find [TARGET_DIRECTORY]/ -name "*.[EXTENSION]" -type f | wc -l

# 2. [Rule Category 1] check
[QUICK_CHECK_COMMAND_1]

# 3. [Rule Category 3] check
[TYPE_CHECKER_COMMAND] [TARGET_DIRECTORY]/

# 4. Find entry points
grep -r "if __name__ == \"__main__\"" [TARGET_DIRECTORY]/ --include="*.[EXTENSION]" -l

# 5. [Rule Category 2] check
[QUICK_CHECK_COMMAND_2]

# 6. [Rule Category 3] check
[QUICK_CHECK_COMMAND_3]
```

## Notes

- **Module-by-module approach**: Each module is fully verified and fixed (all rule categories) before moving to the next.
- **Immediate remediation**: Fix issues as they are found during verification, not deferred to a separate step.
- **Test after changes**: Always run tests and type checker after making changes to a module.
- **Document decisions**: If skipping [rule category] for a file, document why in the compliance report.
- **Reuse-first**: When fixing issues, check for existing patterns/utilities to reuse.
- **Module independence**: Each module verification can be done independently, allowing parallel work if needed.
- **Verification and fixing together**: Each verification step includes immediate remediation, ensuring working state is maintained throughout.

## Template Usage Instructions

When using this template:

1. **Replace placeholders**:
   - `[TARGET_DIRECTORY]` - Directory containing modules to verify (e.g., "src", "tests", "lib")
   - `[LANGUAGE]` - Programming language (e.g., "Python", "TypeScript", "JavaScript")
   - `[EXTENSION]` - File extension (e.g., "py", "ts", "js")
   - `[NUMBER]` - Number of rule sets being checked
   - `[rule-file-1]`, `[rule-file-2]`, etc. - Names of rule files (e.g., "python-file-metadata", "python-code-quality")
   - `[rule categories]` - Comma-separated list of rule categories (e.g., "metadata, code quality, type safety")
   - `[TYPE_CHECKER_COMMAND]` - Type checker command (e.g., "uvx mypy", "tsc", "npx tsc")
   - `[TEST_COMMAND]` - Test execution command (e.g., "uvx pytest", "npm test")
   - `[module1]`, `[module2]`, etc. - Actual module names from your codebase
   - `[Rule Category 1]`, `[Rule Category 2]`, etc. - Names of your rule categories
   - `[Description of rule set X]` - Brief description of each rule set

2. **Customize rule sets**:
   - Add or remove rule categories based on your needs
   - Update detection criteria and remediation guidance for each rule set
   - Adjust verification commands to match your tooling

3. **List all modules**:
   - Replace `[module1]`, `[module2]`, etc. with actual module names
   - Add module-specific notes for each module
   - Adjust step numbers accordingly

4. **Update commands**:
   - Replace all command placeholders with actual commands
   - Adjust file patterns and grep patterns for your language
   - Update type checker and test commands

5. **Customize success criteria**:
   - Update success criteria to match your specific rule sets
   - Add or remove criteria as needed

6. **Add project-specific details**:
   - Add any project-specific preconditions
   - Include any custom verification steps
   - Add domain-specific notes

## Example: Python Code Quality Verification

For a Python project checking file metadata, code quality, and type safety:

- `[TARGET_DIRECTORY]` → `src`
- `[LANGUAGE]` → `Python`
- `[EXTENSION]` → `py`
- `[NUMBER]` → `3`
- `[rule-file-1]` → `python-file-metadata`
- `[rule-file-2]` → `python-code-quality`
- `[rule-file-3]` → `python-type-safety`
- `[TYPE_CHECKER_COMMAND]` → `uvx mypy`
- `[TEST_COMMAND]` → `uvx pytest`
- `[Rule Category 1]` → `File Metadata`
- `[Rule Category 2]` → `Code Quality`
- `[Rule Category 3]` → `Type Safety`

## Example: TypeScript Code Quality Verification

For a TypeScript project checking code quality, type safety, and linting:

- `[TARGET_DIRECTORY]` → `src`
- `[LANGUAGE]` → `TypeScript`
- `[EXTENSION]` → `ts`
- `[NUMBER]` → `3`
- `[rule-file-1]` → `typescript-code-quality`
- `[rule-file-2]` → `typescript-type-safety`
- `[rule-file-3]` → `typescript-linting`
- `[TYPE_CHECKER_COMMAND]` → `npx tsc --noEmit`
- `[TEST_COMMAND]` → `npm test`
- `[Rule Category 1]` → `Code Quality`
- `[Rule Category 2]` → `Type Safety`
- `[Rule Category 3]` → `Linting`

## Reference Implementation

This template was used to create:
- `docs/implementation_plans/verify-src-compliance.plan.md` - Python code quality verification for `src/` modules

The reference implementation demonstrates:
- How to structure module-by-module verification steps
- How to define detection criteria and remediation guidance
- How to create module-specific notes
- How to generate comprehensive compliance reports


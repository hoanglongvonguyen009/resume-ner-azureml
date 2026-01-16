# Documentation Plan Templates

This directory contains reusable templates for creating implementation plans for documentation efforts.

## Available Templates

### 1. `TEMPLATE-module-documentation-plan.md`

Template for creating a master plan to document source code modules (e.g., modules in `src/`).

**Use when**: You need to document source code modules, libraries, or components.

**Key placeholders to replace**:
- `[MODULE_TYPE]` - Type of modules (e.g., "Source", "Infrastructure")
- `[TARGET_DIRECTORY]` - Directory containing modules (e.g., "src", "lib")
- `[LANGUAGE]` - Programming language (e.g., "python", "javascript")
- `[TEST_COMMAND]` - Test execution command (e.g., "uvx pytest")
- `[module1]`, `[module2]` - Actual module names

**Example usage**: See `docs/implementation_plans/MASTER-technical-documentation-for-modules.plan.md`

### 2. `TEMPLATE-test-documentation-plan.md`

Template for creating a master plan to document test modules (e.g., modules in `tests/`).

**Use when**: You need to document test suites, test modules, or test infrastructure.

**Key placeholders to replace**:
- `[TARGET_DIRECTORY]` - Directory containing test modules (e.g., "tests")
- `[TEST_COMMAND]` - Test execution command (e.g., "uvx pytest")
- `[TEST_FRAMEWORK]` - Test framework (e.g., "pytest", "jest")
- `[test_categories]` - Test category names (e.g., "unit, integration, e2e")
- `[module1]`, `[module2]` - Actual test module names

**Example usage**: See `docs/implementation_plans/MASTER-test-documentation.plan.md`

### 3. `TEMPLATE-documentation_standards.md`

Standards and template for creating individual module README documentation.

**Use when**: You need to write or update a module README following consistent standards.

**Key features**:
- Minimum required sections for all modules
- Templates for simple vs. complex modules
- Code example format requirements
- Intake process for analyzing modules
- Definition of Done checklist
- API reference policy (max 10 items)

**Example usage**: Reference this when writing any `src/<module>/README.md`

### 4. `TEMPLATE-test_documentation_standards.md`

Standards and template for creating individual test module README documentation.

**Use when**: You need to write or update a test module README following consistent standards.

**Key features**:
- Minimum required sections for all test modules
- Templates for simple vs. complex test modules
- Test execution example requirements
- Test coverage documentation guidelines
- Intake process for analyzing test modules
- Definition of Done checklist

**Example usage**: Reference this when writing any `tests/<module>/README.md`

### 5. `TEMPLATE-module-documentation-update-plan.md`

Template for creating a master plan to update and maintain existing module documentation.

**Use when**: You have existing documentation that needs updating, maintenance, or standardization.

**Key features**:
- Documentation audit process
- Update checklist for existing READMEs
- Process for identifying outdated content
- Steps for updating modules in priority order
- Cross-reference maintenance
- Standards compliance verification

**Example usage**: Use this when existing module READMEs need updates due to code changes, standards updates, or maintenance

### 6. `TEMPLATE-test-documentation-update-plan.md`

Template for creating a master plan to update and maintain existing test module documentation.

**Use when**: You have existing test documentation that needs updating, maintenance, or standardization.

**Key features**:
- Test documentation audit process
- Update checklist for existing test READMEs
- Process for identifying outdated test content
- Steps for updating test modules in priority order
- Test execution example verification
- Test coverage documentation updates
- Cross-reference maintenance
- Standards compliance verification

**Example usage**: Use this when existing test module READMEs need updates due to test structure changes, framework updates, or maintenance

## How to Use These Templates

### Step 1: Copy the Template

```bash
# For module documentation
cp docs/templates/TEMPLATE-module-documentation-plan.md \
   docs/implementation_plans/MASTER-[your-project]-documentation.plan.md

# For test documentation
cp docs/templates/TEMPLATE-test-documentation-plan.md \
   docs/implementation_plans/MASTER-[your-project]-test-documentation.plan.md
```

### Step 2: Replace Placeholders

1. Search for all `[PLACEHOLDER]` patterns in the file
2. Replace each placeholder with actual values:
   - Use your project's directory structure
   - Use your programming language and test framework
   - List your actual modules
   - Define your priority groups

### Step 3: Customize Steps

1. Review the default steps in the template
2. Add or remove steps based on your project structure
3. Update step descriptions to match your modules
4. Adjust intake commands to match your codebase patterns

### Step 4: Set Priorities

1. Identify your high-priority modules (foundational, frequently used)
2. Identify medium-priority modules (important but less foundational)
3. Identify lower-priority modules (supporting modules)
4. Update the "Module Priority" section

### Step 5: Update Status

As you work through the plan:
1. Update the "Status" section with current state
2. Mark completed steps with ✅
3. Mark pending steps with ⏳
4. Update "Last Updated" date

## Template Structure

Both templates follow the same structure:

1. **Goal** - What the plan aims to achieve
2. **Status** - Current progress tracking
3. **Preconditions** - What must be true before starting
4. **Documentation Template** - Template for individual module READMEs
5. **Proposed Structure** - Directory and file structure
6. **Intake Process** - How to analyze modules before documenting
7. **Definition of Done** - Completion checklist
8. **Steps** - Detailed implementation steps
9. **Success Criteria** - Overall success metrics
10. **Module Priority** - Priority ordering
11. **Maintenance Guidelines** - How to keep docs current

## Best Practices

1. **Start with intake**: Always perform the intake process before writing documentation
2. **Follow the template**: Use the provided README template structure consistently
3. **Verify examples**: All code/test examples must be tested and working
4. **Update cross-references**: Keep "Related Modules" sections current
5. **Review regularly**: Update documentation when modules change

## Related Documents

- `TEMPLATE-documentation_standards.md` - Standards for module documentation (in this directory)
- `TEMPLATE-test_documentation_standards.md` - Standards for test documentation (in this directory)
- `docs/implementation_plans/` - Completed implementation plans using these templates

## Notes

- These templates are designed to be reusable across different projects
- Customize as needed for your specific project structure
- Keep placeholders clear and easy to find (use brackets)
- Document any project-specific customizations in the plan


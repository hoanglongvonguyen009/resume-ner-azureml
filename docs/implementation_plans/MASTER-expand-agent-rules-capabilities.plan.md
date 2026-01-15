# Expand Agent Rules & Capabilities

## Goal

Convert and adapt antigravity-kit rules and skills into Cursor `.mdc` format to enhance agent capabilities for Python/ML development, while maintaining consistency with existing workspace rules.

## Status

**Last Updated**: 2025-01-27

### Completed Steps

- ✅ Step 1: Convert always-on rules from antigravity-kit
- ✅ Step 2: Convert model-decision rules (optional, as reference)
- ✅ Step 3: Convert refactoring-expert skill (Python-adapted)
- ✅ Step 4: Convert code-review skill (Python-adapted)
- ✅ Step 5: Convert testing-expert skill (pytest-adapted)
- ✅ Step 6: Convert devops-expert skill (AzureML-adapted)
- ✅ Step 7: Verify rule integration and test agent behavior
- ✅ Step 8: Document new rules in workspace rules reference

### Pending Steps

- None - all steps completed!

## Preconditions

- `antigravity-kit` repository cloned in workspace root
- Existing `.cursor/rules/` directory with current rules
- Understanding of workspace conventions (Python, ML, AzureML, pytest)

## Steps

### Step 1: Convert Always-On Rules from antigravity-kit

Convert the core always-on rules that enhance agent behavior:

1. **01-identity.md** → `.cursor/rules/agent-identity.mdc`
   - Adapt "Full-stack Engineer" to "ML Engineer / Python Developer" context
   - Keep core principles (scope-bound, clarify-first, transparent, maintainable, quality-over-speed)
   - Set `alwaysApply: true`

2. **02-task-classification.md** → `.cursor/rules/task-classification.mdc`
   - Keep 4-task-type system (CONSULT, BUILD, DEBUG, OPTIMIZE)
   - Adapt recognition rules for Python/ML context
   - Set `alwaysApply: true`

3. **09-checklist.md** → `.cursor/rules/pre-delivery-checklist.mdc`
   - Adapt UI/UX section for ML/backend focus (remove frontend-specific items)
   - Keep code quality, structure, maintainability, performance sections
   - Adapt to Python conventions (pytest, type hints, mypy)
   - Set `alwaysApply: true`

4. **10-special-situations.md** → `.cursor/rules/special-situations.mdc`
   - Keep all special situation handling patterns
   - Adapt examples to Python/ML context
   - Set `alwaysApply: true`

**Success criteria**:

- 4 new `.mdc` files created in `.cursor/rules/`
- All files have proper frontmatter with `alwaysApply: true`
- Content adapted for Python/ML context (no JavaScript/TypeScript references)
- Agent behavior improves (better task classification, clearer communication)

### Step 2: Convert Model-Decision Rules (Optional Reference)

Convert rules that agent can decide when to apply (for reference, not auto-applied):

1. **03-mode-consulting.md** → `.cursor/rules/mode-consulting.mdc`
   - Set `alwaysApply: false` (or omit, rely on description)
   - Keep as reference for consulting workflow

2. **04-mode-build.md** → `.cursor/rules/mode-build.mdc`
   - Set `alwaysApply: false`
   - Adapt build process for Python/ML projects

3. **05-mode-debug.md** → `.cursor/rules/mode-debug.mdc`
   - Set `alwaysApply: false`
   - Adapt debugging process (pytest, logging, AzureML)

4. **06-mode-optimize.md** → `.cursor/rules/mode-optimize.mdc`
   - Set `alwaysApply: false`
   - Adapt optimization process for ML workloads

**Success criteria**:

- 4 reference rule files created
- Content adapted for Python/ML context
- Files serve as reference (not auto-applied)

### Step 3: Convert Technical Standards Rule

Convert and merge with existing code quality rules:

1. **07-technical-standards.md** → Review and merge with `.cursor/rules/python-code-quality.mdc`
   - Adapt naming conventions (camelCase → snake_case for Python)
   - Keep function/logic flow principles (early return, SRP, max lines)
   - Merge type safety section with existing type-safety rule
   - Adapt error handling for Python (try/except, structured logging)
   - Keep comments guidelines

**Success criteria**:

- `python-code-quality.mdc` updated with additional standards
- No duplication with existing rules
- Python conventions properly reflected

### Step 4: Convert Communication Rule

Convert communication style rule:

1. **08-communication.md** → `.cursor/rules/communication-style.mdc`
   - Keep style principles (clear, concise, structured, actionable)
   - Keep format guidelines (markdown, code blocks, tables)
   - Adapt examples to Python/ML context
   - Set `alwaysApply: true`

**Success criteria**:

- Communication rule file created
- Examples adapted for Python/ML
- Agent communication improves

### Step 5: Convert Refactoring-Expert Skill

Convert refactoring expertise to Python-focused skill:

1. **refactoring-expert/SKILL.md** → `.cursor/rules/refactoring-expert.mdc`
   - Adapt all JavaScript/TypeScript examples to Python
   - Replace npm/jest commands with pytest/uvx mypy
   - Adapt code smell detection commands for Python (grep patterns)
   - Keep refactoring techniques (extract method, inline, etc.)
   - Adapt detection scripts for Python files
   - Set `alwaysApply: true` (general refactoring always useful)

**Success criteria**:

- Refactoring expert rule created with Python examples
- All detection commands work for `.py` files
- Refactoring techniques adapted for Python patterns
- Agent proactively suggests refactoring when code smells detected

### Step 6: Convert Code-Review Skill

Convert code review expertise to Python-focused skill:

1. **code-review/SKILL.md** → `.cursor/rules/code-review-expert.mdc`
   - Adapt all TypeScript/JavaScript examples to Python
   - Replace framework detection (Jest/Vitest) with pytest detection
   - Adapt pattern recognition for Python (dataclasses, TypedDict, Protocol)
   - Keep review focus areas (architecture, quality, security, performance, testing, docs)
   - Adapt impact prioritization for ML context (model performance, data quality)
   - Set `alwaysApply: true` (code review always useful)

**Success criteria**:

- Code review expert rule created with Python examples
- Review process adapted for Python/ML codebase
- Agent provides comprehensive, actionable code reviews
- Examples reference Python patterns (dataclasses, pytest, mypy)

### Step 7: Convert Testing-Expert Skill

Convert testing expertise to pytest-focused skill:

1. **testing-expert/SKILL.md** → `.cursor/rules/testing-expert-python.mdc`
   - Replace Jest/Vitest with pytest
   - Replace npm with uv/pip
   - Adapt test structure for pytest (test_*.py, conftest.py)
   - Keep testing strategies (unit, integration, e2e)
   - Adapt mocking for pytest (unittest.mock, pytest fixtures)
   - Set `globs: ["tests/**/*.py", "**/*test*.py"]` (context-aware)

**Success criteria**:

- Testing expert rule created with pytest focus
- All examples use pytest syntax
- Test detection commands work for Python test files
- Agent provides pytest-specific testing guidance

### Step 8: Convert DevOps-Expert Skill

Convert DevOps expertise to AzureML-focused skill:

1. **devops-expert/SKILL.md** → `.cursor/rules/devops-expert.mdc`
   - Adapt for AzureML context (not Kubernetes/Docker-heavy)
   - Keep CI/CD patterns (GitHub Actions)
   - Adapt infrastructure detection for AzureML (workspace, compute targets)
   - Keep monitoring, security, performance sections
   - Set `globs: [".github/workflows/**", "**/Dockerfile*", "**/*azureml*.py"]` (context-aware)

**Success criteria**:

- DevOps expert rule created with AzureML focus
- Examples reference AzureML patterns
- Agent provides AzureML-specific DevOps guidance
- CI/CD patterns adapted for GitHub Actions

### Step 9: Verify Rule Integration

Test that new rules work together and don't conflict:

1. Review all `.mdc` files for:
   - Consistent frontmatter format
   - No conflicting guidance
   - Proper Python/ML context
   - Integration with existing rules

2. Test agent behavior:
   - Task classification works correctly
   - Refactoring suggestions appear when appropriate
   - Code reviews are comprehensive
   - Testing guidance is pytest-focused

**Success criteria**:

- All rules have consistent format
- No conflicts between rules
- Agent behavior demonstrates improved capabilities
- Rules complement existing workspace rules

### Step 10: Document New Rules

Update workspace documentation to reference new rules:

1. Create or update `docs/agent-rules-reference.md`:
   - List all `.mdc` rules
   - Explain when each applies
   - Provide examples of rule activation

2. Update README or contributing guide if needed

**Success criteria**:

- Documentation created/updated
- Clear reference for all agent rules
- Examples show rule usage

## Success Criteria (Overall)

- ✅ 8+ new `.mdc` rule files created in `.cursor/rules/`
- ✅ All rules adapted for Python/ML context (no JS/TS references)
- ✅ Always-on rules improve agent behavior (task classification, communication)
- ✅ Context-aware rules activate appropriately (testing, devops)
- ✅ Skills provide domain expertise (refactoring, code review)
- ✅ Rules integrate seamlessly with existing workspace rules
- ✅ Documentation updated with rule reference
- ✅ Agent demonstrates improved capabilities in practice

## Notes

- **Adaptation Priority**: Focus on converting rules that add value for Python/ML development. Skip frontend-specific skills (React, Next.js, CSS).
- **Integration**: Ensure new rules complement existing rules (`python-type-safety.mdc`, `python-code-quality.mdc`, etc.) rather than duplicate them.
- **Testing**: After conversion, test agent behavior with real tasks to verify rules activate correctly.
- **Iteration**: Rules can be refined based on actual usage patterns.

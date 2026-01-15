# Agent Rules Reference

This document provides a reference for all Cursor agent rules (`.mdc` files) in `.cursor/rules/`.

## Always-On Rules

These rules are automatically applied to all agent interactions.

### Core Behavior Rules

| Rule | File | Description |
|------|------|-------------|
| **Agent Identity** | `agent-identity.mdc` | Defines agent role (ML Engineer/Python Developer) and core working principles |
| **Task Classification** | `task-classification.mdc` | Classifies tasks into 4 types: CONSULT, BUILD, DEBUG, OPTIMIZE |
| **Communication Style** | `communication-style.mdc` | Guidelines for clear, structured, actionable communication |
| **Special Situations** | `special-situations.mdc` | How to handle edge cases, breaking changes, DRY violations |

### Code Quality Rules

| Rule | File | Description |
|------|------|-------------|
| **Python Code Quality** | `python-code-quality.mdc` | Clean code principles, naming conventions, function design |
| **Python Type Safety** | `python-type-safety.mdc` | Type hints, mypy compliance, precise types |
| **Python Dependencies** | `python-deps.mdc` | Dependency hygiene, no ad-hoc installs |
| **Python File Metadata** | `python-file-metadata.mdc` | Structured metadata blocks for entry points/workflows/tests |
| **Python Reuse-First** | `python-reuse-first.mdc` | DRY principles, reuse existing code before creating new |
| **Pre-Delivery Checklist** | `pre-delivery-checklist.mdc` | Mandatory checklist before delivering code |

### Expert Skills (Always-On)

| Rule | File | Description |
|------|------|-------------|
| **Refactoring Expert** | `refactoring-expert.mdc` | Code smell detection, refactoring techniques, Python patterns |
| **Code Review Expert** | `code-review-expert.mdc` | Comprehensive code review across 6 aspects |

## Context-Aware Rules

These rules activate when working with specific file patterns.

### Testing Expert

| Rule | File | Activation | Description |
|------|------|-----------|-------------|
| **Testing Expert** | `testing-expert-python.mdc` | `tests/**/*.py`, `**/*test*.py` | pytest expertise, test structure, mocking strategies |

### DevOps Expert

| Rule | File | Activation | Description |
|------|------|-----------|-------------|
| **DevOps Expert** | `devops-expert.mdc` | `.github/workflows/**`, `**/Dockerfile*`, `**/*azureml*.py` | CI/CD, AzureML, GitHub Actions patterns |

## Mode-Specific Rules (Reference)

These rules provide guidance for specific task types but are not auto-applied.

| Rule | File | Description |
|------|------|-------------|
| **Consulting Mode** | `mode-consulting.mdc` | Process for CONSULT tasks (compare options, provide recommendations) |
| **Build Mode** | `mode-build.mdc` | Process for BUILD tasks (create new code) |
| **Debug Mode** | `mode-debug.mdc` | Process for DEBUG tasks (fix bugs) |
| **Optimize Mode** | `mode-optimize.mdc` | Process for OPTIMIZE tasks (refactor, improve) |

## Workflow & Structure Rules

| Rule | File | Description |
|------|------|-------------|
| **Workflow Entrypoints** | `workflow-entrypoints.mdc` | Orchestration must live in `src/**/workflows/` |
| **Notebooks Thin** | `notebooks-thin.mdc` | Notebooks should be orchestration, extract logic to `src/` |
| **Implementation Plans** | `implementation-plans.mdc` | Structure and lifecycle of implementation plans |
| **Testing Strategy** | `testing-strategy.mdc` | Test public APIs, avoid over-specific assertions |

## Rule Activation

### Always-On Rules

Rules with `alwaysApply: true` in frontmatter are automatically applied:

```yaml
---
name: agent-identity
alwaysApply: true
---
```

### Context-Aware Rules

Rules with `globs` patterns activate when working with matching files:

```yaml
---
name: testing-expert-python
globs:
  - "tests/**/*.py"
  - "**/*test*.py"
alwaysApply: false
---
```

### Reference Rules

Rules with `alwaysApply: false` (or omitted) serve as reference and are not auto-applied.

## Usage Examples

### Example 1: Writing Tests

When you edit `tests/test_training.py`, the **Testing Expert** rule activates automatically, providing:
- pytest conventions
- Fixture patterns
- Mocking strategies
- Test isolation guidance

### Example 2: Code Review

The **Code Review Expert** rule is always active, providing:
- Architecture review
- Code quality assessment
- Security checks
- Performance analysis
- Testing quality review
- Documentation review

### Example 3: Refactoring

The **Refactoring Expert** rule is always active, providing:
- Code smell detection
- Refactoring technique suggestions
- Python-specific patterns
- DRY violation identification

## Integration with Workspace Rules

These agent rules complement the workspace rules in `docs/`:

- **Implementation Plans**: See `docs/implementation_plans/` for structured refactoring plans
- **Code Quality**: Rules align with workspace coding standards
- **Type Safety**: Rules enforce mypy compliance
- **Reuse-First**: Rules promote DRY principles

## Adding New Rules

To add a new rule:

1. Create `.mdc` file in `.cursor/rules/`
2. Add frontmatter with `name`, `description`, and activation settings
3. Write rule content (Python/ML focused)
4. Update this reference document
5. Test rule activation

Example:

```yaml
---
name: my-new-rule
description: Description of what this rule does.
globs:
  - "src/**/*.py"  # Optional: context-aware
alwaysApply: false  # or true for always-on
---

# My New Rule

Rule content here...
```

## Rule Dependencies

Some rules reference others:

- `python-code-quality.mdc` references `@python-type-safety.mdc`
- `pre-delivery-checklist.mdc` references `@python-file-metadata.mdc`
- `refactoring-expert.mdc` references `@testing-expert-python.mdc`

Use `@rule-name.mdc` syntax to reference other rules in content.


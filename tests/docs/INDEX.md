# Test Documentation Index

This index provides navigation to all test module documentation. Test modules are organized by category to help you find the right tests for your needs.

## Test Infrastructure

Foundational test infrastructure that other tests depend on.

### [`tests/fixtures/`](../fixtures/README.md)
Shared test fixtures and helpers. Provides dataset fixtures, MLflow mocking, config fixtures, and validation helpers used across all test modules.

### [`tests/shared/`](../shared/README.md)
Shared test utilities and common patterns. Provides validation utilities for HPO studies and notebook indentation, plus unit tests for shared infrastructure components.

### [`tests/test_data/`](../test_data/README.md)
Test data fixtures and datasets. Provides deterministic test data (text, PDF, PNG files) for API testing and FastAPI inference server tests.

## Workflow Tests

End-to-end workflow tests that validate complete notebook workflows from start to finish.

### [`tests/workflows/`](../workflows/README.md)
End-to-end workflow tests for complete notebook workflows. Tests notebook 01 (HPO + Benchmarking), notebook 02 (Selection → Final Training → Conversion), and full workflow (01 → 02 end-to-end).

## Feature-Specific Tests

Tests for specific features and workflows in the ML pipeline.

### [`tests/hpo/`](../hpo/README.md)
Hyperparameter optimization tests. Covers search space generation, trial execution, checkpoint resume, sweep setup, and full HPO workflow with unit, integration, and E2E tests.

### [`tests/benchmarking/`](../benchmarking/README.md)
Benchmarking tests. Covers benchmark workflow, orchestrator, edge cases, MLflow tracking, and configuration options.

### [`tests/selection/`](../selection/README.md)
Model selection tests. Covers best model selection logic, artifact acquisition from multiple sources (local, drive, MLflow), cache functionality, and selection workflow execution.

### [`tests/final_training/`](../final_training/README.md)
Final training tests. Covers final training components, logging intervals, and configuration validation.

### [`tests/conversion/`](../conversion/README.md)
Model conversion tests. Covers conversion workflows, configuration validation, and conversion options.

## Infrastructure Tests

Tests for infrastructure components including tracking, configuration, and core infrastructure.

### [`tests/tracking/`](../tracking/README.md)
MLflow tracking tests. Covers naming policies, tags registry, MLflow configuration, and Azure ML artifact upload fixes (monkey-patch, child run uploads, refit run completion).

### [`tests/config/`](../config/README.md)
Configuration loading tests. Covers config loader, experiment/data/model configs, paths/naming/mlflow YAML tests, fingerprints, and run mode decision logic.

### [`tests/infrastructure/`](../infrastructure/README.md)
Infrastructure component tests. Covers config run decisions, naming (HPO keys, semantic suffix), and tracking (MLflow queries, sweep tracker) organized by submodule.

## Component Tests

Tests for core components including training and API functionality.

### [`tests/training/`](../training/README.md)
Training component tests. Covers trainer (training loop and data loader), checkpoint loader, data combiner, CV utils, and HPO-specific training features.

### [`tests/api/`](../api/README.md)
API and inference tests. Covers FastAPI server, inference engine, entity extractors, and performance validation with unit and integration tests.

## Test Utilities

Test scripts, documentation, and utilities.

### [`tests/scripts/`](../scripts/README.md)
Test scripts and manual verification tools. Provides standalone scripts for notebook validation and manual verification of fixes and functionality.

### [`tests/docs/`](../docs/README.md)
Test coverage analysis and documentation. Provides coverage analysis documents for YAML configs, test limitations documentation, and coverage status tracking.

## Quick Navigation by Test Type

### Unit Tests
- [`tests/hpo/unit/`](../hpo/README.md) - HPO components
- [`tests/benchmarking/unit/`](../benchmarking/README.md) - Benchmark config
- [`tests/selection/unit/`](../selection/README.md) - Selection config
- [`tests/final_training/unit/`](../final_training/README.md) - Final training config
- [`tests/conversion/unit/`](../conversion/README.md) - Conversion config
- [`tests/tracking/unit/`](../tracking/README.md) - Tracking components
- [`tests/config/unit/`](../config/README.md) - Config loading
- [`tests/unit/training/`](../training/README.md) - Training components
- [`tests/unit/api/`](../api/README.md) - API components

### Integration Tests
- [`tests/hpo/integration/`](../hpo/README.md) - HPO with real components
- [`tests/benchmarking/integration/`](../benchmarking/README.md) - Benchmark workflow
- [`tests/selection/integration/`](../selection/README.md) - Selection workflow
- [`tests/final_training/integration/`](../final_training/README.md) - Final training components
- [`tests/conversion/integration/`](../conversion/README.md) - Conversion config
- [`tests/tracking/integration/`](../tracking/README.md) - Tracking behavior
- [`tests/config/integration/`](../config/README.md) - Config integration
- [`tests/integration/api/`](../api/README.md) - FastAPI server

### E2E Tests
- [`tests/workflows/`](../workflows/README.md) - Complete notebook workflows
- [`tests/hpo/e2e/`](../hpo/README.md) - Full HPO workflow

## Test Dependencies

### Foundation Layer (Used by All Tests)
- [`tests/fixtures/`](../fixtures/README.md) - Shared fixtures
- [`tests/shared/`](../shared/README.md) - Shared utilities
- [`tests/test_data/`](../test_data/README.md) - Test data

### Infrastructure Layer (Used by Feature Tests)
- [`tests/tracking/`](../tracking/README.md) - MLflow tracking
- [`tests/config/`](../config/README.md) - Configuration loading
- [`tests/infrastructure/`](../infrastructure/README.md) - Infrastructure components

### Feature Layer (Workflow Components)
- [`tests/hpo/`](../hpo/README.md) - HPO
- [`tests/benchmarking/`](../benchmarking/README.md) - Benchmarking
- [`tests/selection/`](../selection/README.md) - Model selection
- [`tests/final_training/`](../final_training/README.md) - Final training
- [`tests/conversion/`](../conversion/README.md) - Model conversion

### Workflow Layer (End-to-End)
- [`tests/workflows/`](../workflows/README.md) - Complete workflows

### Component Layer (Core Components)
- [`tests/training/`](../training/README.md) - Training components
- [`tests/api/`](../api/README.md) - API components

## See Also

- [`tests/README.md`](../README.md) - Main testing guide with prerequisites, test structure, and running instructions



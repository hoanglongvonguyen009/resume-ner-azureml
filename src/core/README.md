# Core

Core utilities for token validation, normalization, and placeholder handling used by the naming and path resolution systems.

## TL;DR / Quick Start

Core utilities for the naming system foundation. Provides token registry, normalization functions, and placeholder extraction.

```python
from src.core.tokens import is_token_known, is_token_allowed
from src.core.normalize import normalize_for_name, normalize_for_path
from src.core.placeholders import extract_placeholders

# Check if a token is valid for naming
is_token_allowed("model", scope="name")  # True

# Normalize a value for display
normalized, warnings = normalize_for_name("My Model", rules={"lowercase": True})

# Extract placeholders from a pattern
placeholders = extract_placeholders("{model}_{stage}")  # {'model', 'stage'}
```

## Overview

The `core` module provides foundational utilities for the naming and path resolution systems:

- **Token registry**: Centralized registry of known tokens (e.g., `model`, `env`, `spec_fp`) with scope validation (name vs path)
- **Normalization**: Functions to normalize values for display names and filesystem-safe paths
- **Placeholder extraction**: Utility to parse `{placeholder}` patterns from template strings

This module has **no dependencies** on other `src/` modules, making it safe for use in infrastructure layers that need naming utilities without circular dependencies.

## Module Structure

- `tokens.py`: Token registry and validation functions
- `normalize.py`: Normalization functions for names and paths
- `placeholders.py`: Placeholder extraction from pattern strings

## Usage

### Basic Example: Token Validation

```python
from src.core.tokens import is_token_known, is_token_allowed, get_token

# Check if a token exists in the registry
is_token_known("model")  # True
is_token_known("unknown_token")  # False

# Check if a token is allowed for a specific scope
is_token_allowed("model", scope="name")  # True (model can be used in names)
is_token_allowed("model", scope="path")  # True (model can be used in paths)
is_token_allowed("env", scope="path")  # False (env is name-only)

# Get token object
token = get_token("model")
print(token.scopes)  # {'name', 'path'}
```

### Basic Example: Normalization

```python
from src.core.normalize import normalize_for_name, normalize_for_path

# Normalize for display name (returns tuple with warnings)
normalized, warnings = normalize_for_name(
    "My Model Name",
    rules={"lowercase": True, "replace": {" ": "_"}}
)
# normalized: "my_model_name", warnings: []

# Normalize for filesystem path
normalized, warnings = normalize_for_path(
    "outputs/model@v1.0",
    rules={
        "forbidden_chars": ["@", "."],
        "lowercase": True,
        "max_component_length": 20
    }
)
# normalized: "outputs/model_v1_0", warnings: ["Replaced forbidden char '@'", ...]
```

### Basic Example: Placeholder Extraction

```python
from src.core.placeholders import extract_placeholders

# Extract placeholders from a pattern
placeholders = extract_placeholders("{model}_{stage}_{env}")
# {'model', 'stage', 'env'}

# Use in path resolution
pattern = "outputs/{storage_env}/{model}/trial_{trial_number}"
required = extract_placeholders(pattern)
# {'storage_env', 'model', 'trial_number'}
```

## API Reference

### Token Functions

- `is_token_known(name: str) -> bool`: Check if a token name exists in the registry
- `is_token_allowed(name: str, scope: str) -> bool`: Check if a token is allowed for a scope (name or path)
- `get_token(name: str) -> Optional[Token]`: Get token object by name
- `tokens_for_scope(scope: str) -> Iterable[str]`: Get all token names allowed for a scope
- `TOKENS: Dict[str, Token]`: Registry of all known tokens
- `Token`: Dataclass with `name` and `scopes` fields

### Normalization Functions

- `normalize_for_name(value: Any, rules: Dict[str, Any] | None = None, return_warnings: bool = True) -> Union[str, Tuple[str, List[str]]]`: Normalize value for display/name usage
- `normalize_for_path(value: Any, rules: Dict[str, Any] | None = None) -> Tuple[str, List[str]]`: Normalize value to be filesystem-safe

### Placeholder Functions

- `extract_placeholders(pattern: str) -> Set[str]`: Extract placeholder names from a pattern string

For detailed signatures, see source code.

## Integration Points

### Used By

- `infrastructure/naming/`: Uses token validation and normalization for display names
- `infrastructure/paths/`: Uses normalization and placeholder extraction for path resolution

### Depends On

- No dependencies on other `src/` modules (designed to avoid circular dependencies)

## Testing

```bash
uvx pytest tests/core/
```

## Related Modules

- [`../infrastructure/naming/README.md`](../infrastructure/naming/README.md) - Uses core utilities for naming policies
- [`../infrastructure/paths/README.md`](../infrastructure/paths/README.md) - Uses core utilities for path resolution


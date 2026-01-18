"""MLflow-related constants.

Centralized constants for MLflow query limits, display lengths, and other MLflow-specific values.
"""

# MLflow Query Limits
DEFAULT_MLFLOW_MAX_RESULTS = 1000  # Default limit for MLflow run queries
MEDIUM_MLFLOW_MAX_RESULTS = 2000  # Medium limit for standard queries
LARGE_MLFLOW_MAX_RESULTS = 5000  # Large limit for comprehensive queries
SAFETY_MLFLOW_MAX_RESULTS = 10000  # Safety limit for large queries (prevents memory issues)
SMALL_MLFLOW_MAX_RESULTS = 10  # Small limit for targeted queries
SAMPLE_MLFLOW_MAX_RESULTS = 5  # Sample size for diagnostic queries

# Hash Display Lengths (for logging/display purposes)
HASH_DISPLAY_LENGTH_SHORT = 8  # Short hash display (e.g., for compact logs)
HASH_DISPLAY_LENGTH_MEDIUM = 12  # Medium hash display (default for run IDs, hashes)
HASH_DISPLAY_LENGTH_LONG = 16  # Long hash display (e.g., for detailed debugging)
ERROR_MESSAGE_DISPLAY_LENGTH = 200  # Maximum length for error messages in logs

# Random Seed Defaults
DEFAULT_RANDOM_SEED = 42  # Default random seed for reproducibility

# Stale Detection
DEFAULT_STALE_MINUTES = 30  # Default minutes before considering something stale


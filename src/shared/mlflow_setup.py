"""Platform-aware MLflow setup utility for cross-platform tracking."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Any

try:
    import mlflow
except ImportError:
    raise ImportError(
        "mlflow is required for experiment tracking. "
        "Install it with: pip install mlflow"
    )

from shared.platform_detection import detect_platform
from shared.yaml_utils import load_yaml
from shared.logging_utils import get_logger

logger = get_logger(__name__)


def _load_env_file(env_file_path: Path) -> dict:
    """
    Load environment variables from a .env file.

    Supports simple KEY="VALUE" or KEY=VALUE format.
    Comments (lines starting with #) are ignored.

    Args:
        env_file_path: Path to .env file

    Returns:
        Dictionary of key-value pairs
    """
    env_vars = {}
    if not env_file_path.exists():
        return env_vars

    try:
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Parse KEY="VALUE" or KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    env_vars[key] = value
    except Exception as e:
        logger.warning(f"Could not load {env_file_path}: {e}")

    return env_vars


def setup_mlflow_cross_platform(
    experiment_name: str,
    ml_client: Optional[Any] = None,
    fallback_to_local: bool = True,
) -> str:
    """
    Setup MLflow for cross-platform tracking.

    If ml_client provided, uses Azure ML workspace (unified tracking).
    Otherwise, falls back to platform-specific local tracking (SQLite backend).
    Also sets the MLflow experiment name.

    Args:
        experiment_name: MLflow experiment name (will be created if doesn't exist)
        ml_client: Optional Azure ML client for unified tracking. If provided,
                  must be an instance of azure.ai.ml.MLClient
        fallback_to_local: If True, fallback to local tracking when Azure ML fails

    Returns:
        Tracking URI string that was configured

    Raises:
        ImportError: If mlflow is not installed (with helpful error message)
        RuntimeError: If Azure ML required but unavailable and fallback disabled
    """
    # Check if Azure ML tracking is already configured
    current_tracking_uri = mlflow.get_tracking_uri()
    is_azure_ml_already_set = current_tracking_uri and "azureml" in current_tracking_uri.lower()

    # If Azure ML is already set and we don't have ml_client, preserve it
    if is_azure_ml_already_set and ml_client is None:
        logger.debug(
            f"Preserving existing Azure ML tracking URI: {current_tracking_uri[:50]}...")
        mlflow.set_experiment(experiment_name)
        return current_tracking_uri

    # Try Azure ML first if ml_client provided
    if ml_client is not None:
        try:
            tracking_uri = _get_azure_ml_tracking_uri(ml_client)
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
            logger.info("Using Azure ML workspace tracking")
            logger.debug(f"Tracking URI: {tracking_uri}")
            return tracking_uri
        except Exception as e:
            if not fallback_to_local:
                raise RuntimeError(
                    f"Azure ML tracking failed and fallback disabled: {e}"
                ) from e
            logger.warning(f"Azure ML tracking failed: {e}")
            logger.info("Falling back to local tracking...")

    # Fallback to local tracking
    tracking_uri = _get_local_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    logger.info(f"Using local tracking: {tracking_uri}")
    return tracking_uri


def _get_azure_ml_tracking_uri(ml_client: Any) -> str:
    """
    Get Azure ML workspace tracking URI.

    Args:
        ml_client: Azure ML client instance (azure.ai.ml.MLClient)

    Returns:
        Azure ML workspace tracking URI string

    Raises:
        ImportError: If azureml.mlflow is not available
        RuntimeError: If workspace access fails
    """
    # Import azureml.mlflow to register the 'azureml' URI scheme
    try:
        import azureml.mlflow  # noqa: F401
    except ImportError:
        raise ImportError(
            "azureml.mlflow is required for Azure ML tracking. "
            "Install it with: pip install azureml-mlflow"
        )

    # Get workspace tracking URI
    try:
        workspace = ml_client.workspaces.get(name=ml_client.workspace_name)
        return workspace.mlflow_tracking_uri
    except Exception as e:
        raise RuntimeError(
            f"Failed to get Azure ML workspace tracking URI: {e}"
        ) from e


def _get_local_tracking_uri() -> str:
    """
    Get local tracking URI with platform-aware path resolution.

    Uses SQLite backend to address MLflow deprecation warning for file-based tracking.

    Returns:
        SQLite tracking URI string (e.g., "sqlite:///path/to/mlflow.db")
    """
    platform = detect_platform()

    if platform == "colab":
        # Check if Google Drive is mounted
        drive_path = Path("/content/drive/MyDrive")
        if drive_path.exists() and drive_path.is_dir():
            # Use Drive for persistence across sessions
            mlflow_db = drive_path / "resume-ner-mlflow" / "mlflow.db"
        else:
            # Fallback to /content/ if Drive not mounted
            mlflow_db = Path("/content") / "mlflow.db"
    elif platform == "kaggle":
        # Kaggle outputs in /kaggle/working/ are automatically persisted
        mlflow_db = Path("/kaggle/working") / "mlflow.db"
    else:
        # Local: use current directory
        mlflow_db = Path("./mlruns") / "mlflow.db"

    # Ensure parent directory exists
    mlflow_db.parent.mkdir(parents=True, exist_ok=True)

    # Convert to absolute path and return SQLite URI
    abs_path = mlflow_db.resolve()
    return f"sqlite:///{abs_path}"


def create_ml_client_from_config(
    config_dir: Path,
    mlflow_config: Optional[dict] = None,
) -> Optional[Any]:
    """
    Create Azure ML client from configuration files.

    Args:
        config_dir: Path to config directory (e.g., Path("config"))
        mlflow_config: Optional pre-loaded MLflow config dict. If None, loads from config/mlflow.yaml

    Returns:
        MLClient instance if Azure ML is enabled and credentials available, None otherwise

    Raises:
        ImportError: If azure-ai-ml is not installed
    """
    # Load MLflow config if not provided
    if mlflow_config is None:
        mlflow_config_path = config_dir / "mlflow.yaml"
        if not mlflow_config_path.exists():
            return None
        mlflow_config = load_yaml(mlflow_config_path)

    # Check if Azure ML is enabled
    azure_ml_config = mlflow_config.get("azure_ml", {})
    if not azure_ml_config.get("enabled", False):
        return None

    # Suppress OpenTelemetry warnings (common in Colab/Kaggle)
    os.environ.setdefault("OTEL_SDK_DISABLED", "false")
    os.environ.setdefault("OTEL_LOG_LEVEL", "ERROR")

    # Try to import Azure ML SDK
    try:
        # Suppress verbose OpenTelemetry logging
        import logging
        logging.getLogger("opentelemetry").setLevel(logging.ERROR)

        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        logger.warning(
            "azure-ai-ml and azure-identity are required for Azure ML tracking. "
            "Install with: pip install azure-ai-ml azure-identity. "
            "Falling back to local tracking."
        )
        return None

    # Get credentials from environment variables
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    workspace_name = azure_ml_config.get("workspace_name", "resume-ner-ws")

    # Load Service Principal credentials (for Colab/Kaggle authentication)
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")

    # If environment variables not set, try loading from config.env file (in project root)
    if not subscription_id or not resource_group or not (client_id and client_secret and tenant_id):
        project_root = config_dir.parent
        config_env_path = project_root / "config.env"
        if config_env_path.exists():
            logger.info(
                f"Environment variables not set, loading from {config_env_path}")
            env_vars = _load_env_file(config_env_path)
            subscription_id = subscription_id or env_vars.get(
                "AZURE_SUBSCRIPTION_ID")
            resource_group = resource_group or env_vars.get(
                "AZURE_RESOURCE_GROUP")
            client_id = client_id or env_vars.get("AZURE_CLIENT_ID")
            client_secret = client_secret or env_vars.get(
                "AZURE_CLIENT_SECRET")
            tenant_id = tenant_id or env_vars.get("AZURE_TENANT_ID")

            if subscription_id and resource_group:
                # Set environment variables for this process
                os.environ["AZURE_SUBSCRIPTION_ID"] = subscription_id
                os.environ["AZURE_RESOURCE_GROUP"] = resource_group
                logger.info(
                    "Loaded subscription/resource group from config.env")
                logger.debug(
                    f"AZURE_SUBSCRIPTION_ID: {subscription_id[:8]}...")
                logger.debug(f"AZURE_RESOURCE_GROUP: {resource_group}")

            if client_id and client_secret and tenant_id:
                # Set service principal credentials for authentication
                os.environ["AZURE_CLIENT_ID"] = client_id
                os.environ["AZURE_CLIENT_SECRET"] = client_secret
                os.environ["AZURE_TENANT_ID"] = tenant_id
                logger.info(
                    "Loaded service principal credentials from config.env")
                logger.debug(f"AZURE_CLIENT_ID: {client_id[:8]}...")
                logger.debug(f"AZURE_TENANT_ID: {tenant_id[:8]}...")
            else:
                logger.debug(
                    "Service principal credentials not found in config.env. "
                    "Will try DefaultAzureCredential (may not work in Colab/Kaggle).")
        else:
            logger.warning(f"config.env not found at {config_env_path}")

    # If still not set, try loading from infrastructure.yaml
    # (infrastructure.yaml may contain ${AZURE_SUBSCRIPTION_ID} placeholders)
    if not subscription_id or not resource_group:
        infra_config_path = config_dir / "infrastructure.yaml"
        if infra_config_path.exists():
            infra_config = load_yaml(infra_config_path)
            azure_config = infra_config.get("azure", {})
            # Only use infrastructure.yaml values if they're not placeholders
            infra_sub_id = azure_config.get("subscription_id", "")
            infra_rg = azure_config.get("resource_group", "")
            if infra_sub_id and not infra_sub_id.startswith("${"):
                subscription_id = subscription_id or infra_sub_id
            if infra_rg and not infra_rg.startswith("${"):
                resource_group = resource_group or infra_rg

    # Check if we have required values
    if not subscription_id or not resource_group:
        logger.warning(
            "Azure ML enabled but subscription/resource group not found. Falling back to local tracking.")
        logger.info(
            "Set AZURE_SUBSCRIPTION_ID and AZURE_RESOURCE_GROUP environment variables or add to config.env")
        return None

    # Determine authentication method
    platform = detect_platform()
    has_service_principal = client_id and client_secret and tenant_id

    if platform in ("colab", "kaggle") and not has_service_principal:
        logger.warning(
            f"Azure ML authentication requires Service Principal credentials in {platform.upper()} environments. "
            "Add to config.env: AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID. "
            "Falling back to local tracking."
        )
        logger.info(
            "To use Azure ML from Colab/Kaggle, create a Service Principal and add credentials to config.env:\n"
            "  AZURE_CLIENT_ID=<your-client-id>\n"
            "  AZURE_CLIENT_SECRET=<your-client-secret>\n"
            "  AZURE_TENANT_ID=<your-tenant-id>"
        )
        return None

    try:
        # Suppress verbose credential chain warnings
        import logging
        azure_logger = logging.getLogger("azure.identity")
        azure_logger.setLevel(logging.ERROR)

        # Use Service Principal if available (required for Colab/Kaggle)
        if has_service_principal:
            from azure.identity import ClientSecretCredential
            logger.info(
                "Using Service Principal authentication (from config.env)")
            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            # Use DefaultAzureCredential (works in local/Azure environments)
            logger.info(
                "Using DefaultAzureCredential (trying multiple auth methods)")
            credential = DefaultAzureCredential()

        ml_client = MLClient(
            credential=credential,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
            workspace_name=workspace_name,
        )
        logger.info(
            f"Successfully connected to Azure ML workspace: {workspace_name}")
        return ml_client
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Failed to create Azure ML client: {error_msg}")

        # Provide helpful guidance based on platform
        if platform in ("colab", "kaggle"):
            logger.info(
                "For Colab/Kaggle, you need Service Principal credentials in config.env:\n"
                "  AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID"
            )
        else:
            logger.info(
                "Ensure you're authenticated (Azure CLI: 'az login' or set Service Principal env vars)"
            )
        logger.info("Falling back to local tracking.")
        return None


def setup_mlflow_from_config(
    experiment_name: str,
    config_dir: Path,
    fallback_to_local: bool = True,
) -> str:
    """
    Setup MLflow from configuration files.

    Reads config/mlflow.yaml to determine whether to use Azure ML Workspace
    or local tracking. Automatically creates MLClient if Azure ML is enabled.

    Args:
        experiment_name: MLflow experiment name (will be created if doesn't exist)
        config_dir: Path to config directory (e.g., Path("config"))
        fallback_to_local: If True, fallback to local tracking when Azure ML fails

    Returns:
        Tracking URI string that was configured

    Raises:
        ImportError: If mlflow is not installed
        FileNotFoundError: If config/mlflow.yaml doesn't exist (only if Azure ML enabled)
    """
    # Load MLflow config
    mlflow_config_path = config_dir / "mlflow.yaml"
    if not mlflow_config_path.exists():
        # If config doesn't exist, use local tracking
        logger.warning("MLflow config not found, using local tracking")
        return setup_mlflow_cross_platform(
            experiment_name=experiment_name,
            ml_client=None,
            fallback_to_local=fallback_to_local,
        )

    mlflow_config = load_yaml(mlflow_config_path)

    # Try to create MLClient if Azure ML is enabled
    ml_client = None
    azure_ml_config = mlflow_config.get("azure_ml", {})
    platform = detect_platform()

    if azure_ml_config.get("enabled", False):
        logger.info("Azure ML enabled in config, attempting to connect...")
        logger.debug(
            f"Workspace: {azure_ml_config.get('workspace_name', 'unknown')}")
        # Try to create ML client - it will load from config.env if env vars not set
        # For Colab/Kaggle, requires Service Principal credentials
        ml_client = create_ml_client_from_config(config_dir, mlflow_config)
        if ml_client is None:
            logger.info("Falling back to local tracking")
    else:
        logger.info("Azure ML disabled in config, using local tracking")

    # Setup MLflow with or without Azure ML
    return setup_mlflow_cross_platform(
        experiment_name=experiment_name,
        ml_client=ml_client,
        fallback_to_local=fallback_to_local,
    )

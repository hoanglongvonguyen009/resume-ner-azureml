"""
@meta
name: infrastructure_setup_azure
type: utility
domain: infrastructure
responsibility:
  - Create/verify Azure ML workspace
  - Create/verify storage account and containers
  - Create/verify compute clusters
  - Validate infrastructure components
inputs:
  - infrastructure.yaml config
  - Environment variables (AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, AZURE_LOCATION)
outputs:
  - MLClient instance
  - BlobServiceClient instance
  - Compute cluster instances
tags:
  - utility
  - infrastructure
  - azure
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: true
lifecycle:
  status: active
"""

"""Azure infrastructure setup utilities.

This module provides functions for creating and validating Azure ML infrastructure:
- Workspace creation/retrieval
- Storage account and container setup
- Compute cluster provisioning
- Infrastructure validation
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from azure.ai.ml import MLClient
from azure.ai.ml.entities import AmlCompute, Workspace
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import (
    AccessTier,
    Kind,
    PublicAccess,
    Sku,
    SkuName,
    StorageAccountCreateParameters,
)
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Required environment variables for infrastructure setup
REQUIRED_ENV_VARS = ["AZURE_SUBSCRIPTION_ID", "AZURE_RESOURCE_GROUP"]
CONNECTION_STRING_TEMPLATE = (
    "DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
)


def validate_environment_variables(required_vars: Optional[List[str]] = None) -> None:
    """
    Validate required environment variables are set.

    Args:
        required_vars: List of required environment variable names.
                      If None, uses default REQUIRED_ENV_VARS.

    Raises:
        ValueError: If required variables are missing
    """
    if required_vars is None:
        required_vars = REQUIRED_ENV_VARS

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")


def load_infrastructure_config(
    config_path: Path, env_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Load and resolve infrastructure configuration from YAML file.

    Resolves environment variable placeholders in the config (e.g., ${VAR_NAME:-default}).
    Environment variables take precedence over config file values.

    Args:
        config_path: Path to infrastructure.yaml config file.
        env_path: Optional path to config.env file. If provided, loads environment variables from it.

    Returns:
        Configuration dictionary with resolved environment variables.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If location appears invalid.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # Load environment variables if env_path provided
    if env_path and env_path.exists():
        load_dotenv(env_path, override=True)

    with open(config_path, "r") as f:
        config: Dict[str, Any] = yaml.safe_load(f)

    # Resolve subscription_id - prioritize environment variable
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if subscription_id:
        config["azure"]["subscription_id"] = subscription_id
    elif isinstance(config["azure"]["subscription_id"], str) and config["azure"]["subscription_id"].startswith("${"):
        match = re.match(r'\$\{([^:]+)(?::-([^}]+))?\}', config["azure"]["subscription_id"])
        if match:
            var_name, default = match.groups()
            config["azure"]["subscription_id"] = os.getenv(var_name, default or "")

    # Resolve resource_group - prioritize environment variable
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    if resource_group:
        config["azure"]["resource_group"] = resource_group
    elif isinstance(config["azure"]["resource_group"], str) and config["azure"]["resource_group"].startswith("${"):
        match = re.match(r'\$\{([^:]+)(?::-([^}]+))?\}', config["azure"]["resource_group"])
        if match:
            var_name, default = match.groups()
            config["azure"]["resource_group"] = os.getenv(var_name, default or "")

    # Resolve location - prioritize environment variable
    location = os.getenv("AZURE_LOCATION")
    if location:
        config["azure"]["location"] = location
    elif isinstance(config["azure"]["location"], str) and config["azure"]["location"].startswith("${"):
        match = re.match(r'\$\{([^:]+)(?::-([^}]+))?\}', config["azure"]["location"])
        if match:
            var_name, default = match.groups()
            config["azure"]["location"] = os.getenv(var_name, default or "southeastasia")

    # Warn if location seems invalid (optional validation)
    valid_regions = [
        "eastus",
        "eastus2",
        "westus",
        "westus2",
        "westus3",
        "westcentralus",
        "southcentralus",
        "northcentralus",
        "centralus",
        "westeurope",
        "northeurope",
        "swedencentral",
        "uksouth",
        "ukwest",
        "francecentral",
        "germanywestcentral",
        "norwayeast",
        "switzerlandnorth",
        "eastasia",
        "southeastasia",
        "japaneast",
        "japanwest",
        "koreacentral",
        "koreasouth",
        "australiaeast",
        "australiasoutheast",
        "australiacentral",
        "brazilsouth",
        "canadaeast",
        "canadacentral",
        "southindia",
        "centralindia",
        "westindia",
        "uaenorth",
        "southafricanorth",
        "qatarcentral",
    ]

    if config["azure"]["location"] not in valid_regions:
        # Just a warning, not an error - new regions may be added
        pass  # Could add logging here if desired

    return config


def create_or_get_resource_group(config: Dict[str, Any]) -> None:
    """
    Create resource group if it doesn't exist.

    Args:
        config: Infrastructure configuration dictionary with 'azure' section.

    Raises:
        Exception: If resource group creation fails.
    """
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    location = config["azure"]["location"]
    credential = DefaultAzureCredential()

    resource_client = ResourceManagementClient(credential, subscription_id)

    try:
        resource_client.resource_groups.get(resource_group)
    except ResourceNotFoundError:
        resource_group_params = ResourceGroup(location=location)
        resource_client.resource_groups.create_or_update(resource_group, resource_group_params)


def create_or_get_workspace(config: Dict[str, Any]) -> MLClient:
    """
    Create or retrieve Azure ML Workspace.

    Args:
        config: Infrastructure configuration dictionary with 'azure' and 'workspace' sections.

    Returns:
        MLClient instance connected to the workspace.

    Raises:
        Exception: If workspace creation or access fails.
    """
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    workspace_name = config["workspace"]["name"]
    credential = DefaultAzureCredential()

    create_or_get_resource_group(config)

    try:
        ml_client = MLClient(credential, subscription_id, resource_group, workspace_name)
        ml_client.workspaces.get(workspace_name)
        return ml_client
    except ResourceNotFoundError:
        workspace = Workspace(
            name=workspace_name,
            location=config["azure"]["location"],
            description=config["workspace"].get("description", ""),
            display_name=workspace_name,
        )
        ml_client = MLClient(credential, subscription_id, resource_group)
        ml_client.workspaces.begin_create(workspace).result()
        return MLClient(credential, subscription_id, resource_group, workspace_name)


def build_connection_string(account_name: str, account_key: str) -> str:
    """
    Build storage account connection string.

    Args:
        account_name: Storage account name.
        account_key: Storage account key.

    Returns:
        Connection string for blob service client.
    """
    return CONNECTION_STRING_TEMPLATE.format(account_name=account_name, account_key=account_key)


def create_or_get_storage(config: Dict[str, Any]) -> BlobServiceClient:
    """
    Create or retrieve Azure Blob Storage account and containers.

    Args:
        config: Infrastructure configuration dictionary with 'azure' and 'storage' sections.

    Returns:
        BlobServiceClient instance.

    Raises:
        Exception: If storage creation or access fails.
        ValueError: If public_access value is invalid.
    """
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    location = config["azure"]["location"]
    account_name = config["storage"]["account_name"]

    credential = DefaultAzureCredential()
    storage_management = StorageManagementClient(credential, subscription_id)

    try:
        storage_management.storage_accounts.get_properties(resource_group, account_name)
    except ResourceNotFoundError:
        params = StorageAccountCreateParameters(
            sku=Sku(name=SkuName.STANDARD_LRS),
            kind=Kind.STORAGE_V2,
            location=location,
            access_tier=AccessTier.HOT,
        )
        storage_management.storage_accounts.begin_create(resource_group, account_name, params).result()

    keys = storage_management.storage_accounts.list_keys(resource_group, account_name)
    connection_string = build_connection_string(account_name, keys.keys[0].value)
    blob_client = BlobServiceClient.from_connection_string(connection_string)

    for container_config in config["storage"]["containers"]:
        container_name = container_config["name"]
        public_access_str = container_config.get("public_access", "None")

        if public_access_str is None or public_access_str.lower() == "none":
            public_access = None
        else:
            public_access = getattr(PublicAccess, public_access_str.upper(), None)
            if public_access is None:
                raise ValueError(f"Invalid public_access value: {public_access_str}")

        container = blob_client.get_container_client(container_name)
        if not container.exists():
            container.create_container(public_access=public_access)

    return blob_client


def create_or_get_compute_cluster(
    ml_client: MLClient,
    cluster_name: str,
    vm_size: str,
    min_nodes: int,
    max_nodes: int,
    idle_time_before_scale_down: int,
) -> AmlCompute:
    """
    Create or retrieve a single compute cluster.

    Args:
        ml_client: MLClient instance.
        cluster_name: Name of the compute cluster.
        vm_size: VM size (e.g., "Standard_NC6s_v3").
        min_nodes: Minimum number of nodes (0 for cost savings).
        max_nodes: Maximum number of nodes.
        idle_time_before_scale_down: Idle time in seconds before scaling down.

    Returns:
        AmlCompute instance.

    Raises:
        Exception: If cluster creation or update fails.
    """
    try:
        compute = ml_client.compute.get(cluster_name)

        needs_update = (
            compute.size != vm_size
            or compute.min_instances != min_nodes
            or compute.max_instances != max_nodes
        )

        if needs_update:
            compute.size = vm_size
            compute.min_instances = min_nodes
            compute.max_instances = max_nodes
            compute.idle_time_before_scale_down = idle_time_before_scale_down

            if hasattr(compute, "network_settings") and compute.network_settings is not None:
                if compute.network_settings.subnet is None:
                    compute.network_settings = None

            ml_client.compute.begin_create_or_update(compute).wait()

        return compute

    except ResourceNotFoundError:
        compute = AmlCompute(
            name=cluster_name,
            size=vm_size,
            min_instances=min_nodes,
            max_instances=max_nodes,
            idle_time_before_scale_down=idle_time_before_scale_down,
        )

        ml_client.compute.begin_create_or_update(compute).wait()
        return compute


def create_or_get_compute_clusters(ml_client: MLClient, config: Dict[str, Any]) -> None:
    """
    Create or retrieve compute clusters based on configuration.

    GPU cluster is optional and only created if present in config.
    CPU cluster is required.

    Args:
        ml_client: MLClient instance.
        config: Infrastructure configuration dictionary with 'compute' section.

    Raises:
        KeyError: If compute config or CPU cluster config is missing.
    """
    if "compute" not in config or not config["compute"]:
        raise KeyError("'compute' section not found in config. Please ensure config is loaded correctly.")

    compute_config = config["compute"]

    if "gpu_cluster" in compute_config and compute_config["gpu_cluster"] is not None:
        gpu_config = compute_config["gpu_cluster"]
        create_or_get_compute_cluster(
            ml_client=ml_client,
            cluster_name=gpu_config["name"],
            vm_size=gpu_config["vm_size"],
            min_nodes=gpu_config["min_nodes"],
            max_nodes=gpu_config["max_nodes"],
            idle_time_before_scale_down=gpu_config["idle_time_before_scale_down"],
        )

    if "cpu_cluster" not in compute_config:
        raise KeyError("'cpu_cluster' configuration is required but not found in config.")

    cpu_config = compute_config["cpu_cluster"]
    create_or_get_compute_cluster(
        ml_client=ml_client,
        cluster_name=cpu_config["name"],
        vm_size=cpu_config["vm_size"],
        min_nodes=cpu_config["min_nodes"],
        max_nodes=cpu_config["max_nodes"],
        idle_time_before_scale_down=cpu_config["idle_time_before_scale_down"],
    )


def validate_workspace(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Azure ML Workspace exists and is accessible.

    Args:
        config: Infrastructure configuration dictionary.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: List[str] = []
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    workspace_name = config["workspace"]["name"]

    try:
        ml_client = MLClient(DefaultAzureCredential(), subscription_id, resource_group, workspace_name)
        ml_client.workspaces.get(workspace_name)
        return True, errors
    except ResourceNotFoundError:
        errors.append(f"Workspace '{workspace_name}' not found")
        return False, errors
    except Exception as e:
        errors.append(f"Error accessing workspace: {e}")
        return False, errors


def validate_storage(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Storage Account and Containers exist.

    Args:
        config: Infrastructure configuration dictionary.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: List[str] = []
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    account_name = config["storage"]["account_name"]

    try:
        storage_management = StorageManagementClient(DefaultAzureCredential(), subscription_id)
        storage_management.storage_accounts.get_properties(resource_group, account_name)

        keys = storage_management.storage_accounts.list_keys(resource_group, account_name)
        connection_string = build_connection_string(account_name, keys.keys[0].value)
        blob_client = BlobServiceClient.from_connection_string(connection_string)

        for container_config in config["storage"]["containers"]:
            container_name = container_config["name"]
            if not blob_client.get_container_client(container_name).exists():
                errors.append(f"Container '{container_name}' not found")

        return len(errors) == 0, errors
    except ResourceNotFoundError:
        errors.append(f"Storage account '{account_name}' not found")
        return False, errors
    except Exception as e:
        errors.append(f"Error accessing storage: {e}")
        return False, errors


def validate_compute(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Compute Clusters exist and are accessible.

    Only validates clusters that are present in the configuration.
    GPU cluster is optional, CPU cluster is required.

    Args:
        config: Infrastructure configuration dictionary.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: List[str] = []
    subscription_id = config["azure"]["subscription_id"]
    resource_group = config["azure"]["resource_group"]
    workspace_name = config["workspace"]["name"]

    try:
        ml_client = MLClient(DefaultAzureCredential(), subscription_id, resource_group, workspace_name)
        compute_config = config.get("compute", {})

        if "gpu_cluster" in compute_config and compute_config["gpu_cluster"] is not None:
            gpu_cluster_name = compute_config["gpu_cluster"]["name"]
            try:
                ml_client.compute.get(gpu_cluster_name)
            except ResourceNotFoundError:
                errors.append(f"GPU cluster '{gpu_cluster_name}' not found")
            except Exception as e:
                errors.append(f"Error accessing GPU cluster '{gpu_cluster_name}': {e}")

        if "cpu_cluster" in compute_config:
            cpu_cluster_name = compute_config["cpu_cluster"]["name"]
            try:
                ml_client.compute.get(cpu_cluster_name)
            except ResourceNotFoundError:
                errors.append(f"CPU cluster '{cpu_cluster_name}' not found")
            except Exception as e:
                errors.append(f"Error accessing CPU cluster '{cpu_cluster_name}': {e}")
        else:
            errors.append("CPU cluster configuration is required but not found")

        return len(errors) == 0, errors
    except Exception as e:
        errors.append(f"Error accessing workspace: {e}")
        return False, errors


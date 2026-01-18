from __future__ import annotations

"""
@meta
name: azureml_helpers
type: utility
domain: infrastructure
responsibility:
  - Shared Azure ML helper functions
  - Data input building utilities
inputs:
  - Azure ML data assets
outputs:
  - Azure ML Input objects
tags:
  - utility
  - infrastructure
  - azureml
ci:
  runnable: false
  needs_gpu: false
  needs_cloud: true
lifecycle:
  status: active
"""
from azure.ai.ml import Input
from azure.ai.ml.entities import Data


def build_data_input_from_asset(data_asset: Data) -> Input:
    """
    Build a standard Azure ML ``Input`` for a ``uri_folder`` data asset.

    Args:
        data_asset: Registered Azure ML data asset.

    Returns:
        Input pointing at the asset, mounted as a folder.
    """
    return Input(
        type="uri_folder",
        path=f"azureml:{data_asset.name}:{data_asset.version}",
        mode="mount",
    )


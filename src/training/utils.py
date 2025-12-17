"""Utility functions for training."""

from typing import Optional

import torch


def set_seed(seed: Optional[int]) -> None:
    """
    Set random seed for reproducibility.

    Args:
        seed: Random seed value. If None, no seed is set.
    """
    if seed is None:
        return
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


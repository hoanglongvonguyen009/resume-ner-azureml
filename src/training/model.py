"""Model initialization utilities."""

from typing import Dict, Any

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
)


def create_model_and_tokenizer(
    config: Dict[str, Any],
    label2id: Dict[str, int],
    id2label: Dict[int, str],
    device: torch.device | None = None,
) -> tuple:
    """
    Create model and tokenizer from configuration.

    Args:
        config: Configuration dictionary containing model settings.
        label2id: Mapping from label strings to integer IDs.
        id2label: Mapping from label IDs to label strings.

    Returns:
        Tuple of (model, tokenizer, device).
    """
    model_cfg = config["model"]
    backbone = model_cfg.get("backbone", "distilbert-base-uncased")
    tokenizer_name = model_cfg.get("tokenizer", backbone)

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    model = AutoModelForTokenClassification.from_pretrained(
        backbone,
        num_labels=len(label2id),
        id2label=id2label,
        label2id=label2id,
        use_safetensors=True,
    )

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    return model, tokenizer, device

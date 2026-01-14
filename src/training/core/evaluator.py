"""
@meta
name: evaluator
type: utility
domain: training
responsibility:
  - Model evaluation utilities
  - Extract predictions and labels from model outputs
  - Evaluate models on validation/test sets
inputs:
  - Model outputs (logits, labels, masks)
  - Data loaders
outputs:
  - Evaluation metrics
  - Predictions and labels
tags:
  - utility
  - training
  - evaluation
ci:
  runnable: true
  needs_gpu: true
  needs_cloud: false
lifecycle:
  status: active
"""

"""Model evaluation utilities."""

from typing import Dict, List, Union

import torch
from torch.utils.data import DataLoader

from .metrics import compute_metrics


def extract_predictions_and_labels(
    logits: torch.Tensor,
    labels: torch.Tensor,
    mask: torch.Tensor,
    id2label: Dict[int, str],
) -> tuple[List[List[str]], List[List[str]]]:
    """
    Extract predictions and labels from model outputs.

    Args:
        logits: Model logits tensor.
        labels: True labels tensor.
        mask: Attention mask tensor.
        id2label: Mapping from label IDs to label strings.

    Returns:
        Tuple of (all_labels, all_preds) as lists of label sequences.
    """
    preds = logits.argmax(-1)
    all_preds, all_labels = [], []

    for pred_row, label_row, mask_row in zip(preds, labels, mask):
        pred_tags: List[str] = []
        true_tags: List[str] = []
        for pred_val, label_val, mask_val in zip(
            pred_row.tolist(), label_row.tolist(), mask_row.tolist()
        ):
            if mask_val == 0:
                continue
            true_tags.append(id2label.get(label_val, "O"))
            pred_tags.append(id2label.get(pred_val, "O"))
        if true_tags:
            all_labels.append(true_tags)
            all_preds.append(pred_tags)
    
    return all_labels, all_preds


def evaluate_model(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    id2label: Dict[int, str],
) -> Dict[str, Union[float, str, Dict[str, Dict[str, float]]]]:
    """
    Evaluate model and compute metrics.

    Args:
        model: The model to evaluate.
        dataloader: DataLoader for validation data.
        device: Device to run evaluation on.
        id2label: Mapping from label IDs to label strings.

    Returns:
        Dictionary containing macro_f1, macro_f1_span, and loss metrics.
    """
    model.eval()
    all_preds, all_labels = [], []
    total_loss = 0.0
    steps = 0
    
    with torch.no_grad():
        for batch in dataloader:
            labels = batch["labels"]
            mask = batch["attention_mask"]
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            total_loss += loss.item()
            steps += 1

            logits = outputs.logits.detach().cpu()
            batch_labels, batch_preds = extract_predictions_and_labels(
                logits, labels, mask, id2label
            )
            all_labels.extend(batch_labels)
            all_preds.extend(batch_preds)

    avg_loss = total_loss / max(1, steps)
    return compute_metrics(all_labels, all_preds, avg_loss)


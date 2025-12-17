"""Metric calculation utilities."""

from typing import Dict, List

from seqeval.metrics import f1_score


def compute_f1_for_label(label: str, flat_true: List[str], flat_pred: List[str]) -> float:
    """
    Compute F1 score for a specific label.

    Args:
        label: Label to compute F1 for.
        flat_true: Flat list of true labels.
        flat_pred: Flat list of predicted labels.

    Returns:
        F1 score for the label.
    """
    tp = fp = fn = 0
    for y_t, y_p in zip(flat_true, flat_pred):
        if y_t == label and y_p == label:
            tp += 1
        elif y_t != label and y_p == label:
            fp += 1
        elif y_t == label and y_p != label:
            fn += 1
    
    if tp == 0 and fp == 0 and fn == 0:
        return 0.0
    
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    
    if precision == 0.0 and recall == 0.0:
        return 0.0
    
    return 2 * precision * recall / (precision + recall)


def compute_token_macro_f1(all_labels: List[List[str]], all_preds: List[List[str]]) -> float:
    """
    Compute macro-averaged F1 score across all token labels.

    Args:
        all_labels: List of true label sequences.
        all_preds: List of predicted label sequences.

    Returns:
        Macro-averaged F1 score.
    """
    flat_true: List[str] = [lab for seq in all_labels for lab in seq]
    flat_pred: List[str] = [lab for seq in all_preds for lab in seq]
    unique_labels = sorted(set(flat_true)) if flat_true else []
    
    if not unique_labels:
        return 0.0
    
    f1_scores = [
        compute_f1_for_label(label, flat_true, flat_pred)
        for label in unique_labels
    ]
    
    return sum(f1_scores) / len(f1_scores)


def compute_metrics(
    all_labels: List[List[str]],
    all_preds: List[List[str]],
    avg_loss: float,
) -> Dict[str, float]:
    """
    Compute all evaluation metrics.

    Args:
        all_labels: List of true label sequences.
        all_preds: List of predicted label sequences.
        avg_loss: Average loss value.

    Returns:
        Dictionary containing all computed metrics.
    """
    span_f1 = f1_score(all_labels, all_preds) if all_labels else 0.0
    token_macro_f1 = compute_token_macro_f1(all_labels, all_preds)
    
    return {
        "macro-f1": float(token_macro_f1),
        "macro-f1-span": float(span_f1),
        "loss": float(avg_loss),
    }


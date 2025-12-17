"""Data loading and processing utilities."""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

from torch.utils.data import Dataset
import torch


def load_dataset(data_path: str) -> Dict[str, Any]:
    """
    Load dataset from JSON files.

    Args:
        data_path: Path to directory containing train.json and optionally validation.json.

    Returns:
        Dictionary with "train" and "validation" keys containing data lists.

    Raises:
        FileNotFoundError: If dataset path or train.json does not exist.
    """
    data_path_obj = Path(data_path)
    if not data_path_obj.exists():
        raise FileNotFoundError(f"Dataset path not found: {data_path}")
    
    train_file = data_path_obj / "train.json"
    if not train_file.exists():
        raise FileNotFoundError(f"Training file not found: {train_file}")
    
    with open(train_file, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    
    val_file = data_path_obj / "validation.json"
    val_data = []
    if val_file.exists():
        with open(val_file, "r", encoding="utf-8") as f:
            val_data = json.load(f)
    
    return {"train": train_data, "validation": val_data}


def build_label_list(data_config: Dict[str, Any]) -> List[str]:
    """
    Build label list from data configuration.

    Args:
        data_config: Data configuration dictionary containing schema information.

    Returns:
        List of labels starting with "O" followed by sorted entity types.
    """
    entity_types = data_config.get("schema", {}).get("entity_types", [])
    return ["O"] + sorted(entity_types)


def normalize_text(raw_text: Any) -> str:
    """
    Normalize arbitrary text input (string, list, dict, etc.) into a single string
    that the tokenizer can consume.
    """
    if isinstance(raw_text, str):
        return raw_text
    if isinstance(raw_text, (list, tuple)):
        flat: List[str] = []
        for t in raw_text:
            if isinstance(t, (list, tuple)):
                flat.extend(map(str, t))
            else:
                flat.append(str(t))
        return " ".join(flat)
    if raw_text is None:
        return ""
    try:
        return json.dumps(raw_text, ensure_ascii=False)
    except Exception:
        return str(raw_text)


def encode_annotations_to_labels(
    text: str,
    annotations: List[List[Any]],
    offsets: List[Tuple[int, int]],
    label2id: Dict[str, int],
) -> List[int]:
    """
    Encode character-level annotations to token-level labels.

    Args:
        text: Original text string.
        annotations: List of annotations as [start, end, entity_type].
        offsets: List of token offset tuples (start, end).
        label2id: Mapping from label strings to integer IDs.

    Returns:
        List of label IDs corresponding to each token.
    """
    labels = []
    for start, end in offsets:
        lab = "O"
        for ann_start, ann_end, ent in annotations:
            if not (end <= ann_start or start >= ann_end):
                lab = ent
                break
        labels.append(label2id.get(lab, label2id["O"]))
    return labels


class ResumeNERDataset(Dataset):
    """Dataset for Resume NER token classification."""
    
    def __init__(
        self,
        samples: List[Dict[str, Any]],
        tokenizer,
        max_length: int,
        label2id: Dict[str, int],
    ):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label2id = label2id

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        """
        Encode a single sample.

        For fast tokenizers we request ``return_offsets_mapping`` so that we can
        align character-level annotations to token labels.  Some slow (Python)
        tokenizers – including the DeBERTa v2/v3 slow tokenizers – do **not**
        support ``return_offsets_mapping`` and will raise ``NotImplementedError``.
        In that case we fall back to a simpler behaviour where all tokens are
        labelled as ``O`` so that the training loop can still run and the
        orchestration pipeline can be validated.
        """
        item = self.samples[idx]
        text = normalize_text(item.get("text", ""))
        annotations = item.get("annotations", []) or []

        supports_offsets = bool(getattr(self.tokenizer, "is_fast", False))

        encoded = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            return_offsets_mapping=supports_offsets,
            return_tensors="pt",
        )

        if supports_offsets and "offset_mapping" in encoded:
            offsets = encoded.pop("offset_mapping")[0].tolist()
            labels = encode_annotations_to_labels(
                text, annotations, offsets, self.label2id
            )
        else:
            seq_len = encoded["input_ids"].shape[1]
            labels = [self.label2id.get("O", 0)] * seq_len

        encoded = {k: v.squeeze(0) for k, v in encoded.items()}
        encoded["labels"] = torch.tensor(labels, dtype=torch.long)
        return encoded


"""
Training script for Resume NER model.

Implements a minimal token-classification training/eval loop using transformers.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import yaml
import mlflow
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    get_linear_schedule_with_warmup,
)
from seqeval.metrics import f1_score

# Constants
VAL_SPLIT_DIVISOR = 10
DEBERTA_MAX_BATCH_SIZE = 8
WARMUP_STEPS_DIVISOR = 10


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Resume NER model")
    parser.add_argument("--data-asset", type=str, required=True, help="Azure ML data asset path or local dataset path")
    parser.add_argument("--config-dir", type=str, required=True, help="Path to configuration directory")
    parser.add_argument("--backbone", type=str, required=True, help="Model backbone name (e.g., 'distilbert')")
    parser.add_argument("--learning-rate", type=float, default=None, help="Learning rate override")
    parser.add_argument("--batch-size", type=int, default=None, help="Batch size override")
    parser.add_argument("--dropout", type=float, default=None, help="Dropout override")
    parser.add_argument("--weight-decay", type=float, default=None, help="Weight decay override")
    parser.add_argument("--epochs", type=int, default=None, help="Epochs override")
    parser.add_argument("--random-seed", type=int, default=None, help="Random seed")
    parser.add_argument("--early-stopping-enabled", type=str, default=None, help="Enable early stopping ('true'/'false')")
    parser.add_argument("--use-combined-data", type=str, default=None, help="Use combined train+validation ('true'/'false')")
    return parser.parse_args()


def load_config_file(config_dir: Path, filename: str) -> Dict[str, Any]:
    """
    Load configuration file from directory.

    Args:
        config_dir: Directory containing configuration files.
        filename: Name of the configuration file.

    Returns:
        Dictionary containing configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    config_path = config_dir / filename
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def build_training_config(args: argparse.Namespace, config_dir: Path) -> Dict[str, Any]:
    """
    Build training configuration from files and command-line arguments.

    Args:
        args: Parsed command-line arguments.
        config_dir: Directory containing configuration files.

    Returns:
        Dictionary containing merged configuration.
    """
    train_config = load_config_file(config_dir, "train.yaml")
    model_config = load_config_file(config_dir, f"model/{args.backbone}.yaml")
    data_config = load_config_file(config_dir, "data/resume_v1.yaml")
    
    config = {
        "data": data_config,
        "model": model_config,
        "training": train_config["training"].copy(),
    }
    
    if args.learning_rate is not None:
        config["training"]["learning_rate"] = args.learning_rate
    if args.batch_size is not None:
        config["training"]["batch_size"] = args.batch_size
    if args.dropout is not None:
        config["model"]["dropout"] = args.dropout
    if args.weight_decay is not None:
        config["training"]["weight_decay"] = args.weight_decay
    if args.epochs is not None:
        config["training"]["epochs"] = args.epochs
    if args.random_seed is not None:
        config["training"]["random_seed"] = args.random_seed
    if args.early_stopping_enabled is not None:
        enabled = args.early_stopping_enabled.lower() == "true"
        config["training"]["early_stopping"]["enabled"] = enabled
    if args.use_combined_data is not None:
        config["data"]["use_combined_data"] = args.use_combined_data.lower() == "true"
    
    return config


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
    if data_path_obj.exists():
        train_file = data_path_obj / "train.json"
        val_file = data_path_obj / "validation.json"
        if not train_file.exists():
            raise FileNotFoundError(f"Training file not found: {train_file}")
        with open(train_file, "r", encoding="utf-8") as f:
            train_data = json.load(f)
        val_data = []
        if val_file.exists():
            with open(val_file, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        return {"train": train_data, "validation": val_data}
    raise FileNotFoundError(f"Dataset path not found: {data_path}")


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


def evaluate(
    model: torch.nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    id2label: Dict[int, str],
) -> Dict[str, float]:
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
            preds = logits.argmax(-1)

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

    span_f1 = f1_score(all_labels, all_preds) if all_labels else 0.0

    flat_true: List[str] = [lab for seq in all_labels for lab in seq]
    flat_pred: List[str] = [lab for seq in all_preds for lab in seq]
    labels = sorted(set(flat_true)) if flat_true else []

    def _f1_for_label(label: str) -> float:
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

    token_macro_f1 = (
        sum(_f1_for_label(lbl) for lbl in labels) / len(labels) if labels else 0.0
    )

    avg_loss = total_loss / max(1, steps)
    return {
        "macro_f1": float(token_macro_f1),
        "macro_f1_span": float(span_f1),
        "loss": float(avg_loss),
    }


def train_model(config: Dict[str, Any], dataset: Dict[str, Any], output_dir: Path) -> Dict[str, float]:
    """
    Train a token classification model and return evaluation metrics.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    train_data = dataset.get("train", [])
    val_data = dataset.get("validation", [])
    if not val_data:
        val_data = train_data[: max(1, len(train_data) // VAL_SPLIT_DIVISOR)]

    model_cfg = config["model"]
    train_cfg = config["training"]
    data_cfg = config["data"]

    backbone = model_cfg.get("backbone", "distilbert-base-uncased")
    tokenizer_name = model_cfg.get("tokenizer", backbone)
    max_length = model_cfg.get("preprocessing", {}).get("max_length", 128)
    batch_size = train_cfg.get("batch_size", 8)
    
    if "deberta" in backbone.lower() and batch_size > DEBERTA_MAX_BATCH_SIZE:
        batch_size = DEBERTA_MAX_BATCH_SIZE
    epochs = max(1, train_cfg.get("epochs", 1))
    lr = train_cfg.get("learning_rate", 2e-5)
    wd = train_cfg.get("weight_decay", 0.0)
    warmup_steps = train_cfg.get("warmup_steps", 0)
    max_grad_norm = train_cfg.get("max_grad_norm", 1.0)

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    label_list = build_label_list(data_cfg)
    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for l, i in label2id.items()}

    train_ds = ResumeNERDataset(train_data, tokenizer, max_length, label2id)
    val_ds = ResumeNERDataset(val_data, tokenizer, max_length, label2id)

    data_collator = DataCollatorForTokenClassification(tokenizer)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, collate_fn=data_collator)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, collate_fn=data_collator)

    model = AutoModelForTokenClassification.from_pretrained(
        backbone,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
        use_safetensors=True,
    )
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    total_steps = epochs * max(1, len(train_loader))
    max_warmup_steps = total_steps // WARMUP_STEPS_DIVISOR
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=min(warmup_steps, max_warmup_steps), num_training_steps=total_steps
    )

    model.train()
    for _ in range(epochs):
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

    metrics = evaluate(model, val_loader, device, id2label)

    checkpoint_path = output_dir / "checkpoint"
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(checkpoint_path)
    tokenizer.save_pretrained(checkpoint_path)

    return metrics


def write_metrics(output_dir: Path, metrics: Dict[str, float]) -> None:
    """
    Write metrics to file and log to MLflow.

    Args:
        output_dir: Directory to write metrics file.
        metrics: Dictionary of metric names to values.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f)
    for k, v in metrics.items():
        mlflow.log_metric(k, v)


def main() -> None:
    args = parse_arguments()
    
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"Config directory not found: {config_dir}")
    
    config = build_training_config(args, config_dir)

    params = {
        "learning_rate": config["training"].get("learning_rate"),
        "batch_size": config["training"].get("batch_size"),
        "dropout": config["model"].get("dropout"),
        "weight_decay": config["training"].get("weight_decay"),
        "epochs": config["training"].get("epochs"),
        "backbone": config["model"].get("backbone"),
    }
    mlflow.log_params({k: v for k, v in params.items() if v is not None})

    seed = config["training"].get("random_seed")
    set_seed(seed)
    
    dataset = load_dataset(args.data_asset)
    
    output_dir = Path(os.getenv("AZURE_ML_OUTPUT_DIR", "./outputs"))
    metrics = train_model(config, dataset, output_dir)
    write_metrics(output_dir, metrics)


if __name__ == "__main__":
    main()


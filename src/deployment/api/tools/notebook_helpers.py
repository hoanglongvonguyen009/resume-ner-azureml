"""Helper functions for API testing notebooks."""

import sys
from pathlib import Path
import time
from typing import Any, Optional

import requests


def setup_notebook_paths(project_root: Optional[Path] = None) -> Path:
    """Setup Python paths for notebook execution.
    
    This function:
    1. Determines the project root directory
    2. Adds src/ and project root to sys.path for imports
    
    Args:
        project_root: Optional project root path. If None, will be auto-detected
            based on current working directory (assumes notebook is in notebooks/
            or at project root)
    
    Returns:
        Path to project root directory
    """
    if project_root is None:
        current_dir = Path.cwd()
        if current_dir.name == "notebooks":
            project_root = current_dir.parent
        else:
            project_root = current_dir
    
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    return project_root


def make_request(
    method: str,
    endpoint: str,
    base_url: str = "http://localhost:8000",
    timeout: int = 30,
    **kwargs: Any,
) -> dict[str, Any]:
    """Make HTTP request to API and return response data.
    
    Args:
        method: HTTP method (GET, POST)
        endpoint: API endpoint path
        base_url: Base URL for the API server (default: "http://localhost:8000")
        timeout: Request timeout in seconds (default: 30)
        **kwargs: Additional arguments for requests (e.g., json, files)
    
    Returns:
        Dictionary with:
            - status_code: HTTP status code (None if request failed)
            - data: Response data (parsed JSON or text)
            - latency_ms: Request latency in milliseconds
            - error: Error message if request failed (None otherwise)
    """
    url = f"{base_url}{endpoint}"
    start_time = time.time()
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        latency_ms = (time.time() - start_time) * 1000
        
        result: dict[str, Any] = {
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "error": None,
        }
        
        try:
            result["data"] = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            result["data"] = {"text": response.text}
        
        return result
    except requests.exceptions.RequestException as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "status_code": None,
            "latency_ms": latency_ms,
            "data": None,
            "error": str(e),
        }


def display_entities(
    entities: list[dict[str, Any]],
    source_text: Optional[str] = None,
) -> None:
    """Display extracted entities in a formatted way.
    
    Groups entities by label and displays them with confidence scores.
    Optionally shows entities highlighted in source text context.
    
    Args:
        entities: List of entity dictionaries with keys:
            - label: Entity label (e.g., "NAME", "EMAIL")
            - text: Entity text
            - confidence: Optional confidence score
            - start: Optional start position in source text
            - end: Optional end position in source text
        source_text: Optional source text to show entities in context
    """
    if not entities:
        return
    
    # Group by label
    by_label: dict[str, list[dict[str, Any]]] = {}
    for entity in entities:
        label = entity.get("label", "UNKNOWN")
        if label not in by_label:
            by_label[label] = []
        by_label[label].append(entity)
    
    # Display by label
    for label, label_entities in sorted(by_label.items()):
        print(f"{label} ({len(label_entities)}):")
        for entity in label_entities:
            text = entity.get("text", "")
            confidence = entity.get("confidence")
            conf_str = f" (confidence: {confidence:.3f})" if confidence else ""
            print(f"  - '{text}'{conf_str}")
    
    # Show entities in context if source_text provided
    if source_text:
        highlighted_text = source_text
        sorted_entities = sorted(
            entities, key=lambda e: e.get("start", 0), reverse=True
        )
        for entity in sorted_entities:
            start = entity.get("start", 0)
            end = entity.get("end", 0)
            text = entity.get("text", "")
            label = entity.get("label", "UNKNOWN")
            highlighted_text = (
                highlighted_text[:start]
                + f"[{text}]({label})"
                + highlighted_text[end:]
            )
        print(f"\nContext: {highlighted_text}")



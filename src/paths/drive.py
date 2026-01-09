"""Drive backup path mapping."""

from pathlib import Path
from typing import Optional

from paths.config import load_paths_config


def get_drive_backup_base(config_dir: Path) -> Optional[Path]:
    """
    Get base Google Drive backup directory from config.

    Args:
        config_dir: Config directory.

    Returns:
        Base Drive backup path (e.g., /content/drive/MyDrive/resume-ner-checkpoints), 
        or None if not configured.

    Examples:
        get_drive_backup_base(CONFIG_DIR)
        # -> Path("/content/drive/MyDrive/resume-ner-checkpoints")
    """
    paths_config = load_paths_config(config_dir)
    drive_config = paths_config.get("drive", {})

    if not drive_config:
        return None

    mount_point = drive_config.get("mount_point", "/content/drive")
    backup_base = drive_config.get("backup_base_dir", "resume-ner-checkpoints")

    return Path(mount_point) / "MyDrive" / backup_base


def get_drive_backup_path(
    root_dir: Path,
    config_dir: Path,
    local_path: Path
) -> Optional[Path]:
    """
    Convert local output path to Drive backup path, mirroring structure.

    Only paths within outputs/ can be backed up. The function automatically
    mirrors the exact same directory structure from outputs/ to Drive.

    Args:
        root_dir: Project root directory.
        config_dir: Config directory.
        local_path: Local file or directory path to backup (must be within outputs/).

    Returns:
        Equivalent Drive backup path, or None if Drive not configured or path outside outputs/.

    Examples:
        Local: outputs/hpo/distilbert/trial_0/checkpoint/
        Drive:  /content/drive/MyDrive/resume-ner-checkpoints/outputs/hpo/distilbert/trial_0/checkpoint/

        Local: outputs/cache/best_configurations/latest_best_configuration.json
        Drive:  /content/drive/MyDrive/resume-ner-checkpoints/outputs/cache/best_configurations/latest_best_configuration.json
    """
    paths_config = load_paths_config(config_dir)
    drive_config = paths_config.get("drive", {})

    if not drive_config:
        return None

    # Get the base outputs directory
    base_outputs = paths_config["base"]["outputs"]
    base_outputs_path = Path(base_outputs)
    outputs_dir = (
        base_outputs_path if base_outputs_path.is_absolute() else root_dir / base_outputs
    )
    base_outputs_name = base_outputs_path.name if base_outputs_path.is_absolute() else base_outputs

    # Check if the local path is within outputs/
    try:
        relative_path = local_path.relative_to(outputs_dir)
    except ValueError:
        # Path is not within outputs/, can't mirror it
        return None

    # Get Drive base directory
    drive_base = get_drive_backup_base(config_dir)
    if not drive_base:
        return None

    # Build Drive path: mount_point/MyDrive/backup_base/outputs/relative_path
    drive_path = drive_base / base_outputs_name / relative_path

    return drive_path


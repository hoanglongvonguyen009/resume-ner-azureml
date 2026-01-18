"""Trial finder module for locating best trials from HPO studies or disk."""

# Import from discovery.py (functions in trial_finder/discovery.py)
from .discovery import (
    find_best_trial_from_study,
    find_best_trial_in_study_folder,
    find_best_trials_for_backbones,
    find_study_folder_in_backbone_dir,
)

# Import from champion_selection.py (functions in trial_finder/champion_selection.py)
from .champion_selection import (
    select_champion_per_backbone,
    select_champions_for_backbones,
)

# Import from trial_finder.py (function in trial_finder/trial_finder.py)
from .trial_finder import (
    format_trial_identifier,
)

__all__ = [
    "find_best_trial_from_study",
    "find_best_trial_in_study_folder",
    "find_best_trials_for_backbones",
    "find_study_folder_in_backbone_dir",
    "format_trial_identifier",
    "select_champion_per_backbone",
    "select_champions_for_backbones",
]


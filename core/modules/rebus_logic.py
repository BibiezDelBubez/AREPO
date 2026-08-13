"""
Rebus Business Logic Module for AREPO.
Handles Rebus key decomposition and Stereoscopic Stereogram image ROI pairing logic.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class StereoscopicDifference:
    """Represents a visual difference region between two stereoscopic images."""
    id: int
    roi_left: Tuple[int, int, int, int]   # (x, y, width, height)
    roi_right: Tuple[int, int, int, int]  # (x, y, width, height)
    associated_key: str                   # Rebus key word e.g. "CANE"
    grapheme: str                         # Grapheme letters e.g. "CA"
    description: str                      # Visual detail description


class RebusLogic:
    """Business logic for Rebus key combination and Stereoscopic visual pairing."""

    def __init__(self):
        self.stereoscopic_diffs: List[StereoscopicDifference] = []

    def add_stereoscopic_difference(
        self,
        roi_left: Tuple[int, int, int, int],
        roi_right: Tuple[int, int, int, int],
        associated_key: str,
        grapheme: str = "",
        description: str = ""
    ) -> StereoscopicDifference:
        diff_id = len(self.stereoscopic_diffs) + 1
        diff = StereoscopicDifference(
            id=diff_id,
            roi_left=roi_left,
            roi_right=roi_right,
            associated_key=associated_key.upper(),
            grapheme=grapheme.upper(),
            description=description
        )
        self.stereoscopic_diffs.append(diff)
        return diff

    def clear_stereoscopic_differences(self) -> None:
        self.stereoscopic_diffs.clear()

    def generate_stereoscopic_phrase(self) -> str:
        """Combine all graphemes and keys into full rebus solution phrase."""
        parts = []
        for diff in self.stereoscopic_diffs:
            if diff.grapheme:
                parts.append(diff.grapheme)
            if diff.associated_key:
                parts.append(diff.associated_key)
        return " ".join(parts)

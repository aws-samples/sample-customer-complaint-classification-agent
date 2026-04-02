from dataclasses import dataclass, field
from datetime import datetime
from typing import List

from .base import Serializable


@dataclass
class Complaint(Serializable):
    """Represents a classified complaint."""

    transcript: str
    classification_result: str
    timestamp: datetime
    matched_criteria: List[str] = field(default_factory=list)

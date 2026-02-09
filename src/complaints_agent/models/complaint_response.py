from dataclasses import dataclass, field
from typing import List

from .base import Serializable


@dataclass
class ComplaintResponse(Serializable):
    """Response from the Complaints Agent.
    
    Attributes:
        severity: "low", "medium", "high", or "critical"
        category: Type of complaint
        actions_taken: Actions performed
        next_steps: Recommended follow-up actions
    """
    severity: str
    category: str
    actions_taken: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

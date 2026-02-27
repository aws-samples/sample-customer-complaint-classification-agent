"""Shared data models for the complaints agent system."""

from dataclasses import dataclass, field
from typing import List
import json


@dataclass
class ComplaintResponse:
    """Response model for processed complaints containing severity, category, routing, and action items."""

    severity: str
    category: str
    routing_group: str = "disputes"
    actions_taken: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert the ComplaintResponse to a dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "routing_group": self.routing_group,
            "actions_taken": self.actions_taken,
            "next_steps": self.next_steps
        }

    def to_json(self) -> str:
        """Serialize the ComplaintResponse to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ComplaintResponse":
        """Deserialize a JSON string to a ComplaintResponse object."""
        data = json.loads(json_str)
        return cls(
            severity=data["severity"],
            category=data["category"],
            routing_group=data.get("routing_group", "disputes"),
            actions_taken=data.get("actions_taken", []),
            next_steps=data.get("next_steps", [])
        )

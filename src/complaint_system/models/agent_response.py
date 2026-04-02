from dataclasses import dataclass
from typing import Optional

from .base import Serializable
from .complaint import Complaint
from .complaint_response import ComplaintResponse


@dataclass
class AgentResponse(Serializable):
    """Final response from the Supervisor Agent.
    
    Attributes:
        is_complaint: Whether the transcript was classified as a complaint
        complaint: The Complaint object if classified as complaint
        complaint_response: The ComplaintResponse if processed by Complaints Agent
        summary: Summary of the processing result
    """
    is_complaint: bool
    summary: str
    complaint: Optional[Complaint] = None
    complaint_response: Optional[ComplaintResponse] = None

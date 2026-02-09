from dataclasses import dataclass, field
from typing import Dict, List

from .base import Serializable


@dataclass
class ComplaintCriteria(Serializable):
    """Business defined criteria for complaint classification.
    
    Attributes:
        keywords: Keywords indicating complaints
        sentiment_indicators: Negative sentiment phrases
        severity_thresholds: Thresholds for severity levels
    """
    keywords: List[str] = field(default_factory=list)
    sentiment_indicators: List[str] = field(default_factory=list)
    severity_thresholds: Dict[str, int] = field(default_factory=dict)

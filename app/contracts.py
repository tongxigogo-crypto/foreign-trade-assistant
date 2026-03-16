from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentResult:
    status: str
    notes: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Inquiry:
    sender_email: str
    subject: str
    body: str

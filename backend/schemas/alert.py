from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID

class FraudAlert(BaseModel):
    alert_id: str
    node_id: int
    account_label: str
    risk_score: float
    trigger_reason: str
    triggered_at: str
    status: Literal["unreviewed", "reviewed", "escalated", "false_positive"]

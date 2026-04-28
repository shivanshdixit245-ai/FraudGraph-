import threading
from uuid import uuid4
from datetime import datetime, timedelta
from typing import List, Optional
from ..schemas.alert import FraudAlert

class AlertManager:
    """
    Manages the lifecycle of real-time fraud alerts triggered by model predictions.
    Thread-safe implementation for use across multiple WebSocket and API threads.
    """
    def __init__(self):
        self.alerts: List[FraudAlert] = []
        self.active_node_ids = set() # To prevent duplicate alerts for the same node
        self.lock = threading.Lock()

    def check_and_fire(self, node_id: int, label: str, risk: float, top_shap_feature: str) -> Optional[FraudAlert]:
        """
        Evaluates a node's risk and triggers a new alert if it crosses the threshold.
        """
        if risk > 0.8:
            with self.lock:
                if node_id not in self.active_node_ids:
                    new_alert = FraudAlert(
                        alert_id=str(uuid4()),
                        node_id=node_id,
                        account_label=label,
                        risk_score=float(risk),
                        trigger_reason=top_shap_feature,
                        triggered_at=datetime.now().isoformat(),
                        status="unreviewed"
                    )
                    self.alerts.append(new_alert)
                    self.active_node_ids.add(node_id)
                    return new_alert
        return None

    def get_all(self) -> List[FraudAlert]:
        """
        Returns all alerts, sorted by risk score descending.
        """
        with self.lock:
            return sorted(self.alerts, key=lambda x: x.risk_score, reverse=True)

    def update_status(self, alert_id: str, new_status: str):
        """
        Updates the review status of an existing alert.
        """
        valid_statuses = ["reviewed", "escalated", "false_positive"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
            
        with self.lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.status = new_status
                    return
            raise ValueError(f"Alert ID {alert_id} not found")

    def get_unreviewed_count(self) -> int:
        """
        Returns the number of alerts awaiting review.
        """
        with self.lock:
            return sum(1 for a in self.alerts if a.status == "unreviewed")

    def clear_resolved(self):
        """
        Purges reviewed and false positive alerts that are older than 1 hour.
        """
        one_hour_ago = datetime.now() - timedelta(hours=1)
        with self.lock:
            # We keep unreviewed and recently resolved alerts
            # We also need to remove from active_node_ids so they can re-trigger later if needed
            new_alerts = []
            for a in self.alerts:
                is_resolved = a.status in ["reviewed", "false_positive"]
                triggered_dt = datetime.fromisoformat(a.triggered_at)
                
                if is_resolved and triggered_dt < one_hour_ago:
                    self.active_node_ids.discard(a.node_id)
                    continue
                new_alerts.append(a)
            self.alerts = new_alerts

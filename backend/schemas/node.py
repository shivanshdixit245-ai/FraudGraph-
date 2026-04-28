from pydantic import BaseModel
from typing import List, Optional

class NodeProfile(BaseModel):
    node_id: int
    account_label: str
    risk_score: float
    transaction_count: int
    network_degree: int
    betweenness_centrality: float
    cluster_id: Optional[int]
    is_flagged: bool
    avg_transaction_amount: float
    max_transaction_amount: float
    transaction_velocity_7d: float
    unique_devices: int
    unique_ips: int
    card_prefix: str
    last_updated: str

class TransactionEntry(BaseModel):
    txn_id: int
    counterparty_id: Optional[int]
    counterparty_label: str
    amount: float
    product_code: str
    is_fraud: bool
    timestamp: str

class TransactionHistory(BaseModel):
    node_id: int
    total: int
    page: int
    limit: int
    transactions: List[TransactionEntry]

class DriftDatapoint(BaseModel):
    date: str
    velocity: float
    z_score: float

class DriftResult(BaseModel):
    node_id: int
    baseline_velocity: float
    current_velocity: float
    z_score: float
    is_drifting: bool
    datapoints: List[DriftDatapoint]

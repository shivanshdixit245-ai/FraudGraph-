from pydantic import BaseModel
from typing import List, Optional

class SharedAttributes(BaseModel):
    device_ids: List[str]
    ip_ranges: List[str]
    card_prefixes: List[str]

class ClusterListItem(BaseModel):
    cluster_id: int
    size: int
    cluster_risk: float
    member_node_ids: List[int]
    shared_attributes: SharedAttributes
    created_at: str

class ClusterListResponse(BaseModel):
    total_clusters: int
    clusters: List[ClusterListItem]

class ClusterMember(BaseModel):
    node_id: int
    label: str
    risk: float

class ClusterInternalEdge(BaseModel):
    source: int
    target: int

class ClusterDetailResponse(BaseModel):
    cluster_id: int
    size: int
    cluster_risk: float
    members: List[ClusterMember]
    internal_edges: List[ClusterInternalEdge]
    shared_attributes: SharedAttributes

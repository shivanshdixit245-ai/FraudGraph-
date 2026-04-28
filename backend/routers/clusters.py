from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from ..schemas.cluster import ClusterListResponse, ClusterDetailResponse, ClusterListItem

router = APIRouter()

@router.get("/", response_model=ClusterListResponse)
def get_clusters(
    request: Request,
    min_size: int = Query(2, ge=1),
    min_risk: float = Query(0.0, ge=0.0, le=1.0)
):
    """
    Returns identified entity clusters filtered by size and risk thresholds.
    """
    app = request.app
    all_clusters = getattr(app.state, 'clusters', [])
    
    # Filter
    filtered = [
        c for c in all_clusters 
        if c["size"] >= min_size and c["cluster_risk"] >= min_risk
    ]
    
    # Process for response
    results = []
    for c in filtered:
        results.append({
            "cluster_id": c["cluster_id"],
            "size": c["size"],
            "cluster_risk": c["cluster_risk"],
            "member_node_ids": c["member_node_ids"],
            "shared_attributes": c["shared_attributes"],
            "created_at": datetime.now().isoformat() # Mock creation time
        })
        
    return {
        "total_clusters": len(results),
        "clusters": results
    }

@router.get("/{cluster_id}", response_model=ClusterDetailResponse)
def get_cluster_detail(cluster_id: int, request: Request):
    """
    Returns detailed information for a specific cluster, including its members 
    and the internal graph structure connecting them.
    """
    app = request.app
    all_clusters = getattr(app.state, 'clusters', [])
    data = getattr(app.state, 'data', None)
    scores = getattr(app.state, 'scores', None)
    
    # Find the cluster
    cluster = next((c for c in all_clusters if c["cluster_id"] == cluster_id), None)
    if not cluster:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        
    member_ids = set(cluster["member_node_ids"])
    
    # Build members list with labels and risks
    members = []
    for mid in member_ids:
        members.append({
            "node_id": mid,
            "label": f"ACC-{mid}",
            "risk": float(scores[mid]) if scores is not None else 0.0
        })
        
    # Find internal edges (edges between members of this cluster)
    internal_edges = []
    if data is not None:
        edge_index = data.edge_index.cpu().numpy()
        for i in range(edge_index.shape[1]):
            u, v = int(edge_index[0, i]), int(edge_index[1, i])
            if u in member_ids and v in member_ids:
                internal_edges.append({"source": u, "target": v})
                
    return {
        "cluster_id": cluster["cluster_id"],
        "size": cluster["size"],
        "cluster_risk": cluster["cluster_risk"],
        "members": members,
        "internal_edges": internal_edges,
        "shared_attributes": cluster["shared_attributes"]
    }

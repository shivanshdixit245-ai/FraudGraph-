from datetime import datetime
from fastapi import APIRouter, Request, Query

router = APIRouter()

@router.get("/")
async def get_centrality_leaderboard(
    request: Request,
    top_n: int = Query(10, ge=1, le=100),
    metric: str = Query("betweenness", regex="^(betweenness|eigenvector)$")
):
    """
    Returns the top nodes ranked by graph centrality metrics.
    Useful for identifying 'Money Mules' (Betweenness) and 
    'Network Influencers' (Eigenvector).
    """
    app = request.app
    centrality_results = getattr(app.state, 'centrality_map', {})
    
    # Extract requested metric list
    # Results are already pre-computed and stored in app state
    results = centrality_results.get(metric, [])
    
    # Filter to top_n
    limited_results = results[:top_n]
    
    return {
        "computed_at": datetime.now().isoformat(), # Ideally track real compute time
        "metric": metric,
        "results": limited_results
    }

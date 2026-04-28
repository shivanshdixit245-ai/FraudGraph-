import time
from fastapi import APIRouter, Request

router = APIRouter()

# Module level start time for uptime calculation
START_TIME = time.time()

@router.get("/")
async def health(request: Request):
    """
    Returns API health status, model information, and system uptime.
    """
    app = request.app
    
    # Extract info from app state
    model_loaded = hasattr(app.state, 'model')
    demo_mode = not hasattr(app.state, 'data') and hasattr(app.state, 'demo_nodes')
    
    node_count = 0
    if hasattr(app.state, 'data'):
        node_count = app.state.data.num_nodes
    elif hasattr(app.state, 'demo_nodes'):
        node_count = len(app.state.demo_nodes)
        
    uptime = time.time() - START_TIME
    
    return {
        "status": "ok",
        "mode": "demo" if demo_mode else "live",
        "model_loaded": model_loaded,
        "demo_mode": demo_mode,
        "node_count": node_count,
        "uptime_seconds": round(uptime, 2)
    }

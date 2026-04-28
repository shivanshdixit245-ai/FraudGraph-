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
    node_count = app.state.data.num_nodes if hasattr(app.state, 'data') else 0
    uptime = time.time() - START_TIME
    
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "node_count": node_count,
        "uptime_seconds": round(uptime, 2)
    }

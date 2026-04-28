import random
from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/inject")
def inject_fraud_ring(request: Request):
    """
    Simulates a coordinated fraud ring attack for demo purposes.
    Injects a pre-defined risk escalation schedule for 4 nodes.
    """
    app = request.app
    scores = getattr(app.state, 'scores', None)
    
    if scores is None:
        raise HTTPException(status_code=500, detail="Risk scores not initialized")

    # 1. Select 4 nodes with currently low risk (< 0.3)
    # Convert to list if it's a tensor/ndarray
    all_scores = scores.tolist() if hasattr(scores, 'tolist') else scores
    low_risk_nodes = [i for i, s in enumerate(all_scores) if s < 0.3]
    
    if len(low_risk_nodes) < 4:
        # Fallback to any nodes if not enough low risk nodes
        low_risk_nodes = list(range(min(4, len(all_scores))))
    
    target_nodes = random.sample(low_risk_nodes, 4)
    n0, n1, n2, n3 = target_nodes

    # 2. Define the 8-cycle schedule
    # Each item represents the score overrides for that cycle
    schedule = [
        {n0: 0.35},                 # Cycle 1
        {n0: 0.60},                 # Cycle 2
        {n0: 0.85, n1: 0.40},       # Cycle 3: n0 crosses threshold
        {n0: 0.95, n1: 0.65},       # Cycle 4
        {n1: 0.88, n2: 0.50},       # Cycle 5: n1 crosses
        {n1: 0.98, n2: 0.85},       # Cycle 6: n2 crosses
        {n2: 0.95, n3: 0.60},       # Cycle 7
        {n3: 0.92}                  # Cycle 8: n3 crosses
    ]

    # 3. Store in app state for the WebSocket loop to pick up
    app.state.inject_schedule = schedule
    app.state.inject_step = 0
    
    print(f"DEBUG: Fraud Ring Injected! Targets: {target_nodes}")
    
    return {
        "injected": True,
        "affected_nodes": target_nodes,
        "duration_seconds": 12, # 8 cycles * 1.5s
        "message": "Fraud ring injection sequence started"
    }

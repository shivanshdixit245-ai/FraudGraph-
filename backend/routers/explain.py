from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from ..ml.explainer import explain_node

router = APIRouter()

@router.get("/{node_id}")
def get_node_explanation(node_id: int, request: Request):
    """
    Returns SHAP-based feature importance for a specific node's fraud score.
    Uses an in-memory TTL cache to optimize performance for high-traffic nodes.
    """
    app = request.app
    model = getattr(app.state, 'model', None)
    data = getattr(app.state, 'data', None)
    cache = getattr(app.state, 'explain_cache', None)

    if model is None or data is None:
        raise HTTPException(status_code=503, detail="AI Explainer service not initialized. Model loading in progress.")

    if node_id < 0 or node_id >= data.num_nodes:
        raise HTTPException(status_code=404, detail="Node not found")

    # 1. Check Cache
    cached_result = cache.get(node_id) if cache else None
    if cached_result:
        # Update the metadata for the cached response
        cached_result["cached"] = True
        return cached_result

    # 2. Compute Explanation (Heavy Operation)
    try:
        # explain_node already returns the dict structure: 
        # { node_id, base_value, predicted_value, shap_values: [...] }
        result = explain_node(model, data, node_id)
        
        # 3. Add Metadata
        result["account_label"] = f"ACC-{node_id}"
        result["cached"] = False
        result["computed_at"] = datetime.now().isoformat()
        
        # 4. Save to Cache
        if cache:
            cache.set(node_id, result)
            
        return result
        
    except Exception as e:
        print(f"SHAP explanation failed for node {node_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI explanation: {str(e)}")

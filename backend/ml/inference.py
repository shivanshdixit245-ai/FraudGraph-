import torch
import numpy as np

def score_all_nodes(model, data):
    """
    Runs the FraudGNN model in inference mode to generate risk scores for the entire graph.
    
    Args:
        model: Trained FraudGNN model.
        data: Graph Data object.
        
    Returns:
        np.ndarray: float32 array of risk scores for every node [N,].
    """
    model.eval()
    with torch.no_grad():
        # Handle edge weights if they exist in the data object
        edge_weight = data.edge_weight if hasattr(data, 'edge_weight') else None
        
        # Forward pass
        # model(x, edge_index, edge_weight)
        out = model(data.x, data.edge_index, edge_weight)
        
        # Flatten to 1D and convert to numpy
        return out.view(-1).cpu().numpy().astype(np.float32)

def get_top_fraud_nodes(scores, threshold=0.8):
    """
    Identifies nodes with risk scores above a specified threshold.
    
    Args:
        scores: Numpy array of risk scores.
        threshold: Score threshold for flagging (default 0.8).
        
    Returns:
        List[int]: Sorted list of node indices by risk score (descending).
    """
    # Find indices where score > threshold
    flagged_indices = np.where(scores > threshold)[0]
    
    # Sort these indices by the actual scores in descending order
    sorted_indices = flagged_indices[np.argsort(scores[flagged_indices])[::-1]]
    
    return sorted_indices.tolist()

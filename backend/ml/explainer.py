import torch
import shap
import numpy as np
import time
from ml.model import score_nodes

# Global cache for the explainer object
_EXPLAINER_CACHE = None

# Result cache with TTL: { node_id: (result_dict, timestamp) }
_RESULT_CACHE = {}
CACHE_TTL = 30 # seconds

# Feature names mapping to the 11 features in graph_builder.py
# Order: amt_mean, amt_std, amt_max, count, velocity, card_usage, 
#        addr_match, distance, email_risk, device_count, ip_count
FEATURE_NAMES = [
    "Avg Amount", "Amount Std Dev", "Max Amount", 
    "Transaction Count", "Transaction Velocity", "Card Usage",
    "Address Match Rate", "Distance Feature", "Email Risk",
    "Device Count", "IP Count"
]

def build_explainer(model, data, background_size=50):
    """
    Builds a SHAP KernelExplainer for the FraudGNN model.
    Treats the GNN as a black-box function that takes node features and returns risk scores.
    
    Args:
        model: The trained FraudGNN model.
        data: The graph Data object.
        background_size: Number of nodes to sample for the background distribution.
        
    Returns:
        shap.KernelExplainer: The initialized explainer.
    """
    global _EXPLAINER_CACHE
    if _EXPLAINER_CACHE is not None:
        return _EXPLAINER_CACHE

    model.eval()
    
    # Sample background nodes for KernelSHAP
    # We use the feature matrix of these nodes as the background
    bg_indices = np.random.choice(data.num_nodes, min(background_size, data.num_nodes), replace=False)
    background_data = data.x[bg_indices].cpu().numpy()

    # Define the black-box prediction function
    def predict_fn(x_pert):
        """
        Prediction function for perturbed features.
        Since it's a GNN, perturbing one node technically affects neighbors,
        but KernelSHAP treats features as independent for the target node.
        """
        # x_pert is [batch_size, 11]
        results = []
        with torch.no_grad():
            for i in range(x_pert.shape[0]):
                # Create a copy of the graph or just use a shared one?
                # For efficiency, we only want to score the specific perturbed input.
                # However, GNN needs the graph structure. 
                # We can simulate the node-level prediction by passing the perturbed features.
                perturbed_x = torch.tensor(x_pert[i:i+1], dtype=torch.float).to(data.x.device)
                
                # We need to run the GNN on a graph where the target node has these features.
                # Since we are explaining a specific node_id later, this fn is called by SHAP.
                # KernelSHAP calls this with a batch of perturbations for the features of THE target node.
                # So we need to know WHICH node we are explaining. 
                # KernelSHAP doesn't pass the node_id to the predict_fn directly.
                # We'll set a module-level variable for the current_node_id.
                
                target_id = getattr(predict_fn, 'target_id', 0)
                
                # Efficiently update only the target node's features
                original_x = data.x[target_id].clone()
                data.x[target_id] = perturbed_x
                
                # Run full graph forward
                edge_weight = data.edge_weight if hasattr(data, 'edge_weight') else None
                out = model(data.x, data.edge_index, edge_weight)
                score = out[target_id].item()
                
                # Restore original features
                data.x[target_id] = original_x
                results.append(score)
                
        return np.array(results)

    _EXPLAINER_CACHE = shap.KernelExplainer(predict_fn, background_data)
    return _EXPLAINER_CACHE

def explain_node(model, data, node_id, feature_names=None):
    """
    Calculates SHAP values for a specific node's fraud score.
    
    Args:
        model: Trained FraudGNN model.
        data: Graph Data object.
        node_id: Index of the node to explain.
        feature_names: List of human-readable feature names.
        
    Returns:
        dict: Explanation results including top 5 features.
    """
    # 1. Check Cache
    current_time = time.time()
    if node_id in _RESULT_CACHE:
        result, timestamp = _RESULT_CACHE[node_id]
        if current_time - timestamp < CACHE_TTL:
            return result

    # 2. Build/Get Explainer
    explainer = build_explainer(model, data)
    
    # 3. Set the target_id for the predict_fn so it knows which node to perturb
    explainer.model.target_id = node_id
    
    # 4. Run SHAP
    # We explain the feature vector of the target node
    node_features = data.x[node_id].cpu().numpy().reshape(1, -1)
    
    # nsamples controls the accuracy vs speed
    shap_values = explainer.shap_values(node_features, nsamples=50, silent=True)
    
    # For KernelSHAP with single output, shap_values is a list [array(1, 11)]
    if isinstance(shap_values, list):
        vals = shap_values[0].flatten()
    else:
        vals = shap_values.flatten()
        
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = base_value[0]
        
    predicted_value = base_value + np.sum(vals)
    
    # 5. Format results
    names = feature_names or FEATURE_NAMES
    
    features_list = []
    for i in range(len(names)):
        features_list.append({
            "feature": names[i],
            "value": float(vals[i]),
            "direction": "positive" if vals[i] >= 0 else "negative"
        })
        
    # Sort by absolute value descending and take top 5
    features_list.sort(key=lambda x: abs(x["value"]), reverse=True)
    top_5 = features_list[:5]
    
    result = {
        "node_id": int(node_id),
        "base_value": float(base_value),
        "predicted_value": float(predicted_value),
        "shap_values": top_5
    }
    
    # 6. Cache result
    _RESULT_CACHE[node_id] = (result, current_time)
    
    return result

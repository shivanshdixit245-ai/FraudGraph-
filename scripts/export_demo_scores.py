import os
import torch
import json
import pandas as pd
import numpy as np
import networkx as nx
from datetime import datetime

# Import backend modules
import sys
sys.path.append(os.getcwd())

from backend.ml.model import load_model
from backend.ml.inference import score_all_nodes
from backend.ml.entity_resolver import resolve_entities
from backend.ml.centrality import compute_centrality
from backend.ml.drift_detector import detect_all_drift
from backend.ml.explainer import explain_node
from backend.routers.metrics import compute_model_metrics

def export():
    print("Starting Demo Scores Export...")
    
    # 1. Load Data
    data_path = "data/processed/graph_data.pt"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run preprocess.py first.")
        return
    
    checkpoint = torch.load(data_path)
    data = checkpoint['data']
    scaler = checkpoint['scaler']
    
    # 2. Load Model
    model_path = "backend/models/fraudgnn_v1.pt"
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found. Train the model first.")
        return
    
    model = load_model(model_path, in_channels=data.num_node_features)
    
    # 3. Generate Everything
    print("Scoring all nodes...")
    scores = score_all_nodes(model, data)
    risk_dict = {i: float(scores[i]) for i in range(len(scores))}
    
    print("Building NetworkX graph...")
    G = nx.Graph()
    edge_index = data.edge_index.cpu().numpy()
    for i in range(edge_index.shape[1]):
        G.add_edge(int(edge_index[0, i]), int(edge_index[1, i]))
    
    print("Running entity resolution...")
    try:
        transactions_df = pd.read_csv("data/raw/train_transaction.csv", nrows=10000)
    except:
        transactions_df = pd.DataFrame(columns=['card1', 'TransactionDT', 'DeviceInfo', 'id_30', 'addr1'])
    
    nodes_for_ml = [{"id": i, "risk": risk_dict[i]} for i in range(data.num_nodes)]
    clusters = resolve_entities(nodes_for_ml, transactions_df)
    
    print("Computing centrality...")
    centrality_map = compute_centrality(G, risk_dict, top_n=100)
    
    print("Detecting drift...")
    drift_map = detect_all_drift([n["id"] for n in nodes_for_ml], transactions_df)
    
    print("Computing metrics...")
    metrics = compute_model_metrics(model, data)
    
    print("Building nodes and edges for export...")
    nodes_list = []
    for i in range(data.num_nodes):
        label = f"ACC-{1000 + i}"
        risk = float(scores[i])
        level = "high" if risk > 0.8 else ("medium" if risk > 0.3 else "low")
        degree = int(G.degree[i]) if i in G else 0
        cluster_id = next((c["cluster_id"] for c in clusters if i in c["nodes"]), 0)
        
        # Simple mock positioning for demo graph stability
        x = 400 + 200 * np.cos(2 * np.pi * i / data.num_nodes)
        y = 300 + 200 * np.sin(2 * np.pi * i / data.num_nodes)
        
        # Mock SHAP for instant export
        if risk > 0.8:
            top_shap = {"feature": "Network Degree", "value": 0.28}
        elif risk > 0.3:
            top_shap = {"feature": "Transaction Velocity", "value": 0.15}
        else:
            top_shap = {"feature": "Baseline", "value": 0.05}
            
        nodes_list.append({
            "id": i,
            "label": label,
            "risk": round(risk, 4),
            "level": level,
            "degree": degree,
            "cluster_id": cluster_id,
            "x": round(x, 2),
            "y": round(y, 2),
            "shap": {
                "top_feature": top_shap["feature"],
                "value": round(float(top_shap["value"]), 4)
            }
        })
    
    edges_list = []
    edge_weight = data.edge_weight.cpu().numpy() if hasattr(data, 'edge_weight') and data.edge_weight is not None else [1.0] * edge_index.shape[1]
    
    for i in range(edge_index.shape[1]):
        edges_list.append({
            "source": int(edge_index[0, i]),
            "target": int(edge_index[1, i]),
            "weight": round(float(edge_weight[i]), 2)
        })

    # 4. Save to JSON
    export_data = {
        "metadata": {
            "exported_at": datetime.now().isoformat(),
            "model_version": "fraudgraph-v1.0",
            "node_count": data.num_nodes,
            "metrics": metrics
        },
        "nodes": nodes_list,
        "edges": edges_list,
        "scores": scores.tolist(),
        "clusters": clusters,
        "centrality_map": centrality_map,
        "drift_map": drift_map
    }
    
    output_path = "data/processed/demo_scores.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(export_data, f)
    
    print(f"Success! Demo scores exported to {output_path}")

if __name__ == "__main__":
    export()

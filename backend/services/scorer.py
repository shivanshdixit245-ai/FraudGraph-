import torch
import numpy as np
import networkx as nx
from datetime import datetime
from ml.inference import score_all_nodes
from ml.centrality import get_node_centrality_map
from ml.drift_detector import detect_all_drift

class ScorerService:
    """
    The central intelligence service for FraudGraph. 
    It bridges the machine learning models and the graph algorithms to 
    provide a unified interface for the API layer.
    """
    def __init__(self, model, data, nx_graph, transactions_df, scaler=None):
        self.model = model
        self.data = data
        self.nx_graph = nx_graph
        self.transactions_df = transactions_df
        self.scaler = scaler
        
        # Initial computations
        print("ScorerService: Performing initial scoring and analysis...")
        self.scores = score_all_nodes(model, data)
        self.centrality_map = get_node_centrality_map(nx_graph)
        
        # This will be populated by the main app logic or on demand
        self.clusters = []
        self.drift_map = {}
        
        # Cache for graph positions (reused from graph.py logic)
        self.pos_map = None

    def refresh_scores(self):
        """
        Re-calculates GNN risk scores. Usually called by a background loop.
        """
        self.scores = score_all_nodes(self.model, self.data)
        
        # Recompute drift for all nodes (or a subset)
        # In a real system, we'd only do this if new transactions arrived
        # self.drift_map = detect_all_drift(list(range(self.data.num_nodes)), self.transactions_df)
        return self.scores

    def get_node_profile(self, node_id: int):
        """
        Aggregates all known intelligence for a specific account.
        """
        if node_id < 0 or node_id >= self.data.num_nodes:
            return None
            
        risk = float(self.scores[node_id])
        cent = self.centrality_map.get(node_id, {})
        
        # De-normalize features for real values if scaler is present
        if self.scaler:
            x_raw = self.scaler.inverse_transform(self.data.x[node_id].cpu().numpy().reshape(1, -1))[0]
        else:
            x_raw = self.data.x[node_id].cpu().numpy()

        # Find cluster
        cluster_id = None
        for c in self.clusters:
            if node_id in c["member_node_ids"]:
                cluster_id = c["cluster_id"]
                break

        drift = self.drift_map.get(node_id, {"is_drifting": False})

        return {
            "node_id": node_id,
            "account_label": f"ACC-{node_id}",
            "risk_score": risk,
            "transaction_count": int(x_raw[3]) if len(x_raw) > 3 else 0,
            "network_degree": int(self.nx_graph.degree[node_id]) if node_id in self.nx_graph else 0,
            "betweenness_centrality": float(cent.get('betweenness', 0)),
            "cluster_id": cluster_id,
            "is_flagged": risk > 0.8,
            "is_drifting": drift.get("is_drifting", False),
            "avg_transaction_amount": float(x_raw[0]) if len(x_raw) > 0 else 0.0,
            "max_transaction_amount": float(x_raw[2]) if len(x_raw) > 2 else 0.0,
            "last_updated": datetime.now().isoformat()
        }

    def get_graph_payload(self):
        """
        Prepares a complete graph snapshot for WebSocket broadcasting.
        """
        nodes = []
        # Lazy compute positions if not present
        if self.pos_map is None:
            pos = nx.spring_layout(self.nx_graph, k=0.15, seed=42)
            self.pos_map = {node: [float(c[0] * 500 + 500), float(c[1] * 500 + 500)] for node, c in pos.items()}

        for i in range(self.data.num_nodes):
            risk = float(self.scores[i])
            x, y = self.pos_map.get(i, [500, 500])
            
            cluster_id = None
            for c in self.clusters:
                if i in c["member_node_ids"]:
                    cluster_id = c["cluster_id"]
                    break

            nodes.append({
                "id": i,
                "label": f"ACC-{i}",
                "risk": risk,
                "degree": int(self.nx_graph.degree[i]) if i in self.nx_graph else 0,
                "centrality": float(self.centrality_map.get(i, {}).get('betweenness', 0)),
                "cluster_id": cluster_id,
                "x": x,
                "y": y
            })

        edges = []
        edge_index = self.data.edge_index.cpu().numpy()
        for i in range(edge_index.shape[1]):
            edges.append({
                "source": int(edge_index[0, i]),
                "target": int(edge_index[1, i]),
                "weight": 1.0
            })

        return {
            "type": "graph_update",
            "timestamp": datetime.now().isoformat(),
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": self.data.num_nodes,
                "flagged_nodes": sum(1 for s in self.scores if s > 0.8),
                "avg_risk": float(self.scores.mean()),
                "active_clusters": len(self.clusters)
            }
        }

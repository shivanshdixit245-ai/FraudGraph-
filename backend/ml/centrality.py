import networkx as nx
import numpy as np

def compute_centrality(nx_graph, risk_scores, top_n=10):
    """
    Computes various graph centrality metrics to identify high-risk 'hubs' 
    and money mule accounts.
    
    Args:
        nx_graph: NetworkX graph object.
        risk_scores: Dict of { node_id: risk_score } for all nodes.
        top_n: Number of top nodes to return for betweenness and eigenvector.
        
    Returns:
        dict: Categorized centrality rankings.
    """
    if nx_graph.number_of_nodes() == 0:
        return {"betweenness": [], "eigenvector": [], "high_clustering": []}

    # 1. Betweenness Centrality (Money Mule Indicator)
    # Measures nodes that sit on the most shortest paths
    betweenness = nx.betweenness_centrality(nx_graph, normalized=True)
    
    # 2. Eigenvector Centrality (Network Influence)
    # Measures how well a node is connected to other important nodes
    try:
        # Use risk scores as a hint for the starting vector
        # nstart must have a value for every node
        nstart = {node: risk_scores.get(node, 0.5) for node in nx_graph.nodes()}
        eigenvector = nx.eigenvector_centrality(nx_graph, max_iter=1000, tol=1e-4, nstart=nstart)
    except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
        # Fallback to degree centrality if convergence fails (common in sparse/disconnected graphs)
        eigenvector = nx.degree_centrality(nx_graph)

    # 3. Clustering Coefficient (Fraud Ring Indicator)
    # Measures how interconnected a node's neighbors are
    clustering = nx.clustering(nx_graph)

    # 4. Process and Rank Results
    def get_ranked_list(metric_dict):
        sorted_nodes = sorted(metric_dict.items(), key=lambda x: x[1], reverse=True)
        ranked = []
        for i, (node_id, val) in enumerate(sorted_nodes[:top_n]):
            ranked.append({
                "rank": i + 1,
                "node_id": node_id,
                "label": f"ACC-{node_id}", # Heuristic label
                "centrality": float(val),
                "risk": float(risk_scores.get(node_id, 0))
            })
        return ranked

    high_clustering = []
    for node_id, coeff in clustering.items():
        if coeff > 0.7:
            high_clustering.append({
                "node_id": node_id,
                "clustering_coeff": float(coeff),
                "risk": float(risk_scores.get(node_id, 0))
            })

    return {
        "betweenness": get_ranked_list(betweenness),
        "eigenvector": get_ranked_list(eigenvector),
        "high_clustering": high_clustering
    }

def get_node_centrality_map(nx_graph):
    """
    Calculates centrality metrics for every node in the graph for profile enrichment.
    """
    if nx_graph.number_of_nodes() == 0:
        return {}
        
    bw = nx.betweenness_centrality(nx_graph, normalized=True)
    
    try:
        ev = nx.eigenvector_centrality(nx_graph, max_iter=500, tol=1e-3)
    except:
        ev = nx.degree_centrality(nx_graph)
        
    cl = nx.clustering(nx_graph)
    
    node_map = {}
    for node in nx_graph.nodes():
        node_map[node] = {
            "betweenness": float(bw.get(node, 0)),
            "eigenvector": float(ev.get(node, 0)),
            "clustering": float(cl.get(node, 0))
        }
    return node_map

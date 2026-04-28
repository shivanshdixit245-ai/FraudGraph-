import networkx as nx
from networkx.algorithms.community import louvain_communities
import pandas as pd
import numpy as np

def resolve_entities(graph_nodes, transactions_df):
    """
    Identifies clusters of accounts (fraud rings) by analyzing shared signals 
    such as devices, IPs, and card metadata.
    
    Args:
        graph_nodes: List of dicts or Data object nodes with 'id' and 'risk'.
        transactions_df: The raw transactions DataFrame.
        
    Returns:
        list: List of cluster objects sorted by risk.
    """
    # 1. Build the Entity Graph
    G = nx.Graph()
    
    # Filter transactions to only include nodes in our graph
    # (graph_nodes might be a subset of total card1s)
    node_ids = [n['id'] if isinstance(n, dict) else n for n in graph_nodes]
    node_risks = {n['id']: n.get('risk', 0) for n in graph_nodes if isinstance(n, dict)}
    
    df = transactions_df[transactions_df['card1'].isin(node_ids)].copy()
    
    # Pre-process signals
    # Card Prefix (first 4 digits of card1)
    df['card_prefix'] = df['card1'].astype(str).str[:4]
    
    # IP Range Proxy (if id_30 is used for IP, we take the prefix)
    # Since we don't have real IPs, we'll use addr1 as a proxy for IP clustering 
    # but the logic is generic.
    if 'id_30' in df.columns:
        df['ip_signal'] = df['id_30'].astype(str)
    else:
        df['ip_signal'] = df['addr1'].astype(str)

    # 2. Add edges for shared signals
    def add_shared_edges(df, col, weight):
        if col not in df.columns: return
        # Group cards by shared attribute
        shared = df[df[col].notna()].groupby(col)['card1'].apply(set).tolist()
        for group in shared:
            if len(group) < 2: continue
            cards = list(group)
            for i in range(len(cards)):
                for j in range(i + 1, len(cards)):
                    # Update edge weight if exists, else create
                    if G.has_edge(cards[i], cards[j]):
                        G[cards[i]][cards[j]]['weight'] += weight
                    else:
                        G.add_edge(cards[i], cards[j], weight=weight)

    # Weights: Device=1.0, IP=0.8, Card Prefix=0.6
    add_shared_edges(df, 'DeviceInfo', 1.0)
    add_shared_edges(df, 'ip_signal', 0.8)
    add_shared_edges(df, 'card_prefix', 0.6)

    if G.number_of_nodes() == 0:
        return []

    # 3. Louvain Community Detection
    communities = louvain_communities(G, weight='weight', seed=42)
    
    # 4. Process and Filter Clusters
    clusters = []
    for i, comm in enumerate(communities):
        member_ids = list(comm)
        if len(member_ids) < 2: continue # Skip singletons
        
        # Calculate cluster metrics
        cluster_risk = max([node_risks.get(mid, 0) for mid in member_ids])
        
        # Collect shared attributes for the cluster
        cluster_df = df[df['card1'].isin(member_ids)]
        
        shared_attributes = {
            "device_ids": cluster_df['DeviceInfo'].dropna().unique().tolist()[:5],
            "ip_ranges": cluster_df['ip_signal'].dropna().unique().tolist()[:5],
            "card_prefixes": cluster_df['card_prefix'].dropna().unique().tolist()[:5]
        }
        
        clusters.append({
            "cluster_id": i + 1,
            "member_node_ids": member_ids,
            "size": len(member_ids),
            "cluster_risk": float(cluster_risk),
            "shared_attributes": shared_attributes
        })
        
    # Sort by risk descending
    clusters.sort(key=lambda x: x["cluster_risk"], reverse=True)
    
    return clusters

def get_node_cluster_map(clusters):
    """
    Creates a reverse lookup map for nodes to their cluster IDs.
    
    Args:
        clusters: The list of cluster objects.
        
    Returns:
        dict: { node_id: cluster_id }
    """
    node_map = {}
    for cluster in clusters:
        for node_id in cluster["member_node_ids"]:
            node_map[node_id] = cluster["cluster_id"]
    return node_map

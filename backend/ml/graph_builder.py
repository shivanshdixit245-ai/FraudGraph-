import pandas as pd
import numpy as np
import torch
from torch_geometric.data import Data
from sklearn.preprocessing import StandardScaler

def build_fraud_graph(transaction_csv, identity_csv=None, nrows=10000):
    """
    Loads IEEE-CIS fraud dataset and builds a PyTorch Geometric Data object.
    
    Features (11):
    - transaction_amt_mean, transaction_amt_std, transaction_amt_max
    - transaction_count, transaction_velocity, card_usage_count
    - addr_match_rate, distance_feat, email_domain_risk
    - device_count, ip_count
    """
    
    print(f"Loading {nrows} rows from {transaction_csv}...")
    df_trans = pd.read_csv(transaction_csv, nrows=nrows)
    
    if identity_csv:
        print(f"Merging with identity data from {identity_csv}...")
        df_id = pd.read_csv(identity_csv)
        df = pd.merge(df_trans, df_id, on='TransactionID', how='left')
    else:
        df = df_trans
    
    # Define email risk mapping (heuristic)
    email_risk = {
        'gmail.com': 0.02, 'hotmail.com': 0.05, 'outlook.com': 0.05,
        'yahoo.com': 0.04, 'anonymous.com': 0.15, 'protonmail.com': 0.30,
        'mail.com': 0.20, 'me.com': 0.03, 'icloud.com': 0.03
    }
    df['email_risk_score'] = df['P_emaildomain'].map(email_risk).fillna(0.1)

    # Group by card1 (Account)
    agg_funcs = {
        'TransactionAmt': ['mean', 'std', 'max', 'count'],
        'TransactionDT': lambda x: (x.max() - x.min()) / (len(x) if len(x) > 0 else 1),
        'addr1': lambda x: x.nunique(),
        'dist1': 'mean',
        'email_risk_score': 'mean',
        'isFraud': 'max'
    }
    
    # Identity features if available
    if 'DeviceInfo' in df.columns:
        agg_funcs['DeviceInfo'] = lambda x: x.nunique()
    if 'id_30' in df.columns:
        agg_funcs['id_30'] = lambda x: x.nunique()
    
    print("Aggregating features by card1...")
    node_groups = df.groupby('card1')
    
    # Build feature table
    node_features = pd.DataFrame()
    node_features['transaction_amt_mean'] = node_groups['TransactionAmt'].mean()
    node_features['transaction_amt_std'] = node_groups['TransactionAmt'].std().fillna(0)
    node_features['transaction_amt_max'] = node_groups['TransactionAmt'].max()
    node_features['transaction_count'] = node_groups['TransactionID'].count()
    node_features['transaction_velocity'] = node_groups['TransactionDT'].apply(lambda x: (x.max() - x.min()) / (len(x) if len(x) > 0 else 1))
    node_features['card_usage_count'] = node_features['transaction_count'] # Card usage is count
    
    # Addr match rate (proxy: count of unique addr1 / transaction count)
    # Higher diversity in addr1 for one card might indicate fraud or shared card
    node_features['addr_match_rate'] = node_groups.apply(lambda x: (x['addr1'] == x['addr2']).mean() if 'addr2' in x else 0.5)
    
    node_features['distance_feat'] = node_groups['dist1'].mean().fillna(0)
    node_features['email_domain_risk'] = node_groups['email_risk_score'].mean()
    
    # Device and IP counts (fill with 0 if missing)
    if 'DeviceInfo' in df.columns:
        node_features['device_count'] = node_groups['DeviceInfo'].nunique()
    else:
        node_features['device_count'] = 0
        
    if 'id_30' in df.columns:
        node_features['ip_count'] = node_groups['id_30'].nunique()
    else:
        node_features['ip_count'] = 0

    # Ensure we have exactly 11 features
    expected_cols = [
        'transaction_amt_mean', 'transaction_amt_std', 'transaction_amt_max',
        'transaction_count', 'transaction_velocity', 'card_usage_count',
        'addr_match_rate', 'distance_feat', 'email_domain_risk',
        'device_count', 'ip_count'
    ]
    node_features = node_features[expected_cols]
    
    # Fill NaN with median
    node_features = node_features.fillna(node_features.median())
    
    # Scale features
    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(node_features)
    x = torch.tensor(x_scaled, dtype=torch.float)
    
    # Labels
    y = torch.tensor(node_groups['isFraud'].max().values, dtype=torch.long)
    
    # Build Edges
    # Edge weights: Device=1.0, IP=0.8, Addr=0.6
    print("Building edges based on shared attributes...")
    card_list = node_features.index.tolist()
    card_to_idx = {card: i for i, card in enumerate(card_list)}
    
    edge_list = []
    edge_weights = []
    
    # Pre-calculate sharing groups for efficiency
    def get_sharing_edges(df, col, weight):
        if col not in df.columns: return []
        shared = df[df[col].notna()].groupby(col)['card1'].apply(set).tolist()
        edges = []
        for group in shared:
            if len(group) < 2: continue
            # Convert cards to indices
            indices = [card_to_idx[c] for c in group if c in card_to_idx]
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    edges.append((indices[i], indices[j]))
                    edges.append((indices[j], indices[i]))
                    edge_weights.extend([weight, weight])
        return edges

    # We use addr1, DeviceInfo, id_30 as sharing attributes
    edge_list.extend(get_sharing_edges(df, 'DeviceInfo', 1.0))
    edge_list.extend(get_sharing_edges(df, 'id_30', 0.8))
    edge_list.extend(get_sharing_edges(df, 'addr1', 0.6))
    
    if not edge_list:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0), dtype=torch.float)
    else:
        # Convert to tensor and remove duplicate edges (summing weights)
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_weights, dtype=torch.float)
    
    # Wrap in Data object
    data = Data(x=x, edge_index=edge_index, edge_weight=edge_attr, y=y)
    
    # Summary
    fraud_count = int(y.sum())
    print("-" * 30)
    print("Graph Build Summary")
    print(f"Nodes (Accounts): {data.num_nodes}")
    print(f"Edges (Shares):   {data.num_edges // 2}")
    print(f"Fraud Nodes:      {fraud_count}")
    print(f"Fraud Ratio:      {fraud_count / data.num_nodes:.4f}")
    print("-" * 30)
    
    return data, scaler

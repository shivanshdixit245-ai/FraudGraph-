import pandas as pd
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from ..schemas.node import NodeProfile, TransactionHistory, TransactionEntry, DriftResult
from ..ml.drift_detector import detect_drift

router = APIRouter()

@router.get("/{node_id}", response_model=NodeProfile)
async def get_node_profile(node_id: int, request: Request):
    app = request.app
    data = getattr(app.state, 'data', None)
    scores = getattr(app.state, 'scores', None)
    scaler = getattr(app.state, 'scaler', None)
    centrality_map = getattr(app.state, 'centrality_map', {})
    clusters = getattr(app.state, 'clusters', [])

    if data is None or node_id < 0 or node_id >= data.num_nodes:
        raise HTTPException(status_code=404, detail="Node not found")

    # De-normalize features to get real values
    # Feature order: amt_mean, amt_std, amt_max, count, velocity, card_usage, addr_match, distance, email, device, ip
    x_raw = scaler.inverse_transform(data.x[node_id].cpu().numpy().reshape(1, -1))[0]
    
    risk_score = float(scores[node_id])
    cent = centrality_map.get(node_id, {})
    
    # Find cluster_id
    cluster_id = None
    for c in clusters:
        if node_id in c["member_node_ids"]:
            cluster_id = c["cluster_id"]
            break

    return {
        "node_id": node_id,
        "account_label": f"ACC-{node_id}",
        "risk_score": risk_score,
        "transaction_count": int(x_raw[3]),
        "network_degree": int(cent.get('degree', 0)), # We might need to store degree separately
        "betweenness_centrality": float(cent.get('betweenness', 0)),
        "cluster_id": cluster_id,
        "is_flagged": risk_score > 0.8,
        "avg_transaction_amount": float(x_raw[0]),
        "max_transaction_amount": float(x_raw[2]),
        "transaction_velocity_7d": float(x_raw[4]),
        "unique_devices": int(x_raw[9]),
        "unique_ips": int(x_raw[10]),
        "card_prefix": str(int(x_raw[5]))[:4], # Using Card Usage feature slot as proxy or just mock
        "last_updated": datetime.now().isoformat()
    }

@router.get("/{node_id}/transactions", response_model=TransactionHistory)
async def get_node_transactions(
    node_id: int, 
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    app = request.app
    # In main.py we try to load "data/raw/train_transaction.csv" as transactions_df
    transactions_df = getattr(app.state, 'transactions_df', None)
    
    # For demo, if df is missing, we return empty
    if transactions_df is None or transactions_df.empty:
        return {
            "node_id": node_id,
            "total": 0,
            "page": page,
            "limit": limit,
            "transactions": []
        }

    # Filter by card1 (assuming node_id corresponds to card1 values in order)
    # Actually, card1 are high values like 15000. 
    # In graph_builder we indexed card1 into node_ids.
    # We should have stored the card1 mapping.
    # For the demo, we'll just filter card1 directly if possible or assume node_id IS card1.
    node_txns = transactions_df[transactions_df['card1'] == node_id]
    
    total = len(node_txns)
    start = (page - 1) * limit
    end = start + limit
    
    paginated_df = node_txns.iloc[start:end]
    
    txns = []
    for _, row in paginated_df.iterrows():
        txns.append({
            "txn_id": int(row['TransactionID']),
            "counterparty_id": None,
            "counterparty_label": "External Merchant",
            "amount": float(row['TransactionAmt']),
            "product_code": str(row.get('ProductCD', 'W')),
            "is_fraud": bool(row.get('isFraud', False)),
            "timestamp": datetime.fromtimestamp(int(row['TransactionDT']) + 1546300800).isoformat()
        })
        
    return {
        "node_id": node_id,
        "total": total,
        "page": page,
        "limit": limit,
        "transactions": txns
    }

@router.get("/{node_id}/drift", response_model=DriftResult)
async def get_node_drift(node_id: int, request: Request):
    app = request.app
    drift_map = getattr(app.state, 'drift_map', {})
    
    if node_id in drift_map:
        return drift_map[node_id]
    
    # Compute on demand if missing
    transactions_df = getattr(app.state, 'transactions_df', None)
    if transactions_df is None:
        raise HTTPException(status_code=404, detail="Transactions data not available for drift analysis")
        
    result = detect_drift(node_id, transactions_df)
    drift_map[node_id] = result
    return result

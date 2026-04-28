import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def detect_drift(node_id, transactions_df, window_days=7):
    """
    Detects behavioral drift for a specific account by comparing recent 
    transaction velocity against a historical baseline within a window.
    
    Args:
        node_id: The account ID (card1) to check.
        transactions_df: DataFrame containing TransactionDT and card1.
        window_days: Number of days to analyze (default 7).
        
    Returns:
        dict: Drift results including daily datapoints.
    """
    # 1. Filter transactions for the specific node
    node_df = transactions_df[transactions_df['card1'] == node_id]
    
    # Handle sparse data
    if len(node_df) < 3:
        # Return a flat response for sparse data
        return {
            "node_id": int(node_id),
            "baseline_velocity": 0.0,
            "current_velocity": 0.0,
            "z_score": 0.0,
            "is_drifting": False,
            "datapoints": [
                {"date": f"Day {i+1}", "velocity": 0.0, "z_score": 0.0} 
                for i in range(window_days)
            ]
        }

    # 2. Convert TransactionDT to relative days
    # IEEE-CIS TransactionDT is in seconds. Let's bucket by day (86400 seconds)
    max_dt = transactions_df['TransactionDT'].max()
    min_dt_in_window = max_dt - (window_days * 86400)
    
    # Calculate daily velocity (counts per day)
    # We create a range of days for the window
    start_day = int(min_dt_in_window // 86400)
    end_day = int(max_dt // 86400)
    days = list(range(start_day + 1, end_day + 1))
    
    daily_velocity = []
    for day in days:
        day_start = day * 86400
        day_end = (day + 1) * 86400
        count = len(node_df[(node_df['TransactionDT'] >= day_start) & (node_df['TransactionDT'] < day_end)])
        daily_velocity.append(count)
    
    # Ensure we have exactly window_days (pad if necessary, though logic above handles it)
    daily_velocity = daily_velocity[-window_days:]
    if len(daily_velocity) < window_days:
        daily_velocity = [0] * (window_days - len(daily_velocity)) + daily_velocity

    # 3. Compute Baseline and Current
    # Split: First 70% (baseline), Last 30% (current)
    split_idx = int(window_days * 0.7)
    baseline_vals = daily_velocity[:split_idx]
    current_vals = daily_velocity[split_idx:]
    
    baseline_mean = np.mean(baseline_vals)
    baseline_std = np.std(baseline_vals)
    current_mean = np.mean(current_vals)
    
    # 4. Calculate Z-Score
    z_score = (current_mean - baseline_mean) / (baseline_std + 1e-8)
    is_drifting = abs(z_score) > 2.0
    
    # 5. Build Datapoints
    datapoints = []
    for i, vel in enumerate(daily_velocity):
        # Local z-score for that specific day relative to baseline
        day_z = (vel - baseline_mean) / (baseline_std + 1e-8)
        datapoints.append({
            "date": f"Day {i+1}",
            "velocity": float(vel),
            "z_score": float(day_z)
        })
        
    return {
        "node_id": int(node_id),
        "baseline_velocity": float(baseline_mean),
        "current_velocity": float(current_mean),
        "z_score": float(z_score),
        "is_drifting": bool(is_drifting),
        "datapoints": datapoints
    }

def detect_all_drift(graph_nodes, transactions_df):
    """
    Batch process drift detection for all nodes in the graph.
    
    Args:
        graph_nodes: List of account IDs (node IDs).
        transactions_df: The full transaction DataFrame.
        
    Returns:
        dict: Mapping of node_id to drift_result.
    """
    results = {}
    for node_id in graph_nodes:
        results[node_id] = detect_drift(node_id, transactions_df)
    return results

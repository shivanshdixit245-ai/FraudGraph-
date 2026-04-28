import pytest
import pandas as pd
import torch
import os
from ml.graph_builder import build_fraud_graph

def test_returns_pyg_data(tmp_path):
    # Create mock CSV files
    tx_path = tmp_path / "tx.csv"
    tx_data = pd.DataFrame({
        'TransactionID': range(10),
        'TransactionAmt': [100.0] * 10,
        'card1': [1001, 1002, 1001, 1003, 1004, 1002, 1005, 1001, 1006, 1007],
        'TransactionDT': range(10),
        'ProductCD': ['W'] * 10,
        'isFraud': [0] * 9 + [1],
        'addr1': [191] * 10,
        'dist1': [10.0] * 10,
        'P_emaildomain': ['gmail.com'] * 10,
        'card2': [100.0] * 10 # Adding one more card feat for aggregation
    })
    tx_data.to_csv(tx_path, index=False)
    
    data, scaler = build_fraud_graph(str(tx_path), nrows=10)
    
    assert hasattr(data, 'x')
    assert hasattr(data, 'edge_index')
    assert hasattr(data, 'y')

def test_feature_shape(tmp_path):
    tx_path = tmp_path / "tx.csv"
    tx_data = pd.DataFrame({
        'TransactionID': range(5),
        'TransactionAmt': [50.0] * 5,
        'card1': [1, 2, 1, 3, 4],
        'TransactionDT': range(5),
        'isFraud': [0] * 5,
        'addr1': [100] * 5,
        'dist1': [10.0] * 5,
        'P_emaildomain': ['gmail.com'] * 5
    })
    tx_data.to_csv(tx_path, index=False)
    
    data, scaler = build_fraud_graph(str(tx_path), nrows=5)
    # Target feature count is 11 as per requirements
    assert data.x.shape[1] == 11

def test_no_nan(tmp_path):
    tx_path = tmp_path / "tx.csv"
    tx_data = pd.DataFrame({
        'TransactionID': range(5),
        'TransactionAmt': [50.0, None, 20.0, 10.0, None], # Mix in some NaNs
        'card1': [1, 2, 1, 3, 4],
        'TransactionDT': range(5),
        'isFraud': [0, 0, 0, 1, 0],
        'addr1': [100, 100, None, 100, 100],
        'dist1': [None, 10.0, 10.0, 10.0, 10.0],
        'P_emaildomain': ['gmail.com', 'yahoo.com', None, 'gmail.com', 'gmail.com']
    })
    tx_data.to_csv(tx_path, index=False)
    
    data, scaler = build_fraud_graph(str(tx_path), nrows=5)
    assert not torch.isnan(data.x).any()

def test_edge_bounds(tmp_path):
    tx_path = tmp_path / "tx.csv"
    tx_data = pd.DataFrame({
        'TransactionID': range(5),
        'TransactionAmt': [10.0] * 5,
        'card1': [1, 2, 1, 2, 3], # Will create shared edges
        'TransactionDT': range(5),
        'isFraud': [0] * 5,
        'addr1': [100] * 5, # Shared addr creates edges
        'dist1': [10.0] * 5,
        'P_emaildomain': ['gmail.com'] * 5
    })
    tx_data.to_csv(tx_path, index=False)
    
    data, scaler = build_fraud_graph(str(tx_path), nrows=5)
    if data.edge_index.numel() > 0:
        assert data.edge_index.max() < data.x.shape[0]

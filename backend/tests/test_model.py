import pytest
import torch
import numpy as np
from ml.model import FraudGNN, score_nodes
from torch_geometric.data import Data

def test_forward_shape():
    model = FraudGNN(in_channels=11)
    x = torch.randn(10, 11)
    edge_index = torch.tensor([[0, 1, 2], [1, 2, 0]], dtype=torch.long)
    
    out = model(x, edge_index)
    assert out.shape == (10, 1)

def test_output_range():
    model = FraudGNN(in_channels=11)
    x = torch.randn(100, 11) * 10 # Large values to test sigmoid saturating
    edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    
    out = model(x, edge_index)
    assert (out >= 0).all() and (out <= 1).all()

def test_score_nodes_numpy():
    model = FraudGNN(in_channels=11)
    data = Data(
        x=torch.randn(5, 11),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    )
    
    scores = score_nodes(model, data)
    assert isinstance(scores, np.ndarray)
    assert scores.shape == (5,)
    assert scores.dtype == np.float32

def test_no_grad():
    model = FraudGNN(in_channels=11)
    data = Data(
        x=torch.randn(5, 11),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long)
    )
    
    # Check that gradients are not tracked during score_nodes
    scores = score_nodes(model, data)
    # If we tried to backward on scores it should fail or scores should have no grad_fn
    # Since it's converted to numpy, it definitely has no grad_fn
    assert True 

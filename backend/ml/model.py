import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
import numpy as np

class FraudGNN(nn.Module):
    """
    Graph Attention Network (GAT) for node-level fraud detection.
    Uses multi-head attention to aggregate features from neighboring transaction nodes.
    """
    def __init__(self, in_channels=11):
        super(FraudGNN, self).__init__()
        
        # Layer 1: GATConv with 4 heads, concatenated output
        # In: 11, Out: 64 per head. Concat=True -> 64 * 4 = 256
        self.conv1 = GATConv(in_channels, 64, heads=4, dropout=0.3, concat=True)
        
        # Layer 2: GATConv with 1 head, averaged output
        # In: 256, Out: 64
        self.conv2 = GATConv(256, 64, heads=1, dropout=0.3, concat=False)
        
        # Output layer
        self.fc = nn.Linear(64, 1)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x, edge_index, edge_weight=None):
        """
        Forward pass of the model.
        
        Args:
            x (Tensor): Node feature matrix [N, 11]
            edge_index (Tensor): Graph connectivity [2, E]
            edge_weight (Tensor, optional): Edge weights [E]
            
        Returns:
            Tensor: Risk scores [N, 1]
        """
        # First layer
        x = self.conv1(x, edge_index, edge_attr=edge_weight)
        x = F.elu(x)
        x = self.dropout(x)
        
        # Second layer
        x = self.conv2(x, edge_index, edge_attr=edge_weight)
        x = F.elu(x)
        
        # Output
        x = self.fc(x)
        return torch.sigmoid(x)

def score_nodes(model, data):
    """
    Generates fraud risk scores for all nodes in the provided graph data.
    
    Args:
        model (FraudGNN): Trained model
        data (Data): PyG data object containing x, edge_index, edge_weight
        
    Returns:
        np.ndarray: Array of risk scores in range [0, 1]
    """
    model.eval()
    with torch.no_grad():
        # Pass edge_weight if available
        edge_weight = data.edge_weight if hasattr(data, 'edge_weight') else None
        out = model(data.x, data.edge_index, edge_weight)
        return out.squeeze().cpu().numpy()

def save_model(model, path):
    """
    Saves the model state dictionary to the specified path.
    
    Args:
        model (FraudGNN): Model to save
        path (str): File path for saving
    """
    torch.save(model.state_dict(), path)
    print(f"Model saved to {path}")

def load_model(path, in_channels=11):
    """
    Loads a FraudGNN model from a state dictionary file.
    
    Args:
        path (str): Path to the saved state dict
        in_channels (int): Number of input features
        
    Returns:
        FraudGNN: Model in evaluation mode
    """
    model = FraudGNN(in_channels=in_channels)
    model.load_state_dict(torch.load(path))
    model.eval()
    print(f"Model loaded from {path}")
    return model

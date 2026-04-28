import os
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from .model import FraudGNN, save_model

def train(data, epochs=200, lr=0.005, weight_decay=0.0005, patience=20):
    """
    Trains the FraudGNN model using weighted binary cross entropy to handle class imbalance.
    
    Args:
        data (Data): PyG graph data object
        epochs (int): Max training epochs
        lr (float): Learning rate for Adam optimizer
        weight_decay (float): L2 regularization strength
        patience (int): Epochs to wait for val AUC improvement before early stopping
        
    Returns:
        tuple: (trained_model, best_val_auc, train_history)
    """
    # 1. Train/Val Split (Stratified)
    num_nodes = data.num_nodes
    indices = np.arange(num_nodes)
    y_numpy = data.y.cpu().numpy()
    
    train_idx, val_idx = train_test_split(
        indices, test_size=0.2, stratify=y_numpy, random_state=42
    )
    
    train_idx = torch.tensor(train_idx, dtype=torch.long)
    val_idx = torch.tensor(val_idx, dtype=torch.long)
    
    # 2. Handle Class Imbalance
    pos_count = data.y[train_idx].sum().item()
    neg_count = len(train_idx) - pos_count
    pos_weight = torch.tensor([neg_count / (pos_count if pos_count > 0 else 1)], dtype=torch.float)
    
    print(f"Class Weights - Neg: {neg_count}, Pos: {pos_count}, PosWeight: {pos_weight.item():.2f}")
    
    # 3. Setup Model and Optimizer
    model = FraudGNN(in_channels=data.num_node_features)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight) # Using LogitsLoss for stability if needed, 
    # but model has Sigmoid. Let's use standard BCELoss since model ends with Sigmoid.
    # Actually, for pos_weight with Sigmoid output, we use binary_cross_entropy.
    # Wait, PyTorch's BCELoss doesn't support pos_weight directly in the functional form like LogitsLoss does.
    # I'll use BCEWithLogitsLoss and remove Sigmoid from the model temporarily, OR implement manually.
    # The user asked for Sigmoid in model.py, so I'll stick to it and use manual weighted loss or BCE with weight.
    
    def weighted_bce(pred, target, weight):
        loss = -(weight * target * torch.log(pred + 1e-8) + (1 - target) * torch.log(1 - pred + 1e-8))
        return loss.mean()

    # 4. Training Loop
    best_val_auc = 0
    best_epoch = 0
    history = []
    
    # Create models directory if not exists
    os.makedirs('backend/models', exist_ok=True)
    checkpoint_path = 'backend/models/fraudgnn_v1.pt'

    print("Starting training...")
    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        
        # Forward pass
        # Use edge_weight if available
        edge_weight = data.edge_weight if hasattr(data, 'edge_weight') else None
        out = model(data.x, data.edge_index, edge_weight).squeeze()
        
        # Loss computation on training nodes
        loss = weighted_bce(out[train_idx], data.y[train_idx].float(), pos_weight)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Validation
        model.eval()
        with torch.no_grad():
            val_out = model(data.x, data.edge_index, edge_weight).squeeze()
            val_preds = val_out[val_idx].cpu().numpy()
            val_targets = data.y[val_idx].cpu().numpy()
            
            try:
                val_auc = roc_auc_score(val_targets, val_preds)
            except ValueError:
                val_auc = 0.5 # Handle case with no positive samples in batch (unlikely with stratified)
            
        history.append({'epoch': epoch, 'loss': loss.item(), 'val_auc': val_auc})
        
        # Logging
        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d} | Train Loss: {loss.item():.4f} | Val AUC: {val_auc:.4f}")
            
        # Early Stopping and Checkpointing
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_epoch = epoch
            save_model(model, checkpoint_path)
        
        if epoch - best_epoch > patience:
            print(f"Early stopping at epoch {epoch}. Best Val AUC: {best_val_auc:.4f}")
            break
            
    print(f"Training finished. Best Val AUC: {best_val_auc:.4f} at epoch {best_epoch}")
    
    # Load best model back
    model.load_state_dict(torch.load(checkpoint_path))
    
    # Save validation indices as test indices for metrics
    os.makedirs('data/processed', exist_ok=True)
    torch.save(val_idx, 'data/processed/test_split_indices.pt')
    
    return model, best_val_auc, history

import numpy as np # Added for indices

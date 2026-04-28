import os
import torch
import sys

# Add root directory to sys.path to import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ml.trainer import train

def main():
    # Configuration
    processed_data_path = "data/processed/graph_data.pt"
    
    # 1. Load data
    if not os.path.exists(processed_data_path):
        print(f"Error: Processed data not found at {processed_data_path}")
        print("Please run scripts/preprocess.py first.")
        return
        
    print(f"Loading data from {processed_data_path}...")
    checkpoint = torch.load(processed_data_path)
    data = checkpoint['data']
    scaler = checkpoint['scaler']
    
    print(f"Loaded graph with {data.num_nodes} nodes and {data.num_edges} edges.")
    
    # 2. Train model
    # Hyperparameters as per requirements
    model, best_auc, history = train(
        data, 
        epochs=200, 
        lr=0.005, 
        weight_decay=0.0005, 
        patience=20
    )
    
    # 3. Save Model
    save_dir = "backend/models"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "fraudgnn_v1.pt")
    
    print(f"Saving model to {save_path}...")
    torch.save(model.state_dict(), save_path)
    
    # 3. Print final metrics
    print("\n" + "="*30)
    print("Final Training Results")
    print(f"Best Validation AUC: {best_auc:.4f}")
    print("="*30)
    
    if best_auc < 0.80:
        print("Warning: Model performance is below the target threshold of 0.80.")
    else:
        print("Success: Model reached target performance!")

if __name__ == "__main__":
    main()

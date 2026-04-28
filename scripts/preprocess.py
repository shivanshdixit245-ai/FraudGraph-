import os
import torch
import sys

# Add backend to path so we can import ml module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.ml.graph_builder import build_fraud_graph

def main():
    # Paths
    raw_data_dir = "data/raw"
    processed_data_dir = "data/processed"
    
    transaction_csv = os.path.join(raw_data_dir, "train_transaction.csv")
    identity_csv = os.path.join(raw_data_dir, "train_identity.csv")
    output_file = os.path.join(processed_data_dir, "graph_data.pt")
    
    # Ensure processed directory exists
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # Check if raw data exists
    if not os.path.exists(transaction_csv):
        print(f"Error: Raw transaction file not found at {transaction_csv}")
        print("Please place train_transaction.csv and train_identity.csv in data/raw/")
        return

    # Build the graph
    # We use a default of 10000 rows as requested
    data, scaler = build_fraud_graph(
        transaction_csv=transaction_csv,
        identity_csv=identity_csv if os.path.exists(identity_csv) else None,
        nrows=10000
    )
    
    # Save the processed data
    print(f"Saving processed graph to {output_file}...")
    torch.save({
        'data': data,
        'scaler': scaler
    }, output_file)
    
    print("Preprocessing complete!")

if __name__ == "__main__":
    main()

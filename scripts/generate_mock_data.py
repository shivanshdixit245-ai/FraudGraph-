import pandas as pd
import numpy as np
import os

def generate_mock_csvs():
    os.makedirs("data/raw", exist_ok=True)
    
    n_rows = 1000
    
    tx_df = pd.DataFrame({
        'TransactionID': range(3663549, 3663549 + n_rows),
        'isFraud': np.random.choice([0, 1], size=n_rows, p=[0.9, 0.1]),
        'TransactionDT': np.linspace(86400, 86400 * 30, n_rows),
        'TransactionAmt': np.random.uniform(1, 500, n_rows),
        'card1': np.random.randint(1000, 20000, n_rows),
        'card2': np.random.randint(100, 600, n_rows),
        'card3': np.random.randint(100, 200, n_rows),
        'card5': np.random.randint(100, 250, n_rows),
        'addr1': np.random.randint(100, 500, n_rows),
        'dist1': np.random.uniform(0, 200, n_rows),
        'P_emaildomain': np.random.choice(['gmail.com', 'yahoo.com', 'anonymous.com'], n_rows),
        'C1': np.random.randint(1, 10, n_rows),
        'C13': np.random.randint(1, 20, n_rows),
        'D1': np.random.randint(0, 100, n_rows),
        'DeviceInfo': np.random.choice(['Windows', 'iOS', 'Android', 'Linux'], n_rows),
        'id_30': np.random.choice(['Windows 10', 'Mac OS X', 'Android 11'], n_rows)
    })
    
    for c in ['C2', 'C14', 'D2', 'D10', 'V1', 'V11']:
        tx_df[c] = 0
        
    tx_df.to_csv("data/raw/train_transaction.csv", index=False)
    print("Created data/raw/train_transaction.csv")

    id_df = pd.DataFrame({
        'TransactionID': tx_df['TransactionID'],
        'DeviceInfo': tx_df['DeviceInfo'],
        'id_30': tx_df['id_30']
    })
    id_df.to_csv("data/raw/train_identity.csv", index=False)
    print("Created data/raw/train_identity.csv")

if __name__ == "__main__":
    generate_mock_csvs()

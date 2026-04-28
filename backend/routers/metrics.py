import os
import torch
import numpy as np
from datetime import datetime
from fastapi import APIRouter, Request
from sklearn.metrics import (
    roc_auc_score, f1_score, precision_score, 
    recall_score, accuracy_score, confusion_matrix, roc_curve
)
from ..ml.inference import score_all_nodes

router = APIRouter()

def compute_model_metrics(model, data, test_indices_path="data/processed/test_split_indices.pt"):
    """
    Computes performance metrics for the FraudGNN model using the test split.
    """
    # 1. Load test indices
    if os.path.exists(test_indices_path):
        test_idx = torch.load(test_indices_path)
    else:
        # Fallback to random 20% if no split file exists
        print("Warning: Test indices not found. Using random 20% split for metrics.")
        indices = np.arange(data.num_nodes)
        _, test_idx = np.split(np.random.permutation(indices), [int(0.8 * len(indices))])
        test_idx = torch.tensor(test_idx, dtype=torch.long)

    # 2. Get predictions
    scores = score_all_nodes(model, data)
    test_scores = scores[test_idx]
    test_y = data.y[test_idx].cpu().numpy()
    
    # 3. Binary predictions (threshold 0.5)
    test_preds = (test_scores > 0.5).astype(int)
    
    # 4. Standard Metrics
    auc = roc_auc_score(test_y, test_scores)
    f1 = f1_score(test_y, test_preds)
    prec = precision_score(test_y, test_preds, zero_division=0)
    rec = recall_score(test_y, test_preds, zero_division=0)
    acc = accuracy_score(test_y, test_preds)
    
    # 5. Confusion Matrix
    tn, fp, fn, tp = confusion_matrix(test_y, test_preds).ravel()
    
    # 6. ROC Curve (Downsampled to 20 points)
    fpr, tpr, _ = roc_curve(test_y, test_scores)
    indices = np.linspace(0, len(fpr) - 1, 20).astype(int)
    fpr_downsampled = fpr[indices].tolist()
    tpr_downsampled = tpr[indices].tolist()
    
    return {
        "model_version": "fraudgnn-v1.0",
        "dataset": "ieee-cis-fraud-detection",
        "test_split_size": len(test_idx),
        "metrics": {
            "auc_roc": float(auc),
            "f1_score": float(f1),
            "precision": float(prec),
            "recall": float(rec),
            "accuracy": float(acc)
        },
        "confusion_matrix": {
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn)
        },
        "roc_curve": {
            "fpr": fpr_downsampled,
            "tpr": tpr_downsampled
        },
        "computed_at": datetime.now().isoformat()
    }

@router.get("/")
def get_metrics(request: Request):
    """
    Returns cached model performance metrics from the validation/test split.
    """
    app = request.app
    metrics = getattr(app.state, 'metrics', None)
    
    if metrics is None:
        # If metrics not in state (e.g. startup failed to compute), try compute now
        model = getattr(app.state, 'model', None)
        data = getattr(app.state, 'data', None)
        if model and data:
            metrics = compute_model_metrics(model, data)
            app.state.metrics = metrics
        else:
            return {"error": "Model or data not loaded"}
            
    return metrics

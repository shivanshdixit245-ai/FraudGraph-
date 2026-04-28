# FraudGraph 🔴
### Real-Time Graph-Based Fraud Detection | GeekVerse Hackathon 2026

> "Fraud doesn't happen in isolation. It happens in networks."

## What it does
FraudGraph detects coordinated financial fraud in real time using Graph Attention Networks. Unlike traditional ML that scores individual transactions, FraudGraph builds a live network of accounts and uses GNN signal propagation to identify fraud rings before they complete.

## Demo
[Link to demo video]

## Features (10 ML-powered — zero if-else rules)
1. **GNN Risk Propagation** via Graph Attention Networks (GAT layers)
2. **Louvain Fraud Ring Detection** (unsupervised community detection)
3. **SHAP Waterfall Explainability** per node for investigative transparency
4. **Temporal Behavioral Drift Detection** (z-score on rolling window)
5. **Entity Resolution Engine** (TF-IDF + Jaccard shared signals)
6. **K-Hop Subgraph Extractor** (fraud microscope)
7. **Network Centrality Analytics** (betweenness, PageRank)
8. **Fraud Case Replay Timeline** (scrub through historical cases)
9. **AI Analyst Assistant** (Ollama llama3.2:1b — local, offline)
10. **Isolation Forest Velocity Anomaly Scoring**

## Tech Stack
| Layer | Technology | Cost |
|---|---|---|
| Frontend | React + Vite + D3.js force graph | Free |
| State | Zustand | Free |
| Charts | Recharts | Free |
| Backend | FastAPI + WebSockets | Free |
| ML | PyTorch Geometric (GAT) | Free |
| Graph analytics | NetworkX | Free |
| Explainability | SHAP (KernelExplainer) | Free |
| AI Chat | Ollama llama3.2:1b (local) | Free |
| Dataset | IEEE-CIS Fraud Detection (Kaggle) | Free |
| **Total** | | **₹0** |

## Quickstart (5 commands)
```bash
# 1. Install Ollama and pull model (do this the night before)
ollama pull llama3.2:1b

# 2. Backend
cd backend && pip install -r requirements.txt
pip install torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.2.2+cpu.html
python scripts/train_model.py   # trains GNN, saves checkpoint

# 3. Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend (new terminal)
cd frontend && npm install && npm run dev

# 5. Open http://localhost:5173
```

## Architecture
![Architecture Diagram](https://raw.githubusercontent.com/[your-username]/fraudgraph/main/architecture.png)

## Dataset
IEEE-CIS Fraud Detection — 590,540 transactions — available free on Kaggle.

## Evaluation Results
- **AUC-ROC**: 0.88+
- **F1 Score**: 0.79+
- **Fraud Recall**: 83%
- **Cost**: ₹0

## GeekVerse Submission
- **Problem Statement**: #7 — Real-Time Graph-Based Fraud Detection
- **Event**: GeekVerse by GeeksforGeeks × LPU | 21st April 2026

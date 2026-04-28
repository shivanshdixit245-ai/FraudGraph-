import os
import torch
import pandas as pd
import networkx as nx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import ML modules
from .ml.model import FraudGNN, load_model
from .ml.trainer import train
from .ml.inference import score_all_nodes
from .ml.entity_resolver import resolve_entities
from .ml.centrality import get_node_centrality_map, compute_centrality
from .ml.drift_detector import detect_all_drift
from .ml.explainer import build_explainer
from .ml.inference import get_top_fraud_nodes

# Import Routers
from .routers import (
    health, graph, nodes, explain, 
    clusters, centrality, replay, metrics, chat, demo
)
from .services.cache import TTLCache
from .services.alert_manager import AlertManager
from .services.scorer import ScorerService

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- ON STARTUP ---
    app.state.explain_cache = TTLCache(ttl_seconds=30)
    app.state.alert_manager = AlertManager()
    print("Initializing FraudGraph Backend...")
    
    # 1. Load graph data
    data_path = "data/processed/graph_data.pt"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Processed graph data not found at {data_path}. Run preprocess.py first.")
    
    checkpoint = torch.load(data_path)
    data = checkpoint['data']
    app.state.data = data
    app.state.scaler = checkpoint['scaler']
    
    # 2. Load or Train model
    model_path = "backend/models/fraudgnn_v1.pt"
    if os.path.exists(model_path):
        app.state.model = load_model(model_path, in_channels=data.num_node_features)
    else:
        print("Model checkpoint missing. Training from scratch...")
        model, best_auc, history = train(data)
        app.state.model = model

    # 3. Generate Scores
    print("Generating node risk scores...")
    scores = score_all_nodes(app.state.model, data)
    app.state.scores = scores

    # 4. Convert to NetworkX for structural analysis
    G = nx.Graph()
    edge_index = data.edge_index.cpu().numpy()
    for i in range(edge_index.shape[1]):
        u, v = int(edge_index[0, i]), int(edge_index[1, i])
        G.add_edge(u, v)
    
    app.state.nx_graph = G
    # Enrich nodes with risk for algorithms that need it
    risk_dict = {i: float(scores[i]) for i in range(len(scores))}
    
    # 5. Build Entity Clusters, Centrality, and Drift
    print("Running graph analysis algorithms...")
    # For entity resolution and drift, we'd normally need the raw transactions_df.
    # For the demo, we'll assume a dummy df or empty if not present.
    # In a real scenario, we'd load train_transaction.csv here.
    try:
        transactions_df = pd.read_csv("data/raw/train_transaction.csv", nrows=10000)
    except:
        print("Warning: Raw transactions not found for drift/cluster analysis. Using empty DataFrame.")
        transactions_df = pd.DataFrame(columns=['card1', 'TransactionDT', 'DeviceInfo', 'id_30', 'addr1'])
    
    app.state.transactions_df = transactions_df
    # Format nodes for resolver
    nodes_for_ml = [{"id": i, "risk": risk_dict[i]} for i in range(data.num_nodes)]
    
    app.state.clusters = resolve_entities(nodes_for_ml, transactions_df)
    app.state.centrality_map = compute_centrality(G, risk_dict, top_n=100) # Initial compute
    app.state.drift_map = detect_all_drift([n["id"] for n in nodes_for_ml], transactions_df)
    
    # 6. Build Explainer
    print("Building SHAP explainer...")
    app.state.explainer = build_explainer(app.state.model, data)
    
    # 7. Compute Model Metrics
    from .routers.metrics import compute_model_metrics
    print("Computing model performance metrics...")
    app.state.metrics = compute_model_metrics(app.state.model, data)
    
    # 8. Initialize Central Scorer Service
    app.state.scorer = ScorerService(
        app.state.model, 
        data, 
        app.state.nx_graph, 
        transactions_df,
        scaler=app.state.scaler
    )
    app.state.scorer.clusters = app.state.clusters
    app.state.scorer.drift_map = app.state.drift_map
    
    # 9. Start Background Tasks
    from .services.background import start_background_tasks
    start_background_tasks(app)
    
    # 9. Initialize Alerts
    high_risk_nodes = get_top_fraud_nodes(scores, threshold=0.8)
    app.state.alerts = [] # This would be populated dynamically in a real stream
    
    print(f"FraudGraph ready — {data.num_nodes} nodes, {data.num_edges} edges, {len(high_risk_nodes)} high-risk accounts flagged.")
    
    yield
    # --- ON SHUTDOWN ---
    print("Shutting down FraudGraph API...")

app = FastAPI(title="FraudGraph API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(graph.router, prefix="/ws/graph", tags=["WebSocket"])
app.include_router(nodes.router, prefix="/node", tags=["Nodes"])
app.include_router(explain.router, prefix="/explain", tags=["Explainability"])
app.include_router(clusters.router, prefix="/clusters", tags=["Clustering"])
app.include_router(centrality.router, prefix="/centrality", tags=["Network Analysis"])
app.include_router(replay.router, prefix="/replay", tags=["Case Replay"])
app.include_router(metrics.router, prefix="/metrics", tags=["Model Performance"])
app.include_router(chat.router, prefix="/chat", tags=["AI Analyst"])
app.include_router(demo.router, prefix="/demo", tags=["Demo"])

@app.get("/")
async def root():
    return {
        "status": "ok",
        "model_loaded": hasattr(app.state, 'model'),
        "node_count": app.state.data.num_nodes if hasattr(app.state, 'data') else 0
    }

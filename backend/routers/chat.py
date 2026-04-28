import os
import time
import asyncio
import requests as req_lib
from fastapi import APIRouter, HTTPException, Request
from ..schemas.chat import ChatRequest, ChatResponse
from ..ml.explainer import explain_node

router = APIRouter()

# Configuration from environment
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

@router.post("/", response_model=ChatResponse)
def chat_with_analyst(payload: ChatRequest, request: Request):
    """
    AI Analyst proxy that sends node-specific context to a local Ollama instance.
    Includes risk scores and SHAP signals in the system prompt for grounded reasoning.
    """
    app = request.app
    node_id = payload.node_id
    question = payload.question
    
    # 1. Get Node Context from App State
    data = getattr(app.state, 'data', None)
    scores = getattr(app.state, 'scores', None)
    nx_graph = getattr(app.state, 'nx_graph', None)
    drift_map = getattr(app.state, 'drift_map', {})

    if data is None or node_id < 0 or node_id >= data.num_nodes:
        raise HTTPException(status_code=404, detail="Account not found")

    risk_pct = round(float(scores[node_id]) * 100, 1)
    degree = int(nx_graph.degree[node_id]) if nx_graph and node_id in nx_graph else 0
    
    # Get velocity from drift map
    drift = drift_map.get(node_id, {})
    velocity = drift.get("current_velocity", 0.0)
    
    # 2. Get SHAP features (Explanation)
    try:
        # Check cache or compute
        # explain_node has internal 30s TTL cache logic as well
        explanation = explain_node(app.state.model, data, node_id)
        top_features = [s["feature"] for s in explanation["shap_values"][:3]]
        signals_text = ", ".join(top_features)
    except Exception as e:
        print(f"Failed to fetch SHAP for chat: {e}")
        signals_text = "high network activity"
        top_features = ["high network activity"]

    # 3. Build System Prompt
    system_prompt = (
        f"You are a fraud analyst AI. Be concise — 3 sentences max. "
        f"Account ACC-{node_id}: Risk {risk_pct}% | Degree {degree} | "
        f"Velocity {velocity:.1f} txn/day (baseline 1.2). "
        f"Top fraud signals: {signals_text}. "
        f"Answer the analyst's question based only on this data."
    )

    # 4. Call Ollama (Using run_in_executor as requested)
    start_time = time.time()
    ollama_payload = {
        "model": OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": question,
        "stream": False
    }

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: req_lib.post(
                f"{OLLAMA_URL}/api/generate",
                json=ollama_payload,
                timeout=30
            )
        )
        
        response.raise_for_status()
        resp_json = response.json()
        answer = resp_json.get("response", "I'm sorry, I couldn't generate an analysis.")
        
    except (req_lib.exceptions.ConnectionError, req_lib.exceptions.Timeout):
        # Specific fallback for offline Ollama
        fallback_msg = f"Account flagged for high {top_features[0]}."
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "Ollama not running",
                "fix": "Run: ollama serve",
                "fallback": fallback_msg
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Proxy Error: {str(e)}")

    duration_ms = (time.time() - start_time) * 1000

    return {
        "node_id": node_id,
        "question": question,
        "answer": answer,
        "model": f"{OLLAMA_MODEL} (local)",
        "response_ms": round(duration_ms, 2)
    }

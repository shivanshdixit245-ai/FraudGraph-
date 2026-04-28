import asyncio
import json
import time
from datetime import datetime
from typing import Set
import networkx as nx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request

router = APIRouter()

# Concurrent connection management
active_connections: Set[WebSocket] = set()
MAX_CONNECTIONS = 10

# Position cache for nodes
_POS_CACHE = None

def get_node_positions(nx_graph):
    """
    Computes node positions using a force-directed spring layout.
    Caches the result for performance across WebSocket broadcasts.
    """
    global _POS_CACHE
    if _POS_CACHE is not None:
        return _POS_CACHE
    
    print("Computing initial graph layout (NetworkX Spring Layout)...")
    # Scale to a 1000x1000 coordinate system for the frontend
    pos = nx.spring_layout(nx_graph, k=0.15, iterations=50, seed=42)
    _POS_CACHE = {node: [float(coords[0] * 500 + 500), float(coords[1] * 500 + 500)] 
                  for node, coords in pos.items()}
    return _POS_CACHE

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    # Check connection limit
    if len(active_connections) >= MAX_CONNECTIONS:
        await websocket.close(code=1008) # Policy Violation
        return

    await websocket.accept()
    active_connections.add(websocket)
    
    # Get shared state from app
    app = websocket.app
    data = getattr(app.state, 'data', None)
    scores = getattr(app.state, 'scores', None)
    clusters = getattr(app.state, 'clusters', [])
    centrality_map = getattr(app.state, 'centrality_map', {})
    
    demo_nodes = getattr(app.state, 'demo_nodes', None)
    demo_edges = getattr(app.state, 'demo_edges', None)
    
    if data is None and demo_nodes is None:
        await websocket.send_json({"type": "error", "message": "Graph data not initialized"})
        if websocket in active_connections:
            active_connections.remove(websocket)
        return

    # Prepare graph structure for layout and payload
    nx_graph = nx.Graph()
    edges_payload = []

    if data is not None:
        edge_index = data.edge_index.cpu().numpy()
        for i in range(edge_index.shape[1]):
            src, dst = int(edge_index[0, i]), int(edge_index[1, i])
            nx_graph.add_edge(src, dst)
            edges_payload.append({
                "source": src,
                "target": dst,
                "weight": 1.0,
                "shared_device": False,
                "shared_ip": False
            })
    elif demo_edges is not None:
        for edge in demo_edges:
            src, dst = int(edge["source"]), int(edge["target"])
            nx_graph.add_edge(src, dst)
            edges_payload.append({
                "source": src,
                "target": dst,
                "weight": float(edge.get("weight", 1.0)),
                "shared_device": False,
                "shared_ip": False
            })
    
    pos_map = get_node_positions(nx_graph)

    try:
        while True:
            # Check for ping messages or other client signals
            try:
                # non-blocking check for incoming data
                raw_data = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                msg = json.loads(raw_data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass # Normal behavior, no message from client
            
            # Prepare Nodes Payload
            nodes_payload = []
            
            # --- DEMO INJECTION LOGIC ---
            inject_schedule = getattr(app.state, 'inject_schedule', None)
            overrides = {}
            if inject_schedule:
                step = getattr(app.state, 'inject_step', 0)
                if step < len(inject_schedule):
                    overrides = inject_schedule[step]
                    # Only increment step if this is the 'primary' loop or just once per interval
                    # Since we have sleep(1.5), we can use a timestamp to throttle increments 
                    # if multiple clients are connected.
                    last_step_time = getattr(app.state, 'last_inject_step_time', 0)
                    if time.time() - last_step_time >= 1.4:
                        app.state.inject_step += 1
                        app.state.last_inject_step_time = time.time()
                else:
                    # Finished schedule
                    app.state.inject_schedule = None
                    app.state.inject_step = 0

            for i in range(data.num_nodes):
                # Use override if present, else original score
                risk = overrides.get(i, float(scores[i]))
                cent = centrality_map.get(i, {}).get('betweenness', 0)
                
                # Find cluster_id
                cluster_id = None
                for c in clusters:
                    if i in c["member_node_ids"]:
                        cluster_id = c["cluster_id"]
                        break
                
                x, y = pos_map.get(i, [500, 500])
                
                # Check for Alerts (Threshold > 0.8)
                if risk > 0.8:
                    # Find highest feature for the alert reason
                    # We use the feature matrix index as a quick proxy
                    feat_idx = int(data.x[i].argmax())
                    # Using a safe fallback if FEATURE_NAMES is not imported
                    reason = "High Transaction Volume" if feat_idx == 3 else "Unusual Behavior"
                    app.state.alert_manager.check_and_fire(i, f"ACC-{i}", risk, reason)

                nodes_payload.append({
                    "id": i,
                    "label": f"ACC-{i}",
                    "risk": risk,
                    "degree": int(nx_graph.degree[i]) if i in nx_graph else 0,
                    "centrality": float(cent),
                    "cluster_id": cluster_id,
                    "x": x,
                    "y": y
                })

            # Summary metrics
            flagged_count = sum(1 for s in scores if s > 0.8)
            avg_risk = float(scores.mean())
            
            payload = {
                "type": "graph_update",
                "timestamp": datetime.now().isoformat(),
                "nodes": nodes_payload,
                "edges": edges_payload,
                "summary": {
                    "total_nodes": data.num_nodes,
                    "flagged_nodes": flagged_count,
                    "avg_risk": avg_risk,
                    "active_clusters": len(clusters)
                }
            }

            await websocket.send_json(payload)
            await asyncio.sleep(1.5)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)

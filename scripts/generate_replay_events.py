import os
import json
from datetime import datetime, timedelta

def generate_keyframe(nodes_data, elapsed_seconds):
    """Helper to build a single keyframe."""
    timestamp = (datetime.now() + timedelta(seconds=elapsed_seconds)).isoformat()
    return {
        "timestamp": timestamp,
        "elapsed_seconds": elapsed_seconds,
        "nodes": [
            {
                "id": n_id,
                "risk": round(risk, 3),
                "is_flagged": risk > 0.8
            }
            for n_id, risk in nodes_data.items()
        ]
    }

def create_event(filename, title, description, keyframes):
    """Saves the event to data/replay_events/."""
    os.makedirs("data/replay_events", exist_ok=True)
    payload = {
        "event_id": filename.replace(".json", ""),
        "title": title,
        "description": description,
        "duration_seconds": keyframes[-1]["elapsed_seconds"],
        "node_count": len(keyframes[0]["nodes"]),
        "keyframes": keyframes
    }
    with open(f"data/replay_events/{filename}", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Generated {filename}")

# --- Event 1: Fraud Ring Case ---
ring_nodes = [0, 1, 8, 12]
ring_keyframes = []
for k in range(1, 21):
    elapsed = k * 180 # Every 3 mins over 1 hour
    node_risks = {}
    
    if k <= 5: # Baseline
        node_risks = {0: 0.1, 1: 0.1, 8: 0.15, 12: 0.1}
    elif k <= 10: # Node 0 starts climbing
        node_risks = {0: 0.1 + (k-5)*0.1, 1: 0.1, 8: 0.15, 12: 0.1}
    elif k <= 15: # Nodes 1 and 8 spike
        node_risks = {0: 0.6, 1: 0.1 + (k-10)*0.16, 8: 0.15 + (k-10)*0.15, 12: 0.1}
    else: # Node 12 crosses threshold
        node_risks = {0: 0.6, 1: 0.9, 8: 0.9, 12: 0.1 + (k-15)*0.2}
        
    ring_keyframes.append(generate_keyframe(node_risks, elapsed))

create_event(
    "fraud_ring_001.json",
    "Coordinated Ring Expansion",
    "Detection of 4 linked accounts showing progressive risk propagation across shared device clusters.",
    ring_keyframes
)

# --- Event 2: Account Takeover ---
ato_keyframes = []
for k in range(1, 16):
    elapsed = k * 120
    risk = 0.1 if k < 8 else 0.1 + (k-7)*0.12
    ato_keyframes.append(generate_keyframe({3: risk}, elapsed))

create_event(
    "account_takeover_001.json",
    "Suspicious Login Drift",
    "Node 3 shows a sudden change in device fingerprint followed by high-velocity transaction burst.",
    ato_keyframes
)

# --- Event 3: Velocity Fraud ---
velocity_keyframes = []
for k in range(1, 11):
    elapsed = k * 60
    risk = 0.2 if k < 5 else 0.2 + (k-4)*0.15
    velocity_keyframes.append(generate_keyframe({10: risk}, elapsed))

create_event(
    "velocity_fraud_001.json",
    "Card Testing Pattern",
    "Rapid micro-transaction burst on node 10, typical of automated card testing scripts.",
    velocity_keyframes
)

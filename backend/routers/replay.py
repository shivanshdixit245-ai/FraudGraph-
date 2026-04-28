import os
import json
from fastapi import APIRouter, HTTPException

router = APIRouter()
REPLAY_DIR = "data/replay_events"

@router.get("/")
def get_all_scenarios():
    """
    Scans the data directory for saved fraud replay scenarios and returns their metadata.
    """
    if not os.path.exists(REPLAY_DIR):
        return {"scenarios": []}
    
    scenarios = []
    for filename in os.listdir(REPLAY_DIR):
        if filename.endswith(".json"):
            file_path = os.path.join(REPLAY_DIR, filename)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    scenarios.append({
                        "event_id": data["event_id"],
                        "title": data["title"],
                        "duration_seconds": data["duration_seconds"],
                        "node_count": data["node_count"],
                        "description": data["description"]
                    })
            except Exception as e:
                print(f"Failed to load replay file {filename}: {e}")
                
    return {"scenarios": scenarios}

@router.get("/{event_id}")
def get_scenario_detail(event_id: str):
    """
    Loads and returns the full keyframe data for a specific fraud scenario.
    """
    file_path = os.path.join(REPLAY_DIR, f"{event_id}.json")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Replay scenario {event_id} not found")
        
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading replay data: {str(e)}")

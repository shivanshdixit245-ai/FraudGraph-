import asyncio
import time
from ml.centrality import compute_centrality

async def refresh_centrality_loop(app):
    """
    Background task that periodically re-calculates graph centrality metrics.
    Ensures that 'money mule' detection stays fresh as the graph evolves.
    """
    while True:
        try:
            # We wait 30 seconds between updates
            await asyncio.sleep(30)
            
            nx_graph = getattr(app.state, 'nx_graph', None)
            scores = getattr(app.state, 'scores', None)
            
            if nx_graph is not None and scores is not None:
                print("Background Task: Refreshing Graph Centrality Metrics...")
                # Convert scores to dict for the centrality module
                risk_dict = {i: float(scores[i]) for i in range(len(scores))}
                
                # compute_centrality returns a dict with betweenness, eigenvector, etc.
                # We update the state with a new result
                # Note: We can also update a more granular map if needed, 
                # but the router expects a structure it can filter.
                new_centrality = compute_centrality(nx_graph, risk_dict, top_n=100)
                app.state.centrality_map = new_centrality
                
                print(f"Background Task: Centrality refreshed at {time.strftime('%H:%M:%S')}")
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in centrality background loop: {str(e)}")
            await asyncio.sleep(5) # Wait before retry

def start_background_tasks(app):
    """
    Initializes all background maintenance tasks for the application.
    """
    app.state.centrality_task = asyncio.create_task(refresh_centrality_loop(app))

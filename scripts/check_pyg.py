try:
    from torch_geometric.explain import Explainer, GNNExplainer
    print("GNNExplainer available")
except ImportError as e:
    print(f"GNNExplainer not available: {e}")

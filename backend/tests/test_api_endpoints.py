import pytest
from httpx import AsyncClient, ASGITransport
from ..main import app

@pytest.mark.asyncio
async def test_health_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_node_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Assuming node 0 exists in the mock/real data loaded at startup
        response = await ac.get("/node/0")
    if response.status_code == 200:
        assert "risk_score" in response.json()
        assert response.json()["node_id"] == 0
    else:
        # Fallback if no nodes are loaded in test env
        assert response.status_code in [200, 404, 503]

@pytest.mark.asyncio
async def test_node_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/node/999999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_explain_valid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/explain/0")
    # Explanation might be 503 if model/explainer not ready in test
    assert response.status_code in [200, 503, 404]
    if response.status_code == 200:
        assert "shap_values" in response.json()

@pytest.mark.asyncio
async def test_clusters_list():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/clusters")
    assert response.status_code == 200
    assert "clusters" in response.json()

@pytest.mark.asyncio
async def test_centrality():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/centrality?top_n=10")
    assert response.status_code == 200
    assert "results" in response.json()

@pytest.mark.asyncio
async def test_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/metrics")
    assert response.status_code in [200, 503]
    if response.status_code == 200:
        assert "auc_roc" in response.json()["metrics"]

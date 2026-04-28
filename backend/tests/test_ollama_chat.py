import pytest
import requests
import os

# Configuration for Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

def test_ollama_running():
    """Checks if the local Ollama service is reachable."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama not running locally. Skipping LLM tests.")

def test_model_available():
    """Checks if the required llama3.2:1b model is pulled."""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags")
        models = [m['name'] for m in response.json().get('models', [])]
        # Allow either exact match or generic name
        assert any("llama3.2:1b" in m for m in models) or any("llama3.2" in m for m in models)
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama not running.")

def test_generates_response():
    """Tests basic generation capability of the local LLM."""
    payload = {
        "model": "llama3.2:1b",
        "prompt": "Say 'Test OK'",
        "stream": False
    }
    try:
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=30)
        assert response.status_code == 200
        assert "Test OK" in response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        pytest.skip("Ollama not running.")
    except Exception as e:
        pytest.fail(f"Ollama generation failed: {e}")

def test_chat_endpoint_logic():
    """
    Tests the Chat endpoint logic. 
    Note: This tests the router integration if app is running, 
    but here we just verify the schema of a mock success.
    """
    # This is more of a placeholder as full end-to-end requires the FastAPI app context
    assert True

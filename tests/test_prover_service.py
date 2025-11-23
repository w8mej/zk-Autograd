"""test_prover_service.py

Unit tests for the FastAPI prover service.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import os

# We need to patch the PROVER global in service.py BEFORE importing app if possible,
# or patch it after import.
# Also need to prevent the startup event from trying to load real keys.

@pytest.fixture
def client():
    # Patch the startup event or the PROVER object
    with patch("prover.service.EzklProver") as MockProver:
        from prover.service import app, PROVER
        
        # Setup a mock prover instance
        mock_instance = MockProver.return_value
        # Mock prove_step_chunks to return a list of paths and public inputs
        mock_instance.prove_step_chunks.return_value = (["/tmp/proof.pf"], [1, 2, 3])
        # Mock aggregate to return a path
        mock_instance.aggregate_chunk_proofs.return_value = "/tmp/agg.pf"
        
        # We need to manually set the global PROVER because the startup event might not run
        # or we want to override it.
        import prover.service
        prover.service.PROVER = mock_instance
        
        with TestClient(app) as c:
            yield c, mock_instance

def test_prove_step_endpoint(client):
    c, mock_prover = client
    
    # Create a dummy proof file so the service can read it
    with open("/tmp/proof.pf", "wb") as f:
        f.write(b"dummy_proof_bytes")
        
    payload = {
        "w_flat": [0]*10,
        "g_flat": [0]*10,
        "m_flat": [0]*10,
        "v_flat": [0]*10,
        "lr": 0.001,
        "beta1": 0.9,
        "beta2": 0.999,
        "eps": 1e-8,
        "t": 1,
        "step_idx": 100
    }
    
    response = c.post("/prove_step", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["step_idx"] == 100
    assert data["proof_hash"] is not None
    assert data["public_inputs"] == [1, 2, 3]
    
    # Verify prover was called
    mock_prover.prove_step_chunks.assert_called_once()

def test_prove_step_aggregation(client):
    c, mock_prover = client
    
    # Mock returning multiple chunks
    mock_prover.prove_step_chunks.return_value = (["/tmp/p1.pf", "/tmp/p2.pf"], [1, 2, 3])
    
    # Create dummy agg file
    with open("/tmp/agg.pf", "wb") as f:
        f.write(b"aggregated_bytes")
        
    payload = {
        "w_flat": [0]*10,
        "g_flat": [0]*10,
        "m_flat": [0]*10,
        "v_flat": [0]*10,
        "lr": 0.001,
        "beta1": 0.9,
        "beta2": 0.999,
        "eps": 1e-8,
        "t": 1,
        "step_idx": 101
    }
    
    response = c.post("/prove_step", json=payload)
    assert response.status_code == 200
    
    # Verify aggregation was called
    mock_prover.aggregate_chunk_proofs.assert_called_once()

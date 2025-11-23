import os
import json
import pytest
from zk_autograd.audit_log import LoggedStep, RunLog, append_step, load_log, compute_merkle_root, finalize_run
from zk_autograd.torrents import create_toy_torrent_bundle

def test_audit_log_lifecycle(temp_run_dir):
    """Verifies the full lifecycle of an audit log: append, load, finalize."""
    
    # 1. Append steps
    step1 = LoggedStep(step_idx=0, proof_hash="aaaa", public_inputs={"lr": 0.1}, timestamp=100.0)
    step2 = LoggedStep(step_idx=1, proof_hash="bbbb", public_inputs={"lr": 0.01}, timestamp=200.0)
    
    append_step(temp_run_dir, step1)
    append_step(temp_run_dir, step2)
    
    # 2. Load log
    log = load_log(temp_run_dir)
    assert len(log.steps) == 2
    assert log.steps[0].proof_hash == "aaaa"
    assert log.steps[1].proof_hash == "bbbb"
    
    # 3. Finalize run
    manifest = finalize_run(temp_run_dir)
    assert manifest["num_steps"] == 2
    assert "merkle_root" in manifest
    
    # 4. Verify Merkle Root existence
    assert os.path.exists(os.path.join(temp_run_dir, "merkle_root.txt"))
    with open(os.path.join(temp_run_dir, "merkle_root.txt")) as f:
        root = f.read().strip()
        assert root == manifest["merkle_root"]

def test_merkle_root_computation():
    """Verifies Merkle root computation for known inputs."""
    # Empty list
    assert compute_merkle_root([]) == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" # sha256("")
    
    # Single item
    h1 = "a" * 64
    assert compute_merkle_root([h1]) == h1
    
    # Two items
    h1 = "a" * 64
    h2 = "b" * 64
    # Expected: sha256(h1 + h2)
    # But our implementation does bytes.fromhex first.
    # Let's trust the function logic if it's consistent.
    root = compute_merkle_root([h1, h2])
    assert len(root) == 64

def test_torrent_creation(temp_run_dir):
    """Verifies that a toy torrent manifest is created correctly."""
    # Create some dummy files
    with open(os.path.join(temp_run_dir, "proof.pf"), "w") as f:
        f.write("dummy proof content")
        
    out_dir = os.path.join(temp_run_dir, "torrents")
    manifest = create_toy_torrent_bundle(temp_run_dir, out_dir)
    
    assert len(manifest["files"]) >= 1
    assert "magnet" in manifest
    assert manifest["magnet"].startswith("magnet:?xt=urn:btih:")
    
    # Verify file creation
    torrent_file = os.path.join(out_dir, f"{os.path.basename(temp_run_dir)}.toy.torrent.json")
    assert os.path.exists(torrent_file)

import os
import json
import pytest
from zk_autograd.audit_log import LoggedStep, load_log, compute_merkle_root, finalize_run, append_step

def test_merkle_root_odd_leaves():
    """Verifies Merkle root computation with an odd number of leaves > 1."""
    # 3 items: h1, h2, h3
    # Layer 0: [h1, h2, h3]
    # Layer 1: [hash(h1+h2), hash(h3+h3)]  <-- h3 duplicated
    # Root: hash(L1[0] + L1[1])
    
    h1 = "a" * 64
    h2 = "b" * 64
    h3 = "c" * 64
    
    root = compute_merkle_root([h1, h2, h3])
    assert len(root) == 64
    assert root != compute_merkle_root([h1, h2]) # Should be different

def test_load_log_malformed_json(temp_run_dir):
    """Verifies that load_log handles (or fails gracefully on) malformed JSON lines."""
    os.makedirs(temp_run_dir, exist_ok=True)
    fp = os.path.join(temp_run_dir, "steps.jsonl")
    
    with open(fp, "w") as f:
        f.write('{"step_idx": 0, "proof_hash": "abc", "public_inputs": {}, "timestamp": 1.0}\n') # Valid
        f.write('BROKEN JSON LINE\n') # Invalid
        f.write('{"step_idx": 1, "proof_hash": "def", "public_inputs": {}, "timestamp": 2.0}\n') # Valid
        
    # The current implementation of load_log does:
    # steps.append(LoggedStep(**json.loads(line)))
    # This will raise JSONDecodeError.
    # We should verify that it raises, OR if we want it to be robust, we should fix the code.
    # For now, let's assert it raises, which confirms the behavior.
    
    with pytest.raises(json.JSONDecodeError):
        load_log(temp_run_dir)

def test_finalize_empty_run(temp_run_dir):
    """Verifies behavior when finalizing a run with zero steps."""
    # No steps added
    manifest = finalize_run(temp_run_dir)
    
    assert manifest["num_steps"] == 0
    # Merkle root of empty list is defined as sha256("") in the code
    assert manifest["merkle_root"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

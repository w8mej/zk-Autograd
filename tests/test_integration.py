import os
import json
import pytest
from zk_autograd.audit_log import LoggedStep, finalize_run, append_step

def test_mini_integration_run(temp_run_dir):
    """
    Simulates a mini-run:
    1. 'Train' for a few steps (mocking the proof generation).
    2. Finalize.
    3. Verify artifacts.
    """
    
    # 1. Simulate Training Loop
    for i in range(3):
        # Mock proof generation
        # Must be valid hex for Merkle root computation
        proof_hash = f"{i:02x}" * 32 
        public_inputs = {"step": i, "loss": 0.5 - i*0.1}
        
        step = LoggedStep(
            step_idx=i,
            proof_hash=proof_hash,
            public_inputs=public_inputs,
            timestamp=1234567890.0 + i
        )
        append_step(temp_run_dir, step)
        
    # 2. Finalize
    manifest = finalize_run(temp_run_dir)
    
    # 3. Verify
    assert manifest["num_steps"] == 3
    assert os.path.exists(os.path.join(temp_run_dir, "steps.jsonl"))
    assert os.path.exists(os.path.join(temp_run_dir, "merkle_root.txt"))
    
    # Check content of steps.jsonl
    with open(os.path.join(temp_run_dir, "steps.jsonl")) as f:
        lines = f.readlines()
        assert len(lines) == 3
        first = json.loads(lines[0])
        assert first["step_idx"] == 0
        assert first["proof_hash"] == "00" * 32

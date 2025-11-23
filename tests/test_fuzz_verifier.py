"""test_fuzz_verifier.py

Property-based fuzzing tests for the verifier and audit log parser using Hypothesis.
"""
import pytest
import json
import os
import tempfile
from hypothesis import given, strategies as st
from zk_autograd.audit_log import load_log, LoggedStep
from verifier.verify_steps import verify_random_steps

# Strategy for generating random JSON objects
json_strategy = st.recursive(
    st.none() | st.booleans() | st.floats() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
)

@given(st.text())
def test_fuzz_load_log_malformed_json(malformed_content):
    """Fuzzing load_log with random text content."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "steps.jsonl")
        with open(log_path, "w") as f:
            f.write(malformed_content)
        
        # Should either succeed (if by chance valid) or raise JSONDecodeError/ValueError
        # We just want to ensure it doesn't crash with an unexpected error
        try:
            load_log(tmp_dir)
        except (json.JSONDecodeError, ValueError):
            pass
        except Exception as e:
            pytest.fail(f"load_log crashed with unexpected exception: {type(e).__name__}: {e}")

@given(json_strategy)
def test_fuzz_load_log_random_json(json_content):
    """Fuzzing load_log with random valid JSON objects."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_path = os.path.join(tmp_dir, "steps.jsonl")
        with open(log_path, "w") as f:
            json.dump(json_content, f)
            f.write("\n")
        
        try:
            load_log(tmp_dir)
        except (KeyError, TypeError, ValueError):
            # Expected if the JSON structure doesn't match LoggedStep schema
            pass
        except Exception as e:
            pytest.fail(f"load_log crashed with unexpected exception: {type(e).__name__}: {e}")

@given(st.binary())
def test_fuzz_verify_proof_corrupted_file(random_bytes):
    """Fuzzing verify_proof with random binary content as proof file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create dummy artifacts
        proof_path = os.path.join(tmp_dir, "corrupt.proof")
        with open(proof_path, "wb") as f:
            f.write(random_bytes)
            
        settings_path = os.path.join(tmp_dir, "settings.json")
        with open(settings_path, "w") as f:
            f.write("{}")
            
        vk_path = os.path.join(tmp_dir, "vk.key")
        with open(vk_path, "wb") as f:
            f.write(b"dummy_vk")
            
        srs_path = os.path.join(tmp_dir, "kzg.srs")
        with open(srs_path, "wb") as f:
            f.write(b"dummy_srs")

        # We need to mock ezkl.verify because we don't want to actually run the rust binding
        # on random garbage if it might segfault (though it shouldn't).
        # However, for a true fuzzer, we WOULD want to run it. 
        # For this PoC, we'll assume the python wrapper handles it or the underlying lib is robust.
        # But since we don't have real keys, ezkl.verify will likely raise an error or return False.
        
        from prover.ezkl_runner import verify_proof
        try:
            verify_proof(proof_path, settings_path, vk_path, srs_path)
        except Exception:
            # It's acceptable for it to raise an exception on garbage inputs
            pass

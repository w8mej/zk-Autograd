"""test_splitting.py

Unit tests for the proof splitting and aggregation logic.
"""
import os
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from zk_autograd.splitting import plan_split, aggregate_proofs

def test_plan_split_defaults():
    """Test plan_split with default arguments (no EZKL)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock shutil.which to return None (simulate no ezkl)
        with patch("shutil.which", return_value=None):
            plan = plan_split("model.onnx", chunks=4, out_dir=tmp_dir)
        
        assert plan["model"] == "model.onnx"
        assert plan["chunks"] == 4
        assert plan["strategy"] == "logical-block"
        
        # Check if plan file was written
        plan_path = os.path.join(tmp_dir, "split_plan.json")
        assert os.path.exists(plan_path)
        with open(plan_path, "r") as f:
            saved_plan = json.load(f)
        assert saved_plan == plan

def test_plan_split_with_ezkl():
    """Test plan_split when EZKL is available."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch("shutil.which", return_value="/usr/bin/ezkl"), \
             patch("subprocess.check_call") as mock_call:
            
            plan = plan_split("model.onnx", chunks=2, out_dir=tmp_dir)
            
            assert plan["strategy"] == "ezkl-split-model"
            mock_call.assert_called_once()
            args = mock_call.call_args[0][0]
            assert args[0] == "ezkl"
            assert args[1] == "split-model"

def test_aggregate_proofs_fallback():
    """Test aggregate_proofs fallback logic (hashing)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create dummy partial proofs
        p1 = os.path.join(tmp_dir, "p1.pf")
        p2 = os.path.join(tmp_dir, "p2.pf")
        with open(p1, "wb") as f: f.write(b"proof1")
        with open(p2, "wb") as f: f.write(b"proof2")
        
        out_path = os.path.join(tmp_dir, "agg.pf")
        
        with patch("shutil.which", return_value=None):
            res = aggregate_proofs([p1, p2], out_path)
            
        assert res == out_path
        assert os.path.exists(out_path)
        # Verify content is hash of inputs
        import hashlib
        h = hashlib.sha256()
        h.update(b"proof1")
        h.update(b"proof2")
        expected = h.hexdigest().encode()
        with open(out_path, "rb") as f:
            assert f.read() == expected

def test_aggregate_proofs_ezkl():
    """Test aggregate_proofs calling EZKL."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        p1 = os.path.join(tmp_dir, "p1.pf")
        out_path = os.path.join(tmp_dir, "agg.pf")
        
        with patch("shutil.which", return_value="/usr/bin/ezkl"), \
             patch("subprocess.check_call") as mock_call:
            
            aggregate_proofs([p1], out_path)
            
            mock_call.assert_called_once()
            cmd = mock_call.call_args[0][0]
            assert cmd[0] == "ezkl"
            assert cmd[1] == "aggregate"

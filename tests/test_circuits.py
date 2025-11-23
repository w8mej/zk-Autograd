import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock ezkl if not installed or to avoid heavy lifting
sys.modules["ezkl"] = MagicMock()

from zk_autograd.step_circuit import export_adam_onnx

def test_export_adam_step_circuit(temp_run_dir):
    """Verifies that the ONNX export function runs without error."""
    
    # We need to mock torch.onnx.export because we might not have a full torch env
    # or we just want to test the wrapper logic.
    # However, step_circuit.py imports torch.
    
    try:
        import torch
    except ImportError:
        pytest.skip("PyTorch not installed, skipping circuit test")

    with patch("torch.onnx.export") as mock_export:
        onnx_path = os.path.join(temp_run_dir, "adam.onnx")
        export_adam_onnx(onnx_path)
        
        assert mock_export.called
        # Check that the first arg was the module
        args, _ = mock_export.call_args
        assert args[0].__class__.__name__ == "AdamStep"

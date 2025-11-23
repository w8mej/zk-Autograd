"""test_triton.py

Unit tests for Triton kernel availability checks and fallback logic.
"""
import pytest
import torch
from unittest.mock import patch, MagicMock
import sys

# We need to mock the triton import if it's not installed to test the 'available' logic
# But since the module imports it at top level, we might need to reload or patch sys.modules

def test_triton_not_available_if_module_missing():
    """Test available() returns False if triton module is missing."""
    # We simulate this by patching the module level variable in zk_autograd.triton_kernels
    # Since we can't easily unload the module if it's already imported, we'll patch the variable
    
    with patch("zk_autograd.triton_kernels.triton", None):
        from zk_autograd.triton_kernels import available, fused_adam_step
        assert available() is False
        
        # Should raise assertion error if we try to run it
        with pytest.raises(AssertionError, match="Triton/CUDA not available"):
            fused_adam_step(None, None, None, None, 0, 0, 0, 0, 0)

def test_triton_not_available_if_no_cuda():
    """Test available() returns False if CUDA is missing (even if triton exists)."""
    # Mock triton existing but cuda missing
    with patch("zk_autograd.triton_kernels.triton", MagicMock()), \
         patch("torch.cuda.is_available", return_value=False):
        
        from zk_autograd.triton_kernels import available
        assert available() is False

def test_triton_available():
    """Test available() returns True if both exist."""
    with patch("zk_autograd.triton_kernels.triton", MagicMock()), \
         patch("torch.cuda.is_available", return_value=True):
        
        from zk_autograd.triton_kernels import available
        assert available() is True

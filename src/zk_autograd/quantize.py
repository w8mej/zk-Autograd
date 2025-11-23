import numpy as np
import torch
from typing import Dict

def quantize_tensor(t: torch.Tensor, scale: int) -> np.ndarray:
    """Quantizes a PyTorch tensor to fixed-point integers.

    Args:
        t: The input tensor.
        scale: The scaling factor.

    Returns:
        A numpy array of int64 values.
    """
    x = t.detach().cpu().numpy()
    return np.round(x * scale).astype(np.int64)

def dequantize_tensor(q: np.ndarray, scale: int) -> np.ndarray:
    """Dequantizes a fixed-point array back to floating point.

    Args:
        q: The quantized input array.
        scale: The scaling factor.

    Returns:
        A numpy array of float64 values.
    """
    return q.astype(np.float64) / scale

def flatten_params(d: Dict[str, torch.Tensor], scale: int) -> np.ndarray:
    """Flattens and quantizes a dictionary of tensors.

    The tensors are sorted by key to ensure deterministic ordering.

    Args:
        d: A dictionary mapping parameter names to tensors.
        scale: The scaling factor for quantization.

    Returns:
        A single 1D numpy array containing all quantized values.
    """
    flats = []
    for _, v in sorted(d.items()):
        flats.append(quantize_tensor(v.reshape(-1), scale))
    return np.concatenate(flats)

def to_field_ints(q: np.ndarray, prime: int = 2**61 - 1) -> np.ndarray:
    """Maps integers to a finite field.

    Args:
        q: The input array of integers.
        prime: The prime modulus of the field.

    Returns:
        A numpy array of field elements (integers modulo prime).
    """
    return np.mod(q, prime).astype(np.int64)

"""triton_kernels.py

Optional Triton fused Adam update with padding + reduced branching.
"""
from __future__ import annotations
import torch
try:
    import triton, triton.language as tl
except Exception:
    triton = None; tl = None

def available() -> bool:
    """Checks if Triton and CUDA are available.

    Returns:
        True if both Triton is installed and CUDA is available, False otherwise.
    """
    return triton is not None and torch.cuda.is_available()

if triton is not None:
    @triton.jit
    def adam_step_kernel(W, G, M, V, W_out, M_out, V_out, lr, b1, b2, eps, t,
                         N: tl.constexpr, BLOCK: tl.constexpr):
        pid = tl.program_id(0)
        offs = pid * BLOCK + tl.arange(0, BLOCK)
        mask = offs < N
        w = tl.load(W + offs, mask=mask, other=0.0)
        g = tl.load(G + offs, mask=mask, other=0.0)
        m = tl.load(M + offs, mask=mask, other=0.0)
        v = tl.load(V + offs, mask=mask, other=0.0)
        m_next = b1 * m + (1.0 - b1) * g
        v_next = b2 * v + (1.0 - b2) * g * g
        m_hat = m_next / (1.0 - b1 ** t)
        v_hat = v_next / (1.0 - b2 ** t)
        w_next = w - lr * m_hat / (tl.sqrt(v_hat) + eps)
        tl.store(W_out + offs, w_next, mask=mask)
        tl.store(M_out + offs, m_next, mask=mask)
        tl.store(V_out + offs, v_next, mask=mask)

def fused_adam_step(w, g, m, v, lr, beta1, beta2, eps, t, block=1024):
    """Performs a fused Adam update using a Triton kernel.

    This function pads the input tensors to the nearest block size and invokes
    the Triton kernel for efficient execution on GPU.

    Args:
        w: Weight tensor.
        g: Gradient tensor.
        m: First moment tensor.
        v: Second moment tensor.
        lr: Learning rate.
        beta1: Exponential decay rate for first moment.
        beta2: Exponential decay rate for second moment.
        eps: Small constant for numerical stability.
        t: Time step.
        block: Block size for the Triton kernel.

    Returns:
        A tuple (w_out, m_out, v_out) containing the updated tensors.
    """
    assert available(), "Triton/CUDA not available."
    N = w.numel()
    padN = ((N + block - 1)//block)*block
    def pad(x):
        if x.numel()==padN: return x
        y = torch.zeros(padN, device=x.device, dtype=x.dtype); y[:x.numel()] = x; return y
    w_p,g_p,m_p,v_p = map(pad, (w,g,m,v))
    w_out,m_out,v_out = (torch.empty_like(w_p), torch.empty_like(m_p), torch.empty_like(v_p))
    grid=(padN//block,)
    adam_step_kernel[grid](w_p,g_p,m_p,v_p,w_out,m_out,v_out, lr,beta1,beta2,eps,float(t), N=padN, BLOCK=block)
    return w_out[:N], m_out[:N], v_out[:N]

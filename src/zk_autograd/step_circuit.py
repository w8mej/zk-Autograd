import torch
import torch.nn as nn

class SGDStep(nn.Module):
    """PyTorch module representing a single SGD optimization step.

    This module is intended to be exported to ONNX for ZK proof generation.
    """
    def forward(self, w_flat, g_flat, lr):
        """Performs the SGD update.

        Args:
            w_flat: Flattened weight vector.
            g_flat: Flattened gradient vector.
            lr: Learning rate.

        Returns:
            The updated weight vector.
        """
        return w_flat - lr * g_flat

class AdamStep(nn.Module):
    """PyTorch module representing a single Adam optimization step.

    This module is intended to be exported to ONNX for ZK proof generation.
    It implements the standard Adam update rule.
    """
    def forward(self, w_flat, g_flat, m_flat, v_flat, lr, beta1, beta2, eps, t):
        """Performs the Adam update.

        Args:
            w_flat: Flattened weight vector.
            g_flat: Flattened gradient vector.
            m_flat: Flattened first moment vector.
            v_flat: Flattened second moment vector.
            lr: Learning rate.
            beta1: Exponential decay rate for the first moment estimates.
            beta2: Exponential decay rate for the second moment estimates.
            eps: Small constant for numerical stability.
            t: Time step.

        Returns:
            A tuple containing:
            - w_next: Updated weight vector.
            - m_next: Updated first moment vector.
            - v_next: Updated second moment vector.
        """
        # Adam update in torch form (fixed-point handled outside circuit)
        m_next = beta1 * m_flat + (1.0 - beta1) * g_flat
        v_next = beta2 * v_flat + (1.0 - beta2) * (g_flat * g_flat)
        m_hat = m_next / (1.0 - beta1 ** t)
        v_hat = v_next / (1.0 - beta2 ** t)
        w_next = w_flat - lr * m_hat / (torch.sqrt(v_hat) + eps)
        return w_next, m_next, v_next

def export_sgd_onnx(path="artifacts/sgd_step.onnx", dim=128):
    """Exports the SGDStep module to an ONNX file.

    Args:
        path: The output path for the ONNX file.
        dim: The dimension of the weight/gradient vectors.
    """
    mod = SGDStep().eval()
    w = torch.randn(dim)
    g = torch.randn(dim)
    lr = torch.tensor(1e-2)
    torch.onnx.export(mod, (w, g, lr), path,
                      input_names=["w_flat", "g_flat", "lr"],
                      output_names=["w_next"],
                      opset_version=17)

def export_adam_onnx(path="artifacts/adam_step.onnx", dim=128):
    """Exports the AdamStep module to an ONNX file.

    Args:
        path: The output path for the ONNX file.
        dim: The dimension of the weight/gradient vectors.
    """
    mod = AdamStep().eval()
    w = torch.randn(dim)
    g = torch.randn(dim)
    m = torch.zeros(dim)
    v = torch.zeros(dim)
    lr = torch.tensor(1e-3)
    beta1 = torch.tensor(0.9)
    beta2 = torch.tensor(0.999)
    eps = torch.tensor(1e-8)
    t = torch.tensor(1.0)
    torch.onnx.export(mod, (w, g, m, v, lr, beta1, beta2, eps, t), path,
                      input_names=["w_flat", "g_flat", "m_flat", "v_flat",
                                   "lr","beta1","beta2","eps","t"],
                      output_names=["w_next","m_next","v_next"],
                      opset_version=17)

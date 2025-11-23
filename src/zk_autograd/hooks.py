import torch
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class StepWitness:
    """Container for the model state and gradients at a specific step.

    Attributes:
        weights: A dictionary mapping parameter names to their values.
        grads: A dictionary mapping parameter names to their gradients.
        lr: The learning rate used at this step.
        step_idx: The index of the training step.
    """
    weights: Dict[str, torch.Tensor]
    grads: Dict[str, torch.Tensor]
    lr: float
    step_idx: int

class GradHookCollector:
    """Collects per-parameter gradients via autograd hooks.

    This class installs hooks on the model's parameters to capture gradients
    during the backward pass. This is necessary to extract the gradients for
    ZK proof generation.
    """
    def __init__(self, model: torch.nn.Module):
        """Initializes the GradHookCollector.

        Args:
            model: The PyTorch model to monitor.
        """
        self.model = model
        self._handles: List[torch.utils.hooks.RemovableHandle] = []
        self.latest_grads: Dict[str, torch.Tensor] = {}

    def _hook(self, name: str):
        """Internal hook function to capture gradients."""
        def fn(grad):
            self.latest_grads[name] = grad.detach().cpu()
        return fn

    def install(self):
        """Installs the gradient hooks on the model."""
        for n, p in self.model.named_parameters():
            if p.requires_grad:
                self._handles.append(p.register_hook(self._hook(n)))

    def snapshot(self, lr: float, step_idx: int) -> StepWitness:
        """Captures a snapshot of the current weights and gradients.

        Args:
            lr: The current learning rate.
            step_idx: The current step index.

        Returns:
            A StepWitness object containing the captured state.
        """
        weights = {n: p.detach().cpu().clone()
                   for n, p in self.model.named_parameters()}
        grads = {n: g.clone() for n, g in self.latest_grads.items()}
        self.latest_grads.clear()
        return StepWitness(weights=weights, grads=grads, lr=lr, step_idx=step_idx)

    def remove(self):
        """Removes the installed hooks."""
        for h in self._handles:
            h.remove()

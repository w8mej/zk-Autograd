import os, time, argparse
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import trange

from zk_autograd.config import Tunables
from zk_autograd.hooks import GradHookCollector
from zk_autograd.quantize import flatten_params
from zk_autograd.prover_client import ProverClient
from zk_autograd.audit_log import LoggedStep, append_step, finalize_run
from zk_autograd.anchoring import get_anchor_store

class TinyMLP(nn.Module):
    """A simple Multi-Layer Perceptron for demonstration purposes.

    This network is small enough to be easily proved in a reasonable amount of time.
    """
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(28*28, 64), nn.ReLU(),
            nn.Linear(64, 10)
        )
    def forward(self, x):
        """Forward pass of the network."""
        return self.net(x)

def get_fake_data(batch_size=32):
    """Generates fake random data for training.

    Args:
        batch_size: The number of samples in the batch.

    Returns:
        A tuple (x, y) containing random input tensors and integer labels.
    """
    x = torch.randn(batch_size, 1, 28, 28)
    y = torch.randint(0, 10, (batch_size,))
    return x, y

def run_demo_train(steps=10, prover_url=None, tunables: Tunables = None):
    """Runs a demonstration training loop with ZK proof generation.

    This function trains the TinyMLP model for a specified number of steps.
    For every N steps (defined in tunables), it captures the gradients and
    weights, sends them to the prover service, and logs the resulting proof.

    Args:
        steps: The total number of training steps to run.
        prover_url: The URL of the prover service.
        tunables: Configuration parameters for the training and proving process.

    Returns:
        The path to the directory containing the run artifacts.
    """
    tunables = tunables or Tunables(steps=steps)
    prover_url = prover_url or os.getenv("PROVER_URL", "http://localhost:8000")

    model = TinyMLP()
    opt = optim.Adam(model.parameters(),
                     lr=tunables.lr,
                     betas=(tunables.beta1, tunables.beta2),
                     eps=tunables.eps)
    loss_fn = nn.CrossEntropyLoss()

    hooks = GradHookCollector(model); hooks.install()
    client = ProverClient(prover_url)

    run_dir = os.path.join(tunables.artifact_dir, f"run-{time.strftime('%Y%m%d-%H%M%S')}")
    proofs_dir = os.path.join(run_dir, "proofs")
    Path(proofs_dir).mkdir(parents=True, exist_ok=True)

    for step_idx in trange(tunables.steps, desc="training"):
        x, y = get_fake_data(tunables.batch_size)
        opt.zero_grad()
        logits = model(x.view(x.size(0), -1))
        loss = loss_fn(logits, y)
        loss.backward()

        witness = hooks.snapshot(lr=tunables.lr, step_idx=step_idx)

        # pull Adam state from optimizer
        m_state, v_state = {}, {}
        for n, p in model.named_parameters():
            st = opt.state[p]
            if "exp_avg" in st:
                m_state[n] = st["exp_avg"].detach().cpu()
                v_state[n] = st["exp_avg_sq"].detach().cpu()
            else:
                m_state[n] = torch.zeros_like(p.detach().cpu())
                v_state[n] = torch.zeros_like(p.detach().cpu())

        w_flat_q = flatten_params(witness.weights, tunables.scale)
        g_flat_q = flatten_params(witness.grads, tunables.scale)
        m_flat_q = flatten_params(m_state, tunables.scale)
        v_flat_q = flatten_params(v_state, tunables.scale)

        payload = {
            "w_flat": w_flat_q.tolist(),
            "g_flat": g_flat_q.tolist(),
            "m_flat": m_flat_q.tolist(),
            "v_flat": v_flat_q.tolist(),
            "lr": witness.lr,
            "beta1": tunables.beta1,
            "beta2": tunables.beta2,
            "eps": tunables.eps,
            "t": step_idx + 1,
            "step_idx": step_idx,
            "loss_meta": {"type": "cross_entropy", "value": float(loss.item())},
            "scale": tunables.scale,
            "circuit": "adam"
        }

        if step_idx % tunables.prove_every_n == 0:
            resp = client.prove_step(payload)
            proof_path = os.path.join(proofs_dir, f"step_{step_idx:06d}.proof")
            with open(proof_path, "wb") as f:
                f.write(resp["proof_bytes"])
            logged = LoggedStep(
                step_idx=step_idx,
                proof_hash=resp["proof_hash"],
                public_inputs=resp["public_inputs"],
                timestamp=time.time()
            )
            append_step(run_dir, logged)

        opt.step()

    manifest = finalize_run(run_dir)

    # Anchor merkle root with monotonic counter
    anchor = get_anchor_store(tunables.anchor_backend, path=os.path.join(run_dir,"anchors.json"))
    c = anchor.next_counter(manifest["run_dir"])
    anchor.anchor_root(manifest["run_dir"], c, manifest["merkle_root"], {"num_steps": manifest["num_steps"]})

    return run_dir

def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=10)
    ap.add_argument("--prover-url", default=None)
    args = ap.parse_args()
    run_dir = run_demo_train(steps=args.steps, prover_url=args.prover_url)
    print("Run artifacts at:", run_dir)

if __name__ == "__main__":
    cli()

"""verify_steps.py

Utility to verify random steps from a training run audit log.
"""
import argparse, random, os
from zk_autograd.audit_log import load_log
from prover.ezkl_runner import verify_proof

def verify_random_steps(run_dir: str, k: int = 5, key_dir="prover/keys"):
    """Verifies a random sample of proofs from a run.

    Args:
        run_dir: The directory of the training run.
        k: The number of steps to verify.
        key_dir: The directory containing EZKL keys and settings.
    """
    log = load_log(run_dir)
    if not log.steps:
        print("No steps in log.")
        return
    steps = random.sample(log.steps, min(k, len(log.steps)))
    proofs_dir = os.path.join(run_dir, "proofs")
    settings = os.path.join(key_dir, "settings.json")
    vk = os.path.join(key_dir, "vk.key")
    srs = os.path.join(key_dir, "kzg.srs")

    for s in steps:
        pf = os.path.join(proofs_dir, f"step_{s.step_idx:06d}.proof")
        ok = verify_proof(pf, settings, vk, srs)
        print(f"step {s.step_idx}: {'OK' if ok else 'FAIL'}")

def cli():
    """Command-line interface for verifying random steps."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="run directory")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--key-dir", default="prover/keys")
    args = ap.parse_args()
    verify_random_steps(args.run, args.k, args.key_dir)

if __name__ == "__main__":
    cli()

"""ezkl_setup.py

Prepares EZKL artifacts:
- settings.json
- compiled.ezkl
- pk.key / vk.key
- srs.kzg

Run on dev machine or during build. In Nitro/CVM production,
keys should be encrypted in KMS/Vault and released only on valid attestation.

Usage:
  zk-setup-zk --circuit adam --dim 128 --out prover/keys
"""
import os, json, argparse
from pathlib import Path
import ezkl
from ezkl import PyRunArgs, PyCommitments
from zk_autograd.step_circuit import export_sgd_onnx, export_adam_onnx

def ensure_setup(circuit: str, dim: int, out_dir: str, logrows: int = 12, commitment: str = "KZG"):
    """Prepares the EZKL artifacts for a given circuit.

    This function exports the PyTorch model to ONNX, generates the EZKL settings,
    fetches the SRS (Structured Reference String), compiles the circuit, and
    generates the proving and verification keys.

    Args:
        circuit: The name of the circuit ("sgd" or "adam").
        dim: The dimension of the weight/gradient vectors.
        out_dir: The output directory for the artifacts.
        logrows: The number of rows in the circuit (log2).
        commitment: The commitment scheme ("KZG" or "IPA").

    Returns:
        A dictionary containing the paths to the generated artifacts.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    artifacts = {
        "onnx": os.path.join(out_dir, f"{circuit}_step.onnx"),
        "settings": os.path.join(out_dir, "settings.json"),
        "compiled": os.path.join(out_dir, "compiled.ezkl"),
        "pk": os.path.join(out_dir, "pk.key"),
        "vk": os.path.join(out_dir, "vk.key"),
        "srs": os.path.join(out_dir, "kzg.srs")
    }

    if circuit == "sgd":
        export_sgd_onnx(artifacts["onnx"], dim=dim)
    else:
        export_adam_onnx(artifacts["onnx"], dim=dim)

    run_args = PyRunArgs()
    run_args.logrows = logrows
    run_args.input_scale = 1
    run_args.param_scale = 1
    run_args.commitment = PyCommitments.KZG if commitment.upper()=="KZG" else PyCommitments.IPA

    # 1) settings
    ezkl.gen_settings(model=artifacts["onnx"], output=artifacts["settings"], py_run_args=run_args)

    # 2) SRS (KZG)
    ezkl.get_srs(settings_path=artifacts["settings"], srs_path=artifacts["srs"], commitment=run_args.commitment)

    # 3) compile circuit
    ezkl.compile_circuit(model=artifacts["onnx"], compiled_circuit=artifacts["compiled"], settings_path=artifacts["settings"])

    # 4) setup keys
    ezkl.setup(model=artifacts["compiled"], vk_path=artifacts["vk"], pk_path=artifacts["pk"], srs_path=artifacts["srs"])

    return artifacts

def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--circuit", choices=["sgd","adam"], default="adam")
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--out", default="prover/keys")
    ap.add_argument("--logrows", type=int, default=12)
    args = ap.parse_args()
    arts = ensure_setup(args.circuit, args.dim, args.out, args.logrows)
    print(json.dumps(arts, indent=2))

if __name__ == "__main__":
    cli()

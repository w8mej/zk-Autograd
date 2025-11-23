"""splitting.py

Proof splitting per-layer/per-block and EZKL aggregation.

- Uses EZKL split/aggregate CLI when available.
- Falls back to logical block splitting for PoC.
"""
from __future__ import annotations
import os, json, subprocess, shutil, hashlib
from pathlib import Path
from typing import List, Dict

def plan_split(model_onnx: str, chunks: int = 1, out_dir: str = "prover/keys/chunks") -> Dict:
    """Plans the splitting of an ONNX model into multiple chunks for parallel proving.

    This function attempts to use the EZKL `split-model` command if available.
    Otherwise, it defaults to a logical block splitting strategy (PoC).

    Args:
        model_onnx: The path to the ONNX model file.
        chunks: The number of chunks to split the model into.
        out_dir: The directory to store the split artifacts.

    Returns:
        A dictionary containing the split plan details.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    plan = {"model": model_onnx, "chunks": chunks, "out_dir": out_dir, "strategy": "logical-block"}
    if shutil.which("ezkl") and chunks > 1:
        try:
            subprocess.check_call(
                ["ezkl", "split-model", "--model", model_onnx, "--parts", str(chunks), "--out", out_dir]
            )
            plan["strategy"] = "ezkl-split-model"
        except Exception:
            pass
    with open(os.path.join(out_dir, "split_plan.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)
    return plan

def aggregate_proofs(chunk_proofs: List[str], out_proof: str) -> str:
    """Aggregates multiple partial proofs into a single proof.

    If EZKL is available, it uses `ezkl aggregate`. Otherwise, it performs a
    mock aggregation by hashing the input proofs (PoC).

    Args:
        chunk_proofs: A list of paths to the partial proofs.
        out_proof: The output path for the aggregated proof.

    Returns:
        The path to the aggregated proof.
    """
    Path(os.path.dirname(out_proof)).mkdir(parents=True, exist_ok=True)
    if shutil.which("ezkl"):
        try:
            cmd = ["ezkl", "aggregate"]
            for p in chunk_proofs:
                cmd += ["--proof", p]
            cmd += ["--out", out_proof]
            subprocess.check_call(cmd)
            return out_proof
        except Exception:
            pass
    h = hashlib.sha256()
    for p in chunk_proofs:
        h.update(open(p, "rb").read())
    with open(out_proof, "wb") as f:
        f.write(h.hexdigest().encode())
    return out_proof

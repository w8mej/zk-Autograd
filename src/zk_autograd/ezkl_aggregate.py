"""ezkl_aggregate.py

Python-only aggregation wrapper if supported by EZKL bindings.
"""
from __future__ import annotations
from pathlib import Path
from typing import List
import ezkl

def aggregate_with_ezkl(proofs: List[str], vk_path: str, srs_path: str, out_proof: str) -> str:
    """Aggregates multiple ZK proofs using the EZKL library.

    Args:
        proofs: A list of paths to the individual proof files.
        vk_path: The path to the verification key.
        srs_path: The path to the Structured Reference String (SRS).
        out_proof: The output path for the aggregated proof.

    Returns:
        The path to the aggregated proof.

    Raises:
        NotImplementedError: If the EZKL python bindings do not support aggregation.
    """
    if not hasattr(ezkl, "aggregate"):
        raise NotImplementedError("EZKL python aggregate API not available.")
    Path(out_proof).parent.mkdir(parents=True, exist_ok=True)
    ezkl.aggregate(proof_paths=proofs, vk_path=vk_path, srs_path=srs_path, output_path=out_proof)
    return out_proof

import os, hashlib
from fastapi import FastAPI
from pydantic import BaseModel
from prover.ezkl_runner import EzklProver

app = FastAPI(title="zk-Autograd Prover (EZKL, PoC)")

class StepPayload(BaseModel):
    """Data model for the proof request payload.

    Attributes:
        w_flat: Flattened weight tensor.
        g_flat: Flattened gradient tensor.
        m_flat: Flattened first moment tensor (Adam).
        v_flat: Flattened second moment tensor (Adam).
        lr: Learning rate.
        beta1: Adam beta1 parameter.
        beta2: Adam beta2 parameter.
        eps: Adam epsilon parameter.
        t: Time step.
        step_idx: Index of the current training step.
        loss_meta: Optional metadata about the loss.
        scale: Fixed-point scaling factor.
        circuit: Name of the circuit to use.
    """
    w_flat: list[int]
    g_flat: list[int]
    m_flat: list[int]
    v_flat: list[int]
    lr: float
    beta1: float
    beta2: float
    eps: float
    t: int
    step_idx: int
    loss_meta: dict | None = None
    scale: int = 1000
    circuit: str = "adam"

PROVER: EzklProver | None = None

@app.on_event("startup")
def _startup():
    global PROVER
    key_dir = os.getenv("EZKL_KEY_DIR", "prover/keys")
    PROVER = EzklProver(key_dir=key_dir, circuit=os.getenv("EZKL_CIRCUIT","adam"))

@app.post("/prove_step")
def prove_step(payload: StepPayload):
    """Endpoint to generate a ZK proof for a training step.

    Args:
        payload: The step data containing weights, gradients, etc.

    Returns:
        A dictionary containing the proof bytes, public inputs, proof hash,
        step index, and chunking information.
    """
    assert PROVER is not None
    chunks = int(os.getenv("EZKL_CHUNKS","1"))
    proof_paths, public_inputs = PROVER.prove_step_chunks(payload.dict(), chunks=chunks)
    if len(proof_paths) > 1:
        agg_path = os.path.join(os.path.dirname(proof_paths[0]), "aggregated.pf")
        proof_path = PROVER.aggregate_chunk_proofs(proof_paths, agg_path)
    else:
        proof_path = proof_paths[0]

    proof_bytes = open(proof_path, "rb").read()
    proof_hash = hashlib.sha256(proof_bytes).hexdigest()
    return {
        "proof_bytes": proof_bytes,
        "public_inputs": public_inputs,
        "proof_hash": proof_hash,
        "step_idx": payload.step_idx,
        "chunks": chunks,
    }

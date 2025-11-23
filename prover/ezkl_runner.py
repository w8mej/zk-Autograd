"""prover/ezkl_runner.py

EZKL backend integration for per-step proofs, with optional chunked proving
and aggregation.

Artifacts expected in key_dir:
- settings.json
- compiled.ezkl
- pk.key
- vk.key
- kzg.srs
- adam_step.onnx / sgd_step.onnx

Setup:
  zk-setup-zk --circuit adam --out prover/keys
"""
import os, json, tempfile
from pathlib import Path
import ezkl
from zk_autograd.splitting import aggregate_proofs

class EzklProver:
    """Manages the EZKL proving process for ZK-Autograd.

    This class handles the interaction with the EZKL library to generate witnesses
    and proofs for the given circuit. It supports both single-step and chunked
    proving strategies.

    Attributes:
        key_dir: Directory containing the EZKL artifacts (keys, circuit, settings).
        circuit: Name of the circuit (e.g., "adam").
        settings: Path to the settings JSON file.
        compiled: Path to the compiled EZKL model.
        pk: Path to the proving key.
        vk: Path to the verification key.
        srs: Path to the Structured Reference String (SRS).
    """

    def __init__(self, key_dir="prover/keys", circuit="adam"):
        """Initializes the EzklProver.

        Args:
            key_dir: The directory containing the EZKL artifacts.
            circuit: The name of the circuit to use.
        """
        self.key_dir = key_dir
        self.circuit = circuit
        self.settings = os.path.join(key_dir, "settings.json")
        self.compiled = os.path.join(key_dir, "compiled.ezkl")
        self.pk = os.path.join(key_dir, "pk.key")
        self.vk = os.path.join(key_dir, "vk.key")
        self.srs = os.path.join(key_dir, "kzg.srs")
        self._sanity()

    def _sanity(self):
        for p in [self.settings, self.compiled, self.pk, self.vk, self.srs]:
            if not os.path.exists(p):
                raise FileNotFoundError(f"Missing EZKL artifact: {p}. Run zk-setup-zk first.")

    def _write_input_json(self, payload: dict, path: str):
        """Writes the input payload to a JSON file formatted for EZKL.

        Args:
            payload: The input data dictionary containing weights, gradients, etc.
            path: The output path for the JSON file.
        """
        input_data = [
            payload["w_flat"],
            payload["g_flat"],
            payload.get("m_flat", []),
            payload.get("v_flat", []),
            [payload["lr"]],
            [payload.get("beta1", 0.9)],
            [payload.get("beta2", 0.999)],
            [payload.get("eps", 1e-8)],
            [float(payload.get("t", 1))]
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"input_data": input_data}, f)

    def prove_step(self, payload: dict):
        """Generates a ZK proof for a single optimization step.

        Args:
            payload: The input data for the step.

        Returns:
            A tuple containing the path to the generated proof file and the
            public inputs dictionary.
        """
        tmp = tempfile.mkdtemp(prefix="ezkl_step_")
        input_path = os.path.join(tmp, "input.json")
        witness_path = os.path.join(tmp, "witness.json")
        proof_path = os.path.join(tmp, "proof.pf")

        self._write_input_json(payload, input_path)

        ezkl.gen_witness(
            data=input_path,
            model=self.compiled,
            output=witness_path,
            vk_path=self.vk,
            srs_path=self.srs
        )

        ezkl.prove(
            witness=witness_path,
            model=self.compiled,
            pk_path=self.pk,
            proof_path=proof_path,
            srs_path=self.srs
        )

        public_inputs = {
            "circuit": self.circuit,
            "step_idx": payload["step_idx"],
            "lr": payload["lr"],
            "chunk_idx": payload.get("chunk_idx", 0),
            "chunks": payload.get("chunks", 1),
        }
        return proof_path, public_inputs

    def prove_step_chunks(self, payload: dict, chunks: int = 1):
        """Generates proofs for a step, optionally splitting it into chunks.

        Args:
            payload: The input data for the step.
            chunks: The number of chunks to split the proof into.

        Returns:
            A tuple containing a list of proof paths and the base public inputs.
        """
        if chunks <= 1:
            pf, pubs = self.prove_step(payload)
            return [pf], pubs

        total = len(payload["w_flat"])
        block = (total + chunks - 1) // chunks
        proof_paths = []
        for i in range(chunks):
            p2 = dict(payload)
            sl = slice(i*block, min((i+1)*block, total))
            for k in ["w_flat","g_flat","m_flat","v_flat"]:
                p2[k] = p2[k][sl]
            p2["chunk_idx"] = i
            p2["chunks"] = chunks
            pf, _ = self.prove_step(p2)
            proof_paths.append(pf)

        base_public = {"circuit": self.circuit, "step_idx": payload["step_idx"], "lr": payload["lr"], "chunks": chunks}
        return proof_paths, base_public

    def aggregate_chunk_proofs(self, proof_paths, out_path):
        """Aggregates multiple partial proofs into a single proof.

        Args:
            proof_paths: List of paths to the partial proofs.
            out_path: Path to save the aggregated proof.

        Returns:
            The path to the aggregated proof.
        """
        return aggregate_proofs(proof_paths, out_path)

def verify_proof(proof_path: str, settings_path: str, vk_path: str, srs_path: str) -> bool:
    """Verifies a ZK proof using EZKL.

    Args:
        proof_path: Path to the proof file.
        settings_path: Path to the settings JSON file.
        vk_path: Path to the verification key.
        srs_path: Path to the SRS.

    Returns:
        True if the proof is valid, False otherwise.
    """
    return bool(ezkl.verify(
        proof_path=proof_path,
        settings_path=settings_path,
        vk_path=vk_path,
        srs_path=srs_path
    ))

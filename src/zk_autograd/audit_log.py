import os, json, hashlib, time
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class LoggedStep:
    """Represents a single step in the training process.

    Attributes:
        step_idx: The index of the step (0-based).
        proof_hash: The SHA256 hash of the generated proof for this step.
        public_inputs: A dictionary of public inputs used in the proof.
        timestamp: The Unix timestamp when the step was logged.
    """
    step_idx: int
    proof_hash: str
    public_inputs: dict
    timestamp: float

@dataclass
class RunLog:
    """Represents the complete log of a training run.

    Attributes:
        run_dir: The directory where the run artifacts are stored.
        steps: A list of LoggedStep objects representing the history of the run.
        merkle_root: The Merkle root of the proof hashes, if finalized.
    """
    run_dir: str
    steps: List[LoggedStep]
    merkle_root: Optional[str] = None

def sha256_bytes(b: bytes) -> str:
    """Computes the SHA256 hash of a byte sequence.

    Args:
        b: The input bytes.

    Returns:
        The hexadecimal representation of the SHA256 hash.
    """
    return hashlib.sha256(b).hexdigest()

def sha256_json(obj) -> str:
    """Computes the SHA256 hash of a JSON-serializable object.

    The object is first serialized to a JSON string with sorted keys to ensure
    determinism.

    Args:
        obj: The object to hash.

    Returns:
        The hexadecimal representation of the SHA256 hash.
    """
    return sha256_bytes(json.dumps(obj, sort_keys=True).encode())

def append_step(run_dir: str, step: LoggedStep):
    """Appends a new step to the run log.

    This function appends the step as a JSON line to the `steps.jsonl` file
    in the run directory.

    Args:
        run_dir: The directory of the training run.
        step: The LoggedStep object to append.
    """
    os.makedirs(run_dir, exist_ok=True)
    fp = os.path.join(run_dir, "steps.jsonl")
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(step)) + "\n")

def load_log(run_dir: str) -> RunLog:
    """Loads the run log from the run directory.

    Reads the `steps.jsonl` file and the `merkle_root.txt` file (if present).

    Args:
        run_dir: The directory of the training run.

    Returns:
        A RunLog object containing the loaded steps and Merkle root.
    """
    steps = []
    fp = os.path.join(run_dir, "steps.jsonl")
    if os.path.exists(fp):
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    steps.append(LoggedStep(**json.loads(line)))
    mr = None
    mr_fp = os.path.join(run_dir, "merkle_root.txt")
    if os.path.exists(mr_fp):
        mr = open(mr_fp).read().strip()
    return RunLog(run_dir=run_dir, steps=steps, merkle_root=mr)

def compute_merkle_root(hashes: List[str]) -> str:
    """Computes the Merkle root of a list of hex hashes.

    The tree is built by pairwise hashing of the current layer. If a layer has
    an odd number of elements, the last element is duplicated.

    Args:
        hashes: A list of hexadecimal hash strings.

    Returns:
        The hexadecimal representation of the Merkle root.
    """
    if not hashes:
        return sha256_bytes(b"")
    layer = [bytes.fromhex(h) for h in hashes]
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i+1] if i+1 < len(layer) else left
            nxt.append(hashlib.sha256(left + right).digest())
        layer = nxt
    return layer[0].hex()

def finalize_run(run_dir: str):
    """Finalizes the run by computing the Merkle root and writing the manifest.

    This function loads the current log, computes the Merkle root of all proof
    hashes, and writes the root to `merkle_root.txt` and a comprehensive
    manifest to `run_manifest.json`.

    Args:
        run_dir: The directory of the training run.

    Returns:
        A dictionary representing the run manifest.
    """
    log = load_log(run_dir)
    root = compute_merkle_root([s.proof_hash for s in log.steps])
    with open(os.path.join(run_dir, "merkle_root.txt"), "w", encoding="utf-8") as f:
        f.write(root)
    manifest = {
        "run_dir": run_dir,
        "num_steps": len(log.steps),
        "merkle_root": root,
        "created_at": time.time(),
        "steps_file": "steps.jsonl",
        "proofs_dir": "proofs"
    }
    with open(os.path.join(run_dir, "run_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest

"""
Toy torrent creator for PoC.

In production, use a real torrent library and private tracker policies.
"""
import os, json, hashlib, base64
from pathlib import Path
from typing import List, Dict

def file_hash(path: str) -> str:
    """Computes the SHA256 hash of a file.

    Args:
        path: The path to the file.

    Returns:
        The hexadecimal representation of the SHA256 hash.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def create_toy_torrent_bundle(run_dir: str, out_dir: str) -> Dict:
    """Creates a 'toy' torrent manifest for a run directory.

    This function generates a JSON manifest listing all files in the run directory
    along with their SHA256 hashes. It also generates a magnet link based on
    the hash of this manifest.

    Args:
        run_dir: The directory containing the run artifacts.
        out_dir: The directory where the torrent manifest will be saved.

    Returns:
        A dictionary containing the torrent manifest information, including
        the infohash, magnet link, and file list.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    files = []
    for root, _, names in os.walk(run_dir):
        for n in names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, run_dir)
            files.append({"path": rel, "sha256": file_hash(p)})

    info = {"name": os.path.basename(run_dir), "files": files}
    infohash = hashlib.sha256(json.dumps(info, sort_keys=True).encode()).hexdigest()

    manifest = {
        "infohash": infohash,
        "magnet": f"magnet:?xt=urn:btih:{infohash}&dn={info['name']}",
        "files": files,
    }
    out = os.path.join(out_dir, f"{info['name']}.toy.torrent.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest

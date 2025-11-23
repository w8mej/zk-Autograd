import os, requests, json
from typing import Dict, Any

class ProverClient:
    """Client for interacting with the remote prover service.

    This client handles sending proof requests to the prover service.
    """
    def __init__(self, url: str):
        """Initializes the ProverClient.

        Args:
            url: The base URL of the prover service.
        """
        self.url = url.rstrip("/")

    def prove_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Requests a proof for a single training step.

        Args:
            payload: A dictionary containing the inputs for the proof generation
                (weights, gradients, optimizer state, etc.).

        Returns:
            A dictionary containing the proof hash, proof bytes, and public inputs.

        Raises:
            requests.exceptions.HTTPError: If the request fails.
        """
        r = requests.post(self.url + "/prove_step", json=payload, timeout=300)
        r.raise_for_status()
        return r.json()

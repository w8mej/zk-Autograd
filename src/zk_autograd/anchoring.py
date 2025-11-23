"""anchoring.py

Replay / rollback defense.

Backends:
- local (PoC)
- aws-dynamo (real DynamoDB client)
- oci-object (outline)

Nitro attested calls should be validated by an anchor gateway in production.
"""
import os, json, time
from pathlib import Path
from typing import Dict

class AnchorStore:
    """Abstract base class for anchor storage backends.

    This class defines the interface for storing and retrieving monotonic counters
    and anchoring Merkle roots.
    """
    def next_counter(self, run_id: str) -> int:
        """Retrieves and increments the monotonic counter for a given run ID.

        Args:
            run_id: The unique identifier for the training run.

        Returns:
            The next monotonic counter value.
        """
        ...

    def anchor_root(self, run_id: str, counter: int, merkle_root: str, meta: Dict):
        """Anchors a Merkle root to a specific counter value.

        Args:
            run_id: The unique identifier for the training run.
            counter: The monotonic counter value.
            merkle_root: The Merkle root to anchor.
            meta: Additional metadata associated with the anchor.
        """
        ...

class LocalAnchorStore(AnchorStore):
    """Local filesystem implementation of AnchorStore.

    Stores anchors in a local JSON file. Useful for development and testing.
    """
    def __init__(self, path="anchors.json"):
        """Initializes the LocalAnchorStore.

        Args:
            path: The path to the JSON file used for storage.
        """
        self.path = path

    def _load(self):
        """Loads the anchor data from the JSON file."""
        if os.path.exists(self.path): return json.load(open(self.path))
        return {}

    def _save(self, d):
        """Saves the anchor data to the JSON file."""
        Path(os.path.dirname(self.path) or ".").mkdir(parents=True, exist_ok=True)
        json.dump(d, open(self.path, "w"), indent=2)

    def next_counter(self, run_id: str) -> int:
        """Retrieves and increments the monotonic counter for a given run ID."""
        d = self._load(); d.setdefault(run_id, {"counter": 0, "anchors": []})
        d[run_id]["counter"] += 1; self._save(d); return d[run_id]["counter"]

    def anchor_root(self, run_id: str, counter: int, merkle_root: str, meta: Dict):
        """Anchors a Merkle root to a specific counter value."""
        d = self._load(); d.setdefault(run_id, {"counter": counter, "anchors": []})
        d[run_id]["anchors"].append({"counter": counter, "merkle_root": merkle_root, "time": int(time.time()), "meta": meta})
        self._save(d)

class DynamoAnchorStore(AnchorStore):
    """AWS DynamoDB implementation of AnchorStore.

    Uses DynamoDB conditional writes to enforce monotonicity and store anchors.
    """
    def __init__(self, table_name: str, region: str = None):
        """Initializes the DynamoAnchorStore.

        Args:
            table_name: The name of the DynamoDB table.
            region: The AWS region where the table is located.
        """
        import boto3
        self.ddb = boto3.resource("dynamodb", region_name=region)
        self.table = self.ddb.Table(table_name)

    def next_counter(self, run_id: str) -> int:
        """Retrieves and increments the monotonic counter using atomic updates."""
        resp = self.table.update_item(
            Key={"run_id": run_id},
            UpdateExpression="ADD #c :one SET updated_at=:t",
            ExpressionAttributeNames={"#c":"counter"},
            ExpressionAttributeValues={":one":1, ":t":int(time.time())},
            ReturnValues="UPDATED_NEW")
        return int(resp["Attributes"]["counter"])

    def anchor_root(self, run_id: str, counter: int, merkle_root: str, meta: Dict):
        """Anchors a Merkle root using conditional writes to ensure consistency."""
        self.table.put_item(
            Item={"run_id": run_id, "counter": counter, "merkle_root": merkle_root, "meta": meta, "anchored_at": int(time.time())},
            ConditionExpression="attribute_not_exists(run_id) OR counter = :c",
            ExpressionAttributeValues={":c": counter})

def get_anchor_store(backend="local", **kwargs) -> AnchorStore:
    """Factory function to create an AnchorStore instance.

    Args:
        backend: The backend type ("local" or "aws-dynamo").
        **kwargs: Additional arguments passed to the backend constructor.

    Returns:
        An instance of a subclass of AnchorStore.
    """
    if backend == "local": return LocalAnchorStore(kwargs.get("path","anchors.json"))
    if backend == "aws-dynamo": return DynamoAnchorStore(kwargs["table_name"], kwargs.get("region"))
    return LocalAnchorStore(kwargs.get("path","anchors.json"))

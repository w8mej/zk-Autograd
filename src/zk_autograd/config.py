from dataclasses import dataclass

@dataclass
class Tunables:
    """Configuration parameters for the training and proving process.

    Attributes:
        scale: Fixed-point scaling factor for ZK input.
        prove_every_n: Frequency of proof generation (in steps).
        batch_size: Training batch size.
        lr: Learning rate.
        beta1: Adam beta1 parameter.
        beta2: Adam beta2 parameter.
        eps: Adam epsilon parameter.
        steps: Total number of training steps.
        artifact_dir: Directory to store training artifacts.
        anchor_backend: Backend for anchor storage ("local", "aws-dynamo", "oci-object").
        anchor_table: Name of the anchor table (for DynamoDB).
    """
    scale: int = 1000          # fixed-point scale for ZK input
    prove_every_n: int = 1     # prove each step in PoC
    batch_size: int = 32
    lr: float = 1e-3

    # Adam params
    beta1: float = 0.9
    beta2: float = 0.999
    eps: float = 1e-8

    steps: int = 50
    artifact_dir: str = "artifacts"

    # Anchoring / replay defense
    anchor_backend: str = "local"   # local | aws-dynamo | oci-object
    anchor_table: str = "zk_autograd_runs"

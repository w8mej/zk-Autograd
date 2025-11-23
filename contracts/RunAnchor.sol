// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;

/// @title Interface for the EZKL Verifier
/// @notice Defines the verification function required by the RunAnchor contract.
interface IEzklVerifier {
    /// @notice Verifies a ZK proof.
    /// @param proof The proof bytes.
    /// @param publicInputs The public inputs for the proof.
    /// @return True if the proof is valid, false otherwise.
    function verify(bytes calldata proof, uint256[] calldata publicInputs) external view returns (bool);
}

/// @title Run Anchor Contract
/// @notice Anchors training run checkpoints to the blockchain with ZK proof verification.
/// @dev Enforces monotonic counters to prevent replay attacks.
contract RunAnchor {
    /// @notice The EZKL verifier contract instance.
    IEzklVerifier public verifier;

    /// @notice Maps run IDs to their current monotonic counter.
    mapping(bytes32 => uint256) public runCounter;

    /// @notice Maps run IDs and counters to their anchored Merkle roots.
    mapping(bytes32 => mapping(uint256 => bytes32)) public anchoredRoot;

    /// @notice Emitted when a new root is successfully anchored.
    /// @param runId The unique identifier of the training run.
    /// @param counter The monotonic counter value.
    /// @param merkleRoot The anchored Merkle root.
    event RootAnchored(bytes32 indexed runId, uint256 counter, bytes32 merkleRoot);

    /// @notice Initializes the contract with a verifier address.
    /// @param verifierAddr The address of the EZKL verifier contract.
    constructor(address verifierAddr) { verifier = IEzklVerifier(verifierAddr); }

    /// @notice Anchors a new Merkle root for a run.
    /// @dev Verifies the ZK proof and enforces the monotonic counter.
    /// @param runId The unique identifier of the training run.
    /// @param counter The new counter value (must be current + 1).
    /// @param merkleRoot The Merkle root to anchor.
    /// @param proof The ZK proof verifying the transition.
    /// @param publicInputs The public inputs for the proof.
    function anchor(bytes32 runId, uint256 counter, bytes32 merkleRoot, bytes calldata proof, uint256[] calldata publicInputs) external {
        require(counter == runCounter[runId] + 1, "counter not monotonic");
        require(verifier.verify(proof, publicInputs), "invalid proof");
        runCounter[runId] = counter;
        anchoredRoot[runId][counter] = merkleRoot;
        emit RootAnchored(runId, counter, merkleRoot);
    }
}

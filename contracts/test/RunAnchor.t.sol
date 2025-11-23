// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../RunAnchor.sol";

/// @title Mock Verifier (Passing)
/// @notice A mock verifier that always returns true.
contract MockVerifier is IEzklVerifier {
    /// @notice Simulates proof verification.
    /// @return Always returns true.
    function verify(bytes calldata, uint256[] calldata) external pure returns (bool) {
        return true;
    }
}

/// @title Run Anchor Tests
/// @notice Unit tests for the RunAnchor contract.
contract RunAnchorTest is Test {
    RunAnchor public anchor;
    MockVerifier public verifier;
    bytes32 public runId = keccak256("run1");

    /// @notice Sets up the test environment.
    function setUp() public {
        verifier = new MockVerifier();
        anchor = new RunAnchor(address(verifier));
    }

    /// @notice Tests the happy path of anchoring a root.
    function testAnchorHappyPath() public {
        uint256 counter = 1;
        bytes32 merkleRoot = keccak256("root");
        bytes memory proof = hex"1234";
        uint256[] memory inputs = new uint256[](1);
        inputs[0] = 123;

        anchor.anchor(runId, counter, merkleRoot, proof, inputs);
        
        assertEq(anchor.runCounter(runId), 1);
        assertEq(anchor.anchoredRoot(runId, 1), merkleRoot);
    }

    /// @notice Tests that the monotonic counter is enforced.
    function testMonotonicity() public {
        uint256 counter = 1;
        bytes32 merkleRoot = keccak256("root");
        bytes memory proof = hex"1234";
        uint256[] memory inputs = new uint256[](1);

        anchor.anchor(runId, counter, merkleRoot, proof, inputs);
        
        // Try to anchor same counter again
        vm.expectRevert("counter not monotonic");
        anchor.anchor(runId, counter, merkleRoot, proof, inputs);
        
        // Try to skip a counter
        vm.expectRevert("counter not monotonic");
        anchor.anchor(runId, counter + 2, merkleRoot, proof, inputs);
    }

    /// @notice Tests that the anchor function reverts if the verifier rejects the proof.
    function testVerifierRejection() public {
        uint256 counter = 1;
        bytes32 merkleRoot = keccak256("root");
        bytes memory proof = hex"DEADBEEF"; // Invalid proof
        uint256[] memory inputs = new uint256[](1);

        // Mock verifier to return false
        MockVerifierFailing failingVerifier = new MockVerifierFailing();
        RunAnchor anchor2 = new RunAnchor(address(failingVerifier));
        
        vm.expectRevert("invalid proof");
        anchor2.anchor(runId, counter, merkleRoot, proof, inputs);
    }
}

/// @title Mock Verifier (Failing)
/// @notice A mock verifier that always returns false.
contract MockVerifierFailing is IEzklVerifier {
    /// @notice Simulates proof verification failure.
    /// @return Always returns false.
    function verify(bytes calldata, uint256[] calldata) external pure returns (bool) {
        return false;
    }
}

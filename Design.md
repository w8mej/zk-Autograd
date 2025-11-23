# Design.md — zk-Autograd (EZKL + Adam)

## ZK statement (per step)

For each optimizer step *t*, the prover attests:

Given committed previous weights `C(w_t)`, committed gradient `C(g_t)`, Adam state `m_t,v_t`, hyper‑parameters `(lr, beta1, beta2, eps)` and step circuit `F_adam`:

1. `m_{t+1} = beta1*m_t + (1-beta1)*g_t`
2. `v_{t+1} = beta2*v_t + (1-beta2)*g_t^2`
3. bias‑correction and update:
   `w_{t+1} = w_t − lr * m̂_{t+1} / (sqrt(v̂_{t+1}) + eps)`

The proof reveals only public inputs (commitments, hyper‑params, step index, circuit id) and proof hash.

## Circuit construction

**Backend:** EZKL over ONNX graphs. 

1. `AdamStep` / `SGDStep` module exported to ONNX (see `src/zk_autograd/step_circuit.py`).
2. Inputs quantized to fixed‑point and mapped to field elements.
3. Setup performed once:
   - `ezkl.gen_settings()`
   - `ezkl.get_srs()`
   - `ezkl.compile_circuit()`
   - `ezkl.setup()` 
4. Per‑step proving:
   - `ezkl.gen_witness()`
   - `ezkl.prove()` 
5. Verification:
   - `ezkl.verify()` in verifier CLI. 

## TEE key sealing

### Nitro
- Proving key encrypted in KMS.
- Enclave requests KMS Decrypt with attestation document; KMS releases only if PCR/ImageSha384 matches policy. 

### OCI CVM
- Proving key stored as an OCI Vault secret encrypted under a Vault master key.
- CVM produces SEV attestation report including measurement; a key broker verifies measurement before releasing secret to the VM.

## Replay / rollback defense

Because Nitro enclaves are ephemeral and lack persistent storage, a monotonic counter must live outside the enclave. 

Design:
1. Host finalizes Merkle root for run.
2. Host (or enclave) performs **conditional write** to a monotonic‑counter store:
   - AWS: DynamoDB/QLDB with `counter == prev+1`.
   - OCI: Object Storage conditional PUT (ETag) on a versioned object.
3. Verifiers reject any run missing a valid counter anchor.

PoC implements `local` backend in `src/zk_autograd/anchoring.py`.

## Side‑channel mitigations (partial)

- Keep prover enclave minimal (no shells, no debug).
- Prefer constant‑time math kernels when possible.
- Pad payload sizes and batch shapes to reduce leakage from size/timing.
- Add rate‑limits and fixed‑cadence proving.

## Limitations

- Tiny models only.
- Fixed‑point quantization introduces approximation.
- No formal side‑channel proof.

## Proof splitting per-layer/per-block

EZKL supports splitting large ONNX graphs into multiple circuits using commitments and then aggregating their proofs. 

This repo exercises that plumbing with a logical block split fallback via `prove_step_chunks()`.

## On-chain Merkle anchoring (EVM)

Use EZKL to generate Solidity verifiers:

- `create_evm_verifier` for single proofs.
- `create_evm_verifier_aggr` for aggregated proofs.

Then call `RunAnchor.anchor(...)` with the aggregated proof and public inputs.

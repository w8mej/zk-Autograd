# Security.md — Threat Model & Security Properties

## Threat model

| Adversary | Capability | Goal | Mitigation |
|---|---|---|---|
| Honest‑but‑curious host | Reads host memory/logs, sees traffic to TEE | Learn batch/gradients or proving key | TEE isolation; key sealed to measurement; quantized inputs only |
| Malicious host | Fabricate proofs, roll back/skip steps, alter logs | Make run look honest | EZKL soundness; per‑step proofs; Merkle roots + monotonic anchors |
| Malicious auditor | Samples steps | Exfiltrate secrets | Verifier sees only public inputs |

## Security properties

1. **Step soundness:** each logged EZKL proof implies correct Adam/SGD update for committed inputs.
2. **Tamper evidence:** changing any proof/hash changes Merkle root.
3. **Replay resistance:** monotonic counter anchoring prevents run rollback.
4. **Data‑in‑use protection:** proving key + witness stay inside TEE.
5. **Robustness:** Verifier is fuzzed with Hypothesis to prevent parsing exploits.

## TEE sealing

- **Nitro:** KMS attestation policy binds key use to enclave PCRs/ImageSha384. 
- **OCI CVM:** SEV measurement attestation gates OCI Vault secret release. 

## Supply Chain Security (SLSA)

To prevent tampering before the code reaches the TEE, we implement:
- **Image Signing:** Docker images are signed with **Sigstore/Cosign** in CI.
- **SBOM:** A Software Bill of Materials (SPDX) is generated with **Syft** for every build.
- **Verification:** The TEE host verifies the image signature before launching the enclave.

## Known gaps

- Side‑channels not eliminated; only mitigated.
- Large models require proof splitting/aggregation.
- Optimizer state correctness proved only for Adam/SGD (PoC).

## Hardening roadmap

- Aggregated proofs per epoch.
- On‑chain anchoring of Merkle roots.
- Safer key brokers and sealed storage.
- Broader optimizer coverage (Adafactor, LAMB).

## Triton fused Adam kernels

We include optional Triton GPU kernels (`src/zk_autograd/triton_kernels.py`) to reduce timing/shape leakage by:
- fixed block sizes
- minimal branching
- padding to constant multiples

Install and enable:

```bash
pip install -e .[gpu]
USE_TRITON=1 zk-train --steps 100
```

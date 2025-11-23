# OCI Confidential VM Deployment (EZKL PoC)

Outline for running the prover on an OCI Confidential VM (AMD SEV-backed).

## 1) Prepare artifacts
```bash
zk-setup-zk --circuit adam --out prover/keys
```
Store `pk.key` as an OCI Vault secret (encrypted).

## 2) Provision CVM
Use a Confidential VM shape in a private VCN.

## 3) Seal key to CVM attestation
- CVM produces SEV attestation report with measurement.
- Your key broker verifies report before releasing the Vault secret to the VM. citeturn0search7turn3search31

## 4) Replay/Rollback prevention
Anchor Merkle roots to:
- OCI Object Storage versioned object with conditional PUT (ETag)
- Or an on-chain attestation.

## Files
- `cloud-init.yaml`
- `start_prover.sh`
- `attestation_notes.md`

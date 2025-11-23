# AWS Nitro Enclaves Deployment (EZKL PoC)

This folder shows how the prover runs inside a Nitro Enclave.

## 1) Prepare EZKL artifacts
Run on a dev machine:

```bash
zk-setup-zk --circuit adam --out prover/keys
```

Encrypt `pk.key` under a KMS CMK. Keep only ciphertext on the parent.

## 2) Build EIF
Use `enclave.Dockerfile` and convert to EIF via `nitro-cli build-enclave`.

## 3) Seal proving key to enclave measurement

- Enclave requests KMS `Decrypt` with a signed attestation document.
- KMS policy uses `kms:RecipientAttestation:ImageSha384` / PCR condition keys so **only this EIF measurement can receive plaintext, and it is returned encrypted to the enclave public key.

## 4) Replay/Rollback prevention

Nitro enclaves are stateless and have no persistent storage.
Anchor each run Merkle root to a monotonic counter service:
- DynamoDB conditional PutItem (counter==prev+1)
- Or QLDB ledger

## Files
- `enclave.Dockerfile` — prover EIF image.
- `build_eif.sh`, `run_enclave.sh`
- `vsock_proxy.py` — vsock <-> HTTP bridge (placeholder).

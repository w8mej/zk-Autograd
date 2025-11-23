# attestation_notes.md

PoC note: OCI CVM attestation and Vault-gated key release is not wired here.

Suggested hardening:
1. Obtain CVM attestation evidence from OCI.
2. Verify measurement against expected prover image hash.
3. If valid, fetch proving key from OCI Vault to /dev/shm.
4. Start prover and keep key only in encrypted memory.


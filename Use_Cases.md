# Use_Cases.md — zk-Autograd (Google-style)

## Use Case 1: Auditable fine‑tuning for regulated healthcare LLMs

**Context:** Hospitals fine‑tune models on PHI but must prove training happened under approved procedures without sharing PHI.  
**Goal:** Enable external auditors to verify steps without accessing data.  
**Non‑goals:** Real‑time certification of every gradient at scale.  

**Actors:** ML team (trainer), Compliance auditor (verifier).  

**Design:** Training steps are proved in a TEE. Proof hashes are logged and published with Merkle roots. Auditor samples random steps weekly.  

**Risks:** Quantization error may blur exactness; side‑channels in TEE; auditor sampling bias.  

**Success metrics:** ≥99% sampled steps verify; zero PHI exposure during audit.

---

## Use Case 2: Third‑party marketplace model updates

**Context:** Model vendors distribute fine‑tuned checkpoints to customers who want assurance that training followed a declared recipe.  
**Goal:** Verifiable update provenance for each release.  
**Non‑goals:** Full reproducibility of training data.

**Actors:** Vendor trainer, Customer verifier.  

**Design:** Vendor publishes proof bundles+logs via torrents and a web portal. Customer verifies a random subset before accepting a release.  

**Risks:** Vendors may only prove selected steps unless enforced by policy; torrent metadata leakage.  

**Success metrics:** Customer acceptance flow includes successful verification; reduced dispute rate.

---

## Use Case 3: Defense / government pipelines with air‑gapped audit

**Context:** Sensitive environments prohibit cloud audit tooling.  
**Goal:** Enable offline integrity checking of training.  
**Non‑goals:** Public proof sharing.

**Actors:** Classified training team; internal inspector general.  

**Design:** Proofs/logs are exported on removable media; torrents used inside internal network for replication. Inspector verifies in an offline enclave-free environment.  

**Risks:** Media handling; need strict chain-of-custody; TEEs still require trust.  

**Success metrics:** Offline verification completes within SLA; proofs stored for 7+ years.

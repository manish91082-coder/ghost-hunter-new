# PHANTOMX / FLASH LOAN GHOST HUNTER
# Phase 19 Accelerated Gate Plan

## Purpose
Reduce wall-clock time without weakening any acceptance gate. Independent production evidence lanes run in parallel; no lane is promoted by inference from another lane.

## Operating Rule
A `next` cycle should process a **batch of independent repository-safe actions** rather than one micro-step. CI observation, forensic review, evidence-package preparation, and gate documentation may advance together. External production facts remain evidence-gated.

## Current certified baseline
- Phase-19 deterministic workflow #442: GREEN.
- Private-relay validator workflow #446: GREEN.
- Production readiness: NOT ACHIEVED.
- Live signing: BLOCKED.
- Public broadcast: BLOCKED.
- Live capital: LOCKED.

## Parallel lanes

### Lane A — Polygon production authority
Target evidence:
1. explicitly approved HTTPS Polygon providers
2. intended executor address
3. chain ID 137
4. common observed block
5. owner observation
6. runtime-code identity/hash
7. quorum agreement
8. owner-to-expected-signer binding
9. canonical evidence hash
10. operator + independent witness provenance

Repository artifacts already prepared:
- `PHASE19_PRODUCTION_AUTHORITY_EVIDENCE_INTAKE.md`
- `PHASE19_PRODUCTION_AUTHORITY_OBSERVATION_RUNBOOK.md`
- `scripts/validate_production_authority_evidence.py`
- `tests/phase19/test_production_authority_evidence_validator.py`

### Lane B — Production signer identity
Target evidence:
1. fresh cryptographically random challenge
2. exactly one external production signature
3. independently recovered signer address
4. exact expected-address match
5. provenance record

Repository artifacts already prepared:
- `PHASE19_SIGNER_IDENTITY_RUNBOOK.md`
- `PHASE19_SIGNER_EVIDENCE_INTAKE.md`
- `scripts/verify_signer_identity.py`
- `scripts/validate_signer_evidence.py`

### Lane C — Private relay
Target evidence:
1. explicitly approved production relay identity
2. HTTPS endpoint policy
3. explicit `private=true`
4. externally configured authentication
5. controlled observation in isolated environment
6. non-secret response classification
7. evidence hash + provenance

Repository artifacts already prepared:
- `PHASE19_PRIVATE_RELAY_EVIDENCE_INTAKE.md`
- `scripts/validate_private_relay_evidence.py`
- Phase-19 adversarial validator tests

Current official Polygon research finding: Polygon launched its Private Mempool in 2026 for private transaction submission, with a free starting tier; Polygon states that submission is private while read operations continue through existing RPC providers. Access details are handled through Polygon's request/access process, so this service is a **candidate infrastructure option, not automatic project approval**. [Polygon Labs, Apr/May 2026]

### Lane D — Identical-artifact shadow/staging
Target evidence:
1. exact immutable software commit / artifact digest
2. production configuration identity without secrets
3. production-like execution environment
4. preflight/simulation result
5. submission-path observation without live capital release
6. receipt/lifecycle observation where applicable
7. independent witness/provenance

Rule: no fork test, unit test, or historical deployment claim substitutes for this lane.

### Lane E — Realized economics / PnL
Target evidence:
1. exact immutable artifact identity
2. opportunity/route evidence
3. exact quote evidence
4. gas/relay/borrow/DEX and all applicable cost inputs
5. execution and settlement evidence
6. realized gross result
7. realized total cost
8. realized net PnL
9. strict invariant: `realized net > $0.20`
10. independent reconciliation/provenance

Rule: estimated, simulated, or hypothetical PnL never closes the realized-PnL gate.

## Serialization to avoid unnecessary waiting
Only these dependencies are serialized:
- signer proof is needed before a signer-bound production authority decision can be finalized.
- identical-artifact shadow evidence uses the final verified artifact identity.
- realized-PnL evidence is evaluated only after the observation/submission chain is independently controlled.

All other repository preparation, validators, adversarial tests, evidence schemas, and forensic review work should proceed concurrently.

## External evidence fast path
When operator-controlled production inputs become available, collect all applicable non-secret evidence in one controlled session instead of separate sessions:
- signer challenge/signature proof
- Polygon authority quorum snapshot
- private relay observation
- shadow/staging observation
- realized settlement/PnL reconciliation

Do not combine secrets into the bundle. Private keys, seed phrases, keystore passwords, relay auth tokens, signed/raw transactions, and other sensitive credentials remain outside repository evidence.

## Gate promotion rule
A gate changes from `BLOCKED` to `GREEN` only when:
`external evidence captured → repository validator accepts → independent review passes → provenance retained`.

## Current next batch
1. Observe the latest Phase-19 CI result for the newest repository commit.
2. Prepare one consolidated external-evidence session covering all currently satisfiable independent lanes.
3. Keep all production locks intact until each required gate independently passes.

## Research note
Polygon's current documentation indicates that dedicated/private RPC endpoints are available from third-party providers and that Polygon does not itself recommend a single RPC provider. Polygon documentation also warns that public endpoints can be best-effort or rate-limited for production use. Current provider documentation from QuickNode and Alchemy confirms Polygon PoS mainnet uses chain ID 137 and current Bor-based infrastructure after the 2026 Erigon sunset. These facts inform infrastructure selection, but they do not by themselves constitute project-specific provider approval.

# Phase 19 Consolidated External Evidence Session

## Purpose
Execute one controlled evidence session that captures every currently satisfiable production-gate lane without weakening any independent acceptance criterion.

This document is an operator/session protocol, not production authorization.

## Immutable session inputs
Freeze before observation:

- verified software/artifact commit
- intended Polygon executor candidate
- expected production signer address
- approved Polygon HTTPS provider set and quorum
- approved private-relay identity and access method
- shadow/staging environment identity
- session operator identity
- independent witness identity
- UTC session start time

No private keys, seed phrases, keystore passwords, relay credentials, raw transactions, signed transactions, or transaction hashes are copied into the evidence bundle.

## Session order

### S0 — Freeze and preflight
1. Confirm current verified software commit.
2. Confirm all target addresses and provider identities are frozen.
3. Confirm production capital remains locked.
4. Confirm no public-RPC or public-relay fallback is enabled.
5. Create one session identifier and immutable timestamp.

### S1 — Signer identity lane
Capture:
- fresh 32-byte challenge
- one externally produced 65-byte signature
- expected signer address
- recovered signer address
- verifier commit
- operator/witness provenance

Then run the existing signer verifier and non-secret evidence validator offline.

### S2 — Polygon authority lane
Using only explicitly approved HTTPS providers:
- observe chain ID 137
- determine the common block
- read intended executor owner
- capture runtime code identity/hash
- require quorum agreement
- verify owner == expected signer
- construct and hash the non-secret authority package
- run the existing offline authority validator

Fork/public observations are never promoted to this lane.

### S3 — Private relay lane
Using only the explicitly approved production private relay:
- confirm HTTPS endpoint policy
- confirm explicit private assertion
- authenticate externally
- perform the controlled observation
- retain only non-secret response classification
- construct/hash evidence package
- run the existing offline private-relay validator

Authentication material remains outside the evidence package.

### S4 — Identical-artifact shadow/staging lane
Against the exact frozen artifact identity:
- record artifact digest/commit
- record non-secret configuration identity
- execute the production-like shadow/staging scenario
- capture preflight/simulation outcome
- observe the submission path without live capital release
- capture lifecycle/receipt evidence where applicable
- retain witness/provenance

The result must be explicitly tied to the same immutable artifact identity used for later gates.

### S5 — Realized economics lane
Only after the controlled observation/submission chain is independently established:
- capture exact opportunity/route evidence
- capture exact quotes
- capture gas, borrow, DEX, relay and all other applicable costs
- capture execution and settlement evidence
- reconcile gross result and total costs
- calculate realized net PnL
- require strict `realized net > $0.20`
- retain independent reconciliation/provenance

Simulated or estimated profit never closes this gate.

## Parallelization rule
S1, S2 and S3 can be performed concurrently when their external inputs are independently approved. S4 can run concurrently once the immutable artifact is frozen. S5 is the only lane with a hard dependency on a controlled observation/submission chain.

## Evidence package layout
Keep evidence segregated by lane:

- `signer/` — signer non-secret evidence only
- `polygon_authority/` — provider quorum evidence only
- `private_relay/` — relay observation evidence only
- `shadow_staging/` — identical-artifact evidence only
- `realized_pnl/` — settlement/economic evidence only
- `session/` — session identifier, timestamps, operator/witness provenance

A consolidated manifest may reference lane hashes, but must not duplicate secrets.

## Gate promotion
Each lane follows independently:

`external observation → lane validator → independent review → provenance retained → gate decision`

One lane cannot satisfy or waive another lane.

## Failure handling
If any observation contradicts the frozen inputs, produces ambiguous quorum, fails validation, exposes prohibited material, or cannot establish independent provenance:

`FAIL → FREEZE → FORENSIC → PATCH/REPEAT ONLY THE FAILED LANE`

Do not restart already-certified unrelated lanes.

## Prohibited actions
- no live capital release
- no live broadcast
- no public relay fallback
- no public-RPC substitution for production authority
- no private key handling in repository/chat
- no production authorization based solely on CI/fork tests

## Completion condition
The session is complete only when every attempted lane has a recorded outcome of `GREEN`, `BLOCKED`, or `FAILED`, with evidence provenance. Production readiness remains `NOT ACHIEVED` until every mandatory P0 gate is independently GREEN and the final re-audit is complete.

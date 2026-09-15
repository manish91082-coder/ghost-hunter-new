# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation-bearing commit: `fe748b626060a7a2a63d79e309bb633becdefa17`
- Latest implementation-bearing hardening before this checkpoint: `839f8c30d8b764723135ed135e1f1320fdad682b`
- Earlier implementation-bearing hardening: `6ff08b45e0250880e66e1545fa2f29691a9759ae`, `e40aa7b4abc86cce0bee0951717ab3b7aa651f70`
- Phase: Phase 19 execution-integrity / E2E policy harness
- Live mainnet execution: **BLOCKED**
- Live capital authorization: **BLOCKED**
- Production readiness: **NOT ACHIEVED**
- Economic invariant: realized net profit must be **strictly greater than $0.20 after all applicable costs**

## 1. NON-NEGOTIABLE SAFETY / CONTROL RULES
- Evidence first; contradictory or missing evidence is UNKNOWN/BLOCKED.
- Fail closed on quote, proof, simulation, authorization, nonce, signer, relay, authority, or settlement inconsistency.
- AI is advisory and cannot override deterministic economics, preflight, governance, authorization, or settlement.
- Private execution has no public fallback.
- Live capital remains locked until every P0 gate has reproducible evidence.
- No live signing, public broadcast, production execution authorization, or live capital is granted during Phase 19 certification.

## 2. CANONICAL PRODUCTION SPINE
`LIVE BLOCK → DATA/RPC QUORUM → EXACT QUOTES → ROUTE ENGINE → LOAN OPTIMIZER → EXACT COST MODEL → WORST-CASE NET PNL → AI RANKING → EVM PREFLIGHT → GOVERNOR → SIGNER → PRIVATE SUBMIT → ON-CHAIN EXECUTOR → RECEIPT AUDITOR → REALIZED NET PNL`

Initial scope: Polygon, Aave V3, QuickSwap V2, Uniswap V3, USDC/WETH/WMATIC/WBTC, direct two-leg `A → B → A`.

## 3. VERIFIED IMPLEMENTATION CAPABILITIES
Phase 19 includes strict realized-profit gating, deterministic all-in economics, Keccak hashing, immutable intent/auth/envelope binding, exact block-bound quotes, route simulation and topology commitment, loan optimization, EVM preflight, Governor, signer boundary, durable SQLite nonce/transaction state, atomic replacement/recovery coordination, private-only submission, chain/recovery/reorg/replacement handling, receipt reconciliation, Solidity executor controls, Polygon fork harness, and adversarial/regression coverage.

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage for pre-submission `SIGNED` state, CI runtime modernization, and duplicate-private-submission prevention before relay I/O.

## 4. MVP REPOSITORY CLEANUP / CONSISTENCY
The active branch has been reduced to the targeted Phase-19 implementation/test spine.

- Removed obsolete `v2/` and `v3/` runtime/AI/training/deployment/state stacks.
- Removed legacy root `__init__.py` and obsolete secret-bearing `config/settings.json` configuration surface.
- Rewrote `PROJECT_DETAILS.md` to describe the current Phase-19 MVP instead of deleted legacy launchers/runners/AI artifacts.
- Preserved the Phase-19 Solidity contract, tests, `phantomx/` execution-integrity modules, workflow, requirements, and audit/continuity evidence.

**Security note:** the removed legacy settings file contained a Telegram bot token. Deletion does not revoke a credential that may exist in Git history; revoke/rotate that credential externally.

## 5. CURRENT AUTHORITY-PROOF HARDENING
`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer verifies Polygon chain identity on every configured provider, chooses one common observation block, reads executor `owner()` and runtime bytecode from every provider at that identical block, requires configured provider quorum on owner + runtime-code hash, rejects duplicate identities/wrong chain/insufficient agreement/ambiguous splits, and returns immutable `ExecutorAuthorityEvidence`.

This is read-only and cannot sign or submit transactions.

## 6. VERIFIED CI EVIDENCE
- Run `#258`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 402/402 Python.
- Run `#261`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 403/403 Python.
- Run `#262`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 403/403 Python.
- Run `#266`: GREEN, 14 EVM + 3 Polygon smoke + 1 fork probe + 404/404 Python.
- Run `#268`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 405/405 Python.
- Run `#269`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 406/406 Python.
- Run `#270`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + 407/407 Python.
- Run `#273`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + 408/408 Python.
- Run `#275`: Python gate failed only on a brittle sorted-list assertion; 413 tests, 1 failure.
- Repair commit `e8ded6459a8d7a070310f49481f335043617650e` corrected the assertion.
- Run `#276`: GREEN, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + 413/413 Python.

Historical runner logs also show a successful Phase-19 Python suite of 164/164 tests, but that run checked out an older SHA. Current implementation commits `839f8c30...` and `fe748b626...` have no exposed push-triggered run through the connector's commit-run filter, so no current-head GREEN claim is made.

## 7. CURRENT BLOCKERS / P0 GATES
1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, and chat.

## 8. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 9. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task:** lead-directed submission-path integration audit and duplicate-submission hardening.

**New work completed:**
- `phantomx/execution_submission.py` now revalidates the durable transaction + nonce lifecycle immediately before private relay I/O and requires the prepared artifact to remain in exact `SIGNED` state.
- A repeated call using an already `PRIVATE_SUBMITTED` prepared artifact is rejected before any second relay call.
- `tests/phase19/test_execution_submission.py` now explicitly proves duplicate submission is blocked before network I/O and that durable state remains `PRIVATE_SUBMITTED`/`SUBMITTED` after the first successful submission.

**Current verdict:** the submission boundary is stronger against caller retries and stale prepared-object reuse. The change is not yet current-head CI-certified through the available connector; therefore no GREEN claim is made.

**Authority/input finding:**
- Production authority remains blocked pending approved Polygon provider quorum + intended executor identity + expected signer identity.
- Historical public RPC endpoints are not promoted into production authority.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** obtain authoritative fresh CI for `fe748b626...`; if green, continue the startup/recovery and shadow/staging audit. If not green, perform failure forensics before further implementation work.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**

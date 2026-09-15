# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD
- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation-bearing commit: `164d4522abdf2b224e91a514a1d2bea065f30535`
- Prior implementation-bearing commits: `6ff08b45e0250880e66e1545fa2f29691a9759ae`, `e40aa7b4abc86cce0bee0951717ab3b7aa651f70`, `eb9ee0c6b62e349500f177b8fa761673ce1a999b`
- Certification PR: `#1` (DRAFT, open, base `master`)
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

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, quorum-bound read-only executor authority attestation, nullable durable-nonce-hash replacement coverage, restart-audit coverage proving a pre-submission `SIGNED` nonce may legitimately remain hash-free while the durable transaction record remains authoritative, CI runtime modernization to Node 24-compatible action majors, and pre-network blocking of repeated submission of an already-submitted durable artifact.

## 4. CI CERTIFICATION PATH
The Phase-19 workflow now runs on branch pushes and on pull requests to `master`, while ignoring status-only changes. It uses `actions/checkout@v5` and `actions/setup-python@v6`, then performs Foundry compile, EVM integration, Polygon fork protocol smoke, Polygon fork execution probe, and the Phase-19 unittest suite.

A draft certification PR `#1` was opened specifically to expose current-head PR-triggered checks without merging anything. The connector's commit-run filter still currently returns no PR workflow run for the latest head, so no CI pass is claimed.

Historical run `#276` remains GREEN but predates the newest hardening and is not current-head certification.

## 5. CURRENT AUTHORITY-PROOF HARDENING
`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer verifies Polygon chain identity on every configured provider, chooses one common observation block, reads executor `owner()` and runtime bytecode from every provider at that identical block, requires configured provider quorum on owner + runtime-code hash, rejects duplicate identities/wrong chain/insufficient agreement/ambiguous splits, and returns immutable `ExecutorAuthorityEvidence`.

This is read-only and cannot sign or submit transactions.

## 6. CURRENT BLOCKERS / P0 GATES
1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

Required before real production authority attestation: approved Polygon RPC provider set, controlled confirmation of the intended deployed executor address, and expected signer address. Private key material stays outside repository code, fixtures, logs, and chat.

## 7. GO-LIVE RULE
Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

## 8. CURRENT CHECKPOINT
**Timestamp:** 2026-09-15

**Atomic task:** expose authoritative current-head CI through a controlled draft certification PR.

**New work completed:**
- Extended `.github/workflows/phase19-tests.yml` with a `pull_request` trigger targeting `master`, preserving the `PROJECT_STATUS.md` path ignore.
- Opened draft PR `#1` from `phase-19-e2e-harness` to `master` solely to obtain independently observable PR CI evidence. The PR is explicitly non-merge and does not grant production authority.
- Verified the latest implementation-bearing head is `164d4522abdf2b224e91a514a1d2bea065f30535`.
- The available commit workflow-run filter still exposes no run for this current PR head, so certification remains **UNKNOWN / NOT GREEN**, not fabricated.

**Current verdict:** the repository is structurally coherent and the CI path is now designed to expose current-head PR checks. Production execution remains blocked because fresh certification and all production P0 authority inputs are still outstanding.

**Safety boundary:** no live signing, public broadcast, live capital, or production execution authorization.

**Next atomic action:** inspect the PR-triggered workflow once exposed; if GREEN, continue the highest-value remaining production-like gate. If the workflow fails, perform failure forensics before further feature work.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**

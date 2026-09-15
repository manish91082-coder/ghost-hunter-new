# PHANTOMX / FLASH LOAN GHOST HUNTER
# PROJECT STATUS • MASTER CONTINUITY • MISSION CONTROL

> Canonical project-state anchor. Synchronize this file on every project response. Evidence first, fail closed, no fabricated passes.

## 0. CURRENT RESUME CARD

- Project: `manish91082-coder/ghost-hunter-new`
- Active branch: `phase-19-e2e-harness`
- Latest implementation-bearing commit: `e8ded6459a8d7a070310f49481f335043617650e`
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

Phase 19 currently includes strict realized-profit gating, all-in deterministic economics, Ethereum Keccak hashing, immutable intent/authorization/envelope binding, exact block-bound quotes, shared market-block handling, route simulation and topology commitment, loan optimization, EVM preflight, deterministic Governor, signer boundary, durable SQLite nonce/transaction state, atomic execution/replacement coordination, private-only submission, chain/recovery/reorg/replacement handling, receipt reconciliation, Solidity executor controls, Polygon fork harness, and adversarial/regression coverage.

Recent hardening includes exact observed-transaction recovery binding, no manufactured nonce ownership for unknown replacements, repeated replacement-chain persistence, atomic replacement rollback, semantic intent-mutation protection, exact serialized signer-envelope certification, one-path coordinator artifact-chain certification, and quorum-bound read-only executor authority attestation.

## 4. CURRENT AUTHORITY-PROOF HARDENING

`phantomx/executor_authority.py` provides `observe_executor_authority_quorum(...)`.

The quorum observer:
- verifies every configured provider identifies Polygon;
- reads each provider's latest block and chooses one common block (`min(blocks)`);
- reads executor `owner()` and runtime bytecode from every provider at that identical common block;
- requires unique provider consensus of at least the configured quorum on owner + runtime-code hash;
- rejects duplicate provider identities, wrong-chain providers, insufficient agreement, and ambiguous split consensus;
- returns the existing immutable `ExecutorAuthorityEvidence`, preserving signer/governor compatibility.

This is a read-only authority attestation path. It does not sign or submit transactions.

## 5. VERIFIED CI EVIDENCE

### Prior certified gates

- Run `#258` on `05a9becc1542f6d588cbfc77691beacb8087f29b`: **GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **402/402 Python**.
- Run `#261` on `8212bfd315d5aec11521bc40a3302d88f5bbc72c`: **GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#262` on `3417387353a0866f50115e873ed5a5353a82fb0c`: **GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **403/403 Python**.
- Run `#266` on `e0f8d4d52118ff9cdeae220038029d1baef2307b`: **GREEN**, 14 EVM + 3 Polygon smoke + 1 Polygon fork probe + **404/404 Python**.
- Run `#268` on `ed3451f82c4c4934fe1c5bfe23623222a10d3a3b`: **GREEN**, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + **405/405 Python**.
- Run `#269` on `de6eee477f0e1b8844c88de26be3e884cb8e9d4e`: **GREEN**, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + **406/406 Python**.
- Run `#270` on `2cf90abcf8e613f09fefaa7ab35c4262be53e779`: **GREEN**, 14/14 EVM + 3/3 Polygon smoke + 1/1 fork probe + **407/407 Python**.
- Run `#273` on `2b1a762181ff7488d234110b5d1596343d5dbbf5`: **GREEN**, 14/14 EVM + 3/3 Polygon smoke + 1/1 Polygon fork execution probe + **408/408 Python**.

### Authority-quorum checkpoint

- Commit `408588c1a6a99c4cff545a6f5998c1500cce40ff`: added quorum-bound executor authority observation and adversarial coverage.
- Run `#275` for that commit: **FAILED** only in the Python unit-test step.
- EVM compile/integration, Polygon fork smoke, and Polygon fork execution probe all passed before the Python gate failed.
- Python result: **413 tests, 1 failure**.
- Exact failure: `test_quorum_observation_uses_one_common_block_and_consensus_owner_and_code` asserted a sorted method list in non-sorted expected order. Actual sorted set was `['eth_blockNumber', 'eth_call', 'eth_chainId', 'eth_getCode']`; the test expected `['eth_call', 'eth_chainId', 'eth_getCode', 'eth_blockNumber']`.
- Diagnosis: **test assertion defect, not an observed production-logic failure**.
- Commit `e8ded6459a8d7a070310f49481f335043617650e`: repaired the regression to compare the method set order-independently.
- Run `#276` on `e8ded6459a8d7a070310f49481f335043617650e`: **GREEN**.
- Run #276 passed **14/14 EVM**, **3/3 Polygon fork smoke**, **1/1 Polygon fork execution probe**, and **413/413 Python** tests.
- The corrected quorum regression passed without changing the quorum implementation.

Node.js 20 deprecation messages remain warnings from existing GitHub Actions action versions.

## 6. CURRENT BLOCKERS / P0 GATES

1. Controlled production signer identity proof without exposing private key material.
2. Controlled production Polygon network/provider authority proof using explicitly approved production endpoints and the deployed executor address.
3. Production private relay capability with no public fallback.
4. Startup/recovery safety under production-like conditions.
5. Controlled shadow/staging evidence using the identical immutable artifact chain.
6. Final realized live PnL evidence after all preceding gates are GREEN.
7. Live mainnet capital deployment remains forbidden.

**Required inputs before real production authority attestation:** an approved production Polygon RPC endpoint set, the deployed executor address, and the expected signer address. Private key material must remain outside repository code, logs, test fixtures, and chat.

## 7. GO-LIVE RULE

Every P0 gate must be GREEN with reproducible evidence before live capital. Any unchecked gate means **LIVE CAPITAL = LOCKED**.

The first live hunt is not date-scheduled. It becomes eligible only after deterministic artifact certification, production signer/network authority proof, private-relay proof, startup safety, controlled shadow execution, and final authorization all pass.

## 8. COMPLETION / DISTANCE ASSESSMENT

Engineering readiness estimates only:
- Core architecture + deterministic implementation: approximately **75–80%**.
- Go-live evidence/certification: approximately **60–65%**.
- Overall mission toward first controlled live hunt: approximately **69–73%**.

These are not formal certification scores.

## 9. CURRENT CHECKPOINT

**Checkpoint:** P19-AUTH-02 production-input readiness audit / controlled authority gate.

**Baseline implementation:** `e8ded6459a8d7a070310f49481f335043617650e`.

**New continuity evidence from Library audit:**
- A prior project artifact records `0x24056bCA6538693aE94Cc97E82f21Ee4EC7f128` as a historical `PhantomXV2FlashLoanExecutor` deployment candidate, with deployment transaction `0x92bc4dc8b3450332c281445fb4443f8725586b18e880a063e0892af2c28c595a`.
- That same artifact explicitly states the address was **NOT YET PROVEN LIVE** and that address identity is not source identity. Required verification includes chain ID 137, bytecode presence/equivalence, interface probes, `owner()`, `DOMAIN_SEPARATOR()`, and canonical runtime-code hash.
- Prior Library runtime notes also contain public Polygon endpoints such as `https://1rpc.io/matic` and `https://polygon-mainnet.matic.quiknode.pro`, but these are historical/runtime observations, not an approved production provider quorum.
- Therefore the historical executor address and public endpoints are **candidates/evidence to validate**, not production authority inputs.

**Repository production-input audit remains:**
- `common/active_rpc.txt` contains `https://ethereum-rpc.publicnode.com`, not a Polygon production authority source.
- Repository search for an approved production signer/executor/RPC input set returned no matching configuration.
- `PHASE19_POLYGON_RPC_STATUS.md` requires approved endpoints plus real transport before production authority attestation and explicitly prevents promotion of legacy/public RPC utilities merely because they connect.

**Decision:** P19-AUTH-01 implementation/test certification remains **GREEN**. P19-AUTH-02 real production authority proof remains **BLOCKED**. The newly found historical executor candidate does not satisfy the gate because it lacks current controlled on-chain verification and there is still no approved signer identity or approved provider quorum.

**Required external/controlled inputs:**
- approved Polygon mainnet RPC provider set with distinct provider identities;
- controlled confirmation that the historical or another deployed executor address is the intended production target;
- expected production signer address.

Once those inputs are supplied through an approved configuration channel, the next operation is observation-only: verify Polygon chain identity, establish one common observation block, attest owner + runtime-code hash by quorum, verify the expected executor interface/domain, and cross-check the expected signer identity. Private key material remains outside repository code, fixtures, logs, and chat.

**Safety boundary:** No live signing, public broadcast, live capital, or production execution authorization is granted. Production authority work remains read-only until every prerequisite gate is evidenced.

**Status-sync:** this checkpoint is synchronized in `PROJECT_STATUS.md`. Status-only synchronization does not itself constitute a new Phase 19 CI execution because the workflow excludes `PROJECT_STATUS.md`-only changes.

---

**MISSION: ACTIVE • LIVE CAPITAL: LOCKED • EVIDENCE STANDARD: STRICT • CONTINUITY: ENABLED • STATUS-SYNC: MANDATORY EVERY RESPONSE**

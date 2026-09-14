# Phase 19 Current Checkpoint

**Date:** 2026-09-14
**Branch:** `phase-19-e2e-harness`
**Latest implementation commit:** `79fe97b421bde681868f7fb7cf600ad368c32b5e`
**Phase:** 19
**Live execution:** LOCKED

## This checkpoint

The nonce layer includes persistent local storage plus a chain-aware recovery boundary. The chain layer validates Polygon-compatible Ethereum JSON-RPC pending-nonce observations, supports explicit provider quorum, advances local state monotonically, and refuses ambiguous observations. The recovery layer distinguishes pending, inclusion, revert, not-found, drop proof, and reorg proof instead of guessing from transaction absence.

### Added / hardened
- `phantomx/polygon_nonce.py`
- `phantomx/recovery.py`
- `tests/phase19/test_polygon_nonce.py`
- `tests/phase19/test_recovery.py`
- `requirements-phase19.txt`
- `.github/workflows/phase19-tests.yml`
- `PHASE19_CHAIN_RECOVERY_STATUS.md`

### CI forensic loop

A GitHub Actions run exposed two real defects and they were repaired rather than suppressed:

1. Ethereum Keccak-256 backend was absent on the runner. `pycryptodome` is now declared and installed by the Phase-19 workflow.
2. Several Phase-19 tests were stale after the `ExecutionIntent`, `Authorization`, and settlement-call schemas evolved. Those fixtures/calls were corrected.

The repaired head `e98cb2ecb5bd0ea1efe3bf5574caf931a0473715` then received a **successful GitHub Actions run** (`34829892489`). The suite completed successfully after the fixes.

This checkpoint commit itself is a status-only update and therefore requires its own workflow run before the newest HEAD can be considered green.

### Chain nonce invariants implemented
- `eth_getTransactionCount(sender, "pending")` is treated as a read-only chain-state observation
- malformed RPC responses and RPC errors fail closed
- local nonce reconciliation uses `max(local_next_nonce, chain_pending_nonce)` and never rolls back
- optional quorum requires distinct provider identities and unique consensus
- no signing, broadcasting, or relay behavior exists in the adapter

### In-flight recovery invariants implemented
- transaction observations carry explicit state and nonce
- active transaction hash must match before recovery mutation
- successful/reverted inclusion requires block and receipt evidence plus gas fields
- `NOT_FOUND` never alone proves a dropped transaction
- drop proof requires chain pending nonce to have advanced beyond the transaction nonce
- reorg proof requires a changed canonical block identity and disappeared receipt
- recovery produces explicit durable-state decisions; it does not silently submit replacements

## Evidence boundary

CI execution is now proven for the repaired `e98cb2ec...` head. The newest status-only HEAD must still complete its own workflow before it is marked green. No implementation commit is treated as test proof without a corresponding run.

No live Polygon RPC call, private-key signing, transaction broadcast, private relay submission, or live capital execution was performed.

## Remaining nonce/recovery P0 work

1. verify green CI for this latest checkpoint HEAD
2. wire the read-only nonce adapter to approved Polygon RPC endpoints and enforce production provider/quorum policy
3. startup crash/restart reconciliation for `RESERVED → SIGNED → SUBMITTED` records
4. deterministic replacement fee-policy bounds and replacement authorization
5. chain observation for dropped/replaced/reorged transactions with durable evidence
6. bind `TransactionRecord` to `ExecutionIntent`, `Authorization`, calldata hash, nonce, and transaction hash

Only after these gates are proven should signer/transaction-builder integration begin.

## Governance

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

Any unresolved P0 gate keeps live execution locked.

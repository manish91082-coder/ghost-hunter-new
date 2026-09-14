# Phase 19 Current Checkpoint

**Date:** 2026-09-14
**Branch:** `phase-19-e2e-harness`
**Latest implementation commit:** `4c80e656b7eeba30b0cb1cdec4f293fea200c584`
**Phase:** 19
**Live execution:** LOCKED

## This checkpoint

The nonce layer now includes a persistent SQLite adapter with atomic writer transactions, restart persistence, local multi-process concurrency coverage, and strict replacement-transaction binding.

### Added / hardened
- `phantomx/sqlite_nonce_store.py`
- `tests/phase19/test_sqlite_nonce_store.py`
- `.github/workflows/phase19-tests.yml`

### Durable/concurrency invariants implemented
- persistent sender-specific nonce cursors
- unique `(sender, nonce)` reservation identity
- globally unique reservation IDs
- atomic reservation allocation under `BEGIN IMMEDIATE`
- observed chain pending nonce can advance the cursor but never roll it back
- state transitions are persisted atomically
- submitted/included/replaced states require transaction hashes
- replacement state requires `replacement_of`
- `replacement_of` must match the currently active transaction hash
- invalid transitions roll back without mutating the record
- state survives process restart through the database file
- concurrent local processes are serialized by SQLite writer transactions
- WAL + `synchronous=FULL` are configured for the local durable store

SQLite WAL is intentionally a **single-host** persistence boundary. It must not be placed on a network filesystem or treated as a multi-host database service. A future multi-host deployment must use a suitable transactional server database while preserving the same nonce invariants.

## Evidence boundary

The implementation and adversarial tests are committed, but **actual CI execution evidence is still open**. GitHub Actions has not yet exposed a workflow run for the Phase-19 branch commits, so no test-pass claim is made.

No Polygon RPC, private-key signing, transaction broadcast, or live capital is enabled.

## Remaining nonce P0 work

1. actual GitHub Actions execution evidence
2. chain pending-nonce reconciliation integration against Polygon RPC
3. crash/restart recovery policy for in-flight signed/submitted records
4. replacement transaction fee-policy integration
5. dropped/reorg observation integration
6. TransactionRecord binding

Only after these gates are proven should signer/transaction-builder integration begin.

## Governance

`FAIL → FREEZE → FORENSIC → PATCH → REGRESSION → VERIFY → STATUS → NEXT`

Any unresolved P0 gate keeps live execution locked.

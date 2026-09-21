# Phase 19 • Durable Nonce Implementation Status

**Date:** 2026-09-14
**Branch:** `phase-19-e2e-harness`
**Checkpoint commit:** `35aaeddd8f18023167e3bc68dce6c32345b302aa`
**Live execution:** LOCKED

## Objective

Upgrade the Phase-19 nonce layer from policy-only/in-memory semantics to a persistent, atomic, concurrency-safe local implementation without enabling signing or broadcast.

## Implemented

### `phantomx/sqlite_nonce_store.py`

- persistent sender-specific nonce cursors;
- unique `(sender, nonce)` reservations;
- globally unique reservation IDs;
- atomic reservation using `BEGIN IMMEDIATE`;
- chain pending nonce reconciliation that only advances the allocator;
- durable state transitions;
- required transaction hashes for submitted/included/replaced states;
- required `replacement_of` for replacement transactions;
- invalid transition rollback;
- restart persistence;
- WAL journaling and `synchronous=FULL`;
- local multi-process writer serialization through SQLite transactions.

### `tests/phase19/test_sqlite_nonce_store.py`

Adversarial coverage includes:

- restart persistence;
- no nonce rollback during chain reconciliation;
- duplicate reservation replay rejection without cursor mutation;
- replacement transaction invariants;
- invalid transition rollback;
- 8-process concurrent reservation test expecting unique nonces `100..107`.

### `.github/workflows/phase19-tests.yml`

A deterministic Phase-19 unittest workflow has been added for actual CI evidence. At this checkpoint GitHub has not yet exposed a workflow run for the latest commit, so **no pass claim is made**.

## Architecture boundary

SQLite WAL is valid only for processes sharing the same host/local filesystem. It is not a multi-host database solution and must not be placed on a network filesystem. If the execution topology becomes multi-host, replace this adapter with a transactional server database while preserving the same nonce invariants.

## Still blocked

- Polygon RPC pending-nonce adapter;
- crash/restart recovery policy for signed/submitted transactions;
- replacement fee bump policy;
- dropped/reorg observation from chain receipts;
- TransactionRecord binding;
- production signer;
- private relay;
- live broadcast.

## Evidence rule

Implementation committed ≠ tests passed ≠ production proven.

Until CI/fork/E2E evidence exists, the nonce gate remains **INCOMPLETE** and live execution remains **LOCKED**.

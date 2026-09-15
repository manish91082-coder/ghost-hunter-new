# Phase 19 Hashing Gate

## Status

Canonical Ethereum Keccak-256 adapter and conformance vectors are now present on `phase-19-e2e-harness`.

## Rules

- Ethereum execution integrity uses Keccak-256.
- Python NIST `sha3_256` is not an acceptable substitute.
- SHA-256 fingerprints remain test-only where explicitly labelled.
- If the Ethereum Keccak backend is unavailable, the production adapter fails closed.
- Hash conformance is not yet evidence of transaction signing, EIP-712 encoding, Polygon execution, or live authorization.

## Conformance vectors

- Keccak-256(`b""`) = `c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470`
- Keccak-256(`b"abc"`) = `4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45`

## Evidence boundary

The repository contains the implementation and tests, but this status document does not claim the tests have executed successfully in CI. The current environment previously failed to reach GitHub over the network, so execution evidence must come from an environment where the test suite actually runs.

## Next gate

Wire the canonical hash adapter into the intent/authorization test models without silently changing the existing test-only SHA-256 fingerprints. Then add deterministic authorization-digest tests and CI execution evidence.

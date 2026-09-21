# Phase 19 Polygon RPC Read Boundary

## Scope

Implemented `phantomx/polygon_rpc.py` as a fail-closed, read-only Polygon JSON-RPC boundary.

### Guarantees

- verifies `eth_chainId` before accepting nonce observations
- accepts only Polygon mainnet chain ID 137
- validates JSON-RPC result/error shape
- validates Ethereum hex quantities
- requires explicit provider identity
- quorum requires distinct providers and unique nonce consensus
- RPC failures and quorum disagreement fail closed
- no signing, transaction submission, public fallback, relay, or broadcast capability

## Evidence

`tests/phase19/test_polygon_rpc.py` covers chain mismatch, malformed/provider errors, nonce observation, and 2-of-3 provider consensus.

GitHub Actions remains the authoritative test runner. No real Polygon RPC call is made by these tests.

## Production integration boundary

The next integration step must supply approved endpoint configuration and a real HTTP transport separately from this policy module. Endpoint health, timeout, chain identity, and quorum observations must be persisted/audited before nonce reconciliation can influence execution.

Existing repository RPC utilities are legacy and are not promoted into the production execution spine merely because they can connect to public endpoints.

Live execution remains LOCKED.

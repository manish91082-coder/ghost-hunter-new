# Phase-19 operator checklist

Run these lanes in parallel after starting one controlled session from the verified engineering artifact.

## Freeze
- [ ] Artifact `e117b6550686cf5e0ff787d9bd7d85e83996db07` recorded.
- [ ] Executor recorded.
- [ ] Expected signer recorded.
- [ ] Approved private relay recorded.
- [ ] Operator + independent witness recorded.

## B Signer
- [ ] `python scripts/verify_signer_identity.py --generate-challenge`
- [ ] External signer produces exactly one signature.
- [ ] Verify signature with expected address + fresh challenge.
- [ ] Preserve only non-secret verifier output and provenance.

## A Polygon authority
- [ ] Use explicitly approved HTTPS providers only.
- [ ] Capture fresh chain-137 quorum observation.
- [ ] Validate `polygon_authority_evidence.json`.

## C Private relay
- [ ] Use explicitly approved private relay only.
- [ ] Authentication stays external.
- [ ] Capture non-secret observation.
- [ ] Validate `private_relay_evidence.json`.

## D Shadow/staging
- [ ] Exact artifact identity matches the frozen artifact.
- [ ] No live capital.
- [ ] No public broadcast.
- [ ] Record executor/signer/proof/authority/staging/submission identities.

## Consolidate
- [ ] All evidence paths are relative to the external session workspace.
- [ ] Run `python scripts/validate_consolidated_evidence_session.py session_manifest.json`.
- [ ] Identity and provenance bindings pass.
- [ ] Independent witness reviews all accepted evidence.

## E Realized PnL
- [ ] Only independently observed settlement counts.
- [ ] Canonical receipt + exact gas + all applicable costs.
- [ ] Realized net profit is strictly greater than $0.20.

## Hard stops
- LIVE SIGNING = BLOCKED until external signer proof is independently accepted.
- PUBLIC BROADCAST = BLOCKED.
- LIVE CAPITAL = LOCKED.

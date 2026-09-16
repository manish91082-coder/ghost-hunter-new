# PHANTOMX / FLASH LOAN GHOST HUNTER
# PHASE-19 EXTERNAL GATE LAUNCH PACKET

## Purpose

Compress the remaining production-gate work into one controlled evidence session without weakening any acceptance criterion.

## Frozen Artifact

- Verified engineering artifact: `fc0df125ee6d0ea694b976ff7d86622b9e45eb15`
- Latest completed CI certification: workflow run `467` on that artifact
- Production authorization is NOT implied by CI.
- Any evidence collected for a different artifact must be rejected or recollected.

## One-Session Inputs

Prepare these inputs before entering the controlled session:

1. Intended Polygon executor address.
2. Expected production signer address.
3. Operator identity.
4. Independent witness identity.
5. Approved Polygon production HTTPS provider set and quorum policy.
6. Approved private submission endpoint and its external authentication configuration.
7. Production-like shadow/staging environment capable of executing the identical immutable artifact chain without live capital.

No private key, seed phrase, keystore password, relay credential, or raw secret is placed in the evidence bundle, repository, fixture, or chat.

## Lane A: Polygon Production Authority

Capture fresh observations from the explicitly approved production HTTPS providers.

Required acceptance chain:

`Polygon chain 137 → common block → executor runtime code identity → owner() → quorum agreement → owner == expected signer → canonical evidence hash → operator/witness provenance`

Public RPC endpoints and fork observations may be used for engineering tests but are not production-authority evidence.

## Lane B: Production Signer Identity

Use the frozen expected signer address.

Required sequence:

`fresh 32-byte challenge → externally held production signer produces exactly one signature → independent recovery → recovered address == expected address → provenance record`

The signing key remains outside repository/chat/evidence artifacts.

## Lane C: Private Relay

Current external research confirms Polygon Private Mempool is live and provides private transaction submission that bypasses the public mempool; Polygon states its free tier is broadly available, while its current access page still directs users to request access/details. This makes it a current candidate infrastructure path, not automatic approval for this project.

Polygon also documents that bloXroute offers private transaction submission on Polygon. This is a second current candidate path.

Acceptance for this project remains stricter than vendor availability:

`explicitly approved endpoint → HTTPS → explicit private assertion → externally configured authentication → controlled observation → provenance → canonical evidence hash`

No public fallback is permitted.

## Lane D: Identical-Artifact Shadow / Staging

Run the production-like flow without live capital using the exact frozen artifact identity `fc0df125ee6d0ea694b976ff7d86622b9e45eb15`:

`artifact identity → quotes/context → route/loan/economic proof → authority evidence → governed signer boundary → private-submit boundary simulation/controlled staging path → receipt/reconciliation evidence`

The staging record must identify the exact artifact commit and prove that no code, route, signer identity, authority input, or economic input was silently changed.

## Lane E: Realized Economics / PnL

This lane is not satisfied by estimates, simulations, or a successful receipt alone.

Acceptance remains:

`canonical receipt → exact gas cost → all applicable execution/relay/loan costs → realized output/input accounting → realized net profit strictly > $0.20`

Live capital remains locked until all prerequisite gates are independently evidenced and the final re-audit passes.

## Session Order

`FREEZE ARTIFACT → CAPTURE A/B/C/D IN ONE CONTROLLED WINDOW → OFFLINE VALIDATE EACH LANE → INDEPENDENT REVIEW → ONLY COMPLETE LANES MAY PROMOTE → PREPARE E FOR CONTROLLED REALIZED-SETTLEMENT OBSERVATION → FINAL RE-AUDIT`

## Fail-Closed Rules

- Missing evidence = `BLOCKED`.
- Historical repository deployment claims = forensic only.
- Public/fork observations = engineering evidence only.
- One lane never makes another lane GREEN.
- Any contradiction = `UNKNOWN/BLOCKED`.
- Any secret material in evidence = reject and rotate/contain as required.
- No live signing or public broadcast is authorized by this packet.
- No live capital deployment is authorized by this packet.
- Evidence accepted by the consolidated coordinator must bind to the manifest artifact, executor, signer, operator, and witness identities.
- Evidence files must be referenced with relative paths inside the external session workspace; absolute paths are rejected.

## Operator Capture Checklist

```text
[ ] Frozen artifact commit confirmed: fc0df125ee6d0ea694b976ff7d86622b9e45eb15
[ ] Executor address confirmed
[ ] Expected signer address confirmed
[ ] Approved Polygon providers + quorum confirmed
[ ] Approved private relay + authentication availability confirmed
[ ] Operator identity recorded
[ ] Witness identity recorded
[ ] Fresh signer challenge/signature captured externally
[ ] Fresh Polygon authority quorum evidence captured
[ ] Fresh private-relay observation evidence captured
[ ] Identical-artifact shadow/staging evidence captured
[ ] All non-secret evidence copied into the external session workspace
[ ] Consolidated offline coordinator executed from the verified repository
[ ] Each lane independently reviewed
[ ] No production gate promoted without complete evidence
```
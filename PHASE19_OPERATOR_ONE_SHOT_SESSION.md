# PHANTOMX / FLASH LOAN GHOST HUNTER
# PHASE-19 ONE-SHOT EXTERNAL GATE SESSION WORKSHEET

## Objective

Close as many independently satisfiable production evidence lanes as possible in one controlled session while preserving the frozen artifact, fail-closed behavior, and independent acceptance criteria.

## Frozen Artifact

- Verified artifact commit: `fc0df125ee6d0ea694b976ff7d86622b9e45eb15`
- CI certification: Phase-19 workflow run `467` GREEN
- This worksheet does not authorize production execution or live capital.
- Evidence collected for any other artifact commit is not interchangeable with this session.

## Session Rules

1. Use one controlled operator session and one independent witness.
2. Record the artifact commit before any external observation.
3. Do not place private keys, seed phrases, keystore passwords, relay credentials, raw signed transactions, or authentication secrets in the repository, evidence bundle, or chat.
4. Keep signer, Polygon authority, private relay, and staging evidence independently reviewable.
5. Missing evidence remains BLOCKED.
6. Any contradiction remains UNKNOWN/BLOCKED.
7. No public fallback is permitted for private submission.
8. Do not broadcast a live transaction as part of this evidence session.
9. The consolidated coordinator must bind accepted evidence to the session artifact, executor, signer, operator, and witness identities.
10. Evidence paths in the session manifest are relative to the external session workspace. Absolute paths are rejected.

## Stage 0: Artifact Freeze

PowerShell:

```powershell
git checkout fc0df125ee6d0ea694b976ff7d86622b9e45eb15
git rev-parse HEAD
python -m unittest discover -s tests/phase19 -v
```

Expected artifact identity:

```text
fc0df125ee6d0ea694b976ff7d86622b9e45eb15
```

## Lane B: Production Signer Identity

Generate a fresh challenge from the frozen checkout:

```powershell
python scripts/verify_signer_identity.py --generate-challenge
```

The signer must produce exactly one signature externally. Do not enter or store the private key in this workspace.

Verify using:

```powershell
python scripts/verify_signer_identity.py `
  --expected-address <EXPECTED_SIGNER_ADDRESS> `
  --challenge <FRESH_32_BYTE_CHALLENGE_HEX> `
  --signature <65_BYTE_SIGNATURE_HEX>
```

Preserve only the non-secret evidence record returned by the verifier, plus operator/witness provenance and observed timestamp.

## Lane A: Polygon Production Authority

Supply only explicitly approved production HTTPS providers and the intended executor/signer identities through the operator environment. The repository observer is read-only and does not sign or submit.

Required environment inputs:

```text
PHANTOMX_POLYGON_PROVIDERS_JSON
PHANTOMX_POLYGON_QUORUM
PHANTOMX_EXECUTOR_ADDRESS
PHANTOMX_EXPECTED_SIGNER_ADDRESS
```

Run:

```powershell
python scripts/observe_production_authority.py > polygon_authority_evidence.json
```

Then validate offline:

```powershell
python scripts/validate_production_authority_evidence.py polygon_authority_evidence.json
```

Acceptance requires Polygon chain 137, one common block, runtime-code identity, owner identity, quorum agreement, owner == expected signer, canonical evidence hash, and provenance.

## Lane C: Private Relay

Use an endpoint that has actually been approved for this project and whose authentication is externally configured. Do not place credentials in the evidence package.

Capture the non-secret observation record, then validate:

```powershell
python scripts/validate_private_relay_evidence.py private_relay_evidence.json
```

Vendor availability is not project approval. No public fallback is permitted.

## Lane D: Identical-Artifact Shadow / Staging

Use a non-live environment with the exact frozen artifact commit and no live capital.

Record at minimum:

```text
artifact_commit
executor_identity
expected_signer
route/economic proof identities
authority evidence identity
staging environment identity
operator_identity
witness_identity
observed_at_utc
```

The staging evidence must demonstrate that the artifact, authority inputs, signer identity, route/economic inputs, and submission policy were not silently changed.

## Consolidated Validation

Build one session manifest referencing only evidence files that actually exist inside the external session workspace. Then run from the verified repository checkout:

```powershell
python scripts/validate_consolidated_evidence_session.py session_manifest.json
```

The coordinator must never infer GREEN from a missing file. A successful coordinator result means the available evidence is structurally valid and bound to the session identities; it does not itself grant production authorization.

## Lane E: Realized Settlement / PnL

Do not use an estimate or simulation as realized proof.

Required accounting chain:

```text
canonical receipt
→ exact gas cost
→ applicable loan/relay/execution costs
→ exact realized output/input accounting
→ realized net profit strictly > $0.20
```

This lane remains locked until all prerequisite production gates are separately evidenced.

## End-of-Session Review

```text
[ ] Frozen artifact verified: fc0df125ee6d0ea694b976ff7d86622b9e45eb15
[ ] Signer evidence externally produced and independently verified
[ ] Polygon authority quorum evidence captured
[ ] Private relay observation evidence captured
[ ] Identical-artifact shadow/staging evidence captured
[ ] Evidence files are inside the external session workspace
[ ] Consolidated manifest created
[ ] Offline validators passed for every evidence-backed lane
[ ] Session identity bindings passed
[ ] Independent witness reviewed the evidence
[ ] No secret material entered any artifact/log/chat
[ ] No production broadcast occurred
[ ] Live capital remained locked
```

## Hard Stop

Even after successful evidence collection, do not treat this worksheet as permission to execute live capital. Production authorization requires the complete acceptance chain and final independent re-audit.
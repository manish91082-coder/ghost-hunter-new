# PHANTOMX REPOSITORY STRUCTURE AUDIT • 2026-09-21

## Audit objective
Verify canonical project scope, detect drift/clutter, and remove only files that are unambiguously non-runtime temporary artifacts without deleting project evidence or governance material.

## Canonical branch
- Branch: `phase-19-e2e-harness`
- Audit HEAD before cleanup: `976940176aeb10976a3b0d00d9c0c3b87f27201e`
- Frozen external-evidence artifact: `e117b6550686cf5e0ff787d9bd7d85e83996db07`
- Git comparison: current HEAD is 499 commits ahead and 0 commits behind the frozen artifact.
- This confirms ancestry continuity; it does not imply production readiness.

## Structure inventory
Full recursive Contents API inventory of the canonical branch found:
- 284 tracked files
- 4 directories
- `.github/`: repository automation and isolated kick sentinels
- `contracts/`: Phase-19 executor and EVM test mocks
- `phantomx/`: canonical Python execution-integrity/core modules
- `scripts/`: live-read scanners, inventory tools, evidence validators, operator tooling
- `tests/phase19/`: deterministic/adversarial Python certification suite
- `tests/evm/`: Foundry EVM/fork probes
- root governance/evidence documents: mission, dynamic-market policy, strategy catalog, production gates, continuity/status

## Drift checks
- Legacy `v2/`, `v3/`, `common/`, `agents/`, notebook/runtime branches found in the earlier repository history are absent from the canonical branch tree.
- Current `PROJECT_DETAILS.md` explicitly defines the repository cleanliness rule and the canonical architecture; the current tree follows that structure.
- `PHANTOMX_PROJECT_RESUME_MANIFEST.md`, `PROJECT_STATUS.md`, dynamic-market policy, strategy catalog, and project details all preserve the same mission spine: Polygon 137, Aave V3, direct A→B→A MVP, evidence-first economics, strict `net > $0.20`, and blocked live capital until external gates pass.
- Historical/stale checkpoint sections in continuity documents are retained as audit history and do not override the canonical current state in `PROJECT_STATUS.md`.
- No production credential, private key, relay secret, or tracked external-evidence workspace was identified in the canonical tree inventory.

## Surgical deletion candidates
Only the following files were classified as unequivocally non-project temporary clutter:
1. `scripts/README.tmp` — file body is exactly `temporary`; no executable or evidence role.
2. `tests/phase19/test_control_room_validator.tmp` — non-canonical `.tmp` pointer whose content explicitly points to `tests/phase19/test_control_room_validator.py`.

## Explicitly preserved
The following small files were reviewed and preserved because they have a direct governance/audit role, even though they are redundant-looking:
- `scripts/CONTROL_ROOM_CHANGELOG.md`
- `scripts/CONTROL_ROOM_CHANGELOG.txt`
- `scripts/control_room_gate_README.md`
- `scripts/CONTROL_ROOM_NOTE.md`
- `scripts/CONTROL_ROOM_NOTE2.md`
- `tests/phase19/_control_room_test_helper.txt`

## Safety rule
No core runtime module, strategy adapter, workflow, contract, test suite, policy, evidence artifact, or continuity record is deleted by this cleanup pass.

## Post-cleanup gate
After deletion:
1. Re-inventory the canonical branch.
2. Verify the two deleted paths are absent.
3. Verify `PROJECT_STATUS.md` records this cleanup and current blockers.
4. Do not declare CI GREEN until GitHub Actions publishes a successful verification for the resulting lineage.

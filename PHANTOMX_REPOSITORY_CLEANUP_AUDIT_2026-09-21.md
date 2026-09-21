# PHANTOMX REPOSITORY CLEANUP AUDIT • 2026-09-21

## Scope
Canonical repository:
- `manish91082-coder/ghost-hunter-new`
- Canonical branch: `phase-19-e2e-harness`
- This cleanup intentionally does not modify `master`, which is the declared base branch and contains legacy material outside the canonical MVP execution tree.

## Mission anchors audited
- `PHANTOMX_PROJECT_RESUME_MANIFEST.md`
- `PROJECT_STATUS.md`
- `PROJECT_DETAILS.md`
- `PHANTOMX_POLYGON_ARBITRAGE_STRATEGY_CATALOG.md`
- `PHANTOMX_POLYGON_WIDE_HUNT_PLAN.md`
- Phase-19 production/evidence documents
- Canonical Phase-19 workflows and First-Hunt/history kick controls

## Inventory
The canonical branch contained **320 tracked files before the two surgical deletions** and contains **318 tracked files in the verified post-cleanup tree**. The top-level project directories are:
- `.github/`
- `contracts/`
- `phantomx/`
- `scripts/`
- `tests/`

No legacy `v2/`, `v3/`, `agents/`, `common/`, or training/notebook runtime tree is present on this canonical branch. Those legacy paths observed through repository search belong to the separate `master` baseline and were not touched.

## Classification rule
A file is retained when it has any direct role in one of these surfaces:
1. canonical market discovery / quote / strategy search;
2. dynamic economics / EconomicProof / gas / valuation;
3. execution integrity / calldata / nonce / signer / relay / recovery / settlement;
4. Solidity executor or EVM/fork test harness;
5. Phase-19 deterministic tests;
6. Polygon inventory/history/exhaustion evidence;
7. operator orchestration, control-room validation, safety gates;
8. auditable continuity, production evidence intake, or immutable project-state records.

Deletion requires positive evidence of irrelevance, not merely duplication, historical age, unusual naming, or lack of an obvious direct import.

## Findings
### KEEP
- All `phantomx/` modules inspected by inventory are part of the canonical architecture or its declared strategy/evidence surfaces.
- All `contracts/` files are tied to the executor or isolated EVM mocks.
- All `tests/` files are Phase-19 or EVM/fork verification surfaces.
- All `.github/workflows/` files map to Phase-19 certification, First-Hunt, historical Polygon inventory, or explicitly registered discovery-only strategy lanes.
- All root `PHANTOMX_*`, `PHASE19_*`, `PROJECT_*`, policy, evidence and continuity documents have an audit/continuity or mission-control role.

### RELATED BUT REDUNDANT-LOOKING
The following small control-room documents look repetitive:
- `scripts/CONTROL_ROOM_CHANGELOG.md`
- `scripts/CONTROL_ROOM_CHANGELOG.txt`
- `scripts/control_room_gate_README.md`
- `scripts/CONTROL_ROOM_NOTE.md`
- `scripts/CONTROL_ROOM_NOTE2.md`
- `scripts/validate_phase19_control_room.md`
- `tests/phase19/_control_room_test_helper.txt`

They were not deleted because their content is explicitly about the Phase-19 control-room gate and safety/coordination invariants. The present instruction is to remove unrelated files, not to collapse related audit documentation. They may be candidates for a separate consolidation pass later, but they are not proven irrelevant.

## Deletion result
**DELETE = 2 files**

The two deletions were both provably temporary/non-canonical artifacts:
1. `scripts/README.tmp` — commit `7859fd2a6e4e5170f68c9568583b83b6efca088e`; body was exactly `temporary`.
2. `tests/phase19/test_control_room_validator.tmp` — commit `7b352e5c870f6560afe4011c94e8984da9fc5a5`; body was only a pointer to the canonical `test_control_room_validator.py` suite.

The current tree contains neither deleted path. No additional deletion is justified by the current evidence.

## Drift finding
Architecture drift was not found in the canonical branch: the live code tree, strategy catalog, wide-hunt plan, project details and safety rules all continue to point to the same Polygon/Aave V3/QuickSwap V2/Uniswap V3 evidence-first MVP spine.

A **documentation drift** was found: `PHANTOMX_PROJECT_RESUME_MANIFEST.md` lagged behind the latest 2026-09-21 semantic-revert coverage repair. This cleanup cycle therefore includes a continuity-manifest resync.

## Safety
- No private keys or credentials were accessed.
- No signing, submission, broadcast, or live-capital capability was enabled.
- No historical evidence was deleted.
- `master` was left untouched.

## Verdict
The canonical branch remains structurally focused on the PHANTOMX MVP. The correct surgical outcome is **two evidence-backed temporary deletions, zero deletion of project-bearing artifacts, and documentation correction**, not bulk deletion.

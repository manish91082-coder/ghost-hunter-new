# PHANTOMX CONTROL-PLANE TREE REPAIR EVIDENCE • 2026-09-21

## Purpose

This record documents a canonical-tree integrity incident discovered during a controlled S5 workflow timeout repair, the forensic verification, the repair, and the subsequent safe re-trigger.

## Facts

1. Before the incident, the canonical branch `phase-19-e2e-harness` was at:
   `b6be20f3764b58260ce1114be09052f6c04d52ff`.

2. The canonical tree at that commit contained **338 entries**, including `requirements-phase19.txt` and the full Phase-19 / market-hunt execution tree.

3. A workflow-only timeout adjustment was attempted for S5. The resulting commit `68a52cc025b468d8d7f8f41886d4e6eab736fa73` accidentally created a partial Git tree instead of inheriting the full parent tree.

4. On `68a52cc0...`, S5 run #28 / ID `35633133048` failed during dependency installation because `requirements-phase19.txt` was absent. This was an engineering/control-plane failure, not a market result.

5. Direct tree comparison then proved that the bad commit had removed a large portion of the repository relative to `b6be20f...`, including workflows, contracts, core Python modules, tests, and `requirements-phase19.txt`.

6. The repository was repaired by rebuilding from the full canonical tree of `b6be20f...` and re-applying only the intended S5 timeout/kick changes. Repair commit:
   `aadf4979705ee0fe4e90a176608119b5a7a69a3b`.

7. The repaired tree was independently verified as:
   - **338 entries**
   - `requirements-phase19.txt` present
   - relative to `b6be20f...`, only:
     - `.github/workflows/s5-curve-uv3-live-read.yml`
     - `.github/PHANTOMX_S5_KICK`
     were modified.

8. Restoring the dedicated First-Hunt and History kick files in the repair necessarily appeared to GitHub as path additions relative to the bad commit. This caused two read-only workflows to start:
   - First-Hunt #70 / ID `35633669932`
   - Historical crawler #114 and canonical continuation #115

   These runs were not granted execution authority and are not production actions.

9. First-Hunt #70 completed successfully and produced admissible bounded evidence:
   - 36/36 declared tiles complete
   - 1,280 route observations
   - 0 gross-positive
   - 0 post-flash-positive
   - pinned Polygon block `94204969`
   - economic certification: NOT_PERFORMED
   - profit claim: NONE

   This is bounded current-block discovery evidence only. It is not Polygon-wide exhaustion or an EconomicProof profitability certificate.

10. Historical crawler #115 completed successfully for slice `400000-499999` within campaign `polygon-genesis-94135487`, with next cursor `500000`. All six venue evidence lanes reported `ONCHAIN_UNAVAILABLE`; this is historical availability evidence and must not be interpreted as proof of no pools.

11. A safe kick-only follow-up was then made from the repaired full tree using a complete inherited base tree:
   `dc2deb28cbffce2d48c41f5c124d347d84f649ca`.

12. The `dc2deb28...` tree contains **338 entries**, and relative to `aadf4979...` exactly one file changed:
   `.github/PHANTOMX_S5_KICK`.

13. The S5 workflow on the repaired lineage now has a **60-minute** job timeout, up from 40 minutes. No scanner, route, economics, signer, broadcast, or capital-control implementation was changed by this timeout repair.

14. Current exact-head verification:
   - branch: `phase-19-e2e-harness`
   - HEAD: `dc2deb28cbffce2d48c41f5c124d347d84f649ca`
   - Phase-19 run #1023 / ID `35635494123`: **SUCCESS**
   - S5 run #29 / ID `35635495324`: **IN_PROGRESS**

## Safety disposition

- LIVE SIGNING = BLOCKED
- PUBLIC BROADCAST = BLOCKED
- LIVE CAPITAL = LOCKED
- S5 is read-only.
- First-Hunt is read-only.
- Historical inventory is read-only.
- No production authorization was introduced.

## Operating rule added by this incident

For repository mutations that touch Git trees, never construct a new tree from a partial element list unless the full intended base tree is explicitly preserved. Prefer the GitHub contents API for single-file replacements, or use a complete base tree SHA when using low-level Git tree operations.

## Evidence classification

- `68a52cc0...`: invalid control-plane state; no market evidence accepted.
- `aadf4979...`: canonical tree-repair state.
- `dc2deb28...`: canonical full-tree state with clean S5 kick-only change.
- First-Hunt #70: bounded complete discovery evidence, not profit proof.
- Historical #115: bounded historical slice result with venue availability limitations.


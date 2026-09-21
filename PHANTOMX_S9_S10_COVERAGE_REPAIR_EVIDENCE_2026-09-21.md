# PHANTOMX S9/S10 COVERAGE REPAIR EVIDENCE
## 2026-09-21

### Scope
This record captures the repair and fresh read-only verification of the QuickSwap V2/V3 ↔ Ramses V3 discovery lanes. It is bounded live-market evidence only. It is not an EconomicProof, execution authorization, profitability certificate, or Polygon-wide exhaustion proof.

### Root cause
The earlier S9 and S10 artifacts showed 41 unresolved tiles out of 42. For most affected tiles, the outer route-resolution exception path recorded only `UNAVAILABLE_OR_FAILED` and the aggregate result remained `SUCCESS`. The scanners also called `_retryable_failure` without defining/loading that helper in the script, which caused unresolved-tile paths to terminate at startup on the first repair attempt. The repaired lineage loads the shared discovery retry classifier after repository path setup and makes aggregate coverage fail closed.

### S9 verified run
- Workflow: `PHANTOMX S9 QuickSwap V2 Ramses V3 Live Hunt`
- Run: #19 / 35606425568
- HEAD: `4f34922748c170bb506948239c5db0ad369aee90`
- Artifact ID: 10643105338
- Artifact ZIP digest: `sha256:721e76d48a431b08fe4c8a7f82c4c46c00c21250528f6fb2f231c7834b115263`
- Extracted JSON SHA-256: `8388652378682bba64c554aebada73f2ceeb9db8aeda581d8d04ec727f81cfa7`
- Pair universe: COMPLETE_RECENT_WINDOW, 7 active / 7 seed pairs
- Coverage: 42/42 tiles complete; 41 COMPLETE_NO_COMMON_ROUTE; 1 COMPLETE
- Exact observations: 40
- Gross-positive: 0
- Best gross: -$0.164940 USDC
- Best post-flash: -$0.214940 USDC
- Aave liquidity: 628504.358728 USDC
- Dynamic ceiling: 597079.140791 USDC
- Flash premium: 5 bps
- Economic certification: NOT_PERFORMED
- Profit claim: NONE

### S10 verified run
- Workflow: `PHANTOMX S10 QuickSwap V3 Ramses V3 Live Hunt`
- Run: #19 / 35606425570
- HEAD: `4f34922748c170bb506948239c5db0ad369aee90`
- Artifact ID: 10643145202
- Artifact ZIP digest: `sha256:7f1dfb10632387a916efe7a6fa04efe7cdb8f84d31ad5de56fc53e250593970e`
- Extracted JSON SHA-256: `8cb018257c00462929d64726f3510be80e3cf806943b1aff6ee74da139b215b0`
- Pair universe: COMPLETE_RECENT_WINDOW, 7 active / 7 seed pairs
- Coverage: 42/42 tiles complete; 41 COMPLETE_NO_COMMON_ROUTE; 1 COMPLETE
- Exact observations: 40
- Gross-positive: 0
- Best gross: -$0.002202 USDC
- Best post-flash: -$0.052202 USDC
- Aave liquidity: 628504.358728 USDC
- Dynamic ceiling: 597079.140791 USDC
- Flash premium: 5 bps
- Economic certification: NOT_PERFORMED
- Profit claim: NONE

### Verification gates
- Phase-19 run #1012 / 35606425572: GREEN, 918 tests.
- S9 and S10 workflows: GREEN.
- Current branch safety locks remain active.
- No evidence authorizes signer use, transaction submission, public broadcast, live capital, or a realized-profit claim.

### Next deterministic gate
S5 current-head verification remains the active discovery gate. S5 run #22 is on older HEAD `73edc2c...`; after it terminalizes, trigger and verify a fresh S5 run on the then-current canonical HEAD. Only after S5 is bounded-complete should the lane advance to the next frozen discovery expansion.

#!/usr/bin/env python3
"""Read-only live hunt for Strategy S1: QuickSwap V3 <-> Uniswap V3.

QuickSwap V3 uses Algebra's pair-based pool discovery and quote-returned
dynamic fee. Uniswap V3 fee tiers remain explicit search dimensions.
No signing, submission, broadcast, or live-capital operation occurs.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.cross_venue_qsv3_route import (
    build_quickswap_v3_to_uniswap_v3_route,
    build_uniswap_v3_to_quickswap_v3_route,
)
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import DynamicRouteGuardError, evaluate_simulation_domain
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.quickswap_v3 import QuickSwapV3ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

from first_hunt_live_scan import (
    PAIRS,
    ResultOnlyTransport,
    SEED_LOAN_USDC,
    UNISWAP_V3_FACTORY,
    UNISWAP_V3_FEE_TIERS,
    UNISWAP_V3_QUOTER,
    USDC,
    _endpoints,
    dynamic_loan_frontier_usdc,
)

QUICKSWAP_V3_FACTORY = "0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28"
QUICKSWAP_V3_QUOTER = "0xa15F0D7377B2A0C0c10db057f641beD21028FC89"


def _record(token_b: str, venue_path: str, amount: int, sim: Any) -> dict[str, Any]:
    return {
        "token_a": USDC,
        "token_b": token_b,
        "venue_path": venue_path,
        "loan_amount_raw": amount,
        "loan_amount_usdc": str(Decimal(amount) / Decimal(10**6)),
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": sim.final_amount - sim.initial_amount,
        "gross_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount) / Decimal(10**6)),
        "chain_id": sim.chain_id,
        "block_number": sim.block_number,
        "route_hash": sim.route_hash,
        "legs": [
            {
                "dex": leg.dex,
                "pool_or_router": leg.pool_or_router,
                "token_in": leg.token_in,
                "token_out": leg.token_out,
                "amount_in": leg.amount_in,
                "amount_out": leg.amount_out,
                "fee_raw": leg.fee_raw,
                "quote_hash": leg.quote_hash,
            }
            for leg in sim.legs
        ],
    }


def _scan_endpoint(endpoint: str) -> dict[str, Any]:
    http = PolygonRPCHTTPTransport(
        PolygonRPCHTTPConfig(
            provider_name=f"s1-qsv3:{endpoint}",
            endpoint_url=endpoint,
            timeout_seconds=8.0,
        )
    )
    rpc = ResultOnlyTransport(http)
    qsv3 = QuickSwapV3ExactQuoter(rpc, QUICKSWAP_V3_FACTORY, QUICKSWAP_V3_QUOTER)
    u3 = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)
    context = acquire_market_block(rpc)
    aave = AaveV3PolygonDynamicReader(rpc).snapshot(USDC, context)
    ceiling_raw = compute_dynamic_loan_ceiling(
        DynamicLoanInputs(
            aave_available_raw=aave.available_liquidity_raw,
            route_input_ceiling_raw=aave.available_liquidity_raw,
            price_impact_ceiling_raw=aave.available_liquidity_raw,
            system_hard_cap_raw=None,
            safety_headroom_bps=500,
        )
    )
    frontier = dynamic_loan_frontier_usdc(ceiling_raw // 10**6)
    amounts = tuple(x * 10**6 for x in frontier)
    observations: list[dict[str, Any]] = []
    tiles: list[dict[str, Any]] = []

    for fee in UNISWAP_V3_FEE_TIERS:
        for pair in PAIRS:
            try:
                forward = tuple(
                    build_quickswap_v3_to_uniswap_v3_route(
                        rpc, qsv3, u3,
                        amount_in=amount,
                        token_a=USDC,
                        token_b=pair.token_b,
                        uniswap_fee=fee,
                        block=context,
                    )
                    for amount in amounts
                )
                reverse = tuple(
                    build_uniswap_v3_to_quickswap_v3_route(
                        rpc, qsv3, u3,
                        amount_in=amount,
                        token_a=USDC,
                        token_b=pair.token_b,
                        uniswap_fee=fee,
                        block=context,
                    )
                    for amount in amounts
                )
                ceiling = evaluate_simulation_domain(
                    forward=forward,
                    reverse=reverse,
                    max_degradation_bps=100,
                )
                for item in ceiling.evaluated:
                    if item.forward is not None:
                        observations.append(_record(pair.token_b, "quickswap_v3->uniswap_v3", item.amount, item.forward))
                    if item.reverse is not None:
                        observations.append(_record(pair.token_b, "uniswap_v3->quickswap_v3", item.amount, item.reverse))
                tiles.append({
                    "pair": pair.name,
                    "uniswap_fee_tier": fee,
                    "status": "SUCCESS",
                    "dynamic_route_ceiling_usdc": str(Decimal(ceiling.max_safe_amount) / Decimal(10**6)),
                    "reference_amount_usdc": str(Decimal(ceiling.reference_amount) / Decimal(10**6)),
                    "max_route_degradation_bps": ceiling.max_degradation_bps,
                    "observation_count": len(ceiling.evaluated) * 2,
                })
            except (DynamicRouteGuardError, Exception) as exc:
                tiles.append({
                    "pair": pair.name,
                    "uniswap_fee_tier": fee,
                    "status": "UNAVAILABLE_OR_FAILED",
                    "error_type": type(exc).__name__,
                })

    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    return {
        "endpoint": endpoint,
        "chain_id": 137,
        "blocks": sorted({x["block_number"] for x in observations}),
        "observation_count": len(observations),
        "gross_positive_count": sum(x["gross_delta_raw"] > 0 for x in observations),
        "gross_max_usdc": str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6)) if ranked else "0",
        "top_gross_observations": ranked[:10],
        "tiles": tiles,
        "aave_dynamic": {
            "pool": aave.pool,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_usdc": str(Decimal(ceiling_raw) / Decimal(10**6)),
            "loan_frontier_usdc": list(frontier),
        },
        "status": "SUCCESS",
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    endpoints = _endpoints()

    with ThreadPoolExecutor(max_workers=min(2, len(endpoints))) as pool:
        futures = {endpoint: pool.submit(_scan_endpoint, endpoint) for endpoint in endpoints}
        for endpoint in endpoints:
            try:
                result = futures[endpoint].result()
                results.append(result)
                print(
                    f"SUCCESS {endpoint}: observations={result['observation_count']} "
                    f"gross_positive={result['gross_positive_count']} "
                    f"gross_max_usdc={result['gross_max_usdc']}",
                    flush=True,
                )
            except Exception as exc:
                failures.append({"endpoint": endpoint, "error": type(exc).__name__ + ": " + str(exc)})
                print(f"FAILED {endpoint}: {type(exc).__name__}: {exc}", flush=True)

    artifact = {
        "schema_version": 1,
        "strategy": "S1-QS-V3",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "chain_id_expected": 137,
        "quickSwap_v3_factory": QUICKSWAP_V3_FACTORY,
        "quickSwap_v3_quoter": QUICKSWAP_V3_QUOTER,
        "uniswap_v3_fee_tiers": list(UNISWAP_V3_FEE_TIERS),
        "pairs": [p.name for p in PAIRS],
        "seed_loan_frontier_usdc": list(SEED_LOAN_USDC),
        "successful_endpoints": results,
        "failed_endpoints": failures,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
    }
    Path("artifacts/s1_qsv3_live_scan.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())

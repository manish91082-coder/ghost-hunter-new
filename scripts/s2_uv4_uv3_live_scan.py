#!/usr/bin/env python3
"""Read-only S2: Uniswap V4 <-> Uniswap V3 Polygon discovery.

Coverage is intentionally bounded to hookless V4 pools. Hooked pools are not
treated as candidates until their hook behavior is separately understood and
certified.
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
from phantomx.cross_venue_uv4_uv3_route import (
    build_uniswap_v3_to_v4_route,
    build_uniswap_v4_to_v3_route,
)
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import DynamicRouteGuardError, evaluate_simulation_domain
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from phantomx.uniswap_v4 import DEFAULT_FEE_TIERS, DEFAULT_TICK_SPACINGS, V4PoolKey, ZERO_HOOK, UniswapV4ExactQuoter
from first_hunt_live_scan import ResultOnlyTransport, _endpoints, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER, UNISWAP_V3_FEE_TIERS, dynamic_loan_frontier_usdc

POLYGON_CHAIN_ID = 137
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
DAI = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
USDT_E = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
PAIRS = (
    ("USDC.e/WETH", WETH),
    ("USDC.e/WPOL", WPOL),
    ("USDC.e/WBTC", WBTC),
    ("USDC.e/DAI", DAI),
    ("USDC.e/USDT.e", USDT_E),
)


def _key_for(a: str, b: str, fee: int, tick_spacing: int) -> V4PoolKey:
    c0, c1 = (a, b) if a.lower() < b.lower() else (b, a)
    return V4PoolKey(c0, c1, fee, tick_spacing, ZERO_HOOK)


def _record(path: str, amount: int, key: V4PoolKey, sim: Any, premium_bps: int) -> dict[str, Any]:
    premium = (amount * premium_bps + 5000) // 10000
    return {
        "token_a": USDC_E,
        "token_b": key.currency1 if USDC_E.lower() == key.currency0.lower() else key.currency0,
        "venue_path": path,
        "loan_amount_raw": amount,
        "loan_amount_usdc": str(Decimal(amount) / Decimal(10**6)),
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": sim.final_amount - sim.initial_amount,
        "gross_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount) / Decimal(10**6)),
        "flash_loan_premium_bps": premium_bps,
        "post_flash_premium_delta_raw": sim.final_amount - sim.initial_amount - premium,
        "post_flash_premium_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount - premium) / Decimal(10**6)),
        "v4_pool_key": {
            "currency0": key.currency0,
            "currency1": key.currency1,
            "fee": key.fee,
            "tick_spacing": key.tick_spacing,
            "hooks": key.hooks,
        },
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
                "gas_estimate": leg.gas_estimate,
                "quote_hash": leg.quote_hash,
            }
            for leg in sim.legs
        ],
    }


def _scan_endpoint(endpoint: str) -> dict[str, Any]:
    http = PolygonRPCHTTPTransport(PolygonRPCHTTPConfig(
        provider_name=f"s2-uv4-v3:{endpoint}", endpoint_url=endpoint, timeout_seconds=8.0
    ))
    rpc = ResultOnlyTransport(http)
    uv4 = UniswapV4ExactQuoter(rpc)
    uv3 = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)
    context = acquire_market_block(rpc)
    aave = AaveV3PolygonDynamicReader(rpc).snapshot(USDC_E, context)
    ceiling = compute_dynamic_loan_ceiling(DynamicLoanInputs(
        aave_available_raw=aave.available_liquidity_raw,
        route_input_ceiling_raw=aave.available_liquidity_raw,
        price_impact_ceiling_raw=aave.available_liquidity_raw,
        system_hard_cap_raw=None,
        safety_headroom_bps=500,
    ))
    amounts = tuple(x * 10**6 for x in dynamic_loan_frontier_usdc(ceiling // 10**6))
    observations, tiles = [], []

    for fee in DEFAULT_FEE_TIERS:
        for spacing in DEFAULT_TICK_SPACINGS:
            for pair_name, token_b in PAIRS:
                try:
                    key = _key_for(USDC_E, token_b, fee, spacing)
                    forward = tuple(build_uniswap_v4_to_v3_route(
                        rpc, uv4, uv3, amount_in=amount, token_a=USDC_E,
                        token_b=token_b, v4_pool_key=key, v3_fee=ufee, block=context
                    ) for amount in amounts for ufee in UNISWAP_V3_FEE_TIERS[:1])
                    reverse = tuple(build_uniswap_v3_to_v4_route(
                        rpc, uv4, uv3, amount_in=amount, token_a=USDC_E,
                        token_b=token_b, v4_pool_key=key, v3_fee=ufee, block=context
                    ) for amount in amounts for ufee in UNISWAP_V3_FEE_TIERS[:1])
                    guard = evaluate_simulation_domain(forward=forward, reverse=reverse, max_degradation_bps=100)
                    for item in guard.evaluated:
                        if item.forward is not None:
                            observations.append(_record("uniswap_v4->uniswap_v3", item.amount, key, item.forward, aave.flash_loan_premium_bps))
                        if item.reverse is not None:
                            observations.append(_record("uniswap_v3->uniswap_v4", item.amount, key, item.reverse, aave.flash_loan_premium_bps))
                    tiles.append({
                        "pair": pair_name,
                        "v4_fee": fee,
                        "v4_tick_spacing": spacing,
                        "hooks": ZERO_HOOK,
                        "status": "SUCCESS",
                        "observation_count": len(guard.evaluated) * 2,
                    })
                except (DynamicRouteGuardError, Exception) as exc:
                    tiles.append({
                        "pair": pair_name,
                        "v4_fee": fee,
                        "v4_tick_spacing": spacing,
                        "hooks": ZERO_HOOK,
                        "status": "UNAVAILABLE_OR_FAILED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    })

    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    return {
        "endpoint": endpoint,
        "chain_id": POLYGON_CHAIN_ID,
        "observation_count": len(observations),
        "gross_positive_count": sum(x["gross_delta_raw"] > 0 for x in observations),
        "gross_max_usdc": str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6)) if ranked else "0",
        "top_gross_observations": ranked[:20],
        "successful_tiles": sum(t["status"] == "SUCCESS" for t in tiles),
        "tiles": tiles,
        "aave_dynamic": {
            "pool": aave.pool,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_usdc": str(Decimal(ceiling) / Decimal(10**6)),
        },
        "status": "SUCCESS",
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {e: pool.submit(_scan_endpoint, e) for e in _endpoints()}
        for e, fut in futures.items():
            try:
                r = fut.result(); results.append(r)
                print(f"SUCCESS {e}: observations={r['observation_count']} positive={r['gross_positive_count']} max={r['gross_max_usdc']}", flush=True)
            except Exception as exc:
                failures.append({"endpoint": e, "error": type(exc).__name__ + ": " + str(exc)})
                print(f"FAILED {e}: {type(exc).__name__}: {exc}", flush=True)
    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX S2 UNISWAP V4 <-> UNISWAP V3 READ-ONLY LIVE SCAN",
        "strategy": "S2-UV4-V3",
        "coverage": "partial-hookless-grid",
        "scan_revision": 2,
        "read_only": True, "signing": False, "submission": False, "broadcast": False, "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time()-started, 3),
        "chain_id_expected": POLYGON_CHAIN_ID,
        "v4_pool_manager": "0x67366782805870060151383f4bbff9dab53e5cd6",
        "v4_quoter": "0xb3d5c3dfc3a7aebff71895a7191796bffc2c81b9",
        "v4_fee_tiers": list(DEFAULT_FEE_TIERS),
        "v4_tick_spacings": list(DEFAULT_TICK_SPACINGS),
        "v4_hooks_scope": "ZERO_HOOK_ONLY",
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "successful_endpoints": results,
        "failed_endpoints": failures,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
    }
    Path("artifacts/s2_uv4_uv3_live_scan.json").write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if results else 1

if __name__ == "__main__":
    raise SystemExit(main())

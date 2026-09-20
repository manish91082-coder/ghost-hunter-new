#!/usr/bin/env python3
"""Read-only live hunt for Curve <-> Uniswap V3 on Polygon."""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.curve import CurveRegistryExactQuoter
from phantomx.cross_venue_curve_uv3_route import (
    build_curve_to_uniswap_v3_route,
    build_uniswap_v3_to_curve_route,
)
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import DynamicRouteGuardError, evaluate_simulation_domain
from phantomx.market_block import acquire_market_block
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from phantomx.dynamic_pair_surface import discover_live_base_pairs
from first_hunt_live_scan import UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER, UNISWAP_V3_FEE_TIERS, dynamic_loan_frontier_usdc

POLYGON_CHAIN_ID = 137
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
DAI = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
USDT_E = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
MIMATIC = "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1"
CURVE_SEED_POOLS = {("USDC.e/MIMATIC"): "0x53C38755748745e2dd7D0a136FBCC9fB1A5B83b2"}
PAIRS = (
    ("USDC.e/WETH", WETH),
    ("USDC.e/WPOL", WPOL),
    ("USDC.e/WBTC", WBTC),
    ("USDC.e/DAI", DAI),
    ("USDC.e/USDT.e", USDT_E),
    ("USDC.e/MIMATIC", MIMATIC),
)


def _record(path: str, amount: int, pool_ref: Any, sim: Any, premium_bps: int) -> dict[str, Any]:
    premium = (amount * premium_bps + 5000) // 10000
    return {
        "token_a": USDC_E,
        "token_b": pool_ref.token_out,
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
        "curve_registry": pool_ref.registry_name,
        "curve_pool": pool_ref.pool,
        "curve_i": pool_ref.i,
        "curve_j": pool_ref.j,
        "curve_underlying": pool_ref.underlying,
        "curve_fee_raw": pool_ref.fee_raw,
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


def _scan_rpc(rpc: Any, provider_label: str) -> dict[str, Any]:
    curve = CurveRegistryExactQuoter(rpc)
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
    pair_surface_status = "SEED_ONLY"
    active_pairs = PAIRS
    try:
        pair_surface = discover_live_base_pairs(
            rpc, base_token=USDC_E, seed_pairs=tuple(PAIRS),
            required_venues=("curve", "uniswap_v3"), lookback_blocks=25_000, chunk_size=2_000,
        )
        active_pairs = tuple((p.name, p.token_b) for p in pair_surface.pairs)
        pair_surface_status = pair_surface.status
    except Exception as exc:
        pair_surface_status = "PAIR_UNIVERSE_INCOMPLETE"
        print(f"PAIR_DISCOVERY_FALLBACK: {type(exc).__name__}: {exc}", flush=True)

    for pair_name, token_b in active_pairs:
        refs = curve.find_pools_for_pair(USDC_E, token_b, context, max_pools_per_registry=4)
        seed = CURVE_SEED_POOLS.get(pair_name)
        if seed is not None:
            try:
                direct = curve.direct_pool_ref(seed, USDC_E, token_b, context)
                if all(existing.pool.lower() != direct.pool.lower() for existing in refs):
                    refs.append(direct)
            except Exception:
                pass
        for ref in refs:
            for ufee in UNISWAP_V3_FEE_TIERS:
                try:
                    forward = tuple(build_curve_to_uniswap_v3_route(
                        rpc, curve, uv3, amount_in=amount, token_a=USDC_E, token_b=token_b,
                        curve_pool=ref, uniswap_fee=ufee, block=context
                    ) for amount in amounts)
                    reverse = tuple(build_uniswap_v3_to_curve_route(
                        rpc, curve, uv3, amount_in=amount, token_a=USDC_E, token_b=token_b,
                        curve_pool=ref, uniswap_fee=ufee, block=context
                    ) for amount in amounts)
                    guard = evaluate_simulation_domain(forward=forward, reverse=reverse, max_degradation_bps=100)
                    for item in guard.evaluated:
                        if item.forward is not None:
                            observations.append(_record("curve->uniswap_v3", item.amount, ref, item.forward, aave.flash_loan_premium_bps))
                        if item.reverse is not None:
                            observations.append(_record("uniswap_v3->curve", item.amount, ref, item.reverse, aave.flash_loan_premium_bps))
                    tiles.append({
                        "pair": pair_name,
                        "registry": ref.registry_name,
                        "pool": ref.pool,
                        "curve_fee_raw": ref.fee_raw,
                        "curve_i": ref.i,
                        "curve_j": ref.j,
                        "underlying": ref.underlying,
                        "uniswap_fee": ufee,
                        "status": "SUCCESS",
                        "observation_count": len(guard.evaluated) * 2,
                    })
                except (DynamicRouteGuardError, Exception) as exc:
                    tiles.append({
                        "pair": pair_name,
                        "registry": ref.registry_name,
                        "pool": ref.pool,
                        "uniswap_fee": ufee,
                        "status": "UNAVAILABLE_OR_FAILED",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    })

    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    return {
        "endpoint": provider_label,
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
            "loan_frontier_usdc": list(dynamic_loan_frontier_usdc(ceiling // 10**6)),
        },
        "status": "SUCCESS",
        "pair_universe": {"status": pair_surface_status, "active_count": len(active_pairs)},
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    rpc_pool = build_free_polygon_rpc_pool()
    print(f"Starting task-preserving Polygon RPC pool: providers={len(rpc_pool.records)}", flush=True)
    try:
        result = _scan_rpc(rpc_pool, "failover-pool")
        results.append(result)
        print(
            "SUCCESS failover-pool: observations="
            + str(result["observation_count"])
            + " gross_positive="
            + str(result["gross_positive_count"])
            + " gross_max_usdc="
            + str(result["gross_max_usdc"]),
            flush=True,
        )
    except Exception as exc:
        failures.append({"endpoint": "failover-pool", "error": type(exc).__name__ + ": " + str(exc)})
        print(f"FAILED failover-pool: {type(exc).__name__}: {exc}", flush=True)

    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX S5 CURVE <-> UNISWAP V3 READ-ONLY LIVE SCAN",
        "strategy": "S5-CURVE-UV3",
        "coverage": "registry-driven-direct-and-underlying",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time()-started, 3),
        "chain_id_expected": POLYGON_CHAIN_ID,
        "base_token": USDC_E,
        "notable_static_pool_reference": "0x53C38755748745e2dd7D0a136FBCC9fB1A5B83b2",
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "registries": [],
        "pairs": [name for name, _ in PAIRS],
        "successful_endpoints": results,
        "pair_universe": {"status": results[0].get("pair_universe", {}).get("status", "PAIR_UNIVERSE_INCOMPLETE") if results else "PAIR_UNIVERSE_INCOMPLETE", "active_count": results[0].get("pair_universe", {}).get("active_count", 0) if results else 0},
        "rpc_pool": {
            "mode": "task_preserving_failover",
            "provider_count": len(rpc_pool.records),
            "failover_events": [asdict(x) for x in rpc_pool.failure_history()],
            "provider_stats": list(rpc_pool.provider_stats()),
        },
        "failed_endpoints": failures,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
    }
    Path("artifacts/s5_curve_uv3_live_scan.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
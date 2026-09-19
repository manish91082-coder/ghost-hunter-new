#!/usr/bin/env python3
"""Read-only live hunt for Strategy S3: Ramses V3 <-> Uniswap V3."""
from __future__ import annotations

import json
import os
import sys
import time
from decimal import Decimal
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.cross_venue_ramses_v3_route import (
    build_ramses_v3_to_uniswap_v3_route,
    build_uniswap_v3_to_ramses_v3_route,
)
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import DynamicRouteGuardError, evaluate_simulation_domain
from phantomx.market_block import acquire_market_block
from phantomx.ramses_v3 import DEFAULT_TICK_SPACINGS, RamsesV3ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from phantomx.dynamic_pair_surface import discover_live_base_pairs

from first_hunt_live_scan import (
    UNISWAP_V3_FACTORY,
    UNISWAP_V3_FEE_TIERS,
    UNISWAP_V3_QUOTER,
    dynamic_loan_frontier_usdc,
)

USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
DAI = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
USDT_E = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
AAVE = "0xD6DF932A45C0f255f85145f286eA0b292B21C90B"
UNI = "0xb33EaAd8d922B1083446DC23f610c2567fB5180f"

PAIRS = (
    ("USDC.e/WETH", WETH),
    ("USDC.e/WPOL", WPOL),
    ("USDC.e/WBTC", WBTC),
    ("USDC.e/DAI", DAI),
    ("USDC.e/USDT.e", USDT_E),
    ("USDC.e/AAVE", AAVE),
    ("USDC.e/UNI", UNI),
)

POLYGON_CHAIN_ID = 137
RAMSES_V3_FACTORY = "0x2Bef16A0081565E72100D73CBe19B1Bd2d802380"
RAMSES_V3_QUOTER_V2 = "0x3c4532424Eb018013595e4960Fd3de5397B6f571"
RAMSES_V3_SWAP_ROUTER = "0xdcD5F77697914E27f56FD263EF82923C8524AbAc"


def _record(token_b: str, venue_path: str, amount: int, tick_spacing: int, sim: Any, flash_premium_bps: int = 5) -> dict[str, Any]:
    return {
        "token_a": USDC_E,
        "token_b": token_b,
        "venue_path": venue_path,
        "ramses_tick_spacing": tick_spacing,
        "loan_amount_raw": amount,
        "loan_amount_usdc": str(Decimal(amount) / Decimal(10**6)),
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": sim.final_amount - sim.initial_amount,
        "gross_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount) / Decimal(10**6)),
        "flash_loan_premium_bps": flash_premium_bps,
        "flash_loan_premium_raw": (amount * flash_premium_bps + 5000) // 10000,
        "post_flash_premium_delta_raw": (sim.final_amount - sim.initial_amount) - ((amount * flash_premium_bps + 5000) // 10000),
        "post_flash_premium_delta_usdc": str(Decimal((sim.final_amount - sim.initial_amount) - ((amount * flash_premium_bps + 5000) // 10000)) / Decimal(10**6)),
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
    ramses = RamsesV3ExactQuoter(rpc, RAMSES_V3_FACTORY, RAMSES_V3_QUOTER_V2)
    uniswap = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)
    context = acquire_market_block(rpc)
    aave = AaveV3PolygonDynamicReader(rpc).snapshot(USDC_E, context)
    dynamic_ceiling_raw = compute_dynamic_loan_ceiling(
        DynamicLoanInputs(
            aave_available_raw=aave.available_liquidity_raw,
            route_input_ceiling_raw=aave.available_liquidity_raw,
            price_impact_ceiling_raw=aave.available_liquidity_raw,
            system_hard_cap_raw=None,
            safety_headroom_bps=500,
        )
    )
    frontier = dynamic_loan_frontier_usdc(dynamic_ceiling_raw // 10**6)
    amounts = tuple(x * 10**6 for x in frontier)

    observations: list[dict[str, Any]] = []
    tiles: list[dict[str, Any]] = []
    pair_surface_status = "SEED_ONLY"
    try:
        seed_pairs = tuple(PAIRS)
        pair_surface = discover_live_base_pairs(
            rpc, base_token=USDC_E, seed_pairs=seed_pairs,
            required_venues=(("ramses_v3","uniswap_v3")), lookback_blocks=25_000, chunk_size=2_000,
        )
        active_pairs = tuple((p.name, p.token_b) for p in pair_surface.pairs)
        pair_surface_status = pair_surface.status
    except Exception as exc:
        active_pairs = tuple(PAIRS)
        pair_surface_status = "PAIR_UNIVERSE_INCOMPLETE"
        print(f"PAIR_DISCOVERY_FALLBACK: {type(exc).__name__}: {exc}", flush=True)

    for tick_spacing in DEFAULT_TICK_SPACINGS:
        for fee in UNISWAP_V3_FEE_TIERS:
            for pair in active_pairs:
                try:
                    # Fast tile gate: prove both pools exist at the pinned block
                    # before spending the full loan frontier on quote calls.
                    ramses_pool = ramses.resolve_pool(USDC_E, pair[1], tick_spacing, context)
                    ramses_fee = ramses.pool_fee(ramses_pool, context)
                    uniswap_pool = uniswap.resolve_pool(USDC_E, pair[1], fee, context)
                    if not ramses_pool or not uniswap_pool:
                        raise RuntimeError("required route pool is unavailable")
                    forwards = tuple(
                        build_ramses_v3_to_uniswap_v3_route(
                            rpc,
                            ramses,
                            uniswap,
                            amount_in=amount,
                            token_a=USDC_E,
                            token_b=pair[1],
                            ramses_tick_spacing=tick_spacing,
                            uniswap_fee=fee,
                            block=context,
                        )
                        for amount in amounts
                    )
                    reverses = tuple(
                        build_uniswap_v3_to_ramses_v3_route(
                            rpc,
                            ramses,
                            uniswap,
                            amount_in=amount,
                            token_a=USDC_E,
                            token_b=pair[1],
                            ramses_tick_spacing=tick_spacing,
                            uniswap_fee=fee,
                            block=context,
                        )
                        for amount in amounts
                    )
                    ceiling = evaluate_simulation_domain(
                        forward=forwards,
                        reverse=reverses,
                        max_degradation_bps=100,
                    )
                    for item in ceiling.evaluated:
                        if item.forward is not None:
                            observations.append(_record(pair[1], "ramses_v3->uniswap_v3", item.amount, tick_spacing, item.forward, aave.flash_loan_premium_bps))
                        if item.reverse is not None:
                            observations.append(_record(pair[1], "uniswap_v3->ramses_v3", item.amount, tick_spacing, item.reverse, aave.flash_loan_premium_bps))
                    tiles.append(
                        {
                            "pair": pair[0],
                            "ramses_tick_spacing": tick_spacing,
                            "uniswap_fee_tier": fee,
                            "ramses_pool": ramses_pool,
                            "ramses_fee_raw": ramses_fee,
                            "uniswap_pool": uniswap_pool,
                            "status": "SUCCESS",
                            "observation_count": len(ceiling.evaluated) * 2,
                            "dynamic_route_ceiling_usdc": str(Decimal(ceiling.max_safe_amount) / Decimal(10**6)),
                            "reference_amount_usdc": str(Decimal(ceiling.reference_amount) / Decimal(10**6)),
                            "max_route_degradation_bps": ceiling.max_degradation_bps,
                        }
                    )
                except (DynamicRouteGuardError, Exception) as exc:
                    tiles.append(
                        {
                            "pair": pair[0],
                            "ramses_tick_spacing": tick_spacing,
                            "uniswap_fee_tier": fee,
                            "status": "UNAVAILABLE_OR_FAILED",
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        }
                    )

    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    return {
        "endpoint": provider_label,
        "chain_id": POLYGON_CHAIN_ID,
        "blocks": sorted({x["block_number"] for x in observations}),
        "observation_count": len(observations),
        "gross_positive_count": sum(x["gross_delta_raw"] > 0 for x in observations),
        "gross_max_usdc": str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6)) if ranked else "0",
        "top_gross_observations": ranked[:20],
        "tiles": tiles,
        "aave_dynamic": {
            "pool": aave.pool,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_usdc": str(Decimal(dynamic_ceiling_raw) / Decimal(10**6)),
            "loan_frontier_usdc": list(frontier),
        },
        "status": "SUCCESS",
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
            f"SUCCESS failover-pool: observations={result['observation_count']} "
            f"gross_positive={result['gross_positive_count']} gross_max_usdc={result['gross_max_usdc']}",
            flush=True,
        )
    except Exception as exc:
        failures.append({"endpoint": "failover-pool", "error": type(exc).__name__ + ": " + str(exc)})
        print(f"FAILED failover-pool: {type(exc).__name__}: {exc}", flush=True)

    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX S3 RAMSES V3 <-> UNISWAP V3 READ-ONLY LIVE SCAN",
        "strategy": "S3-RAMSES-UV3",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "chain_id_expected": POLYGON_CHAIN_ID,
        "base_token": USDC_E,
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
            "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "UNKNOWN"),
        },
        "ramses_v3_factory": RAMSES_V3_FACTORY,
        "ramses_v3_quoter_v2": RAMSES_V3_QUOTER_V2,
        "ramses_v3_swap_router": RAMSES_V3_SWAP_ROUTER,
        "ramses_tick_spacings": list(DEFAULT_TICK_SPACINGS),
        "uniswap_v3_fee_tiers": list(UNISWAP_V3_FEE_TIERS),
        "pairs": [name for name, _token in PAIRS],
        "successful_endpoints": results,
        "pair_universe": {"status": pair_surface_status, "seed_count": len(PAIRS), "active_count": len(active_pairs)},
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
    Path("artifacts/s3_ramses_uv3_live_scan.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
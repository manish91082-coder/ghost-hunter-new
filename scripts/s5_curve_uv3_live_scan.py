#!/usr/bin/env python3
"""Read-only live hunt for Curve <-> Uniswap V3 on Polygon."""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.curve import CurveRegistryExactQuoter, REGISTRY_TYPES
from phantomx.cross_venue_curve_uv3_route import (
    build_curve_to_uniswap_v3_route,
    build_uniswap_v3_to_curve_route,
)
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import evaluate_simulation_domain
from phantomx.market_block import acquire_market_block_at
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from phantomx.dynamic_pair_surface import discover_live_base_pairs
from phantomx.opportunity_discovery import OpportunityDiscoveryResult, discover_exact_opportunities
try:
    from first_hunt_live_scan import (
        UNISWAP_V3_FACTORY,
        UNISWAP_V3_QUOTER,
        UNISWAP_V3_FEE_TIERS,
        dynamic_loan_frontier_usdc,
    )
except ModuleNotFoundError:
    from scripts.first_hunt_live_scan import (
        UNISWAP_V3_FACTORY,
        UNISWAP_V3_QUOTER,
        UNISWAP_V3_FEE_TIERS,
        dynamic_loan_frontier_usdc,
    )

POLYGON_CHAIN_ID = 137
# S5 evidence is pinned to a deliberately recent block rather than the exact RPC
# head so free public nodes have a bounded propagation window before historical calls.
S5_MARKET_BLOCK_LAG_BLOCKS = 32
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


def _failure_diagnostics(result: OpportunityDiscoveryResult) -> list[dict[str, Any]]:
    return [{
        "loan_amount_raw": item.loan_amount,
        "venue_path": item.venue_path,
        "error_type": item.error_type,
        "error": item.error_message,
        "retryable": item.retryable,
    } for item in result.failures]


def classify_s5_tile_failure(exc: BaseException) -> str:
    message = str(exc).lower()
    terminal_markers = (
        "uniswap v3 pool does not exist for requested fee tier",
        "curve returned zero output",
        "uniswap v3 returned zero output",
        "seeded curve pool does not contain requested token pair",
        "no pair",
        "required route pool is unavailable",
        "ambiguous execution revert consensus across distinct polygon rpc providers",
        "rpc error code=3 message=execution reverted: spl",
    )
    return "COMPLETE_NO_COMMON_ROUTE" if any(marker in message for marker in terminal_markers) else "PARTIAL_INCOMPLETE"


def classify_s5_tile_results(
    forward: OpportunityDiscoveryResult,
    reverse: OpportunityDiscoveryResult,
    *,
    expected_evaluations_per_direction: int,
) -> str:
    expected = expected_evaluations_per_direction * 2
    accounted = (
        len(forward.evaluated) + len(forward.failures)
        + len(reverse.evaluated) + len(reverse.failures)
    )
    if accounted != expected or forward.retryable_failures or reverse.retryable_failures:
        return "PARTIAL_INCOMPLETE"
    failures = forward.failures + reverse.failures
    if not forward.evaluated and not reverse.evaluated:
        return (
            "COMPLETE_NO_COMMON_ROUTE"
            if all(
                classify_s5_tile_failure(RuntimeError(item.error_message)) == "COMPLETE_NO_COMMON_ROUTE"
                for item in failures
            )
            else "PARTIAL_INCOMPLETE"
        )
    forward_amounts = {item.loan_amount for item in forward.evaluated}
    reverse_amounts = {item.loan_amount for item in reverse.evaluated}
    if forward_amounts & reverse_amounts:
        return "COMPLETE"
    return (
        "COMPLETE_NO_COMMON_ROUTE"
        if failures and all(
            classify_s5_tile_failure(RuntimeError(item.error_message)) == "COMPLETE_NO_COMMON_ROUTE"
            for item in failures
        )
        else "PARTIAL_INCOMPLETE"
    )


def summarize_s5_coverage(
    tiles: Sequence[dict[str, Any]],
    *,
    pair_universe_status: str,
) -> dict[str, Any]:
    completed = sum(
        1 for item in tiles
        if item.get("coverage_status") in {"COMPLETE", "COMPLETE_NO_COMMON_ROUTE"}
    )
    incomplete = sum(
        1 for item in tiles
        if item.get("coverage_status") not in {"COMPLETE", "COMPLETE_NO_COMMON_ROUTE"}
    )
    tile_complete = bool(tiles) and incomplete == 0
    pair_complete = pair_universe_status == "COMPLETE_RECENT_WINDOW"
    return {
        "expected_tile_count": len(tiles),
        "observed_tile_count": len(tiles),
        "completed_tile_count": completed,
        "incomplete_tile_count": incomplete,
        "tile_status": "COMPLETE" if tile_complete else "PARTIAL_INCOMPLETE",
        "pair_universe_status": pair_universe_status,
        "status": "COMPLETE" if tile_complete and pair_complete else "PARTIAL_INCOMPLETE",
    }


def _configured_s5_worker_count(provider_count: int) -> int:
    if provider_count < 1:
        raise ValueError("S5 requires at least one RPC provider")
    raw = os.environ.get("PHANTOMX_S5_WORKERS", "8").strip()
    try:
        requested = int(raw)
    except ValueError as exc:
        raise ValueError("PHANTOMX_S5_WORKERS must be an integer") from exc
    if requested < 1:
        raise ValueError("PHANTOMX_S5_WORKERS must be positive")
    return min(requested, provider_count)


def _evaluate_s5_tile(
    *,
    rpc: Any,
    curve: CurveRegistryExactQuoter,
    uv3: UniswapV3ExactQuoter,
    context: Any,
    premium_bps: int,
    pair_name: str,
    token_b: str,
    ref: Any,
    ufee: int,
    amounts: tuple[int, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    forward_result = discover_exact_opportunities(
        token_pairs=((USDC_E, token_b),),
        loan_amounts=amounts,
        evaluate_route=lambda token_a, token_out, amount: build_curve_to_uniswap_v3_route(
            rpc, curve, uv3, amount_in=amount, token_a=token_a, token_b=token_out,
            curve_pool=ref, uniswap_fee=ufee, block=context
        ),
        venue_path="curve->uniswap_v3",
        continue_on_error=True,
    )
    reverse_result = discover_exact_opportunities(
        token_pairs=((USDC_E, token_b),),
        loan_amounts=amounts,
        evaluate_route=lambda token_a, token_out, amount: build_uniswap_v3_to_curve_route(
            rpc, curve, uv3, amount_in=amount, token_a=token_a, token_b=token_out,
            curve_pool=ref, uniswap_fee=ufee, block=context
        ),
        venue_path="uniswap_v3->curve",
        continue_on_error=True,
    )
    combined = OpportunityDiscoveryResult(
        evaluated=forward_result.evaluated + reverse_result.evaluated,
        failures=forward_result.failures + reverse_result.failures,
    )
    coverage_status = classify_s5_tile_results(
        forward_result,
        reverse_result,
        expected_evaluations_per_direction=len(amounts),
    )
    tile = {
        "pair": pair_name,
        "registry": ref.registry_name,
        "pool": ref.pool,
        "curve_fee_raw": ref.fee_raw,
        "curve_i": ref.i,
        "curve_j": ref.j,
        "underlying": ref.underlying,
        "uniswap_fee": ufee,
        "status": "SUCCESS" if coverage_status in {"COMPLETE", "COMPLETE_NO_COMMON_ROUTE"} else "UNAVAILABLE_OR_FAILED",
        "coverage_status": coverage_status,
        "expected_direction_evaluations": len(amounts) * 2,
        "accounted_direction_evaluations": len(combined.evaluated) + len(combined.failures),
        "retryable_failure_count": len(combined.retryable_failures),
        "terminal_failure_count": len(combined.terminal_failures),
        "failure_diagnostics": _failure_diagnostics(combined),
        "observation_count": 0,
    }
    if coverage_status != "COMPLETE":
        return tile, []

    tile_observations: list[dict[str, Any]] = []
    try:
        forward = tuple(item.simulation for item in forward_result.evaluated)
        reverse = tuple(item.simulation for item in reverse_result.evaluated)
        guard = evaluate_simulation_domain(
            forward=forward,
            reverse=reverse,
            max_degradation_bps=100,
        )
        for item in guard.evaluated:
            if item.forward is not None:
                tile_observations.append(
                    _record("curve->uniswap_v3", item.amount, ref, item.forward, premium_bps)
                )
            if item.reverse is not None:
                tile_observations.append(
                    _record("uniswap_v3->curve", item.amount, ref, item.reverse, premium_bps)
                )
        tile["observation_count"] = len(guard.evaluated) * 2
    except Exception as exc:
        tile["status"] = "UNAVAILABLE_OR_FAILED"
        tile["coverage_status"] = "PARTIAL_INCOMPLETE"
        tile["error_type"] = type(exc).__name__
        tile["error"] = str(exc)
        tile_observations = []
    return tile, tile_observations


def _scan_rpc(rpc: Any, provider_label: str) -> dict[str, Any]:
    curve = CurveRegistryExactQuoter(rpc)
    uv3 = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)
    head_block = int(rpc.call("eth_blockNumber", []), 16)
    context = acquire_market_block_at(
        rpc,
        max(0, head_block - S5_MARKET_BLOCK_LAG_BLOCKS),
    )
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
    curve_refs_from_surface: dict[str, tuple[Any, ...]] = {}
    pair_surface_ready = False
    try:
        pair_surface = discover_live_base_pairs(
            rpc, base_token=USDC_E, seed_pairs=tuple(PAIRS),
            required_venues=("curve", "uniswap_v3"), lookback_blocks=25_000, chunk_size=50,
        )
        active_pairs = tuple((p.name, p.token_b) for p in pair_surface.pairs)
        curve_refs_from_surface = {token.lower(): refs for token, refs in pair_surface.curve_pool_refs}
        pair_surface_ready = True
        pair_surface_status = pair_surface.status
    except Exception as exc:
        pair_surface_status = "PAIR_UNIVERSE_INCOMPLETE"
        print(f"PAIR_DISCOVERY_FALLBACK: {type(exc).__name__}: {exc}", flush=True)

    tile_tasks: list[tuple[str, str, Any, int]] = []
    for pair_name, token_b in active_pairs:
        refs = (
            list(curve_refs_from_surface.get(token_b.lower(), ()))
            if pair_surface_ready
            else curve.find_pools_for_pair(USDC_E, token_b, context, max_pools_per_registry=4)
        )
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
                tile_tasks.append((pair_name, token_b, ref, ufee))

    worker_count = _configured_s5_worker_count(len(rpc.records))
    print(
        f"S5 bounded parallel tile execution: tiles={len(tile_tasks)} workers={worker_count} providers={len(rpc.records)}",
        flush=True,
    )
    task_args = (
        {
            "rpc": rpc,
            "curve": curve,
            "uv3": uv3,
            "context": context,
            "premium_bps": aave.flash_loan_premium_bps,
            "pair_name": pair_name,
            "token_b": token_b,
            "ref": ref,
            "ufee": ufee,
            "amounts": amounts,
        }
        for pair_name, token_b, ref, ufee in tile_tasks
    )
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        for tile, tile_observations in executor.map(
            lambda kwargs: _evaluate_s5_tile(**kwargs),
            task_args,
        ):
            tiles.append(tile)
            observations.extend(tile_observations)
    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    coverage = summarize_s5_coverage(tiles, pair_universe_status=pair_surface_status)
    return {
        "endpoint": provider_label,
        "chain_id": POLYGON_CHAIN_ID,
        "observation_count": len(observations),
        "gross_positive_count": sum(x["gross_delta_raw"] > 0 for x in observations),
        "gross_max_usdc": str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6)) if ranked else "0",
        "top_gross_observations": ranked[:20],
        "successful_tiles": sum(t["status"] == "SUCCESS" for t in tiles),
        "coverage": coverage,
        "tiles": tiles,
        "aave_dynamic": {
            "pool": aave.pool,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_usdc": str(Decimal(ceiling) / Decimal(10**6)),
            "loan_frontier_usdc": list(dynamic_loan_frontier_usdc(ceiling // 10**6)),
        },
        "status": "SUCCESS",
        "pair_universe": {"status": pair_surface_status, "active_count": len(active_pairs), "seed_count": len(PAIRS)},
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
        "registries": [{"name": name, "address": address} for name, address in REGISTRY_TYPES],
        "pairs": [name for name, _ in PAIRS],
        "successful_endpoints": results,
        "pair_universe": {"status": results[0].get("pair_universe", {}).get("status", "PAIR_UNIVERSE_INCOMPLETE") if results else "PAIR_UNIVERSE_INCOMPLETE", "active_count": results[0].get("pair_universe", {}).get("active_count", 0) if results else 0},
        "execution": {
            "max_workers": _configured_s5_worker_count(len(rpc_pool.records)),
            "parallelism": "bounded_tile",
            "market_block_lag_blocks": S5_MARKET_BLOCK_LAG_BLOCKS,
        },
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
    complete = bool(results) and all(
        item.get("status") == "COMPLETE"
        and item.get("coverage", {}).get("status") == "COMPLETE"
        and item.get("pair_universe", {}).get("status") == "COMPLETE_RECENT_WINDOW"
        for item in results
    )
    return 0 if complete else 2 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())
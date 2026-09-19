#!/usr/bin/env python3
"""Read-only S6 triangular arbitrage discovery on Polygon."""
from __future__ import annotations

import itertools
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

from scripts.first_hunt_live_scan import (
    ResultOnlyTransport,
    _endpoints,
    dynamic_loan_frontier_usdc,
    UNISWAP_V3_FACTORY,
    UNISWAP_V3_QUOTER,
    UNISWAP_V3_FEE_TIERS,
)
from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.quickswap_v3 import QuickSwapV3ExactQuoter
from phantomx.ramses_v3 import DEFAULT_TICK_SPACINGS, RamsesV3Error, RamsesV3ExactQuoter
from phantomx.triangular_route import simulate_multi_leg
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137
USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
DAI = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
USDT_E = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
MIMATIC = "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
LINK = "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39"

QUICKSWAP_V3_FACTORY = "0x411b0fAcC3489691f28ad58c47006AF5E3Ab3A28"
QUICKSWAP_V3_QUOTER = "0xa15F0D7377B2A0C0c10db057f641beD21028FC89"
RAMSES_V3_FACTORY = "0x2Bef16A0081565E72100D73CBe19B1Bd2d802380"
RAMSES_V3_QUOTER_V2 = "0x3c4532424Eb018013595e4960Fd3de5397B6f571"

BRIDGES = (
    ("WETH", WETH),
    ("WPOL", WPOL),
    ("DAI", DAI),
    ("USDT.e", USDT_E),
    ("MIMATIC", MIMATIC),
    ("WBTC", WBTC),
    ("LINK", LINK),
)
VENUES = ("quickswap_v3", "ramses_v3", "uniswap_v3")
BRIDGE_BY_NAME = dict(BRIDGES)


def _quote(
    adapters,
    venue: str,
    amount: int,
    token_in: str,
    token_out: str,
    context,
    *,
    ramses_tick_spacing: int | None = None,
    uniswap_fee: int = 500,
):
    try:
        if venue == "quickswap_v3":
            return adapters["quickswap"].quote_snapshot(amount, token_in, token_out, context)
        if venue == "ramses_v3":
            if ramses_tick_spacing is None:
                raise ValueError("Ramses tick spacing is required")
            return adapters["ramses"].quote_snapshot(
                amount, token_in, token_out, ramses_tick_spacing, context
            )
        if venue == "uniswap_v3":
            return adapters["uniswap"].quote_snapshot(
                amount, token_in, token_out, uniswap_fee, context
            )
        raise ValueError(f"unsupported venue: {venue}")
    except Exception as exc:
        raise RuntimeError(
            f"quote_failed venue={venue} token_in={token_in} token_out={token_out} "
            f"amount={amount}: {type(exc).__name__}: {exc}"
        ) from exc


def _record(
    venues, tokens, amount, sim, premium_bps, ramses_tick_spacing, uniswap_fee
):
    premium = (amount * premium_bps + 5000) // 10000
    return {
        "venue_path": "->".join(venues),
        "token_path": ["USDC.e", *tokens, "USDC.e"],
        "loan_amount_raw": amount,
        "loan_amount_usdc": str(Decimal(amount) / Decimal(10**6)),
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": sim.final_amount - sim.initial_amount,
        "gross_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount) / Decimal(10**6)),
        "flash_loan_premium_bps": premium_bps,
        "ramses_tick_spacing": ramses_tick_spacing,
        "uniswap_fee": uniswap_fee,
        "post_flash_premium_delta_raw": sim.final_amount - sim.initial_amount - premium,
        "post_flash_premium_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount - premium) / Decimal(10**6)),
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


def _selected_bridge_ordered_pairs() -> tuple[tuple[tuple[str, str], tuple[str, str]], ...]:
    raw = os.getenv("PHANTOMX_S6_BRIDGE_NAMES", "").strip()
    if not raw:
        return tuple(
            ((first_name, first_addr), (second_name, second_addr))
            for (first_name, first_addr), (second_name, second_addr)
            in itertools.permutations(BRIDGES, 2)
        )

    names = tuple(item.strip() for item in raw.split(",") if item.strip())
    if len(names) != 2 or names[0] == names[1]:
        raise ValueError(
            "PHANTOMX_S6_BRIDGE_NAMES must contain exactly two distinct bridge names"
        )
    unknown = [name for name in names if name not in BRIDGE_BY_NAME]
    if unknown:
        raise ValueError(f"unknown S6 bridge asset(s): {unknown}")

    first = (names[0], BRIDGE_BY_NAME[names[0]])
    second = (names[1], BRIDGE_BY_NAME[names[1]])
    return (
        (first, second),
        (second, first),
    )


def _scan_endpoint(
    endpoint: str,
    ordered_bridge_pairs: tuple[tuple[tuple[str, str], tuple[str, str]], ...],
) -> dict[str, Any]:
    rpc = ResultOnlyTransport(
        PolygonRPCHTTPTransport(
            PolygonRPCHTTPConfig(
                provider_name=f"s6-triangular:{endpoint}",
                endpoint_url=endpoint,
                timeout_seconds=8.0,
            )
        )
    )
    adapters = {
        "quickswap": QuickSwapV3ExactQuoter(rpc, QUICKSWAP_V3_FACTORY, QUICKSWAP_V3_QUOTER),
        "ramses": RamsesV3ExactQuoter(rpc, RAMSES_V3_FACTORY, RAMSES_V3_QUOTER_V2),
        "uniswap": UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER),
    }
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

    observations: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for bridge_names in ordered_bridge_pairs:
        first_name, first_addr = bridge_names[0]
        second_name, second_addr = bridge_names[1]
        tokens = (first_addr, second_addr)

        for venues in itertools.permutations(VENUES, 3):
            route_tokens = (USDC_E, first_addr, second_addr, USDC_E)

            # Preflight the non-Ramses pools before attempting exact quotes.
            quickswap_index = venues.index("quickswap_v3")
            quickswap_token_in = route_tokens[quickswap_index]
            quickswap_token_out = route_tokens[quickswap_index + 1]
            try:
                adapters["quickswap"].resolve_pool(
                    quickswap_token_in, quickswap_token_out, context
                )
            except Exception as exc:
                failures.append({
                    "tokens": ["USDC.e", first_name, second_name],
                    "venues": venues,
                    "error_type": type(exc).__name__,
                    "error": "QuickSwap pool preflight failed: " + str(exc),
                })
                continue

            # Exactly one leg is Uniswap V3 in every venue permutation.
            # Only scan fee tiers whose pool exists at the pinned block.
            uniswap_index = venues.index("uniswap_v3")
            uniswap_token_in = route_tokens[uniswap_index]
            uniswap_token_out = route_tokens[uniswap_index + 1]
            available_uniswap_fees: list[int] = []
            for candidate_fee in UNISWAP_V3_FEE_TIERS:
                try:
                    adapters["uniswap"].resolve_pool(
                        uniswap_token_in, uniswap_token_out, candidate_fee, context
                    )
                    available_uniswap_fees.append(candidate_fee)
                except Exception:
                    continue

            if not available_uniswap_fees:
                failures.append({
                    "tokens": ["USDC.e", first_name, second_name],
                    "venues": venues,
                    "error_type": "NO_UNISWAP_POOL",
                    "error": (
                        f"no Uniswap V3 pool for {uniswap_token_in}->{uniswap_token_out} "
                        f"across canonical fee tiers"
                    ),
                })
                continue

            for uniswap_fee in available_uniswap_fees:
                ramses_index = venues.index("ramses_v3")
                ramses_token_in = route_tokens[ramses_index]
                ramses_token_out = route_tokens[ramses_index + 1]

                available_spacings: list[int] = []
                for spacing in DEFAULT_TICK_SPACINGS:
                    try:
                        ramses_pool = adapters["ramses"].resolve_pool(
                            ramses_token_in, ramses_token_out, spacing, context
                        )
                        pool_state = adapters["ramses"].pool_state(ramses_pool, context)
                        if not pool_state.initialized_and_swappable:
                            continue
                        available_spacings.append(spacing)
                    except RamsesV3Error:
                        continue

                if not available_spacings:
                    failures.append({
                        "tokens": ["USDC.e", first_name, second_name],
                        "venues": venues,
                        "uniswap_fee": uniswap_fee,
                        "error_type": "NO_ACTIVE_Ramses_POOL",
                        "error": (
                            f"no initialized + active-liquidity Ramses V3 pool for "
                            f"{ramses_token_in}->{ramses_token_out} across supported tick spacings"
                        ),
                    })
                    continue

                # Route-level eligibility gate: prove the complete 3-leg path
                # can quote sequentially before spending the full frontier.
                eligible_spacings: list[int] = []
                for ramses_tick_spacing in available_spacings:
                    try:
                        probe_amount = min(amounts)
                        probe_legs = []
                        probe_current_amount = probe_amount
                        probe_current_token = USDC_E
                        for venue, nxt in zip(venues, (*tokens, USDC_E)):
                            probe_leg = _quote(
                                adapters,
                                venue,
                                probe_current_amount,
                                probe_current_token,
                                nxt,
                                context,
                                ramses_tick_spacing=ramses_tick_spacing,
                                uniswap_fee=uniswap_fee,
                            )
                            probe_legs.append(probe_leg)
                            probe_current_amount = probe_leg.amount_out
                            probe_current_token = nxt
                        simulate_multi_leg(probe_legs)
                        eligible_spacings.append(ramses_tick_spacing)
                    except Exception as exc:
                        failures.append({
                            "tokens": ["USDC.e", first_name, second_name],
                            "venues": venues,
                            "ramses_tick_spacing": ramses_tick_spacing,
                            "uniswap_fee": uniswap_fee,
                            "amount": min(amounts),
                            "error_type": type(exc).__name__,
                            "error": "route_probe_failed: " + str(exc),
                        })

                if not eligible_spacings:
                    continue

                for ramses_tick_spacing in eligible_spacings:
                    for amount in amounts:
                        try:
                            legs = []
                            leg_amount = amount
                            current = USDC_E
                            for venue, nxt in zip(venues, (*tokens, USDC_E)):
                                leg = _quote(
                                    adapters,
                                    venue,
                                    leg_amount,
                                    current,
                                    nxt,
                                    context,
                                    ramses_tick_spacing=ramses_tick_spacing,
                                    uniswap_fee=uniswap_fee,
                                )
                                legs.append(leg)
                                leg_amount = leg.amount_out
                                current = nxt
                            sim = simulate_multi_leg(legs)
                            observations.append(
                                _record(
                                    venues,
                                    (first_name, second_name),
                                    amount,
                                    sim,
                                    aave.flash_loan_premium_bps,
                                    ramses_tick_spacing,
                                    uniswap_fee,
                                )
                            )
                        except Exception as exc:
                            failures.append({
                                "tokens": ["USDC.e", first_name, second_name],
                                "venues": venues,
                                "ramses_tick_spacing": ramses_tick_spacing,
                                "uniswap_fee": uniswap_fee,
                                "amount": amount,
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                            })

    ranked = sorted(observations, key=lambda x: x["gross_delta_raw"], reverse=True)
    return {
        "endpoint": endpoint,
        "chain_id": POLYGON_CHAIN_ID,
        "block_number": context.block_number,
        "observation_count": len(observations),
        "gross_positive_count": sum(x["gross_delta_raw"] > 0 for x in observations),
        "route_probe_failure_count": sum(
            1 for x in failures if str(x.get("error", "")).startswith("route_probe_failed:")
        ),
        "gross_max_usdc": str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6)) if ranked else "0",
        "top_gross_observations": ranked[:30],
        "failed_route_count": len(failures),
        "sample_failures": failures[:20],
        "aave_dynamic": {
            "pool": aave.pool,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_usdc": str(Decimal(ceiling) / Decimal(10**6)),
            "loan_frontier_usdc": list(x / 1 for x in dynamic_loan_frontier_usdc(ceiling // 10**6)),
        },
        "status": "SUCCESS",
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results, failures = [], []
    endpoints = _endpoints()
    ordered_bridge_pairs = _selected_bridge_ordered_pairs()
    selected_names = sorted({name for pair in ordered_bridge_pairs for name, _ in pair})
    scope = "full-42-directed-pairs" if not os.getenv("PHANTOMX_S6_BRIDGE_NAMES", "").strip() else "selected-pair-bidirectional"
    print(
        f"S6 scope={scope} bridges={','.join(selected_names)} directed_pairs={len(ordered_bridge_pairs)}",
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=min(2, len(endpoints))) as pool:
        futures = {
            e: pool.submit(_scan_endpoint, e, ordered_bridge_pairs)
            for e in endpoints
        }
        for e, future in futures.items():
            try:
                r = future.result()
                results.append(r)
                print(f"SUCCESS {e}: observations={r['observation_count']} positive={r['gross_positive_count']} max={r['gross_max_usdc']}", flush=True)
            except Exception as exc:
                failures.append({"endpoint": e, "error": type(exc).__name__ + ": " + str(exc)})
                print(f"FAILED {e}: {type(exc).__name__}: {exc}", flush=True)
    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX S6 TRIANGULAR READ-ONLY LIVE SCAN",
        "strategy": "S6-TRIANGULAR",
        "coverage": "bounded-3-venue-v3-grid",
        "coverage_scope": scope,
        "selected_bridge_assets": selected_names,
        "selected_directed_pair_count": len(ordered_bridge_pairs),
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "chain_id_expected": POLYGON_CHAIN_ID,
        "base_token": USDC_E,
        "bridge_assets": [name for name, _ in BRIDGES],
        "venue_families": list(VENUES),
        "ramses_tick_spacings_supported": list(DEFAULT_TICK_SPACINGS),
        "uniswap_v3_fee_tiers": list(UNISWAP_V3_FEE_TIERS),
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
    Path("artifacts/s6_triangular_live_scan.json").write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if results else 1


if __name__ == "__main__":
    raise SystemExit(main())

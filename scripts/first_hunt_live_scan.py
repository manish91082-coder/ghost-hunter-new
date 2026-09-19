#!/usr/bin/env python3
"""Read-only First-Hunt live Polygon quote scanner.

This tool exercises only the certified read/quote/discovery path. It never
signs, submits, broadcasts, reserves capital, or declares net profitability.
It records exact block-pinned A->B->A quote observations for an explicit loan
frontier and leaves full economic certification to the deterministic
cost/evidence pipeline.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.cross_venue_discovery import discover_cross_venue_opportunities
from phantomx.dynamic_route_guard import DynamicRouteGuardError, evaluate_simulation_domain
from phantomx.dynamic_market_policy import compute_dynamic_loan_ceiling
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137
USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
DAI = "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063"
LINK = "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39"
AAVE = "0xD6DF932A45C0f255f85145f286eA0b292B21C90B"
UNI = "0xb33EaAd8d922B1083446DC23f610c2567fB5180f"
USDT_E = "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"
MIMATIC = "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1"

QUICKSWAP_V2_ROUTER = "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"
UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
UNISWAP_V3_QUOTER = "0xb27308f9F90D607463bb33eA1BeBb41C27CE5AB6"
UNISWAP_V3_FEE_TIERS = (100, 500, 3000, 10000)

DEFAULT_ENDPOINTS = (
    "https://polygon.drpc.org/",
    "https://public.1rpc.io/matic",
    "https://polygon-bor-rpc.publicnode.com",
)

# Explicit frontier. Exact over this domain, not a continuous optimum claim.
SEED_LOAN_USDC = (100, 250, 500, 750, 1000, 1500, 2500, 5000, 7500, 10000, 15000, 25000, 50000, 75000, 100000, 150000, 250000)

def dynamic_loan_frontier_usdc(dynamic_ceiling_usdc: int) -> tuple[int, ...]:
    """Build an explicit, live-bounded loan domain; never exceeds the live cap."""
    if not isinstance(dynamic_ceiling_usdc, int) or isinstance(dynamic_ceiling_usdc, bool):
        raise ValueError("dynamic_ceiling_usdc must be an integer")
    accepted = [amount for amount in SEED_LOAN_USDC if amount <= dynamic_ceiling_usdc]
    if dynamic_ceiling_usdc >= SEED_LOAN_USDC[-1]:
        current = SEED_LOAN_USDC[-1]
        while current < dynamic_ceiling_usdc:
            current = min(dynamic_ceiling_usdc, max(current + 1, (current * 3) // 2))
            if current not in accepted:
                accepted.append(current)
    if not accepted:
        raise ValueError("live Aave liquidity is below minimum discovery size")
    return tuple(sorted(set(accepted)))


class ResultOnlyTransport:
    """Adapt the strict HTTP envelope to quote adapters expecting RPC results."""

    def __init__(self, transport: PolygonRPCHTTPTransport) -> None:
        self._transport = transport

    def call(self, method: str, params: Sequence[Any]) -> Any:
        response = self._transport.call(method, params)
        error = response.get("error")
        if error is not None:
            if isinstance(error, Mapping):
                code = error.get("code", "UNKNOWN")
                message = error.get("message", "RPC error")
                raise RuntimeError(f"{method}: RPC error code={code} message={message}")
            raise RuntimeError(f"{method}: RPC error {error}")
        if "result" not in response:
            raise RuntimeError(f"{method}: missing result")
        return response["result"]


@dataclass(frozen=True)
class PairSpec:
    name: str
    token_b: str


PAIRS = (
    PairSpec("USDC/WETH", WETH),
    PairSpec("USDC/WPOL", WPOL),
    PairSpec("USDC/WBTC", WBTC),
    # Exploratory read-only coverage. Each tile must prove an on-chain route
    # exists at the pinned block before observations are retained.
    PairSpec("USDC/DAI", DAI),
    PairSpec("USDC/LINK", LINK),
    PairSpec("USDC/AAVE", AAVE),
    PairSpec("USDC/UNI", UNI),
    PairSpec("USDC/USDT.e", USDT_E),
    PairSpec("USDC/MIMATIC", MIMATIC),
)


def _endpoints() -> tuple[str, ...]:
    raw = os.getenv("PHANTOMX_LIVE_RPC_ENDPOINTS", "")
    if not raw.strip():
        return DEFAULT_ENDPOINTS
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or DEFAULT_ENDPOINTS


def _quote_record(
    *,
    token_a: str,
    token_b: str,
    venue_path: str,
    loan_amount: int,
    sim: Any,
    flash_premium_bps: int,
    route_degradation_bps: int | None,
) -> dict[str, Any]:
    return {
        "token_a": token_a,
        "token_b": token_b,
        "venue_path": venue_path,
        "loan_amount_usdc": str(Decimal(loan_amount) / Decimal(10**6)),
        "loan_amount_raw": loan_amount,
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": sim.final_amount - sim.initial_amount,
        "gross_delta_usdc": str(Decimal(sim.final_amount - sim.initial_amount) / Decimal(10**6)),
        "flash_loan_premium_bps": flash_premium_bps,
        "flash_loan_premium_raw": (loan_amount * flash_premium_bps + 5000) // 10000,
        "post_flash_premium_delta_raw": (sim.final_amount - sim.initial_amount) - ((loan_amount * flash_premium_bps + 5000) // 10000),
        "post_flash_premium_delta_usdc": str(Decimal((sim.final_amount - sim.initial_amount) - ((loan_amount * flash_premium_bps + 5000) // 10000)) / Decimal(10**6)),
        "route_degradation_bps": route_degradation_bps,
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
    quickswap = QuickSwapV2ExactQuoter(rpc, QUICKSWAP_V2_ROUTER)
    uniswap = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)

    context = acquire_market_block(rpc)
    aave = AaveV3PolygonDynamicReader(rpc).snapshot(USDC, context)
    dynamic_ceiling_raw = compute_dynamic_loan_ceiling(
        __import__("phantomx.dynamic_market_policy", fromlist=["DynamicLoanInputs"]).DynamicLoanInputs(
            aave_available_raw=aave.available_liquidity_raw,
            route_input_ceiling_raw=aave.available_liquidity_raw,
            price_impact_ceiling_raw=aave.available_liquidity_raw,
            system_hard_cap_raw=None,
            safety_headroom_bps=500,
        )
    )
    dynamic_ceiling_usdc = dynamic_ceiling_raw // 10**6
    loan_frontier_usdc = dynamic_loan_frontier_usdc(dynamic_ceiling_usdc)
    loan_amounts_raw = tuple(amount * 10**6 for amount in loan_frontier_usdc)

    observations: list[dict[str, Any]] = []
    tile_results: list[dict[str, Any]] = []
    for fee_tier in UNISWAP_V3_FEE_TIERS:
        for pair in PAIRS:
            try:
                discovered = discover_cross_venue_opportunities(
                    rpc,
                    quickswap,
                    uniswap,
                    token_pairs=((USDC, pair.token_b),),
                    loan_amounts=loan_amounts_raw,
                    uniswap_fee=fee_tier,
                    block=context,
                )
                forward_observations = tuple(
                    item.simulation for item in discovered.evaluated
                    if item.venue_path == "quickswap_v2->uniswap_v3"
                )
                reverse_observations = tuple(
                    item.simulation for item in discovered.evaluated
                    if item.venue_path == "uniswap_v3->quickswap_v2"
                )
                ceiling = evaluate_simulation_domain(
                    forward=forward_observations,
                    reverse=reverse_observations,
                    max_degradation_bps=100,
                )
                eligible = {item.amount: item for item in ceiling.evaluated if item.safe}
                for item in ceiling.evaluated:
                    if item.forward is None or item.reverse is None:
                        continue
                    forward = item.forward
                    reverse = item.reverse
                    fd = item.forward_degradation_bps
                    rd = item.reverse_degradation_bps
                    observations.append(_quote_record(
                        token_a=USDC,
                        token_b=pair.token_b,
                        venue_path="quickswap_v2->uniswap_v3",
                        loan_amount=item.amount,
                        sim=forward,
                        flash_premium_bps=aave.flash_loan_premium_bps,
                        route_degradation_bps=fd,
                    ))
                    observations.append(_quote_record(
                        token_a=USDC,
                        token_b=pair.token_b,
                        venue_path="uniswap_v3->quickswap_v2",
                        loan_amount=item.amount,
                        sim=reverse,
                        flash_premium_bps=aave.flash_loan_premium_bps,
                        route_degradation_bps=rd,
                    ))
                tile_results.append({
                    "pair": pair.name,
                    "uniswap_fee_tier": fee_tier,
                    "status": "SUCCESS",
                    "observation_count": len(ceiling.evaluated) * 2,
                    "dynamic_route_ceiling_usdc": str(Decimal(ceiling.max_safe_amount) / Decimal(10**6)),
                    "reference_amount_usdc": str(Decimal(ceiling.reference_amount) / Decimal(10**6)),
                    "max_route_degradation_bps": ceiling.max_degradation_bps,
                })
            except (DynamicRouteGuardError, Exception) as exc:
                tile_results.append({
                    "pair": pair.name,
                    "uniswap_fee_tier": fee_tier,
                    "status": "UNAVAILABLE_OR_FAILED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })

    if not observations:
        raise RuntimeError("no complete pair/fee tier produced an exact route grid")

    blocks = sorted({item["block_number"] for item in observations})
    chains = sorted({item["chain_id"] for item in observations})
    gross_positive = [item for item in observations if item["gross_delta_raw"] > 0]
    ranked = sorted(observations, key=lambda item: item["gross_delta_raw"], reverse=True)
    top_gross = ranked[:10]
    by_tile: dict[str, dict[str, Any]] = {}
    for item in observations:
        tile = f"{item['token_b'][:10]}:{item.get('venue_path', 'unknown')}"
        current = by_tile.get(tile)
        if current is None or item["gross_delta_raw"] > current["gross_delta_raw"]:
            by_tile[tile] = item

    return {
        "endpoint": provider_label,
        "chain_ids": chains,
        "blocks": blocks,
        "observation_count": len(observations),
        "gross_positive_count": len(gross_positive),
        "gross_max_usdc": str(Decimal(top_gross[0]["gross_delta_raw"]) / Decimal(10**6)) if top_gross else "0",
        "top_gross_observations": top_gross,
        "tile_maxima": sorted(
            by_tile.values(),
            key=lambda item: item["gross_delta_raw"],
            reverse=True,
        )[:20],
        "gross_positive_observations": gross_positive,
        "observations": observations,
        "fee_tier_tile_results": tile_results,
        "aave_dynamic": {
            "pool": aave.pool,
            "a_token": aave.a_token,
            "available_liquidity_raw": aave.available_liquidity_raw,
            "available_liquidity_usdc": str(Decimal(aave.available_liquidity_raw) / Decimal(10**6)),
            "flash_loan_premium_bps": aave.flash_loan_premium_bps,
            "dynamic_ceiling_raw": dynamic_ceiling_raw,
            "dynamic_ceiling_usdc": str(Decimal(dynamic_ceiling_raw) / Decimal(10**6)),
            "loan_frontier_usdc": list(loan_frontier_usdc),
            "safety_headroom_bps": 500,
        },
        "status": "SUCCESS",
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    rpc_pool = build_free_polygon_rpc_pool()
    print(
        f"Starting task-preserving Polygon RPC pool: providers={len(rpc_pool.records)}",
        flush=True,
    )
    try:
        result = _scan_rpc(rpc_pool, "failover-pool")
        results.append(result)
        print(
            f"SUCCESS failover-pool: observations={result['observation_count']} "
            f"gross_positive={result['gross_positive_count']} "
            f"gross_max_usdc={result['gross_max_usdc']} "
            f"dynamic_ceiling_usdc={result['aave_dynamic']['dynamic_ceiling_usdc']} "
            f"blocks={result['blocks']}",
            flush=True,
        )
    except Exception as exc:
        failures.append({"endpoint": "failover-pool", "error": type(exc).__name__ + ": " + str(exc)})
        print(f"FAILED failover-pool: {type(exc).__name__}: {exc}", flush=True)

    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX FIRST HUNT READ-ONLY LIVE SCAN",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "generated_at_unix": int(time.time()),
        "duration_seconds": round(time.time() - started, 3),
        "chain_id_expected": POLYGON_CHAIN_ID,
        "pairs": [asdict(pair) for pair in PAIRS],
        "seed_loan_frontier_usdc": list(SEED_LOAN_USDC),
        "uniswap_v3_fee_tiers": list(UNISWAP_V3_FEE_TIERS),
        "successful_endpoints": results,
        "failed_endpoints": failures,
        "rpc_pool": {
            "mode": "task_preserving_failover",
            "provider_count": len(rpc_pool.records),
            "providers": [asdict(record) for record in rpc_pool.records],
            "attempt_count": len(rpc_pool.history),
            "attempt_history": [asdict(attempt) for attempt in rpc_pool.history],
            "provider_stats": list(rpc_pool.provider_stats()),
        },
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
        "notes": [
            "Gross-positive observations are quote evidence only.",
            "Provider failure rotates the same logical read to another healthy provider.",
            "Pinned market-block tags are preserved across failover when the replacement provider supports the block.",
            "No USD valuation, exact final executor-path gas, MEV/relay cost, or final requote is inferred here.",
            "No candidate is certified profitable solely from this scan.",
            "The explicit loan frontier is complete only over the listed amounts.",
            "rpc_exhausted means infrastructure exhaustion, never market no-opportunity.",
        ],
    }

    out = Path("artifacts/first_hunt_live_scan.json")
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}", flush=True)

    if not results:
        print("No read-only Polygon provider in the failover pool produced a complete scan.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
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
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantomx.cross_venue_discovery import discover_cross_venue_opportunities
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.quickswap_v2 import QuickSwapV2ExactQuoter
from phantomx.uniswap_v3 import UniswapV3ExactQuoter

POLYGON_CHAIN_ID = 137
USDC = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
WETH = "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"
WPOL = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"
WBTC = "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"

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
LOAN_USDC = (100, 250, 500, 750, 1000, 1500, 2500, 5000, 7500, 10000, 15000, 25000, 50000, 75000, 100000, 150000, 250000)


class ResultOnlyTransport:
    """Adapt the strict HTTP envelope to quote adapters expecting RPC results."""

    def __init__(self, transport: PolygonRPCHTTPTransport) -> None:
        self._transport = transport

    def call(self, method: str, params: Sequence[Any]) -> Any:
        response = self._transport.call(method, params)
        if response.get("error") is not None:
            raise RuntimeError(f"{method}: RPC error")
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
)


def _endpoints() -> tuple[str, ...]:
    raw = os.getenv("PHANTOMX_LIVE_RPC_ENDPOINTS", "")
    if not raw.strip():
        return DEFAULT_ENDPOINTS
    values = tuple(item.strip() for item in raw.split(",") if item.strip())
    return values or DEFAULT_ENDPOINTS


def _quote_record(candidate: Any) -> dict[str, Any]:
    sim = candidate.simulation
    return {
        "token_a": candidate.token_a,
        "token_b": candidate.token_b,
        "venue_path": candidate.venue_path,
        "loan_amount_usdc": str(Decimal(candidate.loan_amount) / Decimal(10**6)),
        "loan_amount_raw": candidate.loan_amount,
        "final_amount_raw": sim.final_amount,
        "final_amount_usdc": str(Decimal(sim.final_amount) / Decimal(10**6)),
        "gross_delta_raw": candidate.gross_delta,
        "gross_delta_usdc": str(Decimal(candidate.gross_delta) / Decimal(10**6)),
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
    http = PolygonRPCHTTPTransport(
        PolygonRPCHTTPConfig(
            provider_name=f"first-hunt:{endpoint}",
            endpoint_url=endpoint,
            timeout_seconds=8.0,
        )
    )
    rpc = ResultOnlyTransport(http)
    quickswap = QuickSwapV2ExactQuoter(rpc, QUICKSWAP_V2_ROUTER)
    uniswap = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)

    context = acquire_market_block(rpc)

    observations: list[dict[str, Any]] = []
    tile_results: list[dict[str, Any]] = []
    for fee_tier in UNISWAP_V3_FEE_TIERS:
        for pair in PAIRS:
            try:
                candidates = discover_cross_venue_opportunities(
                    rpc,
                    quickswap,
                    uniswap,
                    token_pairs=((USDC, pair.token_b),),
                    loan_amounts=tuple(amount * 10**6 for amount in LOAN_USDC),
                    uniswap_fee=fee_tier,
                    block=context,
                )
                tile_observations = [_quote_record(item) for item in candidates.evaluated]
                observations.extend(tile_observations)
                tile_results.append({
                    "pair": pair.name,
                    "uniswap_fee_tier": fee_tier,
                    "status": "SUCCESS",
                    "observation_count": len(tile_observations),
                })
            except Exception as exc:
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

    return {
        "endpoint": endpoint,
        "chain_ids": chains,
        "blocks": blocks,
        "observation_count": len(observations),
        "gross_positive_count": len(gross_positive),
        "gross_positive_observations": gross_positive,
        "observations": observations,
        "fee_tier_tile_results": tile_results,
        "status": "SUCCESS",
    }


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for endpoint in _endpoints():
        try:
            print(f"Scanning read-only Polygon endpoint: {endpoint}", flush=True)
            result = _scan_endpoint(endpoint)
            results.append(result)
            print(
                f"SUCCESS {endpoint}: observations={result['observation_count']} "
                f"gross_positive={result['gross_positive_count']} blocks={result['blocks']}",
                flush=True,
            )
            # One clean provider is enough to establish live-read availability.
            # Additional providers remain useful for independent corroboration.
        except Exception as exc:
            failures.append({"endpoint": endpoint, "error": type(exc).__name__ + ": " + str(exc)})
            print(f"FAILED {endpoint}: {type(exc).__name__}: {exc}", flush=True)

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
        "loan_frontier_usdc": list(LOAN_USDC),
        "uniswap_v3_fee_tiers": list(UNISWAP_V3_FEE_TIERS),
        "successful_endpoints": results,
        "failed_endpoints": failures,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
        "notes": [
            "Gross-positive observations are quote evidence only.",
            "No USD valuation, exact final executor-path gas, MEV/relay cost, or final requote is inferred here.",
            "No candidate is certified profitable solely from this scan.",
            "The explicit loan frontier is complete only over the listed amounts.",
        ],
    }

    out = Path("artifacts/first_hunt_live_scan.json")
    out.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out}", flush=True)

    if not results:
        print("No read-only Polygon endpoint produced a complete scan.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

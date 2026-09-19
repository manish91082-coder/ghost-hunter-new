#!/usr/bin/env python3
"""Forensic read-only probe for Curve MAI/USDC.e versus Uniswap V3."""
from __future__ import annotations
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from phantomx.curve import CurveRegistryExactQuoter
from phantomx.cross_venue_curve_uv3_route import build_curve_to_uniswap_v3_route, build_uniswap_v3_to_curve_route
from phantomx.market_block import acquire_market_block
from phantomx.polygon_rpc_http import PolygonRPCHTTPConfig, PolygonRPCHTTPTransport
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from first_hunt_live_scan import ResultOnlyTransport, _endpoints, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER

USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
MIMATIC = "0xa3Fa99A148fA48D14Ed51d610c367C61876997F1"
CURVE_POOL = "0x53C38755748745e2dd7D0a136FBCC9fB1A5B83b2"
PROBE_REVISION = 2
UNISWAP_FEES = (100, 500, 3000, 10000)
AMOUNTS = (100 * 10**6, 1000 * 10**6, 10_000 * 10**6)


def _endpoint(endpoint: str) -> dict:
    rpc = ResultOnlyTransport(PolygonRPCHTTPTransport(PolygonRPCHTTPConfig(
        provider_name=f"curve-mai-probe:{endpoint}", endpoint_url=endpoint, timeout_seconds=10.0
    )))
    context = acquire_market_block(rpc)
    curve = CurveRegistryExactQuoter(rpc)
    uv3 = UniswapV3ExactQuoter(rpc, UNISWAP_V3_FACTORY, UNISWAP_V3_QUOTER)
    out = {"endpoint": endpoint, "block_number": context.block_number, "seed": CURVE_POOL, "seed_verification": {}, "quotes": [], "errors": []}

    try:
        ref = curve.direct_pool_ref(CURVE_POOL, USDC_E, MIMATIC, context)
        out["seed_verification"] = {"status": "SUCCESS", "i": ref.i, "j": ref.j, "fee_raw": ref.fee_raw, "token_in": ref.token_in, "token_out": ref.token_out}
    except Exception as exc:
        out["seed_verification"] = {"status": "FAILED", "error_type": type(exc).__name__, "error": str(exc)}
        return out

    for fee in UNISWAP_FEES:
        for amount in AMOUNTS:
            try:
                forward = build_curve_to_uniswap_v3_route(
                    rpc, curve, uv3, amount_in=amount, token_a=USDC_E, token_b=MIMATIC,
                    curve_pool=ref, uniswap_fee=fee, block=context
                )
                reverse = build_uniswap_v3_to_curve_route(
                    rpc, curve, uv3, amount_in=amount, token_a=USDC_E, token_b=MIMATIC,
                    curve_pool=ref, uniswap_fee=fee, block=context
                )
                out["quotes"].append({
                    "uniswap_fee": fee,
                    "amount_usdc": str(Decimal(amount)/Decimal(10**6)),
                    "forward_final_usdc": str(Decimal(forward.final_amount)/Decimal(10**6)),
                    "reverse_final_usdc": str(Decimal(reverse.final_amount)/Decimal(10**6)),
                    "forward_gross_usdc": str(Decimal(forward.final_amount-forward.initial_amount)/Decimal(10**6)),
                    "reverse_gross_usdc": str(Decimal(reverse.final_amount-reverse.initial_amount)/Decimal(10**6)),
                    "forward_route_hash": forward.route_hash,
                    "reverse_route_hash": reverse.route_hash,
                })
            except Exception as exc:
                out["errors"].append({"uniswap_fee": fee, "amount_usdc": str(Decimal(amount)/Decimal(10**6)), "error_type": type(exc).__name__, "error": str(exc)})
    out["status"] = "SUCCESS"
    return out


def main() -> int:
    Path("artifacts").mkdir(exist_ok=True)
    started = time.time()
    results, failures = [], []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {e: pool.submit(_endpoint, e) for e in _endpoints()}
        for e, fut in futures.items():
            try: results.append(fut.result())
            except Exception as exc: failures.append({"endpoint": e, "error": type(exc).__name__ + ": " + str(exc)})
    artifact = {
        "schema_version": 1,
        "mission": "PHANTOMX S5A CURVE MAI/USDC.e FORENSIC PROBE",
        "strategy": "S5-CURVE-UV3",
        "read_only": True, "signing": False, "submission": False, "broadcast": False, "live_capital": False,
        "generated_at_unix": int(time.time()), "duration_seconds": round(time.time()-started, 3),
        "chain_id_expected": 137,
        "provenance": {
            "git_commit_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
            "git_ref": os.environ.get("GITHUB_REF", "UNKNOWN"),
            "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "UNKNOWN"),
        },
        "probe_revision": PROBE_REVISION,
        "curve_pool": CURVE_POOL, "token_a": USDC_E, "token_b": MIMATIC,
        "successful_endpoints": results, "failed_endpoints": failures,
        "economic_certification": "NOT_PERFORMED", "profit_claim": "NONE",
    }
    Path("artifacts/s5a_curve_mai_probe.json").write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    return 0 if results else 1

if __name__ == "__main__":
    raise SystemExit(main())

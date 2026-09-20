#!/usr/bin/env python3
"""Aggregate bounded First-Hunt fee-tier shard evidence.

The aggregator is fail-closed: every declared Uniswap V3 fee tier must supply
one artifact whose coverage is COMPLETE. Gross-positive observations remain
read-only quote evidence and are never converted into profit claims.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

EXPECTED_FEES = (100, 500, 3000, 10000)
EXPECTED_PAIR_INDICES = tuple(range(9))
COMPLETE_COVERAGE = {"COMPLETE", "COMPLETE_NO_COMMON_ROUTE"}


def load_shards(root: Path) -> list[dict]:
    files = sorted(root.glob("*/first_hunt_live_scan.json"))
    shards: list[dict] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise SystemExit(f"invalid shard artifact {path}: {type(exc).__name__}: {exc}") from exc
        shards.append(payload)
    return shards


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "downloaded-shards")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "artifacts/first_hunt_live_scan.json")
    shards = load_shards(root)

    by_shard: dict[tuple[int, int], dict] = {}
    rejected: list[dict] = []
    for shard in shards:
        fees = tuple(int(x) for x in shard.get("selected_fee_tiers", ()))
        if len(fees) != 1 or fees[0] not in EXPECTED_FEES:
            rejected.append({"reason": "invalid_fee_shard", "fees": list(fees)})
            continue
        fee = fees[0]
        try:
            pair_index = int(shard.get("pair_index"))
        except (TypeError, ValueError):
            rejected.append({"reason": "invalid_pair_index", "fee": fee})
            continue
        if pair_index not in EXPECTED_PAIR_INDICES:
            rejected.append({"reason": "invalid_pair_index", "fee": fee, "pair_index": pair_index})
            continue
        pairs = shard.get("successful_endpoints", [])
        if len(pairs) != 1:
            rejected.append({"reason": "missing_successful_endpoint", "fee": fee, "pair_index": pair_index})
            continue
        declared = shard.get("pairs", [])
        if len(declared) != 1:
            rejected.append({"reason": "non_atomic_pair_shard", "fee": fee, "pair_index": pair_index})
            continue
        key = (fee, pair_index)
        if key in by_shard:
            rejected.append({"reason": "duplicate_fee_pair_shard", "fee": fee, "pair_index": pair_index})
            continue
        by_shard[key] = shard

    expected_keys = [(fee, pair_index) for fee in EXPECTED_FEES for pair_index in EXPECTED_PAIR_INDICES]
    missing = [{"fee": fee, "pair_group": group} for fee, group in expected_keys if (fee, group) not in by_shard]
    incomplete = []
    observations: list[dict] = []
    gross_positive: list[dict] = []
    post_flash_positive: list[dict] = []
    tile_results: list[dict] = []
    attempts = 0
    shard_blocks: set[int] = set()
    shard_chains: set[int] = set()

    for fee, pair_index in expected_keys:
        shard = by_shard.get((fee, pair_index))
        if shard is None:
            continue
        result = shard["successful_endpoints"][0]
        coverage = result.get("coverage", {})
        if result.get("market_block_number") is None:
            incomplete.append({
                "fee": fee,
                "coverage_status": "MISSING_MARKET_BLOCK",
            })
        else:
            shard_blocks.add(int(result["market_block_number"]))
        for chain_id in result.get("chain_ids", []):
            shard_chains.add(int(chain_id))
        if coverage.get("status") != "COMPLETE":
            incomplete.append({
                "fee": fee,
                "coverage_status": coverage.get("status"),
                "completed_tile_count": coverage.get("completed_tile_count"),
                "expected_tile_count": coverage.get("expected_tile_count"),
            })
        tile_results.extend(result.get("fee_tier_tile_results", []))
        observations.extend(result.get("observations", []))
        gross_positive.extend(result.get("gross_positive_observations", []))
        post_flash_positive.extend(
            item for item in result.get("observations", [])
            if int(item.get("post_flash_premium_delta_raw", 0)) > 0
        )
        attempts += int(shard.get("rpc_pool", {}).get("attempt_count", 0))

    ranked = sorted(observations, key=lambda item: int(item["gross_delta_raw"]), reverse=True)
    shared_block_valid = len(shard_blocks) == 1
    shared_chain_valid = shard_chains == {137}

    aggregate = {
        "schema_version": 2,
        "mission": "PHANTOMX FIRST HUNT READ-ONLY LIVE SCAN",
        "read_only": True,
        "signing": False,
        "submission": False,
        "broadcast": False,
        "live_capital": False,
        "selected_fee_tiers": list(EXPECTED_FEES),
        "shard_count": len(by_shard),
        "expected_shard_count": len(expected_keys),
        "missing_shards": missing,
        "rejected_shards": rejected,
        "incomplete_shards": incomplete,
        "market_block_numbers": sorted(shard_blocks),
        "market_block_number": next(iter(shard_blocks)) if shared_block_valid else None,
        "market_chain_ids": sorted(shard_chains),
        "coverage": {
            "expected_tile_count": 9 * len(EXPECTED_FEES),
            "completed_tile_count": sum(
                1 for item in tile_results
                if item.get("coverage_status") in COMPLETE_COVERAGE
            ),
            "incomplete_tile_count": sum(
                1 for item in tile_results
                if item.get("coverage_status") not in COMPLETE_COVERAGE
            ),
            "status": (
                "COMPLETE"
                if not missing and not rejected and not incomplete
                and shared_block_valid
                and shared_chain_valid
                and len(tile_results) == 9 * len(EXPECTED_FEES)
                else "PARTIAL_INCOMPLETE"
            ),
        },
        "observation_count": len(observations),
        "gross_positive_count": len(gross_positive),
        "post_flash_positive_count": len(post_flash_positive),
        "gross_max_usdc": (
            str(Decimal(ranked[0]["gross_delta_raw"]) / Decimal(10**6))
            if ranked else "0"
        ),
        "post_flash_max_usdc": (
            str(
                Decimal(
                    max(
                        (int(item["post_flash_premium_delta_raw"]) for item in observations),
                        default=0,
                    )
                ) / Decimal(10**6)
            )
        ),
        "top_gross_observations": ranked[:20],
        "fee_tier_tile_results": tile_results,
        "rpc_attempt_count": attempts,
        "economic_certification": "NOT_PERFORMED",
        "profit_claim": "NONE",
        "notes": [
            "Each Uniswap V3 fee tier is independently bounded to nine declared pairs.",
            "The aggregate is green only when all 36 atomic fee/pair shards and all 36 pair/fee tiles are complete.",
            "Gross-positive observations are quote evidence only.",
            "Post-flash-positive observations are still not net-profit proof.",
            "Exact gas, valuation, relay cost, final requote and realized PnL remain outside this scan.",
        ],
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(aggregate, indent=2, sort_keys=True), encoding="utf-8")
    print(
        f"{aggregate['coverage']['status']} shards={len(by_shard)}/{len(EXPECTED_FEES)} "
        f"tiles={aggregate['coverage']['completed_tile_count']}/{aggregate['coverage']['expected_tile_count']} "
        f"observations={aggregate['observation_count']} "
        f"gross_positive={aggregate['gross_positive_count']} "
        f"post_flash_positive={aggregate['post_flash_positive_count']} "
        f"gross_max_usdc={aggregate['gross_max_usdc']} "
        f"post_flash_max_usdc={aggregate['post_flash_max_usdc']}",
        flush=True,
    )
    return 0 if aggregate["coverage"]["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())

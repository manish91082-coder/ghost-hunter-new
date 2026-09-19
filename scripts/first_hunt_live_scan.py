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
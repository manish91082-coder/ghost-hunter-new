#!/usr/bin/env python3
"""Read-only X1: Uniswap V3 same-venue fee-tier dislocation hunt."""
from __future__ import annotations
import json,os,sys,time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.cycle_route import simulate_cycle
from phantomx.dynamic_market_policy import DynamicLoanInputs,compute_dynamic_loan_ceiling
from phantomx.market_block import acquire_market_block
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from phantomx.dynamic_pair_surface import discover_live_base_pairs
from phantomx.uniswap_v3 import UniswapV3ExactQuoter
from first_hunt_live_scan import PAIRS,UNISWAP_V3_FACTORY,UNISWAP_V3_QUOTER,UNISWAP_V3_FEE_TIERS,USDC,dynamic_loan_frontier_usdc
POLYGON_CHAIN_ID=137

def _scan_rpc(rpc:Any,provider_label:str)->dict[str,Any]:
    uv3=UniswapV3ExactQuoter(rpc,UNISWAP_V3_FACTORY,UNISWAP_V3_QUOTER)
    context=acquire_market_block(rpc)
    aave=AaveV3PolygonDynamicReader(rpc).snapshot(USDC,context)
    ceiling=compute_dynamic_loan_ceiling(DynamicLoanInputs(aave_available_raw=aave.available_liquidity_raw,route_input_ceiling_raw=aave.available_liquidity_raw,price_impact_ceiling_raw=aave.available_liquidity_raw,system_hard_cap_raw=None,safety_headroom_bps=500))
    amounts=tuple(x*10**6 for x in dynamic_loan_frontier_usdc(ceiling//10**6))
    observations=[]; tiles=[]
    pair_surface_status = "SEED_ONLY"
    active_pairs = PAIRS
    try:
        pair_surface = discover_live_base_pairs(
            rpc, base_token=USDC,
            seed_pairs=tuple((p.name, p.token_b) for p in PAIRS),
            required_venues=("uniswap_v3",),
            lookback_blocks=25_000,
            chunk_size=2_000,
        )
        active_pairs = tuple((p.name, p.token_b) for p in pair_surface.pairs)
        pair_surface_status = pair_surface.status
    except Exception as exc:
        pair_surface_status = "PAIR_UNIVERSE_INCOMPLETE"
        print(f"PAIR_DISCOVERY_FALLBACK: {type(exc).__name__}: {exc}", flush=True)
    for pair_name,token_b in active_pairs:
        pools=[]
        pool_errors = []
        for fee in UNISWAP_V3_FEE_TIERS:
            try:
                pools.append((fee,uv3.resolve_pool(USDC,token_b,fee,context)))
            except Exception as exc:
                pool_errors.append({"fee": fee, "error_type": type(exc).__name__, "error": str(exc)})
        if len(pools)<2:
            tiles.append({
                "pair": pair_name,
                "status": "INSUFFICIENT_POOL_VARIANTS",
                "pool_variants": len(pools),
                "pool_errors": pool_errors,
            })
            continue
        for fee_in,pool_in in pools:
            for fee_out,pool_out in pools:
                if fee_in==fee_out: continue
                count=0
                route_errors=[]
                for amount in amounts:
                    try:
                        first=uv3.quote_snapshot(amount,USDC,token_b,fee_in,context)
                        second=uv3.quote_snapshot(first.amount_out,token_b,USDC,fee_out,context)
                        sim=simulate_cycle((first,second))
                        observations.append({
                            "pair":pair_name,"fee_in":fee_in,"fee_out":fee_out,"pool_in":pool_in,"pool_out":pool_out,
                            "loan_amount_usdc":str(Decimal(amount)/Decimal(10**6)),
                            "loan_amount_raw":amount,"final_amount_raw":sim.final_amount,
                            "final_amount_usdc":str(Decimal(sim.final_amount)/Decimal(10**6)),
                            "gross_delta_raw":sim.final_amount-sim.initial_amount,
                            "gross_delta_usdc":str(Decimal(sim.final_amount-sim.initial_amount)/Decimal(10**6)),
                            "chain_id":sim.chain_id,"block_number":sim.block_number,"route_hash":sim.route_hash,
                            "legs":[asdict(leg) for leg in sim.legs],
                        })
                        count+=1
                    except Exception as exc:
                        route_errors.append({
                            "loan_amount_usdc": str(Decimal(amount) / Decimal(10**6)),
                            "error_type": type(exc).__name__,
                            "error": str(exc),
                        })
                        # Do not abandon this fee-tier route because one amount
                        # failed. Continue with the remaining frontier.
                        continue
                tiles.append({
                    "pair":pair_name,
                    "fee_in":fee_in,
                    "fee_out":fee_out,
                    "pool_in":pool_in,
                    "pool_out":pool_out,
                    "status":"SUCCESS" if count else "UNAVAILABLE_OR_FAILED",
                    "observation_count":count,
                    "route_error_count":len(route_errors),
                    "route_errors":route_errors[-5:],
                })

    ranked=sorted(observations,key=lambda x:x["gross_delta_raw"],reverse=True)
    return {"endpoint":provider_label,"chain_id":POLYGON_CHAIN_ID,"block_number":context.block_number,"pair_universe":{"status":pair_surface_status,"seed_count":len(PAIRS),"active_count":len(active_pairs)},"observation_count":len(observations),"gross_positive_count":sum(x["gross_delta_raw"]>0 for x in observations),"gross_max_usdc":str(Decimal(ranked[0]["gross_delta_raw"])/Decimal(10**6)) if ranked else "0","top_gross_observations":ranked[:20],"tiles":tiles,"status":"SUCCESS"}

def main()->int:
    Path("artifacts").mkdir(exist_ok=True); started=time.time(); pool=build_free_polygon_rpc_pool(); results=[]; failures=[]
    try: results.append(_scan_rpc(pool,"failover-pool"))
    except Exception as exc: failures.append({"endpoint":"failover-pool","error":type(exc).__name__+": "+str(exc)})
    artifact={"schema_version":1,"mission":"PHANTOMX X1 UNISWAP V3 SAME-VENUE FEE-TIER DISLOCATION READ-ONLY","strategy":"X1-UV3-FEE-DISLOCATION","read_only":True,"signing":False,"submission":False,"broadcast":False,"live_capital":False,"generated_at_unix":int(time.time()),"duration_seconds":round(time.time()-started,3),"successful_endpoints":results,"failed_endpoints":failures,"rpc_pool":{"mode":"task_preserving_failover","provider_count":len(pool.records),"failover_events":[asdict(x) for x in pool.failure_history()],"provider_stats":list(pool.provider_stats())},"economic_certification":"NOT_PERFORMED","profit_claim":"NONE"}
    Path("artifacts/x1_uv3_fee_dislocation_live_scan.json").write_text(json.dumps(artifact,indent=2,sort_keys=True),encoding="utf-8")
    return 0 if results else 1
if __name__=="__main__": raise SystemExit(main())
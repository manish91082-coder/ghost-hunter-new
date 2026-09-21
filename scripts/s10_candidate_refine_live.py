#!/usr/bin/env python3
"""Read-only refinement of the latest S10 micro-positive candidate family."""
from __future__ import annotations
import json, os, sys, time
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from phantomx.aave_v3_dynamic import AaveV3PolygonDynamicReader
from phantomx.cross_venue_qsv3_ramses_v3_route import build_quickswap_v3_to_ramses_v3_route, build_ramses_v3_to_quickswap_v3_route
from phantomx.dynamic_market_policy import DynamicLoanInputs, compute_dynamic_loan_ceiling
from phantomx.dynamic_route_guard import evaluate_simulation_domain
from phantomx.market_block import acquire_market_block
from phantomx.quickswap_v3 import QuickSwapV3ExactQuoter
from phantomx.ramses_v3 import RamsesV3ExactQuoter
from phantomx.rpc_failover import build_free_polygon_rpc_pool
from first_hunt_live_scan import dynamic_loan_frontier_usdc

CHAIN=137
USDC_E='0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'
DAI='0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063'
QSV3_FACTORY='0x411b0fAcC3489691f28ad58c47006AF5E3Ab3a28'
QSV3_QUOTER='0xa15F0D7377B2A0C0c10db057f641beD21028FC89'
RAMSES_FACTORY='0x2Bef16A0081565E72100D73CBe19B1Bd2d802380'
RAMSES_QUOTER='0x3c4532424Eb018013595e4960Fd3de5397B6f571'

def dense_amounts(ceiling_usdc:int)->tuple[int,...]:
    anchors=[10,20,25,50,75,90,95,100,105,110,125,150,175,200,250,300,400,500,750,1000,1500,2500,5000,7500,10000]
    if ceiling_usdc < 10: raise ValueError('ceiling below $10')
    vals=[x for x in anchors if x<=ceiling_usdc]
    if ceiling_usdc not in vals: vals.append(ceiling_usdc)
    return tuple(sorted(set(vals)))

def _record(sim, amount:int, premium_bps:int, direction:str, tick_spacing:int):
    premium=(amount*premium_bps+5000)//10000
    return {
      'direction':direction,'loan_amount_usdc':str(Decimal(amount)/Decimal(10**6)),
      'gross_delta_usdc':str(Decimal(sim.final_amount-sim.initial_amount)/Decimal(10**6)),
      'post_flash_premium_delta_usdc':str(Decimal(sim.final_amount-sim.initial_amount-premium)/Decimal(10**6)),
      'flash_loan_premium_bps':premium_bps,'block_number':sim.block_number,'chain_id':sim.chain_id,
      'route_hash':sim.route_hash,'legs':[asdict(leg) for leg in sim.legs],
      'pool_in':sim.legs[0].pool_or_router if sim.legs else None,'pool_out':sim.legs[1].pool_or_router if len(sim.legs)>1 else None,
      'ramses_tick_spacing':tick_spacing
    }

def main()->int:
    started=time.time(); Path('artifacts').mkdir(exist_ok=True); pool=build_free_polygon_rpc_pool()
    context=acquire_market_block(pool)
    aave=AaveV3PolygonDynamicReader(pool).snapshot(USDC_E,context)
    ceiling=compute_dynamic_loan_ceiling(DynamicLoanInputs(aave_available_raw=aave.available_liquidity_raw,route_input_ceiling_raw=aave.available_liquidity_raw,price_impact_ceiling_raw=aave.available_liquidity_raw,system_hard_cap_raw=None,safety_headroom_bps=500))
    max_usdc=ceiling//10**6; amounts=tuple(x*10**6 for x in dense_amounts(max_usdc))
    q=QuickSwapV3ExactQuoter(pool,QSV3_FACTORY,QSV3_QUOTER); r=RamsesV3ExactQuoter(pool,RAMSES_FACTORY,RAMSES_QUOTER)
    results=[]
    for spacing in (1,5,10,50,100,200):
      try:
        rp=r.resolve_pool(USDC_E,DAI,spacing,context); qp=q.resolve_pool(USDC_E,DAI,context)
        forward=[]; reverse=[]
        for amount in amounts:
          forward.append(build_quickswap_v3_to_ramses_v3_route(pool,q,r,amount_in=amount,token_a=USDC_E,token_b=DAI,ramses_tick_spacing=spacing,block=context))
          reverse.append(build_ramses_v3_to_quickswap_v3_route(pool,q,r,amount_in=amount,token_a=USDC_E,token_b=DAI,ramses_tick_spacing=spacing,block=context))
        ceiling_eval=evaluate_simulation_domain(forward=tuple(forward),reverse=tuple(reverse),max_degradation_bps=100)
        for item in ceiling_eval.evaluated:
          if item.forward is not None: results.append(_record(item.forward,item.amount,aave.flash_loan_premium_bps,'qsv3->ramses',spacing))
          if item.reverse is not None: results.append(_record(item.reverse,item.amount,aave.flash_loan_premium_bps,'ramses->qsv3',spacing))
      except Exception as exc:
        print(f'spacing={spacing} unavailable: {type(exc).__name__}: {exc}',flush=True)
    ranked=sorted(results,key=lambda x:float(x['gross_delta_usdc']),reverse=True)
    artifact={
      'schema_version':1,'mission':'PHANTOMX S10 CANDIDATE REFINEMENT READ-ONLY','strategy':'S10-QSV3-RAMSES-V3','chain_id':CHAIN,
      'read_only':True,'signing':False,'submission':False,'broadcast':False,'live_capital':False,
      'base_pair':'USDC.e/DAI','pinned_block':context.block_number,'aave_available_liquidity_usdc':str(Decimal(aave.available_liquidity_raw)/Decimal(10**6)),
      'aave_flash_loan_premium_bps':aave.flash_loan_premium_bps,'dynamic_ceiling_usdc':str(Decimal(ceiling)/Decimal(10**6)),
      'dense_loan_amounts_usdc':[x//10**6 for x in amounts],'observation_count':len(results),
      'gross_positive_count':sum(float(x['gross_delta_usdc'])>0 for x in results),
      'post_flash_positive_count':sum(float(x['post_flash_premium_delta_usdc'])>0 for x in results),
      'top_observations':ranked[:25],
      'economic_certification':'NOT_PERFORMED','profit_claim':'NONE',
      'duration_seconds':round(time.time()-started,3),
      'provenance':{'git_commit_sha':os.getenv('GITHUB_SHA','UNKNOWN'),'git_ref':os.getenv('GITHUB_REF','UNKNOWN'),'workflow_run_id':os.getenv('GITHUB_RUN_ID','UNKNOWN'),'workflow_run_attempt':os.getenv('GITHUB_RUN_ATTEMPT','UNKNOWN')},
      'rpc_pool':{'provider_count':len(pool.records),'failover_events':[asdict(x) for x in pool.failure_history()],'provider_stats':list(pool.provider_stats())}
    }
    out=Path('artifacts/s10_candidate_refine.json'); out.write_text(json.dumps(artifact,indent=2,sort_keys=True),encoding='utf-8')
    print(f'REFINEMENT observations={len(results)} gross_positive={artifact["gross_positive_count"]} post_flash_positive={artifact["post_flash_positive_count"]} best_gross={ranked[0]["gross_delta_usdc"] if ranked else "0"}',flush=True)
    print(f'Wrote {out}',flush=True)
    return 0 if results else 1

if __name__=='__main__': raise SystemExit(main())
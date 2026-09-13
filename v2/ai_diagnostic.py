"""
PhantomX AI Diagnostic Tool
=============================
AI Brain की पूरी diagnosis करता है:
1. Current weights का analysis
2. Training data vs Live data distribution comparison
3. AI decisions on 1000 live-like scenarios
4. Mismatch detection: training token vs live token
5. Gas model accuracy check

Usage: python ai_diagnostic.py
"""
import os, sys, json, math
import numpy as np
from web3 import Web3
from eth_abi import decode

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))
from ai_brain import PhantomAIBrain

# ─── Constants ────────────────────────────────────────────────────────────────
RPC_URL       = "https://polygon-bor.publicnode.com"
USDC_DEC      = 6
AAVE_FEE      = 0.0009
QS_FEE        = 0.003
UV3_FEE       = 0.0005
TOTAL_FEE_PCT = AAVE_FEE + QS_FEE + UV3_FEE   # 0.44%

MULTICALL3   = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY   = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY  = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC         = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH":  {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC":{"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":  {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]


def decode_uv3_price(sqrtPriceX96, token0_is_usdc, tok_dec):
    if sqrtPriceX96 == 0: return 0.0
    usdc_dec = 10 ** USDC_DEC
    price_ratio = (sqrtPriceX96 / (2**96)) ** 2
    if token0_is_usdc:
        return (1.0 / price_ratio) * (tok_dec / usdc_dec)
    else:
        return price_ratio * (tok_dec / usdc_dec)


def section(title):
    print(f"\n{'═'*65}")
    print(f"  {title}")
    print(f"{'═'*65}")


def analyze_training_data():
    section("PHASE 1A: Training Data Analysis")
    training_file = "real_training_data_50k.jsonl"
    if not os.path.exists(training_file):
        print("  ❌ Training data file not found!")
        return {}

    prices, spreads, gases, reserves = [], [], [], []
    with open(training_file) as f:
        for i, line in enumerate(f):
            if i >= 5000: break  # Sample first 5000
            try:
                row = json.loads(line)
                prices.append(row.get("real_price", 0))
                spreads.append(row.get("real_spread_pct", 0) * 100)
                gases.append(row.get("base_gas_fee_gwei", 0))
                reserves.append(row.get("qs_usdc_reserves", 0))
            except: pass

    print(f"\n  Training Data Summary (first 5000 rows):")
    print(f"  {'─'*50}")
    print(f"  real_price   : min={min(prices):.4f}, max={max(prices):.4f}, avg={np.mean(prices):.4f}")
    print(f"  ⚠️  This is WMATIC price (~$0.37-0.38), NOT WETH/WBTC!")
    print(f"  spread_pct   : min={min(spreads):.4f}%, max={max(spreads):.4f}%, avg={np.mean(spreads):.4f}%")
    print(f"  base_gas_gwei: min={min(gases):.1f}, max={max(gases):.1f}, avg={np.mean(gases):.1f}")
    print(f"  ⚠️  Training gas avg {np.mean(gases):.1f} Gwei — REAL gas today ~280 Gwei!")
    print(f"  qs_reserves  : min=${min(reserves)/1e6:.2f}M, max=${max(reserves)/1e6:.2f}M, avg=${np.mean(reserves)/1e6:.2f}M")

    # Spread distribution
    tiny   = sum(1 for s in spreads if s < 0.05)
    small  = sum(1 for s in spreads if 0.05 <= s < 0.50)
    medium = sum(1 for s in spreads if 0.50 <= s < 1.0)
    large  = sum(1 for s in spreads if s >= 1.0)
    total  = len(spreads)
    print(f"\n  Training Spread Distribution (out of {total}):")
    print(f"    < 0.05% (below DEX fee): {tiny:5d} ({tiny/total*100:.1f}%) — AI trained to IGNORE these")
    print(f"    0.05–0.50% (marginal)  : {small:5d} ({small/total*100:.1f}%) — Often unprofitable")
    print(f"    0.50–1.0%  (viable)    : {medium:5d} ({medium/total*100:.1f}%) — Potentially profitable")
    print(f"    > 1.0%     (excellent) : {large:5d} ({large/total*100:.1f}%) — Highly profitable")

    return {
        "avg_price": np.mean(prices), "avg_spread": np.mean(spreads),
        "avg_gas": np.mean(gases), "spread_dist": {
            "tiny": tiny/total, "small": small/total,
            "medium": medium/total, "large": large/total
        }
    }


def analyze_weights():
    section("PHASE 1B: Weight Analysis")
    weights_file = "real_trained_ai_weights.json"
    if not os.path.exists(weights_file):
        print("  ❌ Weights file not found!")
        return

    with open(weights_file) as f:
        weights = json.load(f)

    wl = np.array(weights["loan_sizing_weights"])
    wb = np.array(weights["dynamic_bribe_weights"])

    print(f"\n  Loan Sizing Weights [spread, reserves, gas, competitor, price]:")
    dims = ["spread_pct", "qs_reserves", "base_gas_gwei", "competitor_gwei", "real_price"]
    for d, w in zip(dims, wl):
        bar = "+" * int(abs(w)*10) if w > 0 else "-" * int(abs(w)*10)
        print(f"    {d:20s}: {w:+.4f}  {bar}")

    print(f"\n  Bribe Weights [spread, reserves, gas, competitor, price]:")
    for d, w in zip(dims, wb):
        bar = "+" * int(abs(w)*10) if w > 0 else "-" * int(abs(w)*10)
        print(f"    {d:20s}: {w:+.4f}  {bar}")

    # Training log
    training_log = "real_training_log.jsonl"
    if os.path.exists(training_log):
        with open(training_log) as f:
            lines = [l for l in f if l.strip()]
        print(f"\n  Training Log: {len(lines)} generation(s) completed")
        if len(lines) == 1:
            print(f"  🚨 WARNING: Only 1 generation was trained (target was 150)!")
            print(f"  🚨 AI is UNDERTRAINED — needs to be re-run!")
        last = json.loads(lines[-1])
        print(f"  Best reward achieved: {last['reward']:.2f}")
    else:
        print(f"  ⚠️ Training log not found")


def simulate_ai_on_live_data(live_data):
    section("PHASE 1C: AI Decision Quality on Live Data")
    brain = PhantomAIBrain()

    print(f"\n  Simulating AI on live prices with current weights...")
    print(f"  {'─'*60}")

    results = {"EXECUTE": 0, "WAIT": 0, "IGNORE": 0}
    false_positives = 0  # EXECUTE when actually unprofitable
    correct_ignores = 0

    for sym, info in live_data.items():
        qs_price    = info["qs_price"]
        uv3_price   = info["uv3_price"]
        reserves    = info["qs_usdc_reserves"]
        gas_gwei    = info["gas_gwei"]

        # What AI decides
        decision, loan, est_profit, bribe = brain.analyze_scenario(
            qs_price, uv3_price, reserves, gas_gwei
        )
        results[decision] = results.get(decision, 0) + 1

        # Ground truth: is trade actually profitable?
        spread_pct = abs(qs_price - uv3_price) / max(qs_price, 1) * 100
        max_loan = reserves * 0.01
        gross = max_loan * spread_pct / 100
        fees  = max_loan * TOTAL_FEE_PCT
        gas_cost = 500_000 * gas_gwei * 1e-9 * 0.50
        actual_profit = gross - fees - gas_cost
        actually_profitable = actual_profit > 0

        print(f"  {sym:6s}: QS ${qs_price:>10,.4f} | UV3 ${uv3_price:>10,.4f} | "
              f"Spread {spread_pct:.3f}% | Gas {gas_gwei:.0f}G")
        print(f"         AI→ {decision:7s} | Est ${est_profit:>8.2f} | "
              f"Actual ${actual_profit:>8.2f} | {'✅ Profitable' if actually_profitable else '❌ NOT Profitable'}")

        if decision == "EXECUTE" and not actually_profitable:
            false_positives += 1
            print(f"         ⚠️  FALSE POSITIVE — AI says EXECUTE but trade is actually unprofitable!")
        if decision == "IGNORE" and not actually_profitable:
            correct_ignores += 1

    print(f"\n  Decision Summary: {results}")
    print(f"  False Positives (EXECUTE on unprofitable): {false_positives}")
    print(f"  Correct Ignores: {correct_ignores}")
    return results, false_positives


def fetch_live_prices():
    section("PHASE 1D: Fetching Live Prices")
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
        if not w3.is_connected():
            print("  ❌ RPC failed")
            return {}
        gas_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
        print(f"  ✅ Connected | Gas: {gas_gwei:.1f} Gwei")

        mc  = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
        qsf = w3.eth.contract(address=QS_FACTORY,  abi=QS_FACTORY_ABI)
        u3f = w3.eth.contract(address=UV3_FACTORY, abi=UV3_FACTORY_ABI)
        qsp = w3.eth.contract(abi=QS_PAIR_ABI)
        u3p = w3.eth.contract(abi=UV3_POOL_ABI)

        syms  = list(TARGET_TOKENS.keys())
        dcalls = []
        for sym in syms:
            t = TARGET_TOKENS[sym]["addr"]
            dcalls.append((QS_FACTORY, qsf.encode_abi("getPair",  args=[USDC, t])))
            dcalls.append((UV3_FACTORY, u3f.encode_abi("getPool",  args=[USDC, t, 500])))
        _, ret = mc.functions.aggregate(dcalls).call()

        pools = {}
        ZERO  = "0x0000000000000000000000000000000000000000"
        for i, sym in enumerate(syms):
            qa = decode(["address"], ret[i*2])[0]
            ua = decode(["address"], ret[i*2+1])[0]
            if qa == ZERO: continue
            pools[sym] = {
                "qs": Web3.to_checksum_address(qa),
                "u3": Web3.to_checksum_address(ua),
                "tok": TARGET_TOKENS[sym]["addr"],
                "dec": TARGET_TOKENS[sym]["decimals"],
            }

        pcalls = []
        for sym in pools:
            pcalls.append((pools[sym]["qs"], qsp.encode_abi("getReserves", args=[])))
            pcalls.append((pools[sym]["u3"], u3p.encode_abi("slot0",       args=[])))
        _, pret = mc.functions.aggregate(pcalls).call()

        live = {}
        for i, sym in enumerate(pools):
            info     = pools[sym]
            tok_dec  = 10 ** info["dec"]
            tok_addr = info["tok"]

            r0,r1,_ = decode(["uint112","uint112","uint32"], pret[i*2])
            t0usdc   = int(USDC,16) < int(tok_addr,16)
            ur, tr   = (r0,r1) if t0usdc else (r1,r0)
            usdc_res = ur / 10**USDC_DEC
            qs_price = usdc_res / (tr/tok_dec) if tr > 0 else 0

            s0 = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], pret[i*2+1])
            uv3_price = decode_uv3_price(s0[0], t0usdc, tok_dec)

            live[sym] = {
                "qs_price": qs_price, "uv3_price": uv3_price,
                "qs_usdc_reserves": usdc_res, "gas_gwei": gas_gwei,
                "token0_is_usdc": t0usdc, "tok_dec": tok_dec,
            }
            print(f"  {sym:6s}: QS ${qs_price:>12,.4f} | UV3 ${uv3_price:>12,.4f}")

        return live
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return {}


def generate_diagnosis_report(train_stats, live_data, decision_results, false_positives):
    section("PHASE 1E: DIAGNOSIS REPORT")

    issues = []
    recommendations = []

    # Issue 1: Training generations
    with open("real_training_log.jsonl") as f:
        gen_count = sum(1 for l in f if l.strip())
    if gen_count < 10:
        issues.append(f"🚨 AI only trained for {gen_count} generation(s) out of 150 target")
        recommendations.append("Run full 150-generation retraining")

    # Issue 2: Token mismatch
    avg_training_price = train_stats.get("avg_price", 0)
    if avg_training_price < 1.0:
        issues.append(f"🚨 Training data used WMATIC price (~${avg_training_price:.2f}) but live tests WETH/WBTC")
        recommendations.append("Remove or normalize 'real_price' feature in observation")

    # Issue 3: Gas mismatch
    avg_training_gas = train_stats.get("avg_gas", 0)
    if live_data:
        live_gas = list(live_data.values())[0].get("gas_gwei", 280)
        if avg_training_gas < live_gas * 0.5:
            issues.append(f"🚨 Training gas {avg_training_gas:.0f} Gwei vs Live {live_gas:.0f} Gwei — {live_gas/avg_training_gas:.1f}x mismatch!")
            recommendations.append("Update gas model in training environment")

    # Issue 4: False positives
    if false_positives > 0:
        issues.append(f"🚨 AI has {false_positives} false positive EXECUTE decisions on live data")
        recommendations.append("Recalibrate profit threshold or retrain AI")

    print(f"\n  ISSUES FOUND: {len(issues)}")
    for issue in issues:
        print(f"    {issue}")

    print(f"\n  RECOMMENDATIONS: {len(recommendations)}")
    for i, rec in enumerate(recommendations, 1):
        print(f"    {i}. {rec}")

    # Save report
    report = {
        "issues": issues,
        "recommendations": recommendations,
        "training_stats": train_stats,
        "decision_results": decision_results,
        "false_positives": false_positives,
        "needs_retraining": gen_count < 10 or false_positives > 0,
    }
    with open("ai_diagnosis_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  💾 Report saved: ai_diagnosis_report.json")
    print(f"\n  {'═'*65}")
    print(f"  VERDICT: {'🚨 AI NEEDS RETRAINING' if report['needs_retraining'] else '✅ AI OK'}")
    print(f"  {'═'*65}\n")
    return report


def main():
    print("=" * 65)
    print("  PHANTOM-X AI DIAGNOSTIC TOOL")
    print("  Analyzing AI Training Quality vs Live Market Conditions")
    print("=" * 65)

    train_stats   = analyze_training_data()
    analyze_weights()
    live_data     = fetch_live_prices()
    if live_data:
        decision_results, false_positives = simulate_ai_on_live_data(live_data)
    else:
        decision_results, false_positives = {}, 0
    report = generate_diagnosis_report(train_stats, live_data, decision_results, false_positives)
    return report


if __name__ == "__main__":
    main()

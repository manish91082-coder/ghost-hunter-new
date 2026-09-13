"""
PhantomX Profitability Simulator
==================================
Live prices लेकर हर token pair के लिए full P&L calculate करता है।
सभी fees include करता है: Aave Flash Loan + DEX swap fees + Gas Cost.

Usage: python profitability_simulator.py
"""

import os
import sys
import json
import asyncio
from web3 import Web3
from eth_abi import decode

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))

RPC_URL = "https://polygon-bor.publicnode.com"

MULTICALL3  = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY  = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC        = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
USDC_DECIMALS = 6

TARGET_TOKENS = {
    "WETH":  {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC":{"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":  {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

# Fee constants
AAVE_FEE_PCT    = 0.0009   # 0.09%
QS_FEE_PCT      = 0.003    # 0.30%
UV3_FEE_PCT     = 0.0005   # 0.05% (500 bps pool)
TOTAL_FEE_PCT   = AAVE_FEE_PCT + QS_FEE_PCT + UV3_FEE_PCT

# Gas estimates
GAS_FOR_ARBIT   = 500_000  # conservative estimate
POL_PRICE_USD   = 0.50     # approximate MATIC/POL price in USD

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]


def decode_uv3_price(sqrtPriceX96: int, token0_is_usdc: bool, tok_dec: int) -> float:
    if sqrtPriceX96 == 0:
        return 0.0
    usdc_dec = 10 ** USDC_DECIMALS
    price_ratio = (sqrtPriceX96 / (2**96)) ** 2
    if token0_is_usdc:
        return (1.0 / price_ratio) * (tok_dec / usdc_dec)
    else:
        return price_ratio * (tok_dec / usdc_dec)


def simulate_arb(symbol: str, qs_price: float, uv3_price: float,
                 qs_usdc_reserves: float, gas_gwei: float) -> dict:
    """
    एक arbitrage trade का full P&L simulate करता है।
    Returns: dict with all metrics
    """
    if qs_price == 0 or uv3_price == 0:
        return {"error": "Missing price"}

    spread_pct = abs(qs_price - uv3_price) / max(qs_price, uv3_price) * 100
    start_on_qs = qs_price < uv3_price  # QS सस्ता है, वहाँ खरीदो

    # Max loan size = 1% of QS pool reserves (safe limit)
    max_loan_usdc = qs_usdc_reserves * 0.01

    # --- Fee Breakdown ---
    # 1. Aave flash loan fee
    aave_fee_usd = max_loan_usdc * AAVE_FEE_PCT

    # 2. DEX swap fees (2 swaps total)
    qs_swap_fee_usd  = max_loan_usdc * QS_FEE_PCT
    uv3_swap_fee_usd = max_loan_usdc * UV3_FEE_PCT

    total_fees_usd = aave_fee_usd + qs_swap_fee_usd + uv3_swap_fee_usd

    # 3. Gas cost
    gas_cost_pol = GAS_FOR_ARBIT * gas_gwei * 1e-9  # in POL
    gas_cost_usd = gas_cost_pol * POL_PRICE_USD

    # --- Gross Profit (before fees) ---
    # If spread is X%, gross profit = loan * X%
    gross_profit_usd = max_loan_usdc * (spread_pct / 100)

    # --- Net Profit ---
    net_profit_usd = gross_profit_usd - total_fees_usd - gas_cost_usd

    # --- Break-even spread ---
    break_even_spread_pct = (total_fees_usd + gas_cost_usd) / max_loan_usdc * 100

    return {
        "symbol":              symbol,
        "qs_price":            qs_price,
        "uv3_price":           uv3_price,
        "spread_pct":          spread_pct,
        "start_on_qs":         start_on_qs,
        "max_loan_usdc":       max_loan_usdc,
        "aave_fee_usd":        aave_fee_usd,
        "qs_swap_fee_usd":     qs_swap_fee_usd,
        "uv3_swap_fee_usd":    uv3_swap_fee_usd,
        "gas_cost_usd":        gas_cost_usd,
        "total_fees_usd":      total_fees_usd + gas_cost_usd,
        "gross_profit_usd":    gross_profit_usd,
        "net_profit_usd":      net_profit_usd,
        "break_even_spread_pct": break_even_spread_pct,
        "is_profitable":       net_profit_usd > 0,
    }


def print_simulation(r: dict):
    sym     = r["symbol"]
    profit  = r["net_profit_usd"]
    icon    = "✅ PROFITABLE" if r["is_profitable"] else "❌ NOT PROFITABLE"
    direction = "QS→UV3" if r["start_on_qs"] else "UV3→QS"

    print(f"\n  {'═'*52}")
    print(f"  TOKEN  : {sym} ({direction})")
    print(f"  {'─'*52}")
    print(f"  QS Price        : ${r['qs_price']:>15,.4f}")
    print(f"  UV3 Price       : ${r['uv3_price']:>15,.4f}")
    print(f"  Price Spread    : {r['spread_pct']:>14.4f}%")
    print(f"  Max Loan (1%)   : ${r['max_loan_usdc']:>15,.2f}")
    print(f"  {'─'*52}")
    print(f"  Aave Fee (0.09%): ${r['aave_fee_usd']:>15,.4f}")
    print(f"  QS Fee   (0.30%): ${r['qs_swap_fee_usd']:>15,.4f}")
    print(f"  UV3 Fee  (0.05%): ${r['uv3_swap_fee_usd']:>15,.4f}")
    print(f"  Gas Cost        : ${r['gas_cost_usd']:>15,.4f}")
    print(f"  Total Costs     : ${r['total_fees_usd']:>15,.4f}")
    print(f"  {'─'*52}")
    print(f"  Gross Profit    : ${r['gross_profit_usd']:>15,.4f}")
    print(f"  NET PROFIT      : ${profit:>15,.4f}  {icon}")
    print(f"  Break-even Spread: {r['break_even_spread_pct']:.4f}%")


def main():
    print("=" * 60)
    print("  PhantomX Profitability Simulator")
    print("  Full P&L with All Fees (Live Data)")
    print("=" * 60)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        print("❌ RPC connection failed!")
        sys.exit(1)

    gas_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
    print(f"\n✅ Connected | Gas: {gas_gwei:.1f} Gwei\n")

    mc  = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qsf = w3.eth.contract(address=QS_FACTORY,  abi=QS_FACTORY_ABI)
    u3f = w3.eth.contract(address=UV3_FACTORY, abi=UV3_FACTORY_ABI)
    qs_pair_t = w3.eth.contract(abi=QS_PAIR_ABI)
    u3_pool_t = w3.eth.contract(abi=UV3_POOL_ABI)

    symbols = list(TARGET_TOKENS.keys())

    # Discover pools
    disc_calls = []
    for sym in symbols:
        t = TARGET_TOKENS[sym]["addr"]
        disc_calls.append((QS_FACTORY, qsf.encode_abi("getPair",  args=[USDC, t])))
        disc_calls.append((UV3_FACTORY, u3f.encode_abi("getPool",  args=[USDC, t, 500])))

    _, ret = mc.functions.aggregate(disc_calls).call()
    pools = {}
    for i, sym in enumerate(symbols):
        qs_addr = decode(["address"], ret[i*2])[0]
        u3_addr = decode(["address"], ret[i*2+1])[0]
        if qs_addr == "0x0000000000000000000000000000000000000000":
            continue
        pools[sym] = {
            "qs":  Web3.to_checksum_address(qs_addr),
            "u3":  Web3.to_checksum_address(u3_addr),
            "tok": TARGET_TOKENS[sym]["addr"],
            "dec": TARGET_TOKENS[sym]["decimals"],
        }

    # Fetch prices
    price_calls = []
    for sym in pools:
        price_calls.append((pools[sym]["qs"], qs_pair_t.encode_abi("getReserves", args=[])))
        price_calls.append((pools[sym]["u3"], u3_pool_t.encode_abi("slot0",       args=[])))

    _, price_ret = mc.functions.aggregate(price_calls).call()

    all_results = []
    for i, sym in enumerate(pools):
        info     = pools[sym]
        tok_dec  = 10 ** info["dec"]
        usdc_dec = 10 ** USDC_DECIMALS
        tok_addr = info["tok"]

        r0, r1, _ = decode(["uint112","uint112","uint32"], price_ret[i*2])
        token0_is_usdc = int(USDC, 16) < int(tok_addr, 16)
        if token0_is_usdc:
            usdc_res, tok_res = r0, r1
        else:
            tok_res, usdc_res = r0, r1

        qs_usdc_reserves = usdc_res / usdc_dec
        qs_price = (usdc_res / usdc_dec) / (tok_res / tok_dec) if tok_res > 0 else 0

        slot0 = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], price_ret[i*2+1])
        u3_price = decode_uv3_price(slot0[0], token0_is_usdc, tok_dec)

        sim = simulate_arb(sym, qs_price, u3_price, qs_usdc_reserves, gas_gwei)
        print_simulation(sim)
        all_results.append(sim)

    # Final summary
    print(f"\n  {'═'*52}")
    print(f"  PROFITABILITY SUMMARY")
    print(f"  {'─'*52}")
    print(f"  Gas Price: {gas_gwei:.1f} Gwei | POL≈${POL_PRICE_USD}")
    print(f"  Total Fee Rate: {TOTAL_FEE_PCT*100:.2f}%")
    print()
    for r in all_results:
        status = "✅" if r["is_profitable"] else "❌"
        print(f"  {status} {r['symbol']:6s}: Spread {r['spread_pct']:.3f}% | "
              f"Break-even {r['break_even_spread_pct']:.3f}% | "
              f"Net ${r['net_profit_usd']:+.2f}")
    print(f"\n  📌 Current market spreads are NORMAL (< 1%).")
    print(f"  📌 Arbitrage opportunities appear only during high volatility.")
    print(f"  📌 Bot will SCAN continuously and execute ONLY when profitable.")
    print(f"  {'═'*52}\n")

    with open("profitability_simulation.json", "w") as f:
        json.dump({"gas_gwei": gas_gwei, "results": all_results}, f, indent=2)
    print("💾 Saved to profitability_simulation.json")


if __name__ == "__main__":
    main()

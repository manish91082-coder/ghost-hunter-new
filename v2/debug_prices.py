"""
PhantomX Price Diagnostic Tool
===============================
यह tool live blockchain से QS और UV3 prices fetch करता है और compare करता है।
इसे run करने से पहले कोई भी fix देखी जा सकती है।

Usage: python debug_prices.py
"""

import os
import sys
import asyncio
import aiohttp
import json
import time
from web3 import Web3
from eth_abi import decode

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.path.dirname(__file__))

# ─── CONSTANTS ──────────────────────────────────────────────────────────────
RPC_URL = "https://polygon-bor.publicnode.com"

MULTICALL3  = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY  = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC        = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH":  {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC":{"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":  {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

USDC_DECIMALS = 6

# ABIs
MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]


def decode_uv3_price(sqrtPriceX96: int, token0_is_usdc: bool, tok_dec: int) -> float:
    """
    Uniswap V3 sqrtPriceX96 को USDC-per-Token में convert करता है।
    
    Uniswap V3 stores price as sqrt(Token1/Token0) * 2^96
    So: price_ratio = (sqrtPriceX96 / 2^96)^2 = Token1_amount / Token0_amount (in raw units)
    
    Case 1: token0=USDC, token1=WETH
        price_ratio = WETH_raw / USDC_raw
        USDC per WETH = (1/price_ratio) * (tok_dec / usdc_dec)
    
    Case 2: token0=WETH, token1=USDC
        price_ratio = USDC_raw / WETH_raw
        USDC per WETH = price_ratio * (tok_dec / usdc_dec)
    """
    if sqrtPriceX96 == 0:
        return 0.0

    usdc_dec = 10 ** USDC_DECIMALS

    price_ratio = (sqrtPriceX96 / (2**96)) ** 2

    if token0_is_usdc:
        # Token0=USDC(6dec), Token1=e.g.WETH(18dec)
        # price_ratio = WETH_raw / USDC_raw
        # USDC per WETH = (USDC_raw / WETH_raw) * (tok_dec/usdc_dec)
        #               = (1/price_ratio) * (tok_dec/usdc_dec)
        uv3_price = (1.0 / price_ratio) * (tok_dec / usdc_dec)
    else:
        # Token0=e.g.WETH(18dec), Token1=USDC(6dec)
        # price_ratio = USDC_raw / WETH_raw
        # USDC per WETH = (USDC_raw / WETH_raw) * (tok_dec/usdc_dec)
        #               = price_ratio * (tok_dec/usdc_dec)
        uv3_price = price_ratio * (tok_dec / usdc_dec)

    return uv3_price


async def main():
    print("=" * 60)
    print("  PhantomX Price Diagnostic Tool")
    print("  Live QS vs UV3 Price Comparison")
    print("=" * 60)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        print("❌ RPC connection failed!")
        sys.exit(1)

    block = w3.eth.block_number
    gas_price_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
    print(f"\n✅ Connected | Block: {block} | Gas: {gas_price_gwei:.1f} Gwei\n")

    mc  = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qsf = w3.eth.contract(address=QS_FACTORY,  abi=QS_FACTORY_ABI)
    u3f = w3.eth.contract(address=UV3_FACTORY, abi=UV3_FACTORY_ABI)
    qs_pair_t = w3.eth.contract(abi=QS_PAIR_ABI)
    u3_pool_t = w3.eth.contract(abi=UV3_POOL_ABI)

    # ── Step 1: Discover Pools ────────────────────────────────────────────────
    print("🔍 Discovering pools via Multicall3...")
    disc_calls = []
    symbols = list(TARGET_TOKENS.keys())
    for sym in symbols:
        t = TARGET_TOKENS[sym]["addr"]
        disc_calls.append((QS_FACTORY, qsf.encode_abi("getPair",  args=[USDC, t])))
        disc_calls.append((UV3_FACTORY, u3f.encode_abi("getPool",  args=[USDC, t, 500])))

    block_num, ret = mc.functions.aggregate(disc_calls).call()
    pools = {}
    for i, sym in enumerate(symbols):
        qs_addr  = decode(["address"], ret[i*2])[0]
        u3_addr  = decode(["address"], ret[i*2+1])[0]
        token_addr = TARGET_TOKENS[sym]["addr"]
        if qs_addr == "0x0000000000000000000000000000000000000000" or u3_addr == "0x0000000000000000000000000000000000000000":
            print(f"  ⚠️  {sym}: Pool not found!")
            continue
        pools[sym] = {
            "qs":  Web3.to_checksum_address(qs_addr),
            "u3":  Web3.to_checksum_address(u3_addr),
            "tok": token_addr,
            "dec": TARGET_TOKENS[sym]["decimals"],
        }
        print(f"  ✅ {sym}: QS={qs_addr[:10]}... UV3={u3_addr[:10]}...")

    # ── Step 2: Fetch Prices ──────────────────────────────────────────────────
    print("\n📊 Fetching live prices...\n")
    price_calls = []
    for sym in pools:
        price_calls.append((pools[sym]["qs"], qs_pair_t.encode_abi("getReserves", args=[])))
        price_calls.append((pools[sym]["u3"], u3_pool_t.encode_abi("slot0",       args=[])))

    _, price_ret = mc.functions.aggregate(price_calls).call()

    results = []
    for i, sym in enumerate(pools):
        info    = pools[sym]
        tok_dec = 10 ** info["dec"]
        usdc_dec = 10 ** USDC_DECIMALS
        tok_addr = info["tok"]

        # ── Quickswap price ──
        qs_data = price_ret[i*2]
        qs_price = 0.0
        qs_usdc_reserves = 0.0
        if len(qs_data) >= 96:
            r0, r1, _ = decode(["uint112","uint112","uint32"], qs_data)
            token0_is_usdc = int(USDC, 16) < int(tok_addr, 16)
            if token0_is_usdc:
                usdc_res, tok_res = r0, r1
            else:
                tok_res, usdc_res = r0, r1
            qs_usdc_reserves = usdc_res / usdc_dec
            if tok_res > 0:
                qs_price = (usdc_res / usdc_dec) / (tok_res / tok_dec)

        # ── Uniswap V3 price (with FIXED formula) ──
        u3_data = price_ret[i*2+1]
        u3_price = 0.0
        sqrtPriceX96 = 0
        if len(u3_data) >= 224:
            slot0 = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], u3_data)
            sqrtPriceX96 = slot0[0]
            u3_price = decode_uv3_price(sqrtPriceX96, token0_is_usdc, tok_dec)

        # ── Compare ──
        if qs_price > 0 and u3_price > 0:
            spread_pct = abs(qs_price - u3_price) / qs_price * 100
            spread_ok  = "✅" if spread_pct < 2.0 else "🔴 LARGE SPREAD"
        else:
            spread_pct = 0
            spread_ok  = "⚠️ MISSING PRICE"

        results.append({
            "symbol":          sym,
            "qs_price":        qs_price,
            "u3_price":        u3_price,
            "spread_pct":      spread_pct,
            "qs_usdc_reserves":qs_usdc_reserves,
            "sqrtPriceX96":    sqrtPriceX96,
            "token0_is_usdc":  token0_is_usdc,
        })

        print(f"  {'─'*52}")
        print(f"  Token   : {sym}")
        print(f"  QS Price: ${qs_price:>15,.4f}   (Pool USDC reserves: ${qs_usdc_reserves:,.0f})")
        print(f"  UV3 Price:${u3_price:>15,.4f}   (sqrtPriceX96: {sqrtPriceX96})")
        print(f"  Spread  : {spread_pct:.4f}%  {spread_ok}")
        print(f"  token0_is_usdc: {token0_is_usdc}")
        print()

    # ── Step 3: Summary ───────────────────────────────────────────────────────
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Gas Price : {gas_price_gwei:.1f} Gwei")
    total_fees_pct = 0.09 + 0.30 + 0.05  # Aave + QS + UV3
    print(f"  Total DEX Fees (Aave+QS+UV3): {total_fees_pct:.2f}%")
    print(f"  Minimum Profitable Spread   : {total_fees_pct + 0.20:.2f}% (with 0.20% safety margin)")
    print()
    for r in results:
        status = "✅ NORMAL" if r["spread_pct"] < 2 else f"🔴 LARGE ({r['spread_pct']:.2f}%)"
        print(f"  {r['symbol']:6s}: QS ${r['qs_price']:,.2f} | UV3 ${r['u3_price']:,.2f} | {status}")
    print()
    print("  ✅ If QS and UV3 prices are close (< 2%), the UV3 formula is CORRECT.")
    print("  🔴 If UV3 shows astronomically high/low values, formula is still wrong.")
    print("=" * 60)

    # Save results
    with open("debug_prices_output.json", "w") as f:
        json.dump({
            "block": block,
            "gas_gwei": gas_price_gwei,
            "results": results
        }, f, indent=2)
    print("\n💾 Results saved to debug_prices_output.json")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

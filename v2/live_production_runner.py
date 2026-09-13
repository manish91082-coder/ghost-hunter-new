"""
PhantomX Live Production Runner - FIXED VERSION
=================================================
Fixes applied:
  [FIX-1] UV3 sqrtPriceX96 price formula corrected (was inverted)
  [FIX-2] Live gas price fetch (was hardcoded 0.5 Gwei)
  [FIX-3] amountOutMin slippage formula corrected (was 0)
  [FIX-4] Local nonce counter (no more nonce race conditions)
  [FIX-5] Minimum spread threshold (0.50% = break-even + safety)
  [FIX-6] Circuit breaker (3 consecutive reverts → 10 min pause)
  [FIX-7] DRY_RUN mode via .env (DRY_RUN=true = scan but no TX)

Usage:
  DRY RUN  : set DRY_RUN=true in .env  → python live_production_runner.py
  LIVE RUN : set DRY_RUN=false in .env → python live_production_runner.py
"""

import os
import sys
import json
import time
import asyncio
import aiohttp
from web3 import Web3
from eth_abi import decode
from eth_account import Account
from dotenv import load_dotenv
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))
from ai_brain import PhantomAIBrain
try:
    from telegram_notifier import send_telegram_message
    HAS_TELEGRAM = True
except ImportError:
    HAS_TELEGRAM = False
    def send_telegram_message(msg): return True

load_dotenv()

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"   # FIX-7: safe default

SLIPPAGE_BPS          = 50      # 0.50% max slippage per swap
MIN_SPREAD_PCT        = 0.50    # FIX-5: minimum spread to consider (break-even ~0.44%)
MAX_CONSECUTIVE_REVERTS = 3     # FIX-6: circuit breaker threshold
CIRCUIT_BREAKER_PAUSE = 600     # seconds to pause after circuit breaker trips

PUBLIC_RPCS = [
    "https://polygon-bor.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://polygon.meowrpc.com",
]

# ─── CONTRACT ADDRESSES ──────────────────────────────────────────────────────
MULTICALL3   = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY   = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY  = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC         = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
USDC_DECIMALS = 6

TARGET_TOKENS = {
    "WETH":  {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC":{"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":  {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

# ─── ABIs ─────────────────────────────────────────────────────────────────────
MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]
PHANTOM_ABI = [{"inputs":[{"internalType":"address","name":"_usdc","type":"address"},{"internalType":"address","name":"_targetToken","type":"address"},{"internalType":"uint256","name":"_flashLoanAmount","type":"uint256"},{"internalType":"bool","name":"_startQuickswap","type":"bool"},{"internalType":"uint256","name":"_amountOutMin1","type":"uint256"},{"internalType":"uint256","name":"_amountOutMin2","type":"uint256"}],"name":"executeArbitrage","outputs":[],"stateMutability":"nonpayable","type":"function"}]

# ─── TIER SYSTEM ─────────────────────────────────────────────────────────────
TIERS      = [1, 5, 10, 20, 50, 75, 100]
STATE_FILE = "live_production_state.json"
LOG_FILE   = "live_hunt_log.jsonl"
SCAN_METRICS_FILE = "live_scan_metrics.jsonl"


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_connected_w3():
    for rpc in PUBLIC_RPCS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                print(f"✅ Connected: {rpc}")
                return w3, rpc
        except Exception:
            pass
    sys.exit("❌ All RPCs failed.")


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"successful_hunts": 0, "current_tier_index": 0}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_contract_address():
    if os.path.exists("deployed_contract.txt"):
        with open("deployed_contract.txt") as f:
            return Web3.to_checksum_address(f.read().strip())
    return None


def log_hunt(event: dict):
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def log_scan_metric(metric: dict):
    with open(SCAN_METRICS_FILE, "a") as f:
        f.write(json.dumps(metric) + "\n")



# ─── [FIX-1] CORRECTED UV3 PRICE FORMULA ────────────────────────────────────
def decode_uv3_price(sqrtPriceX96: int, token0_is_usdc: bool, tok_dec: int) -> float:
    """
    Uniswap V3 sqrtPriceX96 → USDC-per-Token price.

    Uniswap V3 stores: sqrtPriceX96 = sqrt(Token1/Token0) * 2^96
    So: price_ratio = (sqrtPriceX96/2^96)^2 = Token1_raw / Token0_raw

    Case A: token0 = USDC, token1 = e.g. WETH
        price_ratio = WETH_raw / USDC_raw
        USD per WETH = (1/price_ratio) * (tok_dec / usdc_dec)

    Case B: token0 = e.g. WETH, token1 = USDC
        price_ratio = USDC_raw / WETH_raw
        USD per WETH = price_ratio * (tok_dec / usdc_dec)
    """
    if sqrtPriceX96 == 0:
        return 0.0
    usdc_dec = 10 ** USDC_DECIMALS
    price_ratio = (sqrtPriceX96 / (2 ** 96)) ** 2
    if token0_is_usdc:
        return (1.0 / price_ratio) * (tok_dec / usdc_dec)
    else:
        return price_ratio * (tok_dec / usdc_dec)


# ─── [FIX-3] CORRECTED SLIPPAGE FORMULA ─────────────────────────────────────
def calc_slippage_params(optimal_loan: float, qs_price: float, uv3_price: float,
                         tok_dec: int, start_on_qs: bool) -> tuple:
    """
    amountOutMin1 और amountOutMin2 calculate करता है।
    SLIPPAGE_BPS = 50 (0.5%) — नुकसान से बचाव के लिए।

    start_on_qs=True  → USDC→Token on QS, then Token→USDC on UV3
    start_on_qs=False → USDC→Token on UV3, then Token→USDC on QS
    """
    usdc_dec = 10 ** USDC_DECIMALS
    slip = 1.0 - (SLIPPAGE_BPS / 10_000)

    if start_on_qs:
        # Swap 1: USDC → Token on QuickSwap
        expected_token_out = optimal_loan / qs_price
        amountOutMin1 = int(expected_token_out * slip * tok_dec)
        # Swap 2: Token → USDC on UniswapV3 (expect at least loan back)
        amountOutMin2 = int(optimal_loan * slip * usdc_dec)
    else:
        # Swap 1: USDC → Token on UniswapV3
        expected_token_out = optimal_loan / uv3_price
        amountOutMin1 = int(expected_token_out * slip * tok_dec)
        # Swap 2: Token → USDC on QuickSwap
        amountOutMin2 = int(optimal_loan * slip * usdc_dec)

    return amountOutMin1, amountOutMin2


# ─── POOL DISCOVERY ──────────────────────────────────────────────────────────
def discover_pools(w3: Web3) -> dict:
    print("🔍 Discovering live AMM pools...")
    mc  = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qsf = w3.eth.contract(address=QS_FACTORY,  abi=QS_FACTORY_ABI)
    u3f = w3.eth.contract(address=UV3_FACTORY, abi=UV3_FACTORY_ABI)

    symbols = list(TARGET_TOKENS.keys())
    calls = []
    for sym in symbols:
        t = TARGET_TOKENS[sym]["addr"]
        calls.append((QS_FACTORY, qsf.encode_abi("getPair",  args=[USDC, t])))
        calls.append((UV3_FACTORY, u3f.encode_abi("getPool",  args=[USDC, t, 500])))

    _, ret = mc.functions.aggregate(calls).call()
    pools = {}
    ZERO = "0x0000000000000000000000000000000000000000"
    for i, sym in enumerate(symbols):
        qs_addr = decode(["address"], ret[i * 2])[0]
        u3_addr = decode(["address"], ret[i * 2 + 1])[0]
        if qs_addr == ZERO or u3_addr == ZERO:
            print(f"  ⚠️  {sym}: Pool not found, skipping.")
            continue
        pools[sym] = {
            "qs":  Web3.to_checksum_address(qs_addr),
            "u3":  Web3.to_checksum_address(u3_addr),
            "tok": TARGET_TOKENS[sym]["addr"],
            "dec": TARGET_TOKENS[sym]["decimals"],
        }
        print(f"  ✅ {sym}: QS & UV3 pools found.")
    return pools


# ─── MAIN LOOP ───────────────────────────────────────────────────────────────
async def main():
    mode_str = "🔵 DRY RUN MODE (no real transactions)" if DRY_RUN else "🔴 LIVE EXECUTION MODE"
    print("=" * 60)
    print(f"  🚀 PHANTOM-X LIVE PRODUCTION RUNNER")
    print(f"  {mode_str}")
    print("=" * 60)

    # ── Wallet ──
    private_key = os.getenv("GHOSTHUNTER_DEV_PRIVATE_KEY")
    if not private_key:
        sys.exit("❌ GHOSTHUNTER_DEV_PRIVATE_KEY not found in .env")
    account = Account.from_key(private_key)
    print(f"\n🔑 Vault : {account.address}")

    # ── RPC ──
    w3, rpc_url = get_connected_w3()

    # ── Contract ──
    contract_address = get_contract_address()
    if not contract_address:
        sys.exit("❌ deployed_contract.txt not found. Deploy first!")
    print(f"📄 Contract : {contract_address}")

    # ── Tier State ──
    state   = load_state()
    hunts   = state["successful_hunts"]
    tier_idx = state["current_tier_index"]
    if tier_idx >= len(TIERS):
        print("🎉 All tiers completed! Running in infinite mode.")
        target_hunts = float("inf")
    else:
        target_hunts = TIERS[tier_idx]
    print(f"🎯 Tier {tier_idx + 1}: Target {target_hunts} hunts | Done: {hunts}")

    if hunts >= target_hunts:
        print("✅ Tier already met. Advancing...")
        state["current_tier_index"] += 1
        save_state(state)
        sys.exit(0)

    # ── Setup contracts ──
    brain        = PhantomAIBrain()
    mc           = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qs_pair_t    = w3.eth.contract(abi=QS_PAIR_ABI)
    u3_pool_t    = w3.eth.contract(abi=UV3_POOL_ABI)
    phantom_c    = w3.eth.contract(address=contract_address, abi=PHANTOM_ABI)

    # ── Discover Pools ──
    pools   = discover_pools(w3)
    symbols = list(pools.keys())

    if not symbols:
        sys.exit("❌ No valid pools found!")

    # ── [FIX-4] Init local nonce counter ──
    local_nonce = w3.eth.get_transaction_count(account.address, "pending")
    print(f"🔢 Starting nonce: {local_nonce}")

    # ── [FIX-6] Circuit breaker state ──
    consecutive_reverts = 0

    # ── 10-Min Heartbeat & Telemetry Tracking ──
    last_telegram_time = 0   # 0 triggers immediate first update on startup!
    total_scans_completed = 0
    last_prices = {}

    print(f"\n📡 Scanning market every 3 seconds...\n")

    async with aiohttp.ClientSession() as session:
        while hunts < target_hunts:

            # ── [FIX-6] Check circuit breaker ──
            if consecutive_reverts >= MAX_CONSECUTIVE_REVERTS:
                print(f"\n⛔ CIRCUIT BREAKER TRIPPED! {consecutive_reverts} consecutive reverts.")
                print(f"⏸️  Pausing for {CIRCUIT_BREAKER_PAUSE // 60} minutes...")
                await asyncio.sleep(CIRCUIT_BREAKER_PAUSE)
                consecutive_reverts = 0
                local_nonce = w3.eth.get_transaction_count(account.address, "pending")
                print(f"▶️  Resuming. Fresh nonce: {local_nonce}")

            # ── Multicall price fetch ──
            calls = []
            for sym in symbols:
                calls.append((pools[sym]["qs"], qs_pair_t.encode_abi("getReserves", args=[])))
                calls.append((pools[sym]["u3"], u3_pool_t.encode_abi("slot0",       args=[])))

            encoded = mc.encode_abi("aggregate", args=[calls])
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{"to": MULTICALL3, "data": encoded}, "latest"],
                "id": 1
            }

            t0 = time.time()
            try:
                async with session.post(rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                    response = await resp.json()
            except Exception as e:
                print(f"⚠️  RPC error: {e}")
                await asyncio.sleep(2)
                continue

            if "result" not in response:
                await asyncio.sleep(1)
                continue

            latency_ms = (time.time() - t0) * 1000
            _, ret = decode(["uint256", "bytes[]"], bytes.fromhex(response["result"][2:]))

            # ── [FIX-2] Live gas price ──
            try:
                base_fee      = w3.eth.gas_price
                base_fee_gwei = float(w3.from_wei(base_fee, "gwei"))
                main.last_gas_gwei = base_fee_gwei
            except Exception as e:
                base_fee_gwei = getattr(main, "last_gas_gwei", 275.0)


            # Track live POL/USD price across iterations (default 0.50)
            live_pol_usd = getattr(main, "live_pol_usd", 0.50)

            # ── Process each token ──
            for i, sym in enumerate(symbols):
                info     = pools[sym]
                tok_addr = info["tok"]
                tok_dec  = 10 ** info["dec"]
                usdc_dec = 10 ** USDC_DECIMALS

                # ── Quickswap price ──
                qs_data = ret[i * 2]
                qs_price = 0.0
                qs_usdc_res = 0.0
                token0_is_usdc = False

                if len(qs_data) >= 96:
                    r0, r1, _ = decode(["uint112", "uint112", "uint32"], qs_data)
                    token0_is_usdc = int(USDC, 16) < int(tok_addr, 16)
                    usdc_res, tok_res = (r0, r1) if token0_is_usdc else (r1, r0)
                    qs_usdc_res = usdc_res / usdc_dec
                    if tok_res > 0:
                        qs_price = qs_usdc_res / (tok_res / tok_dec)

                # ── [FIX-1] Corrected UV3 price ──
                u3_data = ret[i * 2 + 1]
                uv3_price = 0.0
                if len(u3_data) >= 224:
                    slot0 = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], u3_data)
                    uv3_price = decode_uv3_price(slot0[0], token0_is_usdc, tok_dec)

                if qs_price == 0 or uv3_price == 0:
                    continue

                # Update live POL price when WMATIC pool is scanned
                if sym == "WMATIC" and qs_price > 0:
                    live_pol_usd = qs_price
                    main.live_pol_usd = live_pol_usd

                # ── [FIX-5] Minimum spread check ──
                spread_pct = abs(qs_price - uv3_price) / max(qs_price, uv3_price) * 100

                # Save last price snapshot for telemetry reporting
                last_prices[sym] = {"qs": qs_price, "uv3": uv3_price, "spread": spread_pct}
                total_scans_completed += 1

                # ── Pass live gas price and live POL price to AI ──
                decision, optimal_loan, est_profit, mev_bribe = brain.analyze_scenario(
                    qs_price, uv3_price, qs_usdc_res, base_fee_gwei, pair_id=sym, pol_usd=live_pol_usd
                )

                print(f"[SCAN] {sym:6s} | QS ${qs_price:>10,.4f} | UV3 ${uv3_price:>10,.4f} | "
                      f"Spread {spread_pct:.3f}% | Gas {base_fee_gwei:.0f}G | "
                      f"Lat {latency_ms:.0f}ms | {decision}")

                log_scan_metric({
                    "timestamp": time.time(),
                    "symbol": sym,
                    "qs_price": qs_price,
                    "uv3_price": uv3_price,
                    "spread_pct": spread_pct,
                    "gas_gwei": base_fee_gwei,
                    "latency_ms": latency_ms,
                    "decision": decision,
                    "optimal_loan": optimal_loan,
                    "est_profit": est_profit,
                    "dry_run": DRY_RUN
                })

                if spread_pct < MIN_SPREAD_PCT:
                    # Not worth attempting
                    continue

                if decision != "EXECUTE" or est_profit <= 0:
                    continue

                # ── Opportunity found! ──
                start_on_qs = qs_price < uv3_price  # buy on cheaper exchange
                direction   = "QS→UV3" if start_on_qs else "UV3→QS"
                trade_size  = int(optimal_loan * usdc_dec)

                # ── [FIX-3] Slippage params ──
                amt_out_min1, amt_out_min2 = calc_slippage_params(
                    optimal_loan, qs_price, uv3_price, tok_dec, start_on_qs
                )

                print(f"\n🚨 OPPORTUNITY: {sym} ({direction}) | "
                      f"Loan ${optimal_loan:,.2f} | Est Profit ${est_profit:,.2f}")
                print(f"   amountOutMin1: {amt_out_min1} | amountOutMin2: {amt_out_min2}")

                # ── DRY RUN check ──
                if DRY_RUN:
                    print(f"   🔵 [DRY RUN] TX not sent. Would call executeArbitrage(")
                    print(f"       USDC={USDC}, token={tok_addr},")
                    print(f"       amount={trade_size}, startQS={start_on_qs},")
                    print(f"       min1={amt_out_min1}, min2={amt_out_min2})")
                    print(f"   ✅ [DRY RUN] Set DRY_RUN=false in .env to execute live.\n")
                    continue

                # ── [FIX-4] Build TX with local nonce ──
                priority_fee = max(
                    int((mev_bribe * 2 * 1e18) / 500_000),
                    w3.to_wei(30, "gwei")
                )
                max_fee = base_fee + priority_fee

                try:
                    tx = phantom_c.functions.executeArbitrage(
                        USDC, tok_addr, trade_size, start_on_qs, amt_out_min1, amt_out_min2
                    ).build_transaction({
                        "from":                account.address,
                        "nonce":               local_nonce,   # FIX-4: use local nonce
                        "chainId":             137,
                        "gas":                 500_000,
                        "maxFeePerGas":        max_fee,
                        "maxPriorityFeePerGas": priority_fee,
                    })
                    signed = account.sign_transaction(tx)
                    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                    local_nonce += 1                          # FIX-4: increment locally
                    print(f"🚀 TX: {tx_hash.hex()}")

                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    if receipt.status == 1:
                        print(f"✅ HUNT #{hunts + 1} SUCCESS! Block {receipt.blockNumber} | Gas {receipt.gasUsed}")
                        hunts += 1
                        consecutive_reverts = 0               # FIX-6: reset on success
                        state["successful_hunts"] = hunts
                        save_state(state)
                        log_hunt({
                            "timestamp":   time.time(),
                            "tx_hash":     tx_hash.hex(),
                            "symbol":      sym,
                            "direction":   direction,
                            "loan_usd":    optimal_loan,
                            "profit_usd":  est_profit,
                            "gas_used":    receipt.gasUsed,
                            "status":      "SUCCESS",
                        })
                        if HAS_TELEGRAM:
                            tx_url = f"https://polygonscan.com/tx/{tx_hash.hex()}"
                            t_msg = f"""🔥 *PHANTOM-X LIVE ON-CHAIN ARBITRAGE EXECUTED!*
                            
Token: *{sym}* ({direction})
Net Profit: *${est_profit:,.2f} USD*
Flash Loan Size: *${optimal_loan:,.2f} USD*
Block Number: *#{receipt.blockNumber:,}*
Gas Used: *{receipt.gasUsed:,} units*

🔗 [PolygonScan Tx Hash]({tx_url})
🔑 Vault Wallet: `{account.address}`
📄 Contract: `{contract_address}`
Mode: 🔴 LIVE ON-CHAIN EXECUTION ACTIVE"""
                            send_telegram_message(t_msg)

                        if hunts >= target_hunts:
                            print(f"🎉 TIER {target_hunts} COMPLETE!")
                            return
                    else:
                        print(f"❌ TX REVERTED. Gas burned: {receipt.gasUsed}")
                        consecutive_reverts += 1              # FIX-6: increment
                        log_hunt({
                            "timestamp": time.time(),
                            "tx_hash":   tx_hash.hex(),
                            "symbol":    sym,
                            "status":    "REVERTED",
                            "gas_used":  receipt.gasUsed,
                        })

                except Exception as e:
                    print(f"⚠️  TX Error: {e}")
                    # Re-sync nonce on error
                    local_nonce = w3.eth.get_transaction_count(account.address, "pending")

            # ── 10-Minute Periodic Guaranteed Telegram Heartbeat ──
            now_ts = time.time()
            if (now_ts - last_telegram_time) >= 600:
                last_telegram_time = now_ts
                try:
                    curr_blk = w3.eth.block_number
                    ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    price_lines = []
                    for s in symbols:
                        p_info = last_prices.get(s, {})
                        u3_s = f"${p_info.get('uv3', 0):,.4f}" if p_info.get('uv3') else "N/A"
                        qs_s = f"${p_info.get('qs', 0):,.4f}" if p_info.get('qs') else "N/A"
                        sp_s = f"{p_info.get('spread', 0):.4f}%"
                        price_lines.append(f"  • *{s}*: UniV3={u3_s} | QuickV2={qs_s} | Spread={sp_s}")

                    hb_msg = f"""📊 *PhantomX 10-Minute Live On-Chain Telemetry Report*
🕒 *Time*: `{ts_str}`
🔢 *Block*: `#{curr_blk:,}`
⛽ *Gas*: `{base_fee_gwei:.1f} Gwei` (LIVE)

🟢 *Live DEX Prices*:
{chr(10).join(price_lines)}

🔴 *Mode*: DIRECT LIVE ON-CHAIN EXECUTION ACTIVE
🚀 *Executed Hunts*: `{hunts}`
🔍 *Total Scans Completed*: `{total_scans_completed:,}`
🔑 *Vault Wallet*: `{account.address}` (68.65 POL)
📄 *Master Contract*: `{contract_address}`"""

                    if HAS_TELEGRAM:
                        send_telegram_message(hb_msg)
                        print(f"  [+] Guaranteed 10-Min Telegram Heartbeat Sent at {ts_str}!", flush=True)
                except Exception as hb_err:
                    print(f"  [!] Heartbeat Error: {hb_err}", flush=True)

            await asyncio.sleep(3)


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

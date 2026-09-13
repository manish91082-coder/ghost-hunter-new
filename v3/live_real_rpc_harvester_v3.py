"""
PhantomX v3 Universal Profit Engine - 24/7 Live Real-Time Polygon Mainnet Harvester (live_real_rpc_harvester_v3.py)
===================================================================================================================
Continuous Live Polygon Mainnet Harvester & Real-Time AI Brain Trainer.
Features:
  - Low-Priority Execution (Idle Priority Class for Zero PC Lag)
  - ExtraDataToPOAMiddleware Enabled (Web3 v7 Compliant)
  - Infinite Failover RPC Reconnect Loop (Zero Crash on WiFi/DNS drop)
  - Multicall3 Batch Real-Time Live Block Stream
  - Evaluates 5 AI Brains + Live Online Weight Tuner
  - Checkpointing in `checkpoint_state_v3.json`
  - Append-Only Data Logging in `logs/live_scan_metrics_v3.jsonl`
  - Zero Gas Loss (`DRY_RUN=true`)
"""

import sys
import os
import time
import json
import psutil
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_abi import decode

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.join(os.path.dirname(__file__), "ai_engines"))

from universal_ai_brain import UniversalAIBrainV3
from live_online_tuner_v3 import LiveOnlineWeightTunerV3

# Set Process Priority to Low (Idle Priority) for Zero PC Lag
try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.IDLE_PRIORITY_CLASS if os.name == 'nt' else 10)
    print("⚡ Process priority set to LOW (Idle Priority) for Zero PC Lag!")
except Exception as e:
    print(f"⚠️ Priority note: {e}")

# Failover RPC Endpoints (Polygon Mainnet)
PUBLIC_RPCS = [
    "https://polygon-bor.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://1rpc.io/matic"
]

MULTICALL3   = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY  = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC        = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH":   {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC": {"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":   {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"payable","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]

QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]

CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), "checkpoint_state_v3.json")
METRICS_FILE    = os.path.join(os.path.dirname(__file__), "logs", "live_scan_metrics_v3.jsonl")

os.makedirs(os.path.join(os.path.dirname(__file__), "logs"), exist_ok=True)

def get_connected_w3():
    attempt = 0
    while True:
        for rpc in PUBLIC_RPCS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                if w3.is_connected():
                    return w3, rpc
            except Exception:
                pass
        attempt += 1
        print(f"⚠️ All RPCs unreachable (WiFi/DNS drop). Retrying in 5 seconds... (Attempt #{attempt})")
        time.sleep(5)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                print(f"🔄 [v3 Auto-Resume Checkpoint] Block #{state.get('last_block', 'N/A')} | Cumulative Scans: {state.get('cumulative_scans', 0):,} | Net PnL: ${state.get('cumulative_pnl', 0):,.2f}")
                return state
        except Exception as e:
            print(f"⚠️ Error loading checkpoint: {e}")
    return {"last_block": 0, "cumulative_scans": 0, "cumulative_pnl": 0.0, "weights_version": "v3"}

def save_checkpoint(state):
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving checkpoint: {e}")

def decode_uv3_price(sqrtPriceX96: int, token0_is_usdc: bool, tok_dec: int) -> float:
    if sqrtPriceX96 == 0:
        return 0.0
    usdc_dec = 10 ** 6
    price_ratio = (sqrtPriceX96 / (2 ** 96)) ** 2
    if token0_is_usdc:
        return (1.0 / price_ratio) * (tok_dec / usdc_dec)
    else:
        return price_ratio * (tok_dec / usdc_dec)

def discover_pools(w3: Web3) -> dict:
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
        if qs_addr != ZERO and u3_addr != ZERO:
            pools[sym] = {
                "qs":  Web3.to_checksum_address(qs_addr),
                "u3":  Web3.to_checksum_address(u3_addr),
                "tok": TARGET_TOKENS[sym]["addr"],
                "dec": TARGET_TOKENS[sym]["decimals"],
            }
    return pools

def main():
    w3, rpc_url = get_connected_w3()
    print(f"🚀 [PhantomX Harvester v3] Connected to Polygon Mainnet via {rpc_url}")

    pools = discover_pools(w3)
    symbols = list(pools.keys())

    mc = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qs_pair_t = w3.eth.contract(abi=QS_PAIR_ABI)
    u3_pool_t = w3.eth.contract(abi=UV3_POOL_ABI)

    brain = UniversalAIBrainV3()
    tuner = LiveOnlineWeightTunerV3()

    checkpoint = load_checkpoint()
    scans_count = checkpoint.get("cumulative_scans", 0)
    cumulative_pnl = checkpoint.get("cumulative_pnl", 0.0)

    print("📡 [v3 24/7 Harvester] Polygon Mainnet Live Data Stream Started... Press Ctrl+C to pause.\n")

    # FIXED: live_pol_usd is NO LONGER hardcoded. It is updated live from WMATIC price.
    # Default=None until first WMATIC block snapshot arrives from blockchain.
    live_pol_usd = None
    spread_histories = {"WETH": [], "WMATIC": [], "WBTC": []}

    while True:
        try:
            calls = []
            for sym in symbols:
                calls.append((pools[sym]["qs"], qs_pair_t.encode_abi("getReserves", args=[])))
                calls.append((pools[sym]["u3"], u3_pool_t.encode_abi("slot0",       args=[])))

            t0 = time.time()
            _, ret = mc.functions.aggregate(calls).call()
            latency_ms = (time.time() - t0) * 1000

            block_number = w3.eth.block_number
            try:
                base_fee_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
            except Exception:
                base_fee_gwei = 275.0

            for i, sym in enumerate(symbols):
                info     = pools[sym]
                tok_addr = info["tok"]
                tok_dec  = 10 ** info["dec"]
                usdc_dec = 10 ** 6

                # Quickswap price
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

                # Uniswap V3 price
                u3_data = ret[i * 2 + 1]
                uv3_price = 0.0
                if len(u3_data) >= 224:
                    slot0 = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], u3_data)
                    uv3_price = decode_uv3_price(slot0[0], token0_is_usdc, tok_dec)

                if qs_price == 0 or uv3_price == 0:
                    continue

                # FIXED: Update live_pol_usd from WMATIC blockchain price (never hardcoded)
                if sym == "WMATIC" and qs_price > 0:
                    live_pol_usd = qs_price

                # Skip scan if live POL price not yet received from blockchain
                if live_pol_usd is None:
                    continue

                # Triangular Price Simulation
                triangular_price = max(qs_price, uv3_price) * 1.0020 if sym == "WMATIC" else 0.0

                # Analyze AGI Opportunity
                res = brain.analyze_block_opportunity(
                    pair_symbol=sym,
                    qs_price=qs_price,
                    uv3_price=uv3_price,
                    pool_usdc_reserve=qs_usdc_res,
                    gas_fee_gwei=base_fee_gwei,
                    triangular_price=triangular_price,
                    pol_usd=live_pol_usd
                )

                scans_count += 1
                if res["decision"] == "EXECUTE":
                    cumulative_pnl += res["expected_net_pnl_usd"]

                # Perform Real-Time Online Weight Tuning
                sh = spread_histories[sym]
                sh.append(res["effective_spread_pct"])
                if len(sh) > 5:
                    sh.pop(0)
                spread_histories[sym] = sh

                tuner_res = tuner.update_weights_on_live_block(sh, res["effective_spread_pct"])

                metric = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "block": block_number,
                    "scan_id": scans_count,
                    "pair": sym,
                    "qs_price": round(qs_price, 4),
                    "uv3_price": round(uv3_price, 4),
                    "direct_spread_pct": res["direct_spread_pct"],
                    "triangular_spread_pct": res["triangular_spread_pct"],
                    "effective_spread_pct": res["effective_spread_pct"],
                    "gas_gwei": round(base_fee_gwei, 1),
                    "latency_ms": round(latency_ms, 1),
                    "decision": res["decision"],
                    "best_route_name": res["best_route_name"],
                    "optimal_loan_usd": res["optimal_loan_usd"],
                    "expected_net_pnl_usd": res["expected_net_pnl_usd"],
                    "online_tuner_mse": tuner_res.get("avg_mse_loss", 0.0)
                }

                # Append Metric Log
                with open(METRICS_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(metric) + "\n")

                # Save Checkpoint State
                checkpoint["last_block"] = block_number
                checkpoint["cumulative_scans"] = scans_count
                checkpoint["cumulative_pnl"] = round(cumulative_pnl, 2)
                checkpoint["last_timestamp"] = metric["timestamp"]
                save_checkpoint(checkpoint)

                print(f"[{metric['timestamp']}] Block #{block_number} | {sym} | Eff.Spread {metric['effective_spread_pct']:.4f}% | Decision: {metric['decision']} | Route: {metric['best_route_name']} | Loan L*: ${metric['optimal_loan_usd']:,} | Latency: {metric['latency_ms']:.1f}ms")

            time.sleep(1.0) # Smooth pacing

        except Exception as e:
            print(f"⚠️ RPC Exception (Auto-reconnecting in 5s...): {e}")
            time.sleep(5)
            w3, _ = get_connected_w3()

if __name__ == "__main__":
    main()

"""
PhantomX Central RPC Data Ingestor (central_rpc_harvester.py)
===============================================================
24/7 Single-Producer Polygon Mainnet Multicall Streamer with Zero PC Lag Guarantee.
Features:
  - Low-Priority Process Execution (Idle / Below Normal Priority)
  - ExtraDataToPOAMiddleware Enabled (Web3 v7 / Polygon POA Compliant)
  - Infinite Failover RPC Reconnect Loop
  - Single Multicall3 Batch Fetching (Zero Redundant RPC Requests)
  - Appends Raw Market Snapshots to `data/central_live_block_stream.jsonl`
"""

import sys
import os
import time
import json
import psutil
import ctypes
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_abi import decode

sys.stdout.reconfigure(encoding="utf-8")

# Programmatically prevent Windows Sleep/Hibernate while training is active
def prevent_sleep():
    if os.name == 'nt':
        try:
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
            print("⚡ [Power Management] Windows Sleep Prevention ACTIVE (ES_SYSTEM_REQUIRED)")
        except Exception as e:
            print(f"⚠️ Power management note: {e}")

prevent_sleep()

# Set Process Priority to Low (Below Normal) for Zero PC Lag
try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 10)
    print("⚡ [Central Ingestor] Process priority set to LOW (Below Normal) for Zero PC Lag!")
except Exception as e:
    print(f"⚠️ Priority note: {e}")

# Polygon Mainnet Public Failover Endpoints
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

BASE_DIR        = os.path.abspath(os.path.dirname(__file__))
DATA_DIR        = os.path.join(BASE_DIR, "data")
CENTRAL_STREAM  = os.path.join(DATA_DIR, "central_live_block_stream.jsonl")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "central_checkpoint.json")

os.makedirs(DATA_DIR, exist_ok=True)

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
        print(f"⚠️ [Central Ingestor] All RPCs unreachable. Retrying in 5s... (Attempt #{attempt})")
        time.sleep(5)

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading central checkpoint: {e}")
    return {"last_block": 0, "total_snapshots": 0}

def save_checkpoint(state):
    try:
        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Error saving central checkpoint: {e}")

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
    print(f"🚀 [Central Ingestor] Connected to Polygon Mainnet via {rpc_url}")
    print(f"📁 Central Stream File: {CENTRAL_STREAM}")

    pools = discover_pools(w3)
    symbols = list(pools.keys())

    mc = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qs_pair_t = w3.eth.contract(abi=QS_PAIR_ABI)
    u3_pool_t = w3.eth.contract(abi=UV3_POOL_ABI)

    checkpoint = load_checkpoint()
    snapshot_count = checkpoint.get("total_snapshots", 0)

    print("📡 [Central Ingestor] 24/7 Polygon Block Streaming Active... Press Ctrl+C to stop.\n")

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

                snapshot_count += 1
                raw_snapshot = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "block": block_number,
                    "snapshot_id": snapshot_count,
                    "pair": sym,
                    "qs_price": round(qs_price, 4),
                    "uv3_price": round(uv3_price, 4),
                    "usdc_reserves": round(qs_usdc_res, 2),
                    "gas_gwei": round(base_fee_gwei, 1),
                    "latency_ms": round(latency_ms, 1)
                }

                # Write to Central Stream
                with open(CENTRAL_STREAM, "a", encoding="utf-8") as f:
                    f.write(json.dumps(raw_snapshot) + "\n")

                checkpoint["last_block"] = block_number
                checkpoint["total_snapshots"] = snapshot_count
                checkpoint["last_timestamp"] = raw_snapshot["timestamp"]
                save_checkpoint(checkpoint)

                print(f"[{raw_snapshot['timestamp']}] Block #{block_number} | {sym} | QS ${qs_price:.4f} | UV3 ${uv3_price:.4f} | Latency: {latency_ms:.1f}ms")

            time.sleep(1.0) # Smooth 1-sec pacing

        except Exception as e:
            print(f"⚠️ [Central Ingestor] RPC Exception (Auto-reconnecting in 5s...): {e}")
            time.sleep(5)
            w3, _ = get_connected_w3()

if __name__ == "__main__":
    main()

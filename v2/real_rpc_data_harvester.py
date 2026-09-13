import os
import sys
import asyncio
import aiohttp
import time
import json
from web3 import Web3
from eth_abi import decode
from rpc_manager import PredictiveRPCManager

class RPCManagerHelper:
    def __init__(self):
        self.manager = PredictiveRPCManager()
        self.active_url = "https://polygon-bor.publicnode.com"

    async def init_rpc(self):
        best = await self.manager.get_best_rpc()
        if best:
            self.active_url = best

    async def call(self, session, payload):
        try:
            async with session.post(self.active_url, json=payload, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as e:
            # Fallback to direct RPC
            try:
                async with session.post("https://polygon-bor.publicnode.com", json=payload, timeout=5) as resp:
                    if resp.status == 200:
                        return await resp.json()
            except:
                pass
        return None


sys.stdout.reconfigure(encoding='utf-8')

MULTICALL3 = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QUICKSWAP_FACTORY = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UNISWAP_V3_FACTORY = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")
USDC = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")

TARGET_TOKENS = {
    "WETH": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"),
    "WMATIC": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"),
    "WBTC": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"),
}

MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]

w3 = Web3()
multicall_contract = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
qs_factory = w3.eth.contract(address=QUICKSWAP_FACTORY, abi=QS_FACTORY_ABI)
uv3_factory = w3.eth.contract(address=UNISWAP_V3_FACTORY, abi=UV3_FACTORY_ABI)
qs_pair_template = w3.eth.contract(abi=QS_PAIR_ABI)
uv3_pool_template = w3.eth.contract(abi=UV3_POOL_ABI)

discovered_pairs = {}

async def discover_pools(session, rpc_manager):
    print("🔍 [Harvester] Discovering Liquidity Pools on Polygon Mainnet via Multicall...")
    calls = []
    symbols = list(TARGET_TOKENS.keys())
    
    for symbol in symbols:
        token_addr = TARGET_TOKENS[symbol]
        qs_calldata = qs_factory.encode_abi("getPair", args=[USDC, token_addr])
        calls.append((QUICKSWAP_FACTORY, qs_calldata))
        uv3_calldata = uv3_factory.encode_abi("getPool", args=[USDC, token_addr, 500])
        calls.append((UNISWAP_V3_FACTORY, uv3_calldata))

    encoded_multicall = multicall_contract.encode_abi("aggregate", args=[calls])
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{"to": MULTICALL3, "data": encoded_multicall}, "latest"],
        "id": 1
    }
    
    response = await rpc_manager.call(session, payload)
    if not response or "result" not in response:
        print("❌ [Harvester] Multicall pool discovery failed!")
        return False

    result_data = response["result"]
    decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
    return_data = decoded_results[1]
    
    idx = 0
    for symbol in symbols:
        qs_data = return_data[idx]
        uv3_data = return_data[idx+1]
        
        qs_address = Web3.to_checksum_address(decode(["address"], qs_data)[0]) if len(qs_data) >= 32 else "0x0000000000000000000000000000000000000000"
        uv3_address = Web3.to_checksum_address(decode(["address"], uv3_data)[0]) if len(uv3_data) >= 32 else "0x0000000000000000000000000000000000000000"
        idx += 2
        
        if qs_address != "0x0000000000000000000000000000000000000000" and uv3_address != "0x0000000000000000000000000000000000000000":
            discovered_pairs[symbol] = {
                "quickswap": qs_address,
                "uniswapV3": uv3_address,
                "token": TARGET_TOKENS[symbol]
            }
            print(f"  ✅ Discovered {symbol}/USDC -> QS: {qs_address[:10]}... | UV3: {uv3_address[:10]}...")
        else:
            print(f"  ⚠️ Could not resolve pair for {symbol}/USDC")

    return len(discovered_pairs) > 0

async def harvest_real_rpc_scans(target_scans=120, output_file="live_real_rpc_scans.jsonl"):
    print(f"\n🌾 Starting Real-RPC Multicall Harvester -> Target Scans: {target_scans} blocks")
    rpc_manager = RPCManagerHelper()
    await rpc_manager.init_rpc()

    
    token_decimals = {"WBTC": 8, "USDT": 6, "USDC": 6, "WETH": 18, "WMATIC": 18}
    usdc_dec = 1e6

    scans_written = 0
    if os.path.exists(output_file):
        os.remove(output_file)

    async with aiohttp.ClientSession() as session:
        ok = await discover_pools(session, rpc_manager)
        if not ok:
            print("❌ Discovery failed. Aborting harvest.")
            return False

        symbols = list(discovered_pairs.keys())
        start_time = time.time()

        while scans_written < target_scans:
            # 1. Fetch current gas price
            gas_payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 99}
            gas_resp = await rpc_manager.call(session, gas_payload)
            base_gas_gwei = 30.0
            if gas_resp and "result" in gas_resp:
                base_gas_gwei = int(gas_resp["result"], 16) / 1e9

            # 2. Multicall for all discovered pairs
            calls = []
            for symbol in symbols:
                pair = discovered_pairs[symbol]
                qs_calldata = qs_pair_template.encode_abi("getReserves", args=[])
                calls.append((pair["quickswap"], qs_calldata))
                uv3_calldata = uv3_pool_template.encode_abi("slot0", args=[])
                calls.append((pair["uniswapV3"], uv3_calldata))

            encoded_multicall = multicall_contract.encode_abi("aggregate", args=[calls])
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_call",
                "params": [{"to": MULTICALL3, "data": encoded_multicall}, "latest"],
                "id": scans_written + 1
            }

            resp = await rpc_manager.call(session, payload)
            if not resp or "result" not in resp:
                await asyncio.sleep(0.5)
                continue

            result_data = resp["result"]
            decoded_results = decode(["uint256", "bytes[]"], bytes.fromhex(result_data[2:]))
            block_number = decoded_results[0]
            return_data = decoded_results[1]

            # 3. Extract prices & calculate POL price dynamically
            pair_data = {}
            pol_usd = 0.45 # Fallback POL price

            idx = 0
            for symbol in symbols:
                token_address = discovered_pairs[symbol]["token"]
                decimals = token_decimals.get(symbol, 18)
                tok_dec = 10**decimals
                token0_is_usdc = int(USDC, 16) < int(token_address, 16)

                # Decode QuickSwap
                qs_raw = return_data[idx]
                qs_price, qs_usdc_reserves = 0.0, 0.0
                if len(qs_raw) >= 96:
                    qs_res = decode(["uint112", "uint112", "uint32"], qs_raw)
                    if token0_is_usdc:
                        usdc_res, tok_res = qs_res[0], qs_res[1]
                    else:
                        tok_res, usdc_res = qs_res[0], qs_res[1]
                    if tok_res > 0:
                        qs_price = (usdc_res / usdc_dec) / (tok_res / tok_dec)
                        qs_usdc_reserves = usdc_res / usdc_dec

                # Decode Uniswap v3
                uv3_raw = return_data[idx+1]
                uv3_price = 0.0
                if len(uv3_raw) >= 224:
                    uv3_res = decode(["uint160", "int24", "uint16", "uint16", "uint16", "uint8", "bool"], uv3_raw)
                    sqrtPriceX96 = uv3_res[0]
                    if sqrtPriceX96 > 0:
                        raw_ratio = (sqrtPriceX96 / (2**96)) ** 2
                        if token0_is_usdc:
                            # token0 = USDC (6 dec), token1 = Token (tok_dec)
                            uv3_price = (1 / raw_ratio) * (tok_dec / usdc_dec) if raw_ratio > 0 else 0.0
                        else:
                            # token0 = Token (tok_dec), token1 = USDC (6 dec)
                            uv3_price = raw_ratio * (tok_dec / usdc_dec)


                if symbol == "WMATIC" and qs_price > 0:
                    pol_usd = qs_price

                spread_raw = abs(qs_price - uv3_price)
                spread_pct = (spread_raw / max(qs_price, 1)) * 100

                pair_data[symbol] = {
                    "qs_price": round(qs_price, 4),
                    "uv3_price": round(uv3_price, 4),
                    "qs_usdc_reserves": round(qs_usdc_reserves, 2),
                    "spread_usd": round(spread_raw, 4),
                    "spread_pct": round(spread_pct, 4)
                }

                idx += 2

            scans_written += 1

            record = {
                "scan_id": scans_written,
                "timestamp": int(time.time()),
                "block_number": block_number,
                "base_gas_gwei": round(base_gas_gwei, 2),
                "pol_usd": round(pol_usd, 4),
                "pairs": pair_data
            }

            with open(output_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

            if scans_written % 10 == 0 or scans_written == 1:
                weth_info = pair_data.get("WETH", {})
                wmatic_info = pair_data.get("WMATIC", {})
                wbtc_info = pair_data.get("WBTC", {})
                print(f" 📦 Scan {scans_written:03d}/{target_scans} | Block {block_number} | Gas: {base_gas_gwei:.1f} Gwei | POL: ${pol_usd:.3f}")
                print(f"    - WETH/USDC:   QS ${weth_info.get('qs_price',0):.2f} | UV3 ${weth_info.get('uv3_price',0):.2f} | Spread {weth_info.get('spread_pct',0):.3f}%")
                print(f"    - WMATIC/USDC: QS ${wmatic_info.get('qs_price',0):.4f} | UV3 ${wmatic_info.get('uv3_price',0):.4f} | Spread {wmatic_info.get('spread_pct',0):.3f}%")
                print(f"    - WBTC/USDC:   QS ${wbtc_info.get('qs_price',0):.2f} | UV3 ${wbtc_info.get('uv3_price',0):.2f} | Spread {wbtc_info.get('spread_pct',0):.3f}%")

            await asyncio.sleep(0.5)

        elapsed = time.time() - start_time
        print(f"\n✅ [Harvester] Successfully collected {scans_written} REAL live RPC block scans in {elapsed:.1f}s.")
        print(f"📄 Saved to: {output_file}")
        return True

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(harvest_real_rpc_scans(target_scans=120))

"""
PhantomX Gas-Free Live Simulation Engine
==========================================
eth_call का use करके arbitrage transactions को simulate करता है।
- Real live blockchain data use करता है
- Gas: $0 (कोई real TX नहीं)
- Contract का executeArbitrage locally simulate होता है
- Revert reason भी capture करता है

Key functions:
  simulate_arb_ethcall()  → eth_call से trade simulate करो
  estimate_gas()          → gas estimate करो (no spend)
  analyze_revert()        → revert reason parse करो

Usage: python live_ethcall_simulator.py (standalone test)
       OR imported by stress_test_harness.py
"""

import os, sys, json, time
from web3 import Web3
from eth_abi import decode

sys.stdout.reconfigure(encoding="utf-8")
sys.path.append(os.path.dirname(__file__))
from ai_brain import PhantomAIBrain

# ─── Config ───────────────────────────────────────────────────────────────────
RPC_URL          = "https://polygon-bor.publicnode.com"
USDC             = Web3.to_checksum_address("0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
USDC_DECIMALS    = 6
SLIPPAGE_BPS     = 50
GAS_UNITS        = 500_000
POL_USD          = 0.50
MULTICALL3       = Web3.to_checksum_address("0xcA11bde05977b3631167028862bE2a173976CA11")
QS_FACTORY       = Web3.to_checksum_address("0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32")
UV3_FACTORY      = Web3.to_checksum_address("0x1F98431c8aD98523631AE4a59f267346ea31F984")

TARGET_TOKENS = {
    "WETH":  {"addr": Web3.to_checksum_address("0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619"), "decimals": 18},
    "WMATIC":{"addr": Web3.to_checksum_address("0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"), "decimals": 18},
    "WBTC":  {"addr": Web3.to_checksum_address("0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"), "decimals": 8},
}

PHANTOM_ABI = [{"inputs":[{"internalType":"address","name":"_usdc","type":"address"},{"internalType":"address","name":"_targetToken","type":"address"},{"internalType":"uint256","name":"_flashLoanAmount","type":"uint256"},{"internalType":"bool","name":"_startQuickswap","type":"bool"},{"internalType":"uint256","name":"_amountOutMin1","type":"uint256"},{"internalType":"uint256","name":"_amountOutMin2","type":"uint256"}],"name":"executeArbitrage","outputs":[],"stateMutability":"nonpayable","type":"function"}]
MULTICALL_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"target","type":"address"},{"internalType":"bytes","name":"callData","type":"bytes"}],"internalType":"struct Multicall3.Call[]","name":"calls","type":"tuple[]"}],"name":"aggregate","outputs":[{"internalType":"uint256","name":"blockNumber","type":"uint256"},{"internalType":"bytes[]","name":"returnData","type":"bytes[]"}],"stateMutability":"view","type":"function"}]
QS_FACTORY_ABI = [{"constant":True,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_FACTORY_ABI = [{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]
QS_PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":False,"stateMutability":"view","type":"function"}]
UV3_POOL_ABI = [{"inputs":[],"name":"slot0","outputs":[{"internalType":"uint160","name":"sqrtPriceX96","type":"uint160"},{"internalType":"int24","name":"tick","type":"int24"},{"internalType":"uint16","name":"observationIndex","type":"uint16"},{"internalType":"uint16","name":"observationCardinality","type":"uint16"},{"internalType":"uint16","name":"observationCardinalityNext","type":"uint16"},{"internalType":"uint8","name":"feeProtocol","type":"uint8"},{"internalType":"bool","name":"unlocked","type":"bool"}],"stateMutability":"view","type":"function"}]


def decode_uv3_price(sqrtPriceX96, token0_is_usdc, tok_dec):
    if sqrtPriceX96 == 0: return 0.0
    usdc_dec = 10 ** USDC_DECIMALS
    ratio    = (sqrtPriceX96 / (2**96)) ** 2
    return (1.0/ratio)*(tok_dec/usdc_dec) if token0_is_usdc else ratio*(tok_dec/usdc_dec)


def calc_slippage(loan_usd, price, tok_dec, start_on_qs, uv3_price=None):
    """Calculate amountOutMin1 and amountOutMin2 with SLIPPAGE_BPS protection."""
    slip     = 1.0 - SLIPPAGE_BPS / 10_000
    usdc_dec = 10 ** USDC_DECIMALS
    ref_price = price if start_on_qs else (uv3_price or price)
    min1 = int((loan_usd / ref_price) * slip * tok_dec)
    min2 = int(loan_usd * slip * usdc_dec)
    return min1, min2


def parse_revert_reason(exc_str: str) -> str:
    """Extract human-readable revert reason from Web3 exception."""
    exc = str(exc_str)
    if "execution reverted" in exc:
        # Try to extract the reason string
        import re
        m = re.search(r"execution reverted[:\s]+(.+?)(?:'|\"|\Z)", exc)
        if m:
            return m.group(1).strip()
        return "execution reverted (no reason)"
    if "insufficient funds" in exc.lower():
        return "insufficient funds for gas"
    if "gas required exceeds" in exc.lower():
        return "out of gas"
    return f"unknown error: {exc[:120]}"


# ─── Core simulator function ──────────────────────────────────────────────────
def simulate_arb_ethcall(
    w3: Web3,
    contract_addr: str,
    caller_addr: str,
    token_addr: str,
    loan_usdc: float,
    start_on_qs: bool,
    qs_price: float,
    uv3_price: float,
    tok_dec: int,
    gas_gwei: float,
) -> dict:
    """
    eth_call से arbitrage transaction simulate करता है।
    Gas: $0. Real state read होती है, TX broadcast नहीं होती।

    Returns:
        {
          "success": bool,
          "revert_reason": str or None,
          "gas_estimate": int or None,
          "eth_call_time_ms": float,
          "would_succeed": bool,
        }
    """
    t0 = time.time()
    result = {
        "success": False,
        "revert_reason": None,
        "gas_estimate": None,
        "eth_call_time_ms": 0,
        "would_succeed": False,
        "loan_usdc": loan_usdc,
        "start_on_qs": start_on_qs,
    }

    try:
        phantom = w3.eth.contract(
            address=Web3.to_checksum_address(contract_addr),
            abi=PHANTOM_ABI
        )
        usdc_dec = 10 ** USDC_DECIMALS
        loan_raw = int(loan_usdc * usdc_dec)

        ref_price = qs_price if start_on_qs else uv3_price
        min1, min2 = calc_slippage(loan_usdc, ref_price, tok_dec, start_on_qs, uv3_price)

        # ── eth_call (0 gas) ──────────────────────────────────────────────────
        phantom.functions.executeArbitrage(
            USDC,
            Web3.to_checksum_address(token_addr),
            loan_raw,
            start_on_qs,
            min1,
            min2,
        ).call({"from": Web3.to_checksum_address(caller_addr)})

        result["success"]      = True
        result["would_succeed"] = True

        # ── Gas estimate ──────────────────────────────────────────────────────
        try:
            gas_est = phantom.functions.executeArbitrage(
                USDC, Web3.to_checksum_address(token_addr),
                loan_raw, start_on_qs, min1, min2,
            ).estimate_gas({"from": Web3.to_checksum_address(caller_addr)})
            result["gas_estimate"]      = gas_est
            result["gas_cost_usd"]      = gas_est * gas_gwei * 1e-9 * POL_USD
        except Exception:
            result["gas_estimate"] = GAS_UNITS  # fallback
            result["gas_cost_usd"] = GAS_UNITS * gas_gwei * 1e-9 * POL_USD

    except Exception as e:
        result["success"]       = False
        result["would_succeed"] = False
        result["revert_reason"] = parse_revert_reason(str(e))

    result["eth_call_time_ms"] = (time.time() - t0) * 1000
    return result


# ─── Pool Discovery ───────────────────────────────────────────────────────────
def discover_pools(w3):
    mc  = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qsf = w3.eth.contract(address=QS_FACTORY,  abi=QS_FACTORY_ABI)
    u3f = w3.eth.contract(address=UV3_FACTORY, abi=UV3_FACTORY_ABI)
    syms  = list(TARGET_TOKENS.keys())
    calls = []
    for sym in syms:
        t = TARGET_TOKENS[sym]["addr"]
        calls.append((QS_FACTORY, qsf.encode_abi("getPair",  args=[USDC, t])))
        calls.append((UV3_FACTORY, u3f.encode_abi("getPool",  args=[USDC, t, 500])))
    _, ret = mc.functions.aggregate(calls).call()
    ZERO   = "0x0000000000000000000000000000000000000000"
    pools  = {}
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
    return pools


def fetch_prices(w3, pools):
    """Fetch live prices for all pools via multicall."""
    mc     = w3.eth.contract(address=MULTICALL3, abi=MULTICALL_ABI)
    qsp    = w3.eth.contract(abi=QS_PAIR_ABI)
    u3p    = w3.eth.contract(abi=UV3_POOL_ABI)
    syms   = list(pools.keys())
    calls  = []
    for sym in syms:
        calls.append((pools[sym]["qs"], qsp.encode_abi("getReserves", args=[])))
        calls.append((pools[sym]["u3"], u3p.encode_abi("slot0",       args=[])))
    _, pret = mc.functions.aggregate(calls).call()

    prices = {}
    for i, sym in enumerate(syms):
        info     = pools[sym]
        tok_dec  = 10 ** info["dec"]
        tok_addr = info["tok"]
        r0,r1,_ = decode(["uint112","uint112","uint32"], pret[i*2])
        t0usdc   = int(USDC,16) < int(tok_addr,16)
        ur,tr    = (r0,r1) if t0usdc else (r1,r0)
        usdc_res = ur / 10**USDC_DECIMALS
        qs_price = usdc_res / (tr/tok_dec) if tr > 0 else 0
        s0       = decode(["uint160","int24","uint16","uint16","uint16","uint8","bool"], pret[i*2+1])
        uv3_price = decode_uv3_price(s0[0], t0usdc, tok_dec)
        prices[sym] = {
            "qs_price": qs_price, "uv3_price": uv3_price,
            "qs_usdc_reserves": usdc_res, "token0_is_usdc": t0usdc,
            "tok_dec": tok_dec, "tok_addr": tok_addr,
        }
    return prices


# ─── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  PhantomX eth_call Simulator — Standalone Test")
    print("  Gas: $0 | Live Data: YES | TX Broadcast: NO")
    print("=" * 60)

    w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        sys.exit("❌ RPC failed")

    gas_gwei = float(w3.from_wei(w3.eth.gas_price, "gwei"))
    print(f"\n✅ Connected | Gas: {gas_gwei:.1f} Gwei")

    # Load wallet + contract
    from dotenv import load_dotenv
    load_dotenv()
    from eth_account import Account
    pk = os.getenv("GHOSTHUNTER_DEV_PRIVATE_KEY")
    account = Account.from_key(pk)
    contract_addr = open("deployed_contract.txt").read().strip()
    print(f"🔑 Wallet: {account.address}")
    print(f"📄 Contract: {contract_addr}")

    brain = PhantomAIBrain()
    pools = discover_pools(w3)
    print(f"\n  Discovered {len(pools)} pools")

    print(f"\n{'─'*60}")
    print(f"  RUNNING eth_call SIMULATIONS (live data, 0 gas):")
    print(f"{'─'*60}")

    prices = fetch_prices(w3, pools)
    for sym, info in prices.items():
        qs    = info["qs_price"]
        uv3   = info["uv3_price"]
        res   = info["qs_usdc_reserves"]
        spread = abs(qs - uv3) / max(qs, 1) * 100

        decision, loan, est_profit, bribe = brain.analyze_scenario(qs, uv3, res, gas_gwei)
        start_on_qs = qs < uv3

        print(f"\n  {sym}: Spread={spread:.3f}% | AI={decision} | Est=${est_profit:.2f}")

        if decision == "EXECUTE" and loan > 0:
            sim = simulate_arb_ethcall(
                w3, contract_addr, account.address,
                info["tok_addr"], loan, start_on_qs,
                qs, uv3, info["tok_dec"], gas_gwei
            )
            status = "✅ WOULD SUCCEED" if sim["success"] else f"❌ WOULD REVERT: {sim['revert_reason']}"
            print(f"    eth_call → {status} | {sim['eth_call_time_ms']:.0f}ms")
            if sim.get("gas_estimate"):
                print(f"    Gas estimate: {sim['gas_estimate']:,} units | ${sim.get('gas_cost_usd',0):.4f}")
        else:
            # Still simulate with minimum loan to check contract health
            test_loan = res * 0.001  # 0.1% test
            if test_loan > 10:
                sim = simulate_arb_ethcall(
                    w3, contract_addr, account.address,
                    info["tok_addr"], test_loan, start_on_qs,
                    qs, uv3, info["tok_dec"], gas_gwei
                )
                status = "✅ Contract healthy" if sim["success"] else f"⚠️ Revert: {sim['revert_reason']}"
                print(f"    Contract health check → {status} | {sim['eth_call_time_ms']:.0f}ms")

    print(f"\n{'═'*60}")
    print(f"  ✅ eth_call Simulator test complete — $0 gas spent!")
    print(f"{'═'*60}\n")

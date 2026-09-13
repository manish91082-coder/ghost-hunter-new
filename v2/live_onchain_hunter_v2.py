import os
import json
import sqlite3
from web3 import Web3
import concurrent.futures
import time

db_path = r'c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter\phantomx_knowledge.db'

def get_rpc():
    try:
        with open("active_rpc.txt", "r") as f:
            return f.read().strip()
    except Exception:
        return "https://ethereum-rpc.publicnode.com"

RPC_URL = get_rpc()
w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={'timeout': 10}))

# Using Uniswap V2 Router ABI to query exact simulated output
ROUTER_ABI = json.loads('[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]')

def check_route(w3_conn, routerA, routerB, tokenIn, tokenOut, amount_in, pair_name):
    try:
        contractA = w3_conn.eth.contract(address=w3_conn.to_checksum_address(routerA), abi=ROUTER_ABI)
        contractB = w3_conn.eth.contract(address=w3_conn.to_checksum_address(routerB), abi=ROUTER_ABI)
        
        path_forward = [w3_conn.to_checksum_address(tokenIn), w3_conn.to_checksum_address(tokenOut)]
        path_backward = [w3_conn.to_checksum_address(tokenOut), w3_conn.to_checksum_address(tokenIn)]
        
        # Simulating the exact on-chain router logic via read-only RPC calls
        outA = contractA.functions.getAmountsOut(amount_in, path_forward).call()
        outB = contractB.functions.getAmountsOut(outA[-1], path_backward).call()
        
        profit = outB[-1] - amount_in
        return profit, f"{pair_name}: RouterA -> RouterB", True
    except Exception as e:
        # Reverts happen on-chain if there's no liquidity or a fee-on-transfer error
        return -1, f"{pair_name}: Reverted ({str(e)[:50]}...)", False

def live_hunting_engine_v2():
    print(f"=== PHANTOMX: ULTRA-DEEP LIVE ON-CHAIN SCAN (V2) ===")
    print(f"Connecting to Selected Premium RPC: {RPC_URL}")
    if not w3.is_connected():
        print("CRITICAL: Cannot connect to blockchain RPC.")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Selecting the highly liquid token pairs injected previously
    c.execute("""
        SELECT p1.pool_name, p1.token_a_address, p1.token_b_address, pr1.router_address, pr2.router_address
        FROM pools p1
        JOIN pools p2 ON p1.pool_name = p2.pool_name AND p1.chain_id = p2.chain_id AND p1.pool_id != p2.pool_id
        JOIN protocols pr1 ON p1.dex_protocol_id = pr1.protocol_id
        JOIN protocols pr2 ON p2.dex_protocol_id = pr2.protocol_id
        WHERE p1.chain_id = 1 AND pr1.router_address IS NOT NULL AND pr2.router_address IS NOT NULL
          AND p1.token_a_address IS NOT NULL AND p1.token_b_address IS NOT NULL
    """)
    pairs = c.fetchall()
    
    print(f"Loaded {len(pairs)} cross-DEX routes for direct on-chain querying...")
    
    # We will test multiple flash loan sizes to find an optimal entry
    loan_sizes_eth = [0.1, 1.0, 10.0, 50.0]
    
    successful = 0
    scanned = 0
    
    start_time = time.time()
    
    # We execute concurrently to demonstrate speed
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for loan_eth in loan_sizes_eth:
            amount_in = int(loan_eth * 10**18)
            print(f"\n--- Scanning with Loan Size: {loan_eth} ETH ---")
            
            futures = []
            for pair in pairs:
                pool_name, tokenA, tokenB, routerA, routerB = pair
                # Test both directions: A->B and B->A
                futures.append(executor.submit(check_route, w3, routerA, routerB, tokenA, tokenB, amount_in, pool_name))
                futures.append(executor.submit(check_route, w3, routerB, routerA, tokenA, tokenB, amount_in, pool_name))
                scanned += 2
                
            for future in concurrent.futures.as_completed(futures):
                profit, msg, is_valid = future.result()
                if is_valid:
                    if profit > 0:
                        print(f"[PROFITABLE] {msg} | Net Profit (wei): {profit}".encode('ascii', 'ignore').decode('ascii'))
                        successful += 1
                    else:
                         print(f"[UNPROFITABLE] {msg} | Loss (wei): {profit}".encode('ascii', 'ignore').decode('ascii'))
                else:
                    print(f"[WARNING] {msg}".encode('ascii', 'ignore').decode('ascii'))
                    
    end_time = time.time()
    print(f"\n=== ON-CHAIN SCAN COMPLETE ===")
    print(f"Total Routes Scanned: {scanned}")
    print(f"Total Profitable Opportunities Found: {successful}")
    print(f"Scan Duration: {end_time - start_time:.2f} seconds")

if __name__ == '__main__':
    live_hunting_engine_v2()

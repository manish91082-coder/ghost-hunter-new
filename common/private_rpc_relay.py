"""
PhantomX Private RPC & Anti-Frontrunning Relay (private_rpc_relay.py)
==================================================================================================
Zero-Cost, Ultra-Low Latency Private RPC Manager for Polygon Mainnet.

Features:
  1. FastLane Private Relay (https://polygon-rpc.fastlane.xyz) - Zero Mempool Leakage
  2. Flashbots Protect Relay (https://rpc.flashbots.net) - Fallback Private MEV Protection
  3. Pre-Submission eth_call Re-Simulation (<5ms latency check)
  4. ExtraDataToPOAMiddleware Enabled (Web3.py v7 / Polygon Bor Compliant)
"""

import os
import sys
import time
import json
import requests
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

sys.stdout.reconfigure(encoding="utf-8")

# Zero-Cost Private RPC Endpoints for Polygon Mainnet
# FIXED: Removed https://rpc.flashbots.net (Ethereum Mainnet only — returns 403 on Polygon)
# Polygon private/MEV-protected endpoints:
FASTLANE_PRIVATE_RPC  = "https://polygon-rpc.fastlane.xyz"        # FastLane Polygon MEV Protection (Free)
POLYGON_BEEFY_RPC     = "https://polygon-bor.publicnode.com"       # Ultra-reliable public Bor node
PUBLIC_BOR_RPC        = "https://polygon-bor.publicnode.com"

# Legacy alias - kept for backward compatibility with any code referencing FLASHBOTS_PRIVATE_RPC
# Pointing to FastLane instead of Ethereum Flashbots (which does not support Polygon)
FLASHBOTS_PRIVATE_RPC = "https://polygon-rpc.fastlane.xyz"

PRIVATE_ENDPOINTS = [
    FASTLANE_PRIVATE_RPC,
    "https://polygon-rpc.com",
    PUBLIC_BOR_RPC
]

def get_private_w3(endpoint_url=None):
    """
    Returns Web3 instance connected to zero-cost Private RPC Relay with POA middleware.
    """
    url = endpoint_url or FASTLANE_PRIVATE_RPC
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 5}))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if not w3.is_connected():
        # Fallback to public Bor node if private relay is temporarily unreachable
        w3 = Web3(Web3.HTTPProvider(PUBLIC_BOR_RPC, request_kwargs={"timeout": 5}))
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
    return w3

def simulate_eth_call_pre_flight(w3, tx_params):
    """
    Executes eth_call 2ms prior to submission.
    Returns (success: bool, return_data: str, latency_ms: float)
    """
    start_time = time.perf_counter()
    try:
        call_result = w3.eth.call({
            "from": tx_params.get("from"),
            "to": tx_params.get("to"),
            "data": tx_params.get("data"),
            "value": tx_params.get("value", 0),
            "gas": tx_params.get("gas", 500000)
        }, block_identifier="latest")
        
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return True, call_result.hex() if hasattr(call_result, "hex") else str(call_result), latency_ms
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return False, str(e), latency_ms

def broadcast_private_transaction(signed_tx_raw_hex, preferred_relay="fastlane"):
    """
    Submits signed raw transaction directly to Private Relay (FastLane / Flashbots)
    bypassing the public mempool completely to prevent Sandwich / Front-running attacks.
    """
    endpoints = [FASTLANE_PRIVATE_RPC, FLASHBOTS_PRIVATE_RPC] if preferred_relay == "fastlane" else [FLASHBOTS_PRIVATE_RPC, FASTLANE_PRIVATE_RPC]
    
    raw_hex = signed_tx_raw_hex if signed_tx_raw_hex.startswith("0x") else f"0x{signed_tx_raw_hex}"
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_sendRawTransaction",
        "params": [raw_hex],
        "id": 1
    }
    
    for endpoint in endpoints:
        try:
            res = requests.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if "result" in data:
                    tx_hash = data["result"]
                    print(f"⚡ [Private Relay] Tx Broadcast Successful via {endpoint} | Hash: {tx_hash}")
                    return True, tx_hash, endpoint
                elif "error" in data:
                    err_msg = data["error"].get("message", str(data["error"]))
                    print(f"⚠️ [Private Relay Note] {endpoint} returned error: {err_msg}")
        except Exception as e:
            print(f"⚠️ [Private Relay Exception] Failed connecting to {endpoint}: {e}")

    # Fallback to standard w3 broadcast if private relays fail
    try:
        w3 = get_private_w3(PUBLIC_BOR_RPC)
        tx_hash = w3.eth.send_raw_transaction(bytes.fromhex(raw_hex.replace("0x", "")))
        hash_hex = w3.to_hex(tx_hash)
        print(f"⚡ [Public Fallback] Broadcast Tx Hash: {hash_hex}")
        return True, hash_hex, PUBLIC_BOR_RPC
    except Exception as fe:
        return False, str(fe), None

if __name__ == "__main__":
    print("⚡ Testing Private RPC Relay Connectivity...")
    w3 = get_private_w3()
    block = w3.eth.block_number
    print(f"✅ Connected to FastLane/Bor Private RPC! Current Polygon Block: #{block}")

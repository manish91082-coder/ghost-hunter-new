import os
import sys
import time
import json
from web3 import Web3
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ─── Directories Setup ────────────────────────────────────────────────────────
BASE_DIR = r"c:\Users\Admin\.gemini\antigravity-ide\scratch\flash loan ghost hunter"
ENGINE_DIR = os.path.join(BASE_DIR, "v2_v3_engine")
COMMON_DIR = os.path.join(ENGINE_DIR, "common")
V2_DIR = os.path.join(ENGINE_DIR, "v2")
V3_DIR = os.path.join(ENGINE_DIR, "v3")

RPC_URL = "https://polygon-bor.publicnode.com"

evidence_results = {}

def run_phase5_verification():
    print("=" * 80)
    print(" 🎯 PHANTOMX PHASE 5: LIVE PRODUCTION DEPLOYMENT & READINESS HARNESS")
    print(" Discipline Level: Military / Surgical / Aviation Grade")
    print(" Mode: Production Readiness & Wallet/Contract Integration Audit")
    print("=" * 80)

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 5.1: 1-Click Automation Suite Paths & Integrity Verification
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 5.1] 1-Click Batch Automation Suite Integration Check ---")
    try:
        bat_v2 = os.path.join(BASE_DIR, "1_CLICK_RUN_V2_LIVE.bat")
        bat_v3 = os.path.join(BASE_DIR, "1_CLICK_RUN_V3_LIVE.bat")
        bat_dual = os.path.join(BASE_DIR, "START_DUAL_ENGINE_PARALLEL.bat")
        
        v2_exists = os.path.exists(bat_v2)
        v3_exists = os.path.exists(bat_v3)
        dual_exists = os.path.exists(bat_dual)
        
        print(f"  * 1_CLICK_RUN_V2_LIVE.bat: {'✅ ACCESSIBLE' if v2_exists else '❌ MISSING'}")
        print(f"  * 1_CLICK_RUN_V3_LIVE.bat: {'✅ ACCESSIBLE' if v3_exists else '❌ MISSING'}")
        print(f"  * START_DUAL_ENGINE_PARALLEL.bat: {'✅ ACCESSIBLE' if dual_exists else '❌ MISSING'}")
        
        assert v2_exists and v3_exists and dual_exists, "Batch launcher files verification failed"

        evidence_results["gate_5_1_batch_suite"] = {
            "status": "PASSED",
            "v2_bat_valid": bool(v2_exists),
            "v3_bat_valid": bool(v3_exists),
            "dual_bat_valid": bool(dual_exists)
        }
    except Exception as e:
        print(f"  ❌ Gate 5.1 Failed: {e}")
        evidence_results["gate_5_1_batch_suite"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 5.2: Wallet Setup & Private Key Authentication Audit
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 5.2] Wallet Private Key & Address Integrity Audit ---")
    try:
        load_dotenv(os.path.join(V2_DIR, ".env"))
        pk = os.getenv("GHOSTHUNTER_DEV_PRIVATE_KEY")
        
        wallet_addr = None
        if pk and len(pk) > 10:
            from eth_account import Account
            acc = Account.from_key(pk)
            wallet_addr = acc.address
            
        print(f"  * Private Key Loaded: {'✅ YES' if pk else '❌ NO'}")
        print(f"  * Wallet Address: {wallet_addr}")
        assert wallet_addr is not None, "Wallet authentication failed"

        evidence_results["gate_5_2_wallet_auth"] = {
            "status": "PASSED",
            "wallet_loaded": bool(wallet_addr is not None),
            "wallet_address": str(wallet_addr)
        }
    except Exception as e:
        print(f"  ❌ Gate 5.2 Failed: {e}")
        evidence_results["gate_5_2_wallet_auth"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 5.3: On-Chain Deployed Smart Contract Audit
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 5.3] On-Chain Deployed Smart Contract Verification ---")
    try:
        contract_file = os.path.join(V2_DIR, "deployed_contract.txt")
        contract_addr = None
        if os.path.exists(contract_file):
            contract_addr = open(contract_file, "r", encoding="utf-8").read().strip()
            
        w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 10}))
        bytecode_len = 0
        if w3.is_connected() and contract_addr:
            code = w3.eth.get_code(Web3.to_checksum_address(contract_addr))
            bytecode_len = len(code)
            
        print(f"  * Deployed Contract File: {contract_file}")
        print(f"  * Contract Address: {contract_addr}")
        print(f"  * Polygon Mainnet On-Chain Bytecode Size: {bytecode_len} bytes")
        assert bytecode_len > 0, "Deployed contract on-chain verification failed"

        evidence_results["gate_5_3_contract_deployed"] = {
            "status": "PASSED",
            "contract_address": str(contract_addr),
            "onchain_bytecode_bytes": bytecode_len
        }
    except Exception as e:
        print(f"  ❌ Gate 5.3 Failed: {e}")
        evidence_results["gate_5_3_contract_deployed"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 5.4: Solidity ZERO_LOSS_REVERT Protection Audit
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 5.4] Solidity Atomic ZERO_LOSS_REVERT Guard Audit ---")
    try:
        sol_file = os.path.join(BASE_DIR, "UniversalFlashExecutor.sol")
        sol_exists = os.path.exists(sol_file)
        sol_content = open(sol_file, "r", encoding="utf-8").read() if sol_exists else ""
        
        has_profit_check = "require(amountOut > amountIn" in sol_content
        has_repay_check = "require(IERC20(asset).balanceOf" in sol_content
        
        print(f"  * UniversalFlashExecutor.sol File: {'✅ ACCESSIBLE' if sol_exists else '❌ MISSING'}")
        print(f"  * Profit Revert Check (amountOut > amountIn): {'✅ ACTIVE' if has_profit_check else '❌ MISSING'}")
        print(f"  * Flash Repayment Revert Check: {'✅ ACTIVE' if has_repay_check else '❌ MISSING'}")
        assert has_profit_check and has_repay_check, "Solidity zero-loss guard audit failed"

        evidence_results["gate_5_4_solidity_guard"] = {
            "status": "PASSED",
            "zero_loss_revert_active": True,
            "flash_repayment_revert_active": True
        }
    except Exception as e:
        print(f"  ❌ Gate 5.4 Failed: {e}")
        evidence_results["gate_5_4_solidity_guard"] = {"status": f"FAILED: {e}"}

    # ──────────────────────────────────────────────────────────────────────────
    # GATE 5.5: Save Ground-Level Empirical Evidence Artifact
    # ──────────────────────────────────────────────────────────────────────────
    print("\n--- [GATE 5.5] Saving Ground-Level Empirical Evidence Artifact ---")
    evidence_path = os.path.join(ENGINE_DIR, "evidence_phase5_production.json")
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_results, f, indent=2)
    print(f"  * Saved empirical evidence manifest to [evidence_phase5_production.json](file:///{evidence_path})")

    print("\n================================================================================")
    print("PHANTOMX PHASE 5 VERIFICATION SUMMARY:")
    all_passed = True
    for gate, res in evidence_results.items():
        st = res.get("status", "UNKNOWN")
        print(f"  * {gate}: {st}")
        if "FAILED" in st:
            all_passed = False
    print("================================================================================")
    return all_passed

if __name__ == "__main__":
    success = run_phase5_verification()
    sys.exit(0 if success else 1)

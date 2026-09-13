import os
import sys
import solcx
import json
import time
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SOLC_VERSION = '0.8.20'
CONTRACT_PATH = os.path.join(os.path.dirname(__file__), 'contracts', 'src', 'PhantomXMVP.sol')

# Free/Public Zero-Cost RPCs for Polygon
PUBLIC_RPCS = [
    "https://polygon-bor.publicnode.com",
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://poly-rpc.gateway.pokt.network",
    "https://polygon.meowrpc.com"
]

def get_connected_w3():
    for rpc in PUBLIC_RPCS:
        print(f"🔄 Trying RPC: {rpc}")
        w3 = Web3(Web3.HTTPProvider(rpc))
        if w3.is_connected():
            print(f"✅ Successfully connected to: {rpc}")
            return w3
    print("❌ Failed to connect to any public RPC.")
    sys.exit(1)

def compile_contract():
    print("⚙️ Compiling PhantomXMVP.sol...")
    if not os.path.exists(CONTRACT_PATH):
        print(f"❌ Contract file not found at {CONTRACT_PATH}")
        sys.exit(1)
        
    with open(CONTRACT_PATH, 'r') as f:
        source = f.read()
    
    # solcx.install_solc(SOLC_VERSION) # Ensure solc is installed
    compiled = solcx.compile_source(
        source,
        output_values=['abi', 'bin'],
        solc_version=SOLC_VERSION
    )
    contract_id, contract_interface = compiled.popitem()
    return contract_interface['abi'], contract_interface['bin']

def main():
    print("🚀 PHANTOM-X MAINNET DEPLOYER")
    is_dry_run = "--dry-run" in sys.argv
    if is_dry_run:
        print("⚠️ RUNNING IN DRY-RUN MODE. NO ACTUAL TRANSACTIONS WILL BE SENT.")
        
    private_key = os.getenv("GHOSTHUNTER_DEV_PRIVATE_KEY")
    if not private_key:
        print("❌ Private key not found in .env")
        sys.exit(1)
        
    account = Account.from_key(private_key)
    print(f"🔑 Using Dev Vault Address: {account.address}")
    
    w3 = get_connected_w3()
    
    balance = w3.eth.get_balance(account.address)
    balance_matic = w3.from_wei(balance, 'ether')
    print(f"💰 Vault Balance: {balance_matic} MATIC")
    
    if balance_matic == 0 and not is_dry_run:
        print("❌ Zero balance! Cannot deploy contract.")
        sys.exit(1)
        
    abi, bytecode = compile_contract()
    
    PhantomContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    print("📝 Building deployment transaction...")
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Use EIP-1559 for deployment
    base_fee = w3.eth.gas_price # Approximation for base fee
    max_priority_fee = w3.to_wei(30, 'gwei') # Minimum 30 gwei on Polygon
    max_fee = base_fee + max_priority_fee
    
    construct_txn = PhantomContract.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'chainId': 137, # Polygon Mainnet
        'gas': 3000000, # Estimated gas for deployment
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': max_priority_fee,
    })
    
    print(f"⛽ Estimated Gas Limit: 3000000")
    print(f"⛽ Max Fee Per Gas: {w3.from_wei(max_fee, 'gwei')} Gwei")
    
    if is_dry_run:
        print("✅ Dry run successful. Ready to shoot!")
        sys.exit(0)
        
    print("🔐 Signing transaction...")
    signed_txn = account.sign_transaction(construct_txn)
    
    print("📤 Broadcasting deployment transaction to Polygon Mainnet...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"⏳ Transaction Hash: {tx_hash.hex()}")
    
    print("⏳ Waiting for receipt...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    print(f"🎉 Contract deployed successfully!")
    print(f"📄 Contract Address: {tx_receipt.contractAddress}")
    
    # Save the contract address to a local file for the runner to use
    with open("deployed_contract.txt", "w") as f:
        f.write(tx_receipt.contractAddress)

if __name__ == "__main__":
    main()

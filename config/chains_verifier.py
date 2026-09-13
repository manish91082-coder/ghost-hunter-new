import json
from web3 import Web3

class ChainVerifier:
    def __init__(self, config_path="chains.json"):
        with open(config_path, "r") as f:
            self.config = json.load(f)

    def verify_all(self):
        results = {}
        for chain_id, data in self.config["chains"].items():
            print(f"Verifying {data['name']} (Chain ID: {chain_id})")
            
            # Connect to first valid RPC
            w3 = None
            for rpc in data["rpc_urls"]:
                temp_w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
                if temp_w3.is_connected():
                    w3 = temp_w3
                    break
            
            if not w3:
                results[chain_id] = {"status": "FAILED", "reason": "All RPCs dead"}
                continue
                
            chain_results = {"rpc": "OK", "dexes": {}, "flash_providers": {}}
            
            for dex_name, dex_data in data["dexes"].items():
                if "router" in dex_data:
                    code = w3.eth.get_code(w3.to_checksum_address(dex_data["router"]))
                    chain_results["dexes"][f"{dex_name}_router"] = "OK" if len(code) > 0 else "MISSING"
                if "factory" in dex_data:
                    code = w3.eth.get_code(w3.to_checksum_address(dex_data["factory"]))
                    chain_results["dexes"][f"{dex_name}_factory"] = "OK" if len(code) > 0 else "MISSING"

            for fp_name, fp_addr in data["flash_loan_providers"].items():
                code = w3.eth.get_code(w3.to_checksum_address(fp_addr))
                chain_results["flash_providers"][fp_name] = "OK" if len(code) > 0 else "MISSING"
                
            results[chain_id] = chain_results
            print(json.dumps(chain_results, indent=2))
            
        return results

if __name__ == "__main__":
    verifier = ChainVerifier()
    verifier.verify_all()

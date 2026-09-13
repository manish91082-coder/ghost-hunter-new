import json
import logging
from typing import Dict, Any, List
from datetime import datetime

class KnowledgeAgent:
    """
    Agent 3: KNOWLEDGE / EVIDENCE
    Records evidence and assumptions explicitly.
    """
    
    VALID_ASSUMPTIONS = {
        "LIVE_CHAIN", "CONTRACT", "API", "CONFIG", 
        "MODEL_ASSUMPTION", "SIMULATED", "SYNTHETIC", "UNKNOWN"
    }

    def __init__(self, log_dir: str = "PFLC_5.2_Reports"):
        self.log_dir = log_dir
        self.evidence_log = []

    def record_evidence(self, opportunity_id: str, data: Dict[str, Any], assumptions: List[str]):
        """
        Records structured evidence for a specific opportunity.
        """
        for a in assumptions:
            if a not in self.VALID_ASSUMPTIONS:
                logging.warning(f"[Knowledge] Invalid assumption tag used: {a}")
                
        record = {
            "timestamp": datetime.now().isoformat(),
            "opportunity_id": opportunity_id,
            "chain_id": data.get("chain_id", "UNKNOWN"),
            "block_number": data.get("block_number", "UNKNOWN"),
            "block_hash": data.get("block_hash", "UNKNOWN"),
            "provider": data.get("rpc_provider", "UNKNOWN"),
            "contract": data.get("pool_address", "UNKNOWN"),
            "token_in": data.get("token_in", "UNKNOWN"),
            "token_out": data.get("token_out", "UNKNOWN"),
            "decimals": data.get("token_decimals", "UNKNOWN"),
            "fee": data.get("fee_tier", "UNKNOWN"),
            "source": data.get("source_type", "UNKNOWN"),
            "assumptions": assumptions
        }
        self.evidence_log.append(record)
        return record

    def dump_evidence(self, filename: str = "Evidence_Manifest.json"):
        import os
        os.makedirs(self.log_dir, exist_ok=True)
        path = os.path.join(self.log_dir, filename)
        with open(path, "w") as f:
            json.dump(self.evidence_log, f, indent=4)

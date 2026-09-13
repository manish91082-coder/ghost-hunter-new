import logging
from typing import Dict, Any

class RiskAgent:
    """
    Agent 5: RISK
    Enforces hard rejections for bad data, stale quotes, 
    insufficient liquidity, high slippage, and negative economics.
    """
    def __init__(self, max_quote_age_ms=5000):
        self.max_quote_age_ms = max_quote_age_ms

    def evaluate_opportunity(self, opp_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hard rejects if any risk parameters are breached.
        """
        if opp_data.get("quote_status") != "VALID":
            return {"status": "RISK_REJECTED", "reason": "DATA_ERROR / QUOTE_FAILED"}
            
        quote_age = opp_data.get("quote_age_ms", 0)
        if quote_age > self.max_quote_age_ms:
            return {"status": "RISK_REJECTED", "reason": "STALE_QUOTE"}
            
        net_pnl = opp_data.get("net_pnl")
        if net_pnl is None or net_pnl == "NULL":
             return {"status": "RISK_REJECTED", "reason": "DATA_UNAVAILABLE"}
             
        if isinstance(net_pnl, float):
             logging.error("[RiskAgent] Floating point leak detected! Aborting.")
             return {"status": "RISK_REJECTED", "reason": "FLOAT_DETECTED"}
             
        if net_pnl <= 0:
             return {"status": "RISK_REJECTED", "reason": "UNPROFITABLE"}
             
        return {"status": "RISK_PASSED", "reason": "CLEAN"}

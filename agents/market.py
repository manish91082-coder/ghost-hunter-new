import logging
from typing import Dict, Any, Optional

class MarketAgent:
    """
    Agent 4: MARKET
    Extracts real market state (reserves, liquidity, exact quotes, dynamic gas).
    """
    def __init__(self, rpc_manager):
        self.rpc_manager = rpc_manager

    def fetch_exact_quote(self, adapter, quoter_address: str, token_in: str, token_out: str, amount_in: int, fee: int) -> Dict[str, Any]:
        """
        Uses the provided DEX adapter to fetch an exact quote. 
        Enforces strict fail-handling (returns FAILED status if no valid quote).
        """
        try:
            state = adapter.fetch_market_state(quoter_address, token_in, token_out, amount_in, fee)
            if state.get("status") != "VALID":
                return {"status": "QUOTE_FAILED", "reason": "No route or data unavailable"}
                
            amount_out = adapter.calculate_out_given_in(state, amount_in)
            return {
                "status": "VALID",
                "amount_out": amount_out,
                "quote_block": state.get("block_number"),
                "quote_timestamp": state.get("timestamp"),
                "estimated_gas": state.get("gas_estimate", 150000)
            }
        except Exception as e:
            logging.error(f"[MarketAgent] Error fetching quote: {e}")
            return {"status": "QUOTE_FAILED", "reason": str(e)}

    def estimate_dynamic_gas(self, profit_calc, config: Dict[str, Any], to_address: str, calldata: bytes) -> Optional[int]:
        """
        Calculates exact gas, including precise L1 data fee logic for L2s, 
        using actual proposed calldata.
        """
        try:
            tx = {"to": to_address, "data": calldata}
            gas_wei = profit_calc.estimate_l2_gas(self.rpc_manager.w3, tx, config)
            return gas_wei
        except Exception as e:
            logging.error(f"[MarketAgent] Dynamic gas estimation failed: {e}")
            return None  # GAS_ESTIMATION_FAILED

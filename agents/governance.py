import logging
from typing import Dict, List, Any

class GovernanceAgent:
    """
    Agent 1: GOVERNANCE
    Enforces mission rules, allowed chains, allowed strategies, 
    test matrix, safety rules, and execution permissions.
    """
    
    ALLOWED_CHAINS = {1, 8453, 10, 42161, 137, 43114, 250, 42220}
    ALLOWED_STRATEGIES = {"Spatial", "Triangular", "Statistical", "Yield", "CrossChain", "Sandwich"}
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_capital_usd = 50000.0  # Mission limit
        self.is_mainnet_active = False  # READ_ONLY by default

    def verify_mission_parameters(self, strategy: str, chain_id: int) -> bool:
        if chain_id not in self.ALLOWED_CHAINS:
            logging.warning(f"[Governance] Chain {chain_id} is strictly prohibited.")
            return False
            
        if strategy not in self.ALLOWED_STRATEGIES:
            logging.warning(f"[Governance] Strategy {strategy} is not authorized.")
            return False
            
        return True
        
    def check_execution_permission(self) -> str:
        """Returns the current execution clearance level."""
        if self.is_mainnet_active:
            return "LIVE_EXECUTION_READY"
        return "SIMULATION_READY"
        
    def validate_trade_size(self, size_usd: float) -> bool:
        if size_usd > self.max_capital_usd:
            logging.warning(f"[Governance] Requested size ${size_usd} exceeds hard limit ${self.max_capital_usd}.")
            return False
        return True

    def validate_opportunity(self, opp_data: Dict[str, Any]) -> str:
        """Final sanity check before allowing an opportunity to be marked EXECUTABLE."""
        # Must have positive net PnL
        if not opp_data.get("is_safe", False):
            return "ABORT_UNSAFE"
        
        if opp_data.get("final_status") != "RECONCILED" and self.is_mainnet_active:
             return "ABORT_STATE_MISMATCH"
             
        return "APPROVED"

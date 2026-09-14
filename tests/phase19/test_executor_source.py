import re
import unittest
from pathlib import Path

CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "Phase19Executor.sol"

class Phase19ExecutorSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = CONTRACT.read_text(encoding="utf-8")

    def test_executor_contract_exists_and_has_expected_interfaces(self):
        self.assertIn("contract Phase19Executor", self.source); self.assertIn("flashLoanSimple", self.source); self.assertIn("executeOperation", self.source); self.assertIn("swapExactTokensForTokens", self.source); self.assertIn("exactInputSingle", self.source)

    def test_no_public_rpc_or_raw_transaction_submission_path(self):
        for token in ("eth_sendRawTransaction", "send_raw_transaction", "polygon-rpc.com", "publicnode"):
            self.assertNotIn(token, self.source)

    def test_callback_is_bound_to_configured_aave_pool_and_self_initiation(self):
        self.assertIn("if (msg.sender != aavePool) revert InvalidCaller();", self.source); self.assertIn("if (initiator != address(this)) revert InvalidInitiator();", self.source); self.assertIn("if (!activeExecution) revert NoActiveExecution();", self.source); self.assertIn("if (asset != activeAsset || amount != activeLoanAmount) revert ActiveExecutionMismatch();", self.source)

    def test_quote_route_is_cryptographically_joined_to_executable_topology(self):
        self.assertIn("bytes32 routeHash;", self.source); self.assertIn("bytes32 routeCommitment;", self.source); self.assertIn("function routeTopologyHash(", self.source); self.assertIn("function routeCommitment(", self.source)
        self.assertIn("p.routeCommitment != routeCommitment(p.routeHash, topology)", self.source)
        for value in ("aavePool", "quickSwapRouter", "uniswapV3Router"):
            self.assertIn(value, self.source)

    def test_replay_protection_is_stateful(self):
        self.assertIn("mapping(bytes32 => bool) public consumedIntent;", self.source); self.assertIn("consumedIntent[p.intentHash]", self.source); self.assertIn("consumedIntent[p.intentHash] = true;", self.source)

    def test_profit_cannot_be_subsidized_by_preexisting_balance(self):
        self.assertIn("activeBalanceBefore = IERC20Phase19(p.asset).balanceOf(address(this));", self.source); self.assertIn("uint256 balanceBefore = activeBalanceBefore;", self.source); self.assertIn("balanceAfter < balanceBefore + repayment", self.source); self.assertIn("balanceAfter < balanceBefore + repayment + p.minimumSurplus", self.source); self.assertIn("balanceAfter - balanceBefore - repayment", self.source)

    def test_exact_token_approval_is_reset(self):
        self.assertIn("approve(spender, 0)", self.source); self.assertIn("_resetApproval(tokenIn, quickSwapRouter)", self.source); self.assertIn("_resetApproval(tokenIn, uniswapV3Router)", self.source)

    def test_per_leg_minimums_and_deadline_are_enforced(self):
        self.assertIn("p.amountOutMinFirst == 0 || p.amountOutMinSecond == 0", self.source); self.assertIn("amountOut < amountOutMin", self.source); self.assertIn("p.deadline < block.timestamp", self.source); self.assertGreaterEqual(len(re.findall(r"p\.deadline < block\.timestamp", self.source)), 2)

    def test_reentrancy_guard_does_not_wrap_flashloan_entrypoint(self):
        execute_match = re.search(r"function execute\([^)]*\) external onlyOwner([^\{]*)\{", self.source); self.assertIsNotNone(execute_match); self.assertNotIn("nonReentrant", execute_match.group(1)); self.assertIsNotNone(re.search(r"function executeOperation\([^)]*\) external nonReentrant", self.source))

if __name__ == "__main__":
    unittest.main(verbosity=2)

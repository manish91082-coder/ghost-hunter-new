import unittest

from phantomx.opportunity_discovery import OpportunityDiscoveryError, discover_exact_opportunities
from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot
from phantomx.route_simulator import RouteSimulation, simulate_two_leg

A = "0x" + "aa" * 20
B = "0x" + "bb" * 20
C = "0x" + "cc" * 20


def make_simulation(token_a: str, token_b: str, amount: int, final: int, block: int = 100) -> RouteSimulation:
    first = QuoteSnapshot.from_exact_quote(
        ExactQuote("quickswap_v2", token_a, token_b, amount, amount - 1, block, 0),
        chain_id=137, observed_at_unix=1000, pool_or_router="0x" + "11" * 20,
    )
    second = QuoteSnapshot.from_exact_quote(
        ExactQuote("uniswap_v3:0x" + "22" * 20, token_b, token_a, amount - 1, final, block, 500),
        chain_id=137, observed_at_unix=1000, pool_or_router="0x" + "22" * 20,
    )
    return simulate_two_leg(first, second)


class OpportunityDiscoveryTests(unittest.TestCase):
    def test_evaluates_complete_domain_and_separates_gross_positive(self):
        result = discover_exact_opportunities(
            token_pairs=((A, B), (A, C)),
            loan_amounts=(100, 200),
            venue_path="QuickSwap→UniswapV3",
            evaluate_route=lambda a, b, amount: make_simulation(
                a, b, amount, amount + (10 if b == B else -2)
            ),
        )
        self.assertEqual(len(result.evaluated), 4)
        self.assertEqual({item.loan_amount for item in result.gross_positive}, {100, 200})
        self.assertTrue(all(item.gross_positive for item in result.gross_positive))

    def test_evaluator_failure_aborts_instead_of_returning_partial_search(self):
        calls = []

        def evaluate(a, b, amount):
            calls.append((a, b, amount))
            if amount == 200:
                raise RuntimeError("quote unavailable")
            return make_simulation(a, b, amount, amount + 1)

        with self.assertRaises(OpportunityDiscoveryError):
            discover_exact_opportunities(
                token_pairs=((A, B),), loan_amounts=(100, 200),
                venue_path="QuickSwap→UniswapV3", evaluate_route=evaluate,
            )
        self.assertEqual(calls, [(A, B, 100), (A, B, 200)])

    def test_mixed_market_blocks_are_rejected(self):
        def evaluate(a, b, amount):
            return make_simulation(a, b, amount, amount + 1, block=100 if amount == 100 else 101)

        with self.assertRaises(OpportunityDiscoveryError):
            discover_exact_opportunities(
                token_pairs=((A, B),), loan_amounts=(100, 200),
                venue_path="QuickSwap→UniswapV3", evaluate_route=evaluate,
            )

    def test_semantic_rpc_revert_is_terminal_not_retryable(self):
        from phantomx.opportunity_discovery import OpportunityFailure
        from phantomx.rpc_failover import RPCPoolError

        def evaluate(a, b, amount):
            raise RPCPoolError("eth_call: RPC error code=-32000 message=execution reverted")

        result = discover_exact_opportunities(
            token_pairs=((A, B),),
            loan_amounts=(100, 200),
            venue_path="QuickSwap→UniswapV3",
            evaluate_route=evaluate,
            continue_on_error=True,
        )
        self.assertEqual(len(result.evaluated), 0)
        self.assertEqual(len(result.failures), 2)
        self.assertEqual(len(result.retryable_failures), 0)
        self.assertEqual(len(result.terminal_failures), 2)
        self.assertTrue(all(item.error_type == "RPCPoolError" for item in result.failures))

    def test_ambiguous_revert_consensus_is_terminal(self):
        from phantomx.rpc_failover import RPCSemanticRevertConsensusError
        def evaluate(a, b, amount):
            raise RPCSemanticRevertConsensusError(
                "ambiguous execution revert consensus across distinct Polygon RPC providers: p1, p2"
            )
        result = discover_exact_opportunities(
            token_pairs=((A, B),), loan_amounts=(100,), venue_path="Curve→UniswapV3",
            evaluate_route=evaluate, continue_on_error=True,
        )
        self.assertEqual(len(result.retryable_failures), 0)
        self.assertEqual(len(result.terminal_failures), 1)
        self.assertEqual(result.terminal_failures[0].error_type, "RPCSemanticRevertConsensusError")

    def test_transport_rpc_pool_error_remains_retryable(self):
        from phantomx.rpc_failover import RPCPoolError

        def evaluate(a, b, amount):
            raise RPCPoolError("eth_call: RPC error code=429 message=rate limit")

        result = discover_exact_opportunities(
            token_pairs=((A, B),),
            loan_amounts=(100,),
            venue_path="QuickSwap→UniswapV3",
            evaluate_route=evaluate,
            continue_on_error=True,
        )
        self.assertEqual(len(result.retryable_failures), 1)
        self.assertEqual(len(result.terminal_failures), 0)

    def test_exhausted_rpc_ambiguity_remains_retryable(self):
        from phantomx.rpc_failover import RPCPoolError

        def evaluate(a, b, amount):
            raise RPCPoolError(
                "all bounded Polygon RPC recovery passes failed: "
                "round=1 p1: execution reverted | round=2 p2: execution reverted"
            )

        result = discover_exact_opportunities(
            token_pairs=((A, B),),
            loan_amounts=(100,),
            venue_path="Curve→UniswapV3",
            evaluate_route=evaluate,
            continue_on_error=True,
        )
        self.assertEqual(len(result.retryable_failures), 1)
        self.assertEqual(len(result.terminal_failures), 0)

    def test_duplicate_amounts_and_identity_errors_fail_closed(self):
        with self.assertRaises(OpportunityDiscoveryError):
            discover_exact_opportunities(
                token_pairs=((A, A),), loan_amounts=(100,),
                venue_path="QuickSwap→UniswapV3", evaluate_route=lambda a, b, x: make_simulation(a, b, x, x + 1),
            )
        with self.assertRaises(OpportunityDiscoveryError):
            discover_exact_opportunities(
                token_pairs=((A, B),), loan_amounts=(100, 100),
                venue_path="QuickSwap→UniswapV3", evaluate_route=lambda a, b, x: make_simulation(a, b, x, x + 1),
            )


if __name__ == "__main__":
    unittest.main()

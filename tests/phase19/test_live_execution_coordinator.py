"""Focused tests for the live discovery-to-signing bridge.

These tests exercise the orchestration boundary without creating or submitting
any live transaction. The concrete discovery/economics/coordinator components
remain covered by their own test suites.
"""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from phantomx.cross_venue_discovery import (
    QUICKSWAP_TO_UNISWAP_PATH,
    UNISWAP_TO_QUICKSWAP_PATH,
)
from phantomx.execution_coordinator import ExecutionCoordinatorError
from phantomx.live_execution_coordinator import (
    LiveExecutionCoordinatorError,
    discover_and_prepare_signed_execution,
)


class LiveExecutionCoordinatorBridgeTests(unittest.TestCase):
    def _inputs(self):
        return {
            "rpc": object(),
            "quickswap": object(),
            "uniswap": object(),
            "token_pairs": (("A", "B"),),
            "loan_amounts": (1000, 2000),
            "uniswap_fee": 500,
            "build_proof_for": Mock(name="build_proof_for"),
            "store": object(),
            "executor": "executor",
            "sender": "sender",
            "executor_authority": object(),
            "authority_evidence_reuse_policy": object(),
            "chain_pending_nonce": 7,
            "deadline": 2000,
            "amount_out_min_first": 1090,
            "amount_out_min_second": 1110,
            "minimum_surplus": 1,
            "aave_pool": "aave",
            "quickswap_router": "quick",
            "uniswap_v3_router": "uni",
            "gas_limit": 500000,
            "max_fee_per_gas": 100,
            "max_priority_fee_per_gas": 10,
            "policy": object(),
            "signer": object(),
            "now": 1500,
            "current_block_number": 123,
            "ai_rank": "rank",
            "reservation_id": "reservation-7",
            "quickswap_gas_estimate": 120000,
            "uniswap_gas_estimate": 140000,
            "block": 123,
        }

    @staticmethod
    def _discovery(path):
        simulation = SimpleNamespace(route_hash="0xroute")
        candidate = SimpleNamespace(venue_path=path, simulation=simulation)
        evaluation = SimpleNamespace(candidate=candidate, proof="economic-proof")
        return SimpleNamespace(evaluated=(evaluation,))

    def test_quickswap_first_path_is_forwarded_to_durable_coordinator(self):
        inputs = self._inputs()
        economics = SimpleNamespace(best=SimpleNamespace(
            candidate=SimpleNamespace(
                venue_path=QUICKSWAP_TO_UNISWAP_PATH,
                simulation="simulation",
            ),
            proof="proof",
        ))
        prepared = object()

        with patch("phantomx.live_execution_coordinator.discover_cross_venue_opportunities") as discover, \
             patch("phantomx.live_execution_coordinator.evaluate_discovered_opportunities", return_value=economics) as evaluate, \
             patch("phantomx.live_execution_coordinator.prepare_signed_execution", return_value=prepared) as prepare:
            discovery = self._discovery(QUICKSWAP_TO_UNISWAP_PATH)
            discover.return_value = discovery

            result = discover_and_prepare_signed_execution(**inputs)

        self.assertEqual(result, (discovery, economics, prepared))
        evaluate.assert_called_once_with(discovery.evaluated, inputs["build_proof_for"])
        self.assertTrue(prepare.call_args.kwargs["first_on_quickswap"])
        self.assertIs(prepare.call_args.kwargs["simulation"], economics.best.candidate.simulation)
        self.assertEqual(prepare.call_args.kwargs["economic_proof"], "proof")
        self.assertEqual(prepare.call_args.kwargs["chain_pending_nonce"], 7)
        self.assertEqual(prepare.call_args.kwargs["reservation_id"], "reservation-7")

        discover.assert_called_once_with(
            inputs["rpc"],
            inputs["quickswap"],
            inputs["uniswap"],
            token_pairs=inputs["token_pairs"],
            loan_amounts=inputs["loan_amounts"],
            uniswap_fee=500,
            quickswap_gas_estimate=120000,
            uniswap_gas_estimate=140000,
            block=123,
        )

    def test_uniswap_first_path_is_mapped_to_false(self):
        inputs = self._inputs()
        economics = SimpleNamespace(best=SimpleNamespace(
            candidate=SimpleNamespace(venue_path=UNISWAP_TO_QUICKSWAP_PATH, simulation="simulation"),
            proof="proof",
        ))
        with patch("phantomx.live_execution_coordinator.discover_cross_venue_opportunities", return_value=self._discovery(UNISWAP_TO_QUICKSWAP_PATH)), \
             patch("phantomx.live_execution_coordinator.evaluate_discovered_opportunities", return_value=economics), \
             patch("phantomx.live_execution_coordinator.prepare_signed_execution", return_value="prepared") as prepare:
            result = discover_and_prepare_signed_execution(**inputs)

        self.assertEqual(result[2], "prepared")
        self.assertFalse(prepare.call_args.kwargs["first_on_quickswap"])

    def test_unknown_venue_path_fails_closed_before_signing_bridge(self):
        inputs = self._inputs()
        economics = SimpleNamespace(best=SimpleNamespace(
            candidate=SimpleNamespace(venue_path="UNKNOWN", simulation="simulation"),
            proof="proof",
        ))
        with patch("phantomx.live_execution_coordinator.discover_cross_venue_opportunities", return_value=self._discovery("UNKNOWN")), \
             patch("phantomx.live_execution_coordinator.evaluate_discovered_opportunities", return_value=economics), \
             patch("phantomx.live_execution_coordinator.prepare_signed_execution") as prepare:
            with self.assertRaisesRegex(LiveExecutionCoordinatorError, "unsupported discovered venue path"):
                discover_and_prepare_signed_execution(**inputs)

        prepare.assert_not_called()

    def test_execution_coordinator_error_is_not_hidden(self):
        inputs = self._inputs()
        economics = SimpleNamespace(best=SimpleNamespace(
            candidate=SimpleNamespace(venue_path=QUICKSWAP_TO_UNISWAP_PATH, simulation="simulation"),
            proof="proof",
        ))
        failure = ExecutionCoordinatorError("governor rejected")
        with patch("phantomx.live_execution_coordinator.discover_cross_venue_opportunities", return_value=self._discovery(QUICKSWAP_TO_UNISWAP_PATH)), \
             patch("phantomx.live_execution_coordinator.evaluate_discovered_opportunities", return_value=economics), \
             patch("phantomx.live_execution_coordinator.prepare_signed_execution", side_effect=failure):
            with self.assertRaises(ExecutionCoordinatorError) as raised:
                discover_and_prepare_signed_execution(**inputs)

        self.assertIs(raised.exception, failure)

    def test_unexpected_error_is_wrapped_without_leaking_details(self):
        inputs = self._inputs()
        failure = RuntimeError("secret internal detail")
        with patch("phantomx.live_execution_coordinator.discover_cross_venue_opportunities", side_effect=failure):
            with self.assertRaisesRegex(LiveExecutionCoordinatorError, "live execution coordination failed") as raised:
                discover_and_prepare_signed_execution(**inputs)

        self.assertIs(raised.exception.__cause__, failure)
        self.assertNotIn("secret internal detail", str(raised.exception))


if __name__ == "__main__":
    unittest.main()

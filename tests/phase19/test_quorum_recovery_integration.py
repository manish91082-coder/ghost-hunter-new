import ast
import unittest
from pathlib import Path

from phantomx.chain_observer import ChainObservationState, ObservationDecision
from phantomx.execution import ExecutionState
from phantomx.execution_observation import persist_quorum_chain_observation
from phantomx.execution_submission import ExecutionSubmissionError, submit_prepared_execution
from phantomx.production_chain_observation import QuorumChainObservation
from phantomx.production_chain_observation_store import (
    ProductionChainObservationStoreError,
    persist_quorum_chain_observation as persist_quorum_evidence,
)

from tests.phase19.test_execution_submission import ExecutionSubmissionTests, FakeRelay

BLOCK_HASH = "0x" + "44" * 32


class QuorumRecoveryIntegrationTests(unittest.TestCase):
    def test_production_plain_observation_entry_is_confined_to_quorum_gate(self):
        root = Path(__file__).resolve().parents[2] / "phantomx"
        offenders = []
        for path in sorted(root.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Name) and func.id == "persist_chain_observation":
                    offenders.append(path.name)
                elif isinstance(func, ast.Attribute) and func.attr == "persist_chain_observation":
                    offenders.append(path.name)
        self.assertEqual(offenders, ["execution_observation.py"])

    def test_single_provider_cannot_reach_durable_settlement_observation(self):
        fixture = ExecutionSubmissionTests()
        fixture.setUp()
        try:
            prepared = fixture._prepare()
            intent = prepared.assembly.intent
            tx_hash = prepared.signed_transaction.transaction_hash

            with self.assertRaisesRegex(ExecutionSubmissionError, "outcome is uncertain"):
                submit_prepared_execution(
                    store=fixture.store,
                    prepared=prepared,
                    relay=FakeRelay(fail=True),
                    now=fixture.now,
                    submission_authority=prepared.authority,
                )

            record_hash = prepared.transaction_record.record_hash()
            self.assertEqual(
                fixture.store.get_transaction(record_hash).state,
                ExecutionState.SUBMISSION_IN_FLIGHT,
            )

            single_provider = QuorumChainObservation(
                schema_version=1,
                chain_id=137,
                tx_hash=tx_hash,
                decision=ObservationDecision(
                    ChainObservationState.INCLUDED,
                    tx_hash,
                    None,
                    "single-provider included evidence",
                ),
                common_observed_block=100,
                attesting_provider_names=("provider-a",),
            )
            persist_quorum_evidence(
                store=fixture.store,
                intent_hash=intent.intent_hash(),
                observation=single_provider,
            )

            with self.assertRaises(ProductionChainObservationStoreError):
                persist_quorum_chain_observation(
                    store=fixture.store,
                    intent=intent,
                    quorum_observation=single_provider,
                    observation=ObservationDecision(
                        ChainObservationState.INCLUDED,
                        tx_hash,
                        None,
                        "canonical receipt observed",
                    ),
                    tx_nonce=intent.nonce,
                    current_observed_block=105,
                    maximum_age_blocks=5,
                    minimum_attesting_providers=2,
                    block_hash=BLOCK_HASH,
                    block_number=100,
                    canonical_block_hash=BLOCK_HASH,
                )

            self.assertEqual(
                fixture.store.get_transaction(record_hash).state,
                ExecutionState.SUBMISSION_IN_FLIGHT,
            )
            with fixture.store._connect() as db:
                observation_count = db.execute("SELECT COUNT(*) FROM chain_observations").fetchone()[0]
            self.assertEqual(observation_count, 0)
        finally:
            fixture.tearDown()


if __name__ == "__main__":
    unittest.main(verbosity=2)

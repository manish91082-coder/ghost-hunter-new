import unittest
from dataclasses import replace

import rlp

from phantomx.execution import Authorization, ExecutionIntent, TransactionEnvelope
from phantomx.executor_authority import ExecutorAuthorityEvidence, runtime_code_binding_hash
from phantomx.governor import GovernorDecision
from phantomx.hashing import keccak256_hex
from phantomx.production_authority_evidence import AuthorityEvidenceReusePolicy
from phantomx.signer import EthereumEip1559Signer, SignerError, recover_eip1559_sender, sign_governed_transaction, prove_signer_identity

TOKEN = "0x" + "aa" * 20
EXECUTOR = "0x" + "bb" * 20
ROUTE = "0x" + "11" * 32
ECONOMIC = "0x" + "22" * 32
SIMULATION = "0x" + "33" * 32
CALldata = b"phase19-calldata"
PRIVATE_KEY = "0x" + "01" * 32
RUNTIME_CODE_HASH = "0x" + "55" * 32

class BlindForeignSigner:
    def __init__(self, private_key):
        self._signer = EthereumEip1559Signer(private_key)
    def sign(self, envelope):
        return self._signer.sign(envelope)

class BlindChallengeSigner:
    def __init__(self, private_key):
        self._signer = EthereumEip1559Signer(private_key)
    def sign_challenge(self, challenge_hash):
        return self._signer.sign_challenge(challenge_hash)

class SignerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_700_000_000
        self.signer = EthereumEip1559Signer(PRIVATE_KEY)
        self.sender = self.signer.address
        self.authority = ExecutorAuthorityEvidence(schema_version=1, chain_id=137, executor=EXECUTOR, owner=self.sender, observed_block=5000, runtime_code_hash=RUNTIME_CODE_HASH)
        self.intent = ExecutionIntent(chain_id=137, executor=EXECUTOR, sender=self.sender, loan_asset=TOKEN, loan_amount=100, route_hash=ROUTE, calldata_hash=keccak256_hex(CALldata), economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION, nonce=7, deadline=self.now + 60)
        self.envelope = TransactionEnvelope(chain_id=137, sender=self.sender, executor=EXECUTOR, nonce=7, calldata=CALldata, gas_limit=300_000, max_fee_per_gas=100, max_priority_fee_per_gas=30)
        self.authorization = Authorization(intent_hash=self.intent.intent_hash(), calldata_hash=self.intent.calldata_hash, economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION, chain_id=137, executor=EXECUTOR, sender=self.sender, nonce=7, deadline=self.intent.deadline, gas_limit=300_000, max_fee_per_gas=100, max_priority_fee_per_gas=30)
        self.governor = GovernorDecision(approved=True, reason="all governor policy gates passed", chain_id=137, block_number=5000, intent_hash=self.intent.intent_hash(), route_hash=ROUTE, economic_proof_hash=ECONOMIC, simulation_proof_hash=SIMULATION, calldata_hash=self.envelope.calldata_hash, executor_authority_hash=self.authority.evidence_hash, ai_rank="0.9")

    def sign(self, **overrides):
        values = {"signer": self.signer, "governor": self.governor, "intent": self.intent, "authorization": self.authorization, "envelope": self.envelope, "executor_authority": self.authority, "now": self.now}
        values.update(overrides)
        return sign_governed_transaction(**values)

    def test_exact_governed_eip1559_transaction_signs_and_recovers(self):
        result = self.sign()
        self.assertEqual(result.transaction_hash, keccak256_hex(result.raw_transaction))
        self.assertEqual(result.intent_hash, self.intent.intent_hash())
        self.assertEqual(result.raw_transaction[:1], b"\x02")
        self.assertEqual(recover_eip1559_sender(result.raw_transaction), self.sender)
        self.assertEqual(result.executor_runtime_binding_hash, runtime_code_binding_hash(self.authority))

    def test_signed_artifact_exactly_matches_governed_envelope(self):
        result = self.sign()
        fields = rlp.decode(result.raw_transaction[1:], strict=True)
        self.assertEqual(len(fields), 12)
        chain_id, nonce, max_priority, max_fee, gas_limit, to, value, data, access_list, _, _, _ = fields
        self.assertEqual(int.from_bytes(chain_id, "big"), self.envelope.chain_id)
        self.assertEqual(int.from_bytes(nonce, "big"), self.envelope.nonce)
        self.assertEqual(int.from_bytes(max_priority, "big"), self.envelope.max_priority_fee_per_gas)
        self.assertEqual(int.from_bytes(max_fee, "big"), self.envelope.max_fee_per_gas)
        self.assertEqual(int.from_bytes(gas_limit, "big"), self.envelope.gas_limit)
        self.assertEqual(to, bytes.fromhex(self.envelope.executor[2:]))
        self.assertEqual(value, b"")
        self.assertEqual(data, self.envelope.calldata)
        self.assertEqual(access_list, [])
        self.assertEqual(result.transaction_hash, keccak256_hex(result.raw_transaction))

    def test_signer_private_key_identity_is_explicit(self):
        self.assertEqual(len(self.signer.address), 42)
        self.assertEqual(self.signer.address, recover_eip1559_sender(self.signer.sign(self.envelope)))

    def test_signer_identity_challenge_proves_key_control_without_key_disclosure(self):
        challenge = b"P" * 32
        evidence = prove_signer_identity(signer=self.signer, expected_address=self.sender, challenge=challenge)
        self.assertEqual(evidence.challenge_hash, keccak256_hex(challenge))
        self.assertEqual(evidence.recovered_address, self.sender)
        self.assertEqual(evidence.expected_address, self.sender)
        self.assertEqual(len(evidence.signature), 65)
        self.assertEqual(evidence.evidence_hash, keccak256_hex((evidence.challenge_hash + self.sender).encode("ascii")))

    def test_blind_challenge_signer_is_independently_verified_by_recovery(self):
        challenge = b"Q" * 32
        blind = BlindChallengeSigner(PRIVATE_KEY)
        evidence = prove_signer_identity(signer=blind, expected_address=self.sender, challenge=challenge)
        self.assertEqual(evidence.recovered_address, self.sender)

    def test_wrong_challenge_signer_is_blocked(self):
        wrong = BlindChallengeSigner("0x" + "02" * 32)
        with self.assertRaisesRegex(SignerError, "challenge identity"):
            prove_signer_identity(signer=wrong, expected_address=self.sender, challenge=b"R" * 32)

    def test_zero_private_key_is_rejected(self):
        with self.assertRaisesRegex(SignerError, "private_key"):
            EthereumEip1559Signer("0x" + "00" * 32)

    def test_wrong_signer_identity_is_blocked_before_signing(self):
        wrong = EthereumEip1559Signer("0x" + "02" * 32)
        with self.assertRaisesRegex(SignerError, "signer identity"):
            self.sign(signer=wrong)

    def test_recovered_sender_mismatch_is_blocked(self):
        foreign = BlindForeignSigner("0x" + "02" * 32)
        with self.assertRaisesRegex(SignerError, "recovered transaction sender"):
            self.sign(signer=foreign)

    def test_authority_identity_mismatch_is_blocked(self):
        foreign = replace(self.authority, owner="0x" + "22" * 20, evidence_hash="")
        with self.assertRaisesRegex(SignerError, "governor executor authority evidence"):
            self.sign(executor_authority=foreign)

    def test_authority_runtime_code_mutation_is_blocked(self):
        mutated = replace(self.authority, runtime_code_hash="0x" + "66" * 32, evidence_hash="")
        with self.assertRaisesRegex(SignerError, "governor executor authority evidence"):
            self.sign(executor_authority=mutated)

    def test_stale_authority_observation_is_blocked(self):
        stale = replace(self.authority, observed_block=4999, evidence_hash="")
        governor = replace(self.governor, executor_authority_hash=stale.evidence_hash, decision_hash="")
        with self.assertRaisesRegex(SignerError, "freshness or identity"):
            self.sign(executor_authority=stale, governor=governor)

    def test_replayed_authority_observation_is_blocked_at_signer_boundary(self):
        replayed = replace(self.authority, observed_block=4997, evidence_hash="")
        governor = replace(self.governor, executor_authority_hash=replayed.evidence_hash, decision_hash="")
        with self.assertRaisesRegex(SignerError, "freshness or identity"):
            self.sign(
                executor_authority=replayed,
                governor=governor,
                authority_evidence_reuse_policy=AuthorityEvidenceReusePolicy(maximum_age_blocks=2),
            )

    def test_future_authority_observation_is_blocked_at_signer_boundary(self):
        future = replace(self.authority, observed_block=5001, evidence_hash="")
        governor = replace(self.governor, executor_authority_hash=future.evidence_hash, decision_hash="")
        with self.assertRaisesRegex(SignerError, "freshness or identity"):
            self.sign(executor_authority=future, governor=governor)

    def test_governor_authority_hash_mismatch_is_blocked(self):
        blocked = replace(self.governor, executor_authority_hash="0x" + "77" * 32, decision_hash="")
        with self.assertRaisesRegex(SignerError, "governor executor authority evidence"):
            self.sign(governor=blocked)

    def test_governor_block_prevents_signer_call(self):
        blocked = replace(self.governor, approved=False, reason="locked", decision_hash="")
        with self.assertRaises(SignerError):
            self.sign(governor=blocked)

    def test_mutations_are_blocked_before_signing(self):
        mutations = [{"intent": replace(self.intent, route_hash="0x" + "44" * 32)}, {"intent": replace(self.intent, economic_proof_hash="0x" + "55" * 32)}, {"intent": replace(self.intent, simulation_proof_hash="0x" + "66" * 32)}, {"envelope": replace(self.envelope, calldata=b"mutated")}, {"envelope": replace(self.envelope, nonce=8)}]
        for mutation in mutations:
            with self.assertRaises(SignerError):
                self.sign(**mutation)

    def test_authorization_mutation_is_blocked(self):
        mutated = replace(self.authorization, gas_limit=300_001)
        with self.assertRaises(SignerError):
            self.sign(authorization=mutated)

    def test_expired_deadline_is_blocked(self):
        with self.assertRaises(SignerError):
            self.sign(now=self.intent.deadline + 1)

    def test_invalid_signer_output_is_blocked(self):
        class BadSigner:
            address = self.sender
            def sign(self, envelope):
                return b""
        with self.assertRaises(SignerError):
            self.sign(signer=BadSigner())

if __name__ == "__main__":
    unittest.main(verbosity=2)
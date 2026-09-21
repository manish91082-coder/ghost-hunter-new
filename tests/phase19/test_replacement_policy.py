"""Adversarial tests for bounded replacement fee authorization."""

import unittest

from phantomx.replacement_policy import ReplacementAuthorization, ReplacementFeePolicy, ReplacementPolicyError


class ReplacementPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = ReplacementFeePolicy(min_bump_bps=11000, max_fee_multiplier_bps=12500, max_absolute_fee_per_gas=150, max_priority_fee_per_gas=50)

    def auth(self, **changes):
        values = dict(original_tx_hash="0x" + "11" * 32, replacement_tx_hash="0x" + "22" * 32, intent_hash="0x" + "33" * 32, authorization_hash="0x" + "44" * 32, nonce=42, old_max_fee_per_gas=100, old_max_priority_fee_per_gas=20, new_max_fee_per_gas=115, new_max_priority_fee_per_gas=23, policy_hash=self.policy.policy_hash())
        values.update(changes)
        return ReplacementAuthorization(**values)

    def test_valid_bounded_replacement(self):
        self.auth().validate(policy=self.policy)

    def test_minimum_bump_is_required(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_fee_per_gas=109, new_max_priority_fee_per_gas=22).validate(policy=self.policy)

    def test_relative_max_fee_ceiling_is_enforced(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_fee_per_gas=126, new_max_priority_fee_per_gas=23).validate(policy=self.policy)

    def test_absolute_max_fee_ceiling_is_enforced(self):
        policy = ReplacementFeePolicy(min_bump_bps=11000, max_fee_multiplier_bps=20000, max_absolute_fee_per_gas=120, max_priority_fee_per_gas=50)
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_fee_per_gas=121, new_max_priority_fee_per_gas=23).validate(policy=policy)

    def test_priority_fee_must_bump_and_stay_below_cap(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_priority_fee_per_gas=21).validate(policy=self.policy)
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_priority_fee_per_gas=51).validate(policy=self.policy)

    def test_max_fee_must_cover_priority_fee(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(new_max_fee_per_gas=22, new_max_priority_fee_per_gas=23).validate(policy=self.policy)

    def test_original_envelope_must_be_valid(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(old_max_fee_per_gas=0).validate(policy=self.policy)
        with self.assertRaises(ReplacementPolicyError):
            self.auth(old_max_fee_per_gas=20, old_max_priority_fee_per_gas=21).validate(policy=self.policy)

    def test_replacement_must_have_distinct_hash(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(replacement_tx_hash="0x" + "11" * 32).validate(policy=self.policy)

    def test_authorization_must_bind_all_identities(self):
        with self.assertRaises(ReplacementPolicyError):
            self.auth(intent_hash="").validate(policy=self.policy)
        with self.assertRaises(ReplacementPolicyError):
            self.auth(authorization_hash="").validate(policy=self.policy)
        with self.assertRaises(ReplacementPolicyError):
            self.auth(policy_hash="").validate(policy=self.policy)

    def test_policy_hash_changes_when_policy_changes(self):
        changed = ReplacementFeePolicy(min_bump_bps=11100, max_fee_multiplier_bps=12500, max_absolute_fee_per_gas=150, max_priority_fee_per_gas=50)
        self.assertNotEqual(self.policy.policy_hash(), changed.policy_hash())

    def test_policy_configuration_rejects_unsafe_bounds(self):
        with self.assertRaises(ValueError):
            ReplacementFeePolicy(min_bump_bps=13000, max_fee_multiplier_bps=12500, max_absolute_fee_per_gas=150)
        with self.assertRaises(ValueError):
            ReplacementFeePolicy(max_absolute_fee_per_gas=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

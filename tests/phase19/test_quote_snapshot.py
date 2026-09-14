import unittest

from phantomx.quote_engine import ExactQuote
from phantomx.quote_snapshot import QuoteSnapshot, QuoteSnapshotError


class QuoteSnapshotTests(unittest.TestCase):
    def make_quote(self):
        return ExactQuote(
            venue="quickswap_v2",
            token_in="0x" + "aa" * 20,
            token_out="0x" + "bb" * 20,
            amount_in=1_000_000,
            amount_out=997_000,
            block_number=12345,
            fee_raw=0,
        )

    def test_from_exact_quote_creates_hash_bound_snapshot(self):
        snapshot = QuoteSnapshot.from_exact_quote(
            self.make_quote(),
            chain_id=137,
            observed_at_unix=1_757_000_000,
            pool_or_router="0x" + "11" * 20,
            gas_estimate=180_000,
        )
        self.assertTrue(snapshot.quote_hash.startswith("0x"))
        self.assertEqual(len(snapshot.quote_hash), 66)
        self.assertEqual(snapshot.compute_hash(), snapshot.quote_hash)

    def test_same_evidence_has_same_hash(self):
        kwargs = dict(
            chain_id=137,
            observed_at_unix=1_757_000_000,
            pool_or_router="0x" + "11" * 20,
        )
        first = QuoteSnapshot.from_exact_quote(self.make_quote(), **kwargs)
        second = QuoteSnapshot.from_exact_quote(self.make_quote(), **kwargs)
        self.assertEqual(first.quote_hash, second.quote_hash)

    def test_timestamp_is_part_of_hash(self):
        quote = self.make_quote()
        first = QuoteSnapshot.from_exact_quote(
            quote, chain_id=137, observed_at_unix=100, pool_or_router="0x" + "11" * 20
        )
        second = QuoteSnapshot.from_exact_quote(
            quote, chain_id=137, observed_at_unix=101, pool_or_router="0x" + "11" * 20
        )
        self.assertNotEqual(first.quote_hash, second.quote_hash)

    def test_hash_tampering_is_rejected(self):
        quote = self.make_quote()
        valid = QuoteSnapshot.from_exact_quote(
            quote, chain_id=137, observed_at_unix=100, pool_or_router="0x" + "11" * 20
        )
        with self.assertRaises(QuoteSnapshotError):
            QuoteSnapshot(
                schema_version=valid.schema_version,
                chain_id=valid.chain_id,
                block_number=valid.block_number,
                observed_at_unix=valid.observed_at_unix,
                dex=valid.dex,
                pool_or_router=valid.pool_or_router,
                token_in=valid.token_in,
                token_out=valid.token_out,
                amount_in=valid.amount_in + 1,
                amount_out=valid.amount_out,
                fee_raw=valid.fee_raw,
                gas_estimate=valid.gas_estimate,
                quote_hash=valid.quote_hash,
            )

    def test_zero_output_rejected(self):
        with self.assertRaises(QuoteSnapshotError):
            QuoteSnapshot.from_exact_quote(
                ExactQuote("x", "a", "b", 1, 0, 1),
                chain_id=137,
                observed_at_unix=1,
                pool_or_router="router",
            )

    def test_non_positive_gas_rejected(self):
        with self.assertRaises(QuoteSnapshotError):
            QuoteSnapshot.from_exact_quote(
                self.make_quote(),
                chain_id=137,
                observed_at_unix=1,
                pool_or_router="router",
                gas_estimate=0,
            )


if __name__ == "__main__":
    unittest.main()

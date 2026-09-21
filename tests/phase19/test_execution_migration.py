import tempfile
import unittest
from pathlib import Path
import sqlite3

from phantomx.execution_migration import (
    MigrationConflict,
    build_migration_manifest,
    inspect_legacy_journal,
    inspect_legacy_nonce_store,
    inspect_legacy_transaction_store,
)


class ExecutionMigrationTests(unittest.TestCase):
    def _db(self):
        tmp = tempfile.TemporaryDirectory()
        path = Path(tmp.name) / "legacy.sqlite3"
        return tmp, path

    def _nonce_schema(self, db):
        db.executescript("""
        CREATE TABLE nonce_records(sender TEXT, nonce INTEGER, reservation_id TEXT, intent_hash TEXT, status TEXT, tx_hash TEXT, replacement_of TEXT);
        """)

    def test_nonce_reader_is_read_only(self):
        tmp, path = self._db()
        try:
            with sqlite3.connect(path) as db:
                self._nonce_schema(db)
                db.execute("INSERT INTO nonce_records VALUES(?,?,?,?,?,?,?)", ("0x1", 3, "r3", "ih", "RESERVED", None, None))
            items = inspect_legacy_nonce_store(str(path))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].identity, "0x1:3")
        finally:
            tmp.cleanup()

    def test_matching_nonce_and_transaction_build_manifest(self):
        tmp, path = self._db()
        try:
            with sqlite3.connect(path) as db:
                self._nonce_schema(db)
                db.execute("INSERT INTO nonce_records VALUES(?,?,?,?,?,?,?)", ("0xsender", 3, "r3", "intent", "SIGNED", "0x" + "11" * 32, None))
            tx_path = Path(tmp.name) / "tx.sqlite3"
            with sqlite3.connect(tx_path) as db:
                db.execute("CREATE TABLE transaction_records(record_hash TEXT,intent_hash TEXT,authorization_hash TEXT,reservation_id TEXT,chain_id INTEGER,sender TEXT,executor TEXT,nonce INTEGER,calldata_hash TEXT,gas_limit INTEGER,max_fee_per_gas INTEGER,max_priority_fee_per_gas INTEGER,tx_hash TEXT,state TEXT,replacement_of TEXT)")
                db.execute("INSERT INTO transaction_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rh", "intent", "auth", "r3", 137, "0xsender", "0xexec", 3, "calldata", 1, 2, 1, "0x" + "11" * 32, "SIGNED", None))
            journal_path = Path(tmp.name) / "journal.sqlite3"
            with sqlite3.connect(journal_path) as db:
                db.execute("CREATE TABLE recovery_journal(sequence INTEGER,record_hash TEXT,action TEXT,chain_state TEXT,tx_hash TEXT,replacement_tx_hash TEXT,reason TEXT,applied INTEGER)")
            manifest = build_migration_manifest(inspect_legacy_nonce_store(str(path)), inspect_legacy_transaction_store(str(tx_path)), inspect_legacy_journal(str(journal_path)))
            self.assertEqual(len(manifest), 2)
        finally:
            tmp.cleanup()

    def test_missing_nonce_conflicts(self):
        tmp, path = self._db()
        try:
            with sqlite3.connect(path) as db: self._nonce_schema(db)
            tx_path = Path(tmp.name) / "tx.sqlite3"
            with sqlite3.connect(tx_path) as db:
                db.execute("CREATE TABLE transaction_records(record_hash TEXT,intent_hash TEXT,authorization_hash TEXT,reservation_id TEXT,chain_id INTEGER,sender TEXT,executor TEXT,nonce INTEGER,calldata_hash TEXT,gas_limit INTEGER,max_fee_per_gas INTEGER,max_priority_fee_per_gas INTEGER,tx_hash TEXT,state TEXT,replacement_of TEXT)")
                db.execute("INSERT INTO transaction_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ("rh", "intent", "auth", "r3", 137, "0xsender", "0xexec", 3, "calldata", 1, 2, 1, "0x" + "11" * 32, "SIGNED", None))
            with self.assertRaises(MigrationConflict):
                build_migration_manifest(inspect_legacy_nonce_store(str(path)), inspect_legacy_transaction_store(str(tx_path)), tuple())
        finally:
            tmp.cleanup()


if __name__ == "__main__": unittest.main(verbosity=2)

"""Run the dependency-free Phase-19 adversarial policy suite.

Usage from repository root:
    python -m unittest discover -s tests/phase19 -v

This runner intentionally does not contact Polygon, sign transactions, or
broadcast anything. Network/fork tests are separate P1/P0 gates later in the
implementation sequence.
"""

from __future__ import annotations

import unittest


def main() -> int:
    suite = unittest.defaultTestLoader.discover("tests/phase19", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

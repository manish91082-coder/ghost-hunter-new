import importlib.util
from pathlib import Path
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "PHANTOMX_COLAB_BRIDGE.py"


def load_bridge():
    module_name = "phantomx_colab_bridge_test_target"
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ColabArgvSanitizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bridge = load_bridge()
        cls.bridge._running_in_ipython = lambda: True

    def test_colab_kernel_pair_is_removed(self):
        raw = [
            "-f",
            "/root/.local/share/jupyter/runtime/kernel-1234.json",
        ]
        self.assertEqual(self.bridge._cli_argv(raw), [])

    def test_kernel_pair_does_not_consume_real_command(self):
        raw = [
            "-f",
            "/root/.local/share/jupyter/runtime/kernel-1234.json",
            "terminal",
        ]
        self.assertEqual(self.bridge._cli_argv(raw), ["terminal"])

    def test_auto_s5_survives_kernel_bootstrap(self):
        raw = [
            "-f",
            "/root/.local/share/jupyter/runtime/kernel-1234.json",
            "auto",
            "--s5",
        ]
        self.assertEqual(self.bridge._cli_argv(raw), ["auto", "--s5"])

    def test_normal_commands_remain_unchanged(self):
        self.assertEqual(self.bridge._cli_argv(["report"]), ["report"])
        self.assertEqual(self.bridge._cli_argv(["terminal"]), ["terminal"])
        self.assertEqual(
            self.bridge._cli_argv(["auto", "--s5"]),
            ["auto", "--s5"],
        )

    def test_direct_kernel_json_fallback_is_removed(self):
        raw = [
            "/root/.local/share/jupyter/runtime/kernel-1234.json",
            "report",
        ]
        self.assertEqual(self.bridge._cli_argv(raw), ["report"])


if __name__ == "__main__":
    unittest.main()

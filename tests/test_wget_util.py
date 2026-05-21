import importlib.util
import unittest
from pathlib import Path


def load_wget_module():
    module_path = Path(__file__).resolve().parents[1] / "src" / "zeroband" / "utils" / "wget.py"
    spec = importlib.util.spec_from_file_location("zeroband_wget", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WgetUtilTests(unittest.TestCase):
    def test_wget_invokes_subprocess_without_shell(self):
        module = load_wget_module()
        captured = {}

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs

        module.shutil.which = lambda name: "/usr/bin/wget" if name == "wget" else None
        module.subprocess.run = fake_run

        module.wget(
            "https://example.com/datasets/model/file.txt;touch /tmp/pwned",
            "/tmp/download target",
        )

        self.assertEqual(
            captured["cmd"],
            [
                "wget",
                "-r",
                "-np",
                "-nH",
                "--cut-dirs=6",
                "-P",
                "/tmp/download target",
                "https://example.com/datasets/model/file.txt;touch /tmp/pwned",
            ],
        )
        self.assertIsNot(captured["kwargs"].get("shell"), True)
        self.assertTrue(captured["kwargs"]["check"])

    def test_wget_requires_wget_binary(self):
        module = load_wget_module()
        module.shutil.which = lambda name: None

        with self.assertRaisesRegex(RuntimeError, "wget is required"):
            module.wget("https://example.com/file.txt", "/tmp/downloads")


if __name__ == "__main__":
    unittest.main()

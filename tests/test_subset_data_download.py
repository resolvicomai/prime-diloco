import importlib.util
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


def load_subset_data_module():
    datasets_stub = types.ModuleType("datasets")
    datasets_stub.BuilderConfig = object
    datasets_stub.load_dataset_builder = lambda *args, **kwargs: None
    sys.modules.setdefault("datasets", datasets_stub)
    hf_stub = types.ModuleType("huggingface_hub")
    hf_stub.get_token = lambda: None
    sys.modules.setdefault("huggingface_hub", hf_stub)

    module_path = Path(__file__).resolve().parents[1] / "scripts" / "subset_data.py"
    spec = importlib.util.spec_from_file_location("subset_data", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SubsetDataDownloadTests(unittest.TestCase):
    def test_download_file_invokes_wget_without_shell(self):
        module = load_subset_data_module()
        captured = {}

        class CompletedProcess:
            returncode = 0
            stderr = b""

        def fake_run(cmd, **kwargs):
            captured["cmd"] = cmd
            captured["kwargs"] = kwargs
            return CompletedProcess()

        module.get_token = lambda: "hf_test_token"
        module.subprocess.run = fake_run

        with TemporaryDirectory() as tmpdir:
            module._download_file(
                "hf://datasets/PrimeIntellect/fineweb-edu@revision/data/train-000.parquet",
                str(Path(tmpdir) / "fineweb-edu" / "data" / "train-000.parquet"),
            )

        self.assertIsInstance(captured["cmd"], list)
        self.assertEqual(captured["cmd"][0], "wget")
        self.assertEqual(captured["cmd"][1], "--header=Authorization: Bearer hf_test_token")
        self.assertEqual(captured["cmd"][-2], "-O")
        self.assertTrue(captured["cmd"][-1].endswith("fineweb-edu/data/train-000.parquet"))
        self.assertIsNot(captured["kwargs"].get("shell"), True)


if __name__ == "__main__":
    unittest.main()

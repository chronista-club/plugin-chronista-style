import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from package import package
from validate import validate

spec = importlib.util.spec_from_file_location("sync_manifests", ROOT / "scripts/sync-manifests.py")
sync_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_module)


class DistributionTest(unittest.TestCase):
    def test_sync_preserves_codex_metadata_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in (".claude-plugin", ".codex-plugin"):
                shutil.copytree(ROOT / folder, root / folder)
            path = root / ".claude-plugin/plugin.json"
            source = json.loads(path.read_text())
            source["version"] = "1.2.3"
            path.write_text(json.dumps(source))
            with self.assertRaises(ValueError):
                sync_module.sync(root, check=True)
            interface = json.loads((root / ".codex-plugin/plugin.json").read_text())["interface"]
            sync_module.sync(root)
            sync_module.sync(root, check=True)
            target = json.loads((root / ".codex-plugin/plugin.json").read_text())
            self.assertEqual(target["version"], "1.2.3")
            self.assertEqual(target["interface"], interface)

    def test_package_excludes_personal_files_and_validates_after_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "plugin.zip"
            package(ROOT, output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertFalse(any(Path(p).name == ".mcp.json" or ".git" in Path(p).parts for p in names))
                self.assertIn("chronista-style/hooks/transcript.py", names)
                self.assertIn("chronista-style/.codex-plugin/plugin.json", names)
                self.assertIn("chronista-style/.claude-plugin/plugin.json", names)
                archive.extractall(root / "unpacked")
            validate(root / "unpacked/chronista-style")


if __name__ == "__main__":
    unittest.main()

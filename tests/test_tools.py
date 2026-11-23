import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_packs  # noqa: E402
from _packs import load_pack, pack_dirs  # noqa: E402


class PackRegistryTests(unittest.TestCase):
    def test_there_is_at_least_one_pack(self):
        self.assertTrue(pack_dirs())

    def test_every_pack_passes_the_checks(self):
        for pack in pack_dirs():
            self.assertEqual(check_packs.check_pack(pack), [], pack.name)

    def test_planned_catalog_is_valid_json_with_unique_ids(self):
        items = json.loads((ROOT / "catalog" / "planned.json").read_text(encoding="utf-8"))
        ids = [i["id"] for i in items]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(set(ids) & {p.name for p in pack_dirs()})


class HygieneTests(unittest.TestCase):
    def test_iban_check_accepts_valid_and_rejects_invalid(self):
        self.assertTrue(check_packs.iban_is_valid("GB82WEST12345698765432"))  # published example IBAN
        self.assertFalse(check_packs.iban_is_valid("GB00EXAM00000000000001"))  # our fake one

    def test_repository_has_no_hygiene_problems(self):
        self.assertEqual(check_packs.scan_hygiene(), [])


class NewPackTests(unittest.TestCase):
    def test_new_pack_scaffolds_from_template(self):
        with tempfile.TemporaryDirectory() as d:
            import shutil
            work = Path(d) / "repo"
            (work / "tools").mkdir(parents=True)
            shutil.copy(ROOT / "tools" / "new_pack.py", work / "tools")
            shutil.copy(ROOT / "tools" / "_packs.py", work / "tools")
            shutil.copytree(ROOT / "packs" / "_template", work / "packs" / "_template")
            r = subprocess.run(
                [sys.executable, str(work / "tools" / "new_pack.py"), "demo-pack", "Demo Pack", "Does a demo."],
                capture_output=True, text=True,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            meta = load_pack(work / "packs" / "demo-pack")
            self.assertEqual((meta["id"], meta["name"]), ("demo-pack", "Demo Pack"))


if __name__ == "__main__":
    unittest.main()

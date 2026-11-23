import json
import unittest
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent


class PackMetadataTests(unittest.TestCase):
    def test_pack_json_describes_this_pack(self):
        meta = json.loads((PACK / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["id"], PACK.name)


if __name__ == "__main__":
    unittest.main()

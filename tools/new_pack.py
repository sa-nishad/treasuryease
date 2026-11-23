"""Create a new pack from the template.

Usage:  python tools/new_pack.py my-pack-id "My Pack Name" "One sentence on what it does."
"""

import json
import re
import shutil
import sys

from _packs import PACKS


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    pack_id, name, summary = argv[1:]
    if not re.fullmatch(r"[a-z][a-z0-9]*(-[a-z0-9]+)*", pack_id):
        print("The pack id must be lower case words joined by hyphens, for example fee-analytics.")
        return 2
    target = PACKS / pack_id
    if target.exists():
        print(f"packs/{pack_id} already exists.")
        return 2
    shutil.copytree(PACKS / "_template", target)
    for path in target.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".json", ".py"}:
            text = path.read_text(encoding="utf-8")
            text = text.replace("PACK_ID", pack_id).replace("PACK_NAME", name).replace("PACK_SUMMARY", summary)
            path.write_text(text, encoding="utf-8")
    meta = json.loads((target / "pack.json").read_text(encoding="utf-8"))
    print(f"Created packs/{pack_id}. Status is '{meta['status']}'. Next: edit packs/{pack_id}/README.md and add tests.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

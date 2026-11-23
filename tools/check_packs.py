"""Check every pack follows the pack guide, and scan for data that should not be published.

Run from the repository root:  python tools/check_packs.py

Optional: set HYGIENE_DENYLIST to a comma-separated list of words (client names,
bank names, internal system names) that must never appear. In GitHub, store it as an
Actions repository variable so the words themselves are not committed.
"""

import os
import re
import sys

from _packs import PACKS, REQUIRED, ROOT, STATUSES, load_pack, pack_dirs

TEXT_SUFFIXES = {".md", ".xml", ".json", ".csv", ".txt", ".py", ".html", ".js", ".toml", ".yml", ".yaml"}
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
LONG_DIGITS_RE = re.compile(r"\d{8,}")
# Example IBANs that appear in public documentation. They are fine to use in samples and tests.
ALLOWED_IBANS = {
    "GB82WEST12345698765432",
    "DE89370400440532013000",
    "FR1420041010050500013M02606",
    "NL91ABNA0417164300",
}


def iban_is_valid(candidate: str) -> bool:
    """True if the string passes the IBAN mod-97 check (so it could be a real account)."""
    s = candidate[4:] + candidate[:4]
    digits = "".join(str(int(c, 36)) for c in s)
    return int(digits) % 97 == 1


def check_pack(path):
    problems = []
    meta = load_pack(path)
    for key in REQUIRED:
        if key not in meta:
            problems.append(f"{path.name}: pack.json is missing '{key}'")
    if meta.get("id") != path.name:
        problems.append(f"{path.name}: pack.json id '{meta.get('id')}' must match the folder name")
    if meta.get("status") not in STATUSES:
        problems.append(f"{path.name}: status must be one of {STATUSES}")
    if not (path / "README.md").exists():
        problems.append(f"{path.name}: README.md is missing")
    if meta.get("status") in ("available", "beta") and not (path / "tests").is_dir():
        problems.append(f"{path.name}: an {meta.get('status')} pack needs a tests/ folder")
    web = meta.get("web")
    if web and not (path / web / "index.html").exists():
        problems.append(f"{path.name}: web folder '{web}' has no index.html")
    shot = meta.get("screenshot")
    if shot and not (path / shot).exists():
        problems.append(f"{path.name}: screenshot '{shot}' not found")
    return problems


def scan_hygiene():
    problems = []
    deny = [w.strip().lower() for w in os.environ.get("HYGIENE_DENYLIST", "").split(",") if w.strip()]
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        if LONG_DIGITS_RE.search(path.name):
            problems.append(f"{rel}: file name contains a long number; bank file names often hold account numbers")
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 5_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if rel.parts[:2] == ("tools", "check_packs.py"):
            continue
        for m in IBAN_RE.finditer(text):
            if m.group() not in ALLOWED_IBANS and iban_is_valid(m.group()):
                problems.append(f"{rel}: contains a string that passes the IBAN check ({m.group()[:4]}...)")
        low = text.lower()
        for word in deny:
            if word in low:
                problems.append(f"{rel}: contains a denylisted word")
    return problems


def main():
    problems = []
    dirs = pack_dirs()
    if not dirs:
        problems.append("no packs found under packs/")
    for d in dirs:
        problems.extend(check_pack(d))
    problems.extend(scan_hygiene())
    for p in problems:
        print("problem:", p)
    print(f"checked {len(dirs)} pack(s); {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

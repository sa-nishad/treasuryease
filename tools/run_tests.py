"""Run the unit tests of the repository tools and of every pack that has a tests/ folder.

Run from the repository root:  python tools/run_tests.py
"""

import subprocess
import sys

from _packs import ROOT, pack_dirs


def run(cwd, label):
    print(f"\n=== {label} ===", flush=True)
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=cwd)
    return result.returncode == 0


def main():
    ok = run(ROOT, "repository tools")
    for pack in pack_dirs():
        if (pack / "tests").is_dir():
            ok = run(pack, f"pack: {pack.name}") and ok
    print("\nall tests passed" if ok else "\nsome tests failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

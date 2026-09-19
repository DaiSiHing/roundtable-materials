#!/usr/bin/env python3
"""verify_rerun.py - after re-running an engine, compare what you produced with what we published.

Run it from anywhere inside a clone of this repository, after running one or more
engines. For every tracked file your run changed, it fetches the published
version from git (HEAD) and compares CONTENT: line endings are ignored, numbers
are compared with a relative tolerance, and text fields are compared exactly.

    python verify_rerun.py              # tolerance 1e-9
    python verify_rerun.py --tol 1e-12

Exit code 0 if every changed file matches within tolerance, 1 otherwise. It
changes nothing; `git checkout .` restores the published files.
Needs numpy (for .npz and .csv) and git.
"""
import io
import json
import subprocess
import sys

import numpy as np

TOL = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 1e-9


def git(*args, binary=False):
    out = subprocess.run(["git", *args], capture_output=True, check=True).stdout
    return out if binary else out.decode("utf-8", "replace")


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def walk(a, b, path, nums, text):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                text.append(f"{path}/{k}: present on one side only")
            else:
                walk(a[k], b[k], f"{path}/{k}", nums, text)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            text.append(f"{path}: length {len(a)} published vs {len(b)} re-run")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f"{path}[{i}]", nums, text)
    elif (isinstance(a, (int, float)) and isinstance(b, (int, float))
          and not isinstance(a, bool) and not isinstance(b, bool)):
        if a != b:
            nums.append((rel(a, b), path))
    elif a != b:
        text.append(f"{path}: text differs")


def compare(path, pub, new):
    """Return (ok, message)."""
    if pub.replace(b"\r\n", b"\n") == new.replace(b"\r\n", b"\n"):
        return True, "identical" + ("" if pub == new else " (line endings aside)")
    low = path.lower()
    if low.endswith(".json"):
        nums, text = [], []
        walk(json.loads(pub), json.loads(new), "", nums, text)
        worst = max(nums, default=(0.0, ""))
        ok = worst[0] <= TOL and not text
        msg = f"{len(nums)} numbers differ, largest relative difference {worst[0]:.1e}"
        if text:
            msg += f"; {len(text)} non-numeric difference(s): " + "; ".join(text[:4])
        return ok, msg
    if low.endswith(".csv"):
        a = np.loadtxt(io.BytesIO(pub), delimiter=",", skiprows=1, ndmin=2)
        b = np.loadtxt(io.BytesIO(new), delimiter=",", skiprows=1, ndmin=2)
        if a.shape != b.shape:
            return False, f"shape {a.shape} published vs {b.shape} re-run"
        worst = float(np.max(np.abs(a - b) / np.maximum(np.abs(a), 1e-300)))
        return worst <= TOL, f"largest relative difference {worst:.1e}"
    if low.endswith(".npz"):
        a, b = np.load(io.BytesIO(pub)), np.load(io.BytesIO(new))
        if sorted(a.files) != sorted(b.files):
            return False, "different arrays inside"
        worst = 0.0
        for k in a.files:
            if a[k].shape != b[k].shape:
                return False, f"{k}: shape differs"
            worst = max(worst, float(np.max(np.abs(a[k] - b[k]) / np.maximum(np.abs(a[k]), 1e-300))))
        return worst <= TOL, f"{len(a.files)} arrays, largest relative difference {worst:.1e}"
    return False, "differs (no content comparison for this file type)"


def main():
    top = git("rev-parse", "--show-toplevel").strip()
    changed = [p for p in git("-C", top, "diff", "--name-only", "HEAD").splitlines() if p]
    if not changed:
        print("No tracked file differs from the published version. "
              "(Either nothing was re-run, or the re-run was byte-identical.)")
        return 0
    bad = 0
    for p in changed:
        pub = git("-C", top, "show", f"HEAD:{p}", binary=True)
        try:
            with open(f"{top}/{p}", "rb") as f:
                new = f.read()
        except FileNotFoundError:
            print(f"MISSING  {p}")
            bad += 1
            continue
        ok, msg = compare(p, pub, new)
        print(f"{'MATCH   ' if ok else 'DIFFERS '} {p}: {msg}")
        bad += 0 if ok else 1
    print(f"\n{len(changed) - bad} of {len(changed)} changed files match the published "
          f"version within a relative tolerance of {TOL:g}.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

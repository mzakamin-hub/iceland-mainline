#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Static package checks (run by .github/workflows/checks.yml, also usable locally from the repository root).

  python3 .github/scripts/package-checks.py

1. every tracked shell script parses (bash -n / sh -n by its shebang), every Python file compiles, every JSON file loads
2. packaging/arch/*/PKGBUILD: every local (non-URL) entry of source=() exists next to the PKGBUILD or is listed in
   its SOURCES-NOT-STAGED.txt, and source=() and sha256sums=() have the same length
3. if a package has a tests/ directory: each tests/test_*.py runs with the arguments of its "Usage:" line
   (no Usage line: "files <package>.spec")
Exit status 0 when every check passes.
"""
import ast
import json
import os
import re
import shlex
import subprocess
import sys

fails = 0


def fail(path, msg, line=None):
    global fails
    fails += 1
    print(f"::error file={path}" + (f",line={line}" if line else "") + f",title=package-checks::{msg}")


files = [f for f in subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True).stdout.decode().split("\0")
         if f and os.path.isfile(f) and not os.path.islink(f)]
n_sh = n_py = n_js = 0
for f in files:
    with open(f, "rb") as fh:
        head = fh.read(4096)
    if b"\0" in head:
        continue
    first = head.split(b"\n", 1)[0].decode("utf-8", "replace")
    if first.startswith("#!") and re.search(r"\b(bash|sh)\b", first) or f.endswith(".sh"):
        sh = "sh" if re.search(r"/sh\b|env sh\b", first) else "bash"
        r = subprocess.run([sh, "-n", f], capture_output=True, text=True)
        n_sh += 1
        if r.returncode:
            fail(f, f"{sh} -n: " + r.stderr.strip().replace("\n", " | "))
    elif f.endswith(".py") or (first.startswith("#!") and "python" in first):
        n_py += 1
        try:
            ast.parse(open(f, encoding="utf-8").read(), f)
        except SyntaxError as e:
            fail(f, f"python: {e.msg}", e.lineno)
    elif f.endswith(".json"):
        n_js += 1
        try:
            json.load(open(f, encoding="utf-8"))
        except ValueError as e:
            fail(f, f"json: {e}")
print(f"syntax: {n_sh} shell scripts, {n_py} Python files, {n_js} JSON files")

# 2. Arch PKGBUILDs: local sources present (or listed as not staged), source / sha256sums lengths equal
def bash_array(pkgbuild, name):
    """The values of a PKGBUILD array, from bash itself (variables expanded, nothing else run)."""
    script = ('set -e; cd "$(dirname "$1")"; srcdir=/nonexistent; pkgdir=/nonexistent; CARCH=aarch64; '
              'source "$1" >/dev/null 2>&1 || true; eval "arr=(\"\\${%s[@]}\")"; '
              'printf "%%s\\0" "${arr[@]}"' % name)
    r = subprocess.run(["bash", "-c", script, "pkgbuild", os.path.abspath(pkgbuild)], capture_output=True)
    return [x.decode() for x in r.stdout.split(b"\0") if x]


n_pkg = 0
for pb in sorted(f for f in files if re.match(r"packaging/arch/[^/]+/PKGBUILD$", f)):
    n_pkg += 1
    d = os.path.dirname(pb)
    srcs, sums = bash_array(pb, "source"), bash_array(pb, "sha256sums")
    if sums and len(srcs) != len(sums):
        fail(pb, f"source=() has {len(srcs)} entries, sha256sums=() {len(sums)}")
    staged = set()
    ns = os.path.join(d, "SOURCES-NOT-STAGED.txt")
    if os.path.exists(ns):
        staged = {line.split("\t")[0] for line in open(ns, encoding="utf-8") if line.strip() and not line.startswith("#")}
    for s in srcs:
        name, _, url = s.partition("::")
        if not url:
            url, name = name, os.path.basename(name)
        if re.match(r"^[a-z+]+://", url):
            continue
        if not os.path.exists(os.path.join(d, name)) and name not in staged:
            fail(pb, f"local source {name} is neither in {d} nor in its SOURCES-NOT-STAGED.txt")
print(f"PKGBUILDs: {n_pkg} checked")

# 3. package tests, when the package carries them
for t in sorted(f for f in files if re.match(r"packaging/[^/]+/tests/test_[^/]+\.py$", f)):
    pdir = t.split("/tests/")[0]
    m = re.search(r"Usage:\s*python3\s+(tests/\S+\.py)([^\n\"]*)", open(t, encoding="utf-8").read())
    args = shlex.split(m.group(2).split(" #")[0]) if m else ["files", os.path.basename(pdir) + ".spec"]
    args = [a for a in args if not (a.startswith("[") or a.endswith("]"))]
    r = subprocess.run([sys.executable, os.path.relpath(t, pdir)] + args, cwd=pdir, capture_output=True, text=True,
                       timeout=600, stdin=subprocess.DEVNULL)
    if r.returncode:
        fail(t, "test failed: " + " | ".join((r.stdout + r.stderr).strip().splitlines()[-5:]))
    else:
        print(f"PASS {t}")

print(f"package-checks: {'PASS' if not fails else 'FAIL'} ({fails} failure(s))")
sys.exit(1 if fails else 0)

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Static package checks (run by .github/workflows/checks.yml, also usable locally from the repository root).

  python3 .github/scripts/package-checks.py

1. every tracked shell script parses (bash -n / sh -n by its shebang), every Python file compiles, every JSON file loads
2. packaging/iceland-device: every SourceN of the spec exists in files/ (or is one of the tarballs build-rpm.sh makes),
   every file in files/ is a source of the spec
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

# 2. iceland-device spec sources <-> files/
pkg = "packaging/iceland-device"
spec = os.path.join(pkg, "iceland-device.spec")
made = re.compile(r"^(audioreach-topology-[0-9a-f]+\.tar\.gz|iceland-audio\.tar\.gz|iceland-tuned\.tar\.gz)$")
if os.path.exists(spec):
    srcs = {}
    for n, line in enumerate(open(spec, encoding="utf-8"), 1):
        m = re.match(r"^Source\d+:\s*(\S+)", line)
        if m:
            srcs[os.path.basename(m.group(1))] = n
    have = {os.path.relpath(f, os.path.join(pkg, "files")) for f in files if f.startswith(pkg + "/files/")}
    top = {h for h in have if "/" not in h}
    for s, n in srcs.items():
        if s not in top and not made.match(s):
            fail(spec, f"Source {s} is not in {pkg}/files", n)
    for h in sorted(top - set(srcs)):
        fail(f"{pkg}/files/{h}", "file is not a Source of iceland-device.spec")
    print(f"iceland-device.spec: {len(srcs)} sources, {len(top)} files in files/")

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

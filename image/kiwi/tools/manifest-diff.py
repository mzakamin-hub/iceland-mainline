#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""image/kiwi/tools/manifest-diff.py - the package set of a PC-built image against B149's (the acceptance of "same content").
PC only, reads two files, writes the report to stdout.

  python3 -I manifest-diff.py IMAGE_MANIFEST.tsv B149.json [--ours ours.tsv] [--allow allow.txt]
  python3 -I manifest-diff.py --selftest

IMAGE_MANIFEST.tsv: NAME<TAB>EPOCH:VERSION-RELEASE<TAB>ARCH per line (image-check.sh writes it with rpm --root -qa).
B149.json: golden-build-b149.json ("packages": name / evr / arch).
FAIL when: a B149 name is missing from the image; the image has a name B149 lacks (unless listed in --allow, one name per
line: e.g. a package Fedora split / renamed since B149); one of ours is not the version of ours.tsv; a floor is not met
(B149's floors: pipewire 1.6.9, wireplumber 0.5.18, ladspa-swh-plugins 0.4.17, qbootctl 0.2.2).
INFO: Fedora packages at another version than B149 (expected: the build takes the Fedora 44 updates of its day, as every
B run's refresh did; the held set is ours only). Last line "MANIFEST-DIFF: PASS|FAIL (...)".
"""
import json, re, sys

FLOORS = {"pipewire": "1.6.9", "wireplumber": "0.5.18", "ladspa-swh-plugins": "0.4.17", "qbootctl": "0.2.2"}


def rpmvercmp(a, b):
    """rpm's version segment comparison (rpmio/rpmvercmp.c), incl. ~ and ^"""
    if a == b:
        return 0
    i = j = 0
    while i < len(a) or j < len(b):
        while i < len(a) and not a[i].isalnum() and a[i] not in "~^":
            i += 1
        while j < len(b) and not b[j].isalnum() and b[j] not in "~^":
            j += 1
        if (i < len(a) and a[i] == "~") or (j < len(b) and b[j] == "~"):
            if not (i < len(a) and a[i] == "~"):
                return 1
            if not (j < len(b) and b[j] == "~"):
                return -1
            i += 1; j += 1; continue
        if (i < len(a) and a[i] == "^") or (j < len(b) and b[j] == "^"):
            if i >= len(a):
                return -1
            if j >= len(b):
                return 1
            if a[i] != "^":
                return 1
            if b[j] != "^":
                return -1
            i += 1; j += 1; continue
        if i >= len(a) or j >= len(b):
            break
        if a[i].isdigit():
            m1 = re.match(r"\d+", a[i:]).group(); m2 = re.match(r"\d+", b[j:])
            if not m2:
                return 1
            m2 = m2.group(); x, y = m1.lstrip("0"), m2.lstrip("0")
            if len(x) != len(y):
                return 1 if len(x) > len(y) else -1
            if x != y:
                return 1 if x > y else -1
            i += len(m1); j += len(m2)
        else:
            m1 = re.match(r"[A-Za-z]+", a[i:]).group(); m2 = re.match(r"[A-Za-z]+", b[j:])
            if not m2:
                return -1
            m2 = m2.group()
            if m1 != m2:
                return 1 if m1 > m2 else -1
            i += len(m1); j += len(m2)
    if i >= len(a) and j >= len(b):
        return 0
    return -1 if i >= len(a) else 1


def evr(s):
    e, _, vr = s.rpartition(":") if ":" in s else ("0", "", s)
    v, _, r = vr.rpartition("-") if "-" in vr else (vr, "", "")
    return (e or "0", v, r)


def cmp_evr(a, b):
    a, b = evr(a), evr(b)
    for x, y in zip(a, b):
        c = rpmvercmp(x, y) if not (x.isdigit() and y.isdigit()) else (int(x) > int(y)) - (int(x) < int(y))
        if c:
            return c
    return 0


def diff(img_rows, ref_pkgs, ours, allow):
    img = {}
    for n, e, a in img_rows:
        img.setdefault(n, []).append(e)
    ref = {}
    for p in ref_pkgs:
        ref.setdefault(p["name"], []).append(p["evr"])
    out, fail = [], 0
    missing = sorted(set(ref) - set(img) - {"gpg-pubkey"})
    extra = sorted(set(img) - set(ref) - set(allow) - {"gpg-pubkey"})
    for n in missing:
        out.append("FAIL missing (in B149): %s" % n); fail += 1
    for n in extra:
        out.append("FAIL extra (not in B149): %s %s" % (n, img[n][0])); fail += 1
    for n, want in ours.items():
        have = [v.split(":", 1)[-1] for v in img.get(n, [])]
        if not any(h.startswith(want) for h in have):
            out.append("FAIL ours %s: %s (want %s*)" % (n, ",".join(have) or "absent", want)); fail += 1
    for n, f in FLOORS.items():
        have = img.get(n, [])
        if not have or all(cmp_evr(h, "0:" + f + "-0") < 0 for h in have):
            out.append("FAIL floor %s >= %s: %s" % (n, f, ",".join(have) or "absent")); fail += 1
    newer = older = 0
    for n in sorted(set(img) & set(ref)):
        if n in ours or n == "gpg-pubkey":
            continue
        a, b = max(img[n], key=lambda x: x), max(ref[n], key=lambda x: x)
        c = cmp_evr(a, b if ":" in b else "0:" + b)
        if c > 0:
            newer += 1
        elif c < 0:
            older += 1; out.append("INFO older than B149: %s %s < %s" % (n, a, b))
    out.append("INFO Fedora packages newer than B149: %d, older: %d (the Fedora 44 updates of the build day)" % (newer, older))
    out.append("MANIFEST-DIFF: %s (%d FAIL; image %d names, B149 %d names, missing %d, extra %d)" % (
        "PASS" if fail == 0 else "FAIL", fail, len(img), len(ref), len(missing), len(extra)))
    return fail, out


def selftest():
    ok = True

    def t(n, c):
        nonlocal ok
        ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    t("vercmp 1.6.10 > 1.6.9", rpmvercmp("1.6.10", "1.6.9") == 1)
    t("vercmp tilde: 7.3.0~rc7 < 7.3.0", rpmvercmp("7.3.0~rc7", "7.3.0") == -1)
    t("vercmp caret: 0.4.4^8 > 0.4.4", rpmvercmp("0.4.4^8", "0.4.4") == 1)
    t("evr epoch wins", cmp_evr("1:1.0-1", "0:9.0-1") == 1)
    ref = [{"name": "pipewire", "evr": "1.6.9-1.fc44"}, {"name": "bash", "evr": "5.3-1.fc44"}, {"name": "wireplumber", "evr": "0.5.18-1.fc44"},
           {"name": "ladspa-swh-plugins", "evr": "0.4.17-20.fc44"}, {"name": "qbootctl", "evr": "0.2.2-1.fc44"},
           {"name": "iceland-device", "evr": "0.28-17.fc44"}]
    img = [("pipewire", "0:1.6.10-1.fc44", "aarch64"), ("bash", "0:5.3-2.fc44", "aarch64"), ("wireplumber", "0:0.5.18-1.fc44", "aarch64"),
           ("ladspa-swh-plugins", "0:0.4.17-20.fc44", "aarch64"), ("qbootctl", "0:0.2.2-1.fc44", "aarch64"), ("iceland-device", "0:0.28-17.fc44", "noarch")]
    f, o = diff(img, ref, {"iceland-device": "0.28-17"}, [])
    t("same names, newer Fedora versions: PASS", f == 0)
    f, o = diff(img[:-1] + [("extra-pkg", "0:1-1", "noarch")], ref, {"iceland-device": "0.28-17"}, [])
    t("a missing name, an extra name, ours absent: 3 FAIL", f == 3)
    f, o = diff([("pipewire", "0:1.6.8-1.fc44", "aarch64")] + img[1:], ref, {}, [])
    t("a floor not met: FAIL", f == 1)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL")); return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        return selftest()
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or not a[i - 1].startswith("--"))]
    if len(pos) != 2:
        print(__doc__); return 2
    rows = [l.rstrip("\n").split("\t") for l in open(pos[0]) if l.strip() and not l.startswith("#")]
    ref = json.load(open(pos[1]))["packages"]
    ours = {}
    if "--ours" in a:
        for l in open(a[a.index("--ours") + 1]):
            if l.strip() and not l.startswith("#"):
                n, v = l.rstrip("\n").split("\t")[:2]; ours[n] = v
    allow = [l.strip() for l in open(a[a.index("--allow") + 1])] if "--allow" in a else []
    fail, out = diff(rows, ref, ours, [x for x in allow if x and not x.startswith("#")])
    print("\n".join(out))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())

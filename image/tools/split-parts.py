#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""wf/generic/recipe/split-parts.py - split a finished install image into release parts (< 2 GiB each, GitHub's per-asset
limit) and write the "image" block of tools/installer/release-manifest.json (name, size, sha256 per part + the whole).
PC only; reads IMAGE, writes only OUT_DIR. The parts are byte ranges in order; joined they are the image (proved here:
the parts are re-read and their concatenation hashed again).
  python3 -I split-parts.py IMAGE OUT_DIR [--part-bytes N] [--base-url URL] [--unpacked BYTES]
  python3 -I split-parts.py --selftest
Writes OUT_DIR/<image>.partNN, OUT_DIR/SHA256SUMS, OUT_DIR/image-manifest.json. --base-url (default a PLACEHOLDER)
prefixes each part's url; the installer refuses PLACEHOLDER urls, so nothing can be downloaded before a release exists.
"""
import hashlib, json, os, sys, tempfile

LIMIT = 2 * 1024 ** 3                 # GitHub: every release asset < 2 GiB
DEFAULT = 2_000_000_000               # 1.86 GiB: margin below the limit
BUF = 16 << 20


def split(img, out, part=DEFAULT, base="PLACEHOLDER: https://github.com/<owner>/<repo>/releases/download/<tag>", unpacked=None):
    assert 0 < part < LIMIT, "part size must be below 2 GiB"
    os.makedirs(out, exist_ok=True)
    name = os.path.basename(img); size = os.path.getsize(img)
    whole = hashlib.sha256(); parts = []
    with open(img, "rb") as f:
        i = 0
        while True:
            left = min(part, size - f.tell())
            if left <= 0:
                break
            i += 1; pn = "%s.part%02d" % (name, i); h = hashlib.sha256(); n = 0
            with open(os.path.join(out, pn), "wb") as o:
                while left:
                    b = f.read(min(BUF, left))
                    if not b:
                        raise IOError("short read")
                    o.write(b); h.update(b); whole.update(b); left -= len(b); n += len(b)
            parts.append({"name": pn, "url": "%s/%s" % (base.rstrip("/"), pn), "size": n, "sha256": h.hexdigest()})
    # proof: the parts, re-read from disk and joined, are the image
    again = hashlib.sha256()
    for p in parts:
        hp = hashlib.sha256()
        with open(os.path.join(out, p["name"]), "rb") as f:
            for b in iter(lambda: f.read(BUF), b""):
                again.update(b); hp.update(b)
        assert hp.hexdigest() == p["sha256"], "part %s changed on disk" % p["name"]
    assert again.hexdigest() == whole.hexdigest(), "the joined parts are not the image"
    assert all(p["size"] < LIMIT for p in parts) and sum(p["size"] for p in parts) == size
    m = {"file": name, "size": size, "sha256": whole.hexdigest(), "parts": parts}
    if unpacked:
        m["unpacked_size"] = int(unpacked)
    json.dump(m, open(os.path.join(out, "image-manifest.json"), "w"), indent=1)
    with open(os.path.join(out, "SHA256SUMS"), "w") as s:
        s.write("%s  %s\n" % (m["sha256"], name))
        for p in parts:
            s.write("%s  %s\n" % (p["sha256"], p["name"]))
    return m


def selftest():
    d = tempfile.mkdtemp(prefix="split-st."); img = os.path.join(d, "x.img")
    data = os.urandom(10 * 1024 * 1024 + 123)
    open(img, "wb").write(data)
    m = split(img, os.path.join(d, "out"), part=3 * 1024 * 1024, unpacked=999)
    ok = (len(m["parts"]) == 4 and m["size"] == len(data) and m["sha256"] == hashlib.sha256(data).hexdigest()
          and b"".join(open(os.path.join(d, "out", p["name"]), "rb").read() for p in m["parts"]) == data
          and m["parts"][-1]["size"] == len(data) - 3 * 3 * 1024 * 1024 and m["unpacked_size"] == 999
          and all(p["url"].startswith("PLACEHOLDER") for p in m["parts"]))
    try:
        split(img, os.path.join(d, "o2"), part=LIMIT); bad = False
    except AssertionError:
        bad = True
    print("SELFTEST %s (4 parts, joined = image, sha256s, placeholder urls; part size >= 2 GiB refused: %s)" % ("PASS" if ok and bad else "FAIL", bad))
    return 0 if ok and bad else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        sys.exit(selftest())
    if len(a) < 2:
        print(__doc__); sys.exit(2)
    kw = {}
    for k, v in zip(a[2::2], a[3::2]):
        kw[{"--part-bytes": "part", "--base-url": "base", "--unpacked": "unpacked"}[k]] = int(v) if k == "--part-bytes" else v
    m = split(a[0], a[1], **kw)
    print("split-parts: %s %d bytes sha256 %s -> %d parts (%s)" % (m["file"], m["size"], m["sha256"][:16], len(m["parts"]),
          ", ".join("%s %d" % (p["name"][-6:], p["size"]) for p in m["parts"])))

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""wf/generic/recipe/mk-small.py - the SMALL generic disk (owner, 15 Oct 2026: one image for every storage size). PC only;
reads the committed golden, writes only new files next to it.

  mk-small.py RUN/golden.json [--name golden-small]              -> NAME.{json,body,tail}
  mk-small.py RUN/golden-small.json --grow-test BYTES [--name N]  -> N.{json,body,tail}: the small disk as it lies in a
        BIGGER userdata (its backup GPT in the middle, the rest unwritten): for the rehearsal that proves the growth
        (rehearsal-pc.sh serve with this json; systemd-repart / iceland-grow must grow it, the overlay keeps the golden)
  mk-small.py --selftest

The golden's virtual disk is userdata-sized (B149 style). The small disk ends right after the root partition: SLACK (1 MiB)
+ the backup GPT (4 entry blocks + header). Its body = the golden's body with blocks 0-5 replaced (protective MBR,
primary header and entries for the small size; same disk GUID, same partitions, same names and GUIDs), its tail = the
new backup GPT. Then mk-sparse.py makes the release image from NAME.json (unpacked size = the small size = the minimum
userdata the installer accepts). On a bigger userdata both boot loaders take the primary GPT (U-Boot part_efi: my_lba,
CRC, usable range within the disk; Linux efi.c: the same, the backup elsewhere only warns) and systemd-repart, then
iceland-grow, move the backup GPT to the end and grow the root (iceland-device 0.28-17).
"""
import hashlib, json, os, shutil, struct, sys, tempfile, zlib

IMG = os.path.expanduser("~/mainline/build/wf/install/cand/image")
sys.path.insert(0, IMG)
# a checkout: iceland_disk.py sits beside this file (image/tools) or in $ICELAND_IMAGE_TOOLS
sys.path.insert(0, os.environ.get("ICELAND_IMAGE_TOOLS") or os.path.dirname(os.path.abspath(__file__)))
import iceland_disk as D   # noqa: E402

BLK = D.BLK
SLACK = 256                      # 1 MiB after the root partition


def sha(p):
    return D.sha256_file(p)


def small(golden_json, name="golden-small"):
    m = json.load(open(golden_json)); d = os.path.dirname(os.path.abspath(golden_json))
    disk = D.Disk(golden_json, readonly=True)
    g = D.parse_gpt(disk.read, m["size"] // BLK)
    parts = sorted(g["parts"], key=lambda p: p["first"])
    last = max(p["last"] for p in parts)
    body_bl = m["body_len"] // BLK
    assert last + 1 <= body_bl, "a partition ends behind the body"
    n = body_bl + SLACK + 1 + D.ENTRY_BLOCKS
    n = max(n, last + 1 + SLACK + 1 + D.ENTRY_BLOCKS)
    primary, backup = D.make_gpt(n, [(p["type"], p["uuid"], p["first"], p["last"], p["name"]) for p in sorted(parts, key=lambda p: p["n"])], g["disk_guid"])
    assert sorted(p["n"] for p in parts) == list(range(1, len(parts) + 1)), "partition numbers must be 1..N (make_gpt keeps the order)"
    ob = os.path.join(d, name + ".body"); ot = os.path.join(d, name + ".tail")
    with open(os.path.join(d, m["body"]), "rb") as src, open(ob + ".part", "wb") as dst:
        shutil.copyfileobj(src, dst, 16 << 20)
        dst.seek(0); dst.write(primary)
    os.replace(ob + ".part", ob)
    open(ot, "wb").write(backup)
    nm = dict(m)
    nm.update(what="OnePlus Pad 4 GENERIC install image (Fedora Remix for OnePlus Pad 4), the SMALL disk: grows into userdata at the first boot",
              size=n * BLK, body=os.path.basename(ob), tail=os.path.basename(ot), tail_len=len(backup),
              body_sha256=sha(ob), tail_sha256=sha(ot), min_userdata_bytes=n * BLK,
              small_from=dict(json=os.path.basename(golden_json), size=m["size"], body_sha256=m.get("body_sha256")))
    oj = os.path.join(d, name + ".json"); json.dump(nm, open(oj, "w"), indent=1)
    # proof: the new disk reads back with both CRCs, the backup at its last block, the same partitions
    nd = D.Disk(oj, readonly=True); g2 = D.parse_gpt(nd.read, n)
    key = lambda q: [(p["n"], p["type"], p["uuid"], p["first"], p["last"], p["name"]) for p in q["parts"]]
    assert key(g2) == key(g) and g2["disk_guid"] == g["disk_guid"] and g2["last_usable"] >= last, "the small GPT differs"
    with open(ob, "rb") as a, open(os.path.join(d, m["body"]), "rb") as b:
        a.seek(6 * BLK); b.seek(6 * BLK)
        ha, hb = hashlib.sha256(), hashlib.sha256()
        for x, h in ((a, ha), (b, hb)):
            for c in iter(lambda: x.read(16 << 20), b""):
                h.update(c)
        assert ha.digest() == hb.digest(), "the body beyond the partition table changed"
    return oj, nm


def grow_test(small_json, size, name):
    """the small disk inside a bigger device: body = small body + small tail (+ zeros to a block), size = BYTES"""
    m = json.load(open(small_json)); d = os.path.dirname(os.path.abspath(small_json))
    assert size % BLK == 0 and size > m["size"] + (1 << 20), "the test device must be bigger than the small disk"
    ob = os.path.join(d, name + ".body"); ot = os.path.join(d, name + ".tail")
    with open(ob + ".part", "wb") as dst:
        with open(os.path.join(d, m["body"]), "rb") as s:
            shutil.copyfileobj(s, dst, 16 << 20)
        dst.seek(m["size"] - m["tail_len"]); dst.write(open(os.path.join(d, m["tail"]), "rb").read())
    os.replace(ob + ".part", ob)
    open(ot, "wb").write(bytes(5 * BLK))          # the device's last blocks: no GPT there (what a bigger userdata has)
    nm = dict(m); nm.update(what="GROWTH TEST device (rehearsal only, never written to a tablet): the small disk in %d bytes" % size,
                            size=size, body=os.path.basename(ob), tail=os.path.basename(ot), body_len=m["size"], tail_len=5 * BLK,
                            body_sha256=sha(ob), tail_sha256=sha(ot), grow_test=True)
    oj = os.path.join(d, name + ".json"); json.dump(nm, open(oj, "w"), indent=1)
    # the primary GPT is still valid on the bigger device (what U-Boot and Linux read)
    nd = D.Disk(oj, readonly=True); g = D.parse_gpt(nd.read)
    assert g["my"] == 1 and g["last_usable"] < size // BLK and g["alt"] == m["size"] // BLK - 1
    return oj


def selftest():
    w = tempfile.mkdtemp(prefix="mksmall.")
    big = 65536                                    # a 256 MiB "userdata"
    parts = [(D.TYPE_ESP, "11111111-2222-3333-4444-555555555555", 6, 255, "EFI System Partition"),
             (D.TYPE_XBOOTLDR, "21111111-2222-3333-4444-555555555555", 256, 511, "boot"),
             (D.TYPE_ROOT_ARM64, "31111111-2222-3333-4444-555555555555", 512, 4095, "root")]
    pri, bak = D.make_gpt(big, parts, "41111111-2222-3333-4444-555555555555")
    body = bytearray(4096 * BLK); body[:len(pri)] = pri
    for b in range(6, 4096):
        struct.pack_into("<I", body, b * BLK, b)  # a mark in every block
    open(w + "/golden.body", "wb").write(body); open(w + "/golden.tail", "wb").write(bak)
    json.dump(dict(size=big * BLK, block=BLK, body="golden.body", tail="golden.tail", body_len=len(body), tail_len=len(bak)), open(w + "/golden.json", "w"))
    ok = True

    def t(n, c):
        nonlocal ok
        ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    oj, nm = small(w + "/golden.json")
    t("small disk: size = body + 1 MiB + backup GPT", nm["size"] == (4096 + SLACK + 1 + D.ENTRY_BLOCKS) * BLK and nm["min_userdata_bytes"] == nm["size"])
    g = D.parse_gpt(D.Disk(oj, readonly=True).read, nm["size"] // BLK)
    t("small GPT: both CRCs, backup at its last block, same 3 partitions", [p["last"] for p in g["parts"]] == [255, 511, 4095])
    sb = open(w + "/golden-small.body", "rb").read()
    t("body beyond block 5 unchanged (every block's mark)", all(struct.unpack_from("<I", sb, b * BLK)[0] == b for b in range(6, 4096)))
    gj = grow_test(oj, big * BLK, "growtest")
    gd = D.Disk(gj, readonly=True); gg = D.parse_gpt(gd.read)
    t("in a bigger device: the primary GPT is valid, its backup is in the middle (what repart / iceland-grow fix)", gg["alt"] == nm["size"] // BLK - 1 and gg["alt"] < big - 1)
    t("in a bigger device: the device end holds no GPT", gd.read(big * BLK - BLK, 8) != b"EFI PART")
    try:
        grow_test(oj, nm["size"], "bad"); bad = False
    except AssertionError:
        bad = True
    t("a growth device not bigger than the small disk is refused", bad)
    shutil.rmtree(w)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL")); return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        sys.exit(selftest())
    if not a:
        print(__doc__); sys.exit(2)
    opt = dict(zip(a[1::2], a[2::2]))
    if "--grow-test" in opt:
        print("mk-small: growth test device %s" % grow_test(a[0], int(opt["--grow-test"]), opt.get("--name", "golden-growtest")))
    else:
        oj, nm = small(a[0], opt.get("--name", "golden-small"))
        print("mk-small: %s: %d bytes (minimum userdata), body sha256 %s, tail %s" % (oj, nm["size"], nm["body_sha256"][:16], nm["tail_sha256"][:16]))

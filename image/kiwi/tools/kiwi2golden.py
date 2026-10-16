#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""image/kiwi/tools/kiwi2golden.py - kiwi's raw disk -> the project's golden disk format (NAME.json / .body / .tail), so that
mk-small.py, mk-sparse.py, privscan.py --golden and rehearsal-pc.sh serve take a PC-built image unchanged. PC only, no root;
reads RAW, writes only OUT_DIR.

  python3 -I kiwi2golden.py RAW OUT_DIR [--name kiwi-b150g] [--keep-esp]
  python3 -I kiwi2golden.py --selftest

Checks (exit 1 on any): a 4096-byte-block GPT with both CRCs (kiwi's target_blocksize="4096"); exactly 3 partitions, in
order ESP / XBOOTLDR / root-arm64 (the types stage0 / B149 have; systemd-repart's "Type=root" needs root-arm64); /boot is
ext4 with 4 KiB blocks; the root is btrfs with 4 KiB sectors and ends inside its partition.
Changes (as mk-golden.py did for the official image): the partition NAMES become B149's ("EFI System Partition", "boot",
"root"; kiwi writes p.UEFI / p.lxboot / p.lxroot) - same GUIDs, same disk GUID, same ranges; and unless --keep-esp the EFI
partition is rebuilt as FAT32 with 4096-byte sectors, same volume id and the same files (kiwi formats it FAT16; B149's is
FAT32 / 4096 and every U-Boot / Linux result was measured on that). Needs mtools + dosfstools for the ESP step.
The body is the disk up to the end of the root partition; mk-small.py then makes the minimum-size disk from NAME.json.
"""
import hashlib, json, os, shutil, struct, subprocess, sys, tempfile

for p in (os.environ.get("ICELAND_IMAGE_TOOLS", ""), os.path.expanduser("~/mainline/build/wf/install/cand/image"),
          os.path.join(os.path.dirname(os.path.abspath(__file__)), "image")):
    if p and os.path.isfile(os.path.join(p, "iceland_disk.py")):
        sys.path.insert(0, p)
        break
import iceland_disk as D   # noqa: E402

BLK = D.BLK
NAMES = ["EFI System Partition", "boot", "root"]
TYPES = [D.TYPE_ESP, D.TYPE_XBOOTLDR, D.TYPE_ROOT_ARM64]


def run(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, MTOOLS_SKIP_CHECK="1"))
    if r.returncode:
        raise SystemExit("FAILED: %s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def reader(path):
    f = open(path, "rb")

    def read(off, n):
        f.seek(off)
        return f.read(n)
    return read


def check_fs(raw, parts):
    read = reader(raw)
    esp, boot, root = parts
    sb = read(boot["first"] * BLK + 1024, 256)
    assert struct.unpack_from("<H", sb, 56)[0] == 0xEF53, "/boot is not ext4"
    assert 1024 << struct.unpack_from("<I", sb, 24)[0] == 4096, "/boot ext4 block size is not 4096"
    bs = read(root["first"] * BLK + 0x10000, 0x100)
    assert bs[0x40:0x48] == b"_BHRfS_M", "root is not btrfs"
    total = struct.unpack_from("<Q", bs, 0x70)[0]; sector = struct.unpack_from("<I", bs, 0x90)[0]
    assert sector == 4096, "btrfs sector size %d" % sector
    assert total <= (root["last"] - root["first"] + 1) * BLK, "btrfs larger than its partition"
    bpb = read(esp["first"] * BLK, 512)
    return dict(btrfs_total=total, esp_sector=struct.unpack_from("<H", bpb, 11)[0],
                esp_fat=("FAT32" if bpb[82:87] == b"FAT32" else bpb[54:59].decode("ascii", "replace").strip()))


def rebuild_esp(body, esp):
    """mk-golden.py's method: copy every file out with mtools, mkfs.fat -F 32 -S 4096 with the same serial / label, copy back,
    compare the two trees by sha256, write the new FAT over the ESP range of BODY"""
    off, ln = esp["first"] * BLK, (esp["last"] - esp["first"] + 1) * BLK
    tmp = tempfile.mkdtemp(prefix="esp-", dir=os.path.dirname(os.path.abspath(body)))
    try:
        old, new = os.path.join(tmp, "old.img"), os.path.join(tmp, "new.img")
        with open(body, "rb") as f, open(old, "wb") as g:
            f.seek(off); left = ln
            while left:
                d = f.read(min(left, 1 << 22)); assert d; g.write(d); left -= len(d)
        bpb = open(old, "rb").read(512)
        fat32 = bpb[82:87] == b"FAT32"
        serial = struct.unpack_from("<I", bpb, 67 if fat32 else 39)[0]
        label = bpb[71:82].decode().strip() if fat32 else bpb[43:54].decode().strip()
        fo, fn = os.path.join(tmp, "fo"), os.path.join(tmp, "fn"); os.makedirs(fo); os.makedirs(fn)
        for e in [l.strip() for l in run("mdir", "-b", "-i", old, "::/").splitlines() if l.strip()]:
            run("mcopy", "-s", "-m", "-n", "-i", old, e, fo + "/")
        run("mkfs.fat", "-F", "32", "-S", "4096", "-s", "1", "-h", str(esp["first"]), "-i", "%08X" % serial,
            "-n", (label if label and label != "NO NAME" else "EFI"), "-C", new, str(ln // 1024))
        for e in sorted(os.listdir(fo)):
            run("mcopy", "-s", "-m", "-i", new, os.path.join(fo, e), "::/")
        for e in [l.strip() for l in run("mdir", "-b", "-i", new, "::/").splitlines() if l.strip()]:
            run("mcopy", "-s", "-m", "-n", "-i", new, e, fn + "/")

        def tree(r):
            return {os.path.relpath(os.path.join(dp, n), r).lower(): hashlib.sha256(open(os.path.join(dp, n), "rb").read()).hexdigest()
                    for dp, _, fs in os.walk(r) for n in fs}
        a, b = tree(fo), tree(fn)
        assert a == b and a, "ESP files differ after the copy (or the ESP is empty)"
        nb = open(new, "rb").read(512)
        assert struct.unpack_from("<H", nb, 11)[0] == 4096 and nb[82:87] == b"FAT32" and struct.unpack_from("<I", nb, 67)[0] == serial
        assert os.path.getsize(new) == ln
        with open(new, "rb") as s, open(body, "r+b") as g:
            g.seek(off); shutil.copyfileobj(s, g, 1 << 22)
        return dict(fat="FAT32", sector=4096, serial="%04X-%04X" % (serial >> 16, serial & 0xffff), files=len(b),
                    rebuilt_from="FAT32" if fat32 else "FAT16")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def convert(raw, out, name="kiwi-b150g", keep_esp=False):
    size = os.path.getsize(raw)
    assert size % BLK == 0, "raw size is not a multiple of 4096"
    nbl = size // BLK
    g = D.parse_gpt(reader(raw), nbl)
    parts = sorted(g["parts"], key=lambda p: p["n"])
    assert [p["n"] for p in parts] == [1, 2, 3], "want partitions 1..3, have %r" % [p["n"] for p in parts]
    assert [p["type"] for p in parts] == TYPES, "partition types %r (want ESP, XBOOTLDR, root-arm64)" % [p["type"] for p in parts]
    fs = check_fs(raw, parts)
    last = parts[2]["last"]
    os.makedirs(out, exist_ok=True)
    body, tail = os.path.join(out, name + ".body"), os.path.join(out, name + ".tail")
    primary, backup = D.make_gpt(nbl, [(t, p["uuid"], p["first"], p["last"], nm) for t, p, nm in zip(TYPES, parts, NAMES)], g["disk_guid"])
    body_len = (last + 1) * BLK
    with open(raw, "rb") as s, open(body + ".part", "wb") as d:
        left = body_len; z = bytes(1 << 20)
        while left:
            c = s.read(min(left, 1 << 20)); assert c
            if c == z[:len(c)]:
                d.seek(len(c), 1)            # keep holes
            else:
                d.write(c)
            left -= len(c)
        d.truncate(body_len)
        d.seek(0); d.write(primary)
    os.replace(body + ".part", body)
    open(tail, "wb").write(backup)
    esp = {"fat": fs["esp_fat"], "sector": fs["esp_sector"], "kept": True} if keep_esp else rebuild_esp(body, parts[0])
    meta = dict(what="OnePlus Pad 4 GENERIC install image built on a PC with kiwi (B150g content), golden format",
                source=os.path.basename(raw), size=size, block=BLK, body=os.path.basename(body), tail=os.path.basename(tail),
                body_len=body_len, tail_len=len(backup), disk_guid=g["disk_guid"],
                partitions=[dict(n=p["n"], type=t, uuid=p["uuid"], first=p["first"], last=p["last"], name=nm,
                                 bytes=(p["last"] - p["first"] + 1) * BLK, offset=p["first"] * BLK) for t, p, nm in zip(TYPES, parts, NAMES)],
                esp=esp, btrfs_total=fs["btrfs_total"], body_sha256=D.sha256_file(body), tail_sha256=D.sha256_file(tail), private=False)
    j = os.path.join(out, name + ".json")
    json.dump(meta, open(j, "w"), indent=1)
    g2 = D.parse_gpt(D.Disk(j, readonly=True).read, nbl)          # proof: reads back through the project's own reader
    assert [(p["type"], p["uuid"], p["first"], p["last"], p["name"]) for p in g2["parts"]] == \
        [(t, p["uuid"], p["first"], p["last"], nm) for t, p, nm in zip(TYPES, parts, NAMES)]
    return j, meta


def selftest():
    w = tempfile.mkdtemp(prefix="k2g."); ok = True

    def t(n, c):
        nonlocal ok
        ok &= bool(c); print(("PASS " if c else "FAIL ") + n)
    nbl = 8192
    parts = [(D.TYPE_ESP, "11111111-2222-3333-4444-555555555555", 256, 511, "p.UEFI"),
             (D.TYPE_XBOOTLDR, "21111111-2222-3333-4444-555555555555", 512, 1023, "p.lxboot"),
             (D.TYPE_ROOT_ARM64, "31111111-2222-3333-4444-555555555555", 1024, 8186, "p.lxroot")]
    pri, bak = D.make_gpt(nbl, parts, "41111111-2222-3333-4444-555555555555")
    img = bytearray(nbl * BLK); img[:len(pri)] = pri; img[-len(bak):] = bak
    sb = 512 * BLK + 1024; struct.pack_into("<I", img, sb + 24, 2); struct.pack_into("<H", img, sb + 56, 0xEF53)
    rb = 1024 * BLK + 0x10000; img[rb + 0x40:rb + 0x48] = b"_BHRfS_M"; struct.pack_into("<Q", img, rb + 0x70, 4096 * 7000); struct.pack_into("<I", img, rb + 0x90, 4096)
    for b in range(1025, 8187, 97):
        struct.pack_into("<I", img, b * BLK + 8, b)
    raw = os.path.join(w, "k.raw"); open(raw, "wb").write(img)
    j, m = convert(raw, w, "g", keep_esp=True)
    t("3 partitions renamed to B149's names, types and GUIDs kept", [p["name"] for p in m["partitions"]] == NAMES)
    bd = open(os.path.join(w, "g.body"), "rb").read()
    t("body ends at the root partition's end", len(bd) == 8187 * BLK)
    t("data beyond the partition table unchanged", all(struct.unpack_from("<I", bd, b * BLK + 8)[0] == b for b in range(1025, 8187, 97)))
    bad = bytearray(img); pr2, bk2 = D.make_gpt(nbl, [parts[0], parts[1], (D.TYPE_ESP,) + parts[2][1:]], "41111111-2222-3333-4444-555555555555")
    bad[:len(pr2)] = pr2; bad[-len(bk2):] = bk2; open(raw, "wb").write(bad)
    try:
        convert(raw, w, "bad", keep_esp=True); r = False
    except AssertionError:
        r = True
    t("a root partition of the wrong type is refused", r)
    open(raw, "wb").write(bytes(img[:4096 * 3]) + bytes(4096 * (nbl - 3)))
    try:
        convert(raw, w, "bad2", keep_esp=True); r = False
    except AssertionError:
        r = True
    t("a disk without a valid 4 KiB GPT is refused", r)
    shutil.rmtree(w)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL")); return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        sys.exit(selftest())
    nm = a[a.index("--name") + 1] if "--name" in a else "kiwi-b150g"
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and not (i > 0 and a[i - 1] == "--name")]
    if len(pos) != 2:
        print(__doc__); sys.exit(2)
    j, m = convert(pos[0], pos[1], nm, "--keep-esp" in a)
    print("kiwi2golden: %s (%d bytes, body %d, ESP %s/%s) body sha256 %s" % (j, m["size"], m["body_len"], m["esp"]["fat"], m["esp"]["sector"], m["body_sha256"][:16]))

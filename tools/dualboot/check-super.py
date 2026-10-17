#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dual boot: independent check of a sparse super image (PC only, reads only).
  check-super.py SUPER.img IMG_DIR
Re-reads the sparse file (header, chunk sizes, total = the super partition), rebuilds the first MiB, checks the LP
geometry + both copies of every metadata slot (header and table sha256), lists the partitions, then reads every
partition's bytes back out of the sparse image by its extent and compares the sha256 with the source image (the
padding after an image must be zeros). One PASS/FAIL line each; last line SUPER-CHECK: N failure(s)."""
import hashlib, os, struct, sys

S, IMGS = sys.argv[1:3]
B = 4096
fails = 0


def t(name, ok):
    global fails
    print(("PASS " if ok else "FAIL ") + name)
    fails += 0 if ok else 1


f = open(S, "rb")
magic, maj, mnr, fhs, chs, bs, tb, tc, _ = struct.unpack("<IHHHHIIII", f.read(28))
t("sparse header (magic, v1.0, 28 / 12, 4096-byte blocks)", (magic, maj, fhs, chs, bs) == (0xED26FF3A, 1, 28, 12, B))
t("sparse total = super partition 14,612,955,136 B", tb * B == 14612955136)
# chunk map: list of (first block, nblocks, file offset or None)
cmap, blk = [], 0
for i in range(tc):
    ct, _, nb, tot = struct.unpack("<HHII", f.read(12))
    if ct == 0xCAC1:
        cmap.append((blk, nb, f.tell()))
        assert tot == 12 + nb * B
        f.seek(nb * B, 1)
    elif ct == 0xCAC3:
        cmap.append((blk, nb, None))
        assert tot == 12
    else:
        raise SystemExit("unexpected chunk type %x" % ct)
    blk += nb
t("chunks cover exactly the partition (%d chunks)" % tc, blk == tb)


def read(byte_off, n):
    out = bytearray()
    while n:
        b0 = byte_off // B
        for start, nb, fo in cmap:
            if start <= b0 < start + nb:
                inside = byte_off - start * B
                k = min(n, (start + nb) * B - byte_off)
                if fo is None:
                    out += bytes(k)
                else:
                    f.seek(fo + inside)
                    out += f.read(k)
                byte_off += k
                n -= k
                break
        else:
            raise SystemExit("offset outside the image")
    return bytes(out)


g = read(B, 52)
gm, gs = struct.unpack_from("<II", g, 0)
mms, slots, lbs = struct.unpack_from("<III", g, 40)
gg = bytearray(read(B, gs)); chk = bytes(gg[8:40]); gg[8:40] = bytes(32)
t("geometry: magic, checksum, 65536 x 3 slots, 4096", gm == 0x616C4467 and hashlib.sha256(gg).digest() == chk and (mms, slots, lbs) == (65536, 3, 4096))
t("geometry backup copy equal", read(B, B) == read(2 * B, B))
metas = []
for copy in (0, 1):
    for s in range(slots):
        o = 3 * B + copy * slots * mms + s * mms
        hd = read(o, 256)
        m, ma, mi, hs = struct.unpack_from("<IHHI", hd, 0)
        if s == 2:
            t("metadata slot 2 (%s) empty, as today" % ("backup" if copy else "primary"), m == 0)
            continue
        hh = bytearray(hd[:hs]); hc = bytes(hh[12:44]); hh[12:44] = bytes(32)
        ts = struct.unpack_from("<I", hd, 44)[0]
        tab = read(o + hs, ts)
        ok = m == 0x414C5030 and (ma, mi, hs) == (10, 2, 256) and hashlib.sha256(hh).digest() == hc and hashlib.sha256(tab).digest() == hd[48:80]
        t("metadata slot %d (%s): v10.2, header + table checksums" % (s, "backup" if copy else "primary"), ok)
        metas.append(hd[:hs] + tab)
t("all four metadata copies identical", len(set(metas)) == 1)
hd = metas[0][:256]; tab = metas[0][256:]
d = struct.unpack_from("<12I", hd, 80)
t("header flag VIRTUAL_AB (1)", struct.unpack_from("<I", hd, 128)[0] == 1)
parts = [struct.unpack_from("<36sIIII", tab, d[0] + i * d[2]) for i in range(d[1])]
exts = [struct.unpack_from("<QIQI", tab, d[3] + i * d[5]) for i in range(d[4])]
grps = [struct.unpack_from("<36sIQ", tab, d[6] + i * d[8]) for i in range(d[7])]
dev = struct.unpack_from("<QIIQ36sI", tab, d[9])
t("block device super, 14,612,955,136 B, data from sector 2048", dev[4].rstrip(b"\0") == b"super" and dev[3] == 14612955136 and dev[0] == 2048)
t("groups: default + qti_dynamic_partitions_b", [g[0].rstrip(b"\0") for g in grps] == [b"default", b"qti_dynamic_partitions_b"])
used = []
for name, attr, fe, ne, gi in parts:
    n = name.rstrip(b"\0").decode()
    base = n[:-2]
    img = os.path.join(IMGS, base + ".img")
    sec, tt, start, src = exts[fe]
    ok = ne == 1 and tt == 0 and src == 0 and gi == 1 and attr == 1 and n.endswith("_b") and start % 2048 == 0 and start >= 2048
    isz = os.path.getsize(img)
    data = read(start * 512, sec * 512)
    same = hashlib.sha256(data[:isz]).digest() == hashlib.sha256(open(img, "rb").read()).digest() and not any(data[isz:])
    t("%-14s extent %d+%d sectors, readonly, group b; bytes = %s.img (%d B)" % (n, start, sec, base, isz), ok and same)
    used.append((start, start + sec))
used.sort()
t("extents do not overlap and stay inside super", all(a[1] <= b[0] for a, b in zip(used, used[1:])) and used[-1][1] * 512 <= dev[3])
t("seven partitions, no -cow, no slot-a names", len(parts) == 7 and not any(b"cow" in p[0] or p[0].rstrip(b"\0").endswith(b"_a") for p in parts))
print("SUPER-CHECK: %d failure(s)" % fails)

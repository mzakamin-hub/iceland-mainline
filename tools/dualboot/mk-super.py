#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dual boot: a `super` image (Android sparse format) for ABL's `fastboot flash super`, holding BlissROM's
seven dynamic partitions for slot b. PC only, writes files only.

  mk-super.py SUPER_HEAD_COPY IMG_DIR OUT.img

SUPER_HEAD_COPY = the first 1 MiB of the tablet's super, read before the change: its geometry and block device are reused
byte for byte (metadata_max_size 65536, 3 slots, logical block 4096, super 14,612,955,136 B, data from sector 2048,
alignment 524288 / offset 81920 as recorded). New metadata (liblp v10.2, header flag VIRTUAL_AB as today):
  groups  default, qti_dynamic_partitions_b (maximum = today's 14,608,760,832 B)
  parts   odm_b product_b system_b system_dlkm_b system_ext_b vendor_b vendor_dlkm_b (attribute READONLY), one extent
          each, packed from sector 2048 upwards, every start aligned to 1 MiB; no -cow partitions, no slot-a names
  slots   metadata slot 0 and slot 1 = this metadata, slot 2 empty (as today); the backup copies after the primary ones
Data = the seven raw images at their extents. Sparse: RAW chunks of at most 64 MiB, DONT_CARE elsewhere (the old
contents of super outside the metadata and the new extents are not erased; nothing reads them)."""
import hashlib, os, struct, sys

HEAD, IMGS, OUT = sys.argv[1:4]
B = 4096
PARTS = ["odm", "product", "system", "system_dlkm", "system_ext", "vendor", "vendor_dlkm"]
SUFFIX = "_b"
GROUP = "qti_dynamic_partitions_b"
ATTR_READONLY = 1
FLAG_VAB = 1

h = open(HEAD, "rb").read()
assert len(h) >= 1 << 20
geo = h[B:2 * B]
gmagic, gsize = struct.unpack_from("<II", geo, 0)
assert gmagic == 0x616C4467 and gsize == 52, "no LP geometry"
mms, slots, lbs = struct.unpack_from("<III", geo, 40)
assert (mms, slots, lbs) == (65536, 3, 4096), (mms, slots, lbs)
assert h[B:2 * B] == h[2 * B:3 * B], "geometry backup differs"
# today's block device entry (from metadata slot 1, the running slot b)
off = 3 * B + 1 * mms
hs = struct.unpack_from("<I", h, off + 8)[0]
desc = struct.unpack_from("<12I", h, off + 80)
dev = h[off + hs + desc[9]: off + hs + desc[9] + desc[11]]
first_sec, align, align_off, size, dname, dflags = struct.unpack_from("<QIIQ36sI", dev, 0)
assert dname.rstrip(b"\0") == b"super" and size == 14612955136 and first_sec == 2048, (dname, size, first_sec)
grp_max = 14608760832

imgs = []
for p in PARTS:
    f = os.path.join(IMGS, p + ".img")
    n = os.path.getsize(f)
    with open(f, "rb") as fh:
        assert fh.read(4) != struct.pack("<I", 0xED26FF3A), f + " is sparse; a raw image is expected"
    imgs.append((p, f, n))

MB_SEC = (1 << 20) // 512
sec = first_sec
extents = []
for p, f, n in imgs:
    nsec = -(-n // B) * (B // 512)          # whole 4 KiB blocks, in 512-byte sectors
    sec = -(-sec // MB_SEC) * MB_SEC          # 1 MiB aligned start
    extents.append((p, f, n, nsec, sec))
    sec += nsec
end_bytes = sec * 512
assert end_bytes <= size and end_bytes - first_sec * 512 <= grp_max, "does not fit"


def name36(s):
    b = s.encode()
    assert len(b) < 36
    return b.ljust(36, b"\0")


parts_t = b"".join(struct.pack("<36sIIII", name36(p + SUFFIX), ATTR_READONLY, i, 1, 1)
                   for i, (p, f, n, nsec, start) in enumerate(extents))
ext_t = b"".join(struct.pack("<QIQI", nsec, 0, start, 0) for (p, f, n, nsec, start) in extents)
grp_t = struct.pack("<36sIQ", name36("default"), 0, 0) + struct.pack("<36sIQ", name36(GROUP), 0, grp_max)
dev_t = dev[:64]
tables = parts_t + ext_t + grp_t + dev_t
po, eo, go, do = 0, len(parts_t), len(parts_t) + len(ext_t), len(parts_t) + len(ext_t) + len(grp_t)
hdr = bytearray(256)
struct.pack_into("<IHHI", hdr, 0, 0x414C5030, 10, 2, 256)
struct.pack_into("<I", hdr, 44, len(tables))
hdr[48:80] = hashlib.sha256(tables).digest()
struct.pack_into("<12I", hdr, 80, po, len(extents), 52, eo, len(extents), 24, go, 2, 48, do, 1, 64)
struct.pack_into("<I", hdr, 128, FLAG_VAB)
hdr[12:44] = hashlib.sha256(bytes(hdr)).digest()     # with the checksum field still zero
meta = bytes(hdr) + tables
assert len(meta) <= mms

# the first 1 MiB of the new super: reserved 4 KiB (zeros, as today), geometry x2 (today's bytes), metadata slots
head = bytearray(first_sec * 512)
head[0:B] = h[0:B]
head[B:3 * B] = h[B:3 * B]
for copy in (0, 1):                 # primary, then backup
    for s in range(slots):
        o = 3 * B + copy * slots * mms + s * mms
        head[o:o + mms] = (meta if s < 2 else bytes(0)).ljust(mms, b"\0")

# ---- sparse writer ----
CH = 64 << 20
chunks = []                         # (type, nblocks, payload source)
pos = 0                             # in blocks


def raw(nblk, src):
    chunks.append(("raw", nblk, src))


def skip(nblk):
    if nblk:
        chunks.append(("skip", nblk, None))


raw(len(head) // B, ("bytes", bytes(head)))
pos = len(head) // B
for p, f, n, nsec, start in extents:
    sb = start * 512 // B
    skip(sb - pos)
    nb = nsec * 512 // B
    o = 0
    while o < nb:
        k = min(CH // B, nb - o)
        raw(k, ("file", f, o * B, k * B, n))
        o += k
    pos = sb + nb
total_blocks = size // B
skip(total_blocks - pos)

with open(OUT, "wb") as w:
    w.write(struct.pack("<IHHHHIIII", 0xED26FF3A, 1, 0, 28, 12, B, total_blocks, len(chunks), 0))
    for typ, nb, src in chunks:
        if typ == "skip":
            w.write(struct.pack("<HHII", 0xCAC3, 0, nb, 12))
            continue
        w.write(struct.pack("<HHII", 0xCAC1, 0, nb, 12 + nb * B))
        if src[0] == "bytes":
            w.write(src[1])
        else:
            _, f, o, ln, n = src
            with open(f, "rb") as fh:
                fh.seek(o)
                data = fh.read(ln)
            w.write(data.ljust(ln, b"\0"))      # the last block of an image padded with zeros
print("super image:", OUT)
print("metadata sha256 %s, %d B; flags VIRTUAL_AB; group %s max %d" % (hashlib.sha256(meta).hexdigest(), len(meta), GROUP, grp_max))
for p, f, n, nsec, start in extents:
    print("  %-14s start sector %10d  %10d sectors  %12d B image" % (p + SUFFIX, start, nsec, n))
print("used %d B of %d (%.2f GiB of %.2f)" % (end_bytes, size, end_bytes / 2**30, size / 2**30))
print("sparse: %d blocks, %d chunks" % (total_blocks, len(chunks)))

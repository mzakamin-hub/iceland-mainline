#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""The file that is later written to the tablet's userdata: a golden disk as an Android sparse image (v1.0,
4096-byte blocks, total size = the userdata partition). PC only.

  mk-sparse.py DISK.json OUT.sparse.img          write, then read back and compare (exit 1 on any difference)
  mk-sparse.py --check DISK.json IMG.sparse.img  only the read-back comparison

Chunks: [0, body) -> RAW for data and FILL(0) for runs of zero blocks, so EVERY block of the partition table,
the EFI partition, /boot and the root is written (zeros included: a free FAT cluster or an ext4 bitmap is
zeros that must reach the tablet); [body, tail) -> DONT_CARE (no partition there until the root grows into it;
the tablet keeps what is there); tail (backup GPT) -> RAW. No CRC chunks.
The read-back expands the sparse image block by block and compares every block of [0, body) and the tail
with the disk, and the chunk map of the gap; it prints the sha256 of the sparse file for the guide's record.
"""
import hashlib, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iceland_disk as D

MAGIC = 0xed26ff3a
RAW, FILL, DONT_CARE, CRC = 0xCAC1, 0xCAC2, 0xCAC3, 0xCAC4
BLK = D.BLK
RUN = 1024   # blocks per RAW chunk at most (4 MiB)


def write(meta, out):
    disk = D.Disk(meta, readonly=True)
    nbl = disk.size // BLK
    body_bl = disk.body_len // BLK
    tail_bl0 = disk.tail_start // BLK
    chunks = 0
    with open(out + ".part", "wb") as f:
        f.write(bytes(28))  # header, filled at the end

        def raw(b0, data):
            nonlocal chunks
            f.write(struct.pack("<HHII", RAW, 0, len(data) // BLK, 12 + len(data))); f.write(data); chunks += 1

        def fill(n):
            nonlocal chunks
            f.write(struct.pack("<HHIII", FILL, 0, n, 16, 0)); chunks += 1

        def dont_care(n):
            nonlocal chunks
            f.write(struct.pack("<HHII", DONT_CARE, 0, n, 12)); chunks += 1

        b = 0
        pend_raw, pend_raw_b0, zeros = bytearray(), 0, 0
        while b < body_bl:
            n = min(256, body_bl - b)
            data = disk.read(b * BLK, n * BLK)
            for i in range(n):
                blk = data[i * BLK:(i + 1) * BLK]
                if blk.count(0) == BLK:
                    if pend_raw:
                        raw(pend_raw_b0, bytes(pend_raw)); pend_raw = bytearray()
                    zeros += 1
                else:
                    if zeros:
                        fill(zeros); zeros = 0
                    if not pend_raw:
                        pend_raw_b0 = b + i
                    pend_raw += blk
                    if len(pend_raw) >= RUN * BLK:
                        raw(pend_raw_b0, bytes(pend_raw)); pend_raw = bytearray()
            b += n
        if pend_raw:
            raw(pend_raw_b0, bytes(pend_raw))
        if zeros:
            fill(zeros)
        if tail_bl0 > body_bl:
            dont_care(tail_bl0 - body_bl)
        raw(tail_bl0, disk.read(disk.tail_start, disk.tail_len))
        f.seek(0)
        f.write(struct.pack("<IHHHHIIII", MAGIC, 1, 0, 28, 12, BLK, nbl, chunks, 0))
    os.replace(out + ".part", out)
    return chunks


def check(meta, img):
    disk = D.Disk(meta, readonly=True)
    h = hashlib.sha256()
    with open(img, "rb") as f:
        hdr = f.read(28)
        magic, ma, mi, fh, ch, bs, total, nch, _ = struct.unpack("<IHHHHIIII", hdr)
        assert magic == MAGIC and ma == 1 and fh == 28 and ch == 12 and bs == BLK, "not a v1 sparse image with 4 KiB blocks"
        assert total * BLK == disk.size, "sparse size %d != disk size %d" % (total * BLK, disk.size)
        b = 0
        kinds = dict(raw=0, fill=0, dont_care=0)
        for _ in range(nch):
            ctype, _, cbl, csz = struct.unpack("<HHII", f.read(12))
            if ctype == RAW:
                data = f.read(cbl * BLK)
                assert data == disk.read(b * BLK, cbl * BLK), "RAW chunk differs at block %d" % b
                kinds["raw"] += cbl
            elif ctype == FILL:
                val = f.read(4)
                assert val == bytes(4)
                assert disk.read(b * BLK, cbl * BLK).count(0) == cbl * BLK, "FILL chunk over data at block %d" % b
                kinds["fill"] += cbl
            elif ctype == DONT_CARE:
                assert b * BLK >= disk.body_len and (b + cbl) * BLK <= disk.tail_start, "DONT_CARE outside the gap"
                kinds["dont_care"] += cbl
            else:
                raise AssertionError("unexpected chunk type %x" % ctype)
            b += cbl
        assert b == total, "chunks cover %d of %d blocks" % (b, total)
        covered = (kinds["raw"] + kinds["fill"]) * BLK
        assert covered == disk.body_len + disk.tail_len, "written blocks %d != body + tail" % covered
        f.seek(0)
        while True:
            d = f.read(1 << 22)
            if not d:
                break
            h.update(d)
    return dict(sparse=os.path.basename(img), sparse_bytes=os.path.getsize(img), sparse_sha256=h.hexdigest(),
                unpacked_bytes=disk.size, chunks=nch, blocks=kinds)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--check":
        print(json.dumps(check(sys.argv[2], sys.argv[3]), indent=1))
    elif len(sys.argv) == 3:
        n = write(sys.argv[1], sys.argv[2])
        r = check(sys.argv[1], sys.argv[2])
        json.dump(r, open(sys.argv[2] + ".json", "w"), indent=1)
        print(json.dumps(r, indent=1))
    else:
        sys.exit(__doc__)

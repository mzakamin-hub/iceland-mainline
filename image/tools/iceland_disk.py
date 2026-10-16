#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""OnePlus Pad 4 install workflow: the disk image as the PC keeps it, and the 4 KiB GPT.

A "golden" disk is three files (written by mk-golden.py, never by anything on the tablet):
  NAME.body   bytes [0, body_len) of the disk: GPT, EFI partition, /boot, the btrfs root (12.8 GB)
  NAME.tail   the last bytes of the disk: the backup GPT (entries + header, 5 blocks of 4096)
  NAME.json   virtual size (= the size of the tablet's userdata partition), body_len, tail_len, checksums
Everything between body and tail reads as zeros and is "don't care" in the sparse image (the tablet keeps
whatever is there; no partition covers it until the root grows into it on the first boot).

An optional OVERLAY directory holds copy-on-write changes (rehearsal boots): cow.log (4 KiB blocks, append
only) and cow.idx (block number -> log offset, -1 = zeros). The base files are never written in overlay mode,
so the file that is later written to the tablet stays byte-identical to the one that was rehearsed.

Pure Python 3 (Linux or Windows), no root, no other tools.
"""
import hashlib, json, os, struct, uuid, zlib

BLK = 4096
GPT_ENTRIES = 128
ENTRY_SIZE = 128
ENTRY_BLOCKS = GPT_ENTRIES * ENTRY_SIZE // BLK      # 4 blocks of 4096
TYPE_ESP = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
TYPE_XBOOTLDR = "bc13c2ff-59e6-4262-a352-b275fd6f7172"
TYPE_ROOT_ARM64 = "b921b045-1df0-41c3-af44-4c6f280d3fae"
ZERO = bytes(BLK)


def guid_bytes(s):
    return uuid.UUID(s).bytes_le


def guid_str(b):
    return str(uuid.UUID(bytes_le=bytes(b)))


def make_gpt(nblocks, parts, disk_guid):
    """GPT for a disk of nblocks 4096-byte blocks. parts = [(type, unique, first, last, name)] (block units).
    Returns (primary bytes for blocks 0..5, backup bytes for blocks nblocks-5..nblocks-1)."""
    assert nblocks > 2 * (2 + ENTRY_BLOCKS)
    first_usable = 2 + ENTRY_BLOCKS
    last_usable = nblocks - 2 - ENTRY_BLOCKS
    ents = bytearray(GPT_ENTRIES * ENTRY_SIZE)
    for i, (ptype, uniq, first, last, name) in enumerate(parts):
        assert first_usable <= first <= last <= last_usable, (name, first, last, first_usable, last_usable)
        nm = name.encode("utf-16-le")[:72].ljust(72, b"\0")
        struct.pack_into("<16s16sQQQ72s", ents, i * ENTRY_SIZE, guid_bytes(ptype), guid_bytes(uniq), first, last, 0, nm)
    ent_crc = zlib.crc32(ents) & 0xffffffff

    def header(my, alt, ent_lba):
        h = bytearray(92)
        struct.pack_into("<8sIIIIQQQQ16sQIII", h, 0, b"EFI PART", 0x00010000, 92, 0, 0, my, alt,
                         first_usable, last_usable, guid_bytes(disk_guid), ent_lba, GPT_ENTRIES, ENTRY_SIZE, ent_crc)
        struct.pack_into("<I", h, 16, zlib.crc32(h) & 0xffffffff)
        return bytes(h).ljust(BLK, b"\0")

    pmbr = bytearray(BLK)
    # protective MBR: one 0xee partition from LBA 1 over the whole disk (capped at 0xffffffff)
    struct.pack_into("<B3sB3sII", pmbr, 446, 0, b"\x00\x02\x00", 0xEE, b"\xff\xff\xff", 1, min(nblocks - 1, 0xFFFFFFFF))
    pmbr[510:512] = b"\x55\xaa"
    primary = bytes(pmbr) + header(1, nblocks - 1, 2) + bytes(ents)
    backup = bytes(ents) + header(nblocks - 1, 1, nblocks - 1 - ENTRY_BLOCKS)
    assert len(primary) == (2 + ENTRY_BLOCKS) * BLK and len(backup) == (1 + ENTRY_BLOCKS) * BLK
    return primary, backup


def parse_gpt(read, nblocks=None):
    """Read a 4096-byte-block GPT through read(offset, length). Checks both CRCs. Returns dict."""
    pm = read(0, BLK)
    assert pm[510:512] == b"\x55\xaa" and pm[446 + 4] == 0xEE, "no protective MBR"
    h = read(BLK, 92)
    sig, rev, hsize, hcrc, _, my, alt, fu, lu, dg, el, ne, es, ecrc = struct.unpack("<8sIIIIQQQQ16sQIII", h)
    assert sig == b"EFI PART", "no GPT header at block 1 (4 KiB units)"
    hh = bytearray(h)
    struct.pack_into("<I", hh, 16, 0)
    assert zlib.crc32(hh) & 0xffffffff == hcrc, "GPT header CRC"
    ents = read(el * BLK, ne * es)
    assert zlib.crc32(ents) & 0xffffffff == ecrc, "GPT entries CRC"
    parts = []
    for i in range(ne):
        t, u, f, l, a, n = struct.unpack_from("<16s16sQQQ72s", ents, i * es)
        if t == bytes(16):
            continue
        parts.append(dict(n=i + 1, type=guid_str(t), uuid=guid_str(u), first=f, last=l,
                          name=n.decode("utf-16-le").rstrip("\0")))
    if nblocks is not None:
        assert alt == nblocks - 1, "backup header not at the last block (%d != %d)" % (alt, nblocks - 1)
    return dict(my=my, alt=alt, first_usable=fu, last_usable=lu, disk_guid=guid_str(dg), parts=parts)


class Disk:
    """Read (and in overlay / base mode write) a golden disk. 4096-byte blocks."""

    def __init__(self, meta_json, overlay=None, readonly=False):
        self.meta = json.load(open(meta_json))
        d = os.path.dirname(os.path.abspath(meta_json))
        self.size = self.meta["size"]
        self.body_len = self.meta["body_len"]
        self.tail_len = self.meta["tail_len"]
        assert self.size % BLK == 0 and self.body_len % BLK == 0 and self.tail_len % BLK == 0
        assert self.body_len + self.tail_len <= self.size
        mode = "rb" if (readonly or overlay) else "r+b"
        self.body = open(os.path.join(d, self.meta["body"]), mode)
        self.tail = open(os.path.join(d, self.meta["tail"]), mode)
        self.readonly = readonly
        self.ov = None
        self.dirty = False
        if overlay:
            # raw descriptors: appends with O_APPEND (one write per request), reads with pread; no buffered seek
            os.makedirs(overlay, exist_ok=True)
            fl = os.O_RDONLY if readonly else (os.O_RDWR | os.O_CREAT | os.O_APPEND)
            self.ov_fd = os.open(os.path.join(overlay, "cow.log"), fl | getattr(os, "O_BINARY", 0), 0o600)
            self.ov_end = os.fstat(self.ov_fd).st_size
            self.ov_idx_path = os.path.join(overlay, "cow.idx")
            self.ov = {}
            if os.path.exists(self.ov_idx_path):
                raw = open(self.ov_idx_path, "rb").read()
                for i in range(0, len(raw) - len(raw) % 16, 16):
                    b, off = struct.unpack_from("<qq", raw, i)
                    self.ov[b] = off
            self.idx_fd = None if readonly else os.open(self.ov_idx_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0), 0o600)
        self.tail_start = self.size - self.tail_len

    # ---- base access (no overlay) ----
    def _base_read_block(self, b):
        off = b * BLK
        if off < self.body_len:
            self.body.seek(off)
            d = self.body.read(BLK)
            return d.ljust(BLK, b"\0")
        if off >= self.tail_start:
            self.tail.seek(off - self.tail_start)
            return self.tail.read(BLK).ljust(BLK, b"\0")
        return ZERO

    def _base_write_block(self, b, data):
        off = b * BLK
        if off < self.body_len:
            self.body.seek(off); self.body.write(data); return
        if off >= self.tail_start:
            self.tail.seek(off - self.tail_start); self.tail.write(data); return
        if data == ZERO:
            return   # zeros over the don't-care gap: nothing to keep
        raise IOError("write at block %d outside body and tail (base mode); a rehearsal needs an overlay" % b)

    # ---- block level with the overlay ----
    def _ov_pread(self, off, n):
        if hasattr(os, "pread"):
            return os.pread(self.ov_fd, n, off)
        os.lseek(self.ov_fd, off, 0)
        return os.read(self.ov_fd, n)

    def read_block(self, b):
        if self.ov is not None and b in self.ov:
            off = self.ov[b]
            if off < 0:
                return ZERO
            return self._ov_pread(off, BLK)
        return self._base_read_block(b)

    def _ov_put(self, b0, data):
        """overlay: len(data) // BLK whole blocks from block b0, appended in one write, indexed in one write"""
        n = len(data) // BLK
        base = self.ov_end
        os.write(self.ov_fd, data)
        self.ov_end += len(data)
        ent = bytearray()
        for i in range(n):
            self.ov[b0 + i] = base + i * BLK
            ent += struct.pack("<qq", b0 + i, base + i * BLK)
        os.write(self.idx_fd, bytes(ent))
        self.dirty = True

    def write_block(self, b, data, zero=False):
        assert not self.readonly and len(data) == BLK
        if self.ov is None:
            self.dirty = True
            return self._base_write_block(b, ZERO if zero else data)
        if zero:
            self.ov[b] = -1
            os.write(self.idx_fd, struct.pack("<qq", b, -1))
            self.dirty = True
        else:
            self._ov_put(b, data)

    def zero(self, offset, length):
        """TRIM / WRITE_ZEROES: the range reads back as zeros. No buffer of the range's size: partial blocks are
        read-modified-written, whole blocks marked zero in the overlay index (one write), and whole blocks of the
        empty part between body and tail that the overlay never touched are already zero (nothing recorded)."""
        assert not self.readonly and 0 <= offset and offset + length <= self.size
        pos, end = offset, offset + length
        if pos % BLK and pos < end:                              # head: part of a block
            b = pos // BLK; s = pos - b * BLK; n = min(BLK - s, end - pos)
            cur = bytearray(self.read_block(b)); cur[s:s + n] = bytes(n); self.write_block(b, bytes(cur))
            pos += n
        if pos >= end:
            return
        b0, b1 = pos // BLK, end // BLK                          # whole blocks [b0, b1)
        if end % BLK:                                            # tail: part of a block
            n = end - b1 * BLK
            cur = bytearray(self.read_block(b1)); cur[:n] = bytes(n); self.write_block(b1, bytes(cur))
        if self.ov is None:
            for b in range(b0, b1):
                self._base_write_block(b, ZERO)
            self.dirty = True
            return
        gap0, gap1 = self.body_len // BLK, self.tail_start // BLK
        ent = bytearray()
        for b in range(b0, b1):
            if gap0 <= b < gap1 and b not in self.ov:
                continue
            if self.ov.get(b) == -1:
                continue
            self.ov[b] = -1
            ent += struct.pack("<qq", b, -1)
        if ent:
            os.write(self.idx_fd, bytes(ent))
            self.dirty = True

    # ---- byte level ----
    def read(self, offset, length):
        assert 0 <= offset and offset + length <= self.size, (offset, length)
        out = bytearray()
        b0, b1 = offset // BLK, (offset + length + BLK - 1) // BLK
        if (self.ov is None or not any(b in self.ov for b in range(b0, b1))) and b1 * BLK <= self.body_len:
            self.body.seek(b0 * BLK)   # fast path: one read from the body
            out = bytearray(self.body.read((b1 - b0) * BLK).ljust((b1 - b0) * BLK, b"\0"))
        else:
            for b in range(b0, b1):
                out += self.read_block(b)
        s = offset - b0 * BLK
        return bytes(out[s:s + length])

    def write(self, offset, data, zero=False):
        assert offset + len(data) <= self.size
        if zero:
            return self.zero(offset, len(data))
        pos, end = offset, offset + len(data)
        while pos < end:
            b = pos // BLK
            s = pos - b * BLK
            n = min(BLK - s, end - pos)
            if s == 0 and n == BLK and self.ov is not None:
                k = (end - pos) // BLK                           # the whole aligned run in one append
                run = data[pos - offset:pos - offset + k * BLK]
                gap0, gap1 = self.body_len // BLK, self.tail_start // BLK
                if gap0 <= b and b + k <= gap1 and not any(x in self.ov for x in range(b, b + k)) \
                        and bytes(run).count(0) == len(run):
                    pos += k * BLK                               # zeros over the untouched empty part: already zero
                    continue
                self._ov_put(b, bytes(run))
                pos += k * BLK
                continue
            if s == 0 and n == BLK:
                self.write_block(b, bytes(data[pos - offset:pos - offset + BLK]))
            else:
                cur = bytearray(self.read_block(b))
                cur[s:s + n] = data[pos - offset:pos - offset + n]
                self.write_block(b, bytes(cur))
            pos += n

    def flush(self):
        """make every completed write durable; a no-op when nothing changed since the last flush"""
        if self.readonly or not self.dirty:
            return
        sync = getattr(os, "fdatasync", os.fsync)
        if self.ov is None:
            for f in (self.body, self.tail):
                f.flush(); os.fsync(f.fileno())
        else:
            sync(self.ov_fd); sync(self.idx_fd)
        self.dirty = False

    def overlay_blocks(self):
        return 0 if self.ov is None else len(self.ov)


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            d = f.read(chunk)
            if not d:
                break
            h.update(d)
    return h.hexdigest()

#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dual boot: compute (never write to a device) the two partition-table changes of the dual boot, from saved
copies of the tables. PC only: reads files, writes the planned table blocks + a report into OUT_DIR.

  gpt-plan.py split  HEAD TAIL LUN_BLOCKS USERDATA_START OUT_DIR [--fedora-guid G] [--userdata-last LBA]
      LUN 0 (W3): userdata keeps its name, type, unique GUID and attributes and gets first_lba = USERDATA_START;
      a new entry "fedora" (Linux filesystem data) covers userdata's old start .. USERDATA_START-1. Every other
      entry, the protective MBR and the disk GUID stay byte-identical. --userdata-last LBA also ends userdata there
      (below the last usable block): the blocks after it stay unpartitioned (on the Pad 4 a boot-loader write lands
      at LUN block N-9 at slot-flag updates, which must not be Android's data).
  gpt-plan.py shrink HEAD TAIL DISK_BLOCKS NEW_BLOCKS OUT_DIR
      Fedora's inner disk (W2): the same table for a disk of NEW_BLOCKS: backup at the new end, last usable
      NEW-6, the partition that ended at the old last usable now ends at NEW-6 (it must still hold its file
      system: the caller shrinks btrfs first), the protective MBR's size NEW-1.

HEAD = a copy of the disk's first blocks (>= 6), TAIL = a copy of its last blocks (>= 5), block size 4096.
Outputs: head-new.bin (blocks 0-5), tail-new.bin (the last 5 blocks), head-old.bin / tail-old.bin (the undo, cut
from the inputs), REPORT.txt, SHA256SUMS. Refuses (exit 1) on any CRC error, primary / backup mismatch, an
unexpected layout or an overlap. The planned table is re-parsed and checked before anything is written out."""
import binascii, hashlib, os, struct, sys, uuid

BS = 4096
LINUX_DATA = "0fc63daf-8483-4772-8e79-3d69d8477de4"


def die(m):
    print("REFUSED: " + m)
    sys.exit(1)


def crc(b):
    return binascii.crc32(b) & 0xffffffff


def gstr(b):
    return str(uuid.UUID(bytes_le=bytes(b)))


def gbytes(s):
    return uuid.UUID(s).bytes_le


def parse_hdr(blk, my):
    if blk[:8] != b"EFI PART":
        die("no GPT header at block %d" % my)
    (rev, hsz, hcrc, _, mylba, alt, fu, lu, dg, elba, ne, esz, ecrc) = struct.unpack_from("<IIIIQQQQ16sQIII", blk, 8)
    h = bytearray(blk[:hsz]); struct.pack_into("<I", h, 16, 0)
    if crc(h) != hcrc:
        die("header CRC at block %d" % my)
    if mylba != my or esz != 128 or hsz != 92:
        die("header fields at block %d" % my)
    return dict(alt=alt, fu=fu, lu=lu, dg=dg, elba=elba, ne=ne, ecrc=ecrc, raw=bytes(blk[:BS]))


def mk_hdr(old_raw, my, alt, fu, lu, elba, ne, ecrc):
    h = bytearray(old_raw)
    struct.pack_into("<QQQQ", h, 24, my, alt, fu, lu)
    struct.pack_into("<Q", h, 72, elba)
    struct.pack_into("<I", h, 80, ne)
    struct.pack_into("<I", h, 88, ecrc)
    struct.pack_into("<I", h, 16, 0)
    struct.pack_into("<I", h, 16, crc(h[:92]))
    return bytes(h)


def entries(raw, ne):
    out = []
    for i in range(ne):
        e = raw[i * 128:(i + 1) * 128]
        t, u, f, l, a = struct.unpack_from("<16s16sQQQ", e)
        name = e[56:128].decode("utf-16le").split("\0")[0]
        out.append(dict(i=i, type=gstr(t), uniq=gstr(u), first=f, last=l, attr=a, name=name, raw=bytes(e),
                        used=t != bytes(16)))
    return out


TRUST_PRIMARY = False   # --trust-primary (shrink only): see load()


def load(head, tail, nblocks):
    hb, tb = open(head, "rb").read(), open(tail, "rb").read()
    if len(hb) < 6 * BS or len(tb) < 5 * BS:
        die("head needs >= 6 blocks, tail >= 5 blocks")
    tb = tb[-5 * BS:]   # the disk's last 5 blocks: N-5 .. N-1
    p = parse_hdr(hb[BS:2 * BS], 1)
    b = parse_hdr(tb[4 * BS:], nblocks - 1)
    if p["alt"] != nblocks - 1 or b["alt"] != 1:
        die("the headers do not point at each other for a disk of %d blocks" % nblocks)
    ebytes = p["ne"] * 128
    pe = hb[p["elba"] * BS:p["elba"] * BS + ebytes]
    if p["elba"] != 2 or len(pe) != ebytes or crc(pe) != p["ecrc"]:
        die("primary entries")
    off = (b["elba"] - (nblocks - 5)) * BS
    if off < 0 or off + ebytes > 4 * BS:
        die("backup entries not in the last 5 blocks")
    be = tb[off:off + ebytes]
    if pe != be and TRUST_PRIMARY:
        # accepted only when every differing byte lies in an entry that is unused in the primary (all-zero there)
        # and the backup header itself agrees with the primary; the new table is built from the primary alone
        bad = sorted({i // 128 for i in range(ebytes) if pe[i] != be[i]})
        if any(pe[k * 128:(k + 1) * 128] != bytes(128) for k in bad):
            die("backup entries differ inside a used entry: %s" % [k + 1 for k in bad])
        print("NOTE: backup entry array differs from the primary in unused entries %s only (stray bytes); "
              "the primary (CRC OK) is used" % [k + 1 for k in bad])
        be = pe
    if pe != be or b["ecrc"] != p["ecrc"] or (p["fu"], p["lu"], p["dg"]) != (b["fu"], b["lu"], b["dg"]):
        die("primary and backup tables differ")
    if p["lu"] != nblocks - 6 or p["fu"] != 6 or b["elba"] != nblocks - 5:
        die("unexpected geometry (first usable %d, last usable %d, backup entries %d)" % (p["fu"], p["lu"], b["elba"]))
    return hb[:6 * BS], tb, p, b, entries(pe, p["ne"])


def check_table(es, fu, lu):
    used = sorted((e for e in es if e["used"]), key=lambda e: e["first"])
    for e in used:
        if not (fu <= e["first"] <= e["last"] <= lu):
            die("entry %s outside the usable range" % e["name"])
    for a, b in zip(used, used[1:]):
        if b["first"] <= a["last"]:
            die("entries %s and %s overlap" % (a["name"], b["name"]))
    names = [e["name"] for e in used]
    if len(set(names)) != len(names):
        die("duplicate partition names")


def build(hb, tb, p, b, es, nblocks_new, mbr_size=None):
    ne = p["ne"]
    raw = b"".join(e["raw"] for e in es)
    ec = crc(raw)
    head = bytearray(hb)
    if mbr_size is not None:
        if head[510:512] != b"\x55\xaa" or head[450] != 0xEE:
            die("no protective MBR")
        struct.pack_into("<I", head, 446 + 12, min(mbr_size, 0xffffffff))
    head[BS:2 * BS] = mk_hdr(p["raw"], 1, nblocks_new - 1, 6, nblocks_new - 6, 2, ne, ec).ljust(BS, b"\0")[:BS]
    head[2 * BS:2 * BS + len(raw)] = raw
    tail = bytearray(tb) if b["elba"] == nblocks_new - 5 else bytearray(5 * BS)
    tail[:len(raw)] = raw
    tail[4 * BS:] = mk_hdr(b["raw"], nblocks_new - 1, 1, 6, nblocks_new - 6, nblocks_new - 5, ne, ec).ljust(BS, b"\0")[:BS]
    return bytes(head), bytes(tail)


def entry_raw(e):
    r = bytearray(128)
    struct.pack_into("<16s16sQQQ", r, 0, gbytes(e["type"]), gbytes(e["uniq"]), e["first"], e["last"], e["attr"])
    n = e["name"].encode("utf-16le"); r[56:56 + len(n)] = n
    return bytes(r)


def main():
    global TRUST_PRIMARY
    a = sys.argv[1:]
    TRUST_PRIMARY = "--trust-primary" in a and a[0] == "shrink"
    if len(a) < 6 or a[0] not in ("split", "shrink"):
        print(__doc__); sys.exit(2)
    mode, head, tail, n1, n2, out = a[0], a[1], a[2], int(a[3]), int(a[4]), a[5]
    fguid = a[a.index("--fedora-guid") + 1] if "--fedora-guid" in a else str(uuid.uuid4())
    ud_last = int(a[a.index("--userdata-last") + 1]) if "--userdata-last" in a else None
    hb, tb, p, b, es = load(head, tail, n1)
    check_table(es, p["fu"], p["lu"])
    rep = ["mode %s, disk %d blocks of %d B, %d entries (%d used)" % (mode, n1, BS, p["ne"], sum(e["used"] for e in es))]
    new = [dict(e) for e in es]
    if mode == "split":
        ud = [e for e in new if e["used"] and e["name"] == "userdata"]
        if len(ud) != 1:
            die("not exactly one userdata entry")
        ud = ud[0]
        if any(e["used"] and e["name"] == "fedora" for e in new):
            die("a fedora entry exists already")
        if ud["last"] != p["lu"] or max(e["last"] for e in new if e["used"]) != ud["last"]:
            die("userdata is not the last partition of the LUN")
        if not (ud["first"] < n2 <= ud["last"]) or n2 % 4096:
            die("USERDATA_START %d not inside userdata or not 16 MiB aligned" % n2)
        free = [e for e in new if not e["used"]]
        if not free:
            die("no free entry")
        old_first = ud["first"]
        ud["first"] = n2
        if ud_last is not None:
            if not (n2 + 1024 <= ud_last <= ud["last"]):
                die("--userdata-last %d not between USERDATA_START + 1024 and the last usable block" % ud_last)
            ud["last"] = ud_last
        ud["raw"] = entry_raw(ud)
        f = free[0]
        f.update(type=LINUX_DATA, uniq=fguid, first=old_first, last=n2 - 1, attr=0, name="fedora", used=True)
        f["raw"] = entry_raw(f)
        check_table(new, p["fu"], p["lu"])
        h2, t2 = build(hb, tb, p, b, new, n1)
        if h2[:512] != hb[:512]:
            die("protective MBR changed")
        nb_check = n1
        if ud_last is not None:
            rep.append("unpartitioned after userdata: LBA %d - %d (%d blocks)" % (ud_last + 1, p["lu"], p["lu"] - ud_last))
        rep.append("userdata: first LBA %d -> %d, last %d: %d blocks = %d B (%.3f GiB); name / type / unique GUID / attributes kept"
                   % (old_first, n2, ud["last"], ud["last"] - n2 + 1, (ud["last"] - n2 + 1) * BS, (ud["last"] - n2 + 1) * BS / 2 ** 30))
        rep.append("fedora (new entry %d): LBA %d - %d: %d blocks = %d B (%.3f GiB), type Linux filesystem data"
                   % (f["i"] + 1, old_first, n2 - 1, n2 - old_first, (n2 - old_first) * BS, (n2 - old_first) * BS / 2 ** 30))
    else:
        if not (1024 < n2 < n1):
            die("NEW_BLOCKS must be smaller than the disk")
        endp = [e for e in new if e["used"] and e["last"] == p["lu"]]
        if len(endp) != 1:
            die("not exactly one partition ends at the last usable block")
        e = endp[0]
        if e["first"] >= n2 - 6:
            die("the last partition would vanish")
        if any(x["used"] and x is not e and x["last"] > n2 - 6 for x in new):
            die("another partition lies beyond the new end")
        e["last"] = n2 - 6; e["raw"] = entry_raw(e)
        check_table(new, 6, n2 - 6)
        h2, t2 = build(hb, tb, p, b, new, n2, mbr_size=n2 - 1)
        nb_check = n2
        rep.append("partition %d (%s): last LBA %d -> %d (%d blocks = %d B); disk %d -> %d blocks; MBR size %d"
                   % (e["i"] + 1, e["name"] or "-", p["lu"], n2 - 6, n2 - 6 - e["first"] + 1, (n2 - 6 - e["first"] + 1) * BS, n1, n2, n2 - 1))
    # re-parse the planned blocks as a disk of nb_check blocks
    _, _, p2, _, es2 = load_bytes(h2, t2, nb_check)
    check_table(es2, p2["fu"], p2["lu"])
    changed = [i for i, (x, y) in enumerate(zip(es, es2)) if x["raw"] != y["raw"]]
    rep.append("entries changed: %s (every other entry byte-identical)" % [i + 1 for i in changed])
    if mode == "split" and len(changed) != 2:
        die("more than two entries changed")
    if mode == "shrink" and len(changed) != 1:
        die("more than one entry changed")
    os.makedirs(out, exist_ok=True)
    files = {"head-new.bin": h2, "tail-new.bin": t2, "head-old.bin": hb, "tail-old.bin": tb}
    for k, v in files.items():
        open(os.path.join(out, k), "wb").write(v)
    sums = ["%s  %s" % (hashlib.sha256(v).hexdigest(), k) for k, v in files.items()]
    open(os.path.join(out, "SHA256SUMS"), "w").write("\n".join(sums) + "\n")
    rep.append("head-new: %d B written at LBA 0; tail-new: %d B written at LBA %d (= byte %d)" % (len(h2), len(t2), nb_check - 5, (nb_check - 5) * BS))
    rep += sums
    rep.append("GPT-PLAN: OK")
    open(os.path.join(out, "REPORT.txt"), "w").write("\n".join(rep) + "\n")
    print("\n".join(rep))


def load_bytes(h, t, n):
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        open(d + "/h", "wb").write(h); open(d + "/t", "wb").write(t)
        return load(d + "/h", d + "/t", n)


if __name__ == "__main__":
    main()

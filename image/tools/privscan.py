#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""wf/generic/privscan/privscan.py - the privacy scan of a finished OnePlus Pad 4 install image (PC only, READ ONLY).
Must PASS before any image is published.

  privscan.py --golden RUN/NAME.json [--out DIR]     a golden (NAME.body + .json, as rehearsal-pc.sh commit writes it)
  privscan.py --raw FILE [--out DIR]                 a raw disk image (4 KiB GPT)
  privscan.py --sparse FILE --work DIR [--out DIR]   an Android sparse image (fedora-iceland.sparse.img): unpacked
                                                     into DIR as a raw file with holes first (needs ~14 GB real space)
  privscan.py --selftest                             the pattern / report logic against synthetic data (no root)
Needs root for the mounts (WSL: wsl.exe -u root -- python3 -I .../privscan.py ...). Every mount is a loop device made
with losetup -r (the kernel refuses writes) and mount -o ro (ext4 noload, btrfs rescue=nologreplay, subvolid=5 = every
subvolume incl. snapshots); all are detached at the end, also on errors. Nothing is written into the image.

The private references are read IN MEMORY from the owner's private files and are never printed:
  the Bluetooth address (build/.bdaddr: colon / plain hex, both cases, the 6 raw bytes in both orders), the serial
  (build/.serial), the owner's Wi-Fi name (the owner-wifi-guard source: the keyfile name in priv/run/ov-r2i/cow.log),
  optional build/.wifimac and build/.lan (one value per line: a MAC / a private IPv4 prefix) when present.
A hit is reported as KIND + partition/offset or KIND + path (the Wi-Fi name masked as <SSID>), never the value.

Checks (FAIL unless said otherwise):
  R  raw byte search over the whole image (holes skipped): bdaddr, serial, SSID, wifimac, LAN prefixes
  F  file search over every file of every mounted file system (decompressed by the kernel: btrfs zstd is covered)
  P  paths: /etc/iceland/bdaddr; the extraction record .iceland-extracted; NetworkManager / ifcfg / iwd / wpa
     connections; NetworkManager leases / seen-bssids / timestamps with content; /var/lib/bluetooth/<adapter>; users with
     uid >= 1000 or a home under /home; ssh host keys, authorized_keys, private keys under /root or /home; machine-id not
     empty / "uninitialized"; /var/lib/systemd/random-seed; journal files; shell histories; GDM autologin; a
     gnome-initial-setup-done stamp; the build's /var/lib/iceland residues (install-build, refresh-before.tsv,
     unheld-rpms); dnf caches (WARN); private IPv4 addresses in /etc, /var, /root, /home other than the USB link
     172.16.42.x (WARN, counts only)
  I  INFO: the sensor registry (generic by the owner's decision of 15 Oct 2026: never a FAIL) with its own identifier
     scan (serial / BD / MAC-like / device-id keywords: counts), btrfs subvolumes, grubenv, the provisioning unit
Exit 0 PASS, 1 FAIL, 2 error. Last line: "PRIVSCAN: PASS|FAIL (n FAIL, m WARN, k INFO)".
"""
import argparse, json, mmap, os, re, shutil, struct, subprocess, sys, tempfile, zlib

PRIV = os.environ.get("ICELAND_PRIV") or os.path.expanduser("~/mainline/build")
OV = PRIV + "/wf/install/priv/run/ov-r2i/cow.log"
CHUNK = 64 << 20
results = []          # (level, check, text)


def rep(level, check, text):
    results.append((level, check, text))
    print("%-4s %-3s %s" % (level, check, text), flush=True)


# ---------------------------------------------------------------- private references (in memory only)
def owner_ssid(ov=OV):
    """the owner-wifi-guard method: the one '<name>.nmconnection' btrfs directory entry in the r2i overlay"""
    S = b".nmconnection"; names = set()
    if not os.path.exists(ov):
        return None
    with open(ov, "rb") as fh:
        m = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)
        i = m.find(S)
        while i != -1:
            for k in range(1, 243):
                L = struct.pack("<H", k + len(S))
                if i - k - 3 < 0:
                    break
                if (m[i - k - 3:i - k - 1] == L and m[i - k - 1] == 1) or m[i - k - 2:i - k] == L:
                    nm = bytes(m[i - k:i])
                    if nm and all(c >= 32 and c != 127 for c in nm) and b"/" not in nm:
                        names.add(nm)
                    break
            i = m.find(S, i + 1)
    return names.pop() if len(names) == 1 else None


def load_refs(priv=PRIV, ov=OV):
    refs = {"bin": [], "text": []}     # (kind, regex)
    def rd(p):
        try:
            return open(p).read().split()
        except OSError:
            return []
    bd = (rd(priv + "/.bdaddr") or [""])[0]
    if re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", bd):
        b = bytes(int(x, 16) for x in bd.split(":"))
        refs["bin"].append(("bdaddr-raw", re.compile(re.escape(b) + b"|" + re.escape(b[::-1]))))
        h = bd.replace(":", "")
        refs["text"].append(("bdaddr", re.compile(rb"(?i)" + re.escape(bd.encode()) + rb"|(?<![0-9a-f])" + re.escape(h.encode()) + rb"(?![0-9a-f])")))
    ser = (rd(priv + "/.serial") or [""])[0]
    if ser:
        refs["text"].append(("serial", re.compile(rb"(?i)(?<![0-9a-z])" + re.escape(ser.encode()) + rb"(?![0-9a-z])")))
    ssid = owner_ssid(ov)
    if ssid:
        refs["text"].append(("ssid", re.compile(rb"(?i)" + re.escape(ssid))))
        refs["ssid"] = ssid
    for v in rd(priv + "/.wifimac"):
        if re.fullmatch(r"([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}", v):
            b = bytes(int(x, 16) for x in v.split(":"))
            refs["bin"].append(("wifimac-raw", re.compile(re.escape(b))))
            refs["text"].append(("wifimac", re.compile(rb"(?i)" + re.escape(v.encode()) + rb"|(?<![0-9a-f])" + re.escape(v.replace(":", "").encode()) + rb"(?![0-9a-f])")))
    for v in rd(priv + "/.lan"):
        if re.fullmatch(r"\d{1,3}(\.\d{1,3}){1,3}\.?", v):
            refs["text"].append(("lan-ip", re.compile(rb"(?<![0-9.])" + re.escape(v.encode()))))
    refs["have"] = {"bdaddr": bool(bd), "serial": bool(ser), "ssid": bool(ssid),
                    "wifimac": os.path.exists(priv + "/.wifimac"), "lan": os.path.exists(priv + "/.lan")}
    return refs


def mask(s, refs):
    if refs.get("ssid"):
        s = re.sub(re.escape(refs["ssid"].decode("utf-8", "replace")), "<SSID>", s, flags=re.I)
    return s


def count_buf(buf, refs):
    out = {}
    for kind, rx in refs["bin"] + refs["text"]:
        n = len(rx.findall(buf))
        if n:
            out[kind] = out.get(kind, 0) + n
    return out


def scan_stream(f, refs, limit=None):
    """chunks with a 256-byte overlap; a match inside the overlap is counted once"""
    tot = {}; tail = b""; left = limit
    while True:
        n = CHUNK if left is None else min(CHUNK, left)
        if n <= 0:
            break
        b = f.read(n)
        if not b:
            break
        if left is not None:
            left -= len(b)
        buf = tail + b
        c = count_buf(buf, refs)
        if tail:
            for k, v in count_buf(tail, refs).items():
                c[k] = c.get(k, 0) - v
        for k, v in c.items():
            if v:
                tot[k] = tot.get(k, 0) + v
        tail = buf[-256:]
    return tot


def scan_raw(path, refs, regions):
    """the whole file, data segments only (SEEK_DATA / SEEK_HOLE); hits attributed to the partition regions"""
    hits = {}
    with open(path, "rb") as f:
        fd = f.fileno(); size = os.fstat(fd).st_size

        def scan_range(name, start, end):
            pos = start
            while pos < end:
                try:
                    d = os.lseek(fd, pos, os.SEEK_DATA)
                except OSError:
                    return
                if d >= end:
                    return
                h = min(os.lseek(fd, d, os.SEEK_HOLE), end)
                f.seek(d)
                for k, v in scan_stream(f, refs, h - d).items():
                    hits[(name, k)] = hits.get((name, k), 0) + v
                pos = h
        covered = []
        for name, start, length in regions:
            scan_range(name, start, min(start + length, size)); covered.append((start, min(start + length, size)))
        covered.sort(); prev = 0
        for a, b in covered:               # the GPT, the gaps and the tail
            if a > prev:
                scan_range("gpt/gaps", prev, a)
            prev = max(prev, b)
        if prev < size:
            scan_range("gpt/gaps", prev, size)
    return hits


# ---------------------------------------------------------------- images and mounts
def gpt(path, bs=4096):
    with open(path, "rb") as f:
        f.seek(bs); h = f.read(92)
        if h[:8] != b"EFI PART":
            return None
        ent_lba, n, esz = struct.unpack_from("<QII", h, 72)
        f.seek(ent_lba * bs); raw = f.read(n * esz)
    parts = []
    for i in range(n):
        e = raw[i * esz:(i + 1) * esz]
        if e[:16] == bytes(16):
            continue
        first, last = struct.unpack_from("<QQ", e, 32)
        name = e[56:128].decode("utf-16-le").rstrip("\0")
        parts.append((name or "p%d" % (i + 1), first * bs, (last - first + 1) * bs))
    return parts


def unsparse(src, dst):
    """Android sparse -> a raw file with holes (DONT_CARE / zero FILL = holes)"""
    with open(src, "rb") as f, open(dst, "wb") as o:
        hd = f.read(28)
        magic, maj, mnr, fhs, chs, bs, nblk, nch, _ = struct.unpack("<IHHHHIIII", hd)
        assert magic == 0xED26FF3A, "not an Android sparse image"
        f.seek(fhs); pos = 0
        for _ in range(nch):
            ch = f.read(chs); t, _r, sz, total = struct.unpack("<HHII", ch[:12])
            n = sz * bs
            if t == 0xCAC1:
                o.seek(pos); left = n
                while left:
                    b = f.read(min(left, CHUNK)); o.write(b); left -= len(b)
            elif t == 0xCAC2:
                v = f.read(4)
                if v != b"\0\0\0\0":
                    o.seek(pos); blk = v * (bs // 4)
                    for _k in range(sz):
                        o.write(blk)
            elif t == 0xCAC3:
                pass
            elif t == 0xCAC4:
                f.read(4); continue
            pos += n
        o.truncate(nblk * bs)
    return nblk * bs


class Mounts:
    def __init__(self):
        self.loops, self.mps = [], []
        self.top = tempfile.mkdtemp(prefix="privscan.")

    def add(self, img, off, size, name):
        lo = subprocess.run(["losetup", "-r", "-f", "--show", "-o", str(off), "--sizelimit", str(size), img],
                            capture_output=True, text=True)
        if lo.returncode:
            raise RuntimeError("losetup %s: %s" % (name, lo.stderr.strip()))
        dev = lo.stdout.strip(); self.loops.append(dev)
        ro = subprocess.run(["blockdev", "--getro", dev], capture_output=True, text=True).stdout.strip()
        if ro != "1":
            raise RuntimeError("%s is not read-only" % dev)
        fs = subprocess.run(["blkid", "-o", "value", "-s", "TYPE", dev], capture_output=True, text=True).stdout.strip()
        mp = os.path.join(self.top, name); os.makedirs(mp)
        opts = {"btrfs": "ro,rescue=nologreplay,subvolid=5", "ext4": "ro,noload", "vfat": "ro"}.get(fs, "ro")
        m = subprocess.run(["mount", "-t", fs, "-o", opts, dev, mp], capture_output=True, text=True)
        if m.returncode:
            raise RuntimeError("mount %s (%s): %s" % (name, fs, m.stderr.strip()))
        self.mps.append(mp)
        return mp, fs

    def close(self):
        for mp in reversed(self.mps):
            subprocess.run(["umount", mp])
        for d in self.loops:
            subprocess.run(["losetup", "-d", d])
        shutil.rmtree(self.top, ignore_errors=True)


# ---------------------------------------------------------------- checks on the mounted trees
def walk_files(root):
    for r, ds, fs in os.walk(root):
        for f in fs:
            p = os.path.join(r, f)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            yield p


def rel(p, mounts):
    for name, mp in mounts.items():
        if p.startswith(mp + "/"):
            return name + ":" + p[len(mp):]
    return p


def roots_of(root_mp):
    """the btrfs top level: the subvolumes that hold a root file system (etc/os-release present)"""
    out = []
    cands = [root_mp]
    for d in sorted(os.listdir(root_mp)):
        sub = os.path.join(root_mp, d)
        if os.path.isdir(sub) and not os.path.islink(sub):
            cands.append(sub)
            if not os.path.isfile(os.path.join(sub, "etc/os-release")):
                cands += [os.path.join(sub, e) for e in sorted(os.listdir(sub)) if os.path.isdir(os.path.join(sub, e))]
    for c in cands:
        if os.path.isfile(os.path.join(c, "etc/os-release")) and c not in out:
            out.append(c)
    return out


def home_subvolume_checks(root_mp):
    """Fedora's btrfs layout: the subvolume 'home' (mounted at /home) next to 'root'"""
    h = os.path.join(root_mp, "home")
    if os.path.isdir(h) and not os.path.isfile(os.path.join(root_mp, "etc/os-release")):
        return sorted(os.listdir(h))
    return []


def path_checks(r, tag, refs, var_root=None):
    """structural checks of one root tree r (a subvolume); tag names it in the report; var_root = the top-level
    subvolume mounted at /var (Fedora's btrfs layout: root, var, home), else r/var"""
    def J(*a):
        p = os.path.join(*a)
        if var_root and (p == "var" or p.startswith("var/")):
            return os.path.join(var_root, p[4:])
        return os.path.join(r, p)
    def present(p):
        return os.path.lexists(J(p))
    def ls(p):
        try:
            return sorted(os.listdir(J(p)))
        except OSError:
            return []
    fails = []
    if present("etc/iceland/bdaddr"):
        fails.append(("P", "%s: /etc/iceland/bdaddr present (unit Bluetooth address)" % tag))
    if present("usr/lib/firmware/updates/.iceland-extracted"):
        fails.append(("P", "%s: the extraction record /usr/lib/firmware/updates/.iceland-extracted present" % tag))
    for d in ("etc/NetworkManager/system-connections", "run/NetworkManager/system-connections"):
        for e in ls(d):
            fails.append(("P", "%s: NetworkManager connection /%s/%s" % (tag, d, mask(e, refs))))
    for e in ls("etc/sysconfig/network-scripts"):
        if e.startswith("ifcfg-") and e != "ifcfg-lo":
            fails.append(("P", "%s: /etc/sysconfig/network-scripts/%s" % (tag, mask(e, refs))))
    for e in ls("var/lib/iwd"):
        fails.append(("P", "%s: iwd network /var/lib/iwd/%s" % (tag, mask(e, refs))))
    for p in ("etc/wpa_supplicant/wpa_supplicant.conf",):
        try:
            if b"network=" in open(J(p), "rb").read():
                fails.append(("P", "%s: /%s has a network= block" % (tag, p)))
        except OSError:
            pass
    for e in ls("var/lib/NetworkManager"):
        q = J("var/lib/NetworkManager", e)
        if (e.endswith(".lease") or e in ("seen-bssids", "timestamps", "secret_key")) and os.path.isfile(q) and os.path.getsize(q) > 0:
            fails.append(("P", "%s: /var/lib/NetworkManager/%s (%d bytes)" % (tag, e, os.path.getsize(q))))
    for e in ls("var/lib/bluetooth"):
        if re.fullmatch(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", e):
            fails.append(("P", "%s: /var/lib/bluetooth/<adapter address> directory (pairings)" % tag))
    try:
        for line in open(J("etc/passwd")):
            w = line.split(":")
            if len(w) > 3 and w[2].isdigit() and 1000 <= int(w[2]) < 60000:
                fails.append(("P", "%s: a user account with uid %s in /etc/passwd" % (tag, w[2])))
    except OSError:
        pass
    for e in ls("home"):
        fails.append(("P", "%s: a home directory /home/%s" % (tag, mask(e, refs))))
    for e in ls("etc/ssh"):
        if e.startswith("ssh_host_"):
            fails.append(("P", "%s: ssh host key /etc/ssh/%s" % (tag, e)))
    for base in ("root",):
        for q in walk_files(J(base)) if os.path.isdir(J(base)) else []:
            b = os.path.basename(q)
            if b in ("authorized_keys", "id_rsa", "id_ed25519", "id_ecdsa", "known_hosts") or b.endswith("_history"):
                fails.append(("P", "%s: /%s" % (tag, os.path.relpath(q, r))))
    try:
        mid = open(J("etc/machine-id")).read().strip()
        if mid not in ("", "uninitialized"):
            fails.append(("P", "%s: /etc/machine-id is set (a 32-hex id): every install would share it" % tag))
    except OSError:
        pass
    if present("var/lib/systemd/random-seed"):
        fails.append(("P", "%s: /var/lib/systemd/random-seed present" % tag))
    for q in walk_files(J("var/log/journal")) if os.path.isdir(J("var/log/journal")) else []:
        if q.endswith((".journal", ".journal~")):
            fails.append(("P", "%s: journal file /%s" % (tag, os.path.relpath(q, r))))
    for p in ("etc/gdm/custom.conf",):
        try:
            t = open(J(p)).read()
            if re.search(r"(?im)^\s*(AutomaticLoginEnable|TimedLoginEnable)\s*=\s*(true|1)", t):
                fails.append(("P", "%s: GDM automatic login enabled in /%s" % (tag, p)))
            if re.search(r"(?im)^\s*InitialSetupEnable\s*=\s*(false|0)", t):
                fails.append(("P", "%s: the first-boot wizard is disabled in /%s" % (tag, p)))
        except OSError:
            pass
    for q in walk_files(J("var/lib/gdm")) if os.path.isdir(J("var/lib/gdm")) else []:
        if os.path.basename(q) == "gnome-initial-setup-done":
            fails.append(("P", "%s: /%s (the first-boot wizard would be skipped)" % (tag, os.path.relpath(q, r))))
    for p in ("var/lib/iceland/install-build", "var/lib/iceland/refresh-before.tsv", "var/lib/iceland/unheld-rpms",
              "var/lib/iceland/refresh-fw-before.txt"):
        if present(p):
            fails.append(("P", "%s: build residue /%s" % (tag, p)))
    warns = []
    for p in ("var/cache/dnf", "var/cache/libdnf5"):
        if os.path.isdir(J(p)) and any(True for _ in walk_files(J(p))):
            warns.append(("P", "%s: dnf cache /%s not empty" % (tag, p)))
    ipre = re.compile(rb"(?<![0-9.])(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![0-9.])")
    nip = 0; nfile = 0; ipfiles = []
    for base in ("etc", "var/lib", "var/log", "root", "home"):
        if not os.path.isdir(J(base)):
            continue
        for q in walk_files(J(base)):
            try:
                if os.path.getsize(q) > (8 << 20):
                    continue
                b = open(q, "rb").read()
            except OSError:
                continue
            ips = [m.group(0) for m in ipre.finditer(b) if not m.group(0).startswith(b"172.16.42.")]
            if ips:
                nip += len(ips); nfile += 1
                ipfiles.append(("/var/" + os.path.relpath(q, var_root)) if var_root and q.startswith(var_root + "/") else "/" + os.path.relpath(q, r))
    if nip:
        warns.append(("P", "%s: %d private IPv4 address(es) (not the USB link) in %d file(s) under /etc /var/lib /var/log /root /home: %s" % (tag, nip, nfile, ", ".join(mask(x, refs) for x in ipfiles[:12]))))
    return fails, warns


def registry_info(r, tag, refs):
    reg = os.path.join(r, "usr/share/qcom/kaanapali/OnePlus/iceland/sensors/registry")
    if not os.path.isdir(reg):
        rep("INFO", "I", "%s: no sensor registry" % tag)
        return
    mac = re.compile(rb"(?i)(?<![0-9a-f])([0-9a-f]{2}[:-]){5}[0-9a-f]{2}(?![0-9a-f])")
    kw = re.compile(rb"(?i)serial|imei|device_?id|uuid|mac_?addr|bd_?addr|bdaddr|ssid|cpuid|chip_?id")
    n = dict(files=0, bytes=0, ident=0, maclike=0, kw=0, faccal=0, faccal_nondefault=0)
    for q in walk_files(reg):
        b = open(q, "rb").read(); n["files"] += 1; n["bytes"] += len(b)
        n["ident"] += sum(count_buf(b, refs).values())
        n["maclike"] += len(mac.findall(b)); n["kw"] += len(kw.findall(b))
        if "fac_cal" in q or q.endswith((".bias", ".corr_mat")):
            n["faccal"] += 1
            vals = re.findall(rb'"data"\s*:\s*"([^"]*)"', b)
            if any(v not in (b"0", b"1", b"0.0", b"1.0", b"0.000000", b"1.000000") for v in vals):
                n["faccal_nondefault"] += 1
    rep("INFO", "I", "%s: sensor registry %d files %d bytes (generic per the owner, 15 Oct: not a FAIL); identifying values: "
        "owner refs %d, MAC-like %d, id keywords %d; calibration files %d, of them with non-default numbers %d"
        % (tag, n["files"], n["bytes"], n["ident"], n["maclike"], n["kw"], n["faccal"], n["faccal_nondefault"]))


def scan_image(img, regions, refs, out):
    rep("INFO", "-", "references loaded (values never printed): " + ", ".join("%s %s" % (k, "yes" if v else "NO RECORD") for k, v in refs["have"].items()))
    # R: raw bytes
    hits = scan_raw(img, refs, regions)
    if hits:
        for (part, kind), n in sorted(hits.items()):
            rep("FAIL", "R", "raw bytes: %s in %s: %d hit(s)" % (kind, part, n))
    else:
        rep("PASS", "R", "raw bytes: no owner value in %d partitions + GPT / gaps" % len(regions))
    M = Mounts(); mounts = {}
    try:
        for name, off, size in regions:
            key = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
            try:
                mp, fs = M.add(img, off, size, key)
                mounts[key] = mp
                rep("INFO", "-", "mounted %s (%s) read-only" % (key, fs))
            except RuntimeError as e:
                rep("WARN", "-", "not mounted: %s" % e)
        # F: every file
        nf = 0; fh = 0
        for key, mp in mounts.items():
            for q in walk_files(mp):
                nf += 1
                try:
                    with open(q, "rb") as f:
                        c = scan_stream(f, refs)
                except OSError:
                    continue
                if c:
                    fh += 1
                    rep("FAIL", "F", "%s: %s" % (mask(rel(q, mounts), refs), ", ".join("%s %d" % kv for kv in sorted(c.items()))))
        rep("PASS" if fh == 0 else "FAIL", "F", "file search: %d files read, %d with an owner value" % (nf, fh))
        # P / I: every root subvolume
        rmp = [mp for k, mp in mounts.items() if os.path.isdir(os.path.join(mp, "root")) or os.path.isfile(os.path.join(mp, "etc/os-release"))]
        trees = []
        for mp in rmp:
            trees += roots_of(mp)
        try:
            for mp in rmp:
                sv = subprocess.run(["btrfs", "subvolume", "list", mp], capture_output=True, text=True)
                if sv.returncode == 0:
                    rep("INFO", "I", "btrfs subvolumes: %s" % ", ".join(l.split()[-1] for l in sv.stdout.splitlines()))
        except FileNotFoundError:
            rep("INFO", "I", "btrfs subvolumes: %s (btrfs-progs not on the PC; directory view)" % ", ".join(os.path.relpath(t, rmp[0]) or "." for t in trees))
        if not trees:
            rep("FAIL", "P", "no root file system found in the image")
        for mp in rmp:
            hs = home_subvolume_checks(mp)
            for e in hs:
                rep("FAIL", "P", "the home subvolume has a home directory %s" % mask(e, refs))
            if not hs and os.path.isdir(os.path.join(mp, "home")):
                rep("PASS", "P", "the home subvolume is empty")
        for t in trees:
            tag = rel(t, mounts) or "root"
            par = os.path.dirname(t)
            vr = os.path.join(par, "var") if t != par and os.path.isdir(os.path.join(par, "var")) and not os.listdir(os.path.join(t, "var")) else None
            if vr:
                rep("INFO", "I", "%s: /var = the top-level subvolume var (Fedora layout)" % tag)
            f, w = path_checks(t, tag, refs, vr)
            for lv, txt in [("FAIL", x) for x in f] + [("WARN", x) for x in w]:
                rep(lv, txt[0], txt[1])
            if not f:
                rep("PASS", "P", "%s: no unit / owner path (bdaddr, record, connections, users, keys, machine-id, seed, journal, autologin, residues)" % tag)
            registry_info(t, tag, refs)
            u = os.path.join(t, "usr/lib/systemd/system/iceland-provision.service")
            rep("INFO", "I", "%s: provisioning unit %s" % (tag, "present" if os.path.exists(u) else "absent (image older than iceland-device 0.28-17)"))
        for key, mp in mounts.items():
            g = os.path.join(mp, "grub2/grubenv")
            if os.path.isfile(g):
                rep("INFO", "I", "grubenv keys: %s" % ", ".join(sorted(set(re.findall(r"(?m)^([a-z_]+)=", open(g, errors="replace").read())))))
    finally:
        M.close()
        rep("INFO", "-", "all mounts and loop devices released")


def selftest():
    d = tempfile.mkdtemp(prefix="privscan-st.")
    os.makedirs(d + "/priv")
    open(d + "/priv/.bdaddr", "w").write("aa:bb:cc:dd:ee:ff\n")
    open(d + "/priv/.serial", "w").write("12ab34cd\n")
    refs = load_refs(d + "/priv", d + "/none")
    ok = True
    def t(name, cond):
        nonlocal ok
        ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name)
    t("colon form any case", count_buf(b"x " + b"aa:bb:cc:dd:ee:ff".upper() + b" y", refs) == {"bdaddr": 1})
    t("plain hex with boundaries", count_buf(b"addr=AABBCCDDEEFF;", refs) == {"bdaddr": 1})
    t("plain hex inside a longer hex digest: no hit", count_buf(b"ffaabbccddeeff00", refs) == {})
    t("raw bytes both orders", count_buf(bytes([170, 187, 204, 221, 238, 255]) + b"..." + bytes([255, 238, 221, 204, 187, 170]), refs) == {"bdaddr-raw": 2})
    t("serial with boundaries, not inside a digest", count_buf(b"sn 12AB34CD\n", refs) == {"serial": 1} and count_buf(b"a12ab34cdb", refs) == {})
    import io
    big = b"z" * (CHUNK - 3) + b"aa:bb:cc:dd:ee:ff" + b"z" * 100
    t("a match across a chunk border counts once", scan_stream(io.BytesIO(big), refs) == {"bdaddr": 1})
    # a fake root tree for the path checks
    r = d + "/root"
    for p in ("etc/iceland", "etc/NetworkManager/system-connections", "home/u", "etc/ssh", "var/log/journal/x", "var/lib/iceland"):
        os.makedirs(os.path.join(r, p))
    open(r + "/etc/iceland/bdaddr", "w").write("x"); open(r + "/etc/NetworkManager/system-connections/w.nmconnection", "w").write("x")
    open(r + "/etc/passwd", "w").write("root:x:0:0::/root:/bin/bash\nu:x:1000:1000::/home/u:/bin/bash\n")
    open(r + "/etc/ssh/ssh_host_ed25519_key", "w").write("x"); open(r + "/etc/machine-id", "w").write("0123456789abcdef0123456789abcdef\n")
    open(r + "/var/log/journal/x/system.journal", "w").write("x"); open(r + "/var/lib/iceland/install-build", "w").write("x")
    os.makedirs(r + "/etc/gdm"); open(r + "/etc/gdm/custom.conf", "w").write("[daemon]\nAutomaticLoginEnable=True\n")
    f, w = path_checks(r, "st", refs)
    kinds = " | ".join(x[1] for x in f)
    for k in ("bdaddr present", "NetworkManager connection", "uid 1000", "home directory", "ssh host key", "machine-id is set",
              "journal file", "automatic login", "build residue"):
        t("path check finds: " + k, k in kinds)
    clean = d + "/clean"
    os.makedirs(clean + "/etc"); open(clean + "/etc/machine-id", "w").write("uninitialized\n"); open(clean + "/etc/passwd", "w").write("root:x:0:0::/root:/bin/bash\n")
    f, w = path_checks(clean, "clean", refs)
    t("a clean tree has no FAIL", f == [])
    vtop = d + "/top"; os.makedirs(vtop + "/root/etc"); os.makedirs(vtop + "/root/var"); os.makedirs(vtop + "/var/lib/systemd")
    open(vtop + "/root/etc/machine-id", "w").write("uninitialized\n"); open(vtop + "/var/lib/systemd/random-seed", "w").write("x")
    f, w = path_checks(vtop + "/root", "split", refs, vtop + "/var")
    t("the var subvolume is checked as /var (random-seed found there)", any("random-seed" in x[1] for x in f))
    shutil.rmtree(d)
    print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    a = argparse.ArgumentParser()
    g = a.add_mutually_exclusive_group(required=True)
    g.add_argument("--golden"); g.add_argument("--raw"); g.add_argument("--sparse"); g.add_argument("--selftest", action="store_true")
    a.add_argument("--work"); a.add_argument("--out"); a.add_argument("--priv", default=PRIV)
    o = a.parse_args()
    if o.selftest:
        return selftest()
    if os.geteuid() != 0:
        print("privscan: needs root for the read-only mounts (wsl.exe -u root -- python3 -I %s ...)" % sys.argv[0]); return 2
    refs = load_refs(o.priv, o.priv + "/wf/install/priv/run/ov-r2i/cow.log")
    tmp = None
    if o.golden:
        m = json.load(open(o.golden)); img = os.path.join(os.path.dirname(o.golden), m["body"])
        regions = [(p.get("name") or "p%d" % p["n"], p["offset"], p["bytes"]) for p in m["partitions"]]
        what = "golden %s (body %s)" % (os.path.basename(o.golden), m["body"])
    else:
        if o.sparse:
            if not o.work:
                print("privscan: --sparse needs --work DIR"); return 2
            os.makedirs(o.work, exist_ok=True); tmp = os.path.join(o.work, "privscan-unsparsed.raw")
            unsparse(o.sparse, tmp); img = tmp; what = "sparse %s" % os.path.basename(o.sparse)
        else:
            img = o.raw; what = "raw %s" % os.path.basename(o.raw)
        regions = gpt(img) or gpt(img, 512)
        if not regions:
            print("privscan: no GPT in %s" % img); return 2
    rep("INFO", "-", "image: %s, %d partitions" % (what, len(regions)))
    try:
        scan_image(img, regions, refs, o.out)
    except Exception as e:
        rep("FAIL", "-", "scan error: %s: %s" % (type(e).__name__, e))
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)
    nf = sum(1 for r in results if r[0] == "FAIL"); nw = sum(1 for r in results if r[0] == "WARN"); ni = sum(1 for r in results if r[0] == "INFO")
    line = "PRIVSCAN: %s (%d FAIL, %d WARN, %d INFO)" % ("PASS" if nf == 0 else "FAIL", nf, nw, ni)
    if o.out:
        os.makedirs(o.out, exist_ok=True)
        with open(os.path.join(o.out, "privscan-report.txt"), "w") as f:
            for r in results:
                f.write("%-4s %-3s %s\n" % r)
            f.write(line + "\n")
    print(line)
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

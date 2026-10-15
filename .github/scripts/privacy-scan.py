#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generic privacy scan for this repository (run by .github/workflows/privacy.yml, also usable locally).

  python3 .github/scripts/privacy-scan.py [--max-blob-kb N] [--allow FILE] [--quiet] [--text FILE...]

--text scans the given text files (e.g. the commit messages of a push) instead of the tracked files; the name and
blob rules do not apply to them.

Scans every tracked file (git ls-files) for generic patterns only:
  mac       MAC / Bluetooth-address-like strings (six two-digit hex groups joined by ':' or '-'; all-equal
            placeholders such as all zeros are ignored)
  ipv4      IPv4 addresses in private ranges (10/8, 172.16/12, 192.168/16)
  email     e-mail addresses other than the maintainer's and noreply addresses
  key       private-key headers (PEM / OpenSSH)
  nm        NetworkManager connection files and their Wi-Fi secret / SSID keys
  name      work-record files that must stay out of the public repositories
  blob      binary or large files (only with --max-blob-kb, for the kernel / package repositories)

The scan holds no device-specific values: it does not know any serial number, address or network name.
Known-safe values and paths are listed in the allow-list (default .github/privacy-allow.txt).
Hits are printed masked (the matched value is never written to the log) as GitHub error annotations.
Exit status: 0 no hits, 1 hits, 2 usage error.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys

OWN_EMAILS = {"mzak.amin@gmail.com"}
RULES = ("mac", "ipv4", "email", "key", "nm", "name", "blob")

RX = {
    "mac": re.compile(r"(?<![0-9A-Fa-f:.-])[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}(?![0-9A-Fa-f:-])"),
    "ipv4": re.compile(r"(?<![\d.])(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}(?![\d.]*\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"),
    "key": re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----|PuTTY-User-Key-File"),
    "nm": re.compile(r"^\s*(?:\[wifi-security\]|psk\s*=|wep-key\d?\s*=|ssid\s*=|password\s*=|\[802-11-wireless(?:-security)?\])",
                     re.I),
}
# Lines of patch files / commit trailers that carry upstream people's addresses (authorship, not private data).
TRAILER = re.compile(r"^[+ -]?\s*(?:From|To|Cc|Signed-off-by|Co-developed-by|Reviewed-by|Acked-by|Tested-by|Reported-by|"
                     r"Suggested-by|Reported-and-tested-by|Requested-by|Cc-by|Link|Closes|Message-Id|Message-ID|"
                     r"Debugged-by|Analyzed-by|Originally-by|Based-on-patch-by|Helped-by|Original-author)\s*:", re.I)
UPSTREAM_CODE = re.compile(r"MODULE_AUTHOR|Copyright|\(C\)|Author:|Authors:|Maintainer|Contact:|"
                           r"^[+ -]?[LMRS]:\s|<[^<>@\s]+@[^<>\s]+>", re.I)
SYSTEMD_TLD = ("service", "socket", "target", "timer", "mount", "path", "slice", "scope", "device", "swap", "automount")
FORBIDDEN_NAMES = re.compile(r"(?:^|/)[^/]*(?:WORKLOG|NEXT-ACTIONS|NEXT_ACTIONS|HANDOVER)[^/]*$", re.I)
NM_FILE = re.compile(r"\.nmconnection$|(?:^|/)system-connections/", re.I)


def load_allow(path):
    values, skips = set(), []
    if not os.path.exists(path):
        return values, skips
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split(None, 2)
            if parts[0] == "value" and len(parts) >= 2:
                values.add(line.split(None, 1)[1].strip().lower())
            elif parts[0] == "skip" and len(parts) == 3 and (parts[1] in RULES or parts[1] == "*"):
                skips.append((parts[1], parts[2].strip()))
            else:
                print(f"{path}:{n}: bad allow-list line", file=sys.stderr)
                sys.exit(2)
    return values, skips


def skipped(rule, path, skips):
    return any((r == rule or r == "*") and fnmatch.fnmatch(path, g) for r, g in skips)


def mask(s):
    return (s[:2] + "*" * max(3, len(s) - 2)) if len(s) > 2 else "***"


def email_ok(addr, line, is_patch, start):
    a = addr.lower()
    if start > 0 and line[start - 1] == "/":
        return True  # a Message-ID inside a URL (lore.kernel.org/r/<id>)
    if a in OWN_EMAILS or "noreply" in a or "no-reply" in a:
        return True
    dom = a.rsplit("@", 1)[1]
    if dom in ("example.com", "example.org", "example.net", "localhost", "localhost.localdomain") or dom.endswith(".example") \
            or dom.endswith(".invalid") or dom.endswith(".test") or dom.endswith(".local"):
        return True
    if dom.rsplit(".", 1)[1] in SYSTEMD_TLD:
        return True  # systemd unit instance (getty@tty1.service)
    if TRAILER.match(line):
        return True
    if is_patch and UPSTREAM_CODE.search(line):
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow", default=".github/privacy-allow.txt")
    ap.add_argument("--max-blob-kb", type=int, default=0, help="fail on binary files and on files larger than N KiB")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--show", action="store_true", help="local use only: print the matched values unmasked")
    ap.add_argument("--text", nargs="+", metavar="FILE", help="scan these text files instead of git ls-files")
    a = ap.parse_args()
    values, skips = load_allow(a.allow)
    if a.text:
        files = a.text
    else:
        files = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True).stdout.decode().split("\0")
    hits = 0

    def hit(rule, path, line, what):
        nonlocal hits
        hits += 1
        loc = f"file={path}" + (f",line={line}" if line else "")
        print(f"::error {loc},title=privacy-scan {rule}::{what}")

    for path in filter(None, files):
        if not os.path.isfile(path) or os.path.islink(path):
            continue
        if not a.text and FORBIDDEN_NAMES.search(path) and not skipped("name", path, skips):
            hit("name", path, 0, "work-record file name (WORKLOG / NEXT-ACTIONS / HANDOVER) must stay out of this repository")
        if not a.text and NM_FILE.search(path) and not skipped("nm", path, skips):
            hit("nm", path, 0, "NetworkManager connection file")
        size = os.path.getsize(path)
        with open(path, "rb") as f:
            data = f.read()
        binary = b"\0" in data[:8192]
        if a.max_blob_kb and not a.text and not skipped("blob", path, skips):
            if binary:
                hit("blob", path, 0, f"binary file ({size} bytes) in a source-only repository")
            elif size > a.max_blob_kb * 1024:
                hit("blob", path, 0, f"large file ({size // 1024} KiB > {a.max_blob_kb} KiB)")
        if binary:
            continue
        text = data.decode("utf-8", errors="replace")
        is_patch = path.endswith((".patch", ".diff"))
        for n, line in enumerate(text.splitlines(), 1):
            for rule, rx in RX.items():
                if skipped(rule, path, skips):
                    continue
                for m in rx.finditer(line):
                    v = m.group(0)
                    if v.strip().lower() in values:
                        continue
                    if rule == "email" and email_ok(v, line, is_patch, m.start()):
                        continue
                    if rule == "mac" and len(set(v.lower().replace(":", "").replace("-", ""))) == 1:
                        continue  # 00:00:..., ff:ff:... style placeholders
                    if rule == "nm" and not (path.endswith(".nmconnection") or "802-11" in line.lower() or "wifi-security" in line.lower()
                                             or re.match(r"\s*(psk|wep-key\d?)\s*=", line, re.I)
                                             or (re.match(r"\s*ssid\s*=", line, re.I) and "[wifi]" in text.lower())):
                        continue
                    hit(rule, path, n, f"{rule}-like value {v.strip() if a.show else mask(v.strip())}")
    if not a.quiet or hits:
        print(f"privacy-scan: {len([f for f in files if f])} files, {hits} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())

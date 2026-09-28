#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
#
# OnePlus Pad 4: convert the stock touch firmware (odm /firmware/tp/25926/FW_NT36536_HUAXING.img, 11.A.38) into
# the Novatek image the mainline nt36536 driver downloads into the touch IC's SRAM (novatek/novatek_nt36536_fw.bin).
# The stock file is a "FwUp!" container: an 80-byte header (payload length, little-endian u32 at 0x0c), the Novatek
# image, and a 128-byte trailer. Runs on the user's PC on their own files; the output is never committed.
# Usage: convert-nt36536.py FW_NT36536_HUAXING.img novatek_nt36536_fw.bin
import hashlib
import struct
import sys

STOCK_SHA256 = "768ffdf8731a3185b4bcca786422f748c235c97d762ca3f92be1d12e3876b20c"
OUT_SHA256 = "5e9d96517199ce11d44db90436e5835fed7982031102f52a74b7230ad64d83e2"

d = open(sys.argv[1], "rb").read()
if hashlib.sha256(d).hexdigest() != STOCK_SHA256:
    sys.exit("not the 11.A.38 FW_NT36536_HUAXING.img (sha256 differs)")
if d[:5] != b"FwUp!":
    sys.exit("not a FwUp container")
n = struct.unpack_from("<I", d, 0x0C)[0]
if len(d) != 80 + n + 128:
    sys.exit(f"unexpected size {len(d)} for payload {n}")
p = d[80:80 + n]
if not any(p[i * 4096 - 3:i * 4096] in (b"NVT", b"MOD") for i in range(1, n // 4096 + 1)):
    sys.exit("no Novatek end flag in the payload")
if hashlib.sha256(p).hexdigest() != OUT_SHA256:
    sys.exit("converted image differs from the tested one")
open(sys.argv[2], "wb").write(p)
print(f"{sys.argv[2]}: {n} bytes, sha256 {OUT_SHA256}")

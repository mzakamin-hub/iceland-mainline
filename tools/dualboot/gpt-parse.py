#!/usr/bin/env python3
"""Dual boot: print a 4 KiB-block disk file's GPT through iceland_disk.parse_gpt (both CRCs, backup at the end).
  gpt-parse.py FILE BLOCKS  -> "<n> <name> <first> <last>" per partition, then "lu <last usable>" """
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "image", "tools"))
import iceland_disk as D

f = open(sys.argv[1], "rb")


def rd(o, n):
    f.seek(o)
    return f.read(n)


g = D.parse_gpt(rd, int(sys.argv[2]))
for p in g["parts"]:
    print(p["n"], p["name"], p["first"], p["last"])
print("lu", g["last_usable"])

# Dual-boot tools (BlissROM + Fedora)

The tools of the dual boot in [docs/DUAL-BOOT.md](../../docs/DUAL-BOOT.md): a power-on menu Fedora / BlissROM / Boot
loader from U-Boot v7, Fedora in its own `fedora` partition, BlissROM in a smaller `userdata`. These are the versions
used on the tested tablet (only comments differ, and `gpt-parse.py` finds `image/tools/iceland_disk.py` in this
repository). Block size is 4096 bytes everywhere.

| Tool | Runs on | What it does |
|---|---|---|
| `dualboot-backup.sh` | the installed Fedora (root) | Read only: the partition tables of every UFS LUN, Fedora's own table, the small Android partitions of both slots, `misc`, `metadata`, the ends of `super`, the slot flags and a comparison of the firmware partitions with BlissROM v20.1's, with `SHA256SUMS`. Its output is the input of `gpt-plan.py` and the undo of the flash steps; it holds the unit's GUIDs, so it stays private |
| `gpt-plan.py` | PC | Computes, never writes, the two table changes from saved copies of a disk's first 6 and last 5 blocks. `split`: LUN 0, `userdata` keeps its name / type / GUID / attributes and starts later (optionally ends early: `--userdata-last`), a new `fedora` entry covers the old start. `shrink`: Fedora's own disk for a smaller size. Refuses on CRC errors, primary / backup mismatch, overlaps; re-parses its result. Writes `head-new.bin`, `tail-new.bin`, the undo `head-old.bin` / `tail-old.bin`, `REPORT.txt`, `SHA256SUMS` |
| `gpt-parse.py` | PC | Prints a disk file's GPT through `iceland_disk.parse_gpt` (both CRCs) |
| `dualboot-w2.sh` | the installed Fedora (root) | Writes Fedora's own (inner) table for the smaller disk: `--dry-run`, `--write --confirm CODE`, `--restore --confirm CODE`. Refuses unless the root is on the loop disk over `userdata`, systemd-repart is masked and the btrfs is already small enough; tail first, then head, each read back. Carries the tested layout's numbers |
| `w3-gpt.sh` | Linux in RAM (root) | Writes LUN 0's table: `--dry-run`, `--write --confirm CODE`, `--restore --confirm CODE`. Refuses unless the device is UFS LUN 0 with the expected size, nothing on it is in use, and LUN 0 holds exactly the saved (or the planned) table; backup copy first, each read back, then the kernel re-reads the table and its partition view is compared |
| `mk-super.py` | PC | Builds a sparse `super` image for ABL's `fastboot flash super`: the tablet's LP geometry and block device, new metadata with BlissROM's seven partitions for slot b (read-only, 1 MiB aligned), the raw images at their extents |
| `check-super.py` | PC | Checks such an image independently: sparse structure, geometry, all metadata copies, every partition's bytes against its source image. Last line `SUPER-CHECK: N failure(s)` |

`SHA256SUMS` lists the files of this folder.

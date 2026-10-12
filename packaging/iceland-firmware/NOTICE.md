# iceland-firmware 11.A.38: notices

These files are proprietary firmware of Qualcomm Technologies, Inc. / Qualcomm Atheros, Inc., Novatek Microelectronics
Corp. and OnePlus (OPLUS), as shipped on every OnePlus Pad 4 (OPD2514) in the stock software release 11.A.38. They are
redistributed UNMODIFIED, with these documented, byte-exact transformations only:

- `*.mbn` built from split images: the `.mdt` header file and its `.bNN` segments joined into one ELF (what
  pil-squasher does); every segment is byte-identical to the stock file.
- `novatek_nt36536_fw.bin`: the stock `FwUp!` container's 80-byte header and 128-byte trailer removed; the payload is
  byte-identical.
- `socinfo/*`: SoC identification values (stock `/sys/devices/soc0`), not vendor code.

All rights remain with their owners. No licence is granted beyond the right to use the files with OnePlus Pad 4 hardware
as the owners permit. `Notice-qca-atheros.txt` is Qualcomm Atheros' notice file for the WCN7860 Wi-Fi firmware
(copy from SuperTurtleDev/iceland-mainline-kernel-firmware d0c0f18, sha256 in MANIFEST/README).
Each file's source partition and path in 11.A.38 and its sha256 are in `MANIFEST.tsv`; unit-specific data (calibration,
addresses, persist data) is never part of this package (`EXCLUDED.tsv`).

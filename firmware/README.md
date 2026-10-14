# Firmware manifest

`manifest.tsv` lists the firmware files the mainline kernel and userspace need on the Pad 4. For each file it gives the
stock source on the tablet (OPD2514, stock 11.A.38), its stock size and sha256, where it goes under `/lib/firmware`, and
what has to happen to it (copy, rename, pil-squasher, convert).

The generic files are packaged in the dedicated repository [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware)
(tags 11.A.38-2 and 11.A.38-3, 278 files plus the decoded thermal model). Each file there is checked by sha256 against its
manifest, and the device package fetches a release only against pinned sha256 values. The files are not stored in this
repository.

Unit-specific data is never published: the sensor calibration registry, the Bluetooth and Wi-Fi addresses and the
extraction record. The installer takes those from the tablet itself, read-only, when the system is set up.

Findings behind the table:

- The map220v firmware repository is used only for file names: 20 of its 22 files differ from this tablet's 11.A.38 files
  (another firmware release, DSP images pre-squashed).
- Mainline asks for different names than stock ships: Bluetooth `gngbt*` (stock `brhbt*`), ath12k `amss.bin`, `m3.bin`,
  `aux_ucode.bin` and `board.bin` (stock `peach/amss20.bin`, `phy_ucode20.elf`, `aux_ucode20.elf`, `bdwlan.*`).
- ADSP and CDSP ship split (`.mdt` plus `.bNN`); they are squashed to `.mbn`.
- SOCCP is started by the boot chain (the `soccp_a` partition); Linux attaches to it.
- Rows marked `status=verify` need a runtime check: the board-specific Wi-Fi BDF, the Bluetooth NVM variant and the touch
  image header.

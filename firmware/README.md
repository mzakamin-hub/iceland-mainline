# Firmware manifest

`manifest.tsv` lists every firmware file the mainline kernel/userspace needs, where it comes from on the
tablet (stock OPD2514 11.A.38), its stock size and sha256 (from `docs/device-facts/capture-20260927-3`),
where it goes under `/lib/firmware`, and what has to happen to it (copy, rename, pil-squasher, convert).

No firmware file is ever committed. The extractor (next step) reads the user's own partitions/OTA and
fails if a sha256 does not match.

Findings behind the table:
- map220v/iceland-firmware is used only for file names: 20 of its 22 files differ from this tablet's
  11.A.38 files (other firmware release; DSP images pre-squashed).
- Mainline asks for different names than stock ships: Bluetooth `gngbt*` (stock `brhbt*`), ath12k
  `amss.bin`/`m3.bin`/`aux_ucode.bin`/`board.bin` (stock `peach/amss20.bin`, `phy_ucode20.elf`,
  `aux_ucode20.elf`, `bdwlan.*`).
- ADSP/CDSP ship split (`.mdt` + `.bNN`) → squash to `.mbn`.
- SOCCP is started by the boot chain (`soccp_a` partition); Linux attaches.
- `status=verify` rows need a runtime check (board-specific Wi-Fi BDF, BT NVM variant, touch image header).

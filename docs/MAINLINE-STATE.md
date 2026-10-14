# Kernel and U-Boot state, 14 Oct 2026

This page is the state of the two upstream-facing ports: the kernel and U-Boot. The project snapshot is in
[PROJECT-STATE.md](PROJECT-STATE.md), the dated history in [../CHANGELOG.md](../CHANGELOG.md).

## Kernel (iceland-linux)

- **Build in use:** `7.3.0-rc7-iceland-00426-g520e85da9244`, queue head **q89g**, branch `iceland-7.3-rc7-q89g`
  (tag `q89g`). It runs on the installed tablet and in the install image (golden B149). The kernel package is
  `kernel-iceland 7.3.0~rc7.iceland.00426`; the build has no compiler warnings.
- **Base:** Linux v7.3-rc7 (`UPSTREAM_COMMIT` 24a19b953e2a) with 426 patch files: 132 in `0001-infiniti` (the
  infiniti-mainline base for SM8850) and 294 in `0002-iceland` (the Pad 4 series).
- **Queue history:** q89 (rc4) -> q89b (rc6 rebase, 10 Oct) -> q89c-tb (tb323fu patches) -> q89d8 and q89d9 (rc6,
  goldens B143 and B145) -> q89e (rc7 rebase, 11-12 Oct; golden B147) -> q89f and q89g (13 Oct; golden B149). The
  rc6 -> rc7 rebase dropped three patches that upstream had merged.
- **Upstream candidates:** the patches that are not in q89g are held: the q6apm RFC (0202-0205; the read-done payload
  size was wrong), the GPU CLX series (0244-0245; the GPU did not start with it), the DW9800K update (0253; a chip-ID
  mismatch), the wcd939x port switches (0254), and two old candidates (the SoundWire IRQ and the hci_qca sleep reset),
  which were dropped.
- **Not sent upstream:** the iris colorimetry patch 0292 is carried in the kernel but is not sent upstream (owner's
  decision). The kernel requires an `Assisted-by` line on such patches.
- **Re-check at each rebase:** patches merged upstream are removed at the next rebase (v7.3 final, then 7.4).
- **Open kernel work:** DP over USB-C (link training and the power contract, see the feature matrix); camera into the
  hardware encoder (the pipeline does not negotiate); Chromium / Electron GPU path; the idle refresh (in the kernel,
  off by default, measured 74.8 Hz instead of 60 Hz); the K4 battery guard and the kernel layer of the thermal guard
  are not in q89g (whether they are still planned is unverified).

## U-Boot (iceland-u-boot)

- **Base:** v2026.10-rc5 (`UPSTREAM_COMMIT` a06e89ab05ea) with the infiniti-mainline series (14 patches) and the Pad 4
  series (`0002-iceland`, patches 0001-0010).
- **Install build v3** (commit aac9e744ec6f, `BUILD_INFO-v3`) is the boot path in `boot_b` on the installed tablet.
  Its patches:
  - 0008: it never resets or powers off by itself;
  - 0009: USB comes up without the boot loader;
  - 0010: `fastboot reboot-bootloader` reaches the boot loader without a key press.
  The plain build's SHA-256 and the footered build's SHA-256 are in the install guide's record.
- **Header and footer:** the boot header carries os_version 17.0.0 and patch level 2026-09 (mkbootimg 808ecd09). They must
  match the day's `boot_b` (anti-rollback). The AVB footer is made with the test key that `vbmeta_b` already chains.
- **Rehearsal build:** a separate build without any storage driver, so a rehearsal cannot write the tablet's storage.
  It is never installed.
- **Fastboot flashing** is disabled in the U-Boot builds; the boot loader's own fastboot performs the writes.

## Generic firmware

- The generic firmware is packaged in iceland-firmware (11.A.38-3: 278 files of stock 11.A.38, plus the decoded stock
  shell-temperature model). Each file is checked by sha256 against the manifest; the device package fetches releases
  against pinned sha256 values and refuses a mismatch.
- The unit-specific files (the sensor calibration registry, the Bluetooth address and the extraction record) are never
  published; the installer takes them from the tablet itself.

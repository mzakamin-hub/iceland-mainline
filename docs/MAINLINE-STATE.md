# Kernel and U-Boot state, 22 Oct 2026

This page is the state of the two upstream-facing ports: the kernel and U-Boot. The dated history is in
[../CHANGELOG.md](../CHANGELOG.md), the current versions in [RELEASE-NOTES.md](RELEASE-NOTES.md).

## Kernel (iceland-linux)

- **Build in use:** `7.3.0-next-20261020-iceland-00463-g9948599f2a47`, queue head **q90i**, branch
  `iceland-7.3-rc7-next` (tag `q90i`). It runs on the installed tablet, installed with dnf. The kernel package is
  `kernel-iceland 7.3.0.next.20261020.iceland.00463`; the build has no compiler warnings; `scripts/build.sh` gives
  the package's config exactly (configs `q90b`, `q90i`, `q90i-shipped`). The first install image (golden B149)
  carries q89g (`7.3.0-rc7-iceland-00426`, tag `q89g`).
- **Base:** linux-next `next-20261020` (`UPSTREAM_COMMIT` 8f7df005a756; Linux 7.3 plus the trees queued for 7.4)
  with 463 patch files: 110 in `0001-infiniti` (the infiniti-mainline base for SM8850), 305 in `0002-iceland` (the
  Pad 4 series) and 48 in the series `0003-glitchfix` (display-timing switches and diagnostics) and `0004-q90b` to
  `0011-q90i`. The rebase dropped 107 patches that are upstream in that base. The q90 kernels have no binder: the
  base removed the C driver, and the Rust one needs a Rust toolchain in the build.
- **Queue history:** q89 (rc4) -> q89b (rc6 rebase, 10 Oct) -> q89c-tb (tb323fu patches) -> q89d8 and q89d9 (rc6,
  goldens B143 and B145) -> q89e (rc7 rebase, 11-12 Oct; golden B147) -> q89f and q89g (13 Oct; golden B149). The
  rc6 -> rc7 rebase dropped three patches that upstream had merged. Since the install the queue grows on
  `iceland-7.3-rc7-next` and reaches the tablet through dnf: q89h to q89m (14-16 Oct: the charge pumps and USB-PD
  settings, the GMU keep-alive, upstream display, Wi-Fi and USB-C fixes, the battery energy), q89n to q89w (16-19 Oct:
  display stall, RTC and GPU preemption fixes, the DPU slave teardown after both timing engines stop, the in-place
  120 / 60 Hz change, the SMP2P sleep-state notifier, upstream fixes, the IOMMU in lazy mode, and DisplayPort over
  USB-C sized to the Type-C lanes, not yet tested with a monitor), q89x to q89z (20 Oct: display-timing switches),
  q90b to q90i (21-22 Oct: the 7.4 base with Qualcomm's split CPU cluster power domains and the rpmhpd fix that lets
  the GPU's CLX start; the display clock controller's own MX vote; dwc3-qcom keeping its interconnect votes across
  runtime suspend, which fixes the display glitches while the sensor hub streams; the A8xx crash-state capture made
  opt-in, so a GPU hang recovers; the Kaanapali CP protect table; the battery power at the nominal voltage; the memlat
  poll off; a config round: VA_BITS 48, HZ 250, PREEMPT_DYNAMIC, CoreSight / STM off).
- **Upstream candidates:** the patches that are not in q90i are held: the q6apm RFC (0202-0205; the read-done payload
  size was wrong), the GPU CLX series (0244-0245; superseded: the 7.4 base's rpmhpd fix makes CLX start), the DW9800K update (0253; a chip-ID
  mismatch), the wcd939x port switches (0254), and two old candidates (the SoundWire IRQ and the hci_qca sleep reset),
  which were dropped.
- **Not sent upstream:** the iris colorimetry patch 0292 is carried in the kernel but is not sent upstream (the
  project's decision). The kernel requires an `Assisted-by` line on such patches.
- **Re-check at each rebase:** patches merged upstream are removed at the next rebase (v7.3 final, then 7.4).
- **Open kernel work:** the rebase onto 7.4-rc1; DP over USB-C (a picture on a monitor; the link is sized to the
  lanes of the Type-C pin assignment, not yet tested; see the feature matrix); camera into the hardware encoder (the
  pipeline does not negotiate); Chromium / Electron GPU path; binder (needs Rust in the build); the K4 battery guard and
  the kernel layer of the thermal guard are not in q90i (whether they are still planned is unverified). The idle
  refresh is on since 22 Oct (30 Hz after 1 s on a static screen, set on the command line by iceland-device 0.28-32).

## U-Boot (iceland-u-boot)

- **Base:** v2026.10-rc5 (`UPSTREAM_COMMIT` a06e89ab05ea) with the infiniti-mainline series (14 patches) and the Pad 4
  series (`0002-iceland`, patches 0001-0015).
- **Install build** (v7, patches 0001-0015; v4 = 0001-0012; v3 = 0001-0010, commit aac9e744ec6f, `BUILD_INFO-v3`)
  is the boot path in `boot_b` on the installed tablet. Its key patches:
  - 0008: it never resets or powers off by itself;
  - 0009: USB comes up without the boot loader;
  - 0010: `fastboot reboot-bootloader` reaches the boot loader without a key press;
  - 0012 (v4): a power-on boot menu on the keys (Fedora, or the boot loader's fastboot);
  - 0013-0015 (v7): a stricter gate for the Android entry, the entry named BlissROM, and BlissROM started from the
    menu with the ramdisks, device tree and bootconfig that ABL prepared (the dual boot, [DUAL-BOOT.md](DUAL-BOOT.md)).
  The plain builds' SHA-256 are in iceland-u-boot's README; a footered image's hash depends on the tablet's `boot_b`.
- **Header and footer:** the boot header carries os_version 17.0.0 and patch level 2026-09 (mkbootimg 808ecd09). They must
  match the slot's current `boot` image (anti-rollback). The AVB footer is made with the key that `vbmeta_b` chains `boot`
  with.
- **Rehearsal build:** a separate build without any storage driver, so a rehearsal cannot write the tablet's storage.
  It is never installed.
- **Fastboot flashing** is disabled in the U-Boot builds; the boot loader's own fastboot performs the writes.

## Generic firmware

- The generic firmware is packaged in iceland-firmware (11.A.38-6: the generic files of stock 11.A.38, the decoded
  stock shell-temperature model, the sensor hub registry and two GPU firmware pairs, stock's and the vendor's). Each file is checked by sha256 against the manifest; the device package fetches releases
  against pinned sha256 values and refuses a mismatch.
- The unit-specific files (the sensor calibration registry, the Bluetooth address and the extraction record) are never
  published; the installer takes them from the tablet itself.

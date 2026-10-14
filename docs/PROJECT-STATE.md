# OnePlus Pad 4 ("iceland") mainline Linux - project state

Snapshot of 14 Oct 2026. The status is in [../README.md](../README.md); this page keeps the working picture: the goal, the
rules, where the work lives, how the tests are run, what is open and the lessons that cost the most time. The published
repositories are the only copies of the project's files that a reader can see.

## Goal and result

Mainline Linux (v7.3-rc7 plus the Pad 4 patch queue) with Fedora 44 GNOME on the OnePlus Pad 4 (Snapdragon SM8850
"Kaanapali", board "iceland"). The goal was reached on 13 Oct 2026: Fedora 44 GNOME is installed and boots on the
tablet. Testing before the install used RAM boots only, through test kits and rehearsals of the install image.

## Hard rules

- The tablet's storage is written only by the owner, by hand, after the PC checks and with each write confirmed. The two
  install writes (`userdata` and `boot_b`) were done that way on 13 Oct 2026. Test kits and rehearsals never write the
  storage; they RAM-boot.
- Every hardware value comes from the stock sources of the Pad 4 (the stock device tree, the firmware logs, the stock
  configuration). Values are not guessed.
- Unit data stays private: the partition backups and their carves, the persist / modem / EFS data, calibration and key
  material, the serial and the addresses, network names, camera traces and test media. The generic firmware may be
  published in the firmware package only (owner's decision, 11 Oct 2026).
- The repositories are public. Commits carry the author's name and `Signed-off-by`.
- The owner's connection and go-ahead come before every action on the tablet. Long runs are started in the background.

## Where the work lives

| What | Where |
|---|---|
| Kernel patch queue, configs, pins | iceland-linux (public): `patches/0001-infiniti`, `patches/0002-iceland`, `configs/`, `kernel.pin`, `scripts/` |
| U-Boot patch queue, install build record | iceland-u-boot (public): `patches/`, `uboot.pin`, `tools/install/` |
| Documents, feature matrix, device package, firmware manifest | iceland-mainline (public): `docs/`, `packaging/`, `firmware/` |
| Generic firmware package | iceland-firmware (public): tags 11.A.38-2 and 11.A.38-3 |
| Work folders, test material, logs and backups | the PC's private working folders; never published |

The feature matrix is generated: `docs/features/features-data.py` holds the rows and `docs/features/build.py` builds
`docs/FEATURES.md` and the page. Each proven result updates the rows, the page is rebuilt, and the commit carries the
privacy checks.

## How the tests run

1. A test kit is a RAM image: a U-Boot build with a Linux image, a busybox initramfs and the tablet's own test scripts.
   The kit is started with `fastboot boot`; nothing is written. Its results come back over the USB network and are kept
   on the PC.
2. A rehearsal boots the exact install image from RAM through the same chain as the installed system (U-Boot, shim, GRUB,
   our kernel), with the root served from the PC. It runs an acceptance list (one summary line: `INSTALL-ACCEPT n PASS,
   0 FAIL`) and a regression set. Suspend is never tested in a rehearsal (its root comes over USB), only in the kits and
   on the installed system.
3. Golden builds (B-runs) build the packages and the image on the tablet from the queue, and are accepted only after a
   final rehearsal with no failure in the regression set and no regression against the previous golden.
4. A kit's kernel build is checked against the exact kernel release string before the run; a kit's log checks ignore the
   kit's own summary lines.

Final goldens: B147 (13 Oct morning), then B149 (13 Oct 15:45, rehearsal r158, 0 failures). The install image was built from
B149 and checked offline (128 PASS, 0 FAIL) before the writes. Golden build 0.28-8 of the device package is not in an image yet.

## Install record (13-14 Oct 2026)

- Write 1, `userdata`: the install image (sha256 prefix `2246e9a7`, unpacked size 237,159,641,088 bytes), 267 s, OKAY,
  on 13 Oct at 18:31.
- Write 2, `boot_b`: the footered U-Boot v3 (footer sha256 prefix `4955ee98`), 2.3 s, OKAY, at 20:47. Fedora started from
  `boot_b` by itself at 20:48, after tethered boots for the first-boot setup.
- The boot counter did not get marked by the Fedora side on the installed system: the slot-mark guard refused the root on
  the loop device, so the tries fell from 7 to 3. The owner marked slot b by hand with `qbootctl` on 14 Oct (Active 1,
  Successful 1, Bootable 1). The fix is `iceland-device` 0.28-8 (commit 946ff95). It is tested on the PC but not yet in an
  image; its thermal file was installed on the tablet by hand on 14 Oct.

## Open items

Owner (physical or subjective):

1. The speaker listening check after the install, at 50 % and 100 %, against Android (make-up +9 dB, the owner's choice).
2. One night unplugged with the cover closed, to measure the standby drain.
3. Cover wake from sleep; USB host with a keyboard, a stick and a hub; a 5 GHz connection with its band recorded.
4. A DisplayPort monitor: picture, then sound over DP.
5. The wall chargers (5 V USB-A, USB-C PD, the OnePlus charger), attended.
6. The pen (tip, hover, buttons, pressure) and the keyboard cover (keys, touchpad, backlight, wake).

PC and rehearsal work:

1. Put 0.28-8 into an image and a rehearsal; update the installed system from the local repository after a snapshot.
   Rehearsal rows: the thermal boost and screen-off rows, and the slot-mark rows.
2. DisplayPort over USB-C: hotplug, link training and mode logs on the installed system; the power contract and lane count.
3. Camera into the hardware encoder (the pipeline does not negotiate on either camera).
4. Chromium and Electron GPU acceleration on Adreno 840 with Mesa 26.2.4.
5. Idle refresh: a debug round before any switch-on (it is off).
6. GStreamer 1.28.9 for BT.601 streams labelled 6/1/6.
7. Upstream merges: re-check at each rebase (v7.3 final, then 7.4).
8. Fedora 45 only after a rehearsal (not scheduled).

## Lessons (the expensive ones)

- Never read every regmap debug file under `/sys/kernel/debug`: unclocked register blocks can hang the kernel. Read one
  register map and only the lines needed.
- Never scan the TLMM pad registers through `/dev/mem` for pads that Linux does not use. The device tree's
  `gpio-reserved-ranges` belong to the secure world, and one such scan reset the tablet.
- The camera sensors answer on their I2C bus only while a sensor of the ADSP's sensor hub is streaming. Camera tests keep
  the sensor hub running.
- The ADSP and CDSP firmware ships split (`.mdt` plus `.bNN`); the kernel loads them as one `.mbn` after squashing.
- `KIT_DESC` and similar test labels must not contain a quote character.
- A GNOME Settings process started from a script needs `XDG_CURRENT_DESKTOP=GNOME`; `gnome-screenshot` does not work on
  GNOME 50.
- Kernel modules for devices without a driver are loaded by udev in a boot that matches an installed system. A test
  that loads only the early module list misses devices such as the sound card.
- The DMA-buf debug option strips pages from the importers' tables and turns every hardware-decoded frame green; it stays
  off in the distribution configuration.
- The ABL slot counter counts a try for every normal power-on of a slot that is not marked successful. Only Android's
  `qbootctl -m` (or Fedora's copy of it) marks a slot good. U-Boot does not.

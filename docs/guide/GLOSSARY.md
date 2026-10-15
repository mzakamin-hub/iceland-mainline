# Glossary

Terms as this project uses them (state 14 Oct 2026). "Pad 4" = OnePlus Pad 4 (OPD2514, codename iceland).

| Term | Meaning |
|---|---|
| **A/B slots** | every firmware and boot partition exists twice (`_a`, `_b`); the boot loader boots the active slot and keeps per-slot flags (successful, unbootable, retry count). Flashing a slot's boot partition resets its flags; each normal boot of a non-successful slot counts the retry count down; only Android or Fedora's `qbootctl -m` marks a slot successful, U-Boot does not. The installed Fedora system runs on slot b (`boot_b`) |
| **ABL** | Android Boot Loader: Qualcomm's (OnePlus-built, closed) UEFI application that boots Android and provides **fastboot**. Never written by this project |
| **ADSP** | the Hexagon audio DSP: runs audio (AudioReach), the **sensor hub** (SSC) and FastRPC services |
| **AOP / AOSS** | the always-on processor and its subsystem: the arbiter of the SoC's sleep states. "AOSS sleep" is the deepest SoC state (not reached on mainline) |
| **AudioReach / GPR / APM / PRM** | Qualcomm's audio framework on the ADSP and its Linux drivers (packet router, graph manager, proxy resource manager) |
| **AVB footer, vbmeta** | Android Verified Boot. `vbmeta_<slot>` signs or chains the boot images. The install build's `boot_b` image carries an AVB hash footer (footer prefix `4955ee98`), made with the AOSP test key that `vbmeta_b` already chains `boot` with, so that the image passes verification without a change to `vbmeta` (the planned approach; the install guide records the check). An unlocked tablet boots in the "orange" state despite verification errors, but not with invalid metadata |
| **blkmap** | a U-Boot block device made from a region of another device or of RAM. U-Boot maps `userdata` (or a `fedora` partition) as a disk with it |
| **BLS** | Boot Loader Specification entries (`/boot/loader/entries/*.conf`), read by Fedora's GRUB |
| **boot_b** | the boot partition of slot b. On the installed tablet it holds our U-Boot install build v3 (footered for AVB); U-Boot then starts Fedora from `userdata` |
| **BCL** | battery current limiting: PMIC alarms on low battery voltage, bound to thermal zones that cap the GPU / CPU (queue patches 0075-0076) |
| **CAMSS, CSIPHY, CSID, VFE** | the camera subsystem: PHY, decoder and front end. The hardware ISP (ICP / IPE) has no mainline driver |
| **CDSP / NPU** | the Hexagon compute DSP with the tensor accelerator (NSP). It runs through FastRPC; never stop it at run time |
| **CMA heap** | the contiguous memory heap (32 MiB). The final kernel does not offer it as a dma-heap (F2); camera frames come from the system heap |
| **coldplug** | re-triggering udev for devices that exist before user space, so that their modules load. Installed systems do it at boot; the test kits did it too |
| **CX collapse** | the SoC's core (CX) power rail switched off during sleep: the measurable sign of deep sleep (95-98 % of a sleep since queue patches 0113-0116) |
| **diag-L-efi.img** | the diagnostic U-Boot image of the bring-up tests (fastboot only, starts Linux through EFI). Not published; the install build v3 and `u-boot-iceland-v4.img` (`scripts/build.sh`) replace it for public use |
| **dracut-iceland** | the installed system's initramfs part (`iceland-device` files `dracut-iceland-*`): read-only flags for the UFS, the loop over `userdata` (the loop root), the rehearsal NBD carrier |
| **DSU** | Dynamic System Updates: Android runs a temporary system image (used once to get root for the backup without flashing) |
| **EDL** | Qualcomm's emergency download mode (9008). Not usable for this tablet (no public loader), so fastboot is the floor |
| **efisp** | a 3 MiB firmware-side partition named after the EFI System Partition. Not used by this project (`02-HARDWARE.md` section 6) |
| **ESP** | the EFI System Partition. Ours is FAT32 with 4096-byte sectors inside the Fedora disk image |
| **fastboot boot / flash** | `boot` loads an image into RAM (no write; the RAM tests use it). `flash` writes a partition (the install only: two writes, each made by hand after its checks) |
| **FastRPC, hexagonrpcd** | the remote-procedure-call path to the DSPs; `hexagonrpcd` serves the DSP's file requests (the sensor hub's config tree) |
| **install checks** | the checks before the first write, in `INSTALL-PLAN.md` section 1 (backups, slot flags, rescue keys, RAM test of the image) |
| **genwf** | the generator of a test run's tablet script (project tooling, not published) |
| **GKI** | Google's generic kernel image used by stock Android 16 (6.12.58) |
| **GMU** | the GPU management unit. Its DT node never gets its own driver, hence `FW_DEVLINK_SYNC_STATE_TIMEOUT` |
| **golden** | the tested image of one state (kernel, device package, firmware, Fedora refresh), named by its build number; an install image is made from a golden that passed its RAM tests |
| **header v2 / v4** | Android boot image formats. `iceland-u-boot` builds U-Boot as v4 (kernel = gzip of U-Boot with its device tree inside); v2 carries the device tree in the header |
| **hold the tablet** | the project's stop word: every tablet action stops at once |
| **iceland-device** | the device package (configuration and scripts: udev, UCM, systemd units, the battery guard, the thermal policy, update rules, the slot marker). Version 0.28-8 |
| **iceland-firmware** | the package of the generic firmware (11.A.38-3); unit-specific files are never in it |
| **infiniti** | the OnePlus 15 mainline port (same SoC); its 132 kernel commits and 14 U-Boot commits are our base series (`patches/0001-infiniti`) |
| **Iris** | Qualcomm's video codec block (VPU 4.0), driver `qcom-iris` |
| **kernel-iceland** | our kernel package (Fedora rpm, installonly, three kept) |
| **kernel.pin** | the upstream tag / commit and the expected tree hashes the queue must reproduce (`iceland-linux`) |
| **kit** | a RAM-boot test bundle of the bring-up tests (U-Boot, a Linux image, the firmware, optional Fedora root). Not published |
| **LUN** | one of the UFS device's 6 logical units (sda-sdf). Each has 4096-byte blocks |
| **loop root** | the installed system's root filesystem: a btrfs filesystem on a loop device (`/dev/loop0`) backed by the `userdata` partition, set up by the initramfs carrier (`dracut-iceland-carrier`). Only the boot LUN is writable, and only for one `qbootctl -m` call (0.28-8) |
| **matrix** | the feature matrix (`features-data.py`, the source; `FEATURES.md` lists the working features) |
| **NBD** | network block device: the rehearsal's root disk served by the PC over the USB link |
| **pmic_glink** | the message channel to the charger firmware on the **SoCCP** (battery, USB-C / UCSI, altmode) |
| **qbootctl** | Fedora's package (0.2.2-2) that reads and sets the A/B slot flags. The `iceland-slot-mark` service calls `qbootctl -m` to mark the running slot successful; it was skipped on the installed loop root until 0.28-8 |
| **queue, queue patch NNNN** | the Pad 4 kernel patch series `iceland-linux/patches/0002-iceland/NNNN-*.patch` (294 patches; numbers have gaps, the newest is 0306 in q89g) on top of `patches/0001-infiniti` (132) |
| **q89g, qNN** | the kernel queue state named by its tag: `q89g` is the current head (Linux 7.3-rc7, kernel `7.3.0-rc7-iceland-00426-g520e85da9244`). Earlier tags (q89b, q89d8, q89e, q89f, ...) are the same series at earlier points |
| **RAM boot** | starting an image from RAM with `fastboot boot`; nothing is written; a reboot returns to the normal boot |
| **rehearsal** | the install's proof without writing: the real boot chain from RAM, with the root disk on the PC. The image is written only after its rehearsal passed |
| **RPMh, RSC, BCM** | the resource-power manager (hardware): rails, clocks and bandwidth votes collected from all processors |
| **SBS / DBS** | the Wi-Fi chip's single-band / dual-band simultaneous modes; SBS is off on this board as on stock (queue patches 0066-0068) |
| **shim, GRUB** | Fedora's first-stage EFI loader and its boot loader, both on the ESP |
| **SoCCP** | the SoC's charger and USB-PD co-processor, started by the boot chain; Linux attaches to it |
| **SSC / sensor hub** | the ADSP's sensor core: accelerometer, gyro, magnetometer, light / proximity, hall |
| **s2idle** | suspend-to-idle, the only system sleep state of this SoC on Linux |
| **sync_state** | the moment a provider driver drops the boot-time votes once all its consumers have probed |
| **TDM** | the speaker audio interface (time-division multiplexed, 8 x 32 bit) |
| **TSENS** | the SoC's temperature sensor controllers (7) |
| **U-Boot install build** | the U-Boot build that the install writes to `boot_b` (`u-boot-iceland-usb.img`, with an AVB footer made for the tablet's `boot_b`; v4 = patches 0001-0012, v3 = 0001-0010). Its rehearsal counterpart `u-boot-iceland-rehearsal-usb.img` has no UFS driver and is for rehearsals only |
| **UCM** | ALSA's use-case manager profile: how PipeWire finds the speakers and microphones |
| **userdata** | the tablet's large data partition. Since the install it holds the whole Fedora disk image; Android no longer starts |
| **XBL / PBL** | the primary boot loader (eXtensible Boot Loader) and the boot ROM. Never written |

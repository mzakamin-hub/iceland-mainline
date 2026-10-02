# Glossary

Terms as this project uses them. "Pad 4" = OnePlus Pad 4 (OPD2514, codename iceland).

| Term | Meaning |
|---|---|
| **A/B slots** | every firmware and boot partition exists twice (`_a`, `_b`); the boot loader boots the active slot and keeps per-slot flags (`slot-successful`, `slot-retry-count`, `slot-unbootable`). The test tablet runs on slot b |
| **ABL** | Android Boot Loader: Qualcomm's (OnePlus-built) UEFI application that boots Android and provides **fastboot**. Never written by this project |
| **ADSP** | the Hexagon audio DSP: runs audio (AudioReach), the **sensor hub** (SSC) and FastRPC services |
| **AOP / AOSS** | the always-on processor and its subsystem: the arbiter of the SoC's sleep states. "AOSS sleep" is the deepest SoC state (not reached on mainline) |
| **area-combo-N, run N** | a numbered kit run of campaign 2 (1 Oct onward); log sets in `~/mainline/build/area-combo-N/` and `iceland-mainline/docs/tests/area-combo-N/`. Older names: `area-display-N`, `area-video-N`, `pc-0NN` (PC relay kits), `linux-runN` |
| **AudioReach / GPR / APM / PRM** | Qualcomm's audio framework on the ADSP and its Linux drivers (packet router, graph manager, proxy resource manager) |
| **AVB, vbmeta** | Android Verified Boot. `vbmeta_<slot>` signs or chains the boot images. An unlocked tablet boots in the "orange" state despite verification errors, but not with invalid metadata |
| **B run, R0-R4, U1-U3** | the install rehearsal's runs: B builds the image on the tablet over the network disk; R0 reads facts; R1 / R2 boot the image; U* rehearse updates; R4 is the final boot of the exact file to be written |
| **BCL** | battery current limiting: PMIC alarms on low battery voltage, bound to thermal zones that cap the GPU / CPU (queue 0075-0076) |
| **blkmap** | a U-Boot block device made from a region of another device or of RAM. U-Boot maps `userdata` (or a `fedora` partition) as a disk with it |
| **BLS** | Boot Loader Specification entries (`/boot/loader/entries/*.conf`), read by Fedora's GRUB |
| **CAMSS, CSIPHY, CSID, VFE** | the camera subsystem: PHY, decoder and front end. The hardware ISP (ICP / IPE) has no mainline driver |
| **CDSP / NPU** | the Hexagon compute DSP with the tensor accelerator (NSP). It runs through FastRPC; never stop it at run time |
| **CMA heap** | the contiguous memory heap (`/dev/dma_heap/reserved`, 32 MiB). The device package makes it root-only so that camera frames use the system heap |
| **coldplug** | re-triggering udev for devices that exist before user space, so that their modules load. Installed systems do it at boot; the kits do it since 2 Oct |
| **CX collapse** | the SoC's core (CX) power rail switched off during sleep: the measurable sign of deep sleep (95-98 % of a sleep since queue 0113-0116) |
| **diag-L-efi.img** | the diagnostic U-Boot boot image every RAM kit starts: fastboot only, starts Linux through EFI. It cannot write the storage |
| **dracut module `90iceland`** | the installed system's initramfs part: read-only flags for the UFS, the loop over `userdata`, the rehearsal NBD carrier |
| **DSU** | Dynamic System Updates: Android runs a temporary system image (used once to get root for the backup without flashing) |
| **EDL** | Qualcomm's emergency download mode (9008). Not usable for this tablet (no public loader), so fastboot is the floor |
| **efisp** | a 3 MiB firmware-side partition named after the EFI System Partition. Not used by this project (`02-HARDWARE.md` section 6) |
| **ESP** | the EFI System Partition. Ours is FAT32 with 4096-byte sectors inside the Fedora disk image |
| **fastboot boot / flash** | `boot` loads an image into RAM (no write; all tests use it). `flash` writes a partition (only in the install guide, with the owner's OK) |
| **FastRPC, hexagonrpcd** | the remote-procedure-call path to the DSPs; `hexagonrpcd` serves the DSP's file requests (the sensor hub's config tree) |
| **fwsuper** | the private carve of the backup's `super` and firmware partitions on the PC (`build/fwsuper`). Never committed |
| **G1-G14** | the install gates in `INSTALL-PLAN.md` section 1 (backups, checks, rehearsal, sleep drain) |
| **genwf.py** | the generator of a kit run's tablet script and PC probe from a template run |
| **GKI** | Google's generic kernel image used by stock Android 16 (6.12.58) |
| **GMU** | the GPU management unit. Its DT node never gets its own driver, hence `FW_DEVLINK_SYNC_STATE_TIMEOUT` |
| **header v2 / v4** | Android boot image formats. U-Boot is wrapped as v4 (kernel = gzip of U-Boot with its DT); kit Linux images are v2 (kernel, ramdisk, DT) |
| **hold the tablet** | the owner's stop word: every tablet action stops at once |
| **iceland-device** | the device package (configuration and scripts: udev, UCM, systemd units, the battery guard, thermal policy, update rules) |
| **infiniti** | the OnePlus 15 mainline port (same SoC); its 138 kernel commits and 14 U-Boot commits are our base series |
| **Iris** | Qualcomm's video codec block (VPU 4.0), driver `qcom-iris` |
| **kernel-iceland** | our kernel package (Fedora rpm, installonly, three kept) |
| **kernel.pin** | the upstream tag / commit and the expected tree hashes the queue must reproduce (`iceland-linux`) |
| **kit** | a RAM-boot test bundle: U-Boot diag L + a Linux image (kernel, initramfs shim, DT, firmware, optional Fedora root) + runner script + checksums |
| **LUN** | one of the UFS device's 6 logical units (sda-sdf). Each has 4096-byte blocks |
| **matrix** | the feature matrix (`features-data.py` -> `FEATURES.md`, the published page) |
| **NBD** | network block device: the rehearsal's root disk served by the PC over the USB link |
| **pmic_glink** | the message channel to the charger firmware on the **SoCCP** (battery, USB-C / UCSI, altmode) |
| **priv/** | the private part of a workflow folder (stock data, traces): never copied into docs or commits |
| **queue, queue patch NNNN** | the Pad 4 kernel patch series `iceland-linux/patches/0002-iceland/NNNN-*.patch` (0001-0174 on 2 Oct, 22:30) |
| **qNN, binqNN** | test kernel NN and its build output folder (`~/mainline/build/binqNN`) |
| **RAM boot** | starting an image from RAM with `fastboot boot`; nothing is written; a reboot returns to Android |
| **rehearsal** | the install's proof without writing: the real boot chain from RAM, with the root disk on the PC |
| **RPMh, RSC, BCM** | the resource-power manager (hardware): rails, clocks and bandwidth votes collected from all processors |
| **SBS / DBS** | the Wi-Fi chip's single-band / dual-band simultaneous modes; SBS is off on this board as on stock (queue 0066-0068) |
| **shim, GRUB** | Fedora's first-stage EFI loader and its boot loader, both on the ESP |
| **SoCCP** | the SoC's charger and USB-PD co-processor, started by the boot chain; Linux attaches to it |
| **SSC / sensor hub** | the ADSP's sensor core: accelerometer, gyro, magnetometer, light / proximity, hall |
| **s2idle** | suspend-to-idle, the only system sleep state of this SoC on Linux |
| **sync_state** | the moment a provider driver drops the boot-time votes once all its consumers have probed |
| **TDM** | the speaker audio interface (time-division multiplexed, 8 x 32 bit) |
| **TSENS** | the SoC's temperature sensor controllers (7) |
| **U-Boot install build / rehearsal build** | `u-boot-iceland.img` (to be written to `boot_b`; maps `userdata`) vs `u-boot-iceland-rehearsal.img` (no UFS driver; for rehearsals only) |
| **UCM** | ALSA's use-case manager profile: how PipeWire finds the speakers and microphones |
| **workflow** | one background agent per open topic, preparing on the PC in `~/mainline/build/wf/<name>/` while the main session tests on the tablet |
| **XBL / PBL** | the primary boot loader (eXtensible Boot Loader) and the boot ROM. Never written |

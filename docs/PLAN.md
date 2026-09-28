# OnePlus Pad 4 (`iceland`, SM8850P) — mainline Linux plan v4

Version 4, 2026-09-28 (evening). Replaces v3 (v3's history is in git; v2 and the discovery notes are in
[RESEARCH.md](RESEARCH.md)).

Changes from v3:
- **Target OS: Fedora 44 Workstation (GNOME), aarch64** (user's decision, 2026-09-28 20:38). pmOS is no longer first:
  pmaports has no OnePlus 15 package to derive from, and Fedora 44 already runs GNOME on the tablet in RAM.
- Phases 2 and 3 are done or nearly done; Phase 4 is rewritten as the Fedora install; the remaining hardware moves to
  Phase 5 in the PC's "B" order.
- **Sleep/standby, hardware-matched thermal handling, and power management (charging, USB-C PD/OTG, whole
  system)** added as Phase 5-PM. Thermal and charging safety are gates for the install.
- **Dual boot (Android + Fedora)** added as Phase 4-DB: U-Boot in the recovery partition, and Fedora in its own
  partition carved from userdata (the user chooses between 4e single-boot and 4-DB).

## Goal

**Fedora 44 Workstation with GNOME, installed on the Pad 4**, booted ABL → U-Boot → EFI → GRUB → our kernel + DTB,
with kernel updates through dnf and no reflashing.
- Other distros (Arch Linux ARM, pmOS, Debian testing, Kali, latest Ubuntu) become **later, optional** targets
  (Phase 7). They reuse the same kernel source and config (`distro-neutral.config` keeps SELinux and AppArmor both
  built in).
- Long-term, **upstream** remains the real "any distro" answer: once the Pad 4 is in mainline Linux and U-Boot,
  Fedora's own kernel boots it and our kernel package disappears.

## What is verified (all by RAM boot; nothing has been written to the tablet)

| Item | Evidence |
|---|---|
| U-Boot RAM-booted by ABL: display, USB fastboot, UFS read, EFI | diag runs 3–4 |
| Linux 7.3-rc4 + infiniti (138) + Pad 4 queue (0001–0035) | iceland-linux 6fcead4 |
| Native display: MSM DRM, dual DSI + DSC, **144 Hz** (stock timing), KTZ8869 backlight | pc-007, pc-023 |
| CPU thermal trips mirroring stock, tested under load; board and flash thermistors | pc-002/003, pc-021 |
| Touch firmware (SRAM download); the touch screen is a libinput device. The pen is ignored by libinput (resolution missing) | pc-008, pc-024 Y9 |
| Wi-Fi (WCN7860, ath12k) + scan; Bluetooth (hci_qca) | pc-009/010 |
| Battery and USB-C data over pmic-glink (SoCCP), units fixed; lid switch; rear flash LEDs | pc-011..019 |
| ADSP boots; the sound card registers (no playback yet) | pc-010, pc-017 |
| Firmware extractor on the tablet (modem_a/bluetooth_a/persist read-only; `super` not yet) | pc-023 |
| **Fedora 44 in RAM:** systemd as PID 1, dnf through the PC, the Adreno 840 renders (freedreno, Mesa 26.2.3), Wayland 120 Hz (glmark2 1836), **GNOME Shell 50 with gdm autologin** | pc-024 Y7–Y9 |
| The early resets were the kit's own `/dev/mem` sampler, not the kernel | pc-022 |

## Architecture

```
ABL (stock) → U-Boot (boot partition, or RAM-booted from the PC) → blkmap userdata → EFI boot manager
  → shim/GRUB on the Fedora ESP → BLS entry → our kernel (kernel-iceland rpm) + our DTB + dracut initramfs
  → Fedora 44 Workstation (btrfs root in userdata)
```
- **U-Boot** (`iceland-u-boot`): infiniti-mainline U-Boot + the Pad 4 board. It never writes storage (fastboot flash
  compiled out).
- **Kernel** (`iceland-linux`): one source + one config. Boot-critical drivers built in; BT/ath12k as modules.
- **Firmware:** extracted from the user's own tablet and OTA, never committed or uploaded.
- **Device files** (UCM, udev, units): one FHS tree under `/usr/lib`.

## Phases

Tablet rule for every phase: RAM boot and allowlisted commands only, until a step explicitly says otherwise and the
user agrees. The PC session runs kits unattended (KNOWLEDGE §2 rule 11), so kits must log their own state.

### Phase 1 — U-Boot bring-up ✅
### Phase 2 — First Linux shell from RAM ✅
### Phase 3 — Core hardware over RAM boot ✅ (except items that need a person: touch/pen/lid events, 5/6 GHz, OTG)

### Phase 4 — Fedora 44 Workstation (GNOME) install

**4a. RAM rehearsal (no writes; in progress on the PC).** This uses the proven `phase4/` workflow: Container Base
rootfs → dnf through `tools/relay/usb-proxy.py` → `rootfstar` hand-back → `ROOTFS_URL`, with systemd as PID 1 in
`ROOTFS_MODE=pid1` (never `switch`).
- Y10: boot `rootfs-gnome.tar.gz` and judge the GNOME session from the journal. The user gives a 30 s touch window.
- **Rehearse the real install in RAM too.** Loop-mount the official `Fedora-Workstation-Disk-44` raw image's
  partitions *in RAM on the tablet* (from the PC over `ROOTFS_URL`, or a trimmed copy). Install our kernel rpm,
  firmware and config into it with the same steps as 4c, and boot that tree in `pid1` mode. This proves the final
  image's userland on the tablet before anything is written.

**4b. Packages and configuration (built in the cloud or on the PC; reproducible, GPL-clean).**
1. **`kernel-iceland` rpm** (own spec, not `make binrpm-pkg`, so the name doesn't clash with Fedora's `kernel`):
   - `/usr/lib/modules/<kver>/{vmlinuz,dtb/qcom/kaanapali-oneplus-iceland.dtb,…}` + modules + System.map + config;
   - `%posttrans`: `kernel-install add` (dracut initramfs + BLS entry in XBOOTLDR);
   - a **kernel-install plugin** that copies the DTB to the ESP as `dtb/qcom/kaanapali-oneplus-iceland.dtb`, where
     U-Boot's EFI boot manager looks for `fdtfile`, and also writes a BLS `devicetree` line as a second path;
   - BUILD_INFO with the source commits; the source rpm is kept next to it (GPL).
2. **Fedora's own kernel must not take over:**
   - `/etc/sysconfig/kernel`: `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=no`;
   - dnf `excludepkgs=kernel kernel-core kernel-modules*` in the image (Fedora's kernel has no Pad 4 support).
   - This is revisited once the Pad 4 is upstream.
3. **Kernel command line (BLS options):**
   - `root=UUID=… rootflags=subvol=root`, the image's own;
   - `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` until the drivers are complete;
   - `console=tty0`; no earlycon;
   - `lsm=` including `selinux`: Fedora runs SELinux enforcing, which our config supports.
4. **dracut** config (`/usr/lib/dracut/dracut.conf.d/iceland.conf`):
   - UFS, PHY, pinctrl and clocks are built in, so no hostonly surprises;
   - add the GPU firmware (`gen80200_*`, the zap) and the touch firmware to the initramfs, so the display and GPU
     come up early (troikoss lesson).
5. **Firmware** into `/usr/lib/firmware/updates/` (takes precedence over and doesn't conflict with Fedora's
   `linux-firmware`):
   - written by `fw-extract.sh` on the tablet from its own partitions;
   - the `super` contents (GPU zap, vpu, Wi-Fi odm BDF/regdb, touch, `tfa98xx.cnt`, pen) come from the PC's OTA until
     `super` is mapped;
   - the audio topology and the converted touch firmware come from the repo tools;
   - built on the device or PC as a local, never-uploaded `iceland-firmware` rpm, or just files.
6. **Device overlay rpm `iceland-device`** (GPL, in the repo):
   - UCM with **volume caps** (no speaker playback before TFA9865 protection);
   - `ath12k` loaded late (a modprobe `softdep` or a unit after USB);
   - BD address from wlan0's MAC (`btmgmt public-addr` unit);
   - libinput quirks until the pen reports resolution;
   - logind lid handling; sleep hooks in `/usr/lib/systemd/system-sleep/`;
   - journald size cap; `sleep.target` unmasked if Fedora masks it (Tab S6 trap).

**4c. Building the install image (on the PC; nothing on the tablet).** Start from the official
`Fedora-Workstation-Disk-44-*.aarch64.raw.xz` (checksum-verified by `phase4/fetch-fedora.sh`; DOS label: 500 MB ESP,
2 GB XBOOTLDR, btrfs root):
- install the three rpms above offline (`dnf --installroot`, or on the tablet during 4a);
- add the ESP `dtb/` file;
- `touch /.autorelabel` (SELinux labels after offline changes);
- convert it with `img2simg` into a **sparse** image.

**4c+. Apps in the final build (the user asked for a full GNOME desktop, not the lean test set).**
- **Base = the full Fedora 44 Workstation default set**, i.e. everything in the official Workstation image and the
  `workstation-product-environment` group. Among others: **Files (Nautilus)**, **Software (GNOME Software, the
  Fedora app store)**, Settings, Firefox, Ptyxis terminal, Text Editor, Calculator, Calendar, Contacts, Clocks,
  Weather, Maps, the image viewer, the video player, the document viewer, Disks, Disk Usage, System Monitor,
  Characters, Fonts, Logs, Connections and LibreOffice.
  - The exact Fedora 44 list comes from `dnf group info workstation-product-environment` (relay 008). Nothing is
    removed from it.
- **Added for the tablet:**
  - `gnome-extensions-app`, `gnome-tweaks`;
  - Flatpak with **Flathub enabled** through Fedora's third-party repositories switch, so GNOME Software shows the
    full catalogue (aarch64 builds);
  - GNOME's built-in on-screen keyboard (on when no keyboard is attached);
  - `powertop` and `lm_sensors` for the power and thermal checks;
  - `bluez` tools; `iio-sensor-proxy` for auto-rotate once sensors work;
  - Extension Manager from Flathub is optional.
  - Snapshot (camera) stays, but it won't find a camera until Phase 5.
- **GNOME Software must not break the boot:**
  - Fedora's `kernel*` packages are excluded (`excludepkgs`), so Software's updates never install them;
  - `kernel-iceland` updates come from our own dnf repo (a local or `file://` repo first; a private repo later, only if
    the user wants one);
  - **Fedora version upgrades (44 → 45) are hidden or blocked** until they've been tested with our kernel. The
    `gnome-software` "upgrade" banner is turned off in the image's defaults;
  - offline updates (PackageKit + systemd offline-update reboot) are tested once, so the reboot goes through U-Boot
    and comes back.
  - fwupd's UEFI capsule plugin is disabled: U-Boot is not a firmware target, and flashing through it must never
    happen.
- **aarch64 caveat:** almost every GNOME and Flathub app exists for aarch64. A few proprietary apps (for example
  Chrome, some games or Steam) are x86-only; Firefox is the browser, and Chromium is available.
- **Checked in 4a:** the RAM rehearsal (Y10 and the Workstation-image rehearsal) opens Files, Software (browse,
  install and remove a Flatpak and an rpm), Settings (display, power, Wi-Fi, Bluetooth, battery) and Firefox, all
  judged from the journal and app logs, plus the user's touch window.

**4d. Before any write (the user's explicit OK; in this order).**
1. Accept that flashing userdata **erases Android's data on both slots** (LineageOS on slot b uses the same userdata).
   Repartitioning is not an option (hard stop), so this is the only way to get disk space.
2. File-level copy of `/data/vendor` (TEE/TA files, needed later by QTEE/minkipc) and persist, read-only, from
   LineageOS with adb root. The raw userdata backup is FBE-encrypted and useless for this.
3. Confirm the existing 151-partition backup and the stock 11.A.38 package are on the PC.

**4e. The writes (each one approved separately; the user runs the commands).**
1. **userdata ← the sparse Fedora image, flashed with stock ABL `fastboot flash userdata`** (ABL supports sparse images;
   max-download 805 MB, so it goes in chunks automatically).
   - Our U-Boot keeps fastboot flash compiled out. No custom writer is needed, and nothing else on the UFS is touched.
   - Alternative if ABL refuses: `dd` from a RAM-booted Linux through a guarded installer (GPT name `userdata` only,
     size check, typed confirmation).
2. **Boot it tethered first:** `fastboot boot` U-Boot from the PC, then U-Boot → `bootefi bootmgr` → Fedora.
   - GNOME first-boot, dnf updates (with our kernel held), and a reboot loop.
3. **Only then choose where U-Boot lives** (the user's decision): the boot partition of the **current** slot (no slot
   switching), keeping the other slot's Android boot image for rollback. Rollback = flash back the saved boot image
   (the proven 2-minute loop).
- **Gate before 4e:** Phase 5-PM A items 1–4 (skin, XO, GPU, BCL) pass their load tests in RAM, and 5-PM C charging
  step 2 (thermal derating, termination, cell safety) is confirmed, or charging stays attended-only with an 80 %
  limit.
- **Exit:** Fedora 44 GNOME boots from UFS without the PC; our kernel updates through dnf; rollback tested once.

### Phase 4-DB — Dual boot: Android + Fedora (the user asked for it; replaces 4d/4e when chosen)

Goal: Android (the current slot's OS: LineageOS on slot b today, or stock OxygenOS) stays the default. Fedora is
one key press away. Neither OS ever writes the other's partitions.

**Boot selection: U-Boot in the recovery partition (recommended).**
- The Pad 4 has dedicated `recovery_a`/`recovery_b` partitions (100 MiB each; GPT entries 27 and 70 on LUN 4, seen
  in U-Boot run 4). ABL boots `recovery_<slot>` for **Power + Volume Up**, `adb reboot recovery`, or "Restart to
  recovery" in Android's power menu.
- So `recovery_<current slot>` ← the same U-Boot image we RAM-boot today (header v4, kernel = gzip(u-boot.bin)).
- Normal power-on → ABL → `boot_<slot>` → **Android**, untouched: ABL still sets up the root of trust, the cmdline,
  vendor_boot and dtbo, so keystore/FBE keep working.
- Power + Volume Up (or `adb reboot recovery`) → ABL → U-Boot → EFI → GRUB → **Fedora**.
- From Fedora, a normal `reboot` returns to Android.
- **Cost:** Android's own recovery is replaced. To sideload or reset Android, flash the saved stock/LineageOS
  recovery image back temporarily; the images are in the 151-partition backup. A/B OTAs don't need recovery
  (update_engine).
- **One write, easy to undo:** `fastboot flash recovery_<slot> u-boot-iceland.img` from stock ABL. Rollback = flash the
  saved recovery image. There's no slot switching and `boot` isn't touched.
- **Check first (no write):** that ABL boots a header v4 image from recovery the way it does with `fastboot boot`.
  Evidence can come from the LineageOS install history and ABL behaviour. The flash itself is the test.

**Alternatives (not recommended):**
- **Key-selector in the Android boot kernel** (Project Aloha DualBootKernelPatcher style, see research/gts6l-tab-s6.md):
  a shellcode in `boot_<slot>` reads a volume key and jumps to an embedded U-Boot, otherwise it continues into Android.
  It keeps recovery, but it patches Android's kernel (redo after every update), and reading the PMIC key over SPMI
  from shellcode is hard. Only a fallback if ABL won't boot U-Boot from recovery.
- **Slot-based** (Android on one slot, U-Boot as the other slot's boot): switching needs `fastboot set_active` (a hard
  stop), OTAs overwrite the other slot, and ABL's retry counter falls back unpredictably. Rejected.
- **U-Boot boots Android:** Android needs ABL's root-of-trust handover (keymint/FBE, AVB state, bootconfig). Not
  possible from U-Boot. Rejected.

**Storage: a separate Fedora partition (needs the user's explicit OK: repartitioning is a hard stop).**
- Android's userdata is metadata-encrypted and FBE, so Fedora can't live in a file inside it. `super` and the other
  partitions are full. Space has to come from **shrinking userdata** on LUN 0 (235.9 GB today).
- Proposed layout on LUN 0; the user picks the sizes:
  - `userdata`: same name, type GUID and attributes, e.g. ~96 GB;
  - `fedora`: e.g. ~128 GB, the Fedora disk;
  - optional `shared`: a few GB of exFAT for swapping files between the two OSes.
- **Procedure (each step approved separately; the user runs the commands):**
  1. Back up the LUN 0 GPT (`sgdisk --backup` from a RAM-booted Linux, read-only) plus the existing 151-partition
     backup. Also do the file-level `/data/vendor` + persist copy (4d).
  2. **Android data is wiped once.** userdata gets reformatted at its new size, and all apps and data are lost.
     Then Android re-encrypts on first boot.
  3. From a RAM-booted Linux kit with a guarded partitioner: only LUN 0, only entry `userdata` shrunk and the new
     entries appended, with a dry run printed and a typed confirmation.
  4. `fastboot -w` (ABL) formats the new userdata. Boot Android once and check it.
  5. Write the Fedora image into `fedora`, with a guarded `dd` from RAM Linux (GPT name `fedora` only). Alternatively
     use ABL `fastboot flash fedora` if ABL accepts a non-Android partition name; check that first.
  6. Flash U-Boot into `recovery_<slot>` (see above).
- **U-Boot env for dual boot:** `fedora_blkmap` maps the partition named `fedora` instead of `userdata`
  (`part start/size scsi 0 fedora`). `bootcmd` = `run fedora_blkmap; bootefi bootmgr; fastboot usb 0`. It's still
  read-only: U-Boot never writes the UFS.
- **Zero-repartition alternative:** Fedora on a USB-C SSD, with Android untouched. It needs U-Boot USB host (untested)
  and working OTG power (on the OnePlus 15, OTG works only with external PD), so it's research, not the plan.

**Keeping the two OSes compatible:**
- **Firmware follows Android updates.** Fedora loads the remoteproc/Wi-Fi/BT firmware straight from the **current
  slot's** read-only partitions (modem, bluetooth) at boot: `fw-extract.sh` as a boot unit, or read-only mounts
  plus `firmware_class.path`. So an Android OTA that changes firmware doesn't break Fedora. `super` contents
  (GPU zap, odm) are refreshed by the same unit once `super` mapping works; until then they come from a copy.
- **Android OTAs flip slots:** after an OTA the new slot's `recovery` is the stock one again. Re-flash U-Boot there
  (a one-line helper, like re-patching Magisk). Kits and helpers never switch slots themselves.
- **Clock:** the PMIC RTC reads 1970 and Android keeps its offset in `/data`. Fedora uses NTP and systemd's timestamp
  file, and never writes the RTC unless that's proven harmless to Android.
- **Isolation:** Fedora mounts no Android partition read-write (persist and modem stay read-only, and there's no
  `userdata` access). Android ignores the unknown `fedora`/`shared` partitions.
- **Exit:** power-on boots Android with its data intact; Power + Volume Up boots Fedora GNOME from `fedora`; each OS
  survives the other's reboot; an Android OTA plus re-flashing U-Boot to recovery keeps both working; rollback is
  tested once (restore recovery; to undo the split, restore the GPT backup and `fastboot -w`).

### Phase 5 — Remaining hardware (on Fedora; test changes by RAM boot first, then as rpm updates)
In the PC's "B" order (KNOWLEDGE §13); sleep and thermal are specified in Phase 5-PM below:
1. suspend/resume (s2idle + RTC wake) → Phase 5-PM B;
2. Wi-Fi under NetworkManager, 5/6 GHz and regdomain;
3. BT address + pairing;
4. audio: speakers on Primary TDM, the TFA9865 protection, UCM, headset, mics;
5. touch/pen/lid events: nt36536 pen `input_abs_set_res`, lid closing;
6. USB host/OTG with PD, DisplayPort alt mode;
7. GPU extras: turnip when Mesa lands the a840, GPU cooling;
8. video (Iris), cameras (SC1320CS/SC820CS + CAMERA_ICP), sensors (SSC via hexagonrpcd), keyboard accessory;
9. `super` mapped for the extractor;
10. kernel loose ends (SoundWire port counts, pstore across PS_HOLD).

### Phase 5-PM — Sleep, standby and thermal handling matched to the Pad 4 (the user asked for it)

This runs before and alongside the install: **the thermal part is a gate for Phase 4e/4-DB** (no installed system
without skin and battery protection). Sleep is the gate for "daily use". Everything is tested by RAM boot first,
unattended with its own logging, as usual.

#### A. Thermal: rebuild stock's policy in the kernel, sensor by sensor

The Pad 4's own sensors and the stock policy, read from the live stock DT (capture 2) and the stock thermal zones
(capture 3):

| Stock zone | Sensor (ADC channel / label) | Stock trips | Our state |
|---|---|---|---|
| `cpu-*`, `cpullc-*` (20) | TSENS | 105 (HAL) / 112 / 114 passive, 125 hot | ✅ mirrored (0023), held at 105 °C under load |
| `cpu-hw-trip-0/1` | LMh hardware | 95 °C | check that the kaanapali firmware limits on its own (SCMI perf) and that Linux sees the throttling |
| `gpuss-0..10` | TSENS | infiniti's GPU trips (value to confirm against stock) | check the GPU cooling map with glmark2 held for 10 min |
| **`sys-therm-2` = `pmh0101_skin_therm`** (0x144) | the **skin** thermistor | **48 / 49 / 50 / 60 / 61 °C** steps (userspace "gears"), 90 °C | **missing: the key one for a tablet held in the hands** |
| `sys-therm-0` = `pmk8850_xo_therm` (0x44) | XO / board | 78 / 80 °C → CPU pause + cluster frequency caps (state 5+), 90 °C hot | missing |
| `sys-therm-9` / `-12` = `pmih010x_batt_therm(_2)` | battery | passive (120 = no action) | battmgr reports battery temperature; charging policy is below |
| `sys-therm-11` = `pmih010x_usb_therm`, `usb_therm`, `chg_cp_therm` | USB connector, charge pumps | 120 (userspace) | missing: connector overheat protection |
| `sys-therm-3/4/5/6/7` = cam_flash, wlan, pa_1, qtm, pa_2 | | 120 | informative; `flash_therm` + `board_therm` done (0032) |
| `shell_front/frame/back` | Oplus virtual "shell" (skin estimates) | computed by the vendor framework | replace with the skin thermistor + a small virtual-sensor formula if needed |
| `pmh0101-bcl-lvl0..2`, `pmih010x-ibat-lvl0/1`, `pmih010x-bcl-lvl0..2`, `vbat`, `socd` | battery current limit (BCL) / low-voltage | stock throttles CPU/GPU on high current or low battery | **missing: protects against brown-out resets at low battery under load** |
| `ddr`, `video`, `camera-*`, `nsphvx/hmx` (CDSP), `mdmss` | TSENS | stock cooling: `ddr-cdev`, `cdsp*`, `display-fps`, `panel0-backlight`, `ufs` | later, when those drivers are in use |

The plan, in order:
1. **Skin control (new DT zones, kernel-only so it works in every distro).** Add `pmh0101_skin_therm` (ADC5 Gen4
   AMUX 0x144, 100k pull-up) as a `skin-thermal` zone with step-wise trips that follow stock's steps:
   - 48 °C → cap the big cluster (cpu6-7) one step at a time;
   - 50 °C → cap both clusters and the GPU (devfreq cooling);
   - 60 °C → strong caps (big ≤ ~1.9 GHz, GPU ≤ mid OPP);
   - 90 °C → `critical` (orderly shutdown).
   The exact frequency caps are tuned to stock's gear table (OnePlus `sys_thermal_control_config.xml`: 20 gears →
   14 CPU levels, e.g. level 3 = 2.36/1.86 GHz) once the PC extracts it, with polling at 1 s.
   - Alternative if step-wise oscillates: `power_allocator` on the skin zone with a measured `sustainable-power`.
2. **XO/board zone** (`pmk8850_xo_therm` 0x44): 78/80 °C passive with CPU cluster caps, as in stock; 90 °C critical.
3. **GPU:** confirm infiniti's GPU trips and cooling on `gpuss-*`; add the stock values if they differ. The GPU is
   the main heat source under GNOME (the Adreno 840 at 1.2 GHz).
4. **BCL / low-battery protection:**
   - look for a mainline or infiniti/XEC driver for the PMH0101/PMIH010x BCL blocks (vbat/ibat alarms as thermal
     zones);
   - otherwise a userspace guard (a systemd unit on the battmgr capacity/voltage) that caps CPU/GPU below ~10 %
     battery or under 3.4 V.
   - Test with a controlled load at low battery; the tablet must not brown-out reset.
5. **Charging thermal:**
   - confirm the charger firmware (SoCCP/ADSP) enforces battery and connector temperature limits itself: log battmgr
     current vs battery temperature while charging under load;
   - add `charge_control_end_threshold` (e.g. 80/85 %) for long plugged-in use;
   - add a `usb_therm`/`chg_cp_therm` zone that stops charging (battmgr) above stock's limit.
6. **GNOME integration:** `power-profiles-daemon` profiles map to cpufreq caps. Power-saver caps the big cluster;
   balanced and performance don't cap, but the skin trips never go above stock's steps. Thermal zones get sensible
   names so `sensors` and GNOME extensions show "skin", "battery" and "board".
7. **Verification (each a kit, judged from logs):**
   - CPU (8 threads), GPU (glmark2 10 min), combined and while charging, each for 15 min;
   - record skin, xo, battery and CPU/GPU frequencies every second;
   - pass = skin ≤ 50 °C sustained (≤ 60 °C peak), no critical trip, no reset, frequencies recover afterwards;
   - compare with stock Android under the same load, read from a LineageOS/stock capture on the PC.

#### B. Sleep and standby states

Qualcomm mainline platforms support **s2idle** (suspend-to-idle; PSCI OS-initiated idle takes the SoC to its deepest
state through RPMh/AOSS). There is no separate "deep" S3. The targets:

| State | What it is on the Pad 4 | Wake sources | Target |
|---|---|---|---|
| **Screen off / idle** | DPMS off (MSM DRM + KTZ8869 backlight off), runtime PM on everything, CPU idle states, GPU collapsed, Wi-Fi power save | touch (optional), keys | fast (< 0.5 s) screen on; idle drain measured |
| **Standby = s2idle** (`mem_sleep_default=s2idle`) | all devices suspended; CPUs in the cluster/system power-down state; RPMh votes released so **CX, DDR and AOSS reach sleep** (the "CXPC/AOSD" counters increase) | power key (PMK8850 PON), **lid open** (TLMM98), pogo keyboard (wake TLMM151), RTC alarm, USB plug/charger events (pmic-glink), optionally Wi-Fi WoWLAN / BT HID | resume ≤ 1.5 s with display, touch, USB, Wi-Fi and BT working; **drain ≤ ~1 %/h** (compare with stock Android's standby drain measured on LineageOS) |
| **Suspend-then-hibernate** (optional, later) | systemd suspends, then hibernates to a swap partition/file after N hours | power key | only after s2idle is solid; needs swap ≥ RAM (12 GB), not in the first install |
| **Power off / reboot** | PS_HOLD, known to work (hard reset) | power key | ✅ |

Work items, in order:
1. **Kit pc-025** (built): s2idle with an RTC alarm (`SUSPEND_AT`, PMK8850 RTC). Check "PM: suspend entry/exit",
   the RTC wake, and that the kit's network, display and touch come back. Logs come from the live stream; nothing is
   watched.
2. **Low-power proof:**
   - enable `qcom_stats` (rpmh-stats, in the infiniti queue) and read the AOSS/CXSD/DDR sleep counters before and
     after each suspend, plus `/sys/power/suspend_stats` and wakeup sources;
   - find blockers with `pm_debug_messages` and `/sys/kernel/debug/wakeup_sources`.
   - Typical blockers: a remoteproc keeping a vote (ADSP/CDSP/SoCCP), USB (dwc3 in peripheral mode with a host
     attached keeps the link up, so also test on battery with the cable out), and the Wi-Fi PCIe link (ath12k
     suspend / PCIe L1ss).
3. **Resume correctness, per device:**
   - display (dual-DSI + DSC panel re-init, KTZ8869 re-programmed with ABL's values: 0024 must also run on resume);
   - touch (TDDI: the firmware is re-downloaded after the panel powers up again, or kept powered for tap-to-wake);
   - pen, pogo keyboard;
   - USB (the dwc3 `power_lost` pattern from aaronsb), Wi-Fi (ath12k suspend/resume or unload/reload as a fallback),
     BT, audio (later), GPU (GMU resume), battmgr.
   - DPU vblank timeouts on resume are a known trap.
4. **Wake sources:** power key, lid open, pogo keyboard, RTC and charger all mark as `wakeup-source` in the DT and are
   tested one by one. The lid close → suspend and open → resume path goes through logind.
5. **Fedora/GNOME integration:**
   - `mem_sleep_default=s2idle`; make sure `sleep.target`/`suspend.target` aren't masked (the Tab S6 found Fedora
     masks them in some images);
   - logind `HandleLidSwitch=suspend`, `HandlePowerKey=suspend`;
   - GNOME idle suspend on battery;
   - sleep hooks in `/usr/lib/systemd/system-sleep/` (for example a Wi-Fi reload or a touch re-init if needed),
     shipped in `iceland-device`.
6. **Measurement:** 8 h overnight standby on battery with Wi-Fi on; drain from the battmgr capacity/energy. Compare
   with stock/LineageOS overnight on the PC side (read-only). Repeat 20 suspend/resume cycles without a failure.
- **Exit:** s2idle reaches the SoC's sleep state, drain ≤ ~1 %/h, 20/20 clean resumes with every device working,
  and lid, power key and keyboard wake work.

#### C. Power management: charging, USB-C PD / OTG, and the whole system (the user asked for it)

**What stock does (live stock DT) and what mainline has:**

| Stock piece | Where it runs on stock | On mainline today |
|---|---|---|
| Basic charging, gauge, USB-C PD/Type-C detection | charger firmware on **SoCCP**, reached over pmic-glink (`qcom,ucsi-glink`, battmgr) | ✅ battery and USB data, UCSI `port0` + partner (pc-011/013). An SDP port gave 5 V / 1.24 A |
| **SuperVOOC 80 W** (`oplus,vooc`, `vooc_power_max_w = 80`), **PPS 11 V / 5 A**, **UFCS 11 V / 6.1 A** | the **OnePlus kernel stack** (`oplus,vooc/pps_charge/ufcs_charge`, `virtual_*` ICs over glink), driving **2× SC8547D charge pumps** on APPS I2C (12-006a, 24-006a) | ❌ none of it. Expect standard USB PD / QC from the firmware only |
| PD/QC normal charging limits: ICL 2 A, 5 V↔9 V switch at vbatt 4.5 V, input power table 2.5–30 W, cool-down tables, VBUS OV 11 V / UV 4.3 V | OnePlus `oplus,wired` (kernel) | the firmware's defaults; to measure |
| **Dual-cell protection** (`oplus,dual_cells_protection`: min FCC, current limit 2.5 A, SOC-jump checks) | OnePlus kernel | ❌. **Safety item:** confirm the pack/gauge/firmware protects the cells on its own before long unattended charging |
| Battery authentication (IN: Maxim DS28E30) | OnePlus kernel + firmware | unknown effect: check whether charging is slowed when nobody authenticates |
| Smart/limit charging (`oplus,smart_charge`, `plc_charge`) | OnePlus kernel | use battmgr `charge_control_*` if the firmware supports it, or a userspace limiter |
| **Pen charging:** MT5806 wireless TX (I2C 25-002b), powered by the PMIH010x **hboost** at 7 V, plus `oplus,wireless_pen_glink` | OnePlus kernel + firmware | ❌. Needs an MT5806 driver + hboost control + the glink pen messages |
| OTG / VBUS out | firmware on request from the OnePlus stack | untested. The OnePlus 15 gets OTG only with external PD power, so the OTG enable is probably a OnePlus glink message |

**Charging plan, in order:**
1. **Measure what the firmware does alone** (kits, logged from battmgr/UCSI, one charger at a time; the user plugs
   them in):
   - SDP (PC port), a DCP 5 V brick, a USB PD charger (9 V/15 V), a PPS charger and the OnePlus SuperVOOC brick;
   - record the negotiated PDO (UCSI), input voltage and current, battery current, and battery/connector temperatures;
   - expected: PD at 9 V up to the firmware's limit (roughly 18–27 W). No PPS/UFCS/VOOC.
2. **Safety before daily charging:**
   - confirm the firmware stops or derates on battery temperature (charge under load, watch current vs
     `batt_therm`) and on connector temperature (`usb_therm`);
   - confirm full-charge termination (current tapers, `status` goes Full);
   - confirm the dual cells stay balanced (gauge per-cell data, if exposed; otherwise the pack protection the stock
     firmware relies on).
   - Until all three pass, charge only while attended, with an 80 % end threshold.
3. **Charge limit for long plugged-in use:** `charge_control_end_threshold` / `_start_threshold` through battmgr, if the
   SoCCP firmware accepts it (upstream battmgr has it for newer platforms). Otherwise a small daemon that asks the
   firmware to suspend charging (the OnePlus glink message, found in the OnePlusOSS `oplus_chg` source).
   Expose it to GNOME (GNOME 48+ has a battery-health charge-limit toggle through UPower).
4. **Fast charging (optional, big job):** PPS through the SC8547D charge pumps is possible in principle: mainline has
   PD PPS support in tcpm, but here PD runs in firmware, so we'd need the OnePlus glink PPS messages plus a
   charge-pump driver. UFCS and SuperVOOC are proprietary. Decision: **not in scope** for the first install; revisit
   once everything else works.
5. **Pen charging:** after the pen input fix. Needs an MT5806 driver (from the OnePlusOSS source, GPL), hboost control
   (PMIH010x) and the pen glink messages. A medium-hard item on its own.

**USB-C roles, PD and OTG:**
1. **Restore the real Type-C wiring in the DT** (removed for bring-up):
   - dwc3 `usb-role-switch` driven by UCSI;
   - the connector graph: UCSI port → dwc3 (HS) + QMP combo PHY (SS/DP) + WCD939x USB-SS mux (orientation and audio
     accessory).
2. Cases, each a kit with the user plugging things in:
   - **device mode** (charging from a PC, gadget): works;
   - **host with self-power** (keyboard, mouse, SSD, hub): VBUS out;
   - **host + charging through a PD hub** (power pass-through, i.e. a data-role swap while sinking);
   - **reverse charging** of a phone (source role, current limit);
   - **DisplayPort alt mode** (pmic-glink altmode + the infiniti DP controller).
3. **OTG enable:** find the OnePlus glink message for OTG/VBUS boost in the `oplus_chg` source (the OnePlus 15's
   "OTG only with PD" symptom says it's missing). Add it to our battmgr/pmic-glink OnePlus variant; compare with XEC's
   OnePlus pmic-glink power-supply driver (df4c73f22d08).
4. **Safety:** VBUS out is never enabled by our code while a source is attached; the firmware's OCP/OVP stays in
   charge. OTG current is limited to stock's value.

**General system power (screen-on battery life):**

| Area | Plan |
|---|---|
| CPU | schedutil governor; **Energy-Aware Scheduling**: make sure an energy model is registered (SCMI perf EM or DT `dynamic-power-coefficient`), so light work stays on the little cores; PSCI OS-initiated cluster idle states (check `cpuidle` usage counters) |
| GPU | msm devfreq DCVS works (160 MHz–1.2 GHz); the GMU idles and collapses; check that it idles under GNOME with a static screen |
| Display (the biggest consumer) | brightness via KTZ8869 (the range and a sensible minimum); **60 Hz on battery, 120/144 Hz on AC** (a udev/`power-profiles-daemon` hook, or a GNOME setting); DPMS off quickly when idle |
| Memory / interconnect | icc votes scale with load; LLCC active; check that DDR frequency drops at idle (`qcom_stats` DDR counters) |
| Storage | UFS runtime PM + auto-hibern8; WriteBooster left as stock |
| Radios | Wi-Fi power save (`wifi.powersave=3` in NetworkManager), BT autosuspend; ath12k PCIe ASPM/L1ss |
| DSPs | **CDSP off** unless used (nothing uses it yet); the ADSP only for audio and sensors; SoCCP is always on (charging) |
| USB | dwc3 runtime suspend with no cable |
| Userspace | `power-profiles-daemon` (power-saver = big cluster capped + 60 Hz + Wi-Fi power save), udev runtime-PM defaults (`power/control=auto` where safe), GNOME dim/blank/suspend defaults; all shipped in `iceland-device` |

**Measurement (fuel gauge `power_now`/`current_now`, logged every second by a kit or a Fedora unit):**
- idle screen-on at minimum and typical brightness;
- 1080p video playback (Iris later; software first);
- web browsing loop;
- Wi-Fi idle, Bluetooth idle.

Compare each against stock/LineageOS doing the same scenario (read-only measurement on the PC side). Target: within
~20 % of stock for screen-on idle and video once the display refresh and DSP policies are in.

**Exit for 5-PM C:**
- PD charging works with thermal derating and termination proven, a charge limit is available in GNOME, and
  battery safety is confirmed;
- host mode, a PD hub and DP alt mode each work or are documented as blocked;
- screen-on power is within ~20 % of stock in the measured scenarios.

### Phase 6 — Upstreaming (runs alongside)
Pad 4 DTS, KTZ8869, the NT36536 panel desc (already in the upstream driver), touch driver cleanup, TFA9865, the
generic fixes found here, and the U-Boot board:
- the MDSS all-power-domains change (0026);
- the video-mode splash handling (0025);
- the pmic_glink early channel (0028);
- the kaanapali DPU clock factor (0035).

Coordinate with map220v and infiniti-mainline. Publishing or contact only when the user asks.

### Phase 7 — Other distros (optional, later)
Same kernel source and config. Per distro, only a kernel package wrapper (PKGBUILD/apk/deb), an initramfs hook, and
a loader entry with `devicetree` and `lsm=`.
- Arch Linux ARM and pmOS first (pmOS needs our own `device-oneplus-iceland`), then Debian testing, Kali and the
  latest non-LTS Ubuntu.
- Not supported: Debian stable and Ubuntu LTS (their Mesa is too old for the a840).

## Hard stops (ask the user)
Any write to the tablet (first: Phase 4e, or 4-DB) · slot switching · repartitioning (needed by 4-DB) · firmware not from this tablet's 11.A.38
(exception: upstream linux-firmware files for the GPU) · publishing or contacting maintainers.

## Where things live
Private GitHub repos:
- `iceland-mainline`: plan, knowledge, facts, tests, firmware manifest, tools, `phase4/`, relay;
- `iceland-linux`: kernel patch queue, config, CI;
- `iceland-u-boot`: U-Boot patch queue, test scripts.

Shared memory of both sessions: [KNOWLEDGE.md](KNOWLEDGE.md). Test history: `docs/tests/README.md`. PC results:
`relay/results/`.

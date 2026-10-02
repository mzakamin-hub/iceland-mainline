# OnePlus Pad 4: plan for the full install of Fedora 44 GNOME (planning only)

Written 2 Oct 2026. **Nothing in this plan has been done on the tablet, and nothing in it runs without your
explicit OK for each write.** So far the project has only booted from RAM; no partition has ever been written by
it. This replaces the short draft in `phase4/INSTALL-PLAN.md`.

## 0. The idea in five lines

1. The whole Fedora system lives in ONE partition: `userdata`. A second small write puts our boot loader (U-Boot)
   where the tablet's own boot loader starts it. Nothing else on the storage is ever written.
2. The tablet's own boot loader (ABL, with fastboot) and all firmware stay exactly as OnePlus shipped them. As long
   as they are untouched the tablet cannot be bricked: fastboot always answers, and fastboot can put everything
   back.
3. Every step is first rehearsed from RAM with the very image that will be written.
4. Return to stock OxygenOS 11.A.38 is possible at every stage with the backup and the scripts that already exist
   (`C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1`).
5. On the installed system Fedora's updates can only change files inside `userdata`. The kernel and the few
   packages that are special on this tablet come from our own repository and are held against Fedora's versions.

## 1. What must be true before anything is written (gates, all without writing)

| Gate | State today | How it is closed |
|---|---|---|
| G1 Backup of all 151 partitions, sha256-verified | exists: `C:\OnePlusPad4\backups\20260927-1933-unknown` | re-verify the checksums on the PC on the day |
| G2 Stock 11.A.38 images + checksums | exists: `C:\OnePlusPad4\stock-11.A.38` | re-verify `SHA256SUMS.txt` |
| G3 Return-to-stock scripts reviewed against today's partition state | scripts exist (30 / 31 / 39) | dry run (`30-Restore-Stock.ps1` without `-Execute`) and read its plan |
| G4 Second copy of G1 + G2 on another disk | not done | copy; the backup holds the per-device calibration that no download has |
| G5 File copy of Android's `/data/vendor` and `persist` | not done | from LineageOS with `adb root`, read only (the raw `userdata` backup is encrypted and useless) |
| G6 Charging safe unattended on a wall charger | partly (limits queued, guard proven; wall chargers need you once) | workflow "charging" + one sitting with you |
| G7 Low-battery protection (BCL) or a documented substitute | not started | workflow "bcl" |
| G8 Thermal protection as stock (skin, GPU, charging when hot) | mostly proven | workflows "thermal", "gpucool" |
| G9 The install image boots from RAM through the real chain (U-Boot, GRUB, our kernel, SELinux on) | not done | section 4 |
| G10 An update and a rollback rehearsed on that image | not done | section 4 |
| G11 The slot flags of the active slot are understood | not done | read-only `fastboot getvar all` in ABL: `slot-successful`, `slot-retry-count`, `slot-unbootable` for a and b |

G6-G8 are the reason an installed tablet may be left alone on a charger. If one of them stays open, the install can
still go ahead with the rule "charge attended, limit 80 %" written into the image's defaults.

## 2. Partitions: what may be written, what must never be written

The storage has 6 units (LUNs) with 151 partitions. The rule is simple: **two partitions may be written, all the
others never.**

### May be written (and how each is undone)

| Partition | Size | What goes there | Undo |
|---|---|---|---|
| `userdata` (unit sda, the last and biggest partition) | 237 GB | the Fedora disk image | `fastboot -w` (formats `userdata` and `metadata`) as part of the return to stock |
| ONE boot-path partition of the ACTIVE slot: `boot_b` today (see 5.2 for the choice) | 96 MB | U-Boot (the same image that is RAM-booted today) | `fastboot flash boot_b` with the saved image from the backup |

`metadata` (64 MB, Android's encryption keys for `userdata`) is only touched on the way back to Android, by
`fastboot -w`.

### Never written (the reason the tablet stays unbrickable)

| Group | Partitions | Why |
|---|---|---|
| Boot firmware | `xbl*`, `xbl_config*`, `uefi*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `qupfw*`, `shrm*`, `cpucp*`, `tme_*`, `multiimg*`, `featenabler*`, `imagefv*`, `uefisecapp*`, `keymaster*`, `secretkeeper*`, `spuservice*`, `oplus_sec*`, `pdp*`, `soccp*`, `dcp*`, `xbl_ramdump*` (both slots) | this is the chain that gives us fastboot. There is no public emergency-download loader for this tablet, so a broken chain cannot be repaired at home |
| Radio / DSP firmware | `modem*`, `bluetooth*`, `dsp*` | signed, version-locked (anti-rollback: never older than 11.A.38); Fedora only READS them |
| Per-device data | `persist`, `cdt`, `ddr`, `dinfo`, `engineering_cdt*`, `ocdt`, `oplusreserve1/2/3/5`, `nonmodemst1/2`, `qweslicstore*`, `DRIVER`, `ompdt` | calibration and identity of this one tablet; exist nowhere else than in your backup |
| Security state | `devinfo` (unlock state), `keystore`, `frp`, `ssd`, `secdata`, `storsec`, `uefivarstore`, `spunvm`, `connsec`, `tzsc` | a wrong byte can lock the boot loader or the secure world |
| Android system | `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `pvmfw*`, `splash*`, `misc` | not needed by Fedora; left alone so that the return to stock stays small. (`recovery_b` is the alternative boot-path partition, see 5.2) |
| The partition tables of all six units | GPT | no repartitioning in this plan |

Further rules that follow from the same reason:
- never `fastboot set_active` (the plan never switches slots; only the return-to-stock script does, at its end);
- never `fastboot flashing lock` while anything but verified stock is installed;
- never `fastboot erase` / `format` on anything but `userdata` / `metadata`;
- never flash firmware older than 11.A.38;
- U-Boot is built WITHOUT the ability to write the storage (as today), and it stays that way.

### Seat belts inside the installed Fedora

So that no program, update or mistake inside Fedora can reach the other partitions:
- a udev rule in `iceland-device` marks every block device of the internal storage read-only except the Fedora
  partition (`sdb` to `sdf` whole, and every `sda` partition but `userdata`);
- firmware is read from the tablet's own partitions through read-only mounts or copied once by the extractor;
- `fwupd`'s UEFI capsule plugin is off (already in `iceland-device`): there is no firmware update path from Fedora;
- no tool in the image changes slots or the boot loader; EFI variables are not persistent (U-Boot keeps them in RAM),
  so `efibootmgr` calls from package scripts fail without effect.

## 3. What the image contains

Base: the official **Fedora-Workstation-Disk-44 aarch64** raw image (checksum-verified): 500 MB EFI partition, 2 GB
boot partition, btrfs root that grows to the partition on first boot. Its package set is Fedora Workstation's own
default, so the default apps are there without us choosing them:

| You asked for | Package in Fedora 44 Workstation | Note for the Pad 4 |
|---|---|---|
| App store | GNOME Software (`gnome-software`) with Flatpak; Flathub switched on | Fedora version upgrades hidden (see 6) |
| Camera | Snapshot (`snapshot`) + `libcamera`, `pipewire-plugin-libcamera` | needs our camera sensor module and the open camera items (see 7) |
| Terminal | Ptyxis (`ptyxis`) | |
| Browser | Firefox (`firefox`) | hardware video decoding in GNOME Web is proven; Firefox to be checked |
| Files, Settings, Text Editor, Calculator, Clocks, Calendar, Contacts, Weather, Maps, image / video / document viewers, Disks, System Monitor, Logs, Fonts, Characters, Connections, LibreOffice | the Workstation defaults | nothing is removed |
| Added for a tablet | `gnome-tweaks`, Extensions app, the on-screen keyboard (GNOME's own) | |

The check in the rehearsal: `rpm -q` of this list on the built image must find every package, and each app must
start once in the RAM rehearsal (window appears, no crash in the journal).

Added on top (all from our repositories, built reproducibly):

| Piece | State today | Missing before the install |
|---|---|---|
| `kernel-iceland` rpm (7.3-rc4 + queue 0001-0073, modules, device tree, `kernel-install` plug-in that puts the device tree where U-Boot looks) | the kernel is proven; it is delivered as kit files, not as an rpm | write the spec and the plug-in, build, rehearse |
| `iceland-device` 0.15 (settings, battery guard, power modes, sensors, sound) | built and installed in RAM sessions | the read-only udev rule (section 2), the snapshot unit (section 6) |
| `hexagonrpc`, `libssc`, `iio-sensor-proxy` (auto-rotate, light, proximity) | built on the tablet, proven (runs 23-26) | nothing |
| Firmware extractor (reads the tablet's own partitions once: GPU, video, Wi-Fi, Bluetooth, audio, touch, the sensor hub's file tree) | parts exist as PC scripts on carved images | one on-device script; the files are never shipped, they stay on the tablet |
| Patched GStreamer V4L2 plug-in (hardware video) | proven as a file | an rpm |
| Camera sensor module | proven, private (register tables from a trace of stock) | a local, never-published module rpm |
| U-Boot image (boots the EFI partition inside `userdata`) | RAM-booted every day | prove the chain U-Boot, GRUB, kernel on the real image (G9) |

## 4. Rehearsal from RAM (no write)

1. **Build the image** on the PC from the official raw image; our rpms are installed into it natively on the
   tablet in a RAM session (the image is served from the PC over the USB network as a network block device; the
   tablet's storage is not used). The firmware extractor runs in the same session against the tablet's own
   partitions, read-only.
2. **Boot that image over the network** through the real chain: `fastboot boot` U-Boot, U-Boot loads GRUB from the
   image's EFI partition, GRUB starts `kernel-iceland` with its initramfs, root on the network block device, SELinux
   enforcing. This is the same software path as after the install; only the disk is on the PC.
3. **Acceptance list** on that boot (automated, from the journal and D-Bus, as in the test runs): GNOME session,
   touch device, Wi-Fi scan with 5 GHz, Bluetooth, sound cards, battery and time estimate, power modes, auto-rotate
   after a boot, suspend and resume, hardware video, both cameras listed, the default apps start, About shows
   "OnePlus Pad 4", `rpm -Va` clean for our packages, no `avc: denied` that breaks a service.
4. **Update rehearsal** on the image: a `dnf upgrade` with Fedora's current updates (our holds must keep the kernel
   and the sensor daemon), an offline update through GNOME Software's path with a reboot through U-Boot, a new
   `kernel-iceland` build installed next to the old one, GRUB shows both, the old one still boots.
5. **Rollback rehearsal** on the image: boot the previous kernel from GRUB's menu; boot the previous root snapshot;
   repair from the rescue kit (the RAM kit used today, with the image mounted).
6. Convert the rehearsed image to a sparse image and record its checksum: **this exact file is what gets written.**

## 5. The writes (each one only after your OK; you run or confirm each command)

### 5.1 Write 1: `userdata`

- Before: G1-G5 and G9-G11 closed; battery above 60 %; the PC's USB port that has been used all along.
- Command (stock ABL fastboot, which splits a sparse image by itself; its limit is 805 MB per piece):
  `fastboot flash userdata fedora-iceland.sparse.img`
- What it changes: Android's data is gone (LineageOS will no longer start; its system partitions stay).
- Proof before going on: boot tethered (`fastboot boot` U-Boot from the PC), Fedora's first-boot setup appears, the
  acceptance list of section 4 passes again, three cold boots in a row.
- Undo: return to stock (section 8), or flash the image again.
- Hazard to know: until write 2 the tablet starts Android when it is switched on without the PC, and Android will
  say its data is damaged and offer a factory reset. Do not confirm it (it would erase Fedora, nothing worse).
  Keep this stage short.

### 5.2 Write 2: the boot path

Recommended: **U-Boot into `boot_b`** (the boot partition of the slot that is active today), so that switching the
tablet on starts Fedora.
- Before: read the slot flags in ABL (G11). The slot must be marked successful, so that ABL does not count boot
  attempts. Save `boot_b` once more from the tablet and compare with the backup.
- Command: `fastboot flash boot_b u-boot-iceland.img` (the image that has been RAM-booted in every test).
- Proof: switch on without the PC three times; then read the slot flags again in ABL (Volume Down + Power): the
  retry counter must not have gone down. If it has, undo this write at once and use the alternative below.
- Undo: `fastboot flash boot_b boot_b.img` from the backup (two minutes).
- Alternative if ABL counts attempts for a boot image it cannot mark good: U-Boot into `recovery_b`. Fedora then
  starts with Power + Volume Up; a plain power-on still starts Android (which has no data). Less convenient, same
  safety.

Not part of this plan: keeping a working Android next to Fedora (dual boot). It needs the partition table of unit
sda changed (shrinking `userdata`), which is the one kind of write this plan avoids. It can be planned separately.

### 5.3 What never happens in the writes

No `-w`, no `flashall`, no `update`, no `set_active`, no flashing of any partition from the never list, no
third-party flashing tool: only `fastboot flash userdata` and `fastboot flash boot_b` with files whose checksums
were recorded in the rehearsal.

## 6. Updates on the installed tablet without breaking it

### Why an update cannot brick the tablet

Fedora can only write inside `userdata` (section 2). The worst an update can do is make Fedora itself not start.
The tablet's boot loader and fastboot are out of its reach, so the PC can always RAM-boot the rescue kit and repair,
or write the image again.

### What Fedora's updates may and may not replace

| Package group | Source | Rule |
|---|---|---|
| `kernel`, `kernel-core`, `kernel-modules*` (Fedora's kernels) | never installed | excluded in dnf's configuration (in `iceland-device` today); they have no Pad 4 support |
| `kernel-iceland` | our local repository (`/var/lib/iceland/repo`, filled by `iceland-repo-sync` from the PC) | three versions kept; a new one becomes the default only after it has booted once (see below) |
| `iio-sensor-proxy`, `hexagonrpc`, `libssc`, the patched GStreamer plug-in, `iceland-device` | our local repository, which has the higher dnf priority; our release numbers stay above Fedora's | Fedora's versions are never chosen while ours exist (checked in run 23: `dnf check-upgrade` offers nothing) |
| `linux-firmware` | Fedora | may update: the tablet's own firmware sits in `/usr/lib/firmware/updates`, which wins |
| Mesa, GNOME, PipeWire, libcamera, everything else | Fedora | updates normally. A regression costs a feature (for example software rendering), never the boot |
| `grub2`, `shim` | Fedora | update normally; they only rewrite files in the image's EFI partition. Covered by the rescue path |
| Fedora 45 (version upgrade) | blocked | the polkit rule in `iceland-device` and GNOME Software's upgrade banner off, until the new version has passed the RAM rehearsal with our kernel |
| `fwupd` firmware updates | off | the capsule plug-in is disabled |

`iceland-device` and `kernel-iceland` are also listed as protected packages, so that dnf refuses to remove them.

### Order of an update that touches our packages

1. PC: build the new rpm (kernel, device package, ...).
2. PC: RAM-boot the new kernel with the kit and run the automated checks (as every kernel so far).
3. PC to tablet: `iceland-repo-sync` copies the rpm into the tablet's local repository (checksums verified).
4. Tablet: `dnf upgrade` (or GNOME Software). A btrfs snapshot of the root is taken first by a unit of
   `iceland-device` (the last three are kept).
5. First boot of a new kernel is a trial: GRUB's "boot once" entry. Only when the system has reached the desktop
   does a unit make it the default. If it does not come up, the next power-on starts the previous kernel by itself.
6. If the desktop itself is broken by Fedora's updates: boot the previous snapshot from GRUB's menu, or repair from
   the rescue kit.

### The rescue path (always available)

`fastboot boot` of the test kit from the PC, exactly as today: it does not use the tablet's storage to start. From
there the installed root can be mounted, checked, rolled back to a snapshot, or the kernel replaced. This is also
how a forgotten password or a full disk is handled.

## 7. Known gaps on the day of writing (what "full install" will not have yet)

- Cameras: pictures and auto-exposure work in tests; focus, the Camera app on screen and one open issue (the camera
  bus depends on the sensor hub's state) are still in work.
- Speakers stay volume-capped until speaker protection exists; fast charging (SuperVOOC) is not planned.
- The NPU needs Qualcomm's SDK (your decision); Wi-Fi 5 GHz connect needs your password once.
- Items that need your hands once: wall-charger checks, one turn of the tablet, the microphone meter, pen and
  keyboard cover.
The feature matrix is the full list.

## 8. Back to stock OxygenOS at any time

Works from every stage, because the boot loader, the firmware and the per-device data were never touched and the
backup holds everything else.

| From which stage | What to do |
|---|---|
| Only RAM boots so far (today) | nothing: reboot, Android starts |
| After write 2 only the boot path should go back | `fastboot flash boot_b boot_b.img` from the backup |
| Full return to stock | `C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1`: verifies the backup and the stock images, shows a dry run, then (after you type the confirmation) writes the stock boot set to both slots and `super` from your backup, erases `userdata`, and proves the result is byte-identical stock |
| Locked boot loader as from the factory (optional) | `31-Relock-Bootloader.ps1`, only after the script's own check says the tablet is exactly stock |

Before the first write the return path is rehearsed as far as it can be without writing: checksums of the backup
and the stock images, the script's dry run, and a read of what it would write against section 2 (it writes only
Android's own boot set and `super`, never firmware).

## 9. Decisions that are yours

1. Go ahead with "Fedora only" as planned here, or plan the dual boot (needs the partition table changed) instead.
2. Boot path: `boot_b` (power-on starts Fedora, recommended) or `recovery_b` (key combination).
3. Whether an open gate G6-G8 blocks the install or only sets the "charge attended, 80 %" default.
4. Whether the camera module (private, built from a trace of stock) is part of the image on your tablet.

## 10. Work list that follows from this plan (PC only, in this order)

1. `kernel-iceland` rpm with the device-tree plug-in; the read-only udev rule and the snapshot / trial-boot units in
   `iceland-device`.
2. The on-device firmware extractor (including the sensor hub's file tree).
3. The image builder and the network-block-device rehearsal (section 4), with the acceptance list as a script.
4. The update and rollback rehearsal.
5. G3, G4, G5, G11 (read-only checks and copies).
6. Then, and only with your OK: write 1, later write 2.

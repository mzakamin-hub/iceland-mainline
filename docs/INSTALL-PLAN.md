# OnePlus Pad 4: plan for the full install of Fedora 44 GNOME (planning only)

Written 2 Oct 2026, updated the same afternoon with the findings of the install workflow (its PC-side tooling is
built and checked) and of runs 45-60. **Nothing in this plan has been done on the tablet, and nothing in it runs
without your explicit OK for each write.** So far the project has only booted from RAM; no partition has ever been
written by it. This replaces the short draft in `phase4/INSTALL-PLAN.md`. The step-by-step guide for the day is
`docs/INSTALL-GUIDE.md`.

## 0. The idea in five lines

1. The whole Fedora system lives in ONE partition: `userdata`. A second small write puts our boot loader (U-Boot)
   where the tablet's own boot loader starts it. Nothing else on the storage is ever written.
2. The tablet's own boot loader (ABL, with fastboot) and all firmware stay exactly as OnePlus shipped them. As long
   as they are untouched the tablet cannot be bricked: fastboot always answers (Volume Down + Power), and fastboot can
   put everything back.
3. Every step is first rehearsed from RAM with the very image that will be written: the PC serves the image over the
   USB cable, the tablet boots it through the real chain, and the file that was rehearsed is byte for byte the file
   that is written.
4. Return to stock OxygenOS 11.A.38 is possible at every stage with the backup and the scripts that already exist
   (`C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1`).
5. On the installed system Fedora's updates can only change files inside `userdata`. The kernel and the few
   packages that are special on this tablet come from our own repository and are held against Fedora's versions;
   boot code and firmware never update by themselves.

## 1. What must be true before anything is written (gates, all without writing)

| Gate | State (2 Oct, afternoon) | How it is closed |
|---|---|---|
| G1 Backup of all 151 partitions, sha256-verified | exists: `C:\OnePlusPad4\backups\20260927-1933-unknown` | re-verify the checksums on the PC on the day |
| G2 Stock 11.A.38 images + checksums | exists: `C:\OnePlusPad4\stock-11.A.38` | re-verify `SHA256SUMS.txt` |
| G3 Return-to-stock scripts reviewed against today's partition state | scripts exist (30 / 31 / 39) | dry run (`30-Restore-Stock.ps1` without `-Execute`) and read its plan |
| G4 Second copy of G1 + G2 on another disk | not done | copy; the backup holds the per-device calibration that no download has |
| G5 File copy of Android's `/data/vendor` and `persist` | not done | from LineageOS with `adb root`, read only (the raw `userdata` backup is encrypted and useless) |
| G6 Charging safe unattended on a wall charger | mostly: stock's charging steps, charge limit and the battery guard are in the kernel queue / device package and pass on the PC port | one sitting with you on two wall chargers |
| G7 Low-battery protection (BCL) | **closed**: queue 0074-0076, green on the queue head (run 45) | - |
| G8 Thermal protection as stock (skin, GPU, charging when hot) | **closed for the kernel** (runs 45: thermal 7 / 7, GPU cooling 20 / 20); the skin policy daemon is in device package 0.17 | your choice of the skin limit (48 C today or stock's 60 / 61 C with the daemon) |
| G9 The install image boots from RAM through the real chain (install U-Boot, shim, GRUB, our kernel, SELinux enforcing) | tooling built and checked on the PC; tablet runs R0-R2 pending | section 4 |
| G10 An update and a rollback rehearsed on that image | tooling built; runs U1-U3, R1b, R2b, R3 pending | section 4 |
| G11 The slot flags of the active slot are understood | not done | read-only `fastboot getvar all` in ABL: `slot-successful`, `slot-retry-count`, `slot-unbootable` for a and b |
| **G12 (new)** Fastboot reached by the keys from a cold start | not done | switch off, hold Volume Down + Power, read `fastboot getvar current-slot` (read only). This is the rescue path that must work without Fedora and without U-Boot |
| **G13 (new)** The rehearsal cannot touch the tablet's storage | asked of the install workflow (2 Oct, 12:00) | written proof that the rehearsal U-Boot never maps the real `userdata` (only the RAM head and the PC's disk), that the read-only rule is active already in the initramfs, and that no step of the chain writes UFS; a self-check that refuses any rehearsal script mapping `userdata` |
| **G14 (new)** Sleep drain known | in work: CX collapse reached for the first time on a test kernel (run 59), the deepest state not yet; no night unplugged yet | the deep-sleep workflow, then one night with you. Not a safety gate: without it the tablet works but drains faster asleep |

G6-G8 are the reason an installed tablet may be left alone on a charger. If one of them stays open, the install can
still go ahead with the rule "charge attended, limit 80 %" written into the image's defaults (the device package's
charge limit 80 / 85 % is on by default from 0.17).

## 2. Partitions: what may be written, what must never be written

The storage has 6 units (LUNs) with 151 partitions. **Every unit has 4096-byte logical blocks** (kernel log of run
45: `[sda] 61853696 4096-byte logical blocks`); this matters for the image (section 3). The rule is simple: **two
partitions may be written, all the others never.**

### May be written (and how each is undone)

| Partition | Size | What goes there | Undo |
|---|---|---|---|
| `userdata` (unit sda, the last and biggest partition) | 237159641088 bytes (0x3737D0F000; to be re-read in run R0) | the Fedora disk image, 4 KiB-native | `fastboot -w` (formats `userdata` and `metadata`) as part of the return to stock |
| ONE boot-path partition of the ACTIVE slot: `boot_b` today (see 5.2 for the choice) | 96 MB | the **install** U-Boot (`u-boot-iceland.img`, see below) | `fastboot flash boot_b` with the saved image from the backup |

`metadata` (64 MB, Android's encryption keys for `userdata`) is only touched on the way back to Android, by
`fastboot -w`.

New: the U-Boot that the kits RAM-boot every day (`diag-L-efi.img`) only waits for fastboot; it is **not** the one to
write. The install U-Boot is a separate build of the same tree with three more patches (finds the disk inside
`userdata` with 4 KiB blocks, lets EFI programs write only that disk, the install environment). It is built on the PC
(sha256 recorded per build; a rebuild changes the hash through the build date, so the record always takes the file
that was rehearsed) and will have been RAM-booted in every rehearsal boot (R1-R4) before it is written.

### Never written (the reason the tablet stays unbrickable)

| Group | Partitions | Why |
|---|---|---|
| Boot firmware | `xbl*`, `xbl_config*`, `uefi*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `qupfw*`, `shrm*`, `cpucp*`, `tme_*`, `multiimg*`, `featenabler*`, `imagefv*`, `uefisecapp*`, `keymaster*`, `secretkeeper*`, `spuservice*`, `oplus_sec*`, `pdp*`, `soccp*`, `dcp*`, `xbl_ramdump*` (both slots) | this is the chain that gives us fastboot. There is no public emergency-download loader for this tablet, so a broken chain cannot be repaired at home |
| Radio / DSP firmware | `modem*`, `bluetooth*`, `dsp*` | signed, version-locked (anti-rollback: never older than 11.A.38); Fedora only READS them |
| Per-device data | `persist`, `cdt`, `ddr`, `dinfo`, `engineering_cdt*`, `ocdt`, `oplusreserve1/2/3/5`, `nonmodemst1/2`, `qweslicstore*`, `DRIVER`, `ompdt` | calibration and identity of this one tablet; exist nowhere else than in your backup |
| Security state | `devinfo` (unlock state), `keystore`, `frp`, `ssd`, `secdata`, `storsec`, `uefivarstore`, `spunvm`, `connsec`, `tzsc` | a wrong byte can lock the boot loader or the secure world |
| Android system | `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `pvmfw*`, `splash*`, `misc` | not needed by Fedora; left alone so that the return to stock stays small. (`recovery_b` is the alternative boot-path partition, see 5.2) |
| The partition tables of all six units | GPT | no repartitioning in this plan |
| **The storage chip's own firmware (new)** | the UFS device firmware | Fedora's `fwupd` lists the UFS storage as an *updatable device* by default (apps run B, area-combo-55). A wrong storage-firmware update is the one software path to a dead tablet that does not go through a partition. The device package turns off every `fwupd` plug-in that can write boot code, EFI variables, the UFS firmware or pins (17 plug-ins) and restarts `fwupd` so that it takes effect (re-checked in apps run D) |

Further rules that follow from the same reason:
- never `fastboot set_active` (the plan never switches slots; only the return-to-stock script does, at its end);
- never `fastboot flashing lock` while anything but verified stock is installed;
- never `fastboot erase` / `format` on anything but `userdata` / `metadata`;
- never flash firmware older than 11.A.38;
- U-Boot is built WITHOUT the ability to write the storage through fastboot (as today), has no shell and no key
  check, and its EFI layer may write only the disk it maps from `userdata` (new option, install workflow finding 6:
  before it, EFI programs such as shim or GRUB could have written every unit).

### Seat belts inside the installed Fedora

So that no program, update or mistake inside Fedora can reach the other partitions:
- a udev rule in `iceland-device` marks every block device of the internal storage read-only except `userdata` (and
  its unit as a whole, which would otherwise make `userdata` read-only too); the same rule is in the initramfs, so it
  holds from the first second; udisks ignores all of them (they do not appear in Files);
- firmware is copied once by the on-device extractor, which opens every partition read-only (it sets the block
  device read-only before opening it); its result was checked on your backup: 23 of 23 items, 627 files identical
  to what the kits load today;
- `fwupd`: only harmless plug-ins stay (see the table above);
- no tool in the image changes slots or the boot loader; EFI variables are not persistent (U-Boot keeps them in RAM),
  so `efibootmgr` calls from package scripts fail without effect;
- dnf can never install Fedora's kernels, a rescue initramfs (`dracut-config-rescue`), akmods / dkms, bootupd,
  sdubby or U-Boot images, and with the default setting also not a new GRUB, shim or firmware package (section 6).
  Proven in a RAM session (apps run C, area-combo-56): 9 of 9 forbidden installs refused, a full simulated upgrade of
  84 packages contained none of them, a request for Fedora 45 was refused.

## 3. What the image contains

Base: the official **Fedora-Workstation-Disk-44 aarch64** raw image (signature by the Fedora 44 key and sha256
checked by the fetch script; it is not downloaded again if it is on the PC).

**New: the official image cannot be written as it is.** It is laid out for 512-byte blocks: a DOS partition table and
a FAT16 EFI partition with 512-byte sectors. On this tablet's 4096-byte storage U-Boot refuses such a FAT ("FAT sector
size mismatch") and Linux reads the table in 4 KiB units, so it would not boot. The image builder (`mk-golden.py`)
re-lays it:
- a GPT in 4 KiB units with the standard partition types;
- the EFI partition rebuilt as FAT32 with 4096-byte sectors (same volume id, same 419 files, compared by sha256);
- `/boot` (ext4) and the btrfs root copied unchanged at the same offsets and verified.

The GPT is also what lets the root grow: the image grows itself on the first boot with systemd-repart, which works on
GPT only; on the original layout the root would have stayed at 10.3 GB. The rehearsal serves the disk with the exact
size of `userdata`, so the growth is rehearsed too.

How the installed tablet starts (each link was read from its source; the ones marked * are first seen on the tablet
in run R1):

1. ABL starts U-Boot from `boot_b`.
2. U-Boot maps `userdata` as a disk with 4 KiB blocks* and starts the EFI boot manager.
3. shim, then GRUB from the image's EFI partition*; with no stored EFI variables, shim's fallback creates the boot
   option for this boot only*.
4. GRUB reads the boot entries, loads `kernel-iceland` and its device tree*.
5. The initramfs (with our dracut module) puts a partitioned loop device over `userdata`, so Fedora finds its root
   inside it as on any disk; SELinux enforcing.

Package set: Fedora Workstation's own default, so the default apps are there without us choosing them:

| You asked for | Package in Fedora 44 Workstation | State (apps runs A-C, area-combo-54..56) |
|---|---|---|
| App store | GNOME Software with Flatpak; Flathub switched on | works through dnf5 (no PackageKit); Flathub lists 3035 aarch64 apps; a first Flatpak app costs about 1.2 GB (the GNOME runtime) |
| Camera | Snapshot + libcamera, `pipewire-plugin-libcamera` | **works**: preview on both cameras, photos, video (area-combo-49, -52), with one rule of the device package that keeps the camera frames out of the small CMA memory area |
| Terminal | Ptyxis | window ok |
| Browser | Firefox; GNOME Web added | GNOME Web plays H.264 and VP9 on the hardware decoder; Firefox decodes in software (OpenH264 / its own VP9); Firefox stays the default |
| Files, Settings, Text Editor, Calculator, Clocks, Calendar, Contacts, Weather, Maps, image / video / document viewers, Disks, System Monitor, Logs, Fonts, Characters, Connections, LibreOffice | the Workstation defaults (1.3 GB in RAM tests) | 28 of 29 windows; Connections did not start (most likely the test's launcher: re-check in run D). Location is off by default (Clocks, Weather, Maps cannot locate) |
| Added for a tablet | `gnome-tweaks`, Extensions app, the on-screen keyboard | the keyboard comes up by itself on a tap into a text field |

Left out on purpose: GNOME Boxes (the CPUs start at EL1: no KVM), virtual-machine guest agents, Fedora's kernels and
U-Boot images.

Added on top (all from our repositories, built reproducibly):

| Piece | State today | Missing before the install |
|---|---|---|
| `kernel-iceland` rpm (7.3-rc4 + queue 0001-0108, modules, device tree, `kernel-install` plug-ins) | spec and plug-ins written; built from test kernel q55 on the PC: 12 / 12 checks (installonly, 950 modules, no firmware, no private module) | merge `install.config` (below), build from the final queue, a second version for the update rehearsal |
| `install.config` (new) | written | **two findings**: SELinux is built into the kernel but never starts (`CONFIG_LSM` does not list it), and the kernel cannot load Fedora's xz-compressed firmware. Both are config lines |
| `iceland-device` 0.17 (one battery guard with the charge limit, stock's charging rules and the thermal cap; the skin policy daemon; the cover drop-in; the camera rules; the update rules) | assembled, 62 PC checks pass; first RAM run (area-combo-57): 23 of 25 checks, two test-side points in work | the install fragment (= 0.18): read-only rule, dracut module, snapshots, trial boot, GRUB setup, protected packages (10 / 10 and 68 / 68 PC checks) |
| `hexagonrpc`, `libssc`, `iio-sensor-proxy` (auto-rotate, light, proximity) | built on the tablet, proven | nothing |
| Firmware extractor | **done**: one on-device script, read-only; checked on your backup (23 / 23 items) | runs once in the build session; the files never leave the tablet / PC |
| Patched GStreamer V4L2 plug-in (hardware video) | proven as a file | an rpm |
| Camera sensor module | proven, private (register tables from a trace of stock) | a local, never-published module rpm (your decision 4) |
| The install U-Boot | built (`u-boot-iceland.img`, 10 / 10 checks: no fastboot flashing, EFI write guard, no FAT / ext4 write, variables not stored) | RAM-booted in the rehearsal runs |
| Bluetooth address | **finding**: not in `persist` (its Bluetooth folder is empty in your backup) | the build session writes it into the image from the PC's private record; the image is private anyway |

## 4. Rehearsal from RAM (no write)

The tablet's storage is never written in any of these runs; each takes at most 10 minutes on the tablet.

**How it works.** The PC keeps the golden disk unchanged and serves it over the USB cable as a network block device
with a copy-on-write overlay. U-Boot is RAM-booted with `fastboot boot`; it receives a small "head" (the EFI partition
and `/boot`, about 200 MB packed) also by `fastboot boot`, keeps it in RAM and starts shim and GRUB from it exactly as
it will from `userdata`. The initramfs then takes the disk from the PC instead of from `userdata`. Everything from
U-Boot on is the installed chain; only the disk is on the PC. A guard returns the tablet to Android when the PC's disk
stops answering or the session limit is reached (`panic=10`, hung-task panic, the hardware watchdog).

One write cannot be rehearsed: on a trial boot GRUB clears its "boot once" entry by writing its environment through
U-Boot. In the rehearsal the head is RAM, so the PC replays exactly that write onto the disk, and Linux also clears
the entry early in every trial boot. Whether U-Boot's write into `userdata` works is first seen after write 1
(guide Part C).

| Run | What | Pass |
|---|---|---|
| R0 facts | normal RAM kit; reads `userdata`'s exact size, the storage path the read-only rule matches, firmware slots a = b, the speed of the disk over USB | size 0x3737D0F000, one partition named `userdata`, read speed at least 15 MB/s |
| B1, B2 build | normal RAM kit; firmware extractor, our rpms, GRUB config, SELinux labels, initramfs into the golden disk (over the network, the tablet's storage untouched) | each step rc 0; the initramfs has our module and the read-only rule |
| R1 first boot | the real chain, SELinux permissive to collect denials | the acceptance list (below); the U-Boot console file and the screen if it stops early |
| R2 acceptance | the same, SELinux enforcing | `INSTALL-ACCEPT: n PASS, 0 FAIL` |
| U1, U2, U2b, U3 | update with Fedora's current updates; a new kernel boots once and is confirmed; a broken kernel falls back by itself; GNOME Software's offline update | held packages offered 0, a snapshot before every transaction, the trial and its fallback as described in section 6 |
| R1b, R2b, R3 | the previous kernel from GRUB's menu; rollback to the previous snapshot; repair from the rescue kit | each as described |
| R4 final | the written file itself from its pristine state (fresh overlay), SELinux enforcing | 0 FAIL; then the sparse image and the record: **this exact file is what gets written** |

Acceptance list (one script, one summary line): GNOME session, touch, Wi-Fi scan with 5 GHz, Bluetooth, sound
cards, battery and time estimate, power modes, auto-rotate after a boot, suspend and resume, hardware video, both
cameras listed, the default apps start, About shows "OnePlus Pad 4", `rpm -Va` clean for our packages, the root
grown to the whole `userdata`, every other partition read-only, no `avc: denied` that breaks a service.

Facts that only the tablet can answer (each has its run): U-Boot unpacking 2.5 GB at its address; shim's fallback
under U-Boot; GRUB on a 4 KiB disk and which device tree Linux gets; whether the USB link survives the sensor /
charger processor starting inside the initramfs; SELinux denials of our daemons; the first-boot growth; sleep with
the root on the network; memory with the head in RAM.

## 5. The writes (each one only after your OK; you run or confirm each command)

### 5.1 Write 1: `userdata`

- Before: G1-G5, G9-G13 closed; battery above 60 %; the PC's USB port that has been used all along.
- Command (stock ABL fastboot, which splits a sparse image by itself; its limit is 805 MB per piece):
  `fastboot flash userdata fedora-iceland.sparse.img` - the sparse image from run R4; its unpacked size equals
  `userdata` exactly, and only about 12.8 GB of it are data.
- What it changes: Android's data is gone (LineageOS will no longer start; its system partitions stay).
- Proof before going on: boot tethered (`fastboot boot` the install U-Boot from the PC), Fedora's first-boot setup
  appears, the acceptance list passes again, three cold boots in a row, and GRUB's environment is compared before
  and after a trial boot (U-Boot's write into `userdata`).
- Undo: return to stock (section 8), or flash the image again.
- Hazard to know: until write 2 the tablet starts Android when it is switched on without the PC, and Android will
  say its data is damaged and offer a factory reset. Do not confirm it (it would erase Fedora, nothing worse).
  Keep this stage short.

### 5.2 Write 2: the boot path

Recommended: **the install U-Boot into `boot_b`** (the boot partition of the slot that is active today), so that
switching the tablet on starts Fedora.
- Before: G11 and G12; the slot must be marked successful, so that ABL does not count boot attempts. Save `boot_b`
  once more from the tablet and compare with the backup; compare the two image headers (`check-header.py`: the saved
  `boot_b` is a version 4 image whose OS version and patch level are zero; Android keeps them in the AVB footer).
- **New finding: `boot_b` is verified by Android Verified Boot** (`vbmeta_b` chains it). After the write ABL finds
  no valid signature for it. On an unlocked tablet a Qualcomm ABL warns ("orange" state) and continues; this is
  expected, but no RAM boot can prove it (`fastboot boot` skips this check). The three cold boots below are the
  proof, and the undo is ready.
- Command: `fastboot flash boot_b u-boot-iceland.img` (the file of the record, RAM-booted in R1-R4).
- Proof: switch on without the PC three times; then read the slot flags again in ABL (Volume Down + Power): the
  retry counter must not have gone down. If it has, undo this write at once and use the alternative below.
- Undo: `fastboot flash boot_b boot_b.img` from the backup (two minutes).
- Alternative if ABL counts attempts for (or refuses) a boot image it cannot verify: U-Boot into `recovery_b`. Fedora
  then starts with Power + Volume Up; a plain power-on still starts Android (which has no data). Less convenient, same
  safety. (`recovery_b` is very likely chained the same way; the backup's `vbmeta_b` says, read with avbtool before
  the day.)

Dual boot (Android next to Fedora) stays outside this plan: it needs the partition table of unit sda changed. The
install U-Boot is ready for it (a partition named `fedora` wins over `userdata`), so it can be planned separately.

### 5.3 What never happens in the writes

No `-w`, no `flashall`, no `update`, no `set_active`, no flashing of any partition from the never list, no
third-party flashing tool: only `fastboot flash userdata` and `fastboot flash boot_b` with files whose checksums
were recorded in the rehearsal. No script of the project contains any other storage write (the install workflow's
self-check refuses the words in every one of its scripts).

## 6. Updates on the installed tablet without breaking it

### Why an update cannot brick the tablet

Fedora can only write inside `userdata` (section 2). The worst an update can do is make Fedora itself not start.
The tablet's boot loader and fastboot are out of its reach, so the PC can always RAM-boot the rescue kit and repair,
or write the image again.

### What Fedora's updates may and may not replace

| Package group | Source | Rule |
|---|---|---|
| `kernel`, `kernel-core`, `kernel-modules*` (Fedora's kernels) | never installed | excluded in dnf's configuration; they have no Pad 4 support |
| `kernel-iceland` | our local repository (`/var/lib/iceland/repo`, filled by `iceland-repo-sync` from the PC) | three versions kept; a new one boots once and becomes the default only when the desktop has been up for 30 s with it |
| `iio-sensor-proxy`, `hexagonrpc`, `libssc`, the patched GStreamer plug-in, `iceland-device` | our local repository (higher priority; our release numbers above Fedora's) | Fedora's versions are never chosen while ours exist |
| `dracut-config-rescue`, akmods / dkms, bootupd, sdubby, U-Boot images, `fwupd-efi` + capsule data | never installed | **new** excludes (they were missing in 0.16; GNOME Software pulled the last two in through fwupd) |
| `grub2`, `shim`, `linux-firmware` and the firmware packages | Fedora | **changed proposal: held by default** (one setting); released one at a time after a RAM rehearsal with the new version. Before, the plan let them update freely; the install work showed that GRUB is the one package that writes during the boot and that shim's fallback path is not yet proven under U-Boot |
| Mesa, GNOME, PipeWire, libcamera, everything else | Fedora | updates normally. A regression costs a feature (for example software rendering), never the boot |
| Fedora 45 (version upgrade) | **pinned to 44** | **new finding**: the 0.16 polkit rule named PackageKit, but Fedora 44's GNOME Software uses dnf5's daemon, which has one permission for updates and upgrades: the rule blocked nothing. The release is now pinned in dnf's repository configuration (proven in run C); an empty file of the same name lifts the pin after a RAM rehearsal of Fedora 45 |
| `fwupd` firmware updates | only harmless plug-ins | see section 2 (the UFS storage was listed as updatable) |

`iceland-device` and `kernel-iceland` are also protected packages: dnf refuses to remove the last of them.

### Order of an update that touches our packages

1. PC: build the new rpm (kernel, device package, ...).
2. PC: RAM-boot the new kernel with the kit and run the automated checks (as every kernel so far).
3. PC to tablet: `iceland-repo-sync` copies the rpm into the tablet's local repository (checksums verified).
4. Tablet: `dnf upgrade` (or GNOME Software). A btrfs snapshot of the root is taken before EVERY transaction (also
   from GNOME Software and offline updates), with a "Roll back to ..." boot entry each; the last three are kept.
5. First boot of a new kernel is a trial ("boot once"). Only when the desktop has been up for 30 s with it does it
   become the default. If it does not come up, the next power-on starts the previous kernel by itself.
6. If the desktop itself is broken by Fedora's updates: boot the previous snapshot from GRUB's menu (shown 3 s,
   chosen with the volume keys), or repair from the rescue kit.

### The rescue path (always available)

`fastboot boot` of the test kit from the PC, exactly as today: it does not use the tablet's storage to start. From
there the installed root can be mounted (read-only first), checked, rolled back to a snapshot, or the kernel
replaced. This is also how a forgotten password or a full disk is handled.

## 7. Known gaps on the day of writing (what "full install" will not have yet)

- Deep sleep: suspend and resume work; the chip's deepest sleep state is not reached yet (CX collapse reached in a
  test kernel, run 59), so the tablet drains faster asleep than on stock until the deep-sleep work is queued and one
  night unplugged has been measured.
- Cameras: everything automated works (both cameras, the Camera app, a browser); automatic focus needs lens support
  in libcamera (not there yet); colours and sharpness need your eyes.
- Speakers stay volume-capped until speaker protection exists; fast charging (SuperVOOC) is not planned.
- The NPU needs Qualcomm's SDK (your decision); Wi-Fi 5 GHz connect needs your password once; the Wi-Fi country
  setting is yours.
- Items that need your hands once: wall-charger checks, one turn of the tablet, the microphone meter, the pen (90 s on
  the magnet side), the keyboard cover (type once), the cover / cable / power-key windows of the wake test.
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
3. Whether an open gate G6-G8 / G14 blocks the install or only sets the "charge attended, 80 %" default.
4. Whether the camera module (private, built from a trace of stock) is part of the image on your tablet.
5. (new) GRUB, shim and firmware held back from Fedora's updates (default, recommended) or updated freely.
6. (new) Fedora pinned to release 44 until 45 is rehearsed (default, recommended).
7. (new) LibreOffice (with Java, about 650 MB) in the image (default yes); GNOME Web next to Firefox (default yes).
8. (new) The skin temperature limit: 48 C as today, or stock's 60 / 61 C with the policy daemon (recommended).
9. (new) A permanent "day 0" snapshot (section 11.2; recommended) and a regular copy of your home folder to the PC.
10. (new) The Wi-Fi country.

## 10. Work list that follows from this plan

| # | Item | State |
|---|---|---|
| 1 | `kernel-iceland` rpm with the device-tree plug-in; the read-only rule, dracut module, snapshot, trial-boot and GRUB units in `iceland-device` | built and checked on the PC (install workflow pieces a, b) |
| 2 | The on-device firmware extractor | done, checked on your backup (piece c) |
| 3 | The image builder, the network-disk rehearsal, the acceptance list as a script | built and checked on the PC (pieces d, e: the network disk 418 / 418 checks plus an independent client) |
| 4 | The update and rollback rehearsal | scripts written (piece f); need the tablet runs |
| 5 | G13: the written proof that the rehearsal cannot touch the storage | asked |
| 6 | Merge `install.config`, build the kernel rpm from the final queue and a second version; iceland-device 0.18 | next, PC only |
| 7 | Runs R0, B1, B2, R1, R2, U1, U2, U2b, U3, R1b, R2b, R3, R4 (RAM only, each under 10 minutes) | after 5 and 6 |
| 8 | G3, G4, G5, G11, G12 (read-only checks and copies; G4 / G5 need you) | yours |
| 9 | Then, and only with your OK: write 1, later write 2 (guide Parts C and D) | yours |

## 11. Unbrickable, restorable, permanent: the suggestions

The plan above already keeps the tablet unbrickable by never writing what fastboot depends on. These suggestions
make every layer above that just as safe, so that the install can be left on the tablet for years.

### 11.1 Unbrickable: the boot firmware can never be reached

1. **Keep the write surface at two partitions forever.** Updates of U-Boot are a new "write 2" with the same
   rehearsal and your OK; everything else updates inside `userdata` only.
2. **Prove the rescue door before the first write (G12).** Fastboot through Volume Down + Power from a cold start
   must work with whatever is in `boot_b`, because ABL opens it before it looks at the boot partition. Doing it once
   on the day turns "should" into "seen".
3. **Never lock the boot loader while Fedora is on the tablet**, never switch slots, never flash older firmware (the
   anti-rollback fuses would refuse it, or worse).
4. **Close the last software path to the hardware:** no storage-firmware update from Fedora (fwupd plug-ins off and
   re-checked after every update of fwupd), no EFI program writes outside `userdata` (U-Boot's write guard), every
   other partition read-only from the initramfs on.
5. **The rehearsal itself must be unable to write (G13).** It is the one place where new boot code runs on the tablet
   before the install; it gets the same written proof as the writes.
6. **Do not let the battery run flat.** A deeply discharged battery is the most common way a tablet "looks bricked".
   Fedora powers off at the critical level as stock does (UPower's critical action), the battery guard keeps its
   shutdown temperatures, and the charge limit keeps the battery between 80 and 85 % on the charger. One fact to see
   on the day: what ABL does when a switched-off tablet is plugged in (stock starts its charging screen from the boot
   partition; with U-Boot there it starts Fedora). Recommended follow-up: let U-Boot pass ABL's boot reason to Linux,
   so that a "plugged in while off" start can show a charging screen or power off again.

### 11.2 Restorable: six ways back, from the smallest to the largest

| Level | What brings it back | Needs the PC | What is lost |
|---|---|---|---|
| L0 trial boot | a new kernel that does not reach the desktop is skipped on the next power-on | no | nothing |
| L1 previous kernel | GRUB's menu (3 s, volume keys): one of the three kept kernels | no | nothing |
| L2 snapshot | "Roll back to ..." entry: the root as before the last update (three kept) | no | changes since that update, not your home folder |
| **L2b day-0 snapshot (suggested)** | a read-only snapshot of the root made at the first boot and never pruned: "factory reset" of Fedora without the PC | no | system changes since the install, not your home folder |
| L3 rescue kit | `fastboot boot` of the RAM kit; mount, check, roll back, replace the kernel | yes | nothing |
| L4 the recorded image | `fastboot flash userdata` with the sparse image of the record | yes | everything in Fedora (your home folder too, unless copied: see below) |
| L5 stock | `39-Return-To-Stock.ps1` with your backup | yes | Fedora |

Suggestions that make these levels real:
- **Keep the release set together on the PC and on a second disk:** the sparse image and its checksum, the install
  U-Boot, the saved `boot_b`, the backup and the stock images, the record of section 10 of the guide. With G4 done,
  L4 and L5 survive a failed PC disk.
- **Copy your home folder to the PC now and then** (a `btrfs send` of a read-only snapshot of `/home` over the USB
  link; a small script in the device package can do it). Then L4 loses nothing that matters.
- **Rehearse L0-L3 before the install** (runs U2b, R1b, R2b, R3) and L4-L5 as far as possible without writing (the
  checksums, the dry run of the return script). A way back that was never tried is a hope, not a way back.

### 11.3 Permanent: stays working through years of updates

1. **Only one source for the kernel**: our repository, each version RAM-tested with the kit before it reaches the
   tablet, then a trial boot on the tablet itself.
2. **Fedora updates normally, boot code does not move by itself**: GRUB, shim and firmware held, Fedora pinned to its
   release; each is released after a RAM rehearsal of the new version with our kernel (the same tools as for the
   install).
3. **The rehearsal tools stay in use after the install**: every Fedora version upgrade and every new U-Boot goes
   through the network-disk rehearsal first (a copy of the installed disk can be served from the PC the same way).
4. **Watch the battery and the sleep drain**: the guard and the thermal daemon run from the device package; the
   deep-sleep work and one measured night belong before calling the install finished (G14).
5. **Keep stock's numbers**: every limit in the package is stock's or lower, and the stock-values audit tool runs
   after every queue change (it exits with an error on a new, unjudged difference).

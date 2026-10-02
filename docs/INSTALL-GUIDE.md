# OnePlus Pad 4: guide for installing Fedora 44 GNOME on the tablet

Written 2 Oct 2026. This is the step-by-step companion of `docs/INSTALL-PLAN.md` (the reasons are there; the steps
are here). Nothing in this guide has been done on the tablet. Every write is done by you, one command at a time,
after its own checks.

**Read section 0 first. On the day of writing the guide can be followed up to the end of Part A. Parts C and D
(the two writes) are locked until Part B has produced the two files and their checksums.**

---

## 0. Where things stand, and the rules

### 0.1 Readiness (update this table before you start)

| Item | State on 2 Oct 2026 | Needed for |
|---|---|---|
| G1 full backup of all 151 partitions, checksummed (`C:\OnePlusPad4\backups\20260927-1933-unknown`) | exists | everything |
| G2 stock 11.A.38 images + checksums (`C:\OnePlusPad4\stock-11.A.38`) | exists | return to stock |
| G3 return-to-stock scripts (`C:\OnePlusPad4\scripts\30-`, `31-`, `39-`) and their dry run | scripts exist; dry run = Part A step 3 | return to stock |
| G4 second copy of G1 + G2 on another disk | **not done** (Part A step 4) | write 1 |
| G5 file copy of Android's `/data/vendor` (and a saved copy of today's `boot_b`) | **not done** (Part A step 5) | write 1 |
| G11 slot flags of the active slot read and understood | **not done** (Part A step 6) | write 2 |
| Kernel as an installable package (`kernel-iceland` rpm with the device-tree hook) | test-built only | Part B |
| Device package `iceland-device` with the read-only rule for the other partitions, the snapshot and the trial-boot units | 0.16 exists; these three parts **not built** | Part B |
| On-device firmware extractor (GPU, video, Wi-Fi, Bluetooth, audio, touch, sensor hub files) | parts exist as PC scripts | Part B |
| Image builder + rehearsal from RAM over the USB network (G9) | **not built** | Part B |
| Update and rollback rehearsal (G10) | **not done** | Part B |
| Charging, low-battery and thermal protection as stock (G6-G8) | kernel parts queued and proven on a PC port; wall chargers need one sitting with you | leaving the tablet alone on a charger |
| Your decisions (section 0.4) | open | Parts C and D |

The install must not start while any line that is "needed for write 1" or "Part B" is open.

### 0.2 The safety rules (the ones set in the plan; they never change)

1. **Only two partitions are ever written:** `userdata` (the Fedora image) and ONE boot-path partition of the
   active slot (`boot_b` today). Each has its own undo.
2. **Never written:** the boot firmware (`xbl*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `uefi*`, `shrm*`,
   `cpucp*`, `qupfw*`, `tme_*`, `imagefv*`, `keymaster*`, ...), the radio / DSP firmware (`modem*`, `bluetooth*`,
   `dsp*`), the per-device data (`persist`, `cdt`, `ddr`, `dinfo`, `ocdt`, `oplusreserve*`, `nonmodemst*`, ...), the
   security state (`devinfo`, `keystore`, `frp`, `ssd`, `secdata`, `uefivarstore`, ...), Android's system
   (`super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `misc`, ...) and every
   partition table. As long as these are untouched the tablet's own boot loader and its fastboot keep working,
   and fastboot can put everything back.
3. **Commands that are never typed** during the install: `fastboot -w`, `fastboot flashall`, `fastboot update`,
   `fastboot set_active`, `fastboot erase ...`, `fastboot format ...`, `fastboot flashing lock`,
   `fastboot flash` with any partition name other than `userdata` and `boot_b`. No third-party flashing tool.
   (`fastboot -w`, `set_active` and the stock boot set are used only by the return-to-stock script, section 8.)
4. **Only files whose SHA-256 was recorded in the rehearsal** are written, and each is checked again right
   before its write.
5. **The image is rehearsed from RAM first**, through the same boot chain, before it is written.
6. **U-Boot stays unable to write the storage.** Fedora gets a rule that makes every other partition read-only.
7. **Nothing is urgent.** If a screen, a message or a number differs from what this guide says: stop, do not
   improvise, do not retry a write. The boot loader is intact in every state this guide can produce, and section 9
   tells what to do.
8. Battery above 60 %, the PC's own USB port that was used in all tests, the same cable, the PC on mains power,
   no sleep on the PC during a write.

### 0.3 What the tablet looks like after each stage

| Stage | Power-on without the PC | With the PC |
|---|---|---|
| Today | LineageOS (slot b) | RAM test kits |
| After write 1 (`userdata`) | Android starts and says its data is damaged. **Do not confirm a factory reset.** Keep this stage short | `fastboot boot` of U-Boot starts Fedora |
| After write 2 (`boot_b`) | Fedora | the RAM rescue kit still works |
| After the return to stock | OxygenOS 11.A.38 | - |

### 0.4 Decisions that are yours (answer them before Part C)

1. Fedora only (this guide), or dual boot with Android (not covered: it needs the partition table changed).
2. Boot path: `boot_b` (a normal power-on starts Fedora; recommended) or `recovery_b` (Power + Volume Up starts
   Fedora, a normal power-on starts Android, which then has no data).
3. Whether an open charging / thermal gate (G6-G8) blocks the install or only sets the rule "charge attended,
   charge limit on".
4. Whether the private camera driver is part of the image on your tablet.

---

## Part A - preparation on the PC and read-only checks (no write)

Open a PowerShell window. All commands assume the tools in `C:\platform-tools` and the kit in `C:\OnePlusPad4`.

### Step 1 - verify the backup (G1)

```powershell
C:\OnePlusPad4\scripts\03-Verify-Backup.ps1 -Backup C:\OnePlusPad4\backups\20260927-1933-unknown
```

Expected: "N files intact (hashes match what the tablet reported)" and, for both slots, "all images identical to
11.A.38" (or a named list of differences that you have seen before). **Stop** if a file is reported damaged or
missing: make a new backup first (`02-Backup-AllPartitions.ps1`, from Android with root).

### Step 2 - verify the stock images (G2)

```powershell
cd C:\OnePlusPad4\stock-11.A.38
Get-Content .\SHA256SUMS.txt | ForEach-Object { $h, $f = $_ -split '\s+', 2; if ((Get-FileHash $f -Algorithm SHA256).Hash -ne $h.ToUpper()) { "DAMAGED: $f" } }
```

Expected: no output. Any "DAMAGED" line: stop and fetch the stock package again.

### Step 3 - dry run of the return to stock (G3)

```powershell
C:\OnePlusPad4\scripts\30-Restore-Stock.ps1
```

Without `-Execute` this only checks and prints its plan. Read the plan: it must list only `boot`, `init_boot`,
`vendor_boot`, `dtbo`, `recovery`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor`, `pvmfw` on both slots, `super`, and
the erase of `userdata` / `metadata`. It must not list any firmware partition. Expected last lines: no problem
found.

### Step 4 - second copy of the backup and the stock images (G4)

Copy `C:\OnePlusPad4\backups\20260927-1933-unknown` and `C:\OnePlusPad4\stock-11.A.38` to a second disk (about
17 GB + the stock package) and run step 1 against the copy (`-Backup <path on the second disk>`). The backup holds
the calibration and identity of this one tablet; no download replaces it. Do not upload it anywhere.

### Step 5 - save what write 1 would destroy (G5)

With LineageOS running, USB debugging on, and "Rooted debugging" enabled in the developer options:

```powershell
cd C:\platform-tools
.\adb.exe root
cmd /c 'C:\platform-tools\adb.exe exec-out "tar -C /data -cf - vendor" > C:\OnePlusPad4\backups\data-vendor-20261002.tar'
.\adb.exe pull /dev/block/by-name/boot_b C:\OnePlusPad4\backups\boot_b-before-install.img
Get-FileHash C:\OnePlusPad4\backups\data-vendor-20261002.tar, C:\OnePlusPad4\backups\boot_b-before-install.img -Algorithm SHA256
(Get-Item C:\OnePlusPad4\backups\boot_b-before-install.img).Length
.\adb.exe unroot
```

Both commands only read (the `cmd /c` form keeps the archive binary-exact; PowerShell's own `>` would damage it).
Expected: `boot_b-before-install.img` is exactly 100663296 bytes (96 MB); write both hashes into section 10. This `boot_b` image is the undo file of write 2. Your photos and other personal files on
LineageOS are **not** covered by this step: copy what you want to keep before write 1 (write 1 erases all Android
data).

### Step 6 - read the slot flags (G11)

```powershell
cd C:\platform-tools
.\adb.exe reboot bootloader
cmd /c 'C:\platform-tools\fastboot.exe getvar all 2>&1 | findstr /i "product current-slot slot-successful slot-retry-count slot-unbootable unlocked partition-size:userdata partition-size:boot_b"'
.\fastboot.exe reboot
```

`getvar` only reads (the filter also keeps the serial number off the screen). Write the values into section 10.
Expected: `product: canoe`, `unlocked: yes`, `current-slot: b`, `slot-successful:b: yes`, `slot-unbootable:b: no`,
a retry count for slot b, `partition-size:userdata: 0x3737D0F000` (237 159 641 088 bytes),
`partition-size:boot_b: 0x6000000`.
If slot b is **not** marked successful, the boot loader counts boot attempts: then write 2 must not use `boot_b`
without the extra check in Part D step 1 (or use `recovery_b`).

---

## Part B - the rehearsal from RAM (no write)

This part is done together with the PC session; its tools are the plan's work list (items 1 to 4) and are not
finished on the day of writing. What it must produce before Part C may start:

1. **The image**: the official Fedora-Workstation-Disk-44 aarch64 raw image (checksum-verified) + our packages
   (`kernel-iceland`, `iceland-device`, the sensor packages, the patched video plug-in, optionally the private
   camera module), with the tablet's own firmware copied in by the extractor from the tablet's partitions, read
   only.
2. **A boot of exactly that image from RAM** through the real chain: `fastboot boot` of U-Boot, U-Boot starts GRUB
   from the image's EFI partition, GRUB starts our kernel, SELinux enforcing; the image is served from the PC over
   the USB network. The tablet's storage is not written.
3. **The acceptance list passed on that boot** (automated): GNOME session, touch, Wi-Fi scan with 5 GHz,
   Bluetooth, sound, battery and time estimate, charge limit, power modes, auto-rotate, suspend and resume,
   hardware video, both cameras, the default apps start, About shows "OnePlus Pad 4", our packages verify clean.
4. **The update rehearsal** (a `dnf upgrade` keeps our kernel and sensor packages; a new kernel is installed next
   to the old one and both start) and **the rollback rehearsal** (previous kernel from GRUB's menu, previous root
   snapshot, repair from the RAM rescue kit).
5. **The two files and their checksums**, written into section 10:
   - `fedora-iceland.sparse.img` (the rehearsed image, converted to a sparse image),
   - `u-boot-iceland.img` (the U-Boot image that was `fastboot boot`ed in the rehearsal; it cannot write the
     storage).

Part B is complete when section 10 has both SHA-256 values and the date of the passed acceptance list.

---

## Part C - write 1: the Fedora image into `userdata`

Only when: section 0.1 has no open line for write 1, section 0.4 is answered, section 10 is filled in, battery
above 60 %, your files from LineageOS are saved.

### Step 1 - check the file

```powershell
cd C:\platform-tools
(Get-FileHash .\fedora-iceland.sparse.img -Algorithm SHA256).Hash
```

Must equal the value in section 10, letter for letter. Otherwise stop.

### Step 2 - enter the boot loader and check the tablet

```powershell
.\adb.exe reboot bootloader
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar unlocked
.\fastboot.exe getvar partition-size:userdata
```

Expected: `canoe`, `b`, `yes`, and `0x3737D0F000` (237 GB; it must be larger than the image's unpacked size noted
in section 10). Anything else: `.\fastboot.exe reboot` and stop.

### Step 3 - the write

Type it exactly; the only partition name is `userdata`:

```powershell
.\fastboot.exe flash userdata .\fedora-iceland.sparse.img
```

The boot loader splits the image into pieces of at most 805 MB and reports each ("Sending sparse 'userdata'
1/N ... OKAY", "Writing 'userdata' ... OKAY"), then "Finished". Do not touch the cable. This erases all Android
data.

If it stops with an error or the cable drops: the boot loader is unaffected. Stay in (or re-enter) fastboot
(Power + Volume Down) and run the same command again from the start. Do not run anything else.

### Step 4 - proof, still tethered

```powershell
.\fastboot.exe boot .\u-boot-iceland.img
```

Expected: U-Boot's text, GRUB, then Fedora's first-boot setup on the tablet. Go through the setup, then switch
off and repeat the tethered boot until you have seen **three cold boots in a row** reach the desktop. The PC
session runs the acceptance list again on one of them.

Until Part D the tablet starts Android when it is switched on without the PC; Android reports damaged data and
offers a factory reset: **choose "Try again" or power off, never the reset** (it would erase Fedora; nothing
worse). Keep this stage short.

Undo of write 1: section 8 (return to stock), or write the image again.

---

## Part D - write 2: U-Boot into `boot_b`

Only after Part C step 4 passed.

### Step 1 - check the file and the slot

```powershell
cd C:\platform-tools
(Get-FileHash .\u-boot-iceland.img -Algorithm SHA256).Hash
(Get-FileHash C:\OnePlusPad4\backups\boot_b-before-install.img -Algorithm SHA256).Hash
```

Both must equal section 10. Then put the tablet into the boot loader's fastboot: switch it off (hold Power about
15 s), hold Power + Volume Down, connect USB. `fastboot getvar product` must answer `canoe` (that is the tablet's
own boot loader; U-Boot's fastboot is not used for a write):

```powershell
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar partition-size:boot_b
```

Expected: `canoe`, `b`, `yes`, the retry count from Part A step 6, `0x6000000`. Note the retry count.

### Step 2 - the write

Type it exactly; the only partition name is `boot_b`:

```powershell
.\fastboot.exe flash boot_b .\u-boot-iceland.img
.\fastboot.exe reboot
```

### Step 3 - proof

1. Unplug the PC. Switch the tablet off and on **three times**. Each time Fedora must reach the desktop.
2. Enter the boot loader once more (power off, hold Power + Volume Down, connect USB) and read:

```powershell
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe reboot
```

The retry count must be the number noted in step 1 and `slot-unbootable:b` must be `no`.
**If the count went down:** the boot loader is counting attempts for a boot image it cannot mark good. Undo
write 2 now (below) and use the `recovery_b` alternative.

Undo of write 2 (two minutes, from the boot loader):

```powershell
.\fastboot.exe flash boot_b C:\OnePlusPad4\backups\boot_b-before-install.img
```

Alternative boot path (`recovery_b`): `tools\dualboot\reflash-recovery.ps1` of the iceland-mainline repository
writes U-Boot into `recovery_b` only, after checking the image and a typed confirmation. Fedora then starts with
Power + Volume Up.

---

## 7. After the install

- **First hour:** Wi-Fi, sound, rotation, a suspend and resume, About shows "OnePlus Pad 4"; Settings > Power
  shows "Battery Charging": choose "Preserve Battery Health" (stops at 85 %).
- **Charging:** until the one sitting with your wall chargers is done (the charging row of the feature matrix),
  charge attended and prefer the PC port or a plain 5 V charger. The tablet does not fast-charge (SuperVOOC is not
  supported); the stock temperature and current limits are enforced by the kernel and the battery guard.
- **Updates:** GNOME Software / `dnf upgrade` as on any Fedora. They can only change files inside the Fedora
  partition. Fedora's own kernels are excluded; our kernel and the few special packages come from the tablet's
  local repository, which the PC fills (`iceland-repo-sync`), and a new kernel only becomes the default after it
  has started once. Do **not** upgrade to Fedora 45 until that version has passed the RAM rehearsal (the upgrade
  is hidden and blocked by the device package).
- **Never from inside Fedora:** no partitioning tool on the internal storage, no `dd` to `/dev/sd*`, no firmware
  update tool, no boot-loader tool. The device package makes the other partitions read-only, so a mistake fails
  instead of doing harm; do not remove that rule.
- **Rescue (always available):** the RAM test kit from the PC (`fastboot boot`, as in every test so far) starts
  without using the storage; from there the installed system can be mounted, checked, rolled back to a snapshot,
  or given another kernel. A forgotten password or a full disk is handled the same way.

---

## 8. Back to stock OxygenOS, from any stage

| From | Do |
|---|---|
| Before any write (today) | nothing: reboot starts Android |
| Only undo write 2 | `fastboot flash boot_b C:\OnePlusPad4\backups\boot_b-before-install.img` |
| Full return to stock | `C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1` |
| Factory state with a locked boot loader (optional) | step 4 of the same script (`31-Relock-Bootloader.ps1`), only when its own check says the tablet is exactly stock |

`39-Return-To-Stock.ps1` first verifies the backup and the stock images (read-only) and shows a dry run. After you
type its confirmation it writes the stock boot set to both slots and `super` from your backup, erases `userdata`
and `metadata`, and then proves the result is byte-identical stock. It never writes firmware. If it is
interrupted: enter fastboot again (Power + Volume Down) and run it again.

---

## 9. If something is not as described

| What you see | What it means | What to do |
|---|---|---|
| `fastboot flash userdata` fails or the cable drops | incomplete image in `userdata`; boot loader untouched | re-enter fastboot (Power + Volume Down), run the same command again |
| After write 1, Android says "data may be corrupt" | expected between write 1 and write 2 | "Try again" or power off; never "Factory data reset" |
| Tethered boot after write 1 does not reach Fedora | image or chain problem | do not do write 2; RAM-boot the test kit for a look; or return to stock |
| After write 2 the screen stays black or stops in U-Boot | U-Boot started but found no system | hold Power about 15 s; enter fastboot (Power + Volume Down); undo write 2 |
| After write 2 the tablet starts Android again by itself | the boot loader fell back to another slot | enter fastboot, read the slot flags (Part D step 3), do not use `set_active`; undo write 2 and run the return to stock if the slot is marked unbootable |
| Retry count went down after write 2 | the boot loader counts attempts | undo write 2, use `recovery_b` |
| Fastboot does not appear with Power + Volume Down | cable / driver, or the tablet is still on | hold Power 15 s to switch off, try again, try the other end of the cable; the boot loader was not written by anything in this guide |
| Fedora does not start after an update | a Fedora-side problem | previous kernel or snapshot from GRUB's menu; else the RAM rescue kit |
| Anything not in this table | - | stop; nothing further is written; ask the PC session with the exact text on the screen |

---

## 10. The record (fill in; the writes use only what is written here)

| Item | Value | Date |
|---|---|---|
| Backup verified (Part A step 1) | | |
| Stock images verified (step 2) | | |
| Return-to-stock dry run read (step 3) | | |
| Second copy made and verified (step 4), where | | |
| `data-vendor-....tar` SHA-256 | | |
| `boot_b-before-install.img` SHA-256 (size 100663296) | | |
| Slot flags: current-slot / successful:b / retry-count:b / unbootable:b | | |
| Acceptance list passed on the rehearsal boot (Part B) | | |
| Update and rollback rehearsal passed | | |
| `fedora-iceland.sparse.img` SHA-256, unpacked size | | |
| `u-boot-iceland.img` SHA-256 | | |
| Decisions 0.4 (1 / 2 / 3 / 4) | | |
| Write 1 done, three tethered cold boots | | |
| Write 2 done, three untethered cold boots, retry count unchanged | | |

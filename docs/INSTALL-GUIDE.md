# OnePlus Pad 4: guide for installing Fedora 44 GNOME on the tablet

Written 2 Oct 2026, revised the same evening (install workflow round 7: the write-2 probe C0 first, the review's
R-1 / R-2 / R-4 / R-8 / R-9 points, the slot-retry finding). This is the step-by-step companion of
`docs/INSTALL-PLAN.md` (the reasons are there; the steps are here). **Nothing in this guide has been done on the
tablet yet.** Every write is done by you, one command at a time, after its own checks.

**Read section 0 first.** The order is: Part A (read only) - Part B (the rehearsal from RAM, no write) - **Part C0
(the write-2 probe: U-Boot into `boot_b` while Android's data is still there, undone the same day)** - Part C (write
1) - Part D (write 2). Parts C and D stay locked until Part B has produced its files and checksums and C0 has passed.

---

## 0. Where things stand, and the rules

### 0.1 Readiness (update this table before you start)

| Item | State on 2 Oct 2026 (evening) | Needed for |
|---|---|---|
| G1 full backup of all 151 partitions, checksummed (`C:\OnePlusPad4\backups\20260927-1933-unknown`) | exists. It predates LineageOS (taken under OxygenOS on 27 Sep): it is the return-to-stock source, **not** the undo of write 2 | everything |
| G2 stock 11.A.38 images + checksums (`C:\OnePlusPad4\stock-11.A.38`) | exists | return to stock |
| G3 return-to-stock scripts (`C:\OnePlusPad4\scripts\30-`, `31-`, `39-`) and their dry run | scripts exist; dry run = Part A step 3. Written and dry-run only, never executed | return to stock |
| G4 second copy of G1 + G2 on another disk | **not done** (Part A step 4) | write 1 |
| G5 file copy of Android's `/data/vendor` | **not done** (Part A step 5) | write 1 |
| G11 slot flags of both slots read and understood | done automatically by Part A step 6 (`parta-read.ps1`) | C0, write 2 |
| G12 fastboot reached by the keys from a cold start | **not done** (Part A step 7) | C0 |
| G13 the rehearsal cannot touch the storage | **closed** (a U-Boot build without UFS support, the read-only rule in the initramfs, a network-disk-only carrier, the self-check) | Part B |
| G14 sleep drain known | in work (deep-sleep workflow); not a safety gate | leaving the tablet asleep for days |
| Kernel as an installable package (`kernel-iceland`) | built from test kernel q78 (queue 0001-0162): K2 and a second version K3 for the update rehearsal, 13 checks each | Part B |
| Device package `iceland-device` 0.18 (read-only rule, dracut module, snapshots, trial boots, GPU firmware from Fedora's `qcom-firmware`) | built on the tablet in the B run (runs 93 / 94); rebuilt with the round-7 fixes before the next B run | Part B |
| Firmware extractor (the tablet's own files, read only) | done; checked on the backup: 23 of 23 items, 0 differ from stock 11.A.38 | Part B |
| Image builder + rehearsal from RAM over the USB network (G9) | built; B run passed (runs 93 / 94); **the first rehearsal boot R1 is pending** (round 5 fixed its U-Boot stop) | Part B |
| Update and rollback rehearsal (G10) | scripts ready; runs U1-U3, R1b, R2b, R3 pending | Part B |
| AVB footer for the install U-Boot + its PC proof (review R-1) | done; re-made and re-proven on the day from today's `boot_b` by Part A step 6 | C0, write 2 |
| Charging, low-battery and thermal protection as stock (G6-G8) | kernel parts queued and proven on a PC port; wall chargers need one sitting with you | leaving the tablet alone on a charger |
| Your decisions (section 0.4) | partly answered | C0, Parts C and D |

The install must not start while any line that is "needed for write 1" or "Part B" is open; C0 must not start
while a line "needed for C0" is open.

### 0.2 The safety rules (the ones set in the plan; they never change)

1. **Only two partitions are ever written:** `userdata` (the Fedora image) and ONE boot-path partition of the
   active slot (`boot_b` today). Each has its own undo. The probe C0 writes `boot_b` once and puts it back the same
   day.
2. **Never written:** the boot firmware (`xbl*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `uefi*`, `shrm*`,
   `cpucp*`, `qupfw*`, `tme_*`, `imagefv*`, `keymaster*`, ...), the radio / DSP firmware (`modem*`, `bluetooth*`,
   `dsp*`), the per-device data (`persist`, `cdt`, `ddr`, `dinfo`, `ocdt`, `oplusreserve*`, `nonmodemst*`, ...), the
   security state (`devinfo`, `keystore`, `frp`, `ssd`, `secdata`, `uefivarstore`, ...), Android's system
   (`super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `misc`, ...), `efisp` and every
   partition table. As long as these are untouched the tablet's own boot loader and its fastboot keep working, and
   fastboot can put everything back.
3. **Commands that are never typed** during the install: `fastboot -w`, `fastboot flashall`, `fastboot update`,
   `fastboot set_active`, `fastboot erase ...`, `fastboot format ...`, `fastboot flashing lock`,
   `fastboot flash` with any partition name other than `userdata` and `boot_b`. No third-party flashing tool.
   (`fastboot -w`, `set_active` and the stock boot set are used only by the return-to-stock script, section 8.)
4. **Only files whose SHA-256 was recorded** (section 10) are written, and each is checked again right before its
   write.
5. **The image is rehearsed from RAM first**, through the same chain from U-Boot on, before it is written.
6. **U-Boot stays unable to write the storage.** Fedora gets a rule that makes every other partition read-only.
7. **Nothing is urgent.** If a screen, a message or a number differs from what this guide says: stop, do not
   improvise, do not retry a write. The boot loader is intact in every state this guide can produce, and section 9
   tells what to do.
8. Battery above 60 %, the PC's own USB port that was used in all tests, the same cable, the PC on mains power,
   no sleep on the PC during a write.
9. **Leaving U-Boot always goes to the boot loader, never through another boot:** hold **Volume Down + Power**
   (about 15 s) until the boot loader's fastboot screen shows. Holding Power alone restarts the tablet, and with
   U-Boot in `boot_b` that is another boot of slot b (section 0.5).

### 0.3 What the tablet looks like after each stage

| Stage | Power-on without the PC | With the PC |
|---|---|---|
| Today | LineageOS (slot b) | RAM test kits |
| During C0 (U-Boot in `boot_b`, Android's data intact) | the boot loader's unlocked warning, then U-Boot's text; U-Boot finds no Fedora, waits 10 minutes in its fastboot, then switches the tablet off | U-Boot's fastboot answers as `oneplus-iceland` (read only) |
| After C0's undo | LineageOS with its data, as today | RAM test kits |
| After write 1 (`userdata`) | Android starts and says its data is damaged. **Do not confirm a factory reset.** Keep this stage short | `fastboot boot` of U-Boot starts Fedora |
| After write 2 (`boot_b`) | Fedora | the RAM rescue kit still works |
| After the return to stock | OxygenOS 11.A.38 (slot a; the script sets slot a active) | - |

### 0.4 Decisions that are yours

Answered on 2 Oct:
- Fedora only for now; a dual-boot plan is prepared separately (`wf/install/DUALBOOT-PLAN.md`), nothing of it is
  done.
- The write-2 probe C0 comes first, while Android's data is intact.
- The GPU microcode in the image is Fedora's own (`qcom-firmware`, the upstream linux-firmware set the kits use).

Still open (answer before the step named):
1. (C0) May the install U-Boot carry an AVB hash footer signed with the AOSP test key that `vbmeta_b` already
   chains `boot` with (review R-1)? No other partition changes. C0 cannot run without it.
2. (C0 step 0) May the exact install U-Boot be RAM-booted once before C0, read only (review R-4)? Recommended: it
   shows its storage path on the real tablet before any write.
3. (Part D, after C0) The permanent boot path: `boot_b` if C0 shows the boot loader does not count down slot b's
   tries, else `recovery_b` (Fedora from the recovery path - probably Power + Volume Up, to be confirmed - or as the
   default with one small write to `misc`; section 0.5 and the plan section 5.2). This guide's Part D covers `boot_b` only.
4. Boot path alternative and its key: as 3.
5. Whether an open charging / thermal gate (G6-G8) blocks the install or only sets the rule "charge attended,
   charge limit on".
6. Whether the private camera driver is part of the image on your tablet.
7. The plan's decisions 5-10 (held boot-code updates, release pin, LibreOffice / GNOME Web, skin temperature limit,
   day-0 snapshot, Wi-Fi country): plan section 9.
8. Is a way back to LineageOS needed after the install, or is the return to stock OxygenOS enough (section 8)?

### 0.5 The boot loader's slot counter (new, from Qualcomm's open boot-loader source)

The boot loader keeps three flags per slot: *successful*, *unbootable* and a *retry count*. What its open-source
version does (OnePlus's own build is closed, so C0 measures it on this tablet):
- **Flashing `boot_b` resets slot b**: *successful* becomes `no`, *retry count* the maximum. The same happens when
  `boot_b` is flashed back (the undo).
- **Every normal power-on of a slot that is not *successful* counts down one try.** Entering fastboot with the keys,
  recovery mode (from Android's "restart to recovery", or Power + Volume Up - the key is not yet confirmed on this
  tablet) and the charging screen do not count. Only a flash of a `boot` partition resets the flags; a flash of
  `recovery_b` does not.
- **At zero** the boot loader marks the slot unbootable. If slot a is marked *successful* and not *unbootable*, it
  switches to slot a and restarts (slot a has no Android system since the LineageOS install); otherwise it stops in its
  fastboot. **Part A on 2 Oct read slot a as successful AND unbootable** (slot b: retry count 6): in that state the boot
  loader does not switch, it stops in its fastboot (the review's case A), and the undo works from there.
- **Only Android marks a slot successful** (after a good boot). U-Boot and Fedora do not.

So: during C0, every untethered power-on costs one try, and C0 has a hard stop (step C0.6). After C0's undo,
LineageOS's first boot marks slot b successful again. Whether `boot_b` can be the permanent boot path depends on
what C0 measures (decision 3).

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
found. (This script has been written and dry-run, never executed on this tablet.)

### Step 4 - second copy of the backup and the stock images (G4)

Copy `C:\OnePlusPad4\backups\20260927-1933-unknown` and `C:\OnePlusPad4\stock-11.A.38` to a second disk (about
17 GB + the stock package) and run step 1 against the copy (`-Backup <path on the second disk>`). The backup holds
the calibration and identity of this one tablet; no download replaces it. Do not upload it anywhere.

### Step 5 - save what write 1 would destroy (G5)

With LineageOS running, USB debugging on, and **Developer options > "Rooted debugging" on** (without it `adb root`
is refused; the setting is yours to switch):

```powershell
cd C:\platform-tools
.\adb.exe root
cmd /c 'C:\platform-tools\adb.exe exec-out "tar -C /data -cf - vendor" > C:\OnePlusPad4\backups\data-vendor-20261002.tar'
Get-FileHash C:\OnePlusPad4\backups\data-vendor-20261002.tar -Algorithm SHA256
.\adb.exe unroot
```

This only reads (the `cmd /c` form keeps the archive binary-exact; PowerShell's own `>` would damage it). Write the
hash into section 10. `/data/vendor` holds Android's per-device runtime data (written by the vendor services, not
part of any image); there is no procedure that restores it, the copy exists so that nothing unique is lost. `persist`
needs no file copy: it is in the raw backup (G1) and is never written. Your photos and other personal files on
LineageOS are **not** covered: copy what you want to keep before write 1 (write 1 erases all Android data).

### Step 6 - the read-only pull for write 2 and its undo (G11; review R-1 / R-2 / R-9)

Same day as C0, LineageOS running, "Rooted debugging" on. The PC session copies `parta-read.ps1` into
`C:\platform-tools` first.

```powershell
powershell -ExecutionPolicy Bypass -File C:\platform-tools\parta-read.ps1
```

About 4 minutes; nothing is written (every adb / fastboot call goes through a list of reading commands). It
1. reads the boot state and, with `adb root`, today's slot b images (`boot`, `vbmeta`, `init_boot`, `vendor_boot`,
   `dtbo`, `recovery`, `vbmeta_system`, `vbmeta_vendor`), slot a's boot set and `misc` into
   `C:\OnePlusPad4\backups\parta-<date-time>\`, and saves `boot_b.img` once more as **`boot_b-before-install.img`:
   the undo file of write 2 and of C0** (today's LineageOS `boot_b`, 100663296 bytes - not the backup's);
2. restarts into the boot loader (`adb reboot bootloader`), reads the slot flags of both slots, the lock state and
   `boot_b`'s size (`fastboot getvar`; the serial number is never asked), and restarts into Android;
3. runs the PC check: a second copy in the workflow's private folder (equal by SHA-256), today's `vbmeta_b` (it must
   chain `boot`), `misc`'s boot command (it must not be `boot-recovery` / `boot-fastboot`), **the footered install
   U-Boot made for today's `boot_b`** (`u-boot-iceland-footered.img`: the install build with an AVB hash footer,
   signed with the key `vbmeta_b` chains `boot` with, rollback index and OS version / security patch copied from
   today's `boot_b`), and the PC proof with Android's own verified-boot code on today's images.

Expected last line: **`PARTA: READY FOR C0`**. Anything else: stop; the lines starting with `STOP` say why.
Write into section 10: the date, the SHA-256 of `boot_b-before-install.img` and of `u-boot-iceland-footered.img`
(both in `RECORD-parta.txt`), slot b's and slot a's flags, and the proof's summary line (`AVB-PROOF: PASS`, incl.
`rot-equal`).

### Step 7 - the rescue keys from a cold start (G12)

Switch LineageOS off (power menu > Power off). Then hold **Volume Down + Power** until the boot loader's fastboot
screen shows, connect USB:

```powershell
cd C:\platform-tools
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe reboot
```

Expected: `canoe`, `b`, then LineageOS starts. Both commands only read. This is the door that must work with
anything in `boot_b`.

---

## Part B - the rehearsal from RAM (no write)

Done by the PC session (automated, RAM only, each run under 10 minutes on the tablet). What it must produce:

1. **The image**: the official Fedora-Workstation-Disk-44 aarch64 raw image (checksum-verified), re-laid for the
   tablet's 4096-byte blocks, + our packages (`kernel-iceland`, `iceland-device`, the sensor packages, our libcamera
   build, optionally the private camera module), with the tablet's own firmware copied in by the extractor from the
   tablet's partitions, read only.
2. **Boots of exactly that image from RAM** through the installed chain from U-Boot on: `fastboot boot` of the
   **rehearsal build** of U-Boot (`u-boot-iceland-rehearsal.img`: the install build's code without any storage
   support, so it cannot see the tablet's storage at all), then a "head" with the image's EFI partition and `/boot`;
   U-Boot starts shim and GRUB from it, GRUB starts our kernel, SELinux enforcing; the root comes from the PC over
   the USB network. The tablet's storage is not written.
3. **The acceptance list passed on that boot** (automated, one line `INSTALL-ACCEPT: n PASS, 0 FAIL`): the boot chain
   and the read-only rule, GNOME session, touch, Wi-Fi scan with 5 GHz, Bluetooth, sound, ADSP and CDSP running with
   no failed firmware request, the GPU with its firmware, battery and time estimate, charge limit (80 / 85 %), power
   modes, auto-rotate, suspend and resume, hardware video, both cameras, the default apps start, About shows
   "OnePlus Pad 4", our packages verify clean.
4. **The update rehearsal** (a `dnf upgrade` keeps our kernel and sensor packages; a new kernel is installed next
   to the old one, boots once and becomes the default) and **the rollback rehearsal** (previous kernel from GRUB's
   menu, previous root snapshot, repair from the RAM rescue kit).
5. **The files and their checksums**, written into section 10 (`priv/run/RECORD.txt`, made after the final run R4):
   - `fedora-iceland.sparse.img` (the rehearsed image as a sparse image; its unpacked size equals `userdata`);
   - `u-boot-iceland.img` (the **install** build: it is NOT the one the rehearsal boots. Its own storage path is first
     seen in C0 step 0 and C0, and with Fedora's disk in Part C step 4) and `u-boot-iceland-footered.img` (the same
     with the AVB footer for `boot_b`, made in Part A step 6). The PC refuses to footer or accept the rehearsal build
     for `boot_b`.

Part B is complete when section 10 has these values and the date of the passed acceptance list.

---

## Part C0 - the write-2 probe: U-Boot into `boot_b`, then back (Android's data stays)

Why: the one thing no RAM boot can show is what the boot loader does with a **written** `boot_b` (verified boot,
the slot flags, the retry counter). C0 finds out while LineageOS and its data are still there, and undoes itself
the same day. U-Boot cannot write the storage, and on today's tablet it finds no Fedora (Android's encrypted data is
in `userdata`), so it waits in its fastboot and then switches the tablet off.

**Only when:** Part A steps 1-7 done the same day, `PARTA: READY FOR C0`, your answers to decisions 1 (and 2 for
step 0), battery above 60 %, the PC's own USB port, about 75 minutes of your time. Write the numbers into section 10
as you go.

### C0.0 - (if decision 2 is yes) one RAM boot of the install U-Boot, read only

The PC session runs:

```powershell
powershell -ExecutionPolicy Bypass -File C:\platform-tools\uboot-ram-probe.ps1
```

About 3 minutes, nothing written: the boot loader RAM-boots `u-boot-iceland.img` (the plain install build); its
console shows `scsi scan`, the `userdata` map, no Fedora, then its fastboot; the script saves the console and sends
`fastboot reboot`. Expected: "U-Boot fastboot after N s", the console lines, "Android is back". This proves U-Boot's
own path before the write; C0 then adds only what the boot loader does with `boot_b`.

### C0.1 - check the files

```powershell
cd C:\platform-tools
(Get-FileHash \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img -Algorithm SHA256).Hash
(Get-FileHash C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img -Algorithm SHA256).Hash
```

Both must equal section 10 (from `RECORD-parta.txt`) letter for letter. Otherwise stop.

### C0.2 - into the boot loader by the keys, and read

Switch LineageOS off, hold **Volume Down + Power**, connect USB:

```powershell
.\fastboot.exe getvar product
.\fastboot.exe getvar unlocked
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar partition-size:boot_b
```

Expected: `canoe`, `yes`, `b`, `yes`, `no`, a number (note it as R0), `0x6000000`. Anything else: `.\fastboot.exe
reboot` and stop.

### C0.3 - THE WRITE (the probe)

Type it exactly; the only partition name is `boot_b`, the file is the **footered** one:

```powershell
.\fastboot.exe flash boot_b \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img
```

Expected: "Sending 'boot_b' (98304 KB) OKAY", "Writing 'boot_b' OKAY", "Finished". If it fails: stay in fastboot,
go to C0.7 (the undo) - nothing else.

### C0.4 - the flags right after the write (before any boot; read only)

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
```

Note them (R1). Expected from the open-source boot loader: `b`, `no`, `no`, the maximum (section 0.5; before the
write slot b read 6 on 2 Oct). If
`current-slot` is not `b` or `slot-unbootable:b` is `yes`: go to C0.7.

### C0.5 - the first boot, with the PC

```powershell
.\fastboot.exe reboot
```

Expected on the screen: the boot loader's unlocked warning (orange), then U-Boot's text: the storage scan, no
Fedora, "fastboot" (U-Boot waits). **A red screen or a stop in the boot loader instead: section 9, row "verified-boot
error".** Then, read only:

```powershell
.\fastboot.exe getvar product
cmd /c 'C:\platform-tools\fastboot.exe oem console > C:\OnePlusPad4\backups\parta-<date-time>\c0-uboot-console-1.txt 2>&1'
```

Expected: `oneplus-iceland` (U-Boot's fastboot). Now **hold Volume Down + Power** (about 15 s) until the boot loader's
fastboot screen shows, and read:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar slot-unbootable:b
```

Note R2. R2 = R1 - 1 means this boot loader counts down slot b's tries (section 0.5); R2 = R1 means it does not.

### C0.6 - untethered cold boots (the real case), with a hard stop

Repeat at most **three** times, and **never when `slot-retry-count:b` is 3 or less** (the next boot would leave 2
or less; then go straight to C0.7):

1. Unplug the USB cable. In the boot loader's menu choose "Power off" (volume keys, Power to select).
2. Press Power briefly. Expected: the unlocked warning, U-Boot's text, after about 10 minutes the screen goes dark
   (U-Boot switches the tablet off by itself; note whether it did). If the screen is still lit after 12 minutes:
   note it, hold Volume Down + Power.
3. From off: hold **Volume Down + Power**, connect USB, read `current-slot`, `slot-retry-count:b`,
   `slot-unbootable:b` as in C0.5. Note them.

Stop at once and go to C0.7 when: `current-slot` reads `a`, `slot-unbootable:b` reads `yes`, the count is 3 or
less, the boot loader shows a verified-boot error, or anything differs from this text.

Optional, only if the count is 5 or more: with the tablet off, plug in the wall charger and note what starts (the
boot loader's charging screen, or U-Boot). Charging-screen starts do not count.

### C0.7 - UNDO (always, the same day)

In the boot loader's fastboot (Volume Down + Power, USB connected). Type it exactly:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe reboot
```

Expected: `b`; "Writing 'boot_b' OKAY"; `no` and the maximum (the flash resets the flags again); then LineageOS
starts **with its data** (your PIN / password if set). If `current-slot` read `a` before the flash: still do the
flash (it is slot b's partition), then **stop and ask** before anything else - no `set_active` (section 9).

### C0.8 - after the undo (PC, read only)

When LineageOS is up for 2 minutes, the PC session runs `parta-read.ps1` again. Expected: `boot_b.img` equal to
`boot_b-before-install.img` (the probe left nothing behind), `slot-successful:b: yes` (LineageOS marked it again),
`PARTA: READY FOR C0` (it stays valid as the input of write 2).

**C0 passed** when: the boot loader started U-Boot from `boot_b` at every power-on (orange warning, no verified-boot
stop); U-Boot found no Fedora and waited in its fastboot (console saved); the keys reached the boot loader every
time; the flags are recorded (does the count go down per boot?); the undo brought LineageOS back with its data and
slot b successful. Write the results into section 10; the PC session decides with you about decision 3.

---

## Part C - write 1: the Fedora image into `userdata`

Only when: section 0.1 has no open line for write 1, C0 passed and decision 3 is answered, section 10 is filled in,
battery above 60 %, your files from LineageOS are saved. **Run Part A step 6 again the same day, just before this
part** (it is the last time Android can be read; its `boot_b-before-install.img` must still equal C0's).

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

Expected: `canoe`, `b`, `yes`, and `0x3737D0F000` (237 159 641 088 bytes; it must **equal** the image's unpacked
size noted in section 10: the image is made with exactly this size). Anything else: `.\fastboot.exe reboot` and
stop.

### Step 3 - the write

Type it exactly; the only partition name is `userdata`:

```powershell
.\fastboot.exe flash userdata .\fedora-iceland.sparse.img
```

The PC's fastboot splits the sparse image into pieces of at most 805 MB (the boot loader's `max-download-size`) and
reports each ("Sending sparse 'userdata' 1/N ... OKAY", "Writing 'userdata' ... OKAY"), then "Finished". Do not
touch the cable. This erases all Android data.

If it stops with an error or the cable drops: the boot loader is unaffected. Stay in (or re-enter) fastboot
(Volume Down + Power) and run the same command again from the start. Do not run anything else.

### Step 4 - proof, still tethered

```powershell
.\fastboot.exe boot \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland.img
```

(the plain install build, RAM only; `fastboot boot` never writes). Expected: U-Boot's text, GRUB's menu (3 s), then
Fedora's first-boot setup on the tablet. Go through the setup. The PC session then runs the acceptance list on this
boot and records GRUB's environment before and after a trial boot (U-Boot's write of GRUB's one-time entry into
`userdata`, the one write no rehearsal can show). Switch off and repeat the tethered boot until you have seen **three
cold boots in a row** reach the desktop.

Until Part D the tablet starts Android when it is switched on without the PC; Android reports damaged data and
offers a factory reset: **choose "Try again" or power off, never the reset** (it would erase Fedora; nothing
worse). Keep this stage short; never let Android run between write 1 and write 2 if you can avoid it (Android
writes a "boot-recovery" command into `misc` when it cannot use its data).

Undo of write 1: section 8 (return to stock), or write the image again.

---

## Part D - write 2: U-Boot into `boot_b`

Only after Part C step 4 passed, and only if decision 3 chose `boot_b` (C0 showed that the boot loader does not count
down slot b's tries with U-Boot there). If C0 showed the count going down, this part is replaced by the
`recovery_b` procedure the PC session writes for that decision.

### Step 1 - check the files and the slot

```powershell
cd C:\platform-tools
(Get-FileHash \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img -Algorithm SHA256).Hash
(Get-FileHash C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img -Algorithm SHA256).Hash
```

Both must equal section 10. The PC session confirms in the same minute: `check-header.py` accepts the footered file
as the install build (it refuses the rehearsal build), and Part A step 6's proof on today's images is `AVB-PROOF:
PASS`. Then put the tablet into the boot loader's fastboot: switch it off (hold Volume Down + Power from Fedora's
U-Boot screen, or power off), hold Volume Down + Power, connect USB. `fastboot getvar product` must answer `canoe`
(the tablet's own boot loader; U-Boot's fastboot is never used for a write):

```powershell
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar partition-size:boot_b
```

Expected: `canoe`, `b`, the values written down after C0.8 (successful `yes`), `no`, a number, `0x6000000`.

### Step 2 - the write

Type it exactly; the only partition name is `boot_b`:

```powershell
.\fastboot.exe flash boot_b \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe reboot
```

Read the two flags **before** the reboot (read only) and note them: a change caused by the flash itself is then told
apart from one caused by the boot.

### Step 3 - proof

1. Unplug the PC. Switch the tablet off and on **three times**. Each time Fedora must reach the desktop.
2. Enter the boot loader once more (power off, hold Volume Down + Power, connect USB) and read:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe reboot
```

`current-slot` must be `b`, the retry count the number read right after the flash, `slot-unbootable:b` `no`.
**If the count went down:** undo write 2 now (below); do not boot again first.

Undo of write 2 (two minutes, from the boot loader):

```powershell
.\fastboot.exe flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img
```

(Android then starts with no data; Fedora stays in `userdata` and can be started tethered as in Part C step 4.)

---

## 7. After the install

- **First hour:** Wi-Fi, sound, rotation, a suspend and resume, About shows "OnePlus Pad 4"; Settings > Power
  shows "Battery Charging": choose "Preserve Battery Health" (stops at 85 %; on by default from the device package).
- **Charging:** until the one sitting with your wall chargers is done (the charging row of the feature matrix),
  charge attended and prefer the PC port or a plain 5 V charger. The tablet does not fast-charge (SuperVOOC is not
  supported); the stock temperature and current limits are enforced by the kernel and the battery guard.
- **Updates:** GNOME Software / `dnf upgrade` as on any Fedora. They can only change files inside the Fedora
  partition. Fedora's own kernels are excluded; our kernel and the few special packages come from the tablet's
  local repository, which the PC fills (`iceland-repo-sync`), and a new kernel only becomes the default after it
  has started once. GRUB, shim and the firmware packages (including the GPU microcode) are held until released
  after a rehearsal. Do **not** upgrade to Fedora 45 until that version has passed the RAM rehearsal (the upgrade is
  hidden and blocked by the device package).
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
| During C0 | C0.7 (the undo): LineageOS returns with its data |
| Only undo write 2 | `fastboot flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img` (today's LineageOS `boot_b` from Part A step 6, **not** the 27 Sep backup's) |
| Full return to stock | `C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1` (written and dry-run, never executed; it leaves the tablet on slot a) |
| Factory state with a locked boot loader (optional) | step 4 of the same script (`31-Relock-Bootloader.ps1`), only when its own check says the tablet is exactly stock |
| Back to LineageOS after write 1 | **not written yet**: return to stock, then `22-Flash-LineageOS.ps1` (it assumes stock on slot a; to be reviewed for the post-install state before it is ever used) |

`39-Return-To-Stock.ps1` first verifies the backup and the stock images (read-only) and shows a dry run. After you
type its confirmation it writes the stock boot set to both slots and `super` from your backup, erases `userdata`
and `metadata`, and then proves the result is byte-identical stock. It never writes firmware. If it is
interrupted: enter fastboot again (Volume Down + Power) and run it again.

---

## 9. If something is not as described

| What you see | What it means | What to do |
|---|---|---|
| `fastboot flash userdata` fails or the cable drops | incomplete image in `userdata`; boot loader untouched | re-enter fastboot (Volume Down + Power), run the same command again |
| After write 1, Android says "data may be corrupt" | expected between write 1 and write 2 | "Try again" or power off; never "Factory data reset" |
| Tethered boot after write 1 does not reach Fedora | image or chain problem | do not do write 2; RAM-boot the test kit for a look; or return to stock |
| The boot loader shows a verified-boot error (instead of its usual unlocked warning) and stops, after C0's write or write 2 | the boot loader refused `boot_b` (review R-1) | Volume Down + Power into the boot loader's fastboot; undo (C0.7 / write 2's undo); write down the slot flags; no `set_active` |
| `getvar current-slot` reads `a` after C0's write or write 2 | the boot loader marked slot b unbootable and switched (slot counter at zero, or a refused `boot_b`); not expected while slot a is marked unbootable (Part A, 2 Oct) - then it stops in its fastboot instead | write nothing else; undo `boot_b`; then ask the PC session before the one-time `set_active b` or the full return to stock |
| The retry count went down after a boot with U-Boot in `boot_b` | the boot loader counts tries for a slot nobody marks good (section 0.5) | C0: continue only while the count stays above 3, then undo. Write 2: undo at once; decision 3 (`recovery_b`) |
| After C0's write or write 2: U-Boot text, then nothing more, the screen stays on (no PC) | U-Boot found no Fedora and waits in its fastboot; it switches the tablet off after 10 minutes without a PC command | wait, or hold Volume Down + Power for the boot loader. With the PC: `fastboot devices` shows U-Boot; `fastboot oem console` (read only) saves its log |
| U-Boot's screen is still lit after 12 minutes | U-Boot's own power-off did not work on this board | hold Volume Down + Power (the boot loader); tell the PC session (review R-6) |
| A black screen with a `grub>` prompt or a GRUB error | GRUB found no configuration (damaged `/boot`) | hold Volume Down + Power; RAM-boot the rescue kit (level L3) and repair `/boot` |
| After write 2 the tablet shows **LineageOS recovery** ("Can't load Android system") instead of Fedora | `misc` still holds a "boot-recovery" command from an Android boot between the writes that was cut off | in that recovery choose **Reboot system now** (it clears the command), never "Factory data reset" |
| The tablet was switched off and plugged into a charger, and it starts U-Boot / Fedora | the boot loader starts the boot partition in charger mode; with U-Boot there that is Fedora (plan 11.1.6) | expected; no action (charging-screen starts do not count down the slot) |
| After write 2 the tablet starts Android again by itself | the boot loader fell back to another slot | enter fastboot, read the slot flags (Part D step 3), no `set_active`; undo write 2 and ask |
| Fastboot does not appear with Volume Down + Power | cable / driver, or the tablet is still on | hold Volume Down + Power about 15 s, try again, try the other end of the cable; the boot loader was not written by anything in this guide |
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
| Part A step 6: folder `parta-<date-time>`, last line `PARTA: READY FOR C0` | | |
| `boot_b-before-install.img` SHA-256 (size 100663296; `RECORD-parta.txt`) | | |
| `u-boot-iceland-footered.img` SHA-256 (made for today's `boot_b`; `RECORD-parta.txt`) | | |
| AVB proof on today's images (`AVB-PROOF: PASS`, `rot-equal`) | | |
| Slot b flags: current-slot / successful / unbootable / retry-count | | |
| Slot a flags: successful / unbootable / retry-count | | |
| G12: Volume Down + Power from cold reaches the boot loader | | |
| C0.0 RAM probe of the install U-Boot (console saved, Android back) | | |
| C0: R0 / R1 (after the write) / R2 and each cold boot's retry count; did U-Boot switch off by itself | | |
| C0 undo: `boot_b` equal to the saved file, slot b successful again | | |
| Acceptance list passed on the rehearsal boot (Part B, `priv/run/RECORD.txt`) | | |
| Update and rollback rehearsal passed | | |
| `fedora-iceland.sparse.img` SHA-256, unpacked size (= 237159641088) | | |
| `u-boot-iceland.img` SHA-256 (the plain install build, Part C step 4) | | |
| Decisions 0.4 | | |
| Write 1 done, three tethered cold boots, GRUB environment before / after | | |
| Write 2 done (flags right after the flash), three untethered cold boots, retry count unchanged | | |

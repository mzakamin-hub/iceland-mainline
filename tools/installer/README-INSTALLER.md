# Install-Pad4Linux.ps1 - Fedora 44 on the OnePlus Pad 4 (iceland), the owner's procedure for other users

Written 15 Oct 2026. PowerShell 7 and Windows PowerShell 5.1. One script, `Install-Pad4Linux.ps1`, driven by a
release manifest (`release-manifest.json`, template: `release-manifest.template.json`).

**Status: BLOCKED for flashing.** No generic install image exists yet. The owner's image (B149) carries the owner's
own tablet data and must never be written to another tablet (section 2). With the template manifest the script
refuses write 1 and write 2. Downloads of placeholder files are refused too. The read-only backup works today.

---

## 1. What the script does (and where each step comes from)

| Phase | What | Source of the procedure |
|---|---|---|
| `Preflight` | PowerShell version, `adb.exe` / `fastboot.exe` (Google platform-tools), manifest check and its blockers, free disk space | `00-Preflight.ps1` (owner's kit), INSTALL-GUIDE 0.2 rule 8 |
| `Download` | every manifest file: URL + size + SHA-256, resumable (HTTP Range), verified after download. Multi-part files (GitHub limits each asset to 2 GiB) are joined, then checked against the whole file's SHA-256 | new; the hash-before-use rule is INSTALL-GUIDE 0.2 rule 4 |
| `Backup` (read only) | in Android (LineageOS, slot b, "Rooted debugging" on): identity `OPD2514` / `OP657AL1`, unlocked state, slot `_b`, battery >= 60 %, `adb root`; then `boot_b`, `vbmeta_b`, `init_boot_b`, `vendor_boot_b`, `dtbo_b`, `recovery_b`, `vbmeta_system_b`, `vbmeta_vendor_b`, `boot_a`, `vbmeta_a`, `init_boot_a`, `vendor_boot_a`, `dtbo_a`, `misc` by `adb pull /dev/block/by-name/<p>` (fallback `adb exec-out dd`), each checked by `sha256sum` on the tablet and SHA-256 on the PC (3 tries). `boot_b` is copied to `boot_b-before-install.img` = the undo file of write 2. PC checks: `misc` boot command, `vbmeta_b` chains `boot` with the AOSP test key, `boot_b`'s AVB footer and boot header. Then `adb reboot bootloader` and `fastboot getvar` of the slot flags, the lock state, `partition-size:boot_b` / `userdata`. `-FullBackup` adds every partition except `userdata` (~17 GB) | `parta-read.ps1` + `parta-check.sh` (INSTALL-GUIDE Part A step 6), `02-Backup-AllPartitions.ps1` (G1) |
| `Flash` | gates (release cleared, today's backup, file hashes, sparse size = `userdata`, U-Boot install build, header and footer match this tablet), ABL checks, **write 1** `fastboot flash userdata <image>`, three tethered cold boots `fastboot boot <plain U-Boot>` (RAM only), **write 2** `fastboot flash boot_b <footered U-Boot>`, flags right after the flash, `fastboot reboot` | INSTALL-GUIDE Parts C and D; the owner's run of 13 Oct 2026 (WORKLOG 18:24-20:48) and the v4 write of 14 Oct |
| `VerifySlot` | reads the slot flags in ABL after Fedora's first boots; stop rule (retry count <= 3, slot a, or unbootable: undo now) | INSTALL-GUIDE Part D step 3, C0.6 |
| `UndoBootB` | `fastboot flash boot_b <backup>\boot_b-before-install.img` | INSTALL-GUIDE section 8 ("Only undo write 2") |
| `Inspect -File x` | prints boot header, U-Boot build kind, AVB footer / vbmeta, sparse size of a local file (PC only) | `check-header.py`, `avbtool info_image` (ported) |
| `All` (default) | Preflight, Download, Backup, Flash in one run | - |

**Dry run is the default.** Without `-Execute` nothing is downloaded and adb / fastboot are never started; every
command is printed. Every run writes a log to `<WorkDir>\logs\` (default `WorkDir` = `%USERPROFILE%\Pad4Linux`).

### Each write

Before write 1 the script shows partition `userdata`, the file, its size, unpacked size and SHA-256, then asks you
to type `I understand my Android data is erased` and then `userdata`. Before write 2 it shows `boot_b`, the file,
size, SHA-256 and the undo file, and asks you to type `boot_b`. The image is hashed again right before write 1.

### Never

Only `userdata` and `boot_b` are written, nothing else, ever. The script never sends `fastboot -w`, `erase`,
`format`, `set_active`, `flashall`, `update`, `flashing lock` / `unlock`, `oem ...`, `reboot fastboot`,
`getvar all` / `serialno`. adb is used only to read (`getprop` of a fixed list, `blockdev --getsize64`,
`sha256sum`, `pull` / `dd` of named partitions other than `userdata`). Every adb / fastboot call goes through a
whitelist; anything else is refused before it is sent (tested, section 9). The owner's procedure used none of the
refused commands (INSTALL-GUIDE 0.2 rule 3); `set_active` and `-w` exist only in the owner's return-to-stock script.

---

## 2. Artifacts: what must be published, and what may not be

| Artifact | SHA-256 | Publishable as-is? | Where |
|---|---|---|---|
| Install image B149 `fedora-iceland.sparse.img` (6,732,251,564 B) | `2246e9a7...482c` | **NO** | never |
| U-Boot v4 install build `u-boot-iceland-v4.img` (544,768 B) | `23ff0be6...2c84` | yes | to publish (e.g. iceland-u-boot release `v4`) |
| U-Boot v4 footered `u-boot-iceland-v4-footered.img` (100,663,296 B) | `b714356a...9af6` | yes, but it fits only some tablets (below) | to publish next to it |
| `avbtool.py` (AOSP external/avb `c5066a96`) | `56986567...3782` | not ours to publish: fetched from android.googlesource.com, pinned | Google |
| `testkey_rsa4096.pem` (AOSP public test key) | `6a224754...4121` | same | Google |
| Google platform-tools | - | user downloads from Google (the manifest can pin a versioned dl.google.com zip + SHA-256) | Google |
| A generic install image | - | to be built (below) | to publish in parts of < 2 GiB |

### Why B149 cannot be published

How it was built (`wf/b149/recipe/tablet-b149.sh` build1a, run on the owner's tablet): `iceland-fw-extract` copies
the tablet's own firmware into `/usr/lib/firmware/updates`, the sensor hub tree into
`/usr/share/qcom/kaanapali/OnePlus/iceland` - including `sensors/registry` **from the owner's `persist` partition**
(`fw-list.tsv`: `dsp:sensors/registry persist ext4 /sensors/registry/registry`), i.e. the sensor calibration - and
an extraction record `.iceland-extracted`; then `install -m 600 $IN/bdaddr /etc/iceland/bdaddr` writes **the
owner's Bluetooth address** (from the private `build/.bdaddr`). INSTALL-GUIDE 0.1 records it: "Private by design (as
every install image): the tablet's own firmware extraction and its Bluetooth address". Both are on the never-publish
list of CLAUDE.md (calibration, BD address). The rest of the offline check is clean (no user, no Wi-Fi networks, no
SSH keys, empty machine-id, no journal, no random seed, owner-SSID guard 0), but that does not make it generic. It
also ships iceland-device 0.28-7, whose slot marking does not work on the installed system (section 7).

### Why U-Boot v4 can be published

Checked on the PC: neither image contains the serial number or the Bluetooth address (byte search, 0 hits, also
without colons). The plain image is built from the public iceland-u-boot tree (U-Boot `e0300255` + queue
0004-0012; `uboot.pin` in iceland-u-boot 382c39f), GPL source available. The footer is an AVB hash footer signed
with the **public AOSP test key** (key sha1 `2597c218...`, the key LineageOS's `vbmeta_b` chains `boot` with), with
rollback index `1788220800`, `os_version 17`, `security_patch 2026-09-01` copied from the owner's LineageOS
`boot_b` - values of that LineageOS build, not of the unit. Caveat: the footered file is correct only for a tablet
whose `boot_b` footer has exactly those three values and the same key. The script compares (pure PowerShell AVB
parser) and, if they differ, makes the footer locally with the owner's `mk-footer.sh` parameters
(`avbtool add_hash_footer --partition_name boot --partition_size 100663296 --algorithm SHA256_RSA4096 --key
testkey_rsa4096.pem --rollback_index <yours> --salt <sha256 of the plain U-Boot> --prop
com.android.build.boot.os_version:<yours> --prop com.android.build.boot.security_patch:<yours> --prop
iceland.image:u-boot-iceland`), then verifies the result (size, inner image = plain U-Boot, hash descriptor, key,
values). That path needs Python 3 and `openssl.exe` (Git for Windows ships one); it is **not tested on Windows**.
The script also refuses when your `boot_b`'s boot header (version / OS version / patch level) differs from the
U-Boot's (the owner's `check-header.py` rule: such a tablet needs a U-Boot built with its values).

### What a generic release image needs (before `flash_allowed` may be set)

1. Built **without** the unit data: no `/etc/iceland/bdaddr`, no `sensors/registry` from a `persist`, no
   `.iceland-extracted` record of the owner's unit, nothing else from `iceland-fw-extract` that is unit-specific.
   Generic firmware only through the public `iceland-firmware` package (already in B149, 11.A.38-3).
2. A first-boot (or install-time) extraction on the user's own tablet, read only: the sensor registry from that
   tablet's `persist`, the Bluetooth address (the owner's came from Android's `persist.vendor.service.bdroid.bdaddr`;
   it is not in `persist/bluetooth`). Neither exists as a package step today - new work, with a rehearsal. Until
   then the image needs a defined fallback (Bluetooth with the firmware's default address, sensors without
   calibration) and the release notes must say so.
3. iceland-device **0.28-9 or newer** (the slot-mark fix for the loop root on `userdata`; B149 has 0.28-7), plus
   the owner's later fixes (q89h kernel, 0.28-14).
4. The existing offline checks (no user, no Wi-Fi, no keys, empty machine-id, no random seed, owner-SSID guard),
   **plus** new guards: no `/etc/iceland/bdaddr`, no registry, no extraction record, a byte search for the owner's
   serial and BD address over the whole raw image.
5. Size: B149 is made for exactly `userdata` = 237,159,641,088 B (the owner's storage). Other storage sizes need
   their own image (the script refuses on `partition-size:userdata` mismatch) or a growable image (repart already
   grows the root) - which needs a rehearsal.
6. A full RAM rehearsal of the generic image (the owner's rule: rehearse before writing), then manifest entries with
   `generic: true`, `contains_unit_data: false`, `slot_mark_automatic: true`, real URLs, sizes and SHA-256 per part.
7. Naming: a modified Fedora image should be called a "Fedora Remix" (Fedora trademark guidelines); kernel, U-Boot
   and device-package sources are public; the firmware is the public `iceland-firmware` package.

---

## 3. Who can use it (the owner's starting point; anything else is unproven)

- OnePlus Pad 4, model **OPD2514** (`OP657AL1`), with `userdata` = `0x3737D0F000` (the owner's storage size).
- Boot loader **already unlocked** by you. The script never unlocks (that erases the tablet and is your decision).
- **LineageOS (test-keys, userdebug) running on slot b**, marked successful. Developer options: USB debugging and
  **Rooted debugging** on. This is the owner's state before the install; `vbmeta_b` must chain `boot` with the AOSP
  test key, otherwise write 2 is refused (a plain U-Boot gives INVALID_METADATA and ABL stops; the footered one is
  verified like LineageOS's own boot).
- Battery above 60 %, the PC's own USB port and cable, PC on mains power, no sleep.
- Google platform-tools (https://developer.android.com/tools/releases/platform-tools), e.g. in `C:\platform-tools`.
- Free disk: about 2.5x the image size + 1 GB (+ 18 GB with `-FullBackup`).
- Your own files copied off LineageOS. **Write 1 erases all Android data. It cannot be backed up by this script:
  Android's data is file-based encrypted with keys in the tablet's secure hardware; a raw copy is useless.**

## 4. Use

```powershell
# 0. the manifest of the release (from its release page; compare its SHA-256 with the page)
# 1. dry run of everything (default): prints every command, touches nothing
powershell -ExecutionPolicy Bypass -File .\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json
# 2. step by step, for real
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Preflight -Execute
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Download  -Execute
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Backup    -Execute   # same day as Flash
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase Flash     -Execute
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase VerifySlot -Execute  # after the slot mark
# undo of write 2
.\Install-Pad4Linux.ps1 -Manifest .\release-manifest.json -Phase UndoBootB -Execute [-BackupDir <folder>]
```

Options: `-WorkDir`, `-PlatformTools <folder>`, `-BackupDir <folder>`, `-FullBackup`, `-Python <python.exe>`,
`-MinBatteryPercent`, `-MinBatteryMv` (ABL `battery-voltage`, default 3800).

## 5. Backups (private, never leave the PC)

`<WorkDir>\backups\backup-<time>\`: the images (read-only files), `SHA256SUMS.txt`, `backup-manifest.json` (facts,
slot flags, AVB analysis, sizes, tablet and PC SHA-256), `PRIVATE-README.txt`. Never upload them. Copy the folder to
a second disk. `Flash` requires a backup from **today** (Part A step 6 "the last time Android can be read") with no
failed checks and re-hashes the undo file.

## 6. The flash, as the owner did it

1. ABL fastboot (switch off, hold **Volume Down + Power**, connect USB): `product` = `canoe` (U-Boot's own
   fastboot `oneplus-iceland` is refused), not fastbootd, unlocked, `current-slot` = `b`, battery, sizes,
   slot b successful / not unbootable.
2. Write 1 (`userdata`, the owner's took 267 s, 9 sparse pieces). On failure: re-enter fastboot and run the same
   phase again; nothing else.
3. Three tethered cold boots: `fastboot boot u-boot-iceland-v4.img` (RAM) -> GRUB -> Fedora's first-boot setup
   (create your user). Between writes, if Android starts and offers a factory reset: **Try again or power off,
   never the reset**.
4. Write 2 (`boot_b`), flags read before the reboot (owner: successful no, unbootable no, retry 7, current b).
5. `fastboot reboot`: the v4 menu (5 s, default Fedora) then Fedora.

## 7. Right after the install: mark the slot (important with B149-era packages)

ABL counts down a try at every normal power-on of slot b until the slot is marked successful. On the owner's
tablet the packaged marker (`iceland-slot-mark`, 0.28-7) did **not** run on the installed system (it skipped the
loop root on `userdata`; the boot LUN is read-only): 4 boots took the count from 7 to 3. At 0 ABL marks slot b
unbootable and, with slot a unbootable, stops in fastboot. Fixed in iceland-device 0.28-8/0.28-9. With an image
whose manifest says `slot_mark_automatic: false`, at the **first** Fedora boot run the owner's manual mark of
14 Oct 2026 in a terminal:

```sh
B=$(readlink -f /dev/disk/by-partlabel/boot_b); L=/dev/$(lsblk -no PKNAME "$B")
sudo dd if="$L" of=$HOME/boot-lun-gpt-head.bin bs=4096 count=6   # a read: copy of that LUN's partition table
sudo blockdev --setrw "$L"; sudo qbootctl -m; sudo blockdev --setro "$L"; sudo qbootctl
```

(`qbootctl` must show slot b Active 1 / Successful 1 / Bootable 1.) Then `-Phase VerifySlot -Execute`. If it says
UNDO NOW: `-Phase UndoBootB -Execute`, no further boot, no `set_active`. A tethered `fastboot boot` of the plain
U-Boot costs no try.

## 8. Undo and return to stock

| From | Undo |
|---|---|
| After write 1 only | run write 1 again, or return to stock |
| After write 2 | `-Phase UndoBootB`: the saved `boot_b` back (two minutes; Fedora stays in `userdata`; Android then starts without data) |
| Full return to stock | **not automated here.** It needs your own full backup (`-FullBackup`, taken before write 1) and the stock OxygenOS images; the owner's `30-Restore-Stock.ps1` / `39-Return-To-Stock.ps1` write the stock boot set to both slots, `super`, `set_active a` and `-w` - written and dry-run, **never executed** even by the owner |
| Rescue | the RAM test kit by `fastboot boot` (needs no storage) |

## 9. If something differs

Stop. Write nothing more. Leave U-Boot only with Volume Down + Power (about 15 s) into the boot loader.

| What you see | What to do |
|---|---|
| `fastboot flash userdata` fails / cable drops | re-enter fastboot, run `-Phase Flash` again |
| Android says data may be corrupt (between the writes) | Try again or power off; never factory reset |
| Tethered boot does not reach Fedora | no write 2; return to stock or rescue kit |
| Verified-boot error instead of the orange warning after write 2 | Volume Down + Power, `-Phase UndoBootB` |
| `current-slot` reads `a` after write 2 | write nothing else; `-Phase UndoBootB`; ask for help before any `set_active` |
| LineageOS recovery "Can't load Android system" after write 2 | "Reboot system now" (clears `misc`), never factory reset |
| Anything not in this table | stop and ask, with the exact text on the screen |

## 10. How the script was checked (15 Oct 2026, PC only, no device)

- Parse check with `[System.Management.Automation.Language.Parser]::ParseFile`: 0 errors in PowerShell 7.6.6 and
  Windows PowerShell 5.1.26100.
- `-DryRun` of `All`, `Flash`, `VerifySlot`, `UndoBootB` with a FAKE manifest (`test_only: true`, fake 4 KiB sparse
  header, the real U-Boot v4 files, a fake backup holding the owner's 13 Oct `boot_b` copy): every command printed,
  the release gate printed BLOCKED, exit 0, in both PowerShell versions. Footer path "match" (the release footered
  U-Boot accepted: rollback, os, patch, key, hash descriptor) and "mismatch" (local avbtool command printed).
- The template manifest: Preflight lists every blocker; Download refuses every placeholder URL.
- Whitelist: 28 commands sent through the real `Invoke-Fb` / `Invoke-AdbCmd` (extracted from the script):
  `erase`, `format`, `-w`, `set_active`, `flashing lock/unlock`, `flashall`, `update`, `getvar all/serialno`,
  `oem`, `reboot fastboot`, `flash boot_a`/`vbmeta_b` (even armed), unarmed `flash userdata`, `boot <other file>`,
  adb writes, `pull userdata`, the BD-address property: all refused; armed `flash userdata` / `boot_b`, `boot` of
  the plain U-Boot, read commands: passed.
- `-Phase Inspect` on the owner's real files reproduces avbtool's values (rollback index, key sha1, chain
  descriptors, props) and validates the hash descriptors; the U-Boot build kind (install / rehearsal) matches
  `check-header.py`.
- **Not tested:** any live run (`-Execute`) against a tablet, the HTTP download / resume, the local avbtool footer
  on Windows.

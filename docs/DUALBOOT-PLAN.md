# OnePlus Pad 4: a plan for Fedora next to LineageOS (dual boot) - PLAN ONLY

> **For the owner, in five lines.**
> - What you get: LineageOS stays the default at power-on; Fedora starts from the recovery path ("Restart to
>   recovery" in LineageOS, `adb reboot recovery`, probably Power + Volume Up).
> - What it costs: Android's data once (backed up by you first); one partition-table write on the storage unit that also
>   holds the per-device data; U-Boot written again after every LineageOS update.
> - What is proven so far: nothing on the tablet. The first step would be the probe DB-P1 (U-Boot in `recovery_b`,
>   undone the same day).
> - **The decision has a deadline: before write 1 of the Fedora-only install** (that write fills `userdata`; a dual
>   boot afterwards means re-making Fedora's disk).

Install workflow, round 7 (2 Oct 2026). **Nothing in this file has been done, and nothing here runs without the
owner's explicit decision for each step.** The owner's order of 2 Oct: "no dual boot for now but prepare a plan for
it with the best safety precautions". The install stays Fedora-only (`docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md`)
until the owner chooses otherwise. For review by the documentation workflow (`07-INSTALL-REVIEW.md` R-5).

Sources: `docs/PLAN.md` v4 Phase 4-DB; `docs/guide/02-HARDWARE.md` section 6 (partitions), `03-BOOT-AND-PARTITIONS.md`
(chain, A/B, AVB, levels); the review; Qualcomm's open ABL (CodeLinaro edk2 `uefi.lnx.5.0.r53-rel`,
`QcomModulePkg`, read in `wf/install/work/abl`); LineageOS's device tree for this tablet
(`device/oneplus/sm8850-common/BoardConfigCommon.mk`, `vendor/etc/fstab.qcom` of the build); this workflow's tools.
OnePlus's own ABL is closed: every statement about "ABL" below is the open-source behaviour, to be confirmed on the
tablet by the probes named.

## 1. The facts that decide the design

| # | Fact | Source | Consequence |
|---|---|---|---|
| D1 | `userdata` is f2fs with file-based encryption v2 **and** metadata encryption, both with **hardware-wrapped keys** (`fileencryption=aes-256-xts:aes-256-cts:v2+inlinecrypt_optimized+wrappedkey_v0`, `metadata_encryption=aes-256-xts:wrappedkey_v0`, `keydirectory=/metadata/vold/metadata_encryption`), `checkpoint=fs` | LineageOS `fstab.qcom` | every block of `userdata` on the storage is ciphertext; the keys exist only inside the TEE / the storage's inline crypto engine, unwrapped for Android's own session after ABL's root of trust. Fedora can neither read Android's data nor a file Android keeps for it through the file system |
| D2 | `userdata` is the last partition of LUN 0 (sda, ~253 GB); LUN 0 also holds `ssd`, `persist`, `misc`, `keystore`, `frp`, `vbmeta_system/_vendor`, `metadata`, `rawdump`, `splash_odm`, `hybridswap`, `super` (all far too small for Fedora, or in use) | 02-HARDWARE section 6 | space for Fedora can only come from `userdata`; any partition-table change touches the LUN that holds the per-device data |
| D3 | No other LUN has room (sdb / sdc 8 MiB, sdd 12 MiB, sde ~2 GB of firmware, sdf ~461 MB of OnePlus data); the LUN layout itself is UFS device configuration | 02-HARDWARE | another LUN is not an option; re-provisioning LUNs is a device-configuration write with brick risk |
| D4 | Android must be started by ABL itself: ABL hands Android's TEE the root of trust (verified-boot key, lock state, boot state, OS version, patch level) that unlocks its keys | 03-BOOT section 3; review | U-Boot can never start Android; Android keeps `boot_<slot>`; Fedora's U-Boot needs a partition ABL starts on another path |
| D5 | ABL starts `recovery_<slot>` for `adb reboot recovery`, LineageOS's "Restart to recovery", `fastboot reboot recovery` (seen on this tablet on 28 Sep) and when `misc` holds the boot command `boot-recovery`; **Power + Volume Up** is the open ABL's key and the 03 guide's statement, but has never been seen on this tablet (to be confirmed in DB-P1) | ABL `LinuxLoader.c` / `Recovery.c` 380-389; `pad4-hardware-boot-partitions.md` section 3 | `recovery_<slot>` is a second boot path, chosen from Android or (probably) by keys, that leaves Android's normal boot untouched |
| D6 | Recovery, fastboot and charging-screen boots do **not** count down a slot's retry counter; normal boots of a slot not marked *successful* do; **only a flash (or erase) of a partition whose name starts with `boot`** resets the slot's flags (`FastbootCmds.c` 1160-1164 and 2138-2140: `StrnCmp (PartitionName, L"boot", 4)` before `FastbootUpdateAttr`), so a flash of `recovery_b` leaves slot b's flags as they are | ABL `IsABRetryCountUpdateRequired`, `FindBootableSlot`, `FastbootUpdateAttr` (OnePlus's closed build: DB-P1 reads the flags before and after) | U-Boot in `recovery_<slot>` never wears down a slot; U-Boot in `boot_b` does (Fedora never marks the slot successful) - see the Fedora-only plan's C0 |
| D7 | `recovery` is an A/B partition, part of every OTA (`AB_OTA_PARTITIONS`), 100 MiB (104857600), verified like `boot` (AVB, `testkey_rsa4096`, rollback index location 1, `avb=vbmeta`) | `BoardConfigCommon.mk`, `fstab.qcom` | U-Boot written there needs an AVB footer made for that partition (the R-1 fix of the Fedora-only plan, for `recovery`); every LineageOS OTA replaces the new slot's recovery with LineageOS's |
| D8 | An OTA installs into the inactive slot and flips the active slot (b -> a -> b ...) | A/B design; `03-BOOT` section 2 | after each LineageOS update, Fedora is reachable only after U-Boot is written into the new slot's `recovery` |
| D9 | The install U-Boot already prefers a GPT partition named `fedora` over `userdata` (`fedora_blkmap`), and the initramfs carrier prefers the label `fedora` | U-Boot patch 0006; `cand/iceland-device/files/dracut/90iceland/iceland-carrier`; unit-tested | a separate partition needs no change in U-Boot or the initramfs; the read-only rule needs one (section 6) |
| D10 | Android's "Erase all data" and its rescue path write `boot-recovery` (+ a wipe command) into `misc` and restart into recovery | AOSP recovery / RescueParty | with U-Boot in recovery, these Android requests land in Fedora's U-Boot instead (failure mode F7) |

## 2. The options

### 2.1 Where Fedora's disk lives

| Option | What is written, where | For | Against | Verdict |
|---|---|---|---|---|
| **(a) An image file inside Android's `userdata`** ("loop device") | Android (root) creates a pinned, fully allocated file (as Android's own Dynamic System Updates do); its physical extents are read with FIEMAP; U-Boot (`blkmap map ... linear`, one per extent) and the initramfs (`dm-linear`) map the **raw** blocks of `userdata`; the image is written raw into those extents | no partition-table write; Android's data stays | a plain loop device over the file is impossible (D1: Fedora cannot mount `userdata`). The raw-extent map bypasses Android's inline encryption: Fedora's data sits unencrypted on the storage, and **one wrong extent means Fedora writes over Android's encrypted file-system blocks** - silent, total loss of Android's data. Fedora must keep `userdata` writable (no read-only seat belt). f2fs pinning and checkpointing (`checkpoint=fs`) are Android internals that may change with any update; an Android factory reset or "Erase all data" deletes Fedora; new, complex tooling that the PC cannot rehearse against the real file system | **not recommended**; research only |
| **(b) A separate partition `fedora` carved from `userdata`** | LUN 0's GPT once (`userdata` shortened at its end, `fedora` appended; optionally a small `shared` exFAT); `userdata` + `metadata` formatted once by ABL (`fastboot -w`); the image into `fedora` | clean isolation (Fedora never needs `userdata` writable); U-Boot and the initramfs support it already (D9); the image is the Fedora-only image re-sized; Android re-encrypts itself on its first boot | one partition-table write on the LUN that holds `persist` / `keystore` / `frp` / `metadata` (a new write type, the most delicate write in the project); Android's data is lost once (backed up first) | **recommended** |
| (c) Another LUN | a LUN re-provisioning (UFS configuration descriptors) | - | D3: no room; re-provisioning is a device-configuration write with brick risk | rejected |
| (d) External USB-C storage | `recovery_<slot>` only | no internal data write at all | U-Boot's USB host and OTG power are untested on this tablet (the OnePlus 15 needed external PD for OTG); a cable pulled while Fedora runs | research, not a plan |

### 2.2 How each system is chosen at power-on

| Option | How | Verdict |
|---|---|---|
| **(d1) U-Boot in `recovery_<active slot>`** | normal power-on -> ABL -> `boot_<slot>` -> LineageOS (unchanged: same images, same root of trust). Power + Volume Up, `adb reboot recovery` or LineageOS's "Restart to recovery" -> ABL -> U-Boot -> Fedora. Fedora's `reboot` -> LineageOS. Recovery boots never count down the slot (D6) | **recommended** (Android stays the default) |
| (d1') as (d1) + `misc` boot command `boot-recovery` | every power-on starts Fedora (ABL honours the command, nothing clears it); Android only after the command is cleared (from Fedora, a write to `misc`) | only if Fedora must be the default; one more write type; Android's own `misc` use (F7) interferes |
| (d2) U-Boot in `boot_<slot>` and U-Boot starts Android | - | impossible (D4) |
| (d3) Android on one slot, U-Boot as the other slot's `boot` | switching needs `fastboot set_active`; OTAs overwrite the other slot; the retry counter decides by itself | rejected |
| (d3') U-Boot in `boot_a` (the inactive slot) - asked by the owner | the flash resets only slot a's flags (clears *unbootable*, which Part A of 2 Oct read as set); slot a stays dormant: ABL never boots it unless `fastboot set_active a` makes it active (it also switches the UFS boot LUN to slot a's boot firmware, identical 11.A.38 since `copy-partitions`). Then every Fedora power-on counts slot a down (nobody marks it successful); at zero ABL marks slot a unbootable and returns to slot b's LineageOS (successful) by itself. Every LineageOS OTA writes slot a and replaces U-Boot | not a dual boot (Fedora expires after a few power-ons, each return to Fedora needs `set_active` from the PC, which the plan forbids outside the return to stock); as a probe it shows nothing a `fastboot boot` does not, unless `set_active` is used. Rejected; a probe would be: flash `boot_a`, read slot a's flags, flash `boot_a` back - no boot |
| (d4) A key check patched into Android's kernel | - | rewrites Android's boot image after every update; rejected |

## 3. The recommended design (if the owner chooses dual boot)

**(b) + (d1): a partition `fedora` on LUN 0, U-Boot in `recovery_<active slot>`, LineageOS the default.**

```
power-on ----------------> ABL -> boot_b (LineageOS, untouched) -> Android (its data in userdata, encrypted)
Power + Volume Up -------> ABL -> recovery_b = install U-Boot (+ AVB footer for recovery)
  ("restart to recovery")         scsi scan; GPT name "fedora" -> blkmap (4 KiB) -> EFI boot option -> shim -> GRUB
                                  -> kernel-iceland -> initramfs: carrier = loop over "fedora"; every other UFS
                                     partition read-only, INCLUDING userdata -> Fedora
Fedora "reboot" ----------> ABL -> boot_b -> Android
```

### 3.1 What is written, where, and its undo

| # | Write | Partition | Who / how | Undo | Probe before |
|---|---|---|---|---|---|
| W1 | U-Boot (install build, AVB footer for `recovery`, OS version / patch level equal to LineageOS's recovery) | `recovery_b` | owner, ABL `fastboot flash recovery_b` | `recovery_b-before.img` (pulled read-only the same day, as Part A of the Fedora-only guide) | DB-P1 |
| W2 | the GPT of LUN 0: `userdata` shortened, `fedora` (and optionally `shared`) appended; primary and backup header + entries | LUN 0 partition table | a guarded editor in a RAM-booted Linux kit (section 4.3), with a printed diff and a typed confirmation | the saved table (`lun0-gpt-before.bin`, primary + backup, pulled read-only) written back by the same editor | DB-R2, DB-R3 |
| W3 | format `userdata` and `metadata` at the new size | `userdata`, `metadata` | owner, ABL `fastboot -w` (as in the return to stock) | none needed: Android sets itself up again (its data is restored from the owner's own backup) | Android boots and re-encrypts (DB-P3) |
| W4 | the Fedora image (the rehearsed sparse image, made for the `fedora` partition's size) | `fedora` | owner, ABL `fastboot flash fedora` if ABL accepts the name (read-only check first: `fastboot getvar partition-size:fedora`), else the guarded RAM-kit writer (name-checked, `fedora` only) | write it again, or W2's undo | the RAM rehearsal (section 5) |
| W5 (each OTA) | U-Boot into the new active slot's `recovery` | `recovery_a` / `recovery_b` | owner, after each LineageOS update | that slot's saved recovery image | DB-P1 for that slot |
| optional W6 | `misc` boot command `boot-recovery` (d1') | `misc` (first 32 bytes) | owner | saved `misc` copy | its own probe |

### 3.2 Never written (unchanged from the Fedora-only plan, plus the dual-boot points)

Everything in `INSTALL-PLAN.md` section 2's never-write list stays, with these changes: `recovery_<slot>` is written
(W1 / W5), LUN 0's GPT is written once (W2), `metadata` is formatted once with `userdata` (W3). Still never: `boot_*`
(Android's), `vbmeta*`, `super`, `persist`, `keystore`, `frp`, `misc` (unless W6 is chosen), every other LUN's table,
all firmware, `efisp`, the UFS configuration. **Fedora never writes `userdata`**: the read-only rule keeps it
read-only from the initramfs on (section 6).

### 3.3 Failure modes and what to do

| # | Failure | Effect | Undo / way out |
|---|---|---|---|
| F1 | ABL refuses `recovery_b` (verified-boot error) | Power + Volume Up shows ABL's error or stops; normal power-on still starts Android | Volume Down + Power -> ABL; flash `recovery_b-before.img`. Probe DB-P1 shows it before any data is at stake |
| F2 | U-Boot in `recovery_b` finds no `fedora` / no ESP | U-Boot's fastboot, power-off after 10 minutes | normal power-on starts Android; RAM rescue kit for Fedora |
| F3 | W2 written wrong (the editor's re-read differs from the planned table) | Android may not find `userdata` / `metadata`; ABL and the firmware LUNs are untouched (ABL lives on LUN 4) | the editor writes the saved table back at once (same session); Android then starts with its old data as long as W3 has not run |
| F4 | W2 interrupted (power / cable) | primary and backup headers may disagree | GPT keeps two copies: the editor writes the backup first, then the primary, and verifies; the RAM kit re-runs the editor's "restore saved table" |
| F5 | W3 not done after W2, and Android starts | Android's f2fs is larger than its new partition: fs_mgr cannot mount `/data`; Android's answer is its "prompt and wipe" request to recovery, which with U-Boot not yet in recovery shows LineageOS's recovery (and with U-Boot there would land in F7) | prevented by staying in ABL's fastboot between W2 and W3; if it happened: back to ABL (Volume Down + Power), do W3 (`fastboot -w`); never let Android "repair" by itself |
| F6 | a LineageOS OTA flipped the slot | Power + Volume Up starts LineageOS recovery, not Fedora | W5 for the new slot (after its own pull and proof) |
| F7 | Android requests recovery for itself (Settings > "Erase all data", RescueParty after crashes, an OTA that needs recovery) | ABL starts U-Boot instead; `misc` keeps `boot-recovery` (+ a wipe command), so **every** power-on goes to U-Boot / Fedora, Android seems gone | do not panic: Android's data is untouched. Flash LineageOS's recovery back into `recovery_<slot>` (the saved image) and let it finish its job (or clear `misc` with the saved copy); then W5 again |
| F8 | Fedora writes `userdata` (a bug, a tool) | Android's data destroyed | prevented: `userdata` read-only from the initramfs on, udisks ignores it, the read-only flag re-checked by the acceptance list (`storage` line) |
| F9 | A boot presents a newer OS version / patch level to the TEE than Android's | Android's keys could be upgraded / rollback-protected away from Android's own state (data loss risk) | U-Boot's header and footer carry exactly LineageOS's recovery values (the PC proof's `rot-equal` check, extended to recovery boots) |
| F10 | Return to stock with the modified GPT | the stock script's checks differ; Android's userdata smaller | restore the saved LUN 0 GPT first (W2's undo), then the return to stock (L5) |

## 4. The procedure (each step its own decision; the owner runs every write)

### 4.1 Before anything (read only)

1. The Fedora-only gates G1-G4, G11, G12 (backup, stock images, return-to-stock dry run, second copy, slot flags,
   rescue keys).
2. The owner's own backup of LineageOS's personal data (photos, app data through the apps' own export). Android's
   data is lost once (W3); a raw copy of the encrypted `userdata` is useless anywhere else and only restorable on
   this tablet in the same software state (D1), so it is not the backup.
3. A Part-A-style read-only pull: today's `recovery_b`, `vbmeta_b`, `misc`, LUN 0's partition table (primary and
   backup, as raw blocks), all hashed, two copies.
4. Sizes decided by the owner, e.g. Android `userdata` 96 GB, `fedora` 128 GB, optional `shared` 4 GB (exFAT),
   boundaries aligned to 16 MiB.

### 4.2 The probes (each undone the same day)

| Probe | What | Shows |
|---|---|---|
| DB-P1 | W1 alone: the footered U-Boot into `recovery_b`; the slot flags read right after the flash (expected unchanged, D6); normal power-on x2 (LineageOS must start, slot flags unchanged); "Restart to recovery" x1 and Power + Volume Up x1 (U-Boot, no Fedora, fastboot, power-off - the second confirms the key, D5); then the undo | ABL verifies and starts U-Boot from recovery; recovery boots do not count down the slot; Android unaffected. **This probe also serves the Fedora-only plan's fallback (U-Boot in `recovery_b`)** |
| DB-P2 | (after W2-W3) a RAM boot of the install U-Boot, read only | U-Boot finds the `fedora` partition on the real LUN and maps it (empty) |
| DB-P3 | (after W3) LineageOS's first boot | Android formats / encrypts its smaller `userdata`, marks the slot successful |

### 4.3 The partition-table editor (new tool, PC-proven first)

Guarded like the extractor: refuses unless the LUN's current table is byte-for-byte the saved one; changes only the
`userdata` entry's last block and appends the new entries (same type GUID / attributes for `userdata`, new GUIDs for
the new ones), recomputes the CRCs, writes the backup table first, then the primary, re-reads both through the
kernel (`BLKRRPART`) and compares with the plan; `--restore` writes the saved table back. PC proof (DB-R2): on a sparse
file the size of LUN 0 holding the saved table, the editor's result checked by `sfdisk --dump`, `sgdisk -v` and the
project's own GPT parser; the restore gives the original bytes back. Tablet dry run (DB-R3, RAM kit): the editor
computes the new table from the real LUN and prints the diff, writes nothing.

### 4.4 The order on the day

DB-P1 (probe, undone) -> backups -> W2 (in a RAM kit; the kit then restarts **into ABL's fastboot**, never into
Android: `reboot bootloader` through the PMIC's reboot reason, proven in a RAM kit beforehand, or you hold Volume Down
during the restart) -> **read `fastboot getvar partition-size:userdata` and `partition-size:fedora`: both must equal
the new table** (ABL reads the partition table when it starts; a format sized from a stale table would be wrong; this
read is also W4's check that ABL knows the name `fedora`) -> W3 (ABL) -> DB-P3 (Android set up again, slot successful) ->
DB-P2 (RAM boot of U-Boot, read only) -> W4 (the image) -> tethered RAM boots of the install U-Boot into Fedora
(acceptance list) -> W1 -> three Power + Volume Up boots and three normal boots, flags read after each.

## 5. RAM rehearsals that prove the Fedora side before any write

- **The same rehearsal as the Fedora-only plan** (runs B, R1-R4, U1-U3, R1b, R2b, R3), with the golden disk made for
  the `fedora` partition's size (the builder and the sparse writer take the size; the first-boot growth then fills
  `fedora`, not `userdata`).
- **The carrier and the read-only rule with both partitions present:** unit tests on the PC (the carrier picks
  `fedora`, never `userdata`; the rule keeps `userdata` read-only when `fedora` exists), and after W2-W3 a RAM-kit
  step that evaluates the rule on the real LUNs and lists every writable device (expected: `fedora` and LUN 0 as a
  whole only).
- **The GPT editor** on the PC (DB-R2) and as a dry run on the tablet (DB-R3).
- **U-Boot from recovery**: probe DB-P1 (a write with its undo; no RAM boot can show ABL's handling of `recovery`).

## 6. Changes the dual boot needs in this workflow's tools (not made)

| Piece | Change |
|---|---|
| `59-iceland-storage-ro.rules` / `iceland-storage-ro` | today: every UFS device read-only except `userdata` and its LUN. Dual boot: except the partition the carrier uses (`fedora`) and its LUN; **`userdata` read-only** whenever `fedora` exists |
| `mk-golden.py`, `mk-sparse.py`, `rehearsal-pc.sh` | a size parameter = the `fedora` partition (today: `userdata`'s exact size) |
| `mk-footer.sh`, `avb-proof.sh`, `parta-read.ps1`, `parta-check.sh` | a `recovery` variant: partition `recovery_<slot>`, size 104857600, rollback index location 1, the recovery boot's requested partitions in `avb-check`, and the OS version / patch level ABL hands the TEE on a recovery boot (from the U-Boot header unless the footer has both props) equal to LineageOS's recovery |
| `accept.sh` | `root` / `storage` lines for the `fedora` carrier (userdata must be read-only) |
| the firmware extractor | reads the active slot (today slot a = b): after an OTA the active slot's firmware can differ; a re-extraction from the new slot (read only, stock-hash compare) after each LineageOS update |
| a new GPT editor | section 4.3 |

## 7. Updates of both systems

- **Fedora**: unchanged (its partition only; kernels from our repository with a trial boot; GRUB, shim, firmware held;
  snapshots). Its `reboot` returns to LineageOS; a kernel trial boot that fails falls back on the next Power + Volume
  Up (L0).
- **LineageOS OTA** (the Updater app, A/B; no recovery needed): installs into the other slot (including its
  `recovery`), flips the active slot. Afterwards Power + Volume Up starts LineageOS's recovery (F6) until W5 is done
  for the new slot: a Part-A-style pull of that slot's `recovery` / `vbmeta`, a footer made for it, the PC proof, the
  write. Firmware in the OTA (if any) reaches Fedora by re-extraction (section 6). Anti-rollback stays: never an older
  build.
- **Sideload / factory reset of LineageOS** need LineageOS's recovery: flash its saved image into the active slot's
  `recovery` for that job, then W5 again (F7).
- **Time**: the PMIC RTC; Android keeps its own offset in `/data`; Fedora uses NTP and must not write the RTC (to be
  checked: the RTC node's write permission in our device tree, chrony's `rtcsync`).

## 8. Backups

| What | How | Restores |
|---|---|---|
| The 151-partition raw backup + stock images (G1 / G2, two copies) | existing | the return to stock (L5) |
| LUN 0's partition table before W2 | the read-only pull (4.1.3) | F3 / F4 / F10 |
| `recovery_<slot>` before W1 / W5, `misc` before W6 | the read-only pull | the probes' and the writes' undo |
| LineageOS's personal data | the owner's own export (apps, photos) | Android after W3 |
| Fedora's home folder | `btrfs send` of a read-only snapshot of `/home` to the PC (the Fedora-only plan 11.2) | L4 without losing the home folder |
| The recorded Fedora image | the rehearsal's sparse image and checksum | L4 |

## 9. The restore levels with dual boot (INSTALL-PLAN section 11.2)

| Level | Fedora side | Android side |
|---|---|---|
| L0-L2b | as Fedora-only (trial boot, previous kernel, snapshots, day-0 snapshot), started with Power + Volume Up | - |
| L3 | the RAM rescue kit (`fastboot boot`, needs no partition) | the same kit can read Android's partitions read-only, not its data (D1) |
| L4 | `fastboot flash fedora` with the recorded image (W4 again) | LineageOS's own recovery (flashed back temporarily) for sideload / reset |
| L5 | the saved LUN 0 table back (W2's undo) + `fastboot -w`, then `39-Return-To-Stock.ps1` | the same: stock OxygenOS |

## 10. Recommendation and precautions

1. **Decide before write 1 of the Fedora-only plan** whether dual boot will be wanted: the Fedora-only install fills
   `userdata`; going to dual boot afterwards means W2-W4 with Fedora's image re-made (Fedora's home folder copied
   first).
2. If yes: **(b) + (d1)**, LineageOS the default, Fedora by Power + Volume Up / "restart to recovery". Not (a): no
   partition-table write, but a silent-corruption failure mode against Android's encrypted data, `userdata` writable
   from Fedora, and Android-internal mechanisms that can change with any update.
3. **Probe first, as for the Fedora-only plan:** DB-P1 (U-Boot in `recovery_b`, undone the same day) before anything
   else. It answers the boot-path question for both plans: if the Fedora-only C0 shows ABL counting down `boot_b`,
   `recovery_b` becomes the Fedora-only boot path too.
4. **The partition-table write only with:** the saved table (two copies), the editor proven on the PC (DB-R2) and dry-run
   on the tablet (DB-R3), backup-before-primary writing, an immediate re-read, the restore path tested on the PC, the
   owner's typed confirmation, battery above 60 %, the PC's own port.
5. **Fedora never writes `userdata`**, enforced from the initramfs on and checked by the acceptance list; the TEE never
   sees newer OS values than LineageOS's (F9).
6. Every write keeps the Fedora-only rules: recorded checksums, one owner command per write, "stop, do not improvise".
7. Expected effort before the first dual-boot write: the recovery variants of the footer / proof / pull tools, the GPT
   editor and its PC proof, the read-only rule change with tests, the re-sized rehearsal - all PC work - plus the
   probes DB-P1 (owner present, about 45 minutes) and DB-R3 (RAM kit).

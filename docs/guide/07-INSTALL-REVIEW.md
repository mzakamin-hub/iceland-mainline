# 07 - Independent review of the installation process

Reviewer: the documentation / SME workflow ("docs"), 2 Oct 2026, evening; status updated about 22:30 (section 0). PC-only review: nothing was run on the
tablet, nothing was built, no file outside `~/mainline/build/wf/docs/` was changed.

**Status of the install on the day of this review:** nothing has been written to the tablet. The PC-side tooling is
built and checked. The rehearsal's build run passed twice: B run `area-combo-93` on kernel q78 (queue 0001-0162),
and its rerun `area-combo-94` with the full device package 0.18. The first rehearsal boot (R1) stopped in the
rehearsal U-Boot at a `blkmap create` argument error (19:38). It was fixed in round 5 of the install workflow, and the
r1debug helper verified the fix 15 / 15 in its own U-Boot sandbox. The re-run is next (section 0). The owner restarted the tablet by hand. Nothing was written.

**Owner decisions taken after the first findings (WORKLOG, 2 Oct evening):**
- R-3: "yes lets test". The write-2 probe comes first, once its preconditions are green: the AVB footer, the PC
  proof with today's `vbmeta_b`, a read-only pull of today's images, and a new guide part C0.
- R-5: "no dual boot for now but prepare a plan for it with the best safety precautions". The install stays
  Fedora-only. The install workflow writes `wf/install/DUALBOOT-PLAN.md`, which this workflow reviews when it
  exists.

## 0. Status of every finding (2 Oct, about 22:30)

Sources: `wf/install/HANDOVER-ROUND6.md` (the install workflow's round-6 record), `wf/r1debug/REPORT.md`,
`docs/INSTALL-RERUN-COMMANDS.md`, WORKLOG after entry 44. The install workflow numbers the coordinator's items
R1-R9: R1 = R-1, R2 = R-2, R3 = R-3, R4 = R-4, R5 = R-6, R6 = R-7, R7 = R-5, R8 = R-8, R9 = R-9, B1 / B2 = R-11,
B3 = R-12 (charge limit).

| Finding | Status | Evidence / what is left |
|---|---|---|
| R-1 AVB footer for `boot_b` | **fixed in the tooling, proven on the PC** | `cand/avb/`: a libavb harness modelled on Qualcomm's public ABL (`ResultShouldContinue()`, `HandleActiveSlotUnbootable`). A plain U-Boot = INVALID_METADATA (stop, slot b unbootable); footered = PUBLIC_KEY_REJECTED (continue, the same as LineageOS today); AVB-PROOF PASS, 12 cases, on the LineageOS build's images. **Left:** rerun on today's pulled images (`parta-check.sh` after `parta-read.ps1`); OnePlus's own ABL is first seen in the write-2 probe (C0) |
| R-2 undo file from the pre-LineageOS backup | **confirmed; enforced in the tooling** | the backup's `vbmeta_b` is stock (flags 0, OnePlus key); the LineageOS build's is flags 1 with a test key. `parta-check.sh` makes `boot_b-before-install.img` from today's pull. **Left:** INSTALL-PLAN sections 2, 5.2, 8 text |
| R-3 write order | **decided: the write-2 probe first, run by the owner** | tooling done (`parta-read.ps1` reads only, a whitelist with 32 refused commands; `parta-check.sh` ends `PARTA: READY FOR C0`). **Left:** guide part C0 text (design in HANDOVER-ROUND6 section 4); Part A read on the tablet (command 6) |
| R-4 rehearsal build vs install build | **guard done; texts open** | `check-header.py --install-only` refuses the rehearsal build. **Left:** plan sections 2 / 5.2, guide Part B item 5 / Part D step 1 |
| R-5 dual boot | **decided: Fedora-only now; plan to be written** | `wf/install/DUALBOOT-PLAN.md` not started (brief: image file in userdata, userdata shrink / `fedora` partition, another LUN, boot selection; FBE, OTA, undo per step, rehearsals). This workflow reviews it |
| R-6 unattended U-Boot waits for ever | **fixed (sandbox-proven)** | U-Boot patch 0007: fastboot leaves after 600 s idle; `fastboot_loop` then powers off (also after 10 sessions). **Left:** guide section 9 rows; no hardware watchdog in U-Boot |
| R-7 boot order over all LUNs; `efisp` | **fixed** | env `fedora_bootopt`: one explicit Boot0001 (blkmap partition 1, `/EFI/fedora/shimaa64.efi`). No vendor LUN, no `EFI/BOOT` fallback, no shim fallback. The backup's `efisp` is all zeros (no file system) |
| R-8 guide behind plan and tooling | **open** | proposed texts to come from the install workflow (`proposed/` in its folder); the main session edits `docs/` |
| R-9 recovery rows, the `misc` trap | **check done; rows open** | ABL acts on `misc` only for `boot-recovery` / `boot-fastboot`; `parta-check.sh` stops on them. AOSP writes `bootonce-bootloader` at `adb reboot bootloader`, which ABL ignores. **Left:** the rows in guide section 9 |
| R-10 device tree via GRUB vs U-Boot | **open, decided by R1** | R1's `dt` acceptance line; `PER_KERNEL_DT=0` is the fallback |
| R-11 initramfs and firmware timing | **fixed in source; not yet in an image** | B1: dracut `omit_drivers` for the root-firmware drivers; the pwrseq `add_drivers` drop-in (`pcieprobe` line). B2: the build chroot gets its own sysfs and a read-only tmpfs over `selinuxfs` (each part reports "kit kernel policy loads N"; run 94 had 16). B4 (new): the GPU microcode trio was missing from run 94's initramfs; now in `fw-list.tsv` (26 items, 0 differ from stock) with a `gpu` line. The battery does **not** depend on the ADSP (BOOT-LOG-PLAN corrected). **Left:** P1 + TIN, then the B run must show "policy loads 0" and "root-firmware drivers 0", then R1's `adsp` / `cdsp` / `fwload` / `gpu` lines |
| R-12 smaller points | **partly fixed** | charge-limit check fixed (B3: `chargethreshold` + `chargelimit` on `qcom-battmgr-bat`). Still open: return to stock never executed; slot a after it; `adb root` pre-check; the plan's kernel numbers; `uboot.pin` comment; iceland-u-boot README |
| New: `unzip` has no length bound | **known gap, not reachable in practice** | a truncated gzip head crashed the sandbox; the head's sha256 is checked before sending. Hardening (`unzip ... ${headmax}`) after R1, then a rebuild and a new footer |
| New: GPU firmware in the image | **decided by the owner: linux-firmware (v5.3.23)** | what every kit since pc-024 used (the stock set is GMU v5.3.39). The install agent adapts B4 (three lines); the firmware count expected in the B run changes with it |
| New: R1 fix | **verified** | r1debug: root cause reproduced exactly; the install agent's fix 15 / 15 in an independent sandbox; `rehearse.ps1` got the busy-U-Boot probe. First tablet step: the 8 KiB notgzip head (command 3) |

## 1. Scope and sources

| Read | What |
|---|---|
| Plan | `docs/INSTALL-PLAN.md` (2 Oct, afternoon update incl. section 11) |
| Guide | `docs/INSTALL-GUIDE.md` (2 Oct, morning) |
| Tooling | `~/mainline/build/wf/install/REPORT.md`, `NEXT.md` (incl. rounds 3-5), `cand/u-boot/0004-0006*.patch`, `cand/rehearsal/rehearse.ps1` (fastboot whitelist), `cand/kernel-iceland/90-iceland-dtb.install`, `install.config`, `cand/fwx/fw-list.tsv`, `cand/iceland-device/files/` (names) |
| Runs | WORKLOG entries 36-44 (runs 63-93, R1), `docs/tests/uboot-run4/uboot-console-D.txt` (the 28 Sep RAM boot of the "normal" U-Boot environment) |
| Return path | `C:\OnePlusPad4\scripts\30-Restore-Stock.ps1`, `39-Return-To-Stock.ps1`, `22-Flash-LineageOS.ps1` (headers), `tools/dualboot/reflash-recovery.ps1` |
| Other | `docs/PLAN.md` v4 Phase 4-DB (dual boot), `docs/BOOT-LOG-PLAN.md`, `iceland-u-boot/uboot.pin`, the 27 Sep backup's partition listing (names, sizes, LUNs only) |

Upstream references used in the reasoning (public sources, not copied): AOSP `external/avb` (libavb
`avb_slot_verify.c`), Qualcomm's open ABL (`QcomModulePkg/Library/avb/VerifiedBoot.c`, CAF), U-Boot v2026.10
`lib/efi_loader/efi_bootmgr.c`, `cmd/fastboot.c`.

## 2. Verdict in short

The design is sound and unusually careful. The write surface is two partitions. Every write has an undo. The
rehearsal is made unable to touch the storage (G13: a U-Boot build without UFS, a read-only initramfs rule, an
NBD-only carrier). There is a self-check against storage-write words, a recorded-checksum discipline, and a written
return-to-stock path.

The review found four things to settle before any write:

1. **The boot path's verified-boot behaviour (AVB) is unproven, and probably fails as designed** (R-1). The fix
   is cheap and does not touch `vbmeta`.
2. **Several facts in the plan come from the 27 Sep backup**, which predates LineageOS on slot b (R-2).
3. **The plan and the guide still describe the old rehearsal**, in which the install U-Boot was RAM-booted in every
   rehearsal (R-4).
4. **The owner's stated goal (dual boot, keeping LineageOS) is not what the plan and guide implement** (R-5).
   Since decided: Fedora-only now, a dual-boot plan to be prepared.

None of the findings below is a brick risk on its own. The ABL / fastboot floor is never written by anything in the
plan. But two of them (R-1, R-3) could leave the tablet in a state where the only documented way back is the full
return to stock.

## 3. Findings, most severe first

Severity: **High** = can stop the install or force the full return to stock; **Medium** = wrong or missing
instruction, or an unattended failure mode; **Low** = wording, stale numbers.

### R-1 (High) - write 2: `boot_b` without an AVB footer is likely refused by ABL

- **Evidence.**
  - Install REPORT finding 11 says `boot` is a chained partition in `vbmeta_b` (flags 0). The plan (5.2) expects ABL
    on an unlocked tablet to "warn (orange) and continue". `u-boot-iceland.img` is a plain header-v4 image without
    an AVB footer (`iceland-u-boot/scripts/build.sh`, `tools/diag/build-diag.sh`).
  - In libavb, a chained partition whose last 64 bytes are not an AVB footer is read as a vbmeta image at offset 0.
    That offset holds the `ANDROID!` boot header, not `AVB0`, so the result is
    `AVB_SLOT_VERIFY_RESULT_ERROR_INVALID_METADATA`.
  - Qualcomm's open ABL continues on an unlocked device only for the "verification", "rollback index" and "public key
    rejected" results (`ResultShouldContinue()`). Invalid metadata gives `EFI_LOAD_ERROR` and the boot state RED.
  - The A/B code then either stops in ABL's fastboot or marks the slot unbootable and tries the other slot.
  - This matches the practice of mainline ports on Qualcomm phones: postmarketOS flashes a vbmeta with verification
    disabled before an unsigned boot image (pmbootstrap `flash_vbmeta`). The plan forbids that, rightly.
  - OnePlus's ABL is closed, so this is a strong expectation, not a proof.
- **Impact if it happens.**
  - Case A: ABL stops in fastboot. Undo write 2 (two minutes, documented).
  - Case B: ABL marks `slot-unbootable:b` and switches to slot a. Slot a holds LineageOS boot images without a system:
    the sideload of `22-Flash-LineageOS.ps1` deleted slot a's system from `super`. Coming back to slot b needs
    `fastboot set_active b`, which the guide forbids outside the return-to-stock script. The documented way out is
    then the full return to stock.
  - In neither case is the tablet bricked: Volume Down + Power still reaches ABL's fastboot.
- **Suggestions.**
  1. Give `u-boot-iceland.img` an AVB hash footer, the way every custom boot image on an unlocked device carries one:
     `avbtool add_hash_footer --image u-boot-iceland.img --partition_name boot --partition_size 100663296
     --algorithm SHA256_RSA4096 --key <a test key>`. Optionally add the
     `com.android.build.boot.os_version` / `security_patch` properties stock carries in its footer.
  2. ABL then sees "public key rejected" (or "verification error" if `boot` is hashed, not chained). Both continue in
     the orange state, the same case as a Magisk-patched or LineageOS-signed boot image. `fastboot boot` ignores the
     footer, so the rehearsal and the kits are unaffected. The file grows to 96 MiB, mostly zeros, so the sparse
     transfer stays small.
  3. **Prove it on the PC before the day.** Run libavb's `avb_slot_verify()` with file-backed ops (AOSP
     `external/avb` ships test ops) on today's `vbmeta_b` plus the candidate image. The result code must be one that
     continues, never `ERROR_INVALID_METADATA` or `ERROR_IO`. This is PC-only and takes minutes.
  4. Read **today's** `vbmeta_b` (and `vbmeta_system_b`) from the tablet, read-only, in Part A: `adb pull` with root,
     then `avbtool info_image`. Record the flags and whether `boot` is chained or hashed, with which key and
     rollback-index location (see R-2).
  5. The same applies to the `recovery_b` alternative and to the dual-boot helper `reflash-recovery.ps1`. It writes
     the same unsigned image into `recovery_<slot>`.
  6. Record slot a's state in Part A as well (`slot-successful:a`, `slot-unbootable:a`, `slot-retry-count:a`, and
     which images `boot_a` / `vendor_boot_a` are, by hash against the LineageOS build). The fallback in case B is
     then known in advance.

### R-2 (High) - the plan's undo for write 2 and its AVB analysis use the 27 Sep backup

- **Evidence.**
  - The backup `C:\OnePlusPad4\backups\20260927-1933-unknown` was taken on 27 Sep at 19:33, under stock OxygenOS.
    LineageOS was flashed on 28 Sep (`22-Flash-LineageOS.ps1`): boot images to slot a, then the OTA sideload to
    slot b, which became active. Before LineageOS's `copy-partitions`, slot b still held the factory 11.A.32 set
    (`docs/reference/pad4-hardware-boot-partitions.md` section 3).
  - So the backup's `boot_b` and `vbmeta_b` are factory slot-b images, not today's LineageOS slot b.
  - INSTALL-PLAN section 2 table ("`fastboot flash boot_b` with the saved image from the backup"), 5.2 ("Undo:
    `fastboot flash boot_b boot_b.img` from the backup") and section 8 (same) would put that factory-era stock boot
    image into LineageOS's slot b.
  - Plan 5.2's "save `boot_b` once more from the tablet and compare with the backup" will always report a
    difference.
  - Install REPORT finding 11 (vbmeta flags 0, the chain descriptor) was read with avbtool from the same backup.
- **Impact.** Following the plan's text instead of the guide gives an Android slot that does not boot. It is not a
  brick: fastboot stays reachable and `boot_b-before-install.img` restores it.
- **Suggestion.**
  1. Make the plan say what the guide already says: the undo file is `boot_b-before-install.img` from Part A step 5
     (today's LineageOS `boot_b`, 100663296 bytes, hash recorded in section 10).
  2. Replace "compare with the backup" by "compare with `boot_b-before-install.img`".
  3. Re-read the AVB facts from today's `vbmeta_b` (R-1, suggestion 4).

### R-3 (High; decided 2 Oct: the probe comes first) - the order of the two writes: probe write 2 first while Android's data is intact

- **Today's order.**
  - Write 1 (`userdata`) destroys LineageOS's data first. Only then is write 2 (`boot_b`) tried, and that is the
    write with the unproven ABL / AVB behaviour (R-1).
  - Between the two writes, any untethered power-on boots LineageOS onto a GPT disk image in `userdata`.
- **Proposed order.**
  1. "Write 2 as a probe" first: the footered install U-Boot into `boot_b`, with Android's data still in
     `userdata`.
  2. Cold-boot it untethered three times.
     - ABL must start U-Boot, and the retry count must not drop.
     - U-Boot maps `userdata` read-only and finds no EFI system (Android's encrypted data). It ends in its fastboot
       loop. This path was seen on 28 Sep in a RAM boot: `uboot-run4/uboot-console-D.txt`, "Loading Boot0006
       'blkmap 0' failed", then fastboot.
  3. Check G12 (Volume Down + Power reaches ABL with U-Boot in `boot_b`) and the slot flags.
  4. Undo (flash `boot_b-before-install.img`). LineageOS comes back **with its data**.
  5. Only then do write 1, then write 2 again with the same file.
- **What it gains.** ABL / AVB, the rescue door and the retry counter are proven before anything is lost. The window
  in which Android boots on a Fedora `userdata` disappears: after write 1 the tablet goes straight to U-Boot.
- **What it costs.** One more write of `boot_b` and its undo (the same partition, the same files, the same
  two-minute undo). It needs the owner's OK like every write.
- An even smaller variant needs no first write at all: a RAM boot of the install build before write 1 (see R-4,
  suggestion 3). It cannot test AVB, though: `fastboot boot` skips verification.

### R-4 (High, consistency) - plan and guide still say the install U-Boot is RAM-booted in every rehearsal

- **Evidence.**
  - Since the G13 change (WORKLOG entry 37), every rehearsal boots `u-boot-iceland-rehearsal.img`: no SCSI / UFS, and
    its bootcmd is `run fastboot_loop`.
  - The install build `u-boot-iceland.img` is first RAM-booted in Part C step 4, after write 1 (install REPORT 7.1,
    NEXT section 4).
  - Still stating the old design:
    - INSTALL-PLAN section 2 ("will have been RAM-booted in every rehearsal boot (R1-R4) before it is written");
    - INSTALL-PLAN 5.2 ("the file of the record, RAM-booted in R1-R4");
    - INSTALL-GUIDE Part B item 5 ("the U-Boot image that was `fastboot boot`ed in the rehearsal").
- **Impact.**
  - The written text overstates what has been proven. The install build's own UFS path (`scsi scan`, `part start` /
    `part size`, `blkmap ... linear`, the boot manager over all LUNs, the new `fastboot_loop`) has never run in its
    current form. Only an older environment ran it, read-only, on 28 Sep.
  - Two similar file names sit side by side in `priv/run/boot/`. Writing the rehearsal build into `boot_b` would
    give a tablet that loops through U-Boot's fastboot sessions and resets, again and again, until the PC or the
    keys intervene.
- **Suggestions.**
  1. Update both texts.
  2. Add a guard to Part D step 1. `check-header.py` (or a new check) must refuse an image whose embedded environment
     has `bootcmd=run fastboot_loop` without the `userdata_blkmap` line, or that lacks UFS symbols. The string is in
     the gzip'd U-Boot, so check after unzip.
  3. Owner decision: allow one dedicated RAM boot of the exact install build **before** write 1, as a read-only
     proof of its UFS path ("R-1 install"). On today's tablet it only reads. The 28 Sep run 4 did exactly this with
     the older environment. G13 rejected it for the rehearsal, but as a single reviewed step with the webcam watching
     it would turn "first seen after write 1" into "seen before any write". It also shows the boot-manager order on
     the real LUNs (R-7).

### R-5 (High; decided 2 Oct: Fedora-only now, a dual-boot plan is being written) - Fedora-only vs dual boot with LineageOS

- **Evidence.**
  - The owner's stated goal (per the coordinator's brief) is a permanent install that keeps Android (LineageOS) as
    dual boot.
  - INSTALL-PLAN and INSTALL-GUIDE implement Fedora-only. Write 1 replaces all of `userdata`, so LineageOS keeps its
    system partitions but loses its data and cannot be used. Dual boot is "outside this plan" (5.2) and decision 1.
  - `docs/PLAN.md` v4 Phase 4-DB describes a dual boot: U-Boot in `recovery_<slot>`, Fedora in a new `fedora`
    partition carved from `userdata`. It needs LUN 0's GPT changed, which INSTALL-PLAN section 2 lists as never
    written. The feature matrix row "Dual boot with Android" is "not started".
  - There is no "back to LineageOS" procedure anywhere. Section 8 of both documents returns to stock OxygenOS only.
- **Impact.** Running Part C as written ends LineageOS on this tablet, which may contradict the owner's goal.
- **Suggestions.**
  1. Do not start Part C until decision 1 is answered in writing.
  2. If dual boot is chosen, write a separate plan that settles:
     - the GPT change of LUN 0 (who writes it, from where, with what dry run and undo);
     - that `userdata` is reformatted once (Android's data is lost once);
     - the AVB footer for `recovery_b` (R-1);
     - LineageOS updates: they are sideloaded through LineageOS recovery, which U-Boot would replace, and an OTA flips
       slots. So each update means flashing LineageOS recovery back, sideloading, then putting U-Boot into the new
       slot's recovery;
     - the RTC offset (PLAN 4-DB already notes it);
     - a rehearsal.
  3. Add a "back to LineageOS" row to section 8: `22-Flash-LineageOS.ps1` exists, but it assumes stock on slot a and
     needs review for the post-install state.

### R-6 (Medium) - unattended failure mode of the installed U-Boot: waits for ever, screen on

- **Evidence.**
  - The install environment (patch 0006) ends `bootcmd` in `run fastboot_loop`: up to 10 `fastboot usb 0` sessions,
    then `reset`.
  - U-Boot's `fastboot usb` command returns only on Ctrl-C, on a detach, or when the host ends the session. It has no
    timeout. With no PC attached, the first session never ends.
  - The comment "then reset: ABL, then Android" is true for RAM boots only. With U-Boot in `boot_b`, a reset starts
    U-Boot again.
- **Impact.** If Fedora cannot be found (a damaged ESP, a bad GRUB update), an unattended tablet sits in U-Boot with
  the screen lit until the battery is flat. Plan 11.1.6 wants exactly that avoided: a flat battery is the most common
  "looks bricked" state. GRUB's own `grub>` prompt (missing config) has the same property.
- **Suggestions.**
  - Install build only: before fastboot, print one clear line on the screen ("Fedora not found - connect the PC, or
    hold Power 15 s").
  - Bound the wait: for example, only enter fastboot when VBUS is present, else power off. If U-Boot cannot power the
    PMIC off on this board, at least run a long sleep and then a reset into ABL's off-mode charging.
  - Arm a hardware watchdog in U-Boot before `bootefi` if a Qualcomm watchdog driver is available. A hang in an EFI
    program then also resets.
  - Add these states to guide section 9.

### R-7 (Medium) - U-Boot's EFI boot manager tries every UFS LUN before the Fedora disk; `efisp` never inspected

- **Evidence.**
  - `uboot-run4/uboot-console-D.txt` shows the generated boot order: Boot0000 'scsi 0' to Boot0005 'scsi 5', then
    Boot0006 'blkmap 0'.
  - With no stored variables (NO_STORE), U-Boot starts `\EFI\BOOT\BOOTAA64.EFI` from the **first** device that has
    it. On 28 Sep none of the six LUNs had one.
  - The `efisp` partition (3 MiB, LUN 4 = sde; by its name Qualcomm's EFI system partition of the boot firmware) is
    the obvious candidate. The project has never listed its files.
- **Impact.** Today it is not hit. But the order makes the boot depend on vendor partitions the plan never controls.
  It also exercises U-Boot's partition and file-system parsers on about 150 vendor partitions at every boot. The
  sandbox already found one parser (`part_mac`) overflowing on 4 KiB blocks; it is not in the device build.
- **Suggestions.**
  - In the install environment, create an explicit boot option before `bootefi bootmgr`, for example
    `efidebug boot add -b 1 Fedora blkmap 0:1 /EFI/fedora/shimaa64.efi; efidebug boot order 1` (needs
    `CMD_EFIDEBUG`). This boots the Fedora disk first, whatever the LUNs hold.
  - It also skips shim's fallback (`fbaa64.efi`), whose behaviour under NO_STORE variables is open fact F6. A
    fallback that resets after creating its entry would loop for ever, because the entry is lost at every reset.
  - Read-only check for the record: list `efisp`'s file names from the backup image on the PC (names only).

### R-8 (Medium) - the guide is behind the afternoon plan and the tooling

| Guide place | Says | Should say (source) |
|---|---|---|
| 0.1 readiness | G1-G5, G11; kernel rpm "test-built only"; device package parts "not built"; image builder + rehearsal "not built" | add G12 (fastboot by keys from cold, read-only), G13 (closed, entry 37), G14 (sleep drain); kernel rpm K2 / K3 built from q78 (13 checks); iceland-device 0.18 built on the tablet in run 93; image builder, NBD rehearsal and B run passed (run 93); R1 pending (plan section 1) |
| 0.4 decisions | 4 decisions | the plan's 10 decisions (plan section 9) + the write order (R-3) + the AVB footer (R-1) |
| Part A | no step for G12 | add: switch off, hold Volume Down + Power, `fastboot getvar current-slot`, `fastboot reboot` (read only) |
| Part A step 5 | `/data/vendor` copy | the plan's G5 also names `persist`. Either drop it from the plan (it is in the raw backup and never written) or add the read-only copy. Say why `/data/vendor` is saved and how it would ever be restored (no procedure exists today) |
| Part B item 5 | install U-Boot "fastboot booted in the rehearsal" | R-4 |
| Part C step 2 | `partition-size:userdata` "must be larger than the image's unpacked size" | must **equal** it: the sparse image is made with exactly userdata's size (install REPORT 4d: unpacked 237159641088 = userdata) |
| Part C step 3 | "The boot loader splits the image into pieces of at most 805 MB" | the PC's fastboot client splits it (ABL's `max-download-size` is 805306368) |
| Part C step 4 | three tethered cold boots | also run `accept.sh` and compare GRUB's environment before / after a trial boot (install NEXT section 4, fact F12) |
| Part D step 1 | hashes and slot flags | also `check-header.py u-boot-iceland.img boot_b-before-install.img`, the rehearsal-build guard (R-4) and the AVB result (R-1) |
| Part D step 2 | flash, then reboot | read the slot flags once right after the flash, before the reboot (read-only), so a flag change caused by the flash itself is told apart from one caused by the boot |
| section 10 | the record | take the values from `priv/run/RECORD.txt` (made by `rehearsal-pc.sh record` after R4), add the AVB result, today's `vbmeta_b` flags, slot a's flags |

### R-9 (Medium) - missing recovery instructions (paste-ready rows for guide section 9)

| What you see | What it means | What to do |
|---|---|---|
| After write 2 the tablet shows **LineageOS recovery** ("Can't load Android system") instead of Fedora | the misc partition still holds a "boot-recovery" command from an Android boot between the writes that was hard powered off | in that recovery choose **Reboot system now** (it clears the command), never "Factory data reset"; nothing is written by this |
| U-Boot text, then nothing, the screen stays on (no PC attached) | U-Boot found no Fedora and waits in its fastboot (R-6) | connect the PC: `fastboot devices` shows U-Boot. `fastboot oem console` (read-only) saves its log. Then RAM-boot the rescue kit through it, or hold Power 15 s |
| A black screen with a `grub>` prompt or a GRUB error | GRUB found no configuration (damaged `/boot`) | hold Power 15 s; RAM-boot the rescue kit (L3) and repair `/boot` |
| ABL shows a verified-boot error (instead of its usual unlocked warning) and stops after write 2 | ABL refused `boot_b` (R-1) | Volume Down + Power into ABL fastboot; undo write 2; record the slot flags; do not use `set_active` |
| `getvar current-slot` reads `a` after write 2 | ABL marked slot b unbootable and switched (R-1 case B) | do not write anything else; undo write 2; ask before the one-time `set_active b` or run the full return to stock |
| The tablet was switched off and plugged into a charger, and it boots Fedora | ABL starts the boot partition in charger mode; with U-Boot there that is Fedora (plan 11.1.6) | expected; no action |

### R-10 (Medium) - device tree delivery is decided in two places

- **The two designs.**
  - `iceland-linux/packaging/fedora/90-iceland-dtb.install` and its README (the committed version) deliberately avoid
    a GRUB `devicetree` line. U-Boot loads the ESP copy and applies ABL's memory fixups.
  - The install candidate (`cand/kernel-iceland/90-iceland-dtb.install`, `iceland-grub-setup`) adds a per-kernel
    `devicetree` line through `GRUB_DEVICETREE`. It relies on U-Boot's `EFI_DT_FIXUP_PROTOCOL` being called by
    Fedora's GRUB (fact F7, first seen in R1). It is switchable (`PER_KERNEL_DT`), and the ESP copy follows the
    confirmed kernel.
- **Suggestions.**
  - Keep the switch. Make R1's `dt` acceptance line the decision point: if Linux's `/proc/device-tree/memory*` does not
    show ABL's segments, set `PER_KERNEL_DT=0`.
  - Bring the committed iceland-linux plug-in and README in line with whatever R1 proves.

### R-11 (Medium) - the installed initramfs and the firmware timing (from BOOT-LOG-PLAN P1-a, P1-b)

- **The problem.**
  - `qcom_q6v5_pas` loads from the initramfs before the root (and the extracted firmware under
    `/usr/lib/firmware/updates`) is mounted. Remoteproc's auto-boot does not retry, so on the installed system the
    ADSP and CDSP stay off. In the kits a script starts them later.
  - Without the ADSP there is no sound and no sensors. BOOT-LOG-PLAN also lists the battery status. The battery data
    path is the SoCCP's pmic_glink channel (`PMIC_RTR_SOCCP_APPS`, hwinv O03), and the SoCCP is attached without a
    firmware file, so this dependency should be verified rather than assumed. The battery guard is the second safety
    layer of charging, so either way it needs an acceptance line.
- **Suggestions.**
  - Make "adsp and cdsp running, no `request_firmware failed`" an R1 / R2 acceptance line.
  - Make "battery guard active with live battery data" an acceptance line too.
  - Either keep the remoteproc driver out of the initramfs (dracut `omit_drivers`) or put that firmware into it; the
    image is private anyway.
  - The build chroot must not load SELinux policy into the RAM kit's kernel (P1-b). This is a rehearsal-integrity
    point, not a safety one.

### R-12 (Low) - smaller points

- **The charge-limit acceptance check** (found by the bypass workflow on run 94):
  - `accept.sh` reads `/sys/class/power_supply/battery`, but the battery's name is `qcom-battmgr-bat`.
  - UPower read the battery's udev properties before udev's coldplug set `CHARGE_LIMIT` (0.17's start-order drop-in
    prevents this on an installed system).
  - Fix the check before R1 / R2: the charge limit is one of the protections that make an unattended charger safe
    (gate G6).

- **The return to stock has never been run.** Only its dry run is planned (G3). Its `super` restore is a 14.6 GB raw
  image sent through ABL's fastboot. The dry run proves the inputs, not the flash. State it plainly in section 8 as
  "written and dry-run, never executed".
- **The return to stock leaves the tablet on slot a** (`set_active a`, by design). The guide's state table should
  say so.
- **`adb root` on LineageOS** needs a userdebug build with "Rooted debugging". Add a pre-check to Part A step 5.
- If `adb pull` refuses the block device, the read-only fallback is `adb exec-out "dd if=/dev/block/by-name/boot_b
  bs=4M"` through `cmd /c ... >`, like the tar line. The size check stays the same.
- **The plan's package table is stale.** Section 3 says kernel-iceland is "7.3-rc4 + queue 0001-0108". The current
  K2 is built from q78 = queue 0001-0162; the queue head is 0174.
- **`uboot.pin` comment.** It says the boot header OS version / patch level "must match stock (anti-rollback)". The
  install REPORT found that today's `boot_b` header carries zero values (GKI keeps them in the AVB footer). Align the
  comment, and put the values into the footer (R-1).
- **`iceland-u-boot/README.md`** still says "ABL -> `boot_a` = U-Boot ... systemd-boot/GRUB". The plan uses `boot_b`
  (the active slot) and GRUB via shim.

## 4. Consistency matrix (plan / guide / tooling / repos)

| Topic | INSTALL-PLAN | INSTALL-GUIDE | wf/install tooling | Repos / other | Consistent? |
|---|---|---|---|---|---|
| Partitions written | `userdata`, `boot_b` | same | same; selfcheck forbids storage-write words | `30-Restore` writes more, on purpose (section 8) | yes |
| U-Boot booted in rehearsal | install build (R1-R4) | install build | rehearsal build (no UFS) | - | **no (R-4)** |
| Undo file for write 2 | "boot_b.img from the backup" | `boot_b-before-install.img` (Part A) | `check-header.py` compares with the saved file | backup predates LineageOS | **no (R-2)** |
| AVB on `boot_b` | "orange, continues" | not mentioned | F16, "not provable by RAM" | libavb / CAF ABL: invalid metadata does not continue | **open (R-1)** |
| userdata size vs image | equal (sections 3, 5.1) | "larger than" | equal | - | **no (R-8)** |
| Gates | G1-G14 | G1-G5, G11 | G13 closed | - | **no (R-8)** |
| Decisions | 10 | 4 | - | brief: dual boot wanted | **no (R-5, R-8)** |
| Device tree to Linux | GRUB loads per-kernel DT (step 4, *) | - | `GRUB_DEVICETREE` switchable, F7 | iceland-linux plug-in: no GRUB line | **two designs (R-10)** |
| Firmware path names | - | - | `qcom/kaanapali/iceland/...` (= board DT `firmware-name`) | `firmware/manifest.tsv` and the reference doc: `qcom/kaanapali/OnePlus/iceland/...` | **no** (manifest stale; the DT is authoritative) |
| Kernel queue in the image | 0001-0108 | - | q78 = 0001-0162 | head 0174 | stale numbers |
| Return to LineageOS | - | - | - | `22-Flash-LineageOS.ps1` (pre-install assumptions) | **missing (R-5)** |

## 5. What is done well (keep it)

- **The write surface is two partitions,** and the "never written" list is complete against the 151-partition
  layout. It includes the UFS device firmware (the fwupd plug-ins).
- **Defence in depth inside Fedora:**
  - the read-only udev rule is already in the initramfs;
  - EFI programs can write only blkmap disks (patch 0005);
  - no FAT / ext4 / GPT writer is linked into U-Boot;
  - EFI variables are not stored;
  - dnf excludes, the release pin, protected packages.
- **The rehearsal is designed to be unable to write:** a build without UFS, an NBD-only carrier, a relay that admits
  only 172.16.42.1, the self-check rules A / B / C / P.
- **Problems found by measurement, not by guessing:** the f_ncm flush bug (runs 85 / 86, queue 0162), the WSL
  forwarder stall, nbd-client's `-C` crash, the blkmap subcommand table (R1, reproduced in the U-Boot sandbox).
- **Recorded checksums of exactly the rehearsed files,** and the "stop, do not improvise" rule.

## 6. Open questions for the owner (from this review)

1. (Answered: Fedora-only now; a dual-boot plan is to be prepared.) When the dual-boot plan exists: may LUN 0's
   partition table be changed once, under that plan?
2. May the install U-Boot carry an AVB hash footer signed with a test key (R-1)? It changes no other partition.
3. (Answered: yes, probe write 2 first.) Remaining: who runs the probe's undo, and when is the probe's evidence
   enough to proceed to write 1?
4. May the exact install U-Boot be RAM-booted once before write 1, read-only, as on 28 Sep (R-4 suggestion 3)?
5. Unattended U-Boot fallback: power off after a timeout, or wait with the screen on (R-6)?
6. Is a "back to LineageOS" path needed, or is "back to stock OxygenOS" enough (R-5)?

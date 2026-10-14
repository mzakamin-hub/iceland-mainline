# 07 - Independent review of the installation process

Reviewer: the documentation / SME workflow ("docs"), 2 Oct 2026, evening; updated 3 Oct (the final build) and 14 Oct
(the install). The review was PC-only at the time: nothing was run on the tablet, nothing was built, and no file outside
the project's private work folder was changed.

**Status (14 Oct 2026).** The install is done. The owner ran the two writes on 13 Oct 2026: `userdata` (write 1, 18:31)
and `boot_b` (write 2, 20:47). Fedora 44 GNOME booted from `boot_b` on its own at 20:48 and is the owner's system.
This review is kept as it was written, so that the reasons for each decision stay visible. Section 7 gives the status
of every finding after the install, section 8 records what the install showed (the writes, the hashes, the state after
the install), and section 9 lists the checks that still need the owner's hands. The install guide the owner followed is
`docs/INSTALL-GUIDE.md` (the B149 edition).

**Status of the install on the day of this review (2 Oct):** nothing had been written to the tablet. The PC-side tooling
was built and checked. The rehearsal's build run had passed twice (the build of kernel q78 and its rerun with the full
device package 0.18). The first rehearsal boot (R1) had stopped in the rehearsal U-Boot at a `blkmap create` argument
error (19:38). It was fixed in round 5 of the install workflow, and a second helper verified the fix 15 / 15 in its own
U-Boot sandbox. The re-run was next. Nothing was written.

**Owner decisions taken after the first findings (2 Oct evening):**
- R-3: the write-2 probe comes first, once its preconditions are green: the AVB footer, the PC proof with today's
  `vbmeta_b`, a read-only pull of today's images, and a new guide part C0.
- R-5: no dual boot for now, but prepare a plan for it with the best safety precautions. The install stays Fedora-only.
  The dual-boot plan is a draft (`docs/DUALBOOT-PLAN.md`).

**Update 3 Oct, the final build:** the install image of the final build (kernel q84 = `7.3.0-rc4-iceland-00313-gba2ed250bf33`,
queue 0001-0185; `iceland-device` 0.19) passed its build run (31 PASS, 0 FAIL) and its rehearsal (45 PASS, 0 FAIL, 0 CHECK).
Nothing had been written to the tablet; C0 and the two writes waited for the owner.

**Update 14 Oct, the install:** the final golden image B149 (kernel q89g, Linux 7.3-rc7; `iceland-device` 0.28-7;
`iceland-firmware` 11.A.38-3) was committed on 13 Oct after the final rehearsal r158 (64 rows, 0 FAIL). The owner's two
writes followed on the same evening. See sections 7 and 8.

## 0. Status of every finding (2 Oct, about 22:30)

Sources at the time: the install workflow's round-6 handover record, the r1debug report, the install rerun commands and
the worklog after entry 44. The install workflow numbers the coordinator's items R1-R9: R1 = R-1, R2 = R-2, R3 = R-3,
R4 = R-4, R5 = R-6, R6 = R-7, R7 = R-5, R8 = R-8, R9 = R-9, B1 / B2 = R-11, B3 = R-12 (charge limit).

| Finding | Status on 2 Oct | Evidence / what is left |
|---|---|---|
| R-1 AVB footer for `boot_b` | **fixed in the tooling, proven on the PC** | A libavb harness modelled on Qualcomm's public ABL. A plain U-Boot gives INVALID_METADATA (stop, slot b unbootable); a footered image gives PUBLIC_KEY_REJECTED (continue, the same as LineageOS today); AVB-PROOF PASS, 12 cases, on the LineageOS build's images. **Left:** the rerun on today's pulled images; OnePlus's own ABL is first seen in the write-2 probe (C0) |
| R-2 undo file from the pre-LineageOS backup | **confirmed; enforced in the tooling** | The backup's `vbmeta_b` is stock (flags 0, OnePlus key); the LineageOS build's is flags 1 with a test key. The checker makes `boot_b-before-install.img` from today's pull. **Left:** the plan's text |
| R-3 write order | **decided: the write-2 probe first, run by the owner** | The read tool is read-only (a whitelist); the checker ends `PARTA: READY FOR C0`. **Left:** guide part C0 text; the Part A read on the tablet |
| R-4 rehearsal build vs install build | **guard done; texts open** | The header check refuses the rehearsal build. **Left:** plan sections 2 / 5.2, guide Part B item 5 / Part D step 1 |
| R-5 dual boot | **decided: Fedora-only now; plan written and reviewed** | The dual-boot draft recommends a `fedora` partition carved from `userdata` (one LUN 0 partition-table write; Android's data lost once) plus U-Boot in `recovery_<slot>`, with a probe first. It rejects an image file inside `userdata` (file-based encryption with hardware-wrapped keys; raw-extent mapping risks silent loss of Android's data). Four review points were settled in the draft: the Power + Volume Up route is unverified (the certain paths are `adb reboot recovery`, "Restart to recovery" and `fastboot reboot recovery`); the flag reset applies only to partitions named `boot*`; a size read between the writes goes back into ABL's fastboot, never Android; the owner's deadline "decide before write 1" |
| R-6 unattended U-Boot waits for ever | **fixed (sandbox-proven)** | U-Boot patch 0007: fastboot leaves after 600 s idle; the loop then powers off (also after 10 sessions). No hardware watchdog in U-Boot. **Left:** the guide's section 9 rows |
| R-7 boot order over all LUNs; `efisp` | **fixed** | An explicit boot option (blkmap partition 1, `/EFI/fedora/shimaa64.efi`); no vendor LUN, no `EFI/BOOT` fallback, no shim fallback. The backup's `efisp` is all zeros (no file system) |
| R-8 guide behind plan and tooling | **open** | Proposed texts to come from the install workflow; the main session edits `docs/` |
| R-9 recovery rows, the `misc` trap | **check done; rows open** | ABL acts on `misc` only for `boot-recovery` / `boot-fastboot`; the checker stops on them. AOSP writes `bootonce-bootloader` at `adb reboot bootloader`, which ABL ignores. **Left:** the rows in guide section 9 |
| R-10 device tree via GRUB vs U-Boot | **open, to be decided by the R1 `dt` line** | the committed packaging (U-Boot loads the ESP copy) and the install candidate (a per-kernel GRUB line) differ; `PER_KERNEL_DT=0` is the fallback |
| R-11 initramfs and firmware timing | **fixed and proven in the rehearsals (3 Oct onward)** | The final design puts the SoCCP / ADSP / CDSP stack and the tablet's DSP firmware into the initramfs (USB-C up before the network disk; R1b's link drop), with Wi-Fi / BT / video omitted. The battery does **not** depend on the ADSP (boot-log review, corrected 2 Oct). GPU microcode trio added (B4) |
| R-12 smaller points | **partly fixed** | Charge-limit check fixed (B3). Still open: return to stock never executed; the slot a state after it; `adb root` pre-check; the plan's kernel numbers; the `uboot.pin` comment; the U-Boot README |
| New: `unzip` has no length bound | **known gap, not reachable in practice** | A truncated gzip head crashed the sandbox; the head's sha256 is checked before sending. Hardening was planned after R1 |
| New: GPU firmware in the image | **decided by the owner: linux-firmware (v5.3.23)** | What every kit since pc-024 used (the stock set is GMU v5.3.39). The firmware package is held and enters an initramfs only with the next kernel-iceland install |
| New: A/B flags reset by the flash, and the countdown | **open owner decision pending C0: `boot_b` or `recovery_b`** | Open ABL source: flashing `boot_b` clears *successful* / *unbootable* and sets *retry count* to max; every normal boot of a slot that is not successful counts down; at 0 the slot is marked unbootable. Only Android marks a slot successful. C0 measures it. Fallback: `recovery_b`. **Status 14 Oct: see section 7** |
| New: footer values handed to the TEE | **fixed** | ABL passes the footer's `os_version` and `security_patch` to the TEE (else the header's). The footer tool copies both from today's `boot_b` and refuses without both |
| New: R1 fix | **verified** | The r1debug check reproduced the root cause; the fix passed 15 / 15 in an independent sandbox; the rehearsal tool got the busy-U-Boot probe. First tablet step: the 8 KiB "not gzip" test head |

## 1. Scope and sources

| Read | What |
|---|---|
| Plan | `docs/INSTALL-PLAN.md` (2 Oct, afternoon update incl. section 11) |
| Guide | `docs/INSTALL-GUIDE.md` (2 Oct, morning; the B149 edition after 13 Oct) |
| Tooling | the install workflow's report, next steps (rounds 3-5), the U-Boot patch series, the rehearsal tool's fastboot whitelist, the kernel install hook, the install configuration and the firmware list (not published) |
| Runs | the worklog entries 36-44 (runs 63-93, R1) (not published); the 28 Sep RAM-boot console log of the normal U-Boot environment |
| Return path | the owner's return-to-stock scripts (headers only; not published) and the dual-boot reflash helper (`tools/dualboot/`) |
| Other | `docs/PLAN.md` v4 Phase 4-DB (dual boot), the boot-log review (not published), `iceland-u-boot/uboot.pin`, the 27 Sep backup's partition listing (names, sizes, LUNs only) |

Upstream references used in the reasoning (public sources, not copied): AOSP `external/avb` (libavb
`avb_slot_verify.c`), Qualcomm's open ABL (`QcomModulePkg/Library/avb/VerifiedBoot.c`, CAF), U-Boot v2026.10
`lib/efi_loader/efi_bootmgr.c`, `cmd/fastboot.c`.

## 2. Verdict in short

The design is sound and unusually careful. The write surface is two partitions. Every write has an undo. The
rehearsal was made unable to touch the storage (a U-Boot build without UFS, a read-only initramfs rule, an
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

**Outcome (14 Oct):** the install went through with the footered image, ABL started it, and Fedora booted from
`boot_b`. The one real problem of the install, the slot marking, was not among the findings (section 7, N-1).

## 3. Findings, most severe first

Severity: **High** = can stop the install or force the full return to stock; **Medium** = wrong or missing
instruction, or an unattended failure mode; **Low** = wording, stale numbers.

### R-1 (High) - write 2: `boot_b` without an AVB footer is likely refused by ABL

- **Evidence.**
  - The install report (finding 11) says `boot` is a chained partition in `vbmeta_b` (flags 0). The plan (5.2) expects ABL
    on an unlocked tablet to "warn (orange) and continue". `u-boot-iceland.img` is a plain header-v4 image without
    an AVB footer (the build script of `iceland-u-boot`, and the diagnostic build script).
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
    the sideload of the LineageOS script deleted slot a's system from `super`. Coming back to slot b needs
    `fastboot set_active b`, which the guide forbids outside the return-to-stock script. The documented way out is
    then the full return to stock.
  - In neither case is the tablet bricked: Volume Down + Power still reaches ABL's fastboot.
- **Suggestions.**
  1. Give `u-boot-iceland.img` an AVB hash footer, the way every custom boot image on an unlocked device carries one
     (a test key; the footer also carries the `os_version` / `security_patch` properties stock carries).
  2. ABL then sees "public key rejected" (or "verification error" if `boot` is hashed, not chained). Both continue in
     the orange state, the same case as a Magisk-patched or LineageOS-signed boot image. `fastboot boot` ignores the
     footer, so the rehearsal and the kits are unaffected. The file grows to 96 MiB, mostly zeros, so the sparse
     transfer stays small.
  3. **Prove it on the PC before the day.** Run libavb's `avb_slot_verify()` with file-backed ops on today's `vbmeta_b`
     plus the candidate image. The result code must be one that continues, never `ERROR_INVALID_METADATA` or `ERROR_IO`.
     This is PC-only and takes minutes.
  4. Read **today's** `vbmeta_b` (and `vbmeta_system_b`) from the tablet, read-only, in Part A: record the flags and
     whether `boot` is chained or hashed, with which key and rollback-index location (see R-2).
  5. The same applies to the `recovery_b` alternative and to the dual-boot helper, which writes the same unsigned image
     into `recovery_<slot>`.
  6. Record slot a's state in Part A as well (`slot-successful:a`, `slot-unbootable:a`, `slot-retry-count:a`, and
     which images `boot_a` / `vendor_boot_a` are, by hash against the LineageOS build). The fallback in case B is
     then known in advance.

### R-2 (High) - the plan's undo for write 2 and its AVB analysis use the 27 Sep backup

- **Evidence.**
  - The backup was taken on 27 Sep, under stock OxygenOS. LineageOS was flashed on 28 Sep: boot images to slot a, then
    the OTA sideload to slot b, which became active. Before LineageOS's `copy-partitions`, slot b still held the
    factory 11.A.32 set (`docs/reference/pad4-hardware-boot-partitions.md` section 3).
  - So the backup's `boot_b` and `vbmeta_b` are factory slot-b images, not today's LineageOS slot b.
  - The plan's undo text ("`fastboot flash boot_b` with the saved image from the backup", section 5.2 and section 8)
    would put that factory-era stock boot image into LineageOS's slot b.
  - Plan 5.2's "save `boot_b` once more from the tablet and compare with the backup" will always report a difference.
  - The install report's finding 11 (vbmeta flags 0, the chain descriptor) was read from the same backup.
- **Impact.** Following the plan's text instead of the guide gives an Android slot that does not boot. It is not a
  brick: fastboot stays reachable and the undo file restores it.
- **Suggestion.**
  1. Make the plan say what the guide already says: the undo file is `boot_b-before-install.img` from Part A (today's
     LineageOS `boot_b`, 100663296 bytes, hash recorded in the guide's record).
  2. Replace "compare with the backup" by "compare with `boot_b-before-install.img`".
  3. Re-read the AVB facts from today's `vbmeta_b` (R-1, suggestion 4).

### R-3 (High; decided 2 Oct: the probe comes first) - the order of the two writes: probe write 2 first while Android's data is intact

- **Today's order.**
  - Write 1 (`userdata`) destroys LineageOS's data first. Only then is write 2 (`boot_b`) tried, and that is the
    write with the unproven ABL / AVB behaviour (R-1).
  - Between the two writes, any untethered power-on boots LineageOS onto a GPT disk image in `userdata`.
- **Proposed order.**
  1. "Write 2 as a probe" first: the footered install U-Boot into `boot_b`, with Android's data still in `userdata`.
  2. Cold-boot it untethered three times.
     - ABL must start U-Boot. The retry count is expected to drop by one per boot (the flash resets slot b's flags,
       and only Android marks a slot successful): hard stop at 2 or less. Whether it drops decides `boot_b` vs
       `recovery_b` (section 0).
     - U-Boot maps `userdata` read-only and finds no EFI system (Android's encrypted data). It ends in its fastboot
       loop. This path was seen on 28 Sep in a RAM boot (the run 4 console log).
  3. Check that Volume Down + Power reaches ABL with U-Boot in `boot_b`, and the slot flags.
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
  - Since the G13 change (worklog entry 37), every rehearsal boots the rehearsal build of U-Boot: no SCSI / UFS, and
    its bootcmd is `run fastboot_loop`.
  - The install build is first RAM-booted in Part C step 4, after write 1 (install report 7.1).
  - Still stating the old design:
    - INSTALL-PLAN section 2 ("will have been RAM-booted in every rehearsal boot (R1-R4) before it is written");
    - INSTALL-PLAN 5.2 ("the file of the record, RAM-booted in R1-R4");
    - the guide's Part B item 5 ("the U-Boot image that was `fastboot boot`ed in the rehearsal").
- **Impact.**
  - The written text overstates what has been proven. The install build's own UFS path (`scsi scan`, `part start` /
    `part size`, `blkmap ... linear`, the boot manager over all LUNs, the new `fastboot_loop`) has never run in its
    current form. Only an older environment ran it, read-only, on 28 Sep.
  - Two similar file names sit side by side in the rehearsal folder. Writing the rehearsal build into `boot_b` would
    give a tablet that loops through U-Boot's fastboot sessions and resets, again and again, until the PC or the
    keys intervene.
- **Suggestions.**
  1. Update both texts.
  2. Add a guard to Part D step 1. The header check must refuse an image whose embedded environment has
     `bootcmd=run fastboot_loop` without the `userdata_blkmap` line, or that lacks UFS symbols. The string is in the
     gzip'd U-Boot, so check after unzip.
  3. Owner decision: allow one dedicated RAM boot of the exact install build **before** write 1, as a read-only proof of
     its UFS path. On today's tablet it only reads. The 28 Sep run 4 did exactly this with the older environment. The
     rehearsal rule rejected it for the rehearsal, but as a single reviewed step with the webcam watching it would turn
     "first seen after write 1" into "seen before any write". It also shows the boot-manager order on the real LUNs (R-7).

### R-5 (High; decided 2 Oct: Fedora-only now, a dual-boot plan is being written) - Fedora-only vs dual boot with LineageOS

- **Evidence.**
  - The owner's stated goal (per the coordinator's brief) was a permanent install that keeps Android (LineageOS) as
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
  3. Add a "back to LineageOS" row to section 8: the LineageOS script exists, but it assumes stock on slot a and
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
  - The 28 Sep console log shows the generated boot order: Boot0000 'scsi 0' to Boot0005 'scsi 5', then
    Boot0006 'blkmap 0'.
  - With no stored variables (NO_STORE), U-Boot starts `\EFI\BOOT\BOOTAA64.EFI` from the **first** device that has
    it. On 28 Sep none of the six LUNs had one.
  - The `efisp` partition (3 MiB, LUN 4; by its name Qualcomm's EFI system partition of the boot firmware) is the
    obvious candidate. The project has never listed its files.
- **Impact.** Today it is not hit. But the order makes the boot depend on vendor partitions the plan never controls.
  It also exercises U-Boot's partition and file-system parsers on about 150 vendor partitions at every boot. The
  sandbox already found one parser (`part_mac`) overflowing on 4 KiB blocks; it is not in the device build.
- **Suggestions.**
  - In the install environment, create an explicit boot option before `bootefi bootmgr`, so that the Fedora disk is
    booted first, whatever the LUNs hold (the EFI boot-option commands of U-Boot, with `CMD_EFIDEBUG`).
  - It also skips shim's fallback, whose behaviour under NO_STORE variables is open. A fallback that resets after
    creating its entry would loop for ever, because the entry is lost at every reset.
  - Read-only check for the record: list `efisp`'s file names from the backup image on the PC (names only).

### R-8 (Medium) - the guide is behind the afternoon plan and the tooling

| Guide place | Says (2 Oct) | Should say (source) |
|---|---|---|
| 0.1 readiness | G1-G5, G11; kernel rpm "test-built only"; device package parts "not built"; image builder + rehearsal "not built" | add G12 (fastboot by keys from cold, read-only), G13 (closed, entry 37), G14 (sleep drain); kernel rpm built; iceland-device 0.18 built on the tablet in run 93; image builder, NBD rehearsal and B run passed (run 93); R1 pending (plan section 1) |
| 0.4 decisions | 4 decisions | the plan's 10 decisions (plan section 9) + the write order (R-3) + the AVB footer (R-1) |
| Part A | no step for G12 | add: switch off, hold Volume Down + Power, `fastboot getvar current-slot`, `fastboot reboot` (read only) |
| Part A step 5 | `/data/vendor` copy | the plan's G5 also names `persist`. Either drop it from the plan (it is in the raw backup and never written) or add the read-only copy. Say why `/data/vendor` is saved and how it would ever be restored (no procedure exists today) |
| Part B item 5 | install U-Boot "fastboot booted in the rehearsal" | R-4 |
| Part C step 2 | `partition-size:userdata` "must be larger than the image's unpacked size" | must **equal** it: the sparse image is made with exactly userdata's size (install report 4d: unpacked 237159641088 = userdata) |
| Part C step 3 | "The boot loader splits the image into pieces of at most 805 MB" | the PC's fastboot client splits it (ABL's `max-download-size` is 805306368) |
| Part C step 4 | three tethered cold boots | also run `accept.sh` and compare GRUB's environment before / after a trial boot (fact F12) |
| Part D step 1 | hashes and slot flags | also the header check of `u-boot-iceland.img` against `boot_b-before-install.img`, the rehearsal-build guard (R-4) and the AVB result (R-1) |
| Part D step 2 | flash, then reboot | read the slot flags once right after the flash, before the reboot (read-only), so a flag change caused by the flash itself is told apart from one caused by the boot |
| section 10 | the record | take the values from the record file (made by the rehearsal script after R4), add the AVB result, today's `vbmeta_b` flags, slot a's flags |

### R-9 (Medium) - missing recovery instructions (paste-ready rows for guide section 9)

| What you see | What it means | What to do |
|---|---|---|
| After write 2 the tablet shows **LineageOS recovery** ("Can't load Android system") instead of Fedora | the misc partition still holds a "boot-recovery" command from an Android boot between the writes that was hard powered off | in that recovery choose **Reboot system now** (it clears the command), never "Factory data reset"; nothing is written by this |
| U-Boot text, then nothing, the screen stays on (no PC attached) | U-Boot found no Fedora and waits in its fastboot (R-6) | connect the PC: `fastboot devices` shows U-Boot. `fastboot oem console` (read-only) saves its log. Then RAM-boot the rescue kit through it, or hold Power 15 s |
| A black screen with a `grub>` prompt or a GRUB error | GRUB found no configuration (damaged `/boot`) | hold Power 15 s; RAM-boot the rescue kit (L3) and repair `/boot` |
| ABL shows a verified-boot error (instead of its usual unlocked warning) and stops after write 2 | ABL refused `boot_b` (R-1) | Volume Down + Power into ABL fastboot; undo write 2; record the slot flags; do not use `set_active` |
| `getvar slot-successful:b` reads `no` right after writing `boot_b` | expected: the flash itself clears the flag and sets the retry count to its maximum (open ABL source) | nothing; note the retry count |
| `slot-retry-count:b` is lower after each power-on | ABL counts boots of a slot that is not successful; U-Boot and Fedora never mark it successful | at 2 or less: stop and undo write 2 at once (the flash resets the count); the permanent place is then `recovery_b` (owner's decision) |
| `getvar current-slot` reads `a` after write 2 | ABL marked slot b unbootable and switched (R-1 case B, or the retry count ran out) | do not write anything else; undo write 2; ask before the one-time `set_active b` or run the full return to stock |
| The tablet was switched off and plugged into a charger, and it boots Fedora | ABL starts the boot partition in charger mode; with U-Boot there that is Fedora (plan 11.1.6) | expected; no action |

### R-10 (Medium) - device tree delivery is decided in two places

- **The two designs.**
  - The committed packaging (`iceland-linux/packaging/fedora/`, its install hook and README) deliberately avoids a GRUB
    `devicetree` line. U-Boot loads the ESP copy and applies ABL's memory fixups.
  - The install candidate adds a per-kernel `devicetree` line through `GRUB_DEVICETREE`. It relies on U-Boot's
    `EFI_DT_FIXUP_PROTOCOL` being called by Fedora's GRUB (fact F7, first seen in R1). It is switchable
    (`PER_KERNEL_DT`), and the ESP copy follows the confirmed kernel.
- **Suggestions.**
  - Keep the switch. Make R1's `dt` acceptance line the decision point: if Linux's `/proc/device-tree/memory*` does not
    show ABL's segments, set `PER_KERNEL_DT=0`.
  - Bring the committed packaging and README in line with whatever R1 proves.

### R-11 (Medium) - the installed initramfs and the firmware timing (from the boot-log review, P1-a, P1-b)

- **The problem.**
  - `qcom_q6v5_pas` loads from the initramfs before the root (and the extracted firmware under
    `/usr/lib/firmware/updates`) is mounted. Remoteproc's auto-boot does not retry, so on the installed system the
    ADSP and CDSP stay off. In the kits a script starts them later.
  - Without the ADSP there is no sound and no sensors. The boot-log review also lists the battery status. The battery
    data path is the SoCCP's pmic_glink channel, and the SoCCP is attached without a firmware file, so this dependency
    should be verified rather than assumed. The battery guard is the second safety layer of charging, so either way it
    needs an acceptance line.
- **Suggestions.**
  - Make "adsp and cdsp running, no `request_firmware failed`" an R1 / R2 acceptance line.
  - Make "battery guard active with live battery data" an acceptance line too.
  - Either keep the remoteproc driver out of the initramfs (dracut `omit_drivers`) or put that firmware into it; the
    image is private anyway.
  - The build chroot must not load SELinux policy into the RAM kit's kernel (P1-b). This is a rehearsal-integrity
    point, not a safety one.

### R-12 (Low) - smaller points

- **The charge-limit acceptance check** (found by the bypass workflow on run 94):
  - the acceptance script reads the generic battery sysfs name, but the battery's name is `qcom-battmgr-bat`.
  - UPower read the battery's udev properties before udev's coldplug set `CHARGE_LIMIT` (the start-order drop-in of
    0.17 prevents this on an installed system).
  - Fix the check before R1 / R2: the charge limit is one of the protections that make an unattended charger safe
    (gate G6).
- **The return to stock has never been run.** Only its dry run is planned (G3). Its `super` restore is a 14.6 GB raw
  image sent through ABL's fastboot. The dry run proves the inputs, not the flash. State it plainly in section 8 as
  "written and dry-run, never executed".
- **The return to stock leaves the tablet on slot a** (`set_active a`, by design). The guide's state table should
  say so.
- **`adb root` on LineageOS** needs a userdebug build with "Rooted debugging". Add a pre-check to Part A step 5.
- If `adb pull` refuses the block device, the read-only fallback is a `dd` of the `boot_b` partition through the
  host's shell, like the tar line. The size check stays the same.
- **The plan's package table is stale.** It names kernel-iceland as "7.3-rc4 + queue 0001-0108". The queue head at
  the time was 0174.
- **`uboot.pin` comment.** It says the boot header OS version / patch level "must match stock (anti-rollback)". The
  install report found that today's `boot_b` header carries zero values (GKI keeps them in the AVB footer). Align the
  comment, and put the values into the footer (R-1).
- **The U-Boot README** still says "ABL -> `boot_a` = U-Boot ... systemd-boot/GRUB". The plan uses `boot_b`
  (the active slot) and GRUB via shim.

## 4. Consistency matrix (plan / guide / tooling / repos), 2 Oct

| Topic | INSTALL-PLAN | INSTALL-GUIDE | Install tooling | Repos / other | Consistent? |
|---|---|---|---|---|---|
| Partitions written | `userdata`, `boot_b` | same | same; the self-check forbids storage-write words | the owner's return-to-stock script writes more, on purpose (section 8) | yes |
| U-Boot booted in rehearsal | install build (R1-R4) | install build | rehearsal build (no UFS) | - | **no (R-4)** |
| Undo file for write 2 | "boot_b.img from the backup" | `boot_b-before-install.img` (Part A) | the header check compares with the saved file | backup predates LineageOS | **no (R-2)** |
| AVB on `boot_b` | "orange, continues" | not mentioned | "not provable by RAM" | libavb / CAF ABL: invalid metadata does not continue | **open (R-1)** |
| userdata size vs image | equal (sections 3, 5.1) | "larger than" | equal | - | **no (R-8)** |
| Gates | G1-G14 | G1-G5, G11 | G13 closed | - | **no (R-8)** |
| Decisions | 10 | 4 | - | brief: dual boot wanted | **no (R-5, R-8)** |
| Device tree to Linux | GRUB loads per-kernel DT (step 4, *) | - | `GRUB_DEVICETREE` switchable, F7 | committed packaging: no GRUB line | **two designs (R-10)** |
| Firmware path names | - | - | `qcom/kaanapali/iceland/...` (= board DT `firmware-name`) | the firmware manifest and the reference doc: `qcom/kaanapali/OnePlus/iceland/...` | **no** (manifest stale; the DT is authoritative) |
| Kernel queue in the image | 0001-0108 | - | q78 = 0001-0162 | head 0174 | stale numbers |
| Return to LineageOS | - | - | - | the LineageOS script (pre-install assumptions) | **missing (R-5)** |

## 5. What is done well (keep it)

- **The write surface is two partitions,** and the "never written" list is complete against the 151-partition
  layout. It includes the UFS device firmware (the fwupd plug-ins).
- **Defence in depth inside Fedora:**
  - the read-only udev rule is already in the initramfs;
  - EFI programs can write only blkmap disks (U-Boot patch 0005);
  - no FAT / ext4 / GPT writer is linked into U-Boot;
  - EFI variables are not stored;
  - dnf excludes, the release pin, protected packages.
- **The rehearsal is designed to be unable to write:** a build without UFS, an NBD-only carrier, a relay that admits
  only the tablet's USB network address, the self-check rules.
- **Problems found by measurement, not by guessing:** the f_ncm flush bug (queue 0162), the WSL forwarder stall, the
  NBD client's crash, the blkmap subcommand table (R1, reproduced in the U-Boot sandbox).
- **Recorded checksums of exactly the rehearsed files,** and the "stop, do not improvise" rule. The same discipline
  carried the install: the owner confirmed each write against the partition, file, size and SHA-256 shown in chat.

## 6. Open questions for the owner (from this review, 2 Oct)

1. (Answered: Fedora-only now; a dual-boot plan is to be prepared.) When the dual-boot plan exists: may LUN 0's
   partition table be changed once, under that plan?
2. May the install U-Boot carry an AVB hash footer signed with a test key (R-1)? It changes no other partition.
   (Answered in practice by the install: the footered image was started by ABL on 13 Oct.)
3. (Answered: yes, probe write 2 first.) Remaining: who runs the probe's undo, and when is the probe's evidence
   enough to proceed to write 1? (Answered 10-13 Oct: the C0 probes were run and undone; the install followed.)
4. May the exact install U-Boot be RAM-booted once before write 1, read-only, as on 28 Sep (R-4 suggestion 3)?
5. Unattended U-Boot fallback: power off after a timeout, or wait with the screen on (R-6)? (Answered in the install
   build: a 600 s idle limit, then power off.)
6. Is a "back to LineageOS" path needed, or is "back to stock OxygenOS" enough (R-5)? (Still open.)

## 7. Status of every finding after the install (14 Oct 2026)

| Finding | Status on 14 Oct | What the install showed |
|---|---|---|
| R-1 AVB footer | **closed by the install** | ABL started the footered `boot_b` after write 2; Fedora booted from it at 20:48 on 13 Oct. The rerun on today's images and the record of the footer's result are in the install record |
| R-2 undo file | **closed** | The guide's Part A undo file was the one available; no undo was needed. The plan's older text still says "from the backup" (unverified whether all copies were corrected) |
| R-3 write order | **partly closed** | The C0 probes ran on 10 Oct (U-Boot into `boot_b`, each undone; the last probe passed at 17:41). The two writes followed on 13 Oct. The sources do not settle the order of the tethered boots against the writes (unverified). Write 1 ended Android's data as the review said it would |
| R-4 rehearsal build vs install build | **closed in practice** | The install build's UFS path ran for the first time in the C0 probes on 10 Oct (its boots from `boot_b`), before the writes. The plan's older text remains (unverified how much was rewritten) |
| R-5 dual boot / LineageOS | **Fedora-only, as decided; the back-to-LineageOS path is still open** | Android's data was replaced by write 1, and Android does not start on the tablet any more. Dual boot is a draft (`docs/DUALBOOT-PLAN.md`) and not started |
| R-6 unattended U-Boot | **fixed in the install build** | 600 s idle limit, then power off (patch 0007). Not recorded separately on the tablet (unverified) |
| R-7 boot order; `efisp` | **boot order fixed; `efisp` still not inspected** | Fedora's disk is booted through the explicit option in the install build (per the install record; unverified on the tablet). The `efisp` file list is still open |
| R-8 guide behind plan | **closed for the guide** | The guide is the B149 edition, which was followed for the install. The plan's older text remains |
| R-9 recovery rows | **open (unverified)** | No recovery case was met on the tablet in the sources; the rows should be checked against the B149 guide |
| R-10 device tree | **open (unverified)** | The sources do not say whether the GRUB per-kernel line or the ESP copy is in use on the installed system |
| R-11 initramfs and firmware timing | **closed on the installed system** | Sound, the sensors and the battery guard work on the installed system; the ADSP and CDSP run. The rehearsal lines were the proof |
| R-12 smaller points | **partly closed** | The charge limit (80 / 85 %) works on the installed system. Return to stock is still never run. The other smaller points are open (unverified) |
| New: GPU firmware | **closed by the owner's decision** | The linux-firmware set is in the image as decided |
| New: A/B flags and the countdown | **observed; open** | The retry count fell to 3 on the installed system (N-1 below). The fix is in 0.28-8, not yet in an image |
| New: footer values to the TEE | **fixed** | Carried in the footer; not separately verified on the tablet (unverified) |
| New: R1 fix | **closed** | The rehearsal reached the desktop and the install boot path runs |

**New findings from the install:**

- **N-1 (High, open): the installed boot tool did not mark the slot.** `iceland-slot-mark` refused the loop root that
  the installed system uses, so Fedora never called `qbootctl -m`, and ABL's retry count for slot b fell to 3 by the
  evening of 13 Oct. The owner marked slot b by hand on 14 Oct, after GPT safety copies. The fix is iceland-device
  0.28-8 (committed 946ff95, PC tests only). The fix is not yet in an image or a rehearsal, and only its thermal file
  was installed on the tablet by hand. Check: after the 0.28-8 image is installed, the slot's flags must stay
  successful across reboots.
- **N-2 (open): DisplayPort over USB-C.** A portable 4K monitor gets HPD, EDID and a DP-1 mode, but no picture, and the
  DP pipeline times out at disable. The monitor's bus power may be above the 2 A contract (unverified).
- **N-3 (open): an Electron app's GPU process crash loop.** It fell back to software rendering and was the largest
  load on the first evening (13 Oct), with Wi-Fi power save switched off for a test. The 60 s power report of 14 Oct,
  with Wi-Fi power save on and one Electron app open, gave a 2.08 W average.
- **N-4 (confirmed): the write sizes.** The sparse image unpacks to exactly the `userdata` size, as R-8 requires; the
  owner's write reported OKAY.

## 8. The install of 13 October 2026 and what it showed

**The two writes** (the owner ran each one after the partition, the file, its size and SHA-256 were shown in chat and
confirmed; the sources give the times and the results):

| Write | Partition and file | Size and hash | Time | Result |
|---|---|---|---|---|
| 1 | `userdata` <- the final golden B149 install image (sparse, 9 pieces) | 6,732,251,564 bytes (sparse); unpacks to 237,159,641,088 bytes (the `userdata` size); SHA-256 prefix `2246e9a7` | 18:31; 267 s | OKAY |
| 2 | `boot_b` <- the footered U-Boot install build v3 | footered SHA-256 prefix `4955ee98` (AVB-PROOF PASS; the unfootered build `979b4076`, 540,672 bytes); the footer's record is in the install record | 20:47; 2.3 s | OKAY |

The image itself is not published (it carries the tablet's own firmware extraction). The hashes are public facts.

**Before the writes (13 Oct):** the backup of all 151 partitions was intact and checked; the stock images were intact;
the return-to-stock dry run was done (the plan: the stock boot set on both slots, `super` restored, `userdata` and
`metadata` erased, slot a set active; never executed); a second copy was verified. The slot flags were read first: slot b
not successful, not unbootable, retry count 6; slot a successful and unbootable. The rehearsal image B149 was committed at
15:45 after rehearsal r158 (64 rows, 0 FAIL) and the install image was rebuilt and held at 17:02 (an offline check of 128
PASS, 0 FAIL).

**After the writes:**
- Tethered boots at 20:43-20:44, then Fedora from `boot_b` on its own at 20:48, after the first-boot setup by the owner
  (their account, the desktop).
- The installed system: Fedora 44, GNOME Shell 50.5, kernel `7.3.0-rc7-iceland-00426-g520e85da9244` (package
  `kernel-iceland 7.3.0~rc7.iceland.00426`), `iceland-device` 0.28-7 (and 0.28-8's thermal file by hand), `iceland-firmware`
  11.A.38-3, libcamera 0.7.1-2, Mesa 26.2.4.
- The chain as installed: ABL -> `boot_b` (U-Boot v3, footered) -> the EFI boot manager on `userdata` -> Fedora's shim and
  GRUB -> `kernel-iceland`. The root is btrfs on a loop device over `userdata`.
- 14 Oct: slot b marked by hand (N-1); the power report (2.08 W at idle); the DisplayPort check (N-2); the feature matrix
  at page v62 (83 working, 13 in progress, 5 not started, 3 not planned, of 104 rows).

**What the install showed.**
- The review's central worry (R-1, the footer) did not materialise: the footered image was started and the tablet
  booted Fedora from `boot_b`.
- The worry about the ABL retry counter (R-3, the "countdown") was right: the flash reset the flags and nothing marked
  the slot successful on the installed system. The cause was not ABL but the project's own slot-marking tool, which
  refused the loop root. That is a new finding (N-1), and it is the one open item of the install that needs watching until the fix is in an
  image.
- The loop root works as the plan described (the root on the loop device; the other LUNs read-only to the running
  system, and the boot LUN read-only except for the one command that marks the slot), but the tools' guards had been
  written for the rehearsal layout. Every guard in the
  installed path needs a check on the real layout, not on the rehearsal's.
- The image's size rule (R-8, the size must equal `userdata`) was right, and the write reported OKAY.

## 9. Open checks after the install (the owner's hands)

These come from the feature matrix and the install guide. They need the owner's hands or eyes; the project's tools
cannot do them.

1. Listen to the speakers after the install at 50 % and 100 % and compare with Android (the +9 dB make-up is the owner's
   choice).
2. One night unplugged with the cover closed; note the battery at evening and morning (the drain logger is prepared,
   its timer is off by default).
3. Cover wake from sleep; USB host with a keyboard, a stick and a hub; a 5 GHz connection with the band recorded.
4. DP monitor: a picture (the monitor's own power, 1080p, a lower mode), then sound over DP.
5. Wall chargers (5 V USB-A, USB-C PD, the OnePlus charger) in one attended sitting.
6. Pen (tip, hover, buttons, pressure); the keyboard cover (keys, touchpad, backlight, wake).

Work left on the PC (not owner checks, listed for completeness): the 0.28-8 image and its rehearsal rows (the thermal
rows and the slot-mark rows), the DP link logs, the camera into the encoder, Chromium / Electron GPU acceleration, the
idle-refresh debug round, and the 0.28-8 update of the installed system through the local repository.

# 06 - Process history: how the project got here, the method, the lessons

State: 14 Oct 2026. The history runs from 27 Sep to 14 Oct; section 1 has the timeline up to 2 Oct, section 1a the
timeline from 3 Oct to 14 Oct (loops 4 and 5, the rebases to Linux 7.3-rc7, the golden builds, the install on
13 Oct, the slot-mark fix on 14 Oct and the public release of the repositories).

Status (14 Oct 2026): the earlier entries of this file are kept as they were written on 2 Oct, with the corrections
marked where a later fact changes them. The running logs the entries came from (the worklog, the save points, the
workflow briefs and the kit logs) are not published; the public record is the feature matrix, the install guide, the
knowledge base and the repositories' history.

Sources for the entries up to 2 Oct: the project worklog (entries 1-44), the dated save points of 28 Sep - 2 Oct, the
knowledge base (sections 10-15), and the workflow briefs. For 3-14 Oct: the fact sheet of the 14 Oct documentation
refresh, which was built from the worklog and the loop 5 log.

## 1. Timeline

All dates 2026. "Run N" = kit run `area-combo-N`; "qNN" = test kernel NN.

| When | Phase | What happened (evidence) |
|---|---|---|
| 27 Sep | Discovery, backup | The boot loader unlocked by the owner. Read-only captures of stock OxygenOS 11.A.38 (device facts, firmware manifest). A full checksummed backup of all 151 partitions except `userdata`, taken under a temporary DSU system for root. Repositories created; first commit 27 Sep 23:34 |
| 28 Sep | LineageOS | LineageOS 24.0 (unofficial build) flashed by the owner's own scripts: boot images to slot a, the OTA to slot b, firmware copied to both slots (anti-rollback window closed). The tablet runs LineageOS on slot b since |
| 28 Sep | Plans v1-v4 | A cloud session ("Mainline") studied the reference ports (infiniti / OnePlus 15, map220v's iceland tree, troikoss, aaronsb, PrestarLin, y700) and wrote plan v3 (one kernel for any rootfs, U-Boot like the OnePlus 15). Plan v4 came in the evening: **Fedora 44 GNOME**, the owner's choice at 20:38 |
| 28 Sep | Phase 1: U-Boot | Diagnostic runs 1-4. ABL accepts `fastboot boot`; the U-Boot device tree must sit inside the gzip; U-Boot reads the UFS GPT; the boot manager finds nothing in Android's `userdata` and falls back to fastboot (the run 4 log is not published) |
| 28 Sep | Phase 2: first Linux | Linux tests 1-7: `bootefi` instead of `bootm`, USB NCM network, the white screen. The cause: the display power domain INT2 switched off by genpd `sync_state` (found by the PC session in relay kit pc-001, queue 0022) |
| 28 Sep | Phase 3: PC relay kits pc-001..pc-024 | CPU thermal trips (pc-002/003); native display (pc-007); touch firmware (pc-008); Wi-Fi + BT (pc-009/010); battery over pmic_glink + GPU power-up (pc-011); the "early reset" bisect, which turned out to be the kit's own `/dev/mem` sampler (pc-016..022); **Fedora 44 in RAM, Wayland, and a full GNOME session from a cold RAM boot at 22:38** (pc-024 Y7-Y10) |
| 29 Sep | Critical items (owner: battery, PM, thermals, sleep, sound, Wi-Fi, BT first) | pc-026 S1-S3: suspend fixed (PCIe WAKE# polarity, queue 0040); ADSP up after the root hand-over (firmware bind); **audio root cause**: the stock ADSP has no Audio-IF module, so the speakers go through TDM as on stock (queue 0038-0051) |
| 29 Sep 21:40 | Hand-over (relay 020) | The PC session owns the whole project (queue, packaging, docs, matrix). Charging safety first: queue 0053 |
| 29-30 Sep | Areas | area-display-1..8: 144 Hz, the refresh-rate black screen (CTL_START, queue 0058), the pink UBWC glitch (queue 0060). area-thermal-1/2: battery guard and thermal protection. area-graphics-1..3: dEQP / WebGL. area-wifi-1..3, area-usb-1 |
| 30 Sep | The ~60 s freeze | Fast PC -> tablet USB traffic while CPUs may power-collapse hangs the SoC. Root-caused over 14 sessions and 7 test runs; fixed with a CPU-latency hold while USB is up (queue 0063). The lighter busy-only variant (0064) froze once in five and was reverted (0065) |
| 30 Sep | Video (owner's item 5) | Iris decode bit-exact against AOSP's reference MD5s. The **green picture** came from `CONFIG_DMABUF_DEBUG` (config fix 92047dc) |
| 1 Oct | Save point 2; model change (Fable 5.1) | Everything committed; project snapshot folder created |
| 1 Oct evening | **Campaign 2** (owner: NPU + video leftovers + camera / Wi-Fi / USB idle + microphone meter, "until green") | Runs 1-10: the NPU runs unsigned programs (CDSP); the microphone fixed (a stale UCM in the RAM image, plus +12 dB as stock's DSP); Wi-Fi 5 GHz fixed (no SBS as stock, queue 0066-0068); camera first light (raw frames from both sensors). The first five background **workflows** started (about, battery, sleep, cpupower, rotate) |
| 2 Oct 00:00-07:30 | Runs 11-37 | Battery estimate (0071-0072); 37 clean s2idle cycles; the sensor programs packaged as RPMs; libcamera on both cameras (0073); the camera-bus mystery (runs 26-34); five more workflows (bcl, charging, chargelimit, gpucool, thermal) and the first INSTALL-PLAN |
| 2 Oct 07:30-10:05 | Runs 38-47 | Stuck CPU limits fixed (0077); charging as stock (0078-0080); camera bus level shifters (0084-0086) and focus motor (0087-0089); iceland-device 0.16; round-4 workflows started (pencharge, pogo, deepsleep, wake, apps, audit, pkg017, install); the flashing guide (INSTALL-GUIDE) |
| 2 Oct 10:05 | Hand-over to a new model (Opus 5.5) | A handover note written; all agents resumed (worklog entries 28-29) |
| 2 Oct 10:00-16:00 | Runs 48-76 | Pogo and pen charger proven without accessories (0090-0097); the Camera app works (the DMA-heap rule); audit kit A / B queued (0099-0112); wake sources (0098, 0115-0116); **CX collapse 98 %** (0113-0114); device package 0.17 committed; install G13 closed (rehearsal U-Boot without UFS); apps 33 of 33; hardware inventory; measured battery life (run 69); NPU cooling (0117-0124) |
| 2 Oct 16:00-19:50 | Runs 77-93 | quick wins (0125-0138); upstream fixes (0139-0161); **the f_ncm USB upload bug** found and fixed (0162; the tablet -> PC direction went from under 0.3 to about 40 MB/s); power telemetry (0163-0166); the GPU ISP workflow finished; **the install B run passed** (run 93) |
| 2 Oct 19:38 | R1 | The first rehearsal boot stopped in the rehearsal U-Boot (`blkmap create` subcommand table). The owner restarted the tablet; nothing was written. Fixed in round 5; a helper ("r1debug") verifies the fix |
| 2 Oct about 20:00 | Documentation, boot log, decisions | This document set and its install review (R-1..R-12, `07-INSTALL-REVIEW.md`). The boot-log review (77 groups, no WARNING / Oops; not published). B rerun with device package 0.18 passed (run 94). Owner decisions: Fedora-only for now, with a dual-boot plan to prepare; the write-2 probe first, run by the owner; ask before every tablet action |
| 2 Oct about 20:30 | Charge limit, commits | Run 95 (the owner's charging sitting): "Preserve Battery Health" and "Maximize charge" confirmed by the owner, then the wall-charger part skipped. Commit t (matrix c2s; the boot-log review corrected: the battery does not need the ADSP). Commit u, iceland-mainline 1c417e9: the docs drafts as `docs/guide/`, project knowledge, the kits' module list |
| 2 Oct about 21:00 | R1 verified, install agent handed over | The r1debug helper (another model) confirmed R1's root cause and the install agent's U-Boot fix 15 / 15 in its own U-Boot sandbox. It proposed a "busy U-Boot" probe for `rehearse.ps1` and an 8 KiB "not gzip" test head as the first tablet step. The install agent wrote a round-6 handover record and a new install agent took over |
| 2 Oct about 21:00 | AVB proven on the PC | Install round 6: a libavb harness modelled on Qualcomm's public ABL. A plain U-Boot in `boot_b` gives INVALID_METADATA (ABL stops, slot b unbootable); with an AVB footer it gives PUBLIC_KEY_REJECTED (continues, as LineageOS does today): AVB-PROOF PASS. Also: U-Boot powers off after 600 s idle (patch 0007); an explicit EFI boot option for shim; the Part A reader / checker; B1 / B2 / B3 / B4 fixes. The backup's `efisp` is all zeros |
| 2-3 Oct night | The rehearsal reaches the desktop | Run 97 / 99: the PCIe L2 line at suspend is upstream behaviour (keep it). R1b: the USB link dropped 5 s after the network disk connected (UCSI came after switch_root); R1c: a test-only initcall blacklist left the panel unmanaged and the tablet lost power (no PS_HOLD reset) - withdrawn; the revised design puts the SoCCP / ADSP / CDSP stack into the initramfs. **R1d: the first complete rehearsal boot to the desktop.** R2 (SELinux enforcing) 29 PASS. The release candidate (q83 = 0174 + camera driver, input-suspend lever, pen-charger grace, snd-seq, touch follower, nftables, hung-task; iceland-device 0.19): R2-final r2f 40 / 2 / 1, r2g 42 / 1 / 1; runs 101-105. Owner decisions: camera driver + stock-derived tuning into the private repos, Wi-Fi country US, no Wi-Fi in sleep, bypass charging later, auto-rotate works on the installed image; the Camera app crashes (F1) |
| 3 Oct from 03:00 | The team | Owner: "stop building, fix everything first basis on the logs", then "a whole team of agents ... an automated process ... to reach a complete working build". The r2g logs consolidated as F1-F23 (the fix list is private); one error ledger, one fix record per finding, gates G0-G4 (found, ready, built, proven, committed); one consolidated build (q84), kit, build run and rehearsal per loop (`docs/TEAM-PLAN.md`). Roles: ledger, fedtest (debugger), review, builder, install, camfix, klog, docs |
| 3 Oct 03:00-09:00 | The final build | One consolidated kernel q84 (`7.3.0-rc4-iceland-00313-gba2ed250bf33`) from the fix records: kit 106 (the charger input cut v3.1: lever, guard and restore PASS, 219 unit checks; sleep PASS), kit 108 (sleep PASS; the kit's U-Boot still passes the `*_ignore_unused` flags, so the installed system's sleep without them is an owner check). `iceland-device` 0.19: B run 107 30 / 1 (a dracut TPM unit; F10 amended), B run 109 **31 PASS, 0 FAIL**. Final rehearsal **r2h: INSTALL-ACCEPT 45 PASS, 0 FAIL, 0 CHECK**, the debugger's suite 29 PASS, the Camera app works (PipeWire 1.6.9), the rehearsal guard ran its full 1500 s. Queued as **0175-0185** (iceland-linux cd0bf55). The ledger's G3 check (r2h against r2g): the fixed findings pass; F5 deferred (libcamera sensor data), F18 the next loop (kernel q85 with the wcd939x fixes, kits 110 / 111), F12 / F17 / F31 await the next run (probe lines), F39 / F40 / F41 benign (debugger and reviewer). Commit x: runs 101-109, the install documents' final edition, release notes, matrix c2v |
| 2 Oct about 21:30-22:30 | bootfix topic B queued, topic A diagnosed | Run 96 on q79: 9 of 9 PASS. Queued **0167-0174** (iceland-linux a88cf03): WCN7860 supplies, backlight vddio optional, VA DMIC rate, FastRPC heap, UFS MCQ, the smem DRAM-info backport (author kept) + overflow fix, the touch message. Topic A: the PCIe L2 timeout comes from ath12k's suspend-time chip reset; diagnosis kit **run 97** (q80, test-only switch) started. Topic C (bypass charging) in progress. The install agent's verified next commands were kept with the install tooling (not published) |

Totals by 2 Oct evening:
- 138 SM8850 base patches + 174 Pad 4 patches;
- 97 `area-combo` runs, plus the earlier relay kits and area runs (about 145 test runs in all, matrix c2s);
- test kernels up to q80;
- feature matrix 61 / 12 / 5 / 2 of 80.

## 1a. Timeline from 3 to 14 October 2026

Dates are from the fact sheet of the 14 Oct refresh; where a date is approximate it says so. The golden builds
("B" numbers) are the images of the rehearsal; "r" numbers are the rehearsals that accepted them.

| When | Phase | What happened |
|---|---|---|
| 3 Oct, later | Loops 1-4 | q85 release candidate: golden B112 with rehearsal r2i (46 PASS, 0 FAIL); q86 with 802.11d off; golden B118 for r2j. Loops 1-4 ran to 9 Oct (boundaries approximate) |
| About 8-9 Oct | Fresh-boot rehearsal | r2m (golden B123) showed the microphone stall (3 of 10 fresh opens came back empty). The image was held; the fix was queued as q87 |
| 9 Oct | Loop 5 | starts, from the loop 4 hand-over |
| 10 Oct | Upstream scan, rc6 rebase | upstream scan by hardware block; the queue rebased to Linux rc6 (q89 -> q89b); the microphone replay passes on q89b; golden B130 (q89b + 0.24) confirmed |
| 10 Oct | tb323fu | the tb323fu patches added (q89c-tb) |
| 10 Oct | Install day, first part | C0 probes: U-Boot into `boot_b`, undone each time; probe #4 passed at 17:41 |
| 11 Oct | Audio, holds, rehearsal | speaker chain at stock (0.27r6); minimal holds (libcamera, GRUB, firmware kept from Fedora); rehearsal B141 (r139) with 4 FAIL, including the Bluetooth race (fixed in iceland-device 0.28-2); the SuperTurtleDev items added (q89d series); kernel q89d8 |
| 11 Oct | Firmware decision | the owner allows the generic firmware to be published in a dedicated repository, with sha256 and notices; unit data stays private |
| 12 Oct | Golden B143 and the first clean final rehearsal | r139c: 36 rows, 0 FAIL. Sound make-up +8, then +9 dB (the owner's choice). Firmware repository public (release 11.A.38-2). Golden B145 (q89d9 + 0.28-3) accepted by r141 (48 PASS; the one FAIL was a test expectation, fixed). Skin policy proven (r150b). libcamera 0.7.1-2 proven (r152). The rc7 rebase starts (q89e). The decoded generic thermal model published in firmware 11.A.38-3 |
| 13 Oct, 06:02 | Golden B147 | q89e (Linux rc7) with the 0.28-5 microphone chain, accepted by r156 (G4 F54 the one FAIL; gone with libcamera 0.7.1-2) |
| 13 Oct | Brightness | the probe r151 confirmed the fight between the panel brightness and GNOME; the kernel clamp was chosen. q89f and q89g (kernel brightness clamp, K3 retry, K6 wake, K7 lens; idle refresh compiled in, off); iceland-device 0.28-7 |
| 13 Oct, 15:45 | Final golden B149 | committed after rehearsal r158 (64 rows, 0 FAIL, no regression against r141); 1,727 packages |
| 13 Oct, 17:02 | Install image | rebuilt from B149 and held after an offline check (128 PASS, 0 FAIL). The image is not published |
| 13 Oct | Install-day checks | the backup and the stock images intact; the return-to-stock dry run (never executed); the second copy verified; the slot flags read (slot b not successful, retry count 6; slot a successful and unbootable) |
| 13 Oct, 18:31 | Write 1 | `userdata` written by the owner (267 s, OKAY) |
| 13 Oct, 20:43-20:44 | Tethered boots | the installed image started tethered (times only; see `03-BOOT-AND-PARTITIONS.md` section 8) |
| 13 Oct, 20:47 | Write 2 | `boot_b` written by the owner (2.3 s, OKAY) |
| 13 Oct, 20:48 | First own boot | Fedora booted from `boot_b`; first-boot setup by the owner (their account, the desktop) |
| 13 Oct | Repository clean-up | the `iceland-mainline` history was rewritten to remove test material (the removed paths are not linked from the guide); other repositories followed |
| 14 Oct | Slot marking by hand | the retry count of slot b had fallen to 3: the installed boot tool skipped every boot on the loop root. The owner marked slot b by hand with `qbootctl` after GPT safety copies |
| 14 Oct | iceland-device 0.28-8 | committed (946ff95): the slot-mark fix for the installed layout, the screen-off thermal table, the stock boost ceiling. Its thermal file installed by hand; not yet in an image |
| 14 Oct | Power and display checks | a 60 s power report on the installed system: 2.08 W average at idle. DisplayPort over USB-C: HPD and EDID work, no picture yet |
| 14 Oct | Feature matrix | page v62; the working rows are published as `docs/FEATURES.md` |
| 13-14 Oct | Public release | the other repositories purged of test material and made public; the owner's six repositories public as of 14 Oct |

**Totals by 14 Oct:**
- the kernel queue is 426 patches on Linux 7.3-rc7: 132 infiniti (base) and 294 Pad 4 patches (q89g, tag `q89g`);
  the earlier totals of 2 Oct (138 base, 174 Pad 4 on rc4) are superseded;
- goldens B112, B118, B123, B130, B143, B145, B147, B149 (the install image is B149); rehearsals r139c to r158 for the
  final builds;
- firmware package 11.A.38-3 (generic files only); iceland-device 0.28-8 in the repository;
- the install done on 13 Oct; the feature matrix 83 / 13 / 5 / 3 of 104.

## 2. The method

### 2.1 RAM kits (every test)

1. **Build.**
   - The kernel: the build scripts (`build-q2.sh` / `build-q56.sh`) on a local branch of the kernel source tree (the queue head +
     candidates). It produces `bin<tag>/` and `modstage<tag>/`.
   - The kit: `prep-area-combo-N.sh` -> `make-kit26.sh` (U-Boot diag L + the Linux image + firmware + a Fedora
     root fetched over USB).
2. **Generate.** A kit generator derives the tablet script, the PC probe and the prep script from a template run,
   and a checker verifies them before a run.
3. **Run in the background.** A chain script:
   - stops old runners;
   - waits for Android (and, since 2 Oct, for at least 40 % battery);
   - stages the kit to the PC's ADB tools folder and verifies its `SHA256SUMS`;
   - starts the webcam watcher if used, and the runner (a Windows script: RAM boot + live kmsg streams);
   - launches the probe, which does ssh, asserts `uname -r`, runs each test part, fetches the log set and reboots
     the tablet to Android.
4. **Judge** from the probe log's summary lines and `area-combo-N/combo/<part>/`.
5. **Queue** what passed: `queue-00NN.sh`.
   - One commit per logical change; the tree must equal the tested kernel's tree; dry run first.
   - Then fast-forward `iceland`, `format-patch` into `iceland-linux`, update `kernel.pin`, verify with
     `prepare.sh` from the local base, commit, push.
6. **Record:**
   - a WORKLOG entry;
   - a `research/matrix-c2X.py` update of the feature matrix, then `build.py`;
   - a commit script with privacy guards (serial, addresses, SSIDs, blobs, rpm files);
   - republish the matrix page.

### 2.2 Workflows (since 1-2 Oct, the owner's order)

"In separate workflows ... use autonomous agents till they are working" (the owner's standing order, 1 Oct).

- **One background agent per open topic** prepares on the PC only, in its own work folder (not published):
  - `REPORT.md`, `NEXT.md` (what to build and run, the pass criteria);
  - `tablet.sh` (one function `wf_<name>`, one summary line);
  - candidates (kernel changes as Python patchers with exact-string asserts);
  - private material, kept apart from anything that could be published.
- **Agents never touch the tablet, never build kernels or kits, never commit.**
- **The main session** reviews every write and limit (charging safety first), builds, runs the test in a kit run,
  sends the result back with precise questions, and repeats until green. Then it queues and commits.
- Briefs: five briefs (round 1, the general rules, the camera, round 4, round 5). They are not published; the
  prompt template is kept in the handover record.
- Workflows so far:
  - round 1: about, battery, sleep, cpupower, rotate;
  - round 2: bcl, charging, chargelimit, gpucool, thermal;
  - camera;
  - round 4: pencharge, pogo, deepsleep, wake, apps, audit, pkg017, install;
  - later: hwinv, quickwins, telemetry, npucool, gpuisp, upsync, r1debug, docs, hwfix (bootfix + bypass).
  - The install workflow changed model on 2 Oct evening through a written handover
    (the round-6 handover record). Agents may also consult the docs agent and the r1debug agent directly.

### 2.3 The rules the work follows

See `01-OVERVIEW.md` section 3. In short:
- RAM boot only; nothing written to the tablet;
- every hardware value from Pad 4 stock sources ("rule 13");
- charging safety first;
- tests automated and at most about 10 minutes; anything needing the owner is deferred;
- private data never committed;
- commits as the owner with `Signed-off-by`;
- "hold the tablet" stops everything.

## 3. Key findings and decisions

| Date | Finding / decision | Why it matters | Where |
|---|---|---|---|
| 28 Sep | ABL accepts `fastboot boot` of header-v4 images; U-Boot's device tree must be inside the gzip | the whole project can run from RAM | tests README, diag run 3 |
| 28 Sep | genpd `sync_state` ignores `pd_ignore_unused`: anything ABL left on without a DT consumer is cut (the display's INT2 GDSC) | first native display | KNOWLEDGE section 12, queue 0022 / 0026-0027 |
| 28 Sep | The "early resets" were the kit's own `/dev/mem` sampler touching display registers during the hand-over | never poke driver-owned registers from user space | pc-016..022 |
| 28 Sep 20:38 | **Fedora 44 + GNOME** (Mesa 26 has the first Adreno gen8 support) | target OS; never pmOS / Debian / Ubuntu for this tablet | project decision note |
| 29 Sep | PCIe WAKE# declared active-high on an active-low line kept s2idle from sleeping | suspend works | queue 0040 |
| 29 Sep | The stock ADSP has no Audio-IF module; speakers run on TDM like stock | sound works | queue 0038-0051 |
| 29 Sep | The PC owns the project; charging safety before anything else | ordering of all later work | relay 020 |
| 30 Sep | Live refresh-rate changes blanked the panel: a CTL_START written after the video engine was switched off | 30-144 Hz live | queue 0058 |
| 30 Sep | Pink / blocky GNOME glitches: the splash take-over reset the display block and programmed UBWC before it was out of reset | clean first login | queue 0060 |
| 30 Sep | **The freeze:** fast USB OUT traffic while CPUs may power-collapse hangs the SoC; hold 2 us CPU latency while USB is up (stock holds it only while busy; that variant froze) | stable sessions; costs idle power only with a data cable | queue 0063, 0065 |
| 30 Sep | `CONFIG_DMABUF_DEBUG` strips pages from importers' tables, so the GPU showed hardware-decoded frames green | correct video | config 92047dc |
| 1 Oct | Wi-Fi 5 GHz lost because the firmware scanned in SBS mode on a second radio without a 5 GHz path; stock sends `enable_sbs=0` | 5 GHz found | queue 0066-0068 |
| 1 Oct | The microphone: a stale UCM in the RAM image; stock adds about 12 dB in its DSP | microphone level as stock | UCM TX_DEC 96 |
| 2 Oct | The camera bus is cut by two PMIC level shifters (RPMh XOB resources LS1B / LS2B) that only the sensor hub happened to vote | cameras without the hub | queue 0084-0086 |
| 2 Oct | The Camera app failed because four 1080p frames do not fit the 32 MiB CMA heap; the CMA heaps are made root-only | GNOME Camera works | iceland-device rule `71-iceland-dma-heap.rules` |
| 2 Oct | The step-wise thermal governor kept a stale limit (CPUs stuck at half speed after a load) | performance after heat | queue 0077 |
| 2 Oct | CX collapse needs the Wi-Fi PCIe port in D3 (no hot-plug slot bit) and the DSI PHYs releasing their clock; AOSS sleep is out of reach (the secure processor has no mainline driver) | deep sleep 95-98 % | queue 0113-0116, the deep-sleep tests |
| 2 Oct | Stopping the CDSP costs CX collapse until reboot | never stop the CDSP; device package 0.18 keeps it running | area-combo-66/-67 |
| 2 Oct | The official Fedora image is laid out for 512-byte sectors, the UFS has 4096; the root grows only with a GPT | the image builder re-lays the image | install review, findings 1-2 |
| 2 Oct | The rehearsal must be unable to touch the storage (G13) | a separate U-Boot build without UFS for rehearsals | WORKLOG 37 |
| 2 Oct | **f_ncm drops its NTB flush when all IN requests are busy**: uploads with traffic both ways collapse | the network-disk rehearsal works (38.6 MB/s writes) | queue 0162, runs 85 / 86 / 90 |
| 2 Oct | fwupd lists the UFS storage as updatable | a storage-firmware update is the one software path to a dead tablet: 17 plug-ins disabled | iceland-device 0.17 |
| 2 Oct | Remote-processor firmware is not reachable from the initramfs; the kits' scripts started the ADSP late | first B1 kept the remote processors out; after R1b / R1c (3 Oct) the SoCCP / ADSP / CDSP stack and its firmware are IN the initramfs, Wi-Fi / BT / video out | boot-log review, worklog 3 Oct |
| 2 Oct | A plain image in a chained `boot` partition is INVALID_METADATA for ABL; a footered one is PUBLIC_KEY_REJECTED | the install U-Boot carries an AVB footer; vbmeta stays untouched | install round 6, AVB-PROOF |
| 2 Oct | R1: U-Boot's sub-command table has its own maxargs, so a patched command was refused before it ran | every U-Boot failure path now returns to fastboot or powers off; never a prompt | r1debug REPORT |
| 2 Oct | The first golden image's initramfs lacked the GPU microcode (MSM is built in and loads it at bind time) | the trio goes into the initramfs; the owner chose linux-firmware's set (v5.3.23, as in every kit) over stock's (v5.3.39) | install B4 |
| 2 Oct | The PCIe L2 timeout at suspend: ath12k resets the WLAN chip at suspend, and it never answers PME_Turn_Off | diagnosis run 97 (it reset the tablet ~150 s into its suspend cycles, logs lost; a split re-run follows); stock keeps the WLAN firmware alive | the boot-fix review, topic A |
| 2 Oct night | Open ABL source: flashing `boot_b` resets its A/B flags (retry count to max, *successful* cleared); every normal boot of a non-successful slot counts down; only Android marks a slot successful | a permanent U-Boot in `boot_b` may run out of boots; C0 measures it; `recovery_b` is the fallback (owner's decision) | install round 6/7, CodeLinaro edk2 |
| 2 Oct night | ABL hands the TEE the footer's `os_version` and `security_patch` | the footer copies both from today's `boot_b` | install round 6/7 |
| 9-10 Oct | The microphone stall of the fresh-boot rehearsal (F55) was reproduced and then passed on the rc6 rebase (q89b) | the rebase carried the fix; the golden B130 confirmed it | worklog, loop 5 |
| 13 Oct | The microphone chain of 0.28-5: TX_DEC 84 (stock's value), the echo canceller, and a +14 dB processed chain as the default; raw source kept | microphone levels as the tested chain; fresh opens after idle stayed clean in the final rehearsal | iceland-device 0.28-5 and later |
| 11-12 Oct | Generic firmware may be published in a dedicated package with sha256 and notices; unit-specific data may not | the firmware repository (11.A.38-2, then -3 with the decoded generic thermal model) | owner's decisions of 11-12 Oct |
| 13 Oct | Brightness: GNOME's brightness control and the kernel's limit fought (probe r151 confirmed it) | the kernel brightness clamp was chosen (q89f / q89g); iceland-device 0.28-7 | rehearsal r151 |
| 13 Oct | ABL started the footered `boot_b` after write 2, and Fedora booted from it on its own | the AVB-footer design held on the real tablet | `03-BOOT-AND-PARTITIONS.md` sections 3 and 8 |
| 13 Oct | The installed boot tool (`iceland-slot-mark`) refused the loop root, so the slot's success was never marked and the retry count fell to 3 | the owner marked slot b by hand on 14 Oct; the fix is iceland-device 0.28-8 (not yet in an image) | `03-BOOT-AND-PARTITIONS.md` section 2 |
| 14 Oct | DisplayPort over USB-C: HPD and EDID work, but no picture with a portable 4K monitor | open; the power contract and the link are being checked | `02-HARDWARE.md` section 4 |

## 4. Lessons learned (the hard-won rules and their reasons)

From the project's working rules, the knowledge base (section 12) and the worklog:

| Rule | Why (what happened) |
|---|---|
| Never read every `/sys/kernel/debug/regmap/*/registers`; read one SPMI regmap, only the needed lines | an MMIO regmap of an unclocked block gives a synchronous external abort; run 4 (1 Oct) died that way |
| Never read TLMM pad registers through `/dev/mem` for pads Linux does not use | the reserved pins belong to the secure world; one scan reset the tablet at once (run 30) |
| Never poke driver-owned registers from user space | the "early resets" of 28 Sep were a sampler touching the display during its reset |
| Camera bus tests need the sensor hub configured first (`pkg2` + `rotpkg start`) | before queue 0084-0086 the cameras only answered while a hub sensor streamed |
| GNOME Settings from a script needs `XDG_CURRENT_DESKTOP=GNOME`; `gnome-screenshot` does not work on GNOME 50 | the webcam or AT-SPI is used instead |
| Write generator scripts as files; from Git Bash, `wsl.exe ... bash -c '...'` loses `$variables` and backslashes | silent changes to inline sed / python |
| Never `pkill -f` / `pgrep -f` a pattern that is in the calling command line | it kills its own caller |
| A kit description must not contain a quote character | it breaks the generated PowerShell |
| The queue is verified from the local kernel repository (`queue-0084.sh`) | the GitHub clone in `prepare.sh` stalled twice |
| The kit installs the repo's UCM over the RAM root at boot | the RAM image carried a stale UCM: a flat microphone meter for days |
| Never count kmsg patterns without excluding the kits' own `iceland-combo` lines; "WARNING\|BUG\|Oops" case-insensitively matches "ramoops" and "debug:" | false failures |
| Never edit a script a running bash is still reading | `run-chain.sh` got a syntax error mid-run |
| No WSL builds while a network-disk run is active, and no `wsl --shutdown` | the NBD server shares the VM |
| A hwdb entry needs `udevadm control --reload` before the re-trigger; UPower reads the thresholds once at start | the charge-limit switch was hidden |
| Re-trigger udev for driverless devices in kits ("coldplug") | the sound card waited for the DP audio codec (runs 83 / 87) |
| A root in RAM moves the kernel firmware loader's root with PID 1; bind `/lib/firmware` into it | the ADSP was "not found" after the hand-over |
| Never `switch_root` away from the busybox shim in a kit | its safety jobs die and the tablet resets about 45 s later |
| Unattended kits need a way back: watchdog, auto reboot, an RTC alarm armed for a sleeping kit | a kit that suspended without a wake source waited for the owner's power key (29 Sep) |
| Two samples are not a location: test a mechanism with a variant that should move or remove the failure | the early-reset hunt |
| Foreground waits are backgrounded by the owner: use background jobs and completion notices | workflow efficiency |
| A log tarball fetched at the end of a session can be truncated: fetch mid-run and check with `tar -tzf` | lost log sets |
| Webcam only during kit runs; frames stay local and are deleted after the verdict | privacy |
| Ask the owner to connect the tablet and wait for the go before any tablet run; never leave a chain waiting on adb | the tablet is unplugged while it recharges (2 Oct) |
| A U-Boot command can be refused by its sub-command table's maxargs even after its parser was patched; test U-Boot changes in a sandbox of the same tree before a tablet boot | R1 stopped at a prompt that only the power button could leave |
| A boot loader path must never end at a prompt nobody can answer: every failure returns to fastboot, resets, or powers off after a timeout | R1, and the review's R-6 |
| A guard written for the test layout must be checked against the installed one: a loop root and a read-only boot LUN are not the rehearsal's layout | the installed slot-mark tool skipped every boot; the retry count fell to 3 (13-14 Oct) |
| Read the shell-estimate thermal reading against the skin sensor before tuning the policy | the 13 Oct reading was right: the estimate sat below the skin sensor |
| Rewrite the history before a repository goes public, then check every path and value in the public tree; old commit hashes change | the 13-14 Oct clean-up; cite only the current hashes (the fact sheet lists them) |
| Put a single owner-run write behind its own check in chat: partition, file, size, SHA-256, and one confirmation per write | the two writes of 13 Oct |

## 5. Where the evidence lives

| Evidence | Where |
|---|---|
| Public history of the project | the repositories' git history (the 13-14 Oct rewrite removed test material; commit hashes cited in older notes may have changed) |
| Current state | `docs/FEATURES.md` and `docs/features/` (the matrix), `docs/INSTALL-GUIDE.md`, `docs/KNOWLEDGE.md` |
| Kernel queue and its verification | `iceland-linux` (branch and tag `q89g`, `kernel.pin`, `patches/`, `scripts/prepare.sh`; the GitHub `main` branch is older and not the queue head) |
| U-Boot queue and install build record | `iceland-u-boot` (`uboot.pin`, `patches/`, `tools/install/` with the v3 record files) |
| Firmware package and its manifest | `iceland-firmware` (`MANIFEST.tsv`, `NOTICE.md`, releases 11.A.38-2 and 11.A.38-3) |
| Device facts (stock captures, masked) | `iceland-mainline/docs/device-facts/` |
| Not published | the backups and stock images, the full log sets and kit images, the camera traces and photos, the install image, the unit's own firmware and data, and the working notes of the workflows |

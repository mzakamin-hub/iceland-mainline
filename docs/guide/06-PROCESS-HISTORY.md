# 06 - Process history: how the project got here, the method, the lessons

State: 2 Oct 2026, evening. Sources:
- `C:\Users\lucne\OnePlusPad4-Mainline\WORKLOG.md` (entries 1-44, the running history);
- `docs/memory/iceland-resume-point.md` (dated save points 28 Sep - 2 Oct);
- `iceland-mainline/docs/KNOWLEDGE.md` (sections 10-15), `CHANGELOG.md`, `docs/tests/README.md`;
- `HANDOVER.md`, `STATE.md`, `CLAUDE.md`, the workflow briefs `docs/WORKFLOW-BRIEF*.md`.

## 1. Timeline

All dates 2026. "Run N" = kit run `area-combo-N`; "qNN" = test kernel NN.

| When | Phase | What happened (evidence) |
|---|---|---|
| 27 Sep | Discovery, backup | The boot loader unlocked by the owner. Read-only captures of stock OxygenOS 11.A.38 (device facts, firmware manifest). A full checksummed backup of all 151 partitions except `userdata`, taken under a temporary DSU system for root. Repositories created; first commit 27 Sep 23:34 |
| 28 Sep | LineageOS | LineageOS 24.0 (unofficial build) flashed by the owner's own scripts: boot images to slot a, the OTA to slot b, firmware copied to both slots (anti-rollback window closed). The tablet runs LineageOS on slot b since |
| 28 Sep | Plans v1-v4 | A cloud session ("Mainline") studied the reference ports (infiniti / OnePlus 15, map220v's iceland tree, troikoss, aaronsb, PrestarLin, y700) and wrote plan v3 (one kernel for any rootfs, U-Boot like the OnePlus 15). Plan v4 came in the evening: **Fedora 44 GNOME**, the owner's choice at 20:38 |
| 28 Sep | Phase 1: U-Boot | Diagnostic runs 1-4. ABL accepts `fastboot boot`; the U-Boot device tree must sit inside the gzip; U-Boot reads the UFS GPT; the boot manager finds nothing in Android's `userdata` and falls back to fastboot (`docs/tests/uboot-run4/`) |
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
| 2 Oct 10:05 | Hand-over to a new model (Opus 5.5) | `HANDOVER.md` written; all agents resumed (WORKLOG 28-29) |
| 2 Oct 10:00-16:00 | Runs 48-76 | Pogo and pen charger proven without accessories (0090-0097); the Camera app works (the DMA-heap rule); audit kit A / B queued (0099-0112); wake sources (0098, 0115-0116); **CX collapse 98 %** (0113-0114); device package 0.17 committed; install G13 closed (rehearsal U-Boot without UFS); apps 33 of 33; hardware inventory; measured battery life (run 69); NPU cooling (0117-0124) |
| 2 Oct 16:00-19:50 | Runs 77-93 | quick wins (0125-0138); upstream fixes (0139-0161); **the f_ncm USB upload bug** found and fixed (0162; the tablet -> PC direction went from under 0.3 to about 40 MB/s); power telemetry (0163-0166); the GPU ISP workflow finished; **the install B run passed** (run 93) |
| 2 Oct 19:38 | R1 | The first rehearsal boot stopped in the rehearsal U-Boot (`blkmap create` subcommand table). The owner restarted the tablet; nothing was written. Fixed in round 5; a helper ("r1debug") verifies the fix |
| 2 Oct evening | Documentation, decisions | This document set (`wf/docs/`) and its install review. The boot-log review (`docs/BOOT-LOG-PLAN.md`). B rerun with device package 0.18 passed (run 94). Owner decisions: Fedora-only for now with a dual-boot plan to prepare; the write-2 probe first. New workflows: **bypass** (stock-like bypass charging with a Quick Settings toggle) and **bootfix** (the PCIe L2 timeout, device-tree gaps vs stock). Run 95: the owner's charging sitting with wall chargers |

Totals by 2 Oct evening:
- 138 SM8850 base patches + 166 Pad 4 patches;
- 93 `area-combo` runs, plus the earlier relay kits and area runs (about 143 test runs in all, matrix c2r);
- test kernels up to q78;
- feature matrix 61 / 12 / 5 / 2 of 80.

## 2. The method

### 2.1 RAM kits (every test)

1. **Build.**
   - The kernel: `build-q2.sh` / `build-q56.sh` on a local branch of `~/mainline/build/src` (the queue head +
     candidates). It produces `bin<tag>/` and `modstage<tag>/`.
   - The kit: `prep-area-combo-N.sh` -> `make-kit26.sh` (U-Boot diag L + the Linux image + firmware + a Fedora
     root fetched over USB).
2. **Generate.** `gen-combo-N.py` calls `an/genwf.py`, which derives the tablet script `an/area-combo-N.sh`, the PC
   probe `an/area-combo-N-probe.sh` and the prep script from a template run. `an/chk.sh N` checks them.
3. **Run in the background.** A chain script:
   - stops old runners;
   - waits for Android (and, since 2 Oct, for at least 40 % battery);
   - stages the kit to `C:\platform-tools` and verifies `SHA256SUMS`;
   - starts the webcam watcher if used, and the runner (`relay-run-kit-early.ps1`: RAM boot + live kmsg streams);
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

"In separate workflows ... use autonomous agents till they are working" (HANDOVER section 1).

- **One background agent per open topic** prepares on the PC only, in `~/mainline/build/wf/<name>/`:
  - `REPORT.md`, `NEXT.md` (what to build and run, the pass criteria);
  - `tablet.sh` (one function `wf_<name>`, one summary line);
  - candidates under `cand/` (kernel changes as Python patchers with exact-string asserts);
  - private material under `priv/`.
- **Agents never touch the tablet, never build kernels or kits, never commit.**
- **The main session** reviews every write and limit (charging safety first), builds, runs the test in a kit run,
  sends the result back with precise questions, and repeats until green. Then it queues and commits.
- Briefs: `docs/WORKFLOW-BRIEF.md` (round 1), `-2.md` (general rules), `-3-camera.md`, `-4.md` (round 4), `-5.md`.
  The prompt template is in `HANDOVER.md` section 5.
- Workflows so far:
  - round 1: about, battery, sleep, cpupower, rotate;
  - round 2: bcl, charging, chargelimit, gpucool, thermal;
  - camera;
  - round 4: pencharge, pogo, deepsleep, wake, apps, audit, pkg017, install;
  - later: hwinv, quickwins, telemetry, npucool, gpuisp, upsync, r1debug, docs.

### 2.3 The rules the work follows

See `01-OVERVIEW.md` section 4. In short:
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
| 28 Sep 20:38 | **Fedora 44 + GNOME** (Mesa 26 has the first Adreno gen8 support) | target OS; never pmOS / Debian / Ubuntu for this tablet | memory `iceland-phase4-target` |
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
| 2 Oct | CX collapse needs the Wi-Fi PCIe port in D3 (no hot-plug slot bit) and the DSI PHYs releasing their clock; AOSS sleep is out of reach (the secure processor has no mainline driver) | deep sleep 95-98 % | queue 0113-0116, wf/deepsleep |
| 2 Oct | Stopping the CDSP costs CX collapse until reboot | never stop the CDSP; device package 0.18 keeps it running | area-combo-66/-67 |
| 2 Oct | The official Fedora image is laid out for 512-byte sectors, the UFS has 4096; the root grows only with a GPT | the image builder re-lays the image | wf/install REPORT finding 1-2 |
| 2 Oct | The rehearsal must be unable to touch the storage (G13) | a separate U-Boot build without UFS for rehearsals | WORKLOG 37 |
| 2 Oct | **f_ncm drops its NTB flush when all IN requests are busy**: uploads with traffic both ways collapse | the network-disk rehearsal works (38.6 MB/s writes) | queue 0162, runs 85 / 86 / 90 |
| 2 Oct | fwupd lists the UFS storage as updatable | a storage-firmware update is the one software path to a dead tablet: 17 plug-ins disabled | iceland-device 0.17 |
| 2 Oct | Remote-processor firmware is not reachable from the initramfs; the kits' scripts started the ADSP late | the installed boot must order it | BOOT-LOG-PLAN P1-a |

## 4. Lessons learned (the hard-won rules and their reasons)

From `CLAUDE.md`, `HANDOVER.md` section 6, `KNOWLEDGE.md` section 12 and the WORKLOG:

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

## 5. Where the evidence lives

| Evidence | Where |
|---|---|
| Running history, every step | `C:\Users\lucne\OnePlusPad4-Mainline\WORKLOG.md` (copy `iceland-mainline/docs/WORKLOG.md`) |
| State, rules, locations | `STATE.md`, `HANDOVER.md`, `CLAUDE.md` (project folder) |
| Save points and memory notes | `docs/memory/` (project folder) |
| Log sets of every committed run (masked) | `iceland-mainline/docs/tests/area-*/`, `linux-run*/`, `uboot-run4/` |
| Full log sets, kernels, kits | WSL `~/mainline/build/area-combo-N/`, `bin<tag>/`, `modstage<tag>/`, `kit/` |
| Relay-era results (28 Sep - 1 Oct) | `iceland-mainline/relay/results/` |
| Kernel queue and its verification | `iceland-linux` (`kernel.pin`, `patches/`, `scripts/prepare.sh`) |
| Workflow reports and candidates | WSL `~/mainline/build/wf/<name>/` (public parts copied to `workflows/` in the project folder) |
| Feature matrix | `iceland-mainline/docs/features/features-data.py` -> `FEATURES.md` + `feature-matrix.html` (published copy: claude.ai artifact GtN6zLRTeabVcyg3LirNBm) |
| Device facts (stock captures, masked) | `iceland-mainline/docs/device-facts/` |
| Private (never committed) | the backup and stock images (`C:\OnePlusPad4`), `build/fwsuper`, firmware trees, camera driver and traces, `wf/*/priv`, `build/.serial`, `build/.bdaddr`, webcam frames |

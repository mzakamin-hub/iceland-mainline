> **Status 14 Oct 2026 (read this first).** The sections below are the hand-over of 2-3 Oct and the
> loop 4 pointer of 9 Oct; they are kept as history. The current state:
>
> - **Fedora 44 GNOME is installed on the tablet** (since 13 Oct 2026). The owner ran the two install writes after the PC
>   checks: `userdata` <- the final golden B149 image (sha256 prefix `2246e9a7`, 18:31), then `boot_b` <- the footered U-Boot
>   install build v3 (footer sha prefix `4955ee98`, 20:47). Fedora has booted from `boot_b` on its own since 20:48.
> - **Kernel** `7.3.0-rc7-iceland-00426` (queue head q89g, tag `q89g`); **iceland-device 0.28-7** is in the installed image
>   and **0.28-8** (commit 946ff95) was installed by hand on 14 Oct (its thermal file only; not yet in an image or a
>   rehearsal); **iceland-firmware 11.A.38-3**; the feature matrix is page v62 (104 rows: 83 ok, 13 part, 5 todo, 3 out).
> - **Last golden and rehearsal:** B149 (committed 13 Oct 15:45), rehearsal r158 (64 rows, 0 FAIL). The install image was
>   rebuilt from B149 and held at 17:09 before the owner's writes.
> - **Workflows (section 3):** all of them are closed or superseded on 14 Oct. The bypass charging feature stays deferred by
>   the owner. The loop 5 team (9-13 Oct) ended with the install; its folders are not in the repository.
> - **Open items:** the owner's checks and the technical items in the status block of `INSTALL-PLAN.md` and in
>   `TODO.md`. The slot-mark fix (0.28-8) still has to be built into an image and rehearsed before the next image.
> - **Lessons added since 3 Oct:** (1) on 10 Oct the first install U-Boot reset itself from `boot_b` and used up the slot's
>   retries; the fixed build (patch 0008) was tested from RAM before any write. (2) On 13 Oct the boot counter did not mark
>   slot b: the installed root is a loop device on `userdata`, `iceland-slot-mark` refused it, and the owner marked slot b by
>   hand on 14 Oct. Any package that touches the boot LUN must keep it read-only except for the one `qbootctl -m`.
> - **Repositories:** all four public repositories were cleaned on 13-14 Oct (test documents, rehearsal scripts and debug
>   patches removed, history rewritten). Paths named below as removed are not in the repository any more.

> **Old resume pointer (3 Oct 2026, history; the file is not published):** read `RESUME-2026-10-03-1300.md` (last section "UPDATE 17:16 - IMAGE HELD") first** - loop 3 (q86 + P1 0.20) in progress, kit 116 results in `<pc-work>/build/an/autosave`, then B run 118 -> r2j -> queue 0189; on resume recall the bypass charging agent to implement the feature.

# OnePlus Pad 4 mainline Linux - hand-over (2 Oct 2026, about 21:00; state table and workflows updated about 23:30)

> **SAVE POINT 3 Oct 2026 02:45 (newest; read first):** the last block of `WORKLOG.md` ("SAVE POINT before a compaction") has the exact state, what is running (r2g + fedtest until about 02:58), the night's results (r2g 42 / 1 / 1; q83 = the final-build kernel; chgsafe v2 ready) and the next steps 1-8 (q84 -> kit 106 -> B 107 -> R2-final -> queue 0175-0179 -> commit x). The tables below are from 2 Oct 23:30.

Written for the next model / session. Read this file, then `STATE.md`, `CLAUDE.md`, the last entries of
`WORKLOG.md` (from entry 44 on: everything of 2 Oct afternoon / evening), the last block of
`docs/memory/iceland-resume-point.md`, and the boot-log plan (removed 13 Oct, not published). The draft documentation set (overview,
hardware, boot and partitions, build-your-own, porting, history, install review) is in the docs repo under
`docs/guide/` (source: WSL `<pc-work>/build/wf/docs/`).

## 1. What the owner has ordered (in force)

Earlier orders (still in force; full text in the 10:00 version of this file in git history and in WORKLOG):
"Test and debug ... until completed and totally green, update constantly the feature matrix and a work log"; keep iterating without asking for confirmation where the owner said so (quick wins, telemetry, NPU cooling).

Orders of 2 Oct afternoon / evening (verbatim):
- "update feature matrix with everything commited" (several times: after every proven result, rebuild + publish).
- "add another workflow to list all hardware that has no drivers or not working on the tablet" (done: wf/hwinv).
- "start combined workflows for items from 1 till 9, keep iterating without asking for my confirmation" (done:
  quick wins, queued 0125-0138).
- "check all errors in kmsg during booting and put a plan to resolve": done, the boot-log plan (removed 13 Oct, not published).
- "also fix pcie timeout and device tree gaps" + "spin a different agent specifically for pcie timeout, device
  tree gaps and bypass charging" -> the "hwfix" agent (wf/bootfix + wf/bypass).
- "yes lets test" = the write-2 probe FIRST (U-Boot into boot_b while Android's data is intact; undo =
  boot_b-before-install.img). Only after the AVB footer proof; **the owner runs every write themselves**.
- "remember that tablet will be disconnected while it recharges so make sure to tell me to connect it before
  testing anything" -> before ANY tablet action ask the owner to connect it and wait for their go; never leave a
  run chain waiting on `adb devices` in the background.
- "battery charge settings working fine (preserve, maximize charge) please commit" (done, commit t).
- "yes do 1-3 and skip this charge testing" (the wall-charger sitting is skipped for now; 1-3 = this commit:
  docs set, project knowledge, the kit module list).

Hard rules (full list in `STATE.md` and `CLAUDE.md`): RAM boot only - never flash, unlock, wipe, switch slots or
install; the owner alone runs any write; tests fully automated, at most 10 minutes each; every hardware value from
Pad 4 stock sources; charging safety first (never raise a limit); private data never committed; serial, MAC / BD
addresses and network names masked; commits as `the owner's name and address (not published)` with `Signed-off-by` and
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; `git pull --rebase` before push; never
`wsl --shutdown`; "hold the tablet" = stop all tablet actions at once. Use they/them for the owner.

## 2. Exact state (history, 2 Oct)

| Thing | State |
|---|---|
| Kernel queue (`<pc-work>/gh/iceland-linux`) | **`a88cf03` = 0001-0174** (0167-0174 = bootfix topic B: WCN7860 supplies, ktz8869 vddio optional, VA DMIC rate, ADSP FastRPC heap, UFS MCQ, smem Glymur DRAM info backport by Konrad Dybcio + the 1000UL fix, NVT deferral message; tested as q79, run 96), verified, pushed. Before it `f84d0d2` = 0001-0166. 0117-0124 NPU cooling (QMI TMD), 0125-0138 quick wins, 0139-0161 23 upstream fixes (authors kept), 0162 f_ncm NTB flush retry, 0163-0166 PMIC power telemetry (hwmon, lazy start). Configs: quick-wins lines, CONFIG_USB_UAS=m, CONFIG_SENSORS_QCOM_SPMI_QPT=m. `build/src` branch `iceland` = queue head "Input: nt36536: do not log the panel wait deferral as an error" (0174), clean; build-q56.sh HEAD_SUBJECT set to it; base config `out-config-base-0174` |
| Docs repo (`<pc-work>/gh/iceland-mainline`) | **`c2d26c0`** (commit w, about 23:10: runs 97-100, install docs round 7 + DUALBOOT-PLAN.md, guide slot facts, bootfix / bypass / bypasssafe / r1debug deliverables, matrix c2u). U-Boot repo `6e53ddd` (uboot.pin 17.0.0 / 2026-09 = today's boot_b). Pushed |
| Feature matrix | 63 working / 12 in progress / 6 not started / 2 not planned (83), page **v43**: https://claude.ai/artifact/GtN6zLRTeabVcyg3LirNBm (publish `scratchpad/feature-matrix.html` = the repo's `docs/features/feature-matrix.html`) |
| Test kernels (`<pc-work>/build`) | `binq79` = 0166 + bootfix B (= the queue head 0174's tree); `binq80` = 0174 + the TEST-ONLY ath12k `suspend_soc_reset` switch (l2diag, never queue) for the PCIe diagnosis; `binq77` = exactly 0166; `binq78` = 0162 plain (the install B-run kernel; its rpms are K2 / K3); private camera module per kernel `camdrv/sc1320cs-qNN.ko` (q70-q78) |
| `out/` build tree | base configs `out-config-base-0174` (queue config of 0166); `build-q56.sh` copies `out/.config` to `out-config-before-<tag>`; restore the base before a new build (see `build-q77.sh`) |
| Device package | repo: iceland-device 0.17. 0.18 = 0.17 + install fragment + gpuisp (hold, wireplumber >= 0.5.18) + deepsleep (npu keep running) is BUILT by `wf/install/next-k2p1u1.sh` step p1 (`wf/install/work/p1/`), proven to build and install in B runs 93 / 94; not committed to the repo yet (after R1 / R2) |
| Tablet | in Android (LineageOS, slot b; slot a successful + UNBOOTABLE, retry 6 each), battery about 50 %, Rooted debugging ON (adb root works). The owner recharges it unplugged: ask before any run |
| PC servers | rootfs server :8000 and USB proxy :3128 run as background shells of this session (restart if a kit says "rootfs server 000"); the NBD server in WSL (`rehearsal-pc.sh serve stage0 build`) may still run: `rehearsal-pc.sh stop` before R1 |

Runs of 2 Oct: up to area-combo-100 + R1b (see WORKLOG; 95 = the owner's charging sitting (95 = the owner's charging sitting, skipped after the charge-limit check; its
log set is in `area-combo-95/`, not committed). Next free numbers: kit run 101, test kernel q81, queue patch 0175,
matrix script `matrix-c2v.py`, commit script `commit-campaign2-x.sh` (make it with `mk-commit-x.py` from
`commit-campaign2-w.sh`; run `MATRIX=matrix-c2v.py MSG=commit-campaign2-x.msg bash commit-campaign2-x.sh`).

## 3. Workflows: where each stands and what to do next (history, 2 Oct; all closed by 14 Oct)

Folders: `<pc-work>/build/wf/<name>/` (WSL). "Agent id" = the background agent of this session; try
`SendMessage` to it first; if unknown in a new session, start a new agent with the template of section 5 and "an
earlier agent worked in your folder: read everything in it (also `work/`) and continue from there".

| Workflow | State | Agent id | Next action |
|---|---|---|---|
| quickwins, npucool, upsync (+uas, f_ncm), telemetry, hwinv | **green**, queued (0117-0166) | - | none (telemetry v3 lazy start proven in run 92) |
| gpuisp | **green**, finished: GPU ISP default (2.3 vs 21 ms CPU per frame), our libcamera 0.7.1 build stops the 19.8 MB-per-start leak | a13d5df432f1df418 | its 0.18 changes are in P1; the local rpms are in `<pc-path>` (private) |
| install (Opus) | Steps 1-4 + 6 done: notgzip PASS; run 100 = clean B run 20 / 0 (devrpm via nosel); U1 rebuilt (header from boot_b, unzip bound); Part A READY FOR C0. **R1b HUNG**: UCSI's late start (B1 keeps qcom_q6v5_pas out of the initramfs) bounces the USB gadget 5 s after the NBD connect; nbd cannot reconnect. **R1c READY** (args only: initcall_blacklist ucsi + altmode, rd.shell=0 rd.emergency=reboot, no plymouth, webcam + ncm-watch.ps1) - owner's go pending. Then P1 + TIN (iceland-rehearsal 5e34ff81: TCP readiness, udhcpd + kmsg units in the real root, no -persist), B run, R1d with kmsg-listen.py | a997748c4c5627a37 | R1c with the owner; then NEXT.md round 7d/7e; C0 only after R1 passes and the owner's decisions |
| r1debug (Fable) | FINISHED again: confirmed the R1b UCSI / VBUS-override chain in our tree, R1c args safe (+ rd.shell=0 rd.emergency=reboot), `wf/r1debug/REPORT-R1B.md`, `cand-r1b/` | ab236e1ef0aa067eb | resume for the next R1 problem |
| hwfix (bootfix + bypass) | B queued (0167-0174). **A CLOSED: keep upstream's 10 ms L2 warning** (run 99: noreset breaks the wake and reset the tablet; base 3 / 3 fine); l2diag test-only, never queue. C bypass: **DEFERRED by the owner** (to be added later) | ab01e21f3f346b12e | none |
| docs (Opus, SME) | current to about 23:00 (wf/docs; slot facts fixed by the main session in 03); copied into docs/guide by commit w | a3047486eb1c0ec68 | keep current; next: R1 outcome, chgsafe, sleeppower |
| deepsleep | kernel parts queued (0113-0116), CX collapse 95-98 %; the overnight drain needs the owner | - | owner night test; the package fallback (CDSP keeps running) is in 0.18 |
| bypasssafe (Opus) | FINISHED: bypass feature SAFE, its test NO-GO as written, corrected `cand/tablet.sh` + guard S1-S3 patch + simulation (REVIEW.md). Bypass deferred, so nothing to adopt now | af82745b453c81a8f | adopt section 5 first when bypass comes back |
| chgsafe (Fable) | RUNNING: (1) desktop notification at guard USB-C / input stops, (2) stock-exact input suspend in qcom_battmgr used by the guard (pre-existing gap, independent of bypass) | a28bff6cb55904eac | build + test its candidates, then 0.18 |
| sleeppower (Fable) | RUNNING: CDSP keep-running in 0.18, run 99's IRQ 316 early wake + mt5806 2250 ms suspend, AOSS re-check, the unplugged-night test made ready. Owner: NO Wi-Fi in sleep | af6b45583d5bb8cc6 | build + test its kit; the night test with the owner |

Decisions / owner items still open: the write-2 probe itself (after the AVB proof; the owner runs it); docs
agent's questions (a read-only RAM boot of the exact install U-Boot before write 1? unattended U-Boot behaviour;
"back to LineageOS" path; brightness maximum 4095 vs stock 3542; skin limit 48 C or stock 60/61 C; camera driver in
the image; INSTALL-PLAN section 9 items 5-10); owner tests: DP monitor, USB accessories (role switch is automatic),
pen, pogo typing, wake windows, overnight drain, apps by finger, USB headset, wall chargers (sitting kit
`gen-combo-95.py` exists), bypass with a wall charger.

## 4. How the work is done (the method to keep; history)

**A workflow** = one background agent per topic. It only analyses and prepares on the PC and delivers files into
`<pc-work>/build/wf/<name>/`: `REPORT.md`, `NEXT.md`, `tablet.sh` (functions `wf_<name>...`, one `sayk` summary
line, a marker `$X/<NAME>-DONE`), candidates under `cand/` (kernel patches as Python patchers with exact-string
asserts + `.msg` commit texts with `--- commit N (file) ---` sections, `apply-kernel.sh` + `kernel.config` for
`build-q56.sh`'s generic case), a parts module for `an/genwf.py` (see `wf/telemetry/cand/telemetry_parts.py`,
`wf/upsync/cand/upsync_parts.py`), private material under `priv/`.

**The main session** owns the tablet, the kernel tree, builds, repositories. Loop per workflow:
1. Read its NEXT.md; review every write of its test and every limit of its candidates (charging safety first).
2. Test kernel: restore the base config (`out-config-base-0174`), `TAG=qNN WF="name ..." bash build-q56.sh`
   (expects HEAD_SUBJECT = the queue head's subject; makes `camdrv/sc1320cs-qNN.ko`). A build only when no kit is
   being prepared (prep takes the kit lock with `flock -n` and refuses if busy). Plain head builds with
   `build-q2.sh` need `camdrv/build.sh` + copy to `sc1320cs-<tag>.ko` (see `an/camdrv-q78.sh`).
3. A kit run: `gen-combo-N.py` with `genwf.gen(..., modtree=True, coldplug=True)` (coldplug = udev loads the modules
   of driverless devices as an installed boot does; without it e.g. the sound card waits forever for the DP audio
   codec); `bash an/chk.sh N`; a chain script in the scratchpad (`sed -e 's/47/N/g' area-combo-47-chain.sh`, longer
   runs `-Wait 2500/4000`); start in the BACKGROUND with `MAXN=... bash scratchpad/run-chain.sh N [N2 ...]
   "pattern"` (it has a battery gate: below 40 % it waits in Android until 45 %) - **only after the owner has
   connected the tablet and said go**. `an/wait-probe.sh N` notifies when one run ends.
4. Judge from `area-combo-N-probe.log` and `area-combo-N/combo/<name>/`; boot errors with
   `python3 an/kmsg-errors.py N [M]`. Send results back with `SendMessage` (first line = what it is, the summary
   line, the log path, numbered questions).
5. Queue what passed: `queue-0NNN.sh` (see `queue-0125.sh` for patcher sections, `queue-0139.sh` for `git am` of
   upstream patches with authors kept + our trailers, `queue-0163.sh`): the tree must equal the tested `binqNN`
   tree, `DRY=1` first, verification with `scripts/prepare.sh` from the local base, commit, push; then update
   `build-q56.sh`'s HEAD_SUBJECT and the base config.
6. After each proven result: WORKLOG entry, `research/matrix-c2X.py` (each runs the previous one; newest
   `matrix-c2s.py`), a commit script made by `mk-commit-X.py` from the previous one (newest
   `commit-campaign2-u.sh`); it copies masked log sets, tools and public workflow deliverables with the privacy
   guards (no rpm, no frames, no priv/work); republish the matrix page.

Install rehearsal (wf/install): the B run (`genwf-install-b.py N q78 "rr dev b1a b1b b2a b2b" 4300 qos=2` with the
NBD server `rehearsal-pc.sh serve stage0 build` on a fresh `ov-build`, the relay `tcp-relay.py --listen=0.0.0.0
--target=wsl:10810 --allow=<usb-ip>` and `linktest-server.py`), then R1 as in section 3. `rehearse.ps1` only
allows fastboot devices / getvar / boot / reboot / `oem console` and adb devices / get-state / reboot bootloader /
shell getprop.

## 5. Prompt template for a workflow agent

Use the `Agent` tool (general-purpose, background). Give: the project in two sentences; the topic and what is known
(with file paths); the hard rules (PC only, no tablet actions, no kit / kernel builds except a compile check in
the agent's own worktree / O= dir, no commits, write only in its own `wf/<name>/`, stock values with sources,
private data, charging safety, never `wsl --shutdown`, script files for WSL commands, no `pkill -f` with its own
pattern); the deliverables (REPORT, NEXT, tablet.sh, cand/, parts module, at most 10 minutes per tablet part); how
to report (SendMessage to "main" for intermediate results; final answer with findings, files, build / test
lines). The prompts of this session for install round 6, hwfix and docs (in the transcript / WORKLOG) are models.

## 6. Lessons that cost time (do not repeat)

- `wsl.exe -d Ubuntu-24.04 -- bash -c '...'` from Git Bash loses `$var`, loops and backslashes: script files.
  Long Python or shell texts with quotes: write them with the Write tool, not a heredoc.
- `pkill -f` / `pgrep -f` with a pattern that is in the calling command line kills the caller (use `[x]` brackets).
- Never edit a script that a running bash is still reading (run-chain.sh got a "syntax error" that way).
- Kits load only their early module list (`build/mods25/all`); a device whose module is not on it stays without
  driver: use `coldplug=True`; the DP audio codec is now on the list.
- A kit's log checks must ignore the kit's own `iceland-combo` lines in kmsg (sayk writes summaries there).
- Kit preps take the kit lock with `flock -n`: no kernel build / queue script while a chain may prep.
- The USB gadget (f_ncm) used to collapse with traffic in both directions: fixed in 0162; uploads need it.
- U-Boot subcommand tables have their own maxargs: a patched command can still be refused before it runs.
- Kit descriptions must not contain a quote character; queue verification from the local repository.
- Camera bus / driver tests need the sensor hub configured (`pkg2` + `rotpkg start`).
- Never read TLMM pad registers through /dev/mem; never read all regmap debug files.
- Foreground waits are backgrounded by the owner: background jobs + their completion notices.
- The owner recharges the tablet unplugged: ask before every tablet action.
- Use they/them for the owner (never assume pronouns).

## 7. Files that matter (WSL `<pc-work>/build` unless said)

- Run pipeline: `an/genwf.py` (coldplug option), `gen-combo-NN.py` (newest 83, 87, 89b, 92, 95),
  `an/area-combo-NN*.sh`, `prep-area-combo-NN.sh`, `an/chk.sh`, `an/wait-probe.sh`, `an/kmsg-errors.py`,
  `mods25/all` (the kits' early modules), scratchpad `area-combo-NN-chain.sh`, `run-chain.sh`.
- Kernel: `build-q2.sh`, `build-q56.sh` (cases pencharge, deepsleep, pogo, uas, ncm, generic), `build-q74..78.sh`,
  `queue-0117.sh`, `queue-0125.sh`, `queue-0139.sh`, `queue-0163.sh`, `out-config-base-0174`.
- Install: `wf/install/` (next-k2p1u1.sh, genwf-install-b.py, cand/rehearsal/*, cand/u-boot/*, NEXT.md),
  `an/r1-prep.sh`, `an/b2-prep.sh`, `an/stop-r1.sh`.
- Commit: `mk-commit-u.py` / `commit-campaign2-u.sh`, `<pc-work>/research/matrix-c2s.py`.
- Snapshot of all this in the project folder: `build/save-project.sh` + `save-project-fix.sh` +
  `save-project-wf.sh`.
- Guides: `docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md` (being updated by the install agent), the boot-log plan (removed 13 Oct, not published),
  `docs/guide/` in the docs repo.

## 8. First ten minutes of the next session (history)

1. `bash <pc-work>/build/an/idle-check.sh` (nothing running, repos clean); `adb devices` by line count only after
   asking the owner whether the tablet is connected.
2. Read the round-6 report of the install agent, the r1debug verification and the hwfix deliveries (resume the
   agents by id, section 3).
3. With the owner's go: R1 (section 3), then the hwfix kernel (q79) and its kit, then the write-2 probe preparation
   with the owner.
4. Log every step in `WORKLOG.md`, keep the matrix and both repositories current.

## Loop 4 -> Loop 5 pointer (9 Oct 2026)

Work continues in `<pc-path>` (the loop 5 package: `START-HERE.md`, `RULES.md`, `NEXT-TESTS.md`,
`STATE-AT-HANDOFF.md`, `WORKLOG.md`). Read that folder first; the sections above describe loop 4 and stay as history.

State at the loop 4 -> loop 5 handoff:
- The image is HELD, not final: the fresh-boot test r2m gave 3 of 10 empty microphone opens and one q6apm APM timeout (F55).
- Commit z = iceland-mainline `a8739a6` (the fixed build, status held).
- Queue 0190 = iceland-linux `2afea47` (kernel q87).
- Loop 5 item 1 is F55 (klog). No tablet action until the owner connects the tablet and gives the go.

# OnePlus Pad 4 mainline Linux - hand-over (2 Oct 2026, about 21:00; state table and workflows updated about 22:30)

Written for the next model / session. Read this file, then `STATE.md`, `CLAUDE.md`, the last entries of
`WORKLOG.md` (from entry 44 on: everything of 2 Oct afternoon / evening), the last block of
`docs/memory/iceland-resume-point.md`, and `docs/BOOT-LOG-PLAN.md`. The draft documentation set (overview,
hardware, boot and partitions, build-your-own, porting, history, install review) is in the docs repo under
`docs/guide/` (source: WSL `~/mainline/build/wf/docs/`).

## 1. What the owner has ordered (in force)

Earlier orders (still in force; full text in the 10:00 version of this file in git history and in WORKLOG):
"Test and debug ... until completed and totally green, update constantly the feature matrix and a work log";
"continue till all workflows are completed and green"; "once all working flows are green, update accordingly the
project knowledge and make sure the repos are updated"; keep iterating without asking for confirmation where the
owner said so (quick wins, telemetry, NPU cooling).

Orders of 2 Oct afternoon / evening (verbatim):
- "update feature matrix with everything commited" (several times: after every proven result, rebuild + publish).
- "add another workflow to list all hardware that has no drivers or not working on the tablet" (done: wf/hwinv).
- "start combined workflows for items from 1 till 9, keep iterating without asking for my confirmation" (done:
  quick wins, queued 0125-0138).
- "proceed with 1 and 3" (UAS in the queue configs; the USB-C upstream fixes): done.
- "check all errors in kmsg during booting and put a plan to resolve": done, `docs/BOOT-LOG-PLAN.md`.
- "no dual boot for now but prepare a plan for it with the best safety precautions" -> the install stays
  Fedora-only; the install agent writes `wf/install/DUALBOOT-PLAN.md` (plan only).
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
addresses and network names masked; commits as `mzak <mzak.amin@gmail.com>` with `Signed-off-by` and
`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; `git pull --rebase` before push; never
`wsl --shutdown`; "hold the tablet" = stop all tablet actions at once. Use they/them for the owner.

## 2. Exact state

| Thing | State |
|---|---|
| Kernel queue (`~/mainline/gh/iceland-linux`) | **`a88cf03` = 0001-0174** (0167-0174 = bootfix topic B: WCN7860 supplies, ktz8869 vddio optional, VA DMIC rate, ADSP FastRPC heap, UFS MCQ, smem Glymur DRAM info backport by Konrad Dybcio + the 1000UL fix, NVT deferral message; tested as q79, run 96), verified, pushed. Before it `f84d0d2` = 0001-0166. 0117-0124 NPU cooling (QMI TMD), 0125-0138 quick wins, 0139-0161 23 upstream fixes (authors kept), 0162 f_ncm NTB flush retry, 0163-0166 PMIC power telemetry (hwmon, lazy start). Configs: quick-wins lines, CONFIG_USB_UAS=m, CONFIG_SENSORS_QCOM_SPMI_QPT=m. `build/src` branch `iceland` = queue head "Input: nt36536: do not log the panel wait deferral as an error" (0174), clean; build-q56.sh HEAD_SUBJECT set to it; base config `out-config-base-0174` |
| Docs repo (`~/mainline/gh/iceland-mainline`) | after this commit: commit u (docs/guide + project knowledge); before it `823eb07` (commit t). Pushed |
| Feature matrix | 61 working / 12 in progress / 5 not started / 2 not planned (80), page v41: https://claude.ai/artifact/GtN6zLRTeabVcyg3LirNBm (publish `scratchpad/feature-matrix.html` = the repo's `docs/features/feature-matrix.html`) |
| Test kernels (`~/mainline/build`) | `binq79` = 0166 + bootfix B (= the queue head 0174's tree); `binq80` = 0174 + the TEST-ONLY ath12k `suspend_soc_reset` switch (l2diag, never queue) for the PCIe diagnosis; `binq77` = exactly 0166; `binq78` = 0162 plain (the install B-run kernel; its rpms are K2 / K3); private camera module per kernel `camdrv/sc1320cs-qNN.ko` (q70-q78) |
| `out/` build tree | base configs `out-config-base-0174` (queue config of 0166); `build-q56.sh` copies `out/.config` to `out-config-before-<tag>`; restore the base before a new build (see `build-q77.sh`) |
| Device package | repo: iceland-device 0.17. 0.18 = 0.17 + install fragment + gpuisp (hold, wireplumber >= 0.5.18) + deepsleep (npu keep running) is BUILT by `wf/install/next-k2p1u1.sh` step p1 (`wf/install/work/p1/`), proven to build and install in B runs 93 / 94; not committed to the repo yet (after R1 / R2) |
| Tablet | in Android (LineageOS, slot b), battery about 50 %. The owner recharges it unplugged: ask before any run |
| PC servers | rootfs server :8000 and USB proxy :3128 run as background shells of this session (restart if a kit says "rootfs server 000"); the NBD server in WSL (`rehearsal-pc.sh serve stage0 build`) may still run: `rehearsal-pc.sh stop` before R1 |

Runs of 2 Oct: up to area-combo-95 (95 = the owner's charging sitting, skipped after the charge-limit check; its
log set is in `area-combo-95/`, not committed). Next free numbers: kit run 96, test kernel q79, queue patch 0167,
matrix script `matrix-c2t.py`, commit script `commit-campaign2-v.sh` (make it with `mk-commit-v.py` from
`commit-campaign2-u.sh`).

## 3. Workflows: where each stands and what to do next

Folders: `~/mainline/build/wf/<name>/` (WSL). "Agent id" = the background agent of this session; try
`SendMessage` to it first; if unknown in a new session, start a new agent with the template of section 5 and "an
earlier agent worked in your folder: read everything in it (also `work/`) and continue from there".

| Workflow | State | Agent id | Next action |
|---|---|---|---|
| quickwins, npucool, upsync (+uas, f_ncm), telemetry, hwinv | **green**, queued (0117-0166) | - | none (telemetry v3 lazy start proven in run 92) |
| gpuisp | **green**, finished: GPU ISP default (2.3 vs 21 ms CPU per frame), our libcamera 0.7.1 build stops the 19.8 MB-per-start leak | a13d5df432f1df418 | its 0.18 changes are in P1; the local rpms are in `C:\platform-tools\rpms\libcamera` (private) |
| install | **now an Opus agent `a997748c4c5627a37`** (the old one stopped after writing `wf/install/HANDOVER-ROUND6.md`; it re-verifies, then sends me the commands: P1 + TIN with the B1 omit_drivers fix + the pwrseq add_drivers drop-in, the B run again (must show "policy loads 0"), the notgzip U-Boot test, R1 on the new golden, parta-read / parta-check for the write-2 probe (AVB-PROOF passed on the PC: the footered U-Boot = PUBLIC_KEY_REJECTED = continue, a plain one = INVALID_METADATA = ABL stops)); round 6 so far: B1 ADSP/CDSP firmware on the installed initramfs, B2 the build chroot loads SELinux into the host, B3 charge-limit accept line; the docs review R1-R9 (AVB footer for u-boot-iceland.img + PC proof, the plan's undo file, rehearsal vs install U-Boot wording + a guard, unattended U-Boot, EFI boot order / efisp, guide fixes, the misc boot-recovery gotcha); the write-2 probe guide part C0; DUALBOOT-PLAN.md | a997748c4c5627a37 (old: a68073ae3baaf9f4b) | wait for its command list; then (owner connected!) R1 on today's golden: `rehearsal-pc.sh stop`, `commit`, `serve golden r1`, `head "enforcing=0"`, `rehearse.ps1 -Yes` + `ACCEPT_SUSPEND=0 rehearsal-probe.sh OUT accept` (TABLET_IN=wf/install/priv/run/tablet-in) |
| r1debug (Fable model) | FINISHED: confirmed the root cause and the install agent's U-Boot fix 15 / 15 in its sandbox; proposed the busy-U-Boot probe (applied in rehearse.ps1 8453bb0c...) and the 8 KiB notgzip test head (`wf/r1debug/work/t/notgzip.img`) as the first tablet step; was verifying the install agent's U-Boot fix (blkmap maxargs 2 -> 3, FAILED lines + fastboot_loop, no Mac/Amiga partition parser) in its own sandbox | ab236e1ef0aa067eb | R1 waits for its verification |
| hwfix (bootfix + bypass) | B GREEN and queued (0167-0174). A: diagnosis kit **run 97** (q80, part bfpcie: base / noreset / wow / nodrv s2idle variants) RUNNING at the save point - judge it and send it to the agent (root cause per the agent: ath12k's suspend-time WLAN SoC reset, the reset chip never answers PME_Turn_Off; upstream made it a 10 ms warning; stock keeps the WLAN firmware alive). C (bypass) in progress. Earlier: A PCIe L2 timeout + 14 probe deferrals, C bypass charging (in the battery guard + a GNOME Quick Settings toggle + polkit helper) and the corrected accept.sh charge-limit check | ab01e21f3f346b12e | build `TAG=q79 WF="bootfix" bash build-q56.sh` when it delivers, run its parts (coldplug), feed back |
| docs (Opus, SME) | drafts done and committed as `docs/guide/` | a3047486eb1c0ec68 | review comments as they come; keep the docs current; review DUALBOOT-PLAN.md |
| deepsleep | kernel parts queued (0113-0116), CX collapse 95-98 %; the overnight drain needs the owner | - | owner night test; the package fallback (CDSP keeps running) is in 0.18 |

Decisions / owner items still open: the write-2 probe itself (after the AVB proof; the owner runs it); docs
agent's questions (a read-only RAM boot of the exact install U-Boot before write 1? unattended U-Boot behaviour;
"back to LineageOS" path; brightness maximum 4095 vs stock 3542; skin limit 48 C or stock 60/61 C; camera driver in
the image; INSTALL-PLAN section 9 items 5-10); owner tests: DP monitor, USB accessories (role switch is automatic),
pen, pogo typing, wake windows, overnight drain, apps by finger, USB headset, wall chargers (sitting kit
`gen-combo-95.py` exists), bypass with a wall charger.

## 4. How the work is done (the method to keep)

**A workflow** = one background agent per topic. It only analyses and prepares on the PC and delivers files into
`~/mainline/build/wf/<name>/`: `REPORT.md`, `NEXT.md`, `tablet.sh` (functions `wf_<name>...`, one `sayk` summary
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
--target=wsl:10810 --allow=172.16.42.1` and `linktest-server.py`), then R1 as in section 3. `rehearse.ps1` only
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

## 7. Files that matter (WSL `~/mainline/build` unless said)

- Run pipeline: `an/genwf.py` (coldplug option), `gen-combo-NN.py` (newest 83, 87, 89b, 92, 95),
  `an/area-combo-NN*.sh`, `prep-area-combo-NN.sh`, `an/chk.sh`, `an/wait-probe.sh`, `an/kmsg-errors.py`,
  `mods25/all` (the kits' early modules), scratchpad `area-combo-NN-chain.sh`, `run-chain.sh`.
- Kernel: `build-q2.sh`, `build-q56.sh` (cases pencharge, deepsleep, pogo, uas, ncm, generic), `build-q74..78.sh`,
  `queue-0117.sh`, `queue-0125.sh`, `queue-0139.sh`, `queue-0163.sh`, `out-config-base-0174`.
- Install: `wf/install/` (next-k2p1u1.sh, genwf-install-b.py, cand/rehearsal/*, cand/u-boot/*, NEXT.md),
  `an/r1-prep.sh`, `an/b2-prep.sh`, `an/stop-r1.sh`.
- Commit: `mk-commit-u.py` / `commit-campaign2-u.sh`, `~/mainline/research/matrix-c2s.py`.
- Snapshot of all this in the project folder: `build/save-project.sh` + `save-project-fix.sh` +
  `save-project-wf.sh`.
- Guides: `docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md` (being updated by the install agent), `docs/BOOT-LOG-PLAN.md`,
  `docs/guide/` in the docs repo.

## 8. First ten minutes of the next session

1. `bash ~/mainline/build/an/idle-check.sh` (nothing running, repos clean); `adb devices` by line count only after
   asking the owner whether the tablet is connected.
2. Read the round-6 report of the install agent, the r1debug verification and the hwfix deliveries (resume the
   agents by id, section 3).
3. With the owner's go: R1 (section 3), then the hwfix kernel (q79) and its kit, then the write-2 probe preparation
   with the owner.
4. Log every step in `WORKLOG.md`, keep the matrix and both repositories current.

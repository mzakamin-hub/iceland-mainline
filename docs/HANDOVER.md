# OnePlus Pad 4 mainline Linux - hand-over (2 Oct 2026, about 10:00)

Written for the next model / session. Read this file, then `STATE.md`, `CLAUDE.md`, the last entries of
`WORKLOG.md` (21-27) and the last block of `docs/memory/iceland-resume-point.md`. Everything below is the state at
the moment the previous session stopped. Nothing is running: no kit run, no build, no agent.

## 1. What the user has ordered (in force, verbatim)

1. Standing order: "combine 1,2,3 in as a singular step and also include mic input meter as still not fixed, tablet is
   connected and on lineageos, Test and debug till 1,2,3 and mic input are completed and totally green update as
   well constantly feature matrix and a work log to make sure your current work and previous and next actions are
   logged to prevent repeating."
2. "in seperate workflows work on : 1)Low-battery current limiting (BCL) 2)Charging 3)Charge limits 4)GPU Cooling
   5)Improved thermals. Also prepare a full plan for full install ..." (done: the five are green, plan =
   `docs/INSTALL-PLAN.md`).
3. "finalize camera as well in seperate workflow" (in progress, see the table).
4. "Start workflows to address below not started items , test run and fix till resolution and use autonomous agents
   till they are working(Display&input,Power&charging, Sleep&powersaving, Software&packaging)" (in progress).
5. "continue till all workflows are completed and green".
6. "once all working flows are green , update accordingly the project knowledge and make sure the repos are updated,
   Meanwhile write a complete guide for flashing this on my tablet and make sure it follows the safety measures set
   before" (guide written: `docs/INSTALL-GUIDE.md`; the final update is still owed).
7. "save everything because im changing models , i need my next model to be able to resume exactly and run the
   agentic workflows as we were" (this file).

Hard rules (full list in `STATE.md` and `CLAUDE.md`): RAM boot only - never flash, unlock, wipe, switch slots or
install; tests fully automated, at most 10 minutes each, anything that needs the user is deferred and listed; every
hardware value from Pad 4 stock sources; charging safety first; private data never committed (firmware, `fwsuper`
carves, camera driver and traces, stock tuning / model data, the user's backup, frames, recordings); serial, MAC /
BD addresses and network names masked; never print `adb devices` raw (count lines); commits as
`mzak <mzak.amin@gmail.com>` with `Signed-off-by` and `Co-Authored-By` trailers; `git pull --rebase` before push;
never `wsl --shutdown`; "hold the tablet" = stop all tablet actions at once.

## 2. Exact state

| Thing | State |
|---|---|
| Kernel queue (`~/mainline/gh/iceland-linux`) | `c52d6ee`, patches 0001-0089, verified, pushed. Branch `iceland` in `~/mainline/build/src` = queue head, clean |
| Docs repo (`~/mainline/gh/iceland-mainline`) | `81cca68` "campaign 2 (k): hand-over ..." (a small follow-up commit with the final facts may sit on top: `git log -2`), pushed |
| Feature matrix | 55 working / 9 in progress / 10 not started / 2 not planned (76), page version 32; https://claude.ai/artifact/GtN6zLRTeabVcyg3LirNBm (publish the rebuilt `scratchpad/feature-matrix.html` to this URL) |
| Test kernels in `~/mainline/build` | `binq55` = tree of the queue head (use this kit kernel for tests of the queue); `binq56` = queue head + pen charging candidates; private camera module per kernel: `camdrv/sc1320cs-q55.ko`, `-q56.ko` (the patched driver; old one `sc1320cs.c.q54`) |
| `out/` build tree | configured for q56 (`CONFIG_CHARGER_MT5806_PEN=m`); copy of the config before: `out-config-before-q56` |
| Device package | iceland-device 0.16 in the repo (built + installed in run 41). 0.17 is being assembled (pkg017 + the camera fragment) |
| Tablet | in Android (LineageOS, slot b), battery about 80 % (drains about 1 % per test run on the PC port; pause below 40 %) |
| PC servers | rootfs server on :8000 and the USB proxy on :3128 were running as background shells of the old session; if a kit run says "rootfs server 000", start them again: `python -m http.server 8000 --bind 0.0.0.0 --directory C:\platform-tools\rootfs-serve` and `python C:\platform-tools\usb-proxy.py 0.0.0.0 3128` (PowerShell, background) |

Runs of this session: 38-47 (`~/mainline/build/area-combo-NN/`, probe logs `area-combo-NN-probe.log`). Run 45 = all
six older workflows green on the queue head. WORKLOG entries 21-27 have every result.

## 3. Workflows: where each stands and what to do next

Folders: `~/mainline/build/wf/<name>/` (WSL). "Agent id" = the background agent of the old session; try
`SendMessage` to that id first ("continue and deliver; the main session was changed"). If the id is unknown in the
new session, start a NEW agent with the prompt template of section 5 and add: "An earlier agent already worked in
your folder: read everything in it (also `work/`) and continue from there instead of starting over."

| Workflow | Matrix row | Agent id | In the folder | State | Next action |
|---|---|---|---|---|---|
| bcl, chargelimit, charging, gpucool | (queued 0074-0080, GPU cooling) | - | complete | **green** on the queue head (run 45) | user items only (wall chargers, a look at Settings) |
| thermal | Skin and XO zones; Skin temperature policy | - | complete; PRIVATE: `priv/`, `tablet-in/thermal-model.json`, `cand/mk-thermal-model.py` | kernel parts green (run 45: 7 PASS); policy daemon proven in RAM (run 39) but not packaged | packaged by pkg017; the skin loop's move to 60 / 61 C stays the user's choice |
| camera | Cameras | `a3b3533c41c6d6b08` | REPORT, NEXT, tablet.sh, cand/, priv/ | bus fix + focus queued (0084-0089); run 46: focus, fixfocus, quality, browser PASS; **app still CHECK** (no preview, 0 of 2 photos even with the permission set) | send the agent run 46's app result (`area-combo-46/combo/camera/app/`), run its next delivery (`gen-combo-46.py` shows the run); then iceland-device camera changes (`cand/wp4-apps/pkg-017-camera.py`: holder unit out, tuning files, WirePlumber rule, fixed-focus helper) |
| pencharge | Pen charging | `a410fb5800fadd638` | REPORT, NEXT, tablet.sh, cand/ (3 patchers + driver) | run 47 on q56: driver up, IC 0x5806 fw 0x20022, 7000 mV confirmed, idle, inhibit ok; 2 rebind checks FAIL (empty pin readings after unbind), note "IC reads 5017 mV" | the agent got the results and three questions (WORKLOG entry 27) but was paused before answering: resend, rebuild if the candidates change, rerun (`gen-combo-47.py`), then queue 4 commits + config line; pen itself = user |
| pogo | Pogo keyboard | `a53da1519c5319e23` | REPORT, NEXT, tablet.sh, `cand/kernel/pogo-kernel.py` + driver + binding | delivered, NOT built, NOT run | add a `pogo)` case to `build-q56.sh` (lines in `wf/pogo/NEXT.md` run A; `--enable KEYBOARD_ONEPLUS_POGO`), build q57 = queue head + pencharge + pogo, run `wf_pogo` (no keyboard needed), send `$X/pogo/` back |
| deepsleep | Deep-sleep proof | `a78a7b8bcac860a75` | REPORT, NEXT, tablet.sh, `tablet-night.sh`, `pc-side.sh`, tablet-in/ | delivered just before the pause, NOT read, NOT run | read NEXT.md, review the writes, run it |
| wake | Wake by lid, keyboard, charger | `a6be96dffe3eab71a` | tablet.sh, tablet-in/, cand/kernel/ (no REPORT / NEXT yet) | paused while writing its documents | resume the agent; then run |
| apps | Full GNOME app set | `a15f21638a769c7c1` | tablet.sh, cand/ (package list, comps file, dnf hold files, sizes) | paused before REPORT / NEXT | resume; then run (installs in slices into RAM) |
| audit | Stock-values audit | `a9cfcdbd7afd6ab6e` | AUDIT-TABLE.md, audit-dt.py, cand/01..10+ fix patchers with messages | paused before REPORT / NEXT | resume; review each fix (regulator voltages first), build, test, queue |
| pkg017 | Device package 0.17 | `a93f7eb7566f701cc` | `pkg-017.py`, `check.sh`, cand/ (merged guard, conf, thermal daemon + service + conf) | paused during its tests | resume; apply the generator, build + install in a run (part `pkg2` with 0.16 -> 0.17 in the script), run `wf_pkg017` |
| install | (Fedora installed on the tablet; guide Part B) | `a68073ae3baaf9f4b` | only `work/` so far | paused early | resume or restart; it builds the RAM-rehearsal tooling; no script of it may write to the tablet |

When every row is green: matrix + WORKLOG + commit, then the user's final request (order 6): update the project
knowledge (this folder's STATE.md, CLAUDE.md, HANDOVER.md, memory, snapshot) and make sure both repositories are
pushed.

Decisions still waiting for the user (none blocks the work above): install (Fedora only or dual boot; `boot_b` or
`recovery_b`; do open gates block; camera driver in the image); charge limit on by default / hold or charge to the
limit; keep awake on a charger (default taken: yes, as stock, one config line); thermal: skin loop at 60 / 61 C
with the policy (recommended) or 48 C as today, Balanced table, may stock's model data be committed; wall-charger
sitting; colours and sharpness by eye; publish the camera driver or not; mutter bug report; 5 GHz password.

## 4. How the work is done (the method to keep)

**A workflow** = one background agent per topic. It only analyses and prepares on the PC and delivers files into
`~/mainline/build/wf/<name>/`: `REPORT.md`, `NEXT.md` (what to build and run, pass criteria, what to send back),
`tablet.sh` (one function `wf_<name>`, one `sayk` summary line, marker `$X/<NAME>-DONE`), candidates under `cand/`
(kernel patches as Python patchers with exact-string asserts, never applied by the agent), private material under
`priv/`. Briefs: `docs/WORKFLOW-BRIEF-2.md` (general rules), `-3-camera.md`, `-4.md` (round 4).

**The main session** owns the tablet, the kernel tree, builds, repositories. Loop per workflow:
1. Read its NEXT.md; review every write of its test and every limit of its candidates (charging safety first).
2. Kernel candidates: a test kernel `build-qNN.sh` (branch `candNN` from `iceland`, one CANDIDATE commit,
   `build-q2.sh`, private camera module, `mk-modfull.sh`). `build-q56.sh` is the current generic one
   (`TAG=q57 WF="pencharge pogo" bash build-q56.sh`; add a case per workflow).
3. A kit run: a small `gen-combo-N.py` that calls `an/genwf.py` (see `gen-combo-46.py`, `gen-combo-47.py`): it
   derives `an/area-combo-N.sh` (tablet side), `an/area-combo-N-probe.sh` (PC side) and `prep-area-combo-N.sh`
   from run 44. Check with `bash an/chk.sh N`. Chain scripts `area-combo-N-chain.sh` are in the session scratchpad
   (copies in `scripts/pc-chains/` of this folder; made from the run-38 chain with sed). Start runs in the
   BACKGROUND: `bash scratchpad/run-chain.sh N [N2 ...] "grep-pattern"` and let the completion notice continue the
   work. Never wait in the foreground (the user backgrounds it).
4. Judge from `area-combo-N-probe.log` (summary lines) and `area-combo-N/combo/<name>/`. Send the summary line and
   the folder path back to the agent with `SendMessage`, with precise questions. Repeat until green or until only
   the user's hands are missing.
5. Queue what passed: `queue-00NN.sh` (see `queue-0077.sh`, `queue-0084.sh`): commits one per logical change with
   real messages on a branch, the tree must equal the tested `binqNN` tree, dry run first (`DRY=1`), fast-forward
   `iceland`, format-patch into iceland-linux, `kernel.pin`, verification with `scripts/prepare.sh` from the LOCAL
   base (the GitHub clone stalled twice), commit, push.
6. After each proven result: WORKLOG entry, a `research/matrix-c2X.py` script (each runs the previous one;
   newest: `matrix-c2i.py`), a commit script made by `mk-commit-X.py` from the previous one (newest:
   `commit-campaign2-j.sh`; usage `MATRIX=matrix-c2i.py MSG=commit-campaign2-j.msg bash commit-campaign2-j.sh 44`),
   which copies the masked log sets, tools and public workflow deliverables and has the privacy guards; then
   republish the matrix page.

Package runs: part `pkg2` builds the sensor RPMs + iceland-device on the tablet and installs them; `rotpkg start`
brings the sensor hub up (camera bus / driver tests need the hub CONFIGURED: run them after these two parts).

## 5. Prompt template for a workflow agent

Use the `Agent` tool (general-purpose, background). Template (fill NAME, ITEM, the item text of the brief):

> You are the workflow "NAME" of a hardware bring-up project: mainline Linux (7.3-rc4 + a patch queue) with Fedora 44
> GNOME on the OnePlus Pad 4 tablet ("iceland", Qualcomm SM8850 / Kaanapali), RAM boot only. The owner asked for
> autonomous workflows that take the not-started items of the feature matrix to "working". Your item: ITEM. Another
> session (the main session) owns the tablet, the kernel tree and all builds; you work on the PC only and deliver
> files; the main session runs your test on the tablet and sends you the results, and you then fix and deliver
> again until it works.
> Read first: `C:\Users\lucne\OnePlusPad4-Mainline\docs\WORKFLOW-BRIEF-4.md` (your item), `docs\WORKFLOW-BRIEF-2.md`
> (general rules), `CLAUDE.md`, `STATE.md`, the end of `WORKLOG.md`.
> Absolute rules: NO tablet actions of any kind (no adb, fastboot, ssh to 172.16.42.1, relay scripts, webcam; do not
> even run `adb devices`). NO kernel builds, NO kit builds, nothing that takes `~/mainline/build/.kit-build.lock`.
> Never check out, commit, stash or edit in `~/mainline/build/src` (read with `git -C ~/mainline/build/src show
> iceland:PATH`); the only compile allowed is a check of a driver COPY as an external module inside your `work/`
> folder. No git commit / push. Write only inside `~/mainline/build/wf/NAME/`. Every hardware value from Pad 4 stock
> sources with file and line. Nothing private in public deliverables (bulk copies from fwsuper, firmware, serials,
> addresses go under `priv/`). The test: automated, no user, at most 10 minutes, RAM session only, writes only what
> is reversible and says exactly what it writes; never read every `/sys/kernel/debug/regmap/*/registers`; never
> touch TLMM pad registers through /dev/mem.
> Practical: run WSL commands from Git Bash as `MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu-24.04 --cd DIR -- bash
> SCRIPT.sh`; anything with shell variables or backslashes goes into a script file written with the Write tool
> (LF line ends); WSL /tmp is cleaned between invocations (use `work/`); never use pkill -f / pgrep -f with a
> pattern that is in your own command line; REPORT.md and NEXT.md are requested by the owner - if a tool refuses
> those names, write them through a Bash script.
> Deliver REPORT.md, tablet.sh (function wf_NAME), candidates under cand/, NEXT.md. Final message: the findings in
> a few plain sentences and the list of files.

Topic-specific additions that were given: pencharge - "CHARGING SAFETY COMES FIRST: every current, voltage, power
and temperature limit is stock's value or lower; a test never enables the transmitter unless stock's own conditions
hold"; deepsleep - "the tablet hangs on a PC port (500 mA): say what the fuel gauge can and cannot show; a
candidate that switches a rail, clock or subsystem off must say why that is safe"; apps - "nothing on the tablet's
storage, install in slices that fit into RAM, never pull in kernel / grub / shim / firmware packages"; audit -
"safety order: battery and charger, regulator voltages, thermal trips, display, speaker gains, pins, clocks,
radios"; pkg017 - "work on a copy of packaging/iceland-device, deliver a generator `pkg-017.py`, never raise a
limit, keep the camera parts alone, stock's thermal model stays private and outside the package"; install - "no
script may contain `fastboot flash / erase / format / set_active / -w / flashing`; rehearsals use `fastboot boot`
only; do not download the Fedora image yourself (deliver a fetch + verify script)"; camera - see
`docs/WORKFLOW-BRIEF-3-camera.md`.

Feedback message pattern (SendMessage): first line = what this is; then the exact summary line, where the log set
is (`~/mainline/build/area-combo-N/combo/<name>/`, `common/dmesg.txt`, `common/journal.txt`), numbered questions,
"keep the test under N minutes; I run it again as soon as you deliver".

## 6. Lessons that cost time (do not repeat)

- `wsl.exe -d Ubuntu-24.04 -- bash -c '...'` from Git Bash: the outer layer expands `$var` and loop variables and
  eats backslashes. Put everything with variables, loops or backslashes into a script file (Write tool) and run
  the file. Generators with `\n` in strings: write them with the Write / Edit tools, never through a heredoc.
- `pkill -f` / `pgrep -f` with a pattern that also appears in the calling command line kills the caller: use a
  script file whose name does not match.
- Kit descriptions (`KIT_DESC`) must not contain a quote character.
- The queue's `prepare.sh` clones the kernel from GitHub and can stall: verify from the local repository as
  `queue-0084.sh` does (pin commit and tree are still checked).
- A camera bus / driver test only means something when the sensor hub is configured (run `pkg2` + `rotpkg start`
  first); "2 of 2 with the hub idle" in a boot without the sensor stack is the boot state.
- The hwdb entry needs `udevadm control --reload` before the re-trigger; UPower reads the thresholds once at start.
- Never read TLMM pad registers through /dev/mem (run 30 reset the tablet); never read all regmap debug files.
- Foreground `sleep` waits are backgrounded by the user: use background jobs and their completion notices.
- A test that greps "WARNING|BUG|Oops" case-insensitively matches "ramoops" and "debug:": look at the lines.

## 7. Files that matter (WSL `~/mainline/build` unless said)

- Run pipeline: `an/genwf.py`, `gen-combo-NN.py`, `an/area-combo-NN.sh`, `an/area-combo-NN-probe.sh`,
  `prep-area-combo-NN.sh`, `an/chk.sh`, `an/idle-check.sh`, `an/wf-status.sh` (delivery state of the workflows),
  scratchpad `area-combo-NN-chain.sh`, `run-chain.sh`.
- Kernel: `build-q2.sh`, `build-q54.sh`, `build-q55.sh`, `build-q56.sh`, `queue-0077.sh`, `queue-0077-finish.sh`,
  `queue-0084.sh`, `an/stepwise-release.py`, `an/tempalarm-trip-priv.py`, `an/rebase-charging.py`.
- Package: `pkg-016.py`, `pkg-016b.py`, `wf/pkg017/pkg-017.py` (not applied), `wf/camera/cand/wp4-apps/pkg-017-camera.py`.
- Commit: `mk-commit-j.py` / `commit-campaign2-j.sh`, `~/mainline/research/matrix-c2i.py`, `an/commit-check.sh`.
- Snapshot of all this in the project folder: `build/save-project.sh` + `save-project-fix.sh` + `save-project-wf.sh`
  (the last one copies the workflows' public parts to `workflows/` and the newest scripts to `scripts/`; the
  `priv/` and `work/` folders and the whole thermal workflow stay in WSL only).
- Guides: `docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md` (Parts C / D locked until the rehearsal exists).

## 8. First ten minutes of the next session

1. `bash ~/mainline/build/an/idle-check.sh` (nothing running, repos clean) and `adb devices` by line count.
2. `bash ~/mainline/build/an/wf-status.sh` (what each workflow has delivered).
3. Resume the paused agents (section 3), camera first (send run 46's app result), then pencharge, wake, apps,
   audit, pkg017, install.
4. Meanwhile on the tablet: read `wf/deepsleep/NEXT.md` and run it; build q57 (pencharge + pogo) and run
   `wf_pogo` + `wf_pencharge`.
5. Log every run in `WORKLOG.md` (next entry: 29), keep the matrix and the repositories current.
6. Next free numbers: kit run 48, test kernel q57, queue patch 0090, matrix script `matrix-c2k.py`, commit script
   `commit-campaign2-l.sh` (make it with a `mk-commit-l.py` from `mk-commit-k.py`), device package 0.17.

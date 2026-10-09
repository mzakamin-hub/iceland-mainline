# OnePlus Pad 4 mainline Linux - instructions for Claude sessions in this folder

Before doing anything, read in this order:

0. `HANDOVER.md` - the exact state, every workflow with its next
   action, the method (agents prepare, the main session runs the tests), the prompt template, the lessons.
1. `STATE.md` - the goal, the user's hard rules (RAM boot only, private data, commit rules, "hold the tablet"), where
   everything lives, how a test run works.
2. `WORKLOG.md` - the running history: every step tried, its result and the next step. Do not repeat a step that is
   logged there; add an entry after every run or decision.
3. `docs/memory/` - the notes of the earlier sessions (resume points, lessons). The newest block of
   `iceland-resume-point.md` is the short version of where things stand.

Standing orders from the user:

- Keep `WORKLOG.md` and the feature matrix current while working: after each proven result update
  `iceland-mainline/docs/features/features-data.py` (through a `research/matrix-*.py` script), run `build.py`,
  commit with the privacy guards, and republish the matrix page (see `STATE.md`).
- Tests are fully automated; anything that needs the user's hands or eyes is deferred and listed.
- Never flash, unlock, wipe or install; never commit private data; mask the serial, addresses and network names.
- The live work is in WSL (`~/mainline`); this folder is a snapshot plus the log. Refresh the snapshot with
  `build/save-project.sh` + `save-project-fix.sh` after larger changes.

How the work is organised since 2 Oct 2026 

- One background agent ("workflow") per open topic prepares on the PC only (analysis, candidates, a tablet test)
  in WSL `~/mainline/build/wf/<name>/`; the main session reviews, builds, runs the test in a RAM kit run, and sends
  the results back to the agent until the topic is green. Briefs: `docs/WORKFLOW-BRIEF-2.md`, `-3-camera.md`,
  `-4.md`, `-5.md`.
- Runs and waits always go into the background; the completion notice continues the work. The user backgrounds
  every foreground wait.
- When all workflows are green: update the project knowledge and make sure both repositories are pushed.

Hard-won rules for test scripts (details in `WORKLOG.md`):

- Never read every `/sys/kernel/debug/regmap/*/registers`: unclocked MMIO blocks kill the kernel. Read one SPMI
  regmap, only the needed lines.
- GNOME Settings started from a script needs `XDG_CURRENT_DESKTOP=GNOME`; `gnome-screenshot` does not work on GNOME 50.
- Write generator scripts as files (not shell heredocs with escapes inside JSON-quoted commands).
- The kit installs the repo's UCM over the RAM rootfs at boot; the rootfs image itself can be stale.
- Never read TLMM pad registers through /dev/mem for pads Linux does not use (the device tree's
  gpio-reserved-ranges belong to the secure world): one such scan reset the tablet at once (area-combo-30).
- The camera sensors only answer on their I2C bus while a sensor of the ADSP's sensor hub is streaming: camera tests
  hold `monitor-sensor --accel` (or run under a GNOME session with the screen on).
- From Git Bash, `wsl.exe ... bash -c '...'` loses `$variables`, loop variables and backslashes to the outer layer:
  put such commands into a script file and run the file. Never `pkill -f` / `pgrep -f` a pattern that is also in
  the calling command line.
- The camera bus / driver tests need the sensor hub configured first (parts `pkg2` + `rotpkg start`).
- A kit description must not contain a quote character; the queue is verified from the local kernel repository
  (`queue-0084.sh`), the GitHub clone of `prepare.sh` can stall.

- **Ask the owner to connect the tablet and wait for their go before ANY tablet action** (they recharge it
  unplugged); never leave a run chain waiting on `adb devices` in the background. Use they/them for the owner.
- Kits load only their early module list (`build/mods25/all`): generate kits with `genwf.gen(..., coldplug=True)`
  so udev loads the modules of driverless devices as an installed boot does (else e.g. no sound card: it waits for
  the DP audio codec).
- Log checks must ignore the kit's own `iceland-combo` lines in kmsg (the kits write their summaries there).
- Never edit a script that a running bash is still reading; kit preps take the kit lock with `flock -n` (no kernel
  build or queue script while a chain may prep); a `build-q2.sh` build needs the private camera module made by hand
  (`an/camdrv-q78.sh`).
- The install rehearsal U-Boot has no storage driver; `rehearse.ps1` allows only fastboot devices / getvar / boot /
  reboot / `oem console`. The owner alone runs any write; the write-2 probe needs the AVB footer proof first.

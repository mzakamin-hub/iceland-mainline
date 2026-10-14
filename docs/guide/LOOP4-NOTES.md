# OnePlus Pad 4 - Fedora 44 GNOME: loop 4 (the one fixed build)

## Status (14 Oct 2026)

The fixed build of loop 4 (kernel q87, iceland-device 0.22) was superseded in loop 5 (kernel q89b, then q89d, q89e,
q89g on Linux 7.3-rc7, the final golden B149 of 13 Oct 2026). What of loop 4 is in the installed system: the stock
skin loop at 60 / 61 C with critical 70 C, stock's gear table in the policy daemon (the 20-gear policy of iceland-thermal), the sensor service as the user `fastrpc` (proven in r2k), bypass charging from the Quick Settings
toggle, and the Performance profile unchanged (the CPU's top steps add nothing measurable, item 3). Two items moved:
the stock thermal model (item 5) is no longer generated at install time only: since 12 Oct 2026 the decoded generic
stock model is in the firmware package iceland-firmware 11.A.38-3 (owner's decision), and the install-time path is the
fallback. The Fedora 44 install itself was done on 13 Oct 2026. The statements below are the state of 3 Oct.

DRAFT 3 Oct 2026, 15:20 (docs workflow). Scope frozen by the owner at 14:48: ONE fixed build. The fields
the result fields are filled in from the queue push and the fresh-boot test r2m (final or held) before this goes into the
repository. **Nothing had been installed on the tablet by 3 Oct** (the install came on 13 Oct): every result is from RAM boots (test kits), from build runs
on the tablet, and from install rehearsals that boot the real install image from the PC's disk without writing it.
Before loop 4: `RC1-NOTES.md` (q85), `LOOP3-NOTES.md` (q86, libcamera iceland2).

## 1. What loop 4 changes

| Piece | Version | Change | Source of the values |
|---|---|---|---|
| Kernel | **q87** = `7.3.0-rc4-iceland-00328-g70d40415c60b` = q86 + queue 0190.. (iceland-linux 2afea47, pushed) | the skin thermistor's kernel loop at stock's **60 / 61 °C** (was 48 / 51 °C); critical 70 °C kept (item 4) | stock's DT overlay trips on the same sensor (cited in the record, not copied) |
| Device package | **iceland-device 0.22** = 0.21 + the GNOME Shell override order for the bypass toggle (3ebdd993) | the sensor service as the user `fastrpc` with systemd hardening (item 6); the policy daemon at stock's normal table (offset 0, item 4); bypass charging only if every check passes (owner O1); the Performance profile as K120 decides (item 3, owner O4) | stock's thermal control table; upstream hexagonrpc's user and udev rule |
| Install time | the stock shell-temperature model generated on your tablet (item 5, owner O2; not committed) | `/etc/iceland/thermal-model.json`, decoded from your tablet's own files; without it the daemon falls back to battery + 2 °C | your tablet's partitions, read only |
| libcamera | iceland2 stays (iceland3, built with 0004's 2 / 2 frame delays, captures cleanly but failed the ship gate) | kit 119 measured a delay of 2 frames for exposure and gain on both sensors (8 of 8) | the sensors themselves (kit 119 camdelay2) |

## 2. What each run proved

| Run | Build | What | Result |
|---|---|---|---|
| A1 | your Android (LineageOS), read only | CPU tables and a 10 s busy loop, thermal zones and trips, the thermal services | data for items 3-5 (kept private; the numbers below cite it) |
| kit 119 | q86 + iceland-device 0.20 | hardware blocks, CPU top steps, camera delays, bypass, thermal baseline | hardware: watchdog, LLCC + EDAC, 3 bandwidth monitors, 4 GPI DMA engines, QFPROM, USB3 / DP combo PHY, headset jack controls PASS; RNG = the kit's bar (statistics normal); gyroscope not run. Inventory: complete, nothing new. Camera delays 8 of 8 = 2. CPU top steps not delivered (item 3). Bypass: every behaviour step PASS, 2 unit failures test-only (item 7). The device package did not build in that kit, so the sensor services, the gyroscope and the thermal baseline did not run |
| kit 120 | q87 + iceland-device 0.21 | the 60 / 61 °C loop with and without the model, the CPU top steps, the sensor user, gyroscope, RNG round 2, camera delays, the charger input cut | the package PASS (0.21, guard active, thermal daemon at offset 0); 60 / 61 °C: the emulated walk and the 120 s load with and without the model PASS (section 4); top steps +0.3 % / -0.7 % (section 3); charger input cut PASS again; RNG round 2 PASS; camera delays measured with early writes (exposure 1 frame on both sensors, gain 2 rear / 1 front); libcamera
  iceland3 (0004's 2 / 2 frames) builds and captures cleanly but failed the ship gate, so the image keeps iceland2; **the sensor service as fastrpc: FAIL - no sensor reading** (section 6); gyroscope FAIL |
| B run 121 | q87 + 0.21 | the packages built and checked on the tablet | 31 PASS, 2 FAIL: the thermal model was absent - the install-time step could not read the tablet's slot-a system_ext (it is no longer stock: no valid file system where the stock image was); the builder's check PASS (q87, 0.21). Your choice: fix first - the image gets the model decoded on the PC from your backup (O2) |
| B run 122 | q87 + 0.21 + the model from your backup | the same, with the model | **33 PASS, 0 FAIL**; the builder's check PASS |
| rehearsal r2k | golden of B run 122 (0.21) | the evidence run: the install image from the PC's disk, item 6, the thermal model and policy, F43's rekey case on your network | INSTALL-ACCEPT 50 PASS, 1 FAIL: the bypass toggle was disabled (Fedora's GNOME Shell override file sorted after ours; fixed in 0.22). **Item 6 proven** (rotate + sensoruser: all four sensors with the service as `fastrpc`); the thermal model and the policy (60 / 61 / 70 °C, offset 0, the daemon active), the package version, the camera stack, 25 apps and the command line PASS. Kernel-log checks all PASS except F18 (one -EBUSY burst at boot). The debugger's suite 36 / 2 / 6 / 1: its sensor step's timing was fixed test-side; Snapshot and the camera links were not reached because the session sat at the Shell's unlock prompt until 379 s (F53, a rehearsal artefact; a Snapshot test at 621 s streamed); F42 reopened (parity + clash at stream start, sound PASS). F43 on your network: CLOSED: not reproduced with 0189 (the 802.11d scan off, as stock's g11dSupportEnabled=0) - 6 of 6 connects, one real TKIP group rekey (r2i's trigger) survived cleanly in the 1081 s hold, 0 beacon losses, 0 drops, still connected; 802.11d starts 0, country refusals 0 (r2j and kit 116: 6 of 6 too). Ledger check of r2k: 73 records, 50 PASS, 6 FAIL - F01 / F44 (the Snapshot and camera-link steps not reached behind the unlock prompt, F53), F18 (the waived burst), F42 (reopened), F36 / F38 (new GNOME Shell / polkit lines from the keyboard test typing into the unlock prompt: the F53 artefact, to be confirmed) - 17 n/a |
| B run 123 | q87 + **0.22** | the final packages built and checked on the tablet | **33 PASS, 0 FAIL**; the builder's check PASS (0.22); golden committed |
| rehearsal r2l | golden of B run 123 | the final rehearsal (with the rehearsal's shell-mode fix v2 for F53) | **INSTALL-ACCEPT 51 PASS, 0 FAIL, 0 CHECK**; the debugger's suite 38 PASS, 1 FAIL, 5 CHECK, 1 SKIP; bypass charging active on the installed image (the guard, D-Bus, polkit, the Quick Settings extension) |
| ledger G3 | r2l | every finding | 73 records, 43 PASS, 13 FAIL, 17 n/a: one product known issue (F54, below); F55 under investigation; F57-F59 open records |
| fresh-boot test r2m | golden of B run 123 | F55 (microphone after idle) on a fresh boot; decides final or held | HELD: 3 of 10 fresh opens empty, 1 APM timeout (F55); loop 5 first item |

## 3. Item 3 - the CPU's top steps (4.5 / 4.6 GHz)

- **What we saw:** the big cores accept the two top steps, but the clock they deliver does not rise. On mainline a
  single thread runs at 4.24-4.26 GHz with or without them (kit 119; the core passes 100 °C within half a second).
- **Android does the same:** on your LineageOS the best single thread averages 4.28 GHz and a thread pinned to one
  core 3.94 GHz (A1). Neither OS sustains 4.5 GHz.
- **Why:** both kernels ask the CPU firmware for the same levels, and the firmware decides what it delivers (per-core
  temperature and current). Android's small extra comes from moving the hot thread between the two prime cores
  (a vendor scheduler hook and firmware channel that mainline does not have). It is worth a few percent on one
  thread and would need new drivers. It is not part of this build.
- **What changes:** Balanced stays as it is (it already meets your O4: no top steps). For Performance, kit 120
  measures a free thread with and without the top steps: if they gain less than 2 %, the Performance profile stops
  asking for them (it only lowers a request; nothing goes above stock); otherwise they stay in Performance only (O4).
  Kit 120: +0.3 % for a free thread, -0.7 % for a pinned one - the top steps add nothing measurable (its own
  proposal stayed "undecided" because one free window did not start below 50 °C), so **the Performance profile is
  unchanged** (your O4: the top steps only in Performance). Loop 5: the 10 s single-thread gap - mainline 3.73-3.87
  GHz against Android's 4.28 GHz for a free thread (Android moves the hot thread between the prime cores).
- Source: `wf/sleeppower/notes/item3-cpu-turbo.md` (measurements, code references, the fix proposal).

## 4. Item 4 - stock's 60 / 61 °C skin loop and its gears (your decision)

- **What changes:** the kernel's own loop on the skin thermistor next to the chip starts at 60 °C and reaches its
  deepest gear at 61 °C (stock's trip values on that sensor; until now we used a stricter 48 / 51 °C). The critical
  shutdown stays at 70 °C. The policy daemon applies stock's normal gear table (it used the table shifted by 4 gears, so its first CPU cap came
  at 40 °C of case temperature instead of stock's 33 °C).
- **Compared:**

| | OxygenOS (stock) | LineageOS (your Android) | ours (q87 + 0.21) |
|---|---|---|---|
| kernel action on the skin thermistor | none (trips only as markers) | none (the same trips, no cooling) | 60 / 61 °C loop, critical 70 °C |
| case-temperature estimate | OnePlus's service from five sensors | the same service runs | our daemon with the same model (item 5), else battery + 2 °C |
| who applies the gears (CPU / GPU / brightness / charging) | OnePlus's thermal control service | no consumer seen | our daemon, stock's table |
| CPU hot spots | 105 °C limit, 112 °C pause, 114 °C off | the same | 105 °C, 112 °C, 114 °C (clamps instead of pausing) |

  Our build follows stock more closely than LineageOS does: stock's gears, plus a kernel loop on top as a backstop.
- **What decides (chgsafe's rule):** kit 120 runs the load twice, with the model (`thermala`) and without it
  (`thermaln`): the skin must stay at or below 62 °C (every 10 s mean at or below 61 °C after 60 °C), the battery
  below 45 °C, the XO sensor below 78 °C, the CPU below 112 °C, the USB-C connector below 54 °C. Both pass: 60 / 61 °C
  ships. Only `thermaln` fails: 60 / 61 °C only with the model (or a fallback as strict as today's). `thermala`
  fails: the build keeps 48 / 51 °C. Kit 120: both runs PASS - with the model the skin peaked at 52.1 °C (battery
  34 °C, XO 46 °C, CPU 80 °C, USB-C 37 °C), without it at 54.3 °C (35 / 48 / 85 / 38 °C); 60 °C was never reached,
  so the loop itself was shown by the emulated walk (6 steps at 60 / 61 °C, PASS); the policy did 20 of 20 steps
  as stock's table and restored everything. **Verdict: GO** - the charging-safety reviewer's final GO
  (`thermal6061.json` "final_k120") and the power workflow's item-4 GO. Evidence limit: the real load never reached
  60 °C, so the 60 / 61 °C trips were exercised by the emulated walk only; a 20-30 min hand check of a long load
  stays on your list.
- Source: `wf/sleeppower/notes/item4-skin-loop.md`, record `wf/sleeppower/fixes/thermal6061.json`.

## 5. Item 5 - the stock thermal model file (your decision O2)

- **What it is:** stock throttles on an estimate of the case temperature (front, frame, back), computed from five
  sensors with coefficients that OnePlus fitted. They sit in encrypted files of OnePlus's thermal service.
- **B run 121 found no model:** the tablet's slot-a system_ext is no longer the stock image, so the install-time step
  had nothing to decode. Your choice (3 Oct): the image carries the model decoded on the PC from your backup's stock
  files (O2); B run 122 checks it. The install-time path below stays for a tablet whose stock partitions are intact.
- **How it gets onto the tablet:** at install time the read-only extractor copies the three files from your tablet's
  own partitions into a RAM scratch folder; a decoder writes `/etc/iceland/thermal-model.json`; the scratch folder is
  deleted; OnePlus's program never enters the image. If anything fails, there is no model and the daemon uses the
  battery temperature + 2 °C, and the install log says so. Your O2 allows shipping and committing it (private
  repositories only); it is not committed: the image carries it (since B run 121 decoded on the PC from your backup)
  and the repositories do not. [Status 14 Oct: the decoded generic model is now published in iceland-firmware 11.A.38-3;
  see the status block above.]
- **Why it matters:** at idle the fallback is close (within about 2 °C, at most one gear). Under a sustained load it
  lags: after a minute it reads 3.5-4 °C low, two gears too few, so stock's caps apply later and the kernel's
  60 / 61 °C loop does more of the work. Kit 120: with the model the load ended at gear 6, with the fallback at
  gear 5 (one gear fewer, as expected), both within every limit. B run 122 and r2k: the model is in the image and the policy runs with it (thermalmodel,
  thermalpolicy PASS).
- **One fix needed for your Android's version of the program:** the decoder's key search must cover the whole
  program file (LineageOS's is larger than stock's); every candidate key is still proven against the data before it
  is used.
- Source: `wf/sleeppower/notes/item5-thermal-model.md`; licensing / privacy note: the review's (pending).

## 6. Item 6 - the sensor service no longer runs as root

- **What changes:** hexagonrpcd, the file server the sensor hub reads its configuration from, ran as root. It now
  runs as the upstream package's own user `fastrpc`, with systemd hardening (no new privileges, a read-only system,
  private temporary files, restricted socket families).
- **Why it is safe:** it never writes (its file tree is a read-only view; write requests are refused and logged),
  it opens only the DSP device and files below its own tree, and the DSP device already belongs to the `fastrpc`
  group through the upstream udev rule. The one thing that had to change: the DSP tree keeps stock's file modes, so
  a tmpfiles rule makes it readable for `fastrpc` without loosening anything else.
- **Proof:** kit 120 starts the service for the first time under the new user (the hub asks for its files only once,
  early) and checks every file as `fastrpc` before and after the rule, then rotation, light, proximity and the compass
  through iio-sensor-proxy. **Kit 120: FAIL.** The service started as `fastrpc` with the hardening, and every file of
  the hub's tree was readable after the image's rule (602 of 602; 351 were not before it), but no sensor reading came
  through (accelerometer, light, proximity, compass; GNOME got 0 readings; libssc could not open the gyroscope).
  The failure is put down to the late attach: the kit started the service 380-510 s after the sensor DSP, against
  33-181 s in every working run (the debugger and the install workflow agree). **Decision:** the image ships
  0.21 with item 6, and r2k decides (the installed boot, the service as `fastrpc` from boot): its acceptance needs a
  real accelerometer reading (rotate) and the service as `fastrpc` (sensoruser) in the same boot. B runs only build
  the image and never boot it with the sensor hub. The fallback (0.21 without item 6) was ready. **r2k: proven** - rotate + sensoruser, all four sensors with
  hexagonrpcd as `fastrpc`.
- Source: record `wf/install/fixes/sensor-user.json`, kit part `wf/install/cand/sensoruser.sh`, patcher
  `wf/install/cand/iceland-device/item6-sensoruser.py`.

## 7. Bypass charging (your decision O1)

- Kit 119 on the tablet: install, switch on, hold (the level stays, the charger powers the tablet), the charge limit
  still wins, the input cut and the restore all PASS. The 2 unit-test failures came from the test's own folder name
  (test-only, confirmed by the bypass safety reviewer, `wf/bypasssafe/REVIEW-119b.md`); the test is hardened.
- Safety review: GO for iceland-device 0.21; it goes into the image only if every charging, power and charge-limit
  check passes (O1). r2k (0.21): FAIL - the Quick Settings toggle was disabled, because Fedora's GNOME Shell override
  file sorted after ours. Your order (16:22): fix the toggle only - iceland-device 0.22 = 0.21 + the override order
  (`zz_`), reviewed by review, chgsafe and the bypass safety reviewer. r2l: Bypass charging ships (O1): every charging, power and charge-limit check passed - kit 119's behaviour, chgsafe's GO and the bypass safety reviewer's GO - and r2l's installed-image check shows the guard, D-Bus, polkit and the Quick Settings extension active. The wall-charger checks W1-W8 stay on your list.

## 8. What stays open (not in this build)

- **F54 (known issue of this build):** closing the camera can crash WirePlumber once - a libcamera stop race; it
  restarts by itself within 0.3 s. The fix comes in the next loop.
- **F55 (under investigation):** microphone recordings that start after the tablet sat idle can come out silent (the
  audio DSP's q6apm commands time out). A fresh-boot test (r2m) decides whether the image is final or held:
  HELD: r2m, a fresh boot of the golden image, gave 3 of 10 empty mic opens and 1 APM timeout, so the image is held and F55 is the first item of loop 5.
- F57-F59: other new log lines of r2l, open records.
- F18: one -EBUSY burst at boot in r2k (a race after 0188's guard): the build ships with a waiver of at most one
  burst per boot; the fix (k10) is prepared and reviewed for the next build.
- F42 reopened: a SoundWire parity error and bus clash at stream start (sound works): a comparison with stock for the
  next build.
- F53: the rehearsal's session sat at the Shell's unlock prompt (a rehearsal artefact; its fix v2 runs in r2l).
- The gyroscope (kit 120: libssc could not open it), the RGB colour sensor (no Linux user-space path), the CPU
  firmware's prime-core oscillation (item 3).
- Your Wi-Fi keyfile (O3): the copy on the PC is shredded (a leak scan found it nowhere else); the rehearsal overlays
  are being scanned and you decide about them.
- Loop 5: the camera control delays by a phase sweep (the camera subsystem has no frame-start event); the CPU's
  10 s single-thread gap against Android.
- Your hands: a 20-30 min hand check of a long load (how warm the case gets), H1-H3 (charger cut, 9 V charger, notices), the first suspend on the installed system and a night
  unplugged, typing by touch in a dialog, the pen, a USB-C monitor, wall chargers, the keyboard cover, a headset.
- Your install decisions: `docs/INSTALL-GUIDE.md` 0.4 (AVB footer, the RAM probe of the install U-Boot, boot_b or
  recovery_b, open charging / thermal gates, dual boot).

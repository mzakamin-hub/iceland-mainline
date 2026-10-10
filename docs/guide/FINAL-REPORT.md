# OnePlus Pad 4 - mainline Linux + Fedora 44 GNOME: final report of 3 Oct 2026

**Update 10 Oct 2026 (final package):** the image is still HELD. The final install package (q89b-024-b130) is built from the golden of B run 130 (kernel q89b + iceland-device 0.24 + libcamera iceland4), the build the confirmation rehearsal r2w booted (accept 51 / 0 / 0); offline content check 84 PASS / 0 FAIL. Open before the install: the write-2 probe C0, the owner's decisions 1 and 3, Part A step 6 with the AVB proof, the update / rollback rehearsals. See LOOP5-NOTES.md.

**Update 10 Oct 2026 (loop 5):** the image is still HELD. The candidate is kernel q89b (Linux 7.3-rc6, iceland-linux branch iceland-7.3-rc6-q89b) + iceland-device 0.23 + libcamera iceland4; r2v passed the F55 replay for the second time, but the image becomes final only after a clean fresh-boot rehearsal with the fixed checkers, the cable-out idle test and the owner's items. See LOOP5-NOTES.md.

3 Oct 2026, 17:30 (docs workflow). Status of the image: HELD (the fresh-boot test r2m: 3 of 10 mic opens empty, F55). The
result fields are filled in from that test, the queue push of the skin trips (0190), the
ledger's G3 check of r2l and commit z. **Nothing has been installed on the tablet.** Every result is from RAM boots
(test kits), build runs on the tablet, and install rehearsals that boot the real install image from the PC's disk
without writing the tablet. Installing is your decision and your hands.

## 1. Where it stands

- **The build:** kernel q87 (Linux 7.3-rc4 + 138 SM8850 base patches + the Pad 4 queue 0001-0190),
  kernel-iceland K2 / K3, iceland-device 0.22, libcamera 0.7.1 iceland2 (iceland3 failed its ship gate in kit 120), on Fedora 44 Workstation
  (GNOME 50), re-laid for the tablet's 4 KiB storage blocks.
- **The proof:** B run 123: 33 PASS, 0 FAIL; the final rehearsal r2l: INSTALL-ACCEPT 51 PASS, 0 FAIL, 0 CHECK (the
  debugger's suite 38 / 1 / 5 / 1); the ledger's G3 check of r2l: 43 PASS, 13 FAIL, 17 n/a (section 3). The
  evidence rehearsal r2k (0.21, golden of B run 122: 33 / 0): INSTALL-ACCEPT 50 / 1 (the bypass toggle, fixed in
  0.22); item 6, the thermal model and the policy proven there; its ledger check 50 PASS, 6 FAIL (F01 / F44 not
  reached behind the unlock prompt = F53, F18 waived, F42, F36 / F38 = the keyboard test typing into the unlock prompt), 17 n/a.
- **The feature matrix:** 73 working, 11 in progress, 6 not started, 2 not planned of 92 rows (after kit 119: 69 / 15 / 6 / 2; the published page and `docs/FEATURES.md`).
- **The repositories (private):** iceland-linux (the kernel queue: 0186-0188 = a9b55d4, 0189 = 67adee0,
  iceland-linux 2afea47), iceland-mainline (docs, matrix, packaging, test logs: commit x 9002850 = RC1, commit y 6213410 =
  loop 3, commit z = this build, its id in the WORKLOG), iceland-u-boot (the boot loader for the install).

## 2. The day in four loops

| Loop | Build | What it fixed | Proof |
|---|---|---|---|
| 1 (final build of the night) | q84 + iceland-device 0.19 | the r2g findings F1-F24: Camera app, full-size captures, battery guard v3.1 with the charger input cut, Wi-Fi country, first-boot setup, disk scheduler, no `*_ignore_unused` | B run 109 31 / 0; r2h 45 / 0 / 0 |
| 2 = RC1 | q85 (+ 0186-0188) | the headset codec's error flood (F18) | kit 110; B run 112 31 / 0; r2i 46 / 0 / 0 |
| 3 | q86 (+ 0189) + 0.20 + libcamera iceland2 | Wi-Fi 802.11d scan off (F43 suspect), libcamera sensor data (F5) and link handling (F44) | kits 115-117; B run 118 31 / 0; r2j 45 / 0 / 1 |
| 4 = the fixed build | q87 + 0.22 | stock's 60 / 61 °C skin loop, the sensor service as fastrpc, the CPU profile, bypass (if every check passes), the thermal model at install time | kits 119 / 120; B runs 121-123; r2k (evidence); B run 123 33 / 0; r2l 51 / 0 / 0 |

Details: `docs/guide/RC1-NOTES.md`, `LOOP3-NOTES.md`, `LOOP4-NOTES.md`; the history `docs/guide/06-PROCESS-HISTORY.md`
and `docs/WORKLOG.md`.

## 3. Known issues of the fixed build

From r2l's ledger check (73 records: 43 PASS, 13 FAIL, 17 n/a):
- **F54 - the one product known issue:** closing the camera can crash WirePlumber once (a libcamera stop race); it
  restarts by itself within 0.3 s; the fix comes in the next loop;
- **F55 - under investigation:** microphone recordings that start after the tablet sat idle can come out silent (the
  audio DSP's q6apm commands time out); you ordered a fresh-boot test (r2m) before the image is called final:
  HELD: the image waits for loop 5 (F55 first);
- F57-F59: other new log lines of r2l, open records;
- F18: one -EBUSY burst at boot in r2k (a race after 0188's guard) - the build ships with a waiver (at most one burst
  per boot); the fix k10 comes with the next build;
- F42 reopened: a SoundWire parity error and bus clash at stream start (sound works) - a stock comparison for the
  next build;
- F53: the rehearsal's session sat at the Shell's unlock prompt - a rehearsal artefact, its fix v2 runs in r2l;
- F43 (Wi-Fi): closed: not reproduced with 0189 (the 802.11d scan off, as stock's g11dSupportEnabled=0) - 6 of 6 connects, one real TKIP group rekey (r2i's trigger) survived cleanly in the 1081 s hold, 0 beacon losses, 0 drops, still connected; 802.11d starts 0, country refusals 0 (r2j and kit 116: 6 of 6 too);
- the gyroscope is not shown yet; the RGB colour sensor has no Linux user-space path;
- the 60 / 61 °C trips were exercised by an emulated walk only (the real load stayed at 52-54 °C);
- loop 5: the camera control delays by a phase sweep (the image keeps iceland2's), the CPU's 10 s single-thread gap
  against Android (3.73-3.87 vs 4.28 GHz; the top steps add nothing on either OS).

## 4. Checks only you can do

| Check | How long | What it shows |
|---|---|---|
| H1: unplug the cable for real while the charger input cut holds | a few minutes | the cut and its restore with a real cable |
| H2: a wall charger at 9 V after a cut is released | about 15 min | charging comes back at the charger's 9 V |
| H3: the charge notifications | a minute | the desktop notices read and look right |
| A 20-30 min long load (a game or a video export) with your hand on the case | 30 min | how warm the case gets with stock's 60 / 61 °C loop and gears |
| The first suspend on the installed system, then one night unplugged | a night | sleep without the `*_ignore_unused` flags and the real standby drain |
| Typing by touch in a dialog (e.g. a password prompt) | a minute | the on-screen keyboard in a modal dialog |
| The pen on the magnet side | about 90 s | pen charging and pen input |
| A USB-C monitor or dock; USB accessories; a USB headset; an analog USB-C headset | a few minutes each | DisplayPort and DP audio, host mode and SuperSpeed, headset detection |
| Wall chargers (5 V USB-A, USB-C PD, the OnePlus charger) | about 20 min | the charge-current limits off the PC port |
| The keyboard cover (pogo) | a few minutes | keys, touchpad, lamps, backlight, wake by a key |
| Bypass charging from the Quick Settings toggle (if it ships) | a few minutes | W1-W8 of the bypass workflow |

## 5. Your decisions

Taken today: stock's 60 / 61 °C skin loop; O1 bypass charging in the image only if every check passes; O2 the thermal
model file generated at install time (allowed to ship and to commit in private repositories; not committed: the
image carries it); O3 the Wi-Fi keyfile kept
until r2k (then deleted); O4 the CPU's top steps only in Performance; the camera driver and its tuning in the private
repositories; Fedora only for now; the write-2 probe C0 first.

Open, before the install (`docs/INSTALL-GUIDE.md` 0.4): the AVB hash footer on the install U-Boot; one read-only RAM
boot of the exact install U-Boot before C0; U-Boot's permanent place (`boot_b` or `recovery_b`, decided by C0);
whether an open charging / thermal check blocks the install; held boot-code updates, release pin, LibreOffice /
GNOME Web, a day-0 snapshot; a way back to LineageOS or stock only; later: a hardware watchdog, dual boot.

## 6. How to continue

- The install: `docs/INSTALL-GUIDE.md` (Part A read only -> C0 -> write 1 -> write 2), each write only with your OK.
- The project state for a new session: `HANDOVER.md`, `STATE.md`, `WORKLOG.md` in the project folder; the team's
  workflows in WSL `~/mainline/build/wf/<name>/`; the ledger `wf/ledger/LEDGER.md`.
- Private and never committed: your backup and stock images, firmware trees, camera traces / photos, `wf/*/priv`,
  the rehearsal log bundles, the serial and the Bluetooth / Wi-Fi addresses, the Wi-Fi keyfile (deleted after r2k).

# OnePlus Pad 4 - Fedora 44 GNOME: release candidate 1 (RC1)

3 Oct 2026, 12:10 (docs workflow), with the results of B run 112, the rehearsal r2i, the ledger's G3 check of r2i
and the queue push of 0186-0188. **Nothing has been installed on the tablet**: every result here is from RAM boots (test kits), from build runs on the tablet, and from install
rehearsals that boot the real install image from the PC's disk without writing the tablet.

## 1. What RC1 is

| Piece | Version | What is new against the q84 build (r2h, 45 / 0 / 0) |
|---|---|---|
| Kernel | **q85** = `7.3.0-rc4-iceland-00324-ge0373b2308fc`: Linux 7.3-rc4 + 138 SM8850 base patches + the Pad 4 queue 0001-0185 (iceland-linux cd0bf55) + **0186-0188** (queued and verified: iceland-linux a9b55d4, the queued tree equals q85's) | the three headset-codec fixes for F18 (below) |
| Kernel packages | K2 `kernel-iceland-7.3.0~rc4.iceland.00324.ge0373b2308fc-1.fc44`, K3 `...ge0373b2308fc.1-1.fc44` (the twin for the update rehearsal) | rebuilt from q85 |
| Device package | P1: `iceland-device` 0.19, the package of B run 109 (battery guard v3.1 with the charger input cut, PipeWire 1.6.8 or newer, Wi-Fi regulatory domain US, no TPM modules in the initramfs, the UFS scheduler one disk at a time, no `*_ignore_unused` flags, the camera tuning) | unchanged |
| Tablet-side tooling | TIN: the rehearsal / install bundle the tablet receives (acceptance list, tablet script, firmware extractor, rescue script) | as for r2h |
| Left out | the USB-C jack mode (k5), see section 3 | - |

The three kernel fixes (queue 0186-0188, written by the klog workflow from r2f / r2g / r2h's logs):
- **0186** `ASoC: codecs: wcd-common`: the codec's interrupt loop stops when a status register cannot be read. Before,
  a suspended codec left stale status words and the loop called the nested handlers again and again.
- **0187** `ASoC: codecs: wcd-mbhc-v2`: the headset plug-detect work wakes the codec first, as the other headset
  paths already did. Before, it read the codec while it was asleep and every read failed with -16.
- **0188** `ASoC: codecs: wcd939x`: no impedance measurement when the codec cannot be read. Before, each failed read
  counted as a result, the loop ran its full 900 rounds per channel and logged about 3600 "ASoC error (-16)" lines
  for one plug event (finding F18).

## 2. What each run proved

| Run | Build | What | Result |
|---|---|---|---|
| kit 106 | q84 | the charger input cut v3.1 at a hot USB-C connector; sleep | the lever, the guard and the restore PASS (219 unit checks); sleep PASS |
| kit 108 | q84 | sleep | PASS (the kit's U-Boot still passes the `*_ignore_unused` flags) |
| B run 107 / 109 | q84 + 0.19 | the packages built and checked on the tablet | 30 / 1 (a dracut TPM unit; F10 amended), then **31 PASS, 0 FAIL** |
| rehearsal r2h | q84 + 0.19 | the real install image from the PC's disk | **INSTALL-ACCEPT 45 PASS, 0 FAIL, 0 CHECK**; the debugger's suite 29 PASS; the Camera app works (PipeWire 1.6.9); the rehearsal guard ran its full 1500 s |
| kit 110 | **q85** | the F18 fixes, sound, sleep | **F18 PASS**: no WCD "-16" line in the boot, the headset-detection interrupt exercised, the headset codec's bus without a clash or a parity error; F17 PASS (no port-count line, the microphones record: 217 KB captured); the first sleep after boot fixed (a 21 s sleep woken by the clock; CX collapse reached, 78 % in the probe); GPU faults 0 |
| kit 111 | q85u = q85 + k5 | the USB-C jack mode (opt-in candidate) | its probe PASS (USB high speed and the DisplayPort switch unaffected, no failed or deferred line; no headset was plugged in); F18 PASS; the first sleep fixed (CX collapse reached, 76 % in the probe) |
| B run 112 | q85 + 0.19 | the RC's packages built and checked on the tablet | **31 PASS, 0 FAIL**; the builder's RC check 8 / 8 (the kit ran q85; its boot entry, device tree and initramfs; the installed `kernel-iceland-...00324.ge0373b2308fc-1`, one kernel; `iceland-device` 0.19) |
| rehearsal r2i | q85 + 0.19 | the RC's install image from the PC's disk | **INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK** (r2h's 45 + a new check of the kernel command line: q85, no `*_ignore_unused`); the klog probes **14 / 14 PASS** on the installed image (F18: no WCD "-16" line, the headset-detection interrupt exercised, no bus clash or parity error); the debugger's suite 32 PASS, 2 FAIL, 3 CHECK, 1 SKIP (the Camera app started 6 times without a crash; the FAILs are F44 and a suite index bug, section 2a); Fedora's first-boot setup was on the screen and the owner joined their Wi-Fi in it; the session guard extended to 1500 s as designed |
| ledger G3 | r2i | 62 records (F1-F50, B-ids, chgsafe, sleep) | **51 PASS, 7 FAIL, 4 n/a** (the first check, with 55 records: 44 / 7 / 4); **F18 reaches G3** (kit 110 + r2i); the 7 FAILs in section 2a |

Kits 110 and 111 also showed the kit-only probe verdicts klog-f11 FAIL (setregdomain still fails once; phy0 stays US), klog-f12 FAIL (irqbalance is not running in the kit) and klog-f20 FAIL (3-5 Wi-Fi probe attempts before
the link; Wi-Fi came up). On r2i, with the installed system's services, the same probes passed (14 / 14: f12 benign,
f20 two probe attempts, f31 benign).

### 2a. The ledger's 7 FAILs on r2i, plainly

| Id | What failed | What it means |
|---|---|---|
| F01 | the debugger's Snapshot step | F44 (section 3a), not F1: the app itself started 6 times without a crash |
| F02 | the line with the full-size frame | a suite index bug: this boot listed the two cameras in the other order; the kernel side passed (system heap only, no CMA failure, full-size frames) |
| F05 | libcamera's sensor data | deferred (section 3) |
| F08, F31 | a new WirePlumber line in their subsystem ("failed to activate item") | the findings themselves passed (F31's probe: benign); the new line is recorded as F50 and being classified |
| F43, F44 | the known issues of RC1 | section 3a |

F36 and F38 failed in the first check and pass in the newest one: their new lines (a GNOME Shell timeout when
NetworkManager asks again for the Wi-Fi secret, polkit / pkexec lines) became the benign records F46-F49 (install
workflow; the debugger and the reviewer to confirm).

## 3a. Known issues of RC1

| Id | What you notice | Cause | When |
|---|---|---|---|
| F43 | **Wi-Fi**: on the owner's network the connection drops after about 110 s, and every reconnect (2.4 and 5 GHz) fails until a reboot; GNOME then says "Activation of network connection failed" | found: the Wi-Fi firmware's 802.11d scan (country detection) is re-armed at every disconnect; stock switches 802.11d off. r2i was the first real Wi-Fi association on mainline: earlier images had no saved network | fix k9 in loop 3, then a reconnect test on the owner's network |
| F44 | the Camera app (Snapshot) can fail to start a camera when another camera program used the other camera since login | a stale link in the camera pipeline ("Device or resource busy") | loop 3 (camfix) |
| F45 | GNOME Software can abort after a network change | an upstream GTK 4 accessibility assertion | benign (recorded by the install workflow; the debugger and the reviewer to confirm) |

## 3. Deferred (not in RC1)

| Item | Why | When |
|---|---|---|
| F5: libcamera's data for the SC1320CS / SC820CS sensors | the cameras work with libcamera's generic model (exposure and gain less exact than stock); the sensor data needs a libcamera change | later (camfix) |
| The USB-C jack mode (k5) | describes the codec-to-switch link as the SM8650 boards do, so headset detection only runs for an analog USB-C accessory. Kit 111 shows it breaks nothing, but no headset has been tested with it | opt-in after a test with your headset (owner's decision, 3 Oct) |
| Bypass charging | built and reviewed by the bypass safety reviewer (wf/bypasssafe, REVIEW.md) | your decision (2 Oct): later |
| F50 (the new WirePlumber line), F46-F49 (benign records) | F50 is being classified; F46-F49 wait for the debugger and the reviewer (F12 and F17 passed on r2i) | the ledger, after r2i |

## 4. Checks only the owner can do (for the final report)

| Check | How long | What it shows |
|---|---|---|
| H1: unplug the cable for real while the charger input cut holds | a few minutes | the cut and its restore with a real cable, not only the emulation |
| H2: a wall charger at 9 V after a cut is released | about 15 min | charging comes back at the charger's 9 V |
| H3: the charge notifications | a minute | the desktop notices read and look right |
| A Wi-Fi reconnect on your network after the F43 fix (loop 3) | a few minutes | the connection survives a drop and a group rekey |
| The first suspend on the installed system, then one night unplugged | a night | sleep without the `*_ignore_unused` flags (every kit still had them) and the real standby drain (target about 1 % per hour or less) |
| Typing by touch in a dialog (e.g. a password prompt) | a minute | the on-screen keyboard in a modal dialog (F38) |
| The pen on the magnet side | about 90 s | pen charging, and whether the boost follows the pen's 10 V request |
| A USB-C monitor or dock | a few minutes | DisplayPort and DP audio |
| Wall chargers (5 V USB-A, USB-C PD, the OnePlus charger) | about 20 min | the charge-current limits off the PC port |
| The keyboard cover (pogo) | a few minutes | keys, touchpad, Caps Lock lamp, backlight, wake by a key |

Also useful once: USB accessories and a USB headset (host mode), the 5 GHz password, the default apps by finger, the
cameras' colours and sharpness, 144 Hz.

**The install decisions** (before the steps named; details in `docs/INSTALL-GUIDE.md` 0.4 and `docs/INSTALL-PLAN.md` 9):
1. (C0) The AVB hash footer on the install U-Boot, signed with the AOSP test key that `vbmeta_b` already chains
   `boot` with.
2. (C0 step 0) One read-only RAM boot of the exact install U-Boot before C0 (recommended).
3. (after C0) U-Boot's permanent place: `boot_b` only if C0 shows the boot loader does not count down slot b;
   otherwise `recovery_b`.
4. Whether an open charging / thermal check blocks the install or only sets "charge attended, charge limit on".
5. Held boot-code updates, Fedora pinned to 44, LibreOffice and GNOME Web in the image, the skin temperature limit, a
   day-0 snapshot.
6. A way back to LineageOS after the install, or the return to stock OxygenOS only.
7. Later: a hardware watchdog on the installed system; dual boot (`docs/DUALBOOT-PLAN.md`, decided before write 1).

The writes are the owner's alone: Part A (read only) -> C0 (the write-2 probe, undone the same day) -> write 1
(`userdata`) -> write 2 (the boot path), each with its checks (`docs/INSTALL-GUIDE.md`).

## 5. Where the evidence is

The kit and build-run logs (`docs/tests/area-combo-106` to `-112`), the ledger's checks (`relay/results/pc-016-020/wf/
ledger/check-*.md`; the r2i check and its scripts come with the loop-3 commit), the fix records' text (`relay/results/pc-016-020/wf/klog/cand/`), the queue commit for 0186-0188
(iceland-linux a9b55d4), the release notes of the q84 build (`docs/RELEASE-NOTES.md`). The rehearsal
logs (r2h, r2i) stay private; their findings are in the ledger.

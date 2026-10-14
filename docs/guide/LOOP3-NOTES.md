# OnePlus Pad 4 - Fedora 44 GNOME: loop 3 (after release candidate 1)

## Status (14 Oct 2026)

Loop 3 is closed and superseded. Its kernel (q86, Linux 7.3-rc4) and its libcamera iceland2 build went on through loop 4
and loop 5; the image they fed was never installed. Results of this loop that still stand: the F43 Wi-Fi drop was not
reproduced with the 802.11d scan off (patch 0189 stays, it is stock's setting), and F5 (sensor data) and F44 (camera
links) were proven here (kit 117, r2j). After this loop: the final golden B149 (kernel q89g on Linux 7.3-rc7, committed
13 Oct 2026 15:45, rehearsal r158 with 0 FAIL) and the Fedora 44 install on the tablet on 13 Oct 2026. For the path
from here see [LOOP5-NOTES.md](LOOP5-NOTES.md) and [FINAL-REPORT.md](FINAL-REPORT.md). The version numbers and the
"nothing installed" statements below are the state of 3 Oct.

3 Oct 2026 (docs workflow), with the results of the rehearsal r2j, the ledger's G3 check of r2j and the queue push of
0189 (iceland-linux 67adee0). **Nothing had been installed on the tablet by 3 Oct** (the install came on 13 Oct):
every result here is from RAM boots (test kits), from build runs on the tablet, and from install rehearsals that boot
the real install image from the PC's disk without writing the tablet. RC1 itself: `RC1-NOTES.md`.

## 1. What loop 3 changes against RC1

| Piece | Version | Change |
|---|---|---|
| Kernel | **q86** = `7.3.0-rc4-iceland-00327-g1833a6deb42d`: queue 0001-0188 + **0189** (queued and verified: iceland-linux 67adee0) | 0189 `wifi: ath12k`: the firmware's 802.11d scan is off by default (`ath12k.enable_11d=1` restores upstream's behaviour); stock's Wi-Fi driver runs with `g11dSupportEnabled=0` (findings F43, F11) |
| Kernel packages | K2 `kernel-iceland-7.3.0~rc4.iceland.00327.g1833a6deb42d-1.fc44`, K3 `...g1833a6deb42d.1-1.fc44` | rebuilt from q86 |
| Device package | `iceland-device` 0.20 (P1) | version and changelog for the new libcamera build; everything else as 0.19 |
| libcamera | our build `0.7.1-1.fc44.iceland2` (in the image through the local repository) | 0004: libcamera's data for the SC1320CS / SC820CS sensors (F5); 0005: the simple pipeline no longer trusts its cached link flags - both sensors share one CSID, which allows only one enabled link (F44) |

## 2. What each run proved

| Run | Build | What | Result |
|---|---|---|---|
| kit 113 | q85 | libcamera iceland2 built in RAM; camera control delays | built (5 rpms, GPU acceleration yes, 5 of 5 patches); its first `cam -l` saw 0 cameras because the camera modules were not loaded yet at that step (test order). Delays: only the rear sensor's gain delay (2) was seen, so 0004 keeps empty delays |
| kit 114 | q85 | the libcamera check | not run: a test-tool bug (cpio missing in the kit), fixed for kit 117 |
| kit 115 | q86 | F43 A/B without a network | **PASS**: with the 802.11d scan off the firmware starts it 0 times and refuses no country request; switched on (`enable_11d=1`): 4 starts, 2 refusals; off again: 0 / 0 |
| kit 116 | q86 | F43 on the owner's network (their OK; the network's keyfile in RAM only, root-only, never logged) | every phase PASS (6 / 6 connects each, held 10 min) - also with 802.11d switched on: r2i's failure was **not reproduced**, so the 802.11d cause of F43 is not proven; k9 is harmless |
| kit 117 | q85 | the libcamera check with iceland2 | **F5 proven**: both sensors report UnitCellSize 1120x1120 and no "No static properties" line; captures on iceland2, 10 frames from each camera. F44 was not exercised (the test pipeline was never linked): its proof moved to r2j |
| B run 118 | q86 + 0.20 + iceland2 | the loop-3 packages built and checked on the tablet | **31 PASS, 0 FAIL**; the builder's check 8 / 8 |
| rehearsal r2j | golden of B run 118 | the install image from the PC's disk (up to 2400 s, with klog's F43 test on the owner's network) | **INSTALL-ACCEPT 45 PASS, 0 FAIL, 1 CHECK** (a test-side desktop id); the klog checks 14 PASS on the installed image; the debugger's suite 33 PASS, 2 FAIL, 5 CHECK, 1 SKIP - the 2 FAILs were the session's lock state (Snapshot never asked for the camera), and the same steps re-run on the same boot passed: Snapshot streams (F1), camera links in both orders (F44); sensor properties (F5) and full-size captures (F2) pass; the sound loopback CHECK was the tablet lying face-down. 3 Oct 13:47-14:18, ended by main's early reboot after all tests |
| ledger G3 | r2j | F01 / F02 / F05 / F44 / F43 | first check 51 PASS, 5 FAIL, 13 n/a (F05 the expected line's form, F17 / F42 a new SoundWire line, F23 the face-down tablet, F43 waits for r2k); after the record fixes and main's test-position waiver: 69 records, **55 PASS, 0 FAIL**, 1 await (F43, for r2k), 13 n/a |

## 3. F43 (Wi-Fi) - what is known

- r2i: on the owner's network the connection dropped after about 110 s and every reconnect failed until a reboot.
- klog's analysis: ath12k re-arms the firmware's 802.11d scan at every disconnect and starts it with the next host
  scan, so authentication and the handshake can run while the firmware scans off-channel; stock switches 802.11d off.
  0189 does the same.
- Kit 115 shows the scan off with 0189; kit 116 could not reproduce r2i's failure even with the scan on.
- r2j on the installed image, again on the owner's network: 6 of 6 reconnects, 0 drops, connected after the hold.
  F43 is **not reproduced with the 802.11d scan off**; 0189 stays (it is the stock setting). r2i's original trigger,
  a TKIP group rekey, is checked once more in r2k (the ledger keeps F43 at "await" until then).
- The owner's network keyfile stays private (decision O3: kept until r2k, deleted after the last F43 test); it is never
  committed - the commit script checks that the network's name and password are in no staged file.

## 4. The owner's decisions for loop 4 (3 Oct, about 13:45)

- The skin temperature loop at stock's 60 / 61 °C with its gear policy (kernel q87; implemented and proven before it
  ships, never above stock).
- O1: bypass charging goes into the image (iceland-device 0.21) if it passes every charging, power and charge-limit
  check.
- O2: the stock thermal model file is generated on the owner's tablet at install time, and it may be shipped and
  committed (private repositories).
- O3: the Wi-Fi keyfile is kept until r2k if F43 is still open after r2j.
- O4: the CPU's top steps (4.5 / 4.6 GHz, if Android reaches them) only in the Performance power mode.

Loop 4: kernel q87 (queue 0190.., the 60 / 61 °C loop) and iceland-device 0.21 -> kits 119 / 120 -> B run 121 -> r2k.

## 5. Where the evidence is

The kit and build-run logs (area-combo-113 to -118, not published; run 116 ran on the owner's network and has no
journal), the ledger's checks (not published), klog's 0189 record text and camfix's libcamera patches and recipe (not
published as separate files). The rehearsal logs stay private; their findings are in the ledger.

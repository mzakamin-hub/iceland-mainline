# OnePlus Pad 4 - mainline Linux + Fedora 44 GNOME: final report of 3 Oct 2026

## Status (14 Oct 2026)

- **Installed on 13 Oct 2026.** The owner wrote the install image (built from the final golden B149; sha256 prefix
  `2246e9a7`) to `userdata` at 18:31, and the footered U-Boot install build v3 (`4955ee98`) to `boot_b` at 20:47. Fedora 44
  GNOME booted from `boot_b` at 20:48. The image itself is private; the repositories describe its hashes only.
- **The image is no longer HELD.** The final golden B149 was committed on 13 Oct at 15:45 after rehearsal r158
  (64 rows, 0 FAIL, no regression against r141).
- **Versions now:** kernel q89g = `7.3.0-rc7-iceland-00426-g520e85da9244` (Linux 7.3-rc7; the rc4 and rc6 builds named
  below are superseded); iceland-device 0.28-7 installed, 0.28-8 committed on 14 Oct (slot-mark fix, screen-off thermal
  table, boost ceiling); iceland-firmware 11.A.38-3; libcamera 0.7.1-2 from Fedora.
- **Slot marking:** on the installed system the boot counter did not mark slot b by itself (the root is a loop device
  on `userdata` and the boot LUN is read-only); the owner marked slot b by hand on 14 Oct. The fix is in 0.28-8.
- **Working features:** [docs/FEATURES.md](../FEATURES.md).
- **Publication:** all four repositories are public since 14 Oct 2026.
- The body below is the state of 3 Oct unless a line says otherwise. Where a line names a removed path or a private
  working note, that note is not published.

**Update 10 Oct 2026 (final package):** the final install package (q89b-024-b130) is built from the golden of B run 130 (kernel q89b + iceland-device 0.24 + libcamera iceland4), the build the confirmation rehearsal r2w booted (accept 51 / 0 / 0); offline content check 84 PASS / 0 FAIL. See LOOP5-NOTES.md.

**Update 10 Oct 2026 (loop 5):** the candidate is kernel q89b (Linux 7.3-rc6, iceland-linux branch iceland-7.3-rc6-q89b) + iceland-device 0.23 + libcamera iceland4; r2v passed the F55 replay for the second time. See LOOP5-NOTES.md.

3 Oct 2026, 17:30 (docs workflow). The
result fields are filled in from the queue push of the skin trips (0190), the
ledger's G3 check of r2l and commit z. **Nothing had been installed on the tablet by 3 Oct** (the install came on 13 Oct). Every result is from RAM boots
(test kits), build runs on the tablet, and install rehearsals that boot the real install image from the PC's disk
without writing the tablet. Installing is your decision and your hands.

## 1. Where it stands

- **The build (3 Oct; the installed build is q89g, see the status block):** kernel q87 (Linux 7.3-rc4 + 138 SM8850 base patches + the Pad 4 queue 0001-0190),
  kernel-iceland K2 / K3, iceland-device 0.22, libcamera 0.7.1 iceland2 (iceland3 failed its ship gate in kit 120), on Fedora 44 Workstation
  (GNOME 50), re-laid for the tablet's 4 KiB storage blocks.
- **The proof:** B run 123: 33 PASS, 0 FAIL; the final rehearsal r2l: INSTALL-ACCEPT 51 PASS, 0 FAIL, 0 CHECK. The evidence rehearsal r2k (0.21, golden of B run 122:
  33 / 0): the thermal model and the policy proven there.
- **The working features:** `docs/FEATURES.md`.
- **The repositories (private on 3 Oct; public since 14 Oct):** iceland-linux (the kernel queue: 0186-0188 = a9b55d4, 0189 = 67adee0,
  iceland-linux 2afea47), iceland-mainline (docs, matrix, packaging, test logs: commit x 9002850 = RC1, commit y 6213410 =
  loop 3, commit z = this build, its id in the private work log), iceland-u-boot (the boot loader for the install).

## 2. The day in four loops

| Loop | Build | What it fixed | Proof |
|---|---|---|---|
| 1 (final build of the night) | q84 + iceland-device 0.19 | the r2g findings F1-F24: Camera app, full-size captures, battery guard v3.1 with the charger input cut, Wi-Fi country, first-boot setup, disk scheduler, no `*_ignore_unused` | B run 109 31 / 0; r2h 45 / 0 / 0 |
| 2 = RC1 | q85 (+ 0186-0188) | the headset codec's error flood (F18) | kit 110; B run 112 31 / 0; r2i 46 / 0 / 0 |
| 3 | q86 (+ 0189) + 0.20 + libcamera iceland2 | Wi-Fi 802.11d scan off (F43: 6 of 6 connects and a group rekey survived in r2j and kit 116), libcamera sensor data (F5) and link handling (F44) | kits 115-117; B run 118 31 / 0; r2j 45 / 0 / 1 |
| 4 = the fixed build | q87 + 0.22 | stock's 60 / 61 °C skin loop, the sensor service as fastrpc, the CPU profile, the thermal model at install time | kits 119 / 120; B runs 121-123; r2k (evidence); B run 123 33 / 0; r2l 51 / 0 / 0 |

Details: `docs/guide/RC1-NOTES.md`, `LOOP3-NOTES.md`, `LOOP4-NOTES.md`; the history `docs/guide/06-PROCESS-HISTORY.md`
and `docs/WORKLOG.md`.

## 3. Your decisions

Taken on 3 Oct: stock's 60 / 61 °C skin loop; O2 the thermal
model file generated at install time (allowed to ship and to commit in private repositories; not committed: the
image carries it); O3 the Wi-Fi keyfile kept
until r2k (then deleted); O4 the CPU's top steps only in Performance; the camera driver and its tuning in the private
repositories; Fedora only for now; the write-2 probe C0 first.

## 4. How to continue

- The install: `docs/INSTALL-GUIDE.md` (Part A read only -> C0 -> write 1 -> write 2), each write only with your OK.
  Done on 13 Oct 2026 (see the status block).
- The project's working notes, the ledger and the team's workflow folders are private and not published.
- Private and never committed: your backup and stock images, firmware trees, camera traces / photos, `wf/*/priv`,
  the rehearsal log bundles, the serial and the Bluetooth / Wi-Fi addresses, the Wi-Fi keyfile (deleted after r2k).

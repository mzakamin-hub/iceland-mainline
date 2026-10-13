# OnePlus Pad 4: guide for installing Fedora 44 GNOME on the tablet

Written 2 Oct 2026, revised the same evening (install workflow round 7: the write-2 probe C0 first, the review's
R-1 / R-2 / R-4 / R-8 / R-9 points, the slot-retry finding). This is the step-by-step companion of
`docs/INSTALL-PLAN.md` (the reasons are there; the steps are here). **Edition: 3 Oct 2026, release candidate 1 (kernel q85 = queue 0001-0188, iceland-device 0.19, rehearsal r2i 46 / 0 / 0)**: adds the
first-boot setup note (Part C step 4) and section 11 (known issues and what this build fixes). **Final edition 13 Oct 2026 (morning): the final golden B147 (kernel q89e = v7.3-rc7 + iceland-device 0.28-5 +
iceland-firmware 11.A.38-3), accepted after the final rehearsal r156 / r156u / r156ub (only FAIL: the known F54
libcamera race, accepted by you); the install image is rebuilt from B147 and HELD for your two writes (section 0.1,
Part B, section 10). It replaces the B145 image of 12 Oct. The speaker level is your choice (+9 dB): a listening
check follows the install.** On 10 Oct the install-day steps ran: the read-only checks, and four
C0 probes that wrote `boot_b` and undid it the same day. No `userdata` write has been done and Fedora is not installed.
Every write is done by you, one command at a time, after its own checks.

**Read section 0 first.** The order is: Part A (read only) - Part B (the rehearsal from RAM, no write) - **Part C0
(the write-2 probe: U-Boot into `boot_b` while Android's data is still there, undone the same day)** - Part C (write
1) - Part D (write 2). Parts C and D stay locked until Part B has produced its files and checksums and C0 has passed.

---

## 0. Where things stand, and the rules

### 0.1 Readiness (state on 12 Oct 2026; update this table before you start)

Sources: the Loop 5 log (`OnePlusPad4-Loop5\WORKLOG.md`, `R138-TRACKER.md`, `STATE-2026-10-12-0230.md`,
`STATE-2026-10-12-1220.md`),
`docs/R138-PLAN.md`, `docs/SOUND-PLAN-2026-10-12.md` and `docs/AUTOMATE-FINAL-2026-10-12.md`. Run names are as they appear there. A **golden** is the B-run build of the rehearsal image.

| Item | State on 12 Oct 2026 | Needed for |
|---|---|---|
| G1 full backup of all 151 partitions, checksummed (`C:\OnePlusPad4\backups\20260927-1933-unknown`) | exists; checked on the install day (10 Oct): G1 151 OK. The first check failed because two partitions are both named `last_parti`; their read-only copies are in a supplement to the hash list. It predates LineageOS: it is the return-to-stock source, **not** the undo of write 2 | everything |
| G2 stock 11.A.38 images + checksums (`C:\OnePlusPad4\stock-11.A.38`) | exists; 9 stock images checked OK on 10 Oct | return to stock |
| G3 return-to-stock scripts (`C:\OnePlusPad4\scripts\30-`, `31-`, `39-`) and their dry run | scripts exist; the dry run (Part A step 3) is **not recorded** in the Loop 5 log: open | return to stock |
| G4 second copy of G1 + G2 on another disk | **OPEN (owner)**: on 10 Oct drive D: had 2.5 GB free for an 18 GB copy (WORKLOG, 10 Oct) | write 1 |
| G5 file copy of Android's `/data/vendor` | **done 10 Oct**: `data-vendor-20261010.tar`, 12,293,712 bytes, SHA-256 begins `6d965739` (record the full hash in section 10) | write 1 |
| G10 update and rollback rehearsal (U1-U3, R1b, R2b, R3) | **done 12 Oct, as rehearsal rows** (RAM boots, nothing written): r142 / r142b on B143 - UPD (a `dnf5` downgrade + upgrade from local signed repositories, a read-only snapshot before each), HL (held names never offered), RBK (a rollback boot entry for the snapshot), RB2 (the rollback boot: the snapshot became the root); r146 / r146b - a new `kernel-iceland` installed by its rpm gets its boot entry and an initramfs with the iceland module and boots; on the final golden B145: r141u (UPD / HL / RBK PASS) and r141ub (rollback boot 7/7 PASS). The rescue-kit repair (L3) is not a rehearsal row | write 1; the update path |
| G11 slot flags of both slots read and understood | **done 10 Oct 12:24** (`parta-read.ps1`): `PARTA: READY FOR C0`, `AVB-PROOF: PASS`; slot b successful, not unbootable, retry 6; slot a successful and unbootable, retry 6. After the C0 #1 undo: `boot_b` back to the original (`254ad805`), slot b retry 6 | C0, write 2 |
| G12 fastboot reached by the keys from a cold start | **done 10 Oct** through the C0 runs: the owner's Volume Down + Power from a cold start reached the boot loader's fastboot, where the flags were read (C0 #1 12:4x, #2 14:1x, #3 16:3x). The Part A step 7 commands are not logged as a separate run | C0 (closed) |
| G13 the rehearsal cannot touch the storage | **closed** (a U-Boot build without UFS support, the read-only rule in the initramfs, a network-disk-only carrier, the self-check) | Part B |
| G14 sleep drain known | open; no measurement in the Loop 5 log. Not a safety gate | leaving the tablet asleep for days |
| G6-G8 charging, low battery, thermal | the owner's rule is recorded (10 Oct): attended charging with the 80 % limit (WORKLOG, 10 Oct 08:3x). The protective parts are not re-tested in the Loop 5 log | leaving the tablet alone on a charger |
| Kernel `kernel-iceland`: **q89e** (final, 13 Oct) | **final, in golden B147**: `7.3.0-rc7-iceland-00412-g4917dfb48aab` = q89d9 rebased onto v7.3-rc7 (411 patches kept unchanged, 3 dropped because they are merged upstream, 0 conflicts; config and device tree unchanged; 0 build warnings) + one video-driver fix (iris: SD video signalled as BT.601 6/6/6 and decoded colour codes mapped consistently; r156 VE-601 PASS). Five queue patches by Joonhoe Kim carry a provenance note (docs/PROVENANCE.md). Kernel rpm `03903142`. r155 / r156: NO-REGRESSION against r141. The q89d9 row below is the previous final (B145) | Part B, install |
| Kernel `kernel-iceland`: q89d9 (B145, superseded by q89e) | q89d8 (`up3-qd6`) + 0291 Bluetooth hci_qca: the WCN7860 baudrate-change RX burst dropped (`9e7350a6ab`; no more "Frame reassembly failed (-84)" at every Bluetooth power-on), `7.3.0-rc6-iceland-00414-g9e7350a6ab86`, on rc6, 0 build warnings. r146 / r146b: BT84 PASS (0 lines over 5 setups) + the kernel-update path; in golden B145. Pushed 12 Oct to the private iceland-linux repository: branch `iceland-7.3-rc6-q89d9` (commit `a2c12cb`, on top of `iceland-7.3-rc6-q89d8` `bdae4ee`), tag `q89d9`. N1 (SoundWire) and N2 (hci_qca IBS) were tested and dropped | Part B, install |
| Device package `iceland-device` **0.28-5** (`7e361fe2`, 13 Oct) | **final, in golden B147**: 0.28-3 (row below) + 0.28-4: the **minimal hold file** (Fedora's repositories hold back only `iio-sensor-proxy*`, `hexagonrpc*`, `libssc*`, `alsa-ucm`, `kernel-iceland*`, `iceland-*`; GRUB, shim, Fedora's firmware and libcamera update from Fedora), the firmware fetch helper `iceland-firmware-fetch` with its sha256 pin list (`/usr/share/iceland/firmware-pins.tsv`: 11.A.38-2, 11.A.38-3), **`BRIGHTNESS=0`** in `/etc/iceland/thermal.conf` (the thermal service never writes the backlight: GNOME's own brightness fought a sysfs cap, r151; the brightness cap comes back as a kernel clamp in the ktz8869 driver, a later tested change), the microphone decimators TX_DEC0 / TX_DEC1 back to stock's 84 + 0.28-5: **the microphone chain** - echo canceller (`iceland_mic_aec`, hidden) -> a limiter stage `61-iceland-mic-gain.conf` (+14 dB after the echo canceller, ceiling -1 dBFS) -> "Internal microphones (voice processing)" (`iceland_mic_processed`, the default). r156: speech level -40.0 dBFS (r141 -40.4), 0 clipped samples in 9 processed recordings, raw capture clipping 215 samples (r141: 68,749) | Part B, install |
| Device package `iceland-device` 0.28-3 (mk9, `25273c65`, B145) | in golden B145: 0.28-2 (Fedora slot marking `iceland-slot-mark` = `qbootctl -m` once after a good boot, only when the slot is not yet marked, skipped in kits and rehearsals; audio at stock 0 dB; `iceland-bdaddr` v2) + the speaker loudness item: a compressor make-up gain of **+9 dB (your choice, 12 Oct; within the 14 dB cap; that it stays at or below stock is NOT proven by measurement - both Android comparisons were inconclusive)**, limiter 0 dB in / -1 dBFS out, HPF 150 Hz 4th order, amplifiers and DSP stream at stock; only the protected "Speakers" and the processed microphone are listed (the raw ones renamed "... (raw, unprotected)") + the sensor resume unit (A52: hexagonrpcd and iio-sensor-proxy back after a resume, kit 144 3/3) + Fedora's repositories never offer `kernel-iceland*` / `iceland-*`. 37 package tests. `qbootctl` 0.2.2-2 from Fedora; the real `qbootctl -m` runs first on the installed system | Part B, install |
| `iceland-firmware` **11.A.38-3** (13 Oct) | **in golden B147**, held: 11.A.38-2 (row below) + ONE non-firmware file, stock's shell-temperature model for the thermal service, `/etc/iceland/thermal-model.json` (sha256 `4f476a7d4b0b9c52`; decoded, generic, published by your decision of 12 Oct; the encrypted vendor inputs, the key and the decoder stay unpublished). RPM `297669a0` = tag and GitHub release 11.A.38-3 of the iceland-firmware repository. r153 / r156: FP1-FP4 PASS, the model owned by the package and read by the thermal service | Part B, install |
| `iceland-firmware` 11.A.38-2 (B145) | in golden B145, held; published in https://github.com/mzakamin-hub/iceland-firmware (created 12 Oct 2026, public, commit c40c33e, tag + release 11.A.38-2 (RPM sha256 14833f719be4... = the package pinned in golden B145, + SRPM)): the tablet's GENERIC stock 11.A.38 firmware as a package (278 files: ADSP / CDSP, GPU zap, video, WCN7860 Wi-Fi / Bluetooth, touch, the sensor hub tree as root:fastrpc 0750 / 0640), byte-identical to what the installer extracts. Unit-specific data (the sensor calibration registry from `persist`, the Bluetooth address, the extraction record) is not in it and stays extracted from your tablet. r145 / r145b: `rpm -V` clean on both boots, 0 firmware load failures; r141 FP1-FP4 PASS | Part B, install |
| libcamera | **Fedora stock `0.7.1-1.fc44`** (F44 stable; 0.7.1-2 is only in updates-testing), updated by Fedora (not held). In r139c F54 40/40 and both cameras stream. **Known issue F54** (accepted by you): a rare WirePlumber abort when a camera stream stops (libcamera's soft-ISP stop race, upstream issues #320 / #335, not fixed upstream): r156 G4 1 of 40 cycles, r148c 1 of 40, r141 0 of 40; the cameras keep working after it. r152: 0.7.1-2 (updates-testing) 40/40 in both modes; it arrives as a normal Fedora update once stable | Part B |
| Golden (B run) | **B147 = the final golden** (committed 13 Oct 06:02, first try; B-RUN 38/0, check-b142 14/0, its judge check-b147 6/0): q89e + iceland-device 0.28-5 + iceland-firmware 11.A.38-3 + the Fedora 44 stable refresh (B146 recipe, minimal holds), no random seed, **1727 packages, manifest `0c35227ddf92`, body `e294b240f98e`**. **Final rehearsal r156 / r156u / r156ub on B147 (13 Oct 06:0x-07:04): accepted** - r156: 64 rows, 47 PASS, **1 FAIL (G4 = the known F54 libcamera race, 1 of 40 cycles; accepted by you)**, 4 CHECK (test-side and measurement rows such as G2 test-tool denials, LP upright loopback, PV camera pre-grant), 11 INFO, 1 DEFERRED (your listening check); r156u 25 PASS, 0 FAIL, 1 CHECK; r156ub 7/7 PASS (rollback boot). PASS includes SPEECH, PCLIP, MICCHAIN, GAIN, ST (the microphone chain), SK 12/12 (stock skin policy 60 / 61 / 70 C), FFI / FF6 / FF7 (firmware fetch), FP1-FP4, VE-601 (SD video colours), REC, RNG, update / rollback. B146 (13 Oct 04:13, 0.28-4) stays committed but is not the install image (r155: speech 14 dB too low, fixed in 0.28-5) | the install image |
| Golden (B run) of 12 Oct | B145 (superseded by B147; committed 12 Oct 11:11; B-RUN 33/0, its judge check-b144 4/0 with check-b142 14/0): q89d9 + iceland-device 0.28-3 + iceland-firmware 11.A.38-2 + the Fedora 44 stable refresh of B143, 1727 packages, manifest `9b752df5f7e1`, body `fce4bd794fb9`. **Minimal holds** (refresh): kernel, kernel-core, kernel-modules*, kernel-iceland, iio-sensor-proxy, hexagonrpc, libssc, iceland-device, iceland-firmware; shim + GRUB, libcamera, qbootctl and Fedora's firmware packages come from Fedora (signatures checked). **Final rehearsal r141 / r141u / r141ub on B145 (12 Oct 12:14-13:00): accepted, NO-REGRESSION against r139c / r140 over 36 rows** (r141: 64 rows, 48 PASS, 1 FAIL, 3 CHECK, 11 INFO, 1 DEFERRED; r141u 23 PASS, 1 FAIL, 2 CHECK; r141ub 7/7 PASS). Both FAILs are test expectations, fixed in the test scripts since: CAMDRV (the module check ran behind a session guard and listed nothing; B145's `kernel-iceland` ships the in-tree `sc1320cs.ko`, digest = the stripped in-tree build) and PK (expected 0.28-2) | the install image |
| Install image on C: | **rebuilt from B147 on 13 Oct (07:17), HELD** (nothing written to the tablet; you run the two writes): `C:\OnePlusPad4\final\fedora-iceland.sparse.img`, **6,591,322,540 bytes, SHA-256 `09ea7f446f969f382739bd4797989c939891ac464e53611caaa7bbc7060a150a`**, unpacked 237,159,641,088 bytes (= `userdata`), 31,956 chunks (full read-back). It replaced B145's image in place (B145's package stays in WSL `wf/final/q89d9-0283-b145`; its small files on C: are kept as `*-b145`). Package files: `SHA256SUMS`, `MANIFEST.json`, `VERIFY.txt`, `golden.json`, `u-boot-iceland-v3.img`; `flashguide\record.json` now names this image's hash (the old one kept as `record.json.pre-b147`). **Offline content check (`VERIFY.txt`): 109 PASS, 0 FAIL**: q89e kernel / initramfs / BLS entry / device tree, one kernel tree, iceland-device 0.28-5 (113 files equal the package digests), iceland-firmware 11.A.38-3, the minimal hold file exactly (GRUB, shim, firmware, libcamera not held), `kernel-iceland*` / `iceland-*` never offered by Fedora, TX_DEC0/1 at 84, the microphone chain (61-iceland-mic-gain.conf: +14 dB limiter after the echo canceller, -1 dBFS), `BRIGHTNESS=0`, the fetch helper + pin of 11.A.38-3, the thermal model owned by iceland-firmware (sha `4f476a7d`, no private copy), slot marking enabled, the first-boot setup not done and not disabled, no user, no autologin, no rehearsal arguments / units / dconf keys, empty machine-id, no SSH keys, no Wi-Fi networks, no journal, **no random seed** (B145's only FAIL is gone), root locked, make-up 9 dB, owner Wi-Fi guard on the raw disk: SSID 0, keyfile 0 (its one structural match is a printf format string, as in B145). Private by design (as every install image): the tablet's own firmware extraction and its Bluetooth address (the thermal model is now generic and published) | write 1 |
| Install image of 12 Oct (superseded, replaced on C: by B147's) | rebuilt from B145 on 12 Oct (13:17), was `C:\OnePlusPad4\final\fedora-iceland.sparse.img`, 6,034,694,960 bytes, SHA-256 `0e65a4d54111cbc84cf3d9ec93c903b8038864e7921505c05c00e7f90aed7ae4`, unpacked 237,159,641,088 bytes (= `userdata`), 32,104 chunks; it replaced B130's image in place (B130's package stays in WSL `wf/final/q89b-024-b130`). Package files: `SHA256SUMS`, `MANIFEST.json`, `VERIFY.txt`, `golden.json`, `u-boot-iceland-v3.img`; `flashguide\record.json` now names this image's hash (the old one kept as `record.json.pre-b145`). **Offline content check (`VERIFY.txt`): 98 PASS, 1 FAIL**: q89d9 kernel / initramfs / BLS entry, iceland-device 0.28-3, iceland-firmware 11.A.38-2, the minimal hold file exactly, `kernel-iceland*` / `iceland-*` never offered by Fedora, slot marking enabled (unit shipped, preset enable, no off switch, no `iceland.noslotmark`, qbootctl installed), the first-boot setup not done and not disabled, no user, no autologin, no rehearsal arguments / units / dconf keys, empty machine-id, no SSH keys, no Wi-Fi networks, no journal, root locked, make-up 9 dB, owner Wi-Fi guard 0 hits on the raw disk. The FAIL: `/var/lib/systemd/random-seed` (32 bytes) left by the B run's boots - not unit data and not a secret of yours; systemd replaces it at the first boot and the kernel is seeded by the hardware RNG (r142 RN PASS). The PC session can remove it in a later golden; it does not block the install. Private by design (as every install image): the tablet's own firmware extraction, its Bluetooth address and its thermal model | write 1 |
| Install U-Boot | **v3**: install build `979b4076` (patches 0008-0010: no self power-off or reset, USB up without ABL, `fastboot reboot-bootloader`). Footered `4955ee98` (AVB-PROOF PASS, rot-equal; made from 10 Oct's `boot_b`, re-made on the install day by Part A step 6); `record.json` points to v3. The B147 package (as B145's) lists `u-boot-iceland-v3.img` in its `SHA256SUMS`; the older `u-boot-iceland.img` (`fb2bed8d`) on C: is not part of it and is not used | write 2 |
| AVB footer for the install U-Boot (review R-1) | done for v3 (`4955ee98`); decision 1 = footer A (10 Oct). Re-made on the install day from the then-current `boot_b` by Part A step 6 | C0, write 2 |
| C0 write-2 probe (`boot_b`, undone the same day each time) | **done, all undone.** #1 FAIL (`c39a24e6`, 10 Oct 12:4x): slot b unbootable with retry 0 after one boot; undone at once. #2 (`8729065f`, 13:55): U-Boot holds, no USB (dwc3 core reset timeout). #3 (`cb1b707e`, patch 0009, 16:17): U-Boot fastboot enumerates after 7 s from a normal boot. #4 PASS (`4955ee98`, patch 0010, 17:41): `fastboot reboot-bootloader` reaches the boot loader without a key press, flags unchanged | Parts C, D |
| Your decisions (section 0.4) | answered on 10 Oct: 1, 2, 5; plan decisions 8-9 recorded; open: 3, 4, 7 (part), 8 (way back to LineageOS, in part) | Parts C and D |

The install must not start while any line that is "needed for write 1" or "Part B" is open. As of 13 Oct (morning)
those are: G3 (dry run), G4 and decision 3. The final golden (B147), its rehearsal (r156), G10 and the install image
(rebuilt from B147) are done; the image is HELD for you. C0 is done (every probe undone); its lines are closed. After the install: the listening check
of the speakers (+9 dB, your choice) and the other deferred checks below.

**Rehearsal record since 10 Oct** (RAM boots, nothing written to the tablet's storage):
- r2t (10 Oct 04:10, q89 + 0.23): FAIL (camera, mic, GPU). Fixed in the later builds.
- r2u (q89b + 0.23, 05:06): accept 51/0, F55 replay PASS, F54 40 cycles.
- r2v (0.23 with the processed-mic fix, 05:45): F55 replay PASS; the owner's echo test found the processed mic better.
- r2w (golden B130, q89b + 0.24, 07:12, the confirmation run): accept 51/0/0, F55 replay PASS, echo processed -31.5 dBFS
  against raw -42.1 dBFS. Its F54 "stream no" cycles 1-11 were a test artefact (GNOME's lock screen, 08:1x).
- r136 (golden B134, 10 Oct 23:56): K6 RTC offset kept across Android PASS; B9 Wi-Fi address stable PASS; B8 stock
  libcamera CHECK (it streams both cameras).
- Kits 136 and 137 (RAM kits, not rehearsals): the owner heard no sound in either; kit 137 proved the K3 USB latency fix.
- r137 (golden B138, 11 Oct 03:19): FAIL 8 of 45 rows. Cover screen off/on PASS and the slot-marking guard PASS. The
  audio breakdown was traced to disruptive test steps (speaker-gain step, libcamera swap) and test bugs. The owner
  found the volume too low.
- r138a (golden B138, 10:34): SA devices present after every step, APM timeouts 0 (r137: 95), F54 40/40, RTC d = 1 s.
  FAIL: sensors (iio-sensor-proxy never sees the accelerometer, C9a/C9b) and two accept rows (test expectations).
- r138b (golden B139, autonomous, ~15:5x on 11 Oct): FAIL 2 of 18 rows. Clean: SA after every step, APM / PRM 0, F55
  opens PASS, F54 40/40 with stock libcamera, sensors v2 10/10 with a claiming client, RTC d = 0 s with no RTC write.
  FAIL: the loopback (the speaker is acoustically far too quiet: 1 kHz at -12 dBFS arrives at -54 dBFS) and the camera
  metrics script (a test bug). Decision: keep the 0.27r4 speaker chain.
- r138c (golden B140 = B139 + 0.27r6, 11 Oct ~17:3x): FAIL 2 of 19 rows. Every live gain at or below stock; the speaker
  about 15.5 dB louder at the microphones than in r138b; one F55 round without a running PCM (later clean).
- r139 (golden B141: q89d7t + 0.28-1 + the Fedora 44 refresh, 19:2x): FAIL 4 of 29. Bluetooth "no powered controller"
  (cause: our address helper's race, made visible by bluez 5.87; fixed by `iceland-bdaddr` v2); N1 dropped; N3 PASS.
- r139a (golden B142: q89d8, 23:5x): FAIL 4 of 31. Bluetooth v2 helper PASS (BTf), N3 PASS, GPU rows PASS; the sensor
  checker's orientation was a test bug (the tablet stood upright in landscape, Pad 4's natural orientation).
- r139b (golden B143, minimal holds, 12 Oct 01:31): FAIL 3 of 36, all tests (an idle-dimmed session during the camera
  cycles, a slow mirror for the test tools, two display-controller lines during idle dimming, under watch). Slot
  marking I1 (Fedora qbootctl) PASS, signatures, own firmware, shim / GRUB from the golden's packages PASS.
- **r139c (golden B143 unchanged, test fixes only, 12 Oct 02:28): CLEAN** - 36 rows, 0 FAIL, 2 CHECK (SELinux denials
  of the test's own tools; raw microphone clipping with the tablet upright), 28 PASS, 6 INFO.
- r140 (B143 + the 0.28-3 sound files in the overlay, 03:08): sound behaviour PASS (defaults, names, gains at or below
  stock, no clipping after the chain); loudness vs stock not provable.
- r142 / r142b, r143-r147 (12 Oct, quiet change rehearsals): update + rollback (UPD / HL / RBK / RB2), gyroscope, hardware
  RNG, the iceland-firmware package (r145 / r145b clean), q89d9's Bluetooth fix + the kernel-update path (r146 / r146b),
  video: hardware encode H.264 / HEVC and bit-exact decode of the AOSP test vectors H.264 / HEVC / VP9 / AV1 (r147).
  Kit 144: the sensor resume fix 3/3.
- Android reference + r140b (12 Oct ~09:xx, with your go for the loud runs): both loudness comparisons INCONCLUSIVE
  (different capture paths); you chose **+9 dB** for the make-up ("Proceed with 9db").
- **r141 / r141u / r141ub (final golden B145, 12 Oct 12:14-13:00): ACCEPTED** - NO-REGRESSION against r139c / r140
  over 36 rows; MK (+9 dB: no clipping after the chain), FP1-FP4, BT84, BTd, SA / AE, F54 40/40, cameras, sensors,
  update / rollback, video, gyroscope, RNG PASS; rollback boot 7/7. Two FAILs, both test expectations (CAMDRV, PK;
  section 0.1 golden line); CHECKs: test-tool SELinux denials, raw microphone clipping upright, a camera-portal
  pre-grant check, SD BT.601 video in stock GStreamer.
- r148c / r150 / r150b / r151 / r152 / r153 (12-13 Oct, quiet change rehearsals on B145): the loaded camera module is
  kernel-iceland's in-tree `sc1320cs` (no private build); stock skin temperature policy 60 / 61 / 70 C (SK 12/12);
  the brightness probe (the sysfs cap fights GNOME -> `BRIGHTNESS=0` until a kernel clamp); libcamera 0.7.1-2 40/40;
  iceland-firmware 11.A.38-3 + the fetch helper.
- r155 (golden B146 = q89e + 0.28-4, 13 Oct 04:14-05:15): NO-REGRESSION against r141; SPEECH FAIL (processed speech
  14 dB too low at TX_DEC 84) -> 0.28-5 adds +14 dB after the echo canceller (your choice). B146 is not the install image.
- **r156 / r156u / r156ub (final golden B147, 13 Oct, done 07:04): ACCEPTED** - only FAIL G4 (F54, the known libcamera
  stop race, 1 of 40 cycles; accepted by you, row kept). SPEECH -40.0 dBFS (r141 -40.4), PCLIP 0 clipped, MICCHAIN,
  GAIN, ST, SK 12/12, FFI / FF6 / FF7, HX0-2, FP1-FP4, RNG, VE-601, REC PASS; r156u 25 PASS / 0 FAIL / 1 CHECK;
  r156ub 7/7 PASS.

**Deferred physical checks** (the owner's hands or eyes; not automated, never waited for by a run):
- Cover wake from s2idle: a suspend cannot run in a rehearsal (the no-suspend rule). Only the screen off/on with the cover
  is tested (r137 K8c PASS).
- USB host (hub) and DP monitor replug: not testable in kits (STATE-2026-10-10-2225, item 8).
- Keyboard cover (pogo): physical test; the owner kept the pogo keyboard support (11 Oct).
- Cold start of the installed system: after the install.
- Wi-Fi throughput and the SCMI cold soak: not testable in kits (STATE-2026-10-10-2225, item 8).
- Listening check of the speakers after the install: the make-up is +9 dB by your choice; that it stays at or below
  stock's loudness is not proven by measurement. If it sounds louder than Android at the same volume, or harsh, tell
  the PC session (the value is one line in the device package).
- Chargers: the sitting with your wall chargers (attended charging, 80 % limit until then).

### 0.2 The safety rules (the ones set in the plan; they never change)

1. **Only two partitions are ever written:** `userdata` (the Fedora image) and ONE boot-path partition of the
   active slot (`boot_b` today). Each has its own undo. The probe C0 writes `boot_b` and puts it back the same day
   (four tries on 10 Oct, all undone).
2. **Never written:** the boot firmware (`xbl*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `uefi*`, `shrm*`,
   `cpucp*`, `qupfw*`, `tme_*`, `imagefv*`, `keymaster*`, ...), the radio / DSP firmware (`modem*`, `bluetooth*`,
   `dsp*`), the per-device data (`persist`, `cdt`, `ddr`, `dinfo`, `ocdt`, `oplusreserve*`, `nonmodemst*`, ...), the
   security state (`devinfo`, `keystore`, `frp`, `ssd`, `secdata`, `uefivarstore`, ...), Android's system
   (`super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `misc`, ...), `efisp` and every
   partition table. As long as these are untouched the tablet's own boot loader and its fastboot keep working, and
   fastboot can put everything back.
3. **Commands that are never typed** during the install: `fastboot -w`, `fastboot flashall`, `fastboot update`,
   `fastboot set_active`, `fastboot erase ...`, `fastboot format ...`, `fastboot flashing lock`,
   `fastboot flash` with any partition name other than `userdata` and `boot_b`. No third-party flashing tool.
   (`fastboot -w`, `set_active` and the stock boot set are used only by the return-to-stock script, section 8.)
4. **Only files whose SHA-256 was recorded** (section 10) are written, and each is checked again right before its
   write.
5. **The image is rehearsed from RAM first**, through the same chain from U-Boot on, before it is written.
6. **U-Boot stays unable to write the storage.** Fedora gets a rule that makes every other partition read-only.
7. **Nothing is urgent.** If a screen, a message or a number differs from what this guide says: stop, do not
   improvise, do not retry a write. The boot loader is intact in every state this guide can produce, and section 9
   tells what to do.
8. Battery above 60 %, the PC's own USB port that was used in all tests, the same cable, the PC on mains power,
   no sleep on the PC during a write.
9. **Leaving U-Boot always goes to the boot loader, never through another boot:** hold **Volume Down + Power**
   (about 15 s) until the boot loader's fastboot screen shows. Holding Power alone restarts the tablet, and with
   U-Boot in `boot_b` that is another boot of slot b (section 0.5).

### 0.3 What the tablet looks like after each stage

| Stage | Power-on without the PC | With the PC |
|---|---|---|
| Today | LineageOS (slot b) | RAM test kits |
| During C0 (U-Boot in `boot_b`, Android's data intact) | the boot loader's unlocked warning, then U-Boot's text; U-Boot finds no Fedora and holds in its USB fastboot (the v3 build has no self power-off or reset: patch 0008) | U-Boot's fastboot answers as `oneplus-iceland` (read only) |
| After C0's undo | LineageOS with its data, as today | RAM test kits |
| After write 1 (`userdata`) | Android starts and says its data is damaged. **Do not confirm a factory reset.** Keep this stage short | `fastboot boot` of U-Boot starts Fedora |
| After write 2 (`boot_b`) | Fedora | the RAM rescue kit still works |
| After the return to stock | OxygenOS 11.A.38 (slot a; the script sets slot a active) | - |

### 0.4 Decisions that are yours

Answered on 2 Oct:
- Fedora only for now; a dual-boot plan is prepared separately (`wf/install/DUALBOOT-PLAN.md`), nothing of it is
  done.
- The write-2 probe C0 comes first, while Android's data is intact.
- The GPU microcode in the image is Fedora's own (`qcom-firmware`, the upstream linux-firmware set the kits use).

Answered on 3 Oct:
- 6: the camera driver is in the image (in-tree in the private kernel queue, in kernel-iceland, with the stock-derived
  tuning files in the private device package).
- 10: the Wi-Fi country: the firmware's US stays.

Answered on 10 Oct (the owner's "take the recommended, safest option"; recorded in `wf/final/DECISIONS-2026-10-10.md`,
quoted in WORKLOG 10 Oct 08:3x; that file is not part of the Loop 5 sources):
- 1: footer A, the AOSP test-key hash footer on the install U-Boot (done for v3, section 0.1).
- 2: one RAM boot of the exact install U-Boot before C0 (done on the earlier builds 13:42 and 13:44, and on v3 at 17:31).
- 5: attended charging with the 80 % limit as the default (G6-G8 and G14).
- 7, in part: plan decision 8 (skin temperature limit, the 60 / 61 policy) and 9 (day-0 snapshot and a home backup) are
  recorded; third-party repos are the default.
- 8, in part: "way back = stock 11.A.38" is recorded. A way back to LineageOS is not in the record.

Still open (answer before the step named):
3. (Part D, after C0) The permanent boot path. The record of 10 Oct says: if the count falls on `boot_b`, `boot_b` cannot
   be the permanent path, and `recovery_b` needs its own plan (WORKLOG, 10 Oct 08:2x and 12:4x: the scripts refuse
   `recovery_b` and any decision 3 other than `boot_b`). Since then C0 #3 and #4 showed `boot_b` reachable and undone, and the reboot to the boot loader
   costs no try. But C0 #1 fell from 7 to 0 within one boot, and the Fedora slot marking (`iceland-slot-mark` with
   Fedora's `qbootctl`, in 0.28-2) has not run on the tablet yet: its package and guard pass in the rehearsals
   (r139b / r139c I1), the real mark happens only on the first installed boot. The final image has the marking enabled (offline
   check: unit, preset, no off switch). `record.json` decision 3 is still empty (open on 12 Oct). This guide's Part D covers `boot_b` only.
4. Boot path alternative (`recovery_b`): not scripted; needs its own plan, footer, probe and owner OK. Its key is not
   confirmed on this tablet.
5. (answered on 10 Oct, above).
6. (answered 3 Oct, above).
7. The plan's decisions 5-7 (held boot-code updates, release pin, LibreOffice / GNOME Web): not in the Loop 5 record;
   open. Decisions 8 and 9 are recorded (above).
8. Is a way back to LineageOS needed after the install? Write 1 erases LineageOS's data (the way back would be a restore
   from the G1 backup). The record says the way back is stock 11.A.38 (section 8); the owner should confirm.

### 0.5 The boot loader's slot counter (new, from Qualcomm's open boot-loader source)

The boot loader keeps three flags per slot: *successful*, *unbootable* and a *retry count*. What its open-source
version does (OnePlus's own build is closed, so C0 measures it on this tablet):
- **Flashing `boot_b` resets slot b**: *successful* becomes `no`, *retry count* the maximum. The same happens when
  `boot_b` is flashed back (the undo).
- **Every normal power-on of a slot that is not *successful* counts down one try.** Entering fastboot with the keys,
  recovery mode (from Android's "restart to recovery", or Power + Volume Up - the key is not yet confirmed on this
  tablet) and the charging screen do not count. Only a flash of a `boot` partition resets the flags; a flash of
  `recovery_b` does not.
- **At zero** the boot loader marks the slot unbootable. If slot a is marked *successful* and not *unbootable*, it
  switches to slot a and restarts (slot a has no Android system since the LineageOS install); otherwise it stops in its
  fastboot. **Part A on 2 Oct read slot a as successful AND unbootable** (slot b: retry count 6): in that state the boot
  loader does not switch, it stops in its fastboot (the review's case A), and the undo works from there.
- **Only Android marks a slot successful** (after a good boot). U-Boot does not. Since package 0.27r5 (now 0.28-2)
  the Fedora side does: `iceland-slot-mark` runs Fedora's `qbootctl -m` once after a good boot, only if the current
  slot is not yet marked (skipped in kits and rehearsals). Its effect on the tries is not yet tested on the tablet
  (r137 / r139b / r139c check the package and the guard only).

So: during C0, every untethered power-on costs one try, and C0 has a hard stop (step C0.6). After C0's undo,
LineageOS's first boot marks slot b successful again. Whether `boot_b` can be the permanent boot path depends on
what C0 measures (decision 3).

Measured on 10 Oct (C0 #1-#4, all undone the same day): in #1 the retry count went from 7 to 0 within one boot (the owner
also saw several U-Boot self-resets; patch 0008 removes the reset and power-off paths), so the one-try rule alone does not
explain it. In #4 a normal boot into U-Boot counted one try (7 to 6), and `fastboot reboot-bootloader` from U-Boot into the
boot loader's fastboot did not count (6 before and after).

---

## Part A - preparation on the PC and read-only checks (no write)

Open a PowerShell window. All commands assume the tools in `C:\platform-tools` and the kit in `C:\OnePlusPad4`.

### Step 1 - verify the backup (G1)

```powershell
C:\OnePlusPad4\scripts\03-Verify-Backup.ps1 -Backup C:\OnePlusPad4\backups\20260927-1933-unknown
```

Expected: "N files intact (hashes match what the tablet reported)" and, for both slots, "all images identical to
11.A.38" (or a named list of differences that you have seen before). **Stop** if a file is reported damaged or
missing: make a new backup first (`02-Backup-AllPartitions.ps1`, from Android with root).

### Step 2 - verify the stock images (G2)

```powershell
cd C:\OnePlusPad4\stock-11.A.38
Get-Content .\SHA256SUMS.txt | ForEach-Object { $h, $f = $_ -split '\s+', 2; if ((Get-FileHash $f -Algorithm SHA256).Hash -ne $h.ToUpper()) { "DAMAGED: $f" } }
```

Expected: no output. Any "DAMAGED" line: stop and fetch the stock package again.

### Step 3 - dry run of the return to stock (G3)

```powershell
C:\OnePlusPad4\scripts\30-Restore-Stock.ps1
```

Without `-Execute` this only checks and prints its plan. Read the plan: it must list only `boot`, `init_boot`,
`vendor_boot`, `dtbo`, `recovery`, `vbmeta`, `vbmeta_system`, `vbmeta_vendor`, `pvmfw` on both slots, `super`, and
the erase of `userdata` / `metadata`. It must not list any firmware partition. Expected last lines: no problem
found. (This script has been written and dry-run, never executed on this tablet.)

### Step 4 - second copy of the backup and the stock images (G4)

Copy `C:\OnePlusPad4\backups\20260927-1933-unknown` and `C:\OnePlusPad4\stock-11.A.38` to a second disk (about
17 GB + the stock package) and run step 1 against the copy (`-Backup <path on the second disk>`). The backup holds
the calibration and identity of this one tablet; no download replaces it. Do not upload it anywhere.

### Step 5 - save what write 1 would destroy (G5)

With LineageOS running, USB debugging on, and **Developer options > "Rooted debugging" on** (without it `adb root`
is refused; the setting is yours to switch):

```powershell
cd C:\platform-tools
.\adb.exe root
cmd /c 'C:\platform-tools\adb.exe exec-out "tar -C /data -cf - vendor" > C:\OnePlusPad4\backups\data-vendor-20261002.tar'
Get-FileHash C:\OnePlusPad4\backups\data-vendor-20261002.tar -Algorithm SHA256
.\adb.exe unroot
```

This only reads (the `cmd /c` form keeps the archive binary-exact; PowerShell's own `>` would damage it). Write the
hash into section 10. `/data/vendor` holds Android's per-device runtime data (written by the vendor services, not
part of any image); there is no procedure that restores it, the copy exists so that nothing unique is lost. `persist`
needs no file copy: it is in the raw backup (G1) and is never written. Your photos and other personal files on
LineageOS are **not** covered: copy what you want to keep before write 1 (write 1 erases all Android data).

### Step 6 - the read-only pull for write 2 and its undo (G11; review R-1 / R-2 / R-9)

Same day as C0, LineageOS running, "Rooted debugging" on. The PC session copies `parta-read.ps1` into
`C:\platform-tools` first.

```powershell
powershell -ExecutionPolicy Bypass -File C:\platform-tools\parta-read.ps1
```

About 4 minutes; nothing is written (every adb / fastboot call goes through a list of reading commands). It
1. reads the boot state and, with `adb root`, today's slot b images (`boot`, `vbmeta`, `init_boot`, `vendor_boot`,
   `dtbo`, `recovery`, `vbmeta_system`, `vbmeta_vendor`), slot a's boot set and `misc` into
   `C:\OnePlusPad4\backups\parta-<date-time>\`, and saves `boot_b.img` once more as **`boot_b-before-install.img`:
   the undo file of write 2 and of C0** (today's LineageOS `boot_b`, 100663296 bytes - not the backup's);
2. restarts into the boot loader (`adb reboot bootloader`), reads the slot flags of both slots, the lock state and
   `boot_b`'s size (`fastboot getvar`; the serial number is never asked), and restarts into Android;
3. runs the PC check: a second copy in the workflow's private folder (equal by SHA-256), today's `vbmeta_b` (it must
   chain `boot`), `misc`'s boot command (it must not be `boot-recovery` / `boot-fastboot`), **the footered install
   U-Boot made for today's `boot_b`** (`u-boot-iceland-footered.img`: the install build with an AVB hash footer,
   signed with the key `vbmeta_b` chains `boot` with, rollback index and OS version / security patch copied from
   today's `boot_b`), and the PC proof with Android's own verified-boot code on today's images.

Expected last line: **`PARTA: READY FOR C0`**. Anything else: stop; the lines starting with `STOP` say why.
Write into section 10: the date, the SHA-256 of `boot_b-before-install.img` and of `u-boot-iceland-footered.img`
(both in `RECORD-parta.txt`), slot b's and slot a's flags, and the proof's summary line (`AVB-PROOF: PASS`, incl.
`rot-equal`).

### Step 7 - the rescue keys from a cold start (G12)

Switch LineageOS off (power menu > Power off). Then hold **Volume Down + Power** until the boot loader's fastboot
screen shows, connect USB:

```powershell
cd C:\platform-tools
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe reboot
```

Expected: `canoe`, `b`, then LineageOS starts. Both commands only read. This is the door that must work with
anything in `boot_b`.

---

## Part B - the rehearsal from RAM (no write)

Done by the PC session (automated, RAM only; since 11 Oct fully autonomous: a full final rehearsal takes about an
hour on the tablet, a change rehearsal less). What it must produce:

1. **The image**: the official Fedora-Workstation-Disk-44 aarch64 raw image (checksum-verified), re-laid for the
   tablet's 4096-byte blocks, refreshed to Fedora 44 stable, + our packages (`kernel-iceland` q89e, `iceland-device`
   0.28-5, `iceland-firmware` 11.A.38-3, the sensor packages `iio-sensor-proxy` / `hexagonrpc` / `libssc`), Fedora's own
   libcamera, `qbootctl`, shim and GRUB, with the tablet's firmware in `/usr/lib/firmware/updates` (extracted from the
   tablet's partitions, read only; the generic files are owned by `iceland-firmware` with the same checksums, the
   unit-specific ones by no package). The goldens of 11-13 Oct are built this way (B147 = the final golden).
2. **Boots of exactly that image from RAM** through the installed chain from U-Boot on: `fastboot boot` of the
   **rehearsal build** of U-Boot (`u-boot-iceland-rehearsal.img`: the install build's code without any storage
   support, so it cannot see the tablet's storage at all), then a "head" with the image's EFI partition and `/boot`;
   U-Boot starts shim and GRUB from it, GRUB starts our kernel, SELinux enforcing; the root comes from the PC over
   the USB network. The tablet's storage is not written.
3. **The acceptance list passed on that boot** (automated, one line `INSTALL-ACCEPT: n PASS, 0 FAIL`): the boot chain
   and the read-only rule, GNOME session, touch, Wi-Fi scan with 5 GHz, Bluetooth, sound, ADSP and CDSP running with
   no failed firmware request, the GPU with its firmware, battery and time estimate, charge limit (80 / 85 %), power
   modes, auto-rotate, hardware video, both cameras, the default apps start, About shows
   "OnePlus Pad 4", our packages verify clean.
4. **The update rehearsal** (a `dnf upgrade` keeps our kernel and sensor packages; a new kernel is installed next
   to the old one, boots once and becomes the default) and **the rollback rehearsal** (previous kernel from GRUB's
   menu, previous root snapshot, repair from the RAM rescue kit).
5. **The files and their checksums**, written into section 10 (`priv/run/RECORD.txt`, made after the final run R4):
   - `fedora-iceland.sparse.img` (the rehearsed image as a sparse image; its unpacked size equals `userdata`);
   - `u-boot-iceland.img` (the **install** build: it is NOT the one the rehearsal boots. Its own storage path is first
     seen in C0 step 0 and C0, and with Fedora's disk in Part C step 4) and `u-boot-iceland-footered.img` (the same
     with the AVB footer for `boot_b`, made in Part A step 6). The PC refuses to footer or accept the rehearsal build
     for `boot_b`.

Suspend and resume are tested in the RAM kits and on the installed system, **never in a rehearsal**: the
rehearsal's root comes from the PC over the USB link, and the USB gadget's suspend loses it (R2-final, 3 Oct). Since
11 Oct (B run 139 suspended when the cover was closed) every rehearsal and B run masks the five sleep targets from
the first moment (rehearsal head command line; kits: a `/run` layer from the kit's init) and stops at once when
the masks are missing. The installed system is not changed by this.

**State on 13 Oct (morning):** items 2-3 are met on the final golden B147 (r156 accepted: its only FAIL is the
known F54 libcamera race, accepted by you; the acceptance list is part of its rows). Item 4 (G10) is met as
rehearsal rows (r142 / r142b, r146 / r146b, r141u / r141ub, r156u / r156ub). Item 5: the image is rebuilt from B147
(`C:\OnePlusPad4\final`, section 0.1 and section 10), offline check 109 PASS / 0 FAIL; the install U-Boot is v3
(`u-boot-iceland-v3.img`, `979b4076`).

Part B is complete when section 10 has these values and the date of the passed acceptance list.

---

## Part C0 - the write-2 probe: U-Boot into `boot_b`, then back (Android's data stays)

Why: the one thing no RAM boot can show is what the boot loader does with a **written** `boot_b` (verified boot,
the slot flags, the retry counter). C0 finds out while LineageOS and its data are still there, and undoes itself
the same day. U-Boot cannot write the storage, and on today's tablet it finds no Fedora (Android's encrypted data is
in `userdata`), so it waits in its fastboot and then switches the tablet off.

**Only when:** Part A steps 1-7 done the same day, `PARTA: READY FOR C0`, your answers to decisions 1 (and 2 for
step 0), battery above 60 %, the PC's own USB port, about 75 minutes of your time. Write the numbers into section 10
as you go.

### C0.0 - (if decision 2 is yes) one RAM boot of the install U-Boot, read only

The PC session runs:

```powershell
powershell -ExecutionPolicy Bypass -File C:\platform-tools\uboot-ram-probe.ps1
```

About 3 minutes, nothing written: the boot loader RAM-boots `u-boot-iceland.img` (the plain install build); its
console shows `scsi scan`, the `userdata` map, no Fedora, then its fastboot; the script saves the console and sends
`fastboot reboot`. Expected: "U-Boot fastboot after N s", the console lines, "Android is back". This proves U-Boot's
own path before the write; C0 then adds only what the boot loader does with `boot_b`.

### C0.1 - check the files

```powershell
cd C:\platform-tools
(Get-FileHash \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img -Algorithm SHA256).Hash
(Get-FileHash C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img -Algorithm SHA256).Hash
```

Both must equal section 10 (from `RECORD-parta.txt`) letter for letter. Otherwise stop.

### C0.2 - into the boot loader by the keys, and read

Switch LineageOS off, hold **Volume Down + Power**, connect USB:

```powershell
.\fastboot.exe getvar product
.\fastboot.exe getvar unlocked
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar partition-size:boot_b
```

Expected: `canoe`, `yes`, `b`, `yes`, `no`, a number (note it as R0), `0x6000000`. Anything else: `.\fastboot.exe
reboot` and stop.

### C0.3 - THE WRITE (the probe)

Type it exactly; the only partition name is `boot_b`, the file is the **footered** one:

```powershell
.\fastboot.exe flash boot_b \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img
```

Expected: "Sending 'boot_b' (98304 KB) OKAY", "Writing 'boot_b' OKAY", "Finished". If it fails: stay in fastboot,
go to C0.7 (the undo) - nothing else.

### C0.4 - the flags right after the write (before any boot; read only)

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
```

Note them (R1). Expected from the open-source boot loader: `b`, `no`, `no`, the maximum (section 0.5; before the
write slot b read 6 on 2 Oct). If
`current-slot` is not `b` or `slot-unbootable:b` is `yes`: go to C0.7.

### C0.5 - the first boot, with the PC

```powershell
.\fastboot.exe reboot
```

Expected on the screen: the boot loader's unlocked warning (orange), then U-Boot's text: the storage scan, no
Fedora, "fastboot" (U-Boot waits). **A red screen or a stop in the boot loader instead: section 9, row "verified-boot
error".** Then, read only:

```powershell
.\fastboot.exe getvar product
cmd /c 'C:\platform-tools\fastboot.exe oem console > C:\OnePlusPad4\backups\parta-<date-time>\c0-uboot-console-1.txt 2>&1'
```

Expected: `oneplus-iceland` (U-Boot's fastboot). Now **hold Volume Down + Power** (about 15 s) until the boot loader's
fastboot screen shows, and read:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar slot-unbootable:b
```

Note R2. R2 = R1 - 1 means this boot loader counts down slot b's tries (section 0.5); R2 = R1 means it does not.

### C0.6 - untethered cold boots (the real case), with a hard stop

Repeat at most **three** times, and **never when `slot-retry-count:b` is 3 or less** (the next boot would leave 2
or less; then go straight to C0.7):

1. Unplug the USB cable. In the boot loader's menu choose "Power off" (volume keys, Power to select).
2. Press Power briefly. Expected: the unlocked warning, U-Boot's text, after about 10 minutes the screen goes dark
   (U-Boot switches the tablet off by itself; note whether it did). If the screen is still lit after 12 minutes:
   note it, hold Volume Down + Power.
3. From off: hold **Volume Down + Power**, connect USB, read `current-slot`, `slot-retry-count:b`,
   `slot-unbootable:b` as in C0.5. Note them.

Stop at once and go to C0.7 when: `current-slot` reads `a`, `slot-unbootable:b` reads `yes`, the count is 3 or
less, the boot loader shows a verified-boot error, or anything differs from this text.

Optional, only if the count is 5 or more: with the tablet off, plug in the wall charger and note what starts (the
boot loader's charging screen, or U-Boot). Charging-screen starts do not count.

### C0.7 - UNDO (always, the same day)

In the boot loader's fastboot (Volume Down + Power, USB connected). Type it exactly:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe reboot
```

Expected: `b`; "Writing 'boot_b' OKAY"; `no` and the maximum (the flash resets the flags again); then LineageOS
starts **with its data** (your PIN / password if set). If `current-slot` read `a` before the flash: still do the
flash (it is slot b's partition), then **stop and ask** before anything else - no `set_active` (section 9).

### C0.8 - after the undo (PC, read only)

When LineageOS is up for 2 minutes, the PC session runs `parta-read.ps1` again. Expected: `boot_b.img` equal to
`boot_b-before-install.img` (the probe left nothing behind), `slot-successful:b: yes` (LineageOS marked it again),
`PARTA: READY FOR C0` (it stays valid as the input of write 2).

**C0 passed** when: the boot loader started U-Boot from `boot_b` at every power-on (orange warning, no verified-boot
stop); U-Boot found no Fedora and waited in its fastboot (console saved); the keys reached the boot loader every
time; the flags are recorded (does the count go down per boot?); the undo brought LineageOS back with its data and
slot b successful. Write the results into section 10; the PC session decides with you about decision 3.

---

## Part C - write 1: the Fedora image into `userdata`

Only when: section 0.1 has no open line for write 1, C0 passed and decision 3 is answered, section 10 is filled in,
battery above 60 %, your files from LineageOS are saved. **Run Part A step 6 again the same day, just before this
part** (it is the last time Android can be read; its `boot_b-before-install.img` must still equal C0's).

### Step 1 - check the file

```powershell
cd C:\platform-tools
(Get-FileHash C:\OnePlusPad4\final\fedora-iceland.sparse.img -Algorithm SHA256).Hash
```

Must equal the value in section 10, letter for letter (B147: `09ea7f446f969f382739bd4797989c939891ac464e53611caaa7bbc7060a150a`). Otherwise stop.

### Step 2 - enter the boot loader and check the tablet

```powershell
.\adb.exe reboot bootloader
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar unlocked
.\fastboot.exe getvar partition-size:userdata
```

Expected: `canoe`, `b`, `yes`, and `0x3737D0F000` (237 159 641 088 bytes; it must **equal** the image's unpacked
size noted in section 10: the image is made with exactly this size). Anything else: `.\fastboot.exe reboot` and
stop.

### Step 3 - the write

Type it exactly; the only partition name is `userdata`:

```powershell
.\fastboot.exe flash userdata C:\OnePlusPad4\final\fedora-iceland.sparse.img
```

The PC's fastboot splits the sparse image into pieces of at most 805 MB (the boot loader's `max-download-size`) and
reports each ("Sending sparse 'userdata' 1/N ... OKAY", "Writing 'userdata' ... OKAY"), then "Finished". Do not
touch the cable. This erases all Android data.

If it stops with an error or the cable drops: the boot loader is unaffected. Stay in (or re-enter) fastboot
(Volume Down + Power) and run the same command again from the start. Do not run anything else.

### Step 4 - proof, still tethered

```powershell
.\fastboot.exe boot C:\OnePlusPad4\final\u-boot-iceland-v3.img
```

(the plain install build v3, `979b4076`, the file `record.json` names; RAM only; `fastboot boot` never writes). Expected: U-Boot's text, GRUB's menu (3 s), then
Fedora's first-boot setup on the tablet. Go through the setup. (It never showed up during the rehearsals for a known
reason: GDM opened it about 17 s after every rehearsal boot - r2g's log: "New session 'c1' of user
'gnome-initial-setup' with class 'greeter'" - and about a minute later the rehearsal's acceptance check, on rehearsal
boots only, created its own test user with automatic login and restarted the login screen, which closed the setup.
Nothing in the image creates a user or switches the setup off, so on the installed tablet it is the first screen.)

> **First-boot setup.** It asks for language, keyboard, Wi-Fi, privacy and **your user account and password**:
> the image has no preset user and no default password (finding F8: the rehearsal-only test user never reaches
> the installed system).

On this boot `iceland-slot-mark` checks slot b: LineageOS already marked it successful (C0.8), so it only logs
that and writes nothing (`journalctl -u iceland-slot-mark`). The PC session then runs the acceptance list on this
boot and records GRUB's environment before and after a trial boot (U-Boot's write of GRUB's one-time entry into
`userdata`, the one write no rehearsal can show). Switch off and repeat the tethered boot until you have seen **three
cold boots in a row** reach the desktop.

Until Part D the tablet starts Android when it is switched on without the PC; Android reports damaged data and
offers a factory reset: **choose "Try again" or power off, never the reset** (it would erase Fedora; nothing
worse). Keep this stage short; never let Android run between write 1 and write 2 if you can avoid it (Android
writes a "boot-recovery" command into `misc` when it cannot use its data).

Undo of write 1: section 8 (return to stock), or write the image again.

---

## Part D - write 2: U-Boot into `boot_b`

Only after Part C step 4 passed, and only if decision 3 chose `boot_b` (**decision 3 is still open on 12 Oct**).
What C0 measured: a normal boot into U-Boot from a written `boot_b` counts one try (C0 #4: 7 to 6), and
`fastboot reboot-bootloader` from U-Boot costs none. The flash of write 2 resets slot b to *not successful*, so the
first good Fedora boot must mark it: that is `iceland-slot-mark` (Fedora's `qbootctl -m`, once, after a good boot),
which has not yet run on the tablet. If decision 3 is not `boot_b`, this part is replaced by the `recovery_b`
procedure the PC session writes for that decision.

### Step 1 - check the files and the slot

```powershell
cd C:\platform-tools
(Get-FileHash \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img -Algorithm SHA256).Hash
(Get-FileHash C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img -Algorithm SHA256).Hash
```

Both must equal section 10. The PC session confirms in the same minute: `check-header.py` accepts the footered file
as the install build (it refuses the rehearsal build), and Part A step 6's proof on today's images is `AVB-PROOF:
PASS`. Then put the tablet into the boot loader's fastboot: switch it off (hold Volume Down + Power from Fedora's
U-Boot screen, or power off), hold Volume Down + Power, connect USB. `fastboot getvar product` must answer `canoe`
(the tablet's own boot loader; U-Boot's fastboot is never used for a write):

```powershell
.\fastboot.exe getvar product
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar partition-size:boot_b
```

Expected: `canoe`, `b`, the values written down after C0.8 (successful `yes`), `no`, a number, `0x6000000`.

### Step 2 - the write

Type it exactly; the only partition name is `boot_b`:

```powershell
.\fastboot.exe flash boot_b \\wsl.localhost\Ubuntu-24.04\home\mzak\mainline\build\wf\install\priv\run\boot\u-boot-iceland-footered.img
.\fastboot.exe getvar slot-successful:b
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe reboot
```

Read the two flags **before** the reboot (read only) and note them: a change caused by the flash itself is then told
apart from one caused by the boot.

### Step 3 - proof

1. Unplug the PC. Switch the tablet off and on **three times**. Each time Fedora must reach the desktop.
2. Enter the boot loader once more (power off, hold Volume Down + Power, connect USB) and read:

```powershell
.\fastboot.exe getvar current-slot
.\fastboot.exe getvar slot-retry-count:b
.\fastboot.exe getvar slot-unbootable:b
.\fastboot.exe reboot
```

`current-slot` must be `b` and `slot-unbootable:b` `no`. With the slot marking working, `slot-successful:b` reads
`yes` after the first good Fedora boot and the count no longer goes down (expected from the design and the package
tests; **not yet seen on the tablet**). **If `slot-successful:b` is still `no` and the count went down:** undo write
2 now (below); do not boot again first.

Undo of write 2 (two minutes, from the boot loader):

```powershell
.\fastboot.exe flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img
```

(Android then starts with no data; Fedora stays in `userdata` and can be started tethered as in Part C step 4.)

---

## 7. After the install

- **First start:** Fedora's first-boot setup creates your user account (see Part C step 4); there is no preset
  user or password.
- **First hour:** Wi-Fi, sound, rotation, a suspend and resume, About shows "OnePlus Pad 4"; Settings > Power
  shows "Battery Charging": choose "Preserve Battery Health" (stops at 85 %; on by default from the device package).
  Check once that `iceland-slot-mark` marked slot b (`journalctl -u iceland-slot-mark`; Part D step 3 reads it from
  the boot loader).
- **Sound:** "Speakers" (the protected chain) and the processed microphone are the defaults; the raw ones are named
  "... (raw, unprotected)" - do not use the raw speaker output for loud playback. The speaker make-up is +9 dB (your
  choice); do the **listening check** in the first hour: music and speech at 50 % and 100 %, compared with how
  Android sounded. Louder than Android, distorted or harsh: tell the PC session. The microphone: "Internal
  microphones (voice processing)" is the default (echo canceller -> +14 dB limiter, ceiling -1 dBFS; the microphones
  themselves at stock's TX_DEC 84); "Internal microphones (raw)" is the unprocessed one.
- **Brightness:** the thermal service does not touch the backlight (`BRIGHTNESS=0` in `/etc/iceland/thermal.conf`):
  GNOME's automatic brightness and a sysfs cap fought each other (r151). The skin-temperature policy (CPU / GPU /
  charging, stock 60 / 61 C) is active; a brightness cap returns later as a kernel clamp in the backlight driver,
  as its own tested update. Do not set `BRIGHTNESS=1` yourself.
- **Charging:** until the one sitting with your wall chargers is done (the charging row of the feature matrix),
  charge attended and prefer the PC port or a plain 5 V charger. The tablet does not fast-charge (SuperVOOC is not
  supported); the stock temperature and current limits are enforced by the kernel and the battery guard.
- **Updates:** GNOME Software / `dnf upgrade` as on any Fedora. They can only change files inside the Fedora
  partition. Fedora's own kernels are excluded; our kernel and the few special packages come from the tablet's
  local repository, which the PC fills (`iceland-repo-sync`), and a new kernel only becomes the default after it
  has started once. The image was built with these held: kernel, kernel-core, kernel-modules*, kernel-iceland,
  iio-sensor-proxy, hexagonrpc, libssc, iceland-device, iceland-firmware; Fedora's repositories never offer
  `kernel-iceland*` or `iceland-*`. The device package's hold file (`50-iceland-fedora-hold.repo`, minimal since
  0.28-4) keeps only the sensor programs (`iio-sensor-proxy`, `hexagonrpc`, `libssc`) and `alsa-ucm` from Fedora's
  updates until a rehearsal has passed them (`iceland-update-check` lists what is held back); GRUB, shim, Fedora's
  firmware packages and libcamera update from Fedora as usual. The tablet's generic firmware is the
  `iceland-firmware` package (held; a newer release comes through `iceland-firmware-fetch`, checked against the
  sha256 pins shipped in the device package); the unit-specific files are owned by no package, so an update cannot
  replace them. Do **not**
  upgrade to Fedora 45 until that version has passed the RAM rehearsal (the upgrade is hidden and blocked by the
  device package).
- **Never from inside Fedora:** no partitioning tool on the internal storage, no `dd` to `/dev/sd*`, no firmware
  update tool, no boot-loader tool. The device package makes the other partitions read-only, so a mistake fails
  instead of doing harm; do not remove that rule.
- **Rescue (always available):** the RAM test kit from the PC (`fastboot boot`, as in every test so far) starts
  without using the storage; from there the installed system can be mounted, checked, rolled back to a snapshot,
  or given another kernel. A forgotten password or a full disk is handled the same way.

---

## 8. Back to stock OxygenOS, from any stage

| From | Do |
|---|---|
| Before any write (today) | nothing: reboot starts Android |
| During C0 | C0.7 (the undo): LineageOS returns with its data |
| Only undo write 2 | `fastboot flash boot_b C:\OnePlusPad4\backups\parta-<date-time>\boot_b-before-install.img` (today's LineageOS `boot_b` from Part A step 6, **not** the 27 Sep backup's) |
| Full return to stock | `C:\OnePlusPad4\scripts\39-Return-To-Stock.ps1` (written and dry-run, never executed; it leaves the tablet on slot a) |
| Factory state with a locked boot loader (optional) | step 4 of the same script (`31-Relock-Bootloader.ps1`), only when its own check says the tablet is exactly stock |
| Back to LineageOS after write 1 | **not written yet**: return to stock, then `22-Flash-LineageOS.ps1` (it assumes stock on slot a; to be reviewed for the post-install state before it is ever used) |

`39-Return-To-Stock.ps1` first verifies the backup and the stock images (read-only) and shows a dry run. After you
type its confirmation it writes the stock boot set to both slots and `super` from your backup, erases `userdata`
and `metadata`, and then proves the result is byte-identical stock. It never writes firmware. If it is
interrupted: enter fastboot again (Volume Down + Power) and run it again.

---

## 9. If something is not as described

| What you see | What it means | What to do |
|---|---|---|
| `fastboot flash userdata` fails or the cable drops | incomplete image in `userdata`; boot loader untouched | re-enter fastboot (Volume Down + Power), run the same command again |
| After write 1, Android says "data may be corrupt" | expected between write 1 and write 2 | "Try again" or power off; never "Factory data reset" |
| Tethered boot after write 1 does not reach Fedora | image or chain problem | do not do write 2; RAM-boot the test kit for a look; or return to stock |
| The boot loader shows a verified-boot error (instead of its usual unlocked warning) and stops, after C0's write or write 2 | the boot loader refused `boot_b` (review R-1) | Volume Down + Power into the boot loader's fastboot; undo (C0.7 / write 2's undo); write down the slot flags; no `set_active` |
| `getvar current-slot` reads `a` after C0's write or write 2 | the boot loader marked slot b unbootable and switched (slot counter at zero, or a refused `boot_b`); not expected while slot a is marked unbootable (Part A, 2 Oct) - then it stops in its fastboot instead | write nothing else; undo `boot_b`; then ask the PC session before the one-time `set_active b` or the full return to stock |
| The retry count went down after a boot with U-Boot in `boot_b` | the boot loader counts tries for a slot nobody marks good (section 0.5) | C0: continue only while the count stays above 3, then undo. Write 2: undo at once; decision 3 (`recovery_b`) |
| After C0's write or write 2: U-Boot text, then nothing more, the screen stays on (no PC) | U-Boot found no Fedora and waits in its fastboot; it switches the tablet off after 10 minutes without a PC command | wait, or hold Volume Down + Power for the boot loader. With the PC: `fastboot devices` shows U-Boot; `fastboot oem console` (read only) saves its log |
| U-Boot's screen is still lit after 12 minutes | U-Boot's own power-off did not work on this board | hold Volume Down + Power (the boot loader); tell the PC session (review R-6) |
| A black screen with a `grub>` prompt or a GRUB error | GRUB found no configuration (damaged `/boot`) | hold Volume Down + Power; RAM-boot the rescue kit (level L3) and repair `/boot` |
| After write 2 the tablet shows **LineageOS recovery** ("Can't load Android system") instead of Fedora | `misc` still holds a "boot-recovery" command from an Android boot between the writes that was cut off | in that recovery choose **Reboot system now** (it clears the command), never "Factory data reset" |
| The tablet was switched off and plugged into a charger, and it starts U-Boot / Fedora | the boot loader starts the boot partition in charger mode; with U-Boot there that is Fedora (plan 11.1.6) | expected; no action (charging-screen starts do not count down the slot) |
| After write 2 the tablet starts Android again by itself | the boot loader fell back to another slot | enter fastboot, read the slot flags (Part D step 3), no `set_active`; undo write 2 and ask |
| Fastboot does not appear with Volume Down + Power | cable / driver, or the tablet is still on | hold Volume Down + Power about 15 s, try again, try the other end of the cable; the boot loader was not written by anything in this guide |
| Fedora does not start after an update | a Fedora-side problem | previous kernel or snapshot from GRUB's menu; else the RAM rescue kit |
| Anything not in this table | - | stop; nothing further is written; ask the PC session with the exact text on the screen |

---

## 10. The record (fill in; the writes use only what is written here)

| Item | Value | Date |
|---|---|---|
| Backup verified (Part A step 1) | | |
| Stock images verified (step 2) | | |
| Return-to-stock dry run read (step 3) | | |
| Second copy made and verified (step 4), where | | |
| `data-vendor-....tar` SHA-256 | | |
| Part A step 6: folder `parta-<date-time>`, last line `PARTA: READY FOR C0` | | |
| `boot_b-before-install.img` SHA-256 (size 100663296; `RECORD-parta.txt`) | | |
| `u-boot-iceland-footered.img` SHA-256 (made for today's `boot_b`; `RECORD-parta.txt`) | | |
| AVB proof on today's images (`AVB-PROOF: PASS`, `rot-equal`) | | |
| Slot b flags: current-slot / successful / unbootable / retry-count | | |
| Slot a flags: successful / unbootable / retry-count | | |
| G12: Volume Down + Power from cold reaches the boot loader | | |
| C0.0 RAM probe of the install U-Boot (console saved, Android back) | | |
| C0: R0 / R1 (after the write) / R2 and each cold boot's retry count; did U-Boot switch off by itself | | |
| C0 undo: `boot_b` equal to the saved file, slot b successful again | | |
| Acceptance list passed on the rehearsal boot (Part B, `priv/run/RECORD.txt`) | final rehearsal r156 on B147: accepted; only FAIL G4 = known F54 libcamera race, accepted by the owner (PC session) | 2026-10-13 |
| Update and rollback rehearsal passed | r142 / r142b, r146 / r146b; on B145 r141u + r141ub; on B147 r156u (25 PASS, 0 FAIL) + r156ub (RB2 7/7) (PC session) | 2026-10-13 |
| Final golden and its confirmation rehearsal | B run 147 (manifest `0c35227ddf92`, body `e294b240f98e`, 1727 packages), r156 / r156u / r156ub (PC session) | 2026-10-13 |
| `fedora-iceland.sparse.img` SHA-256, unpacked size (= 237159641088), rebuilt from that golden | `09ea7f446f969f382739bd4797989c939891ac464e53611caaa7bbc7060a150a`, 6591322540 bytes, unpacked 237159641088; offline check 109 PASS / 0 FAIL (`C:\OnePlusPad4\final`, PC session; check again before write 1) | 2026-10-13 |
| `u-boot-iceland-v3.img` SHA-256 (the plain install build, Part C step 4) | `979b40767afba37367354cfe047994acff10b21831f7664933ee30c7dc89f94c` (v3, `record.json` `uboot_plain`) | 2026-10-10 |
| Decisions 0.4 | | |
| Write 1 done, three tethered cold boots, GRUB environment before / after | | |
| Write 2 done (flags right after the flash), three untethered cold boots, retry count unchanged | | |

---

## 11. Known issues and what this build fixes

### Status 13 Oct 2026, morning (FINAL: golden B147 = kernel q89e + iceland-device 0.28-5 + iceland-firmware 11.A.38-3)

- **Final rehearsal r156 / r156u / r156ub on B147: accepted.** New since B145: the kernel on v7.3-rc7 (q89e) with the
  SD video colour fix; the minimal Fedora holds (GRUB, shim, firmware, libcamera update from Fedora); the microphone
  chain (stock TX_DEC 84 in front of the echo canceller, +14 dB limiter after it: speech level as before, raw clipping
  215 samples instead of 68,749, 0 clipped processed samples); the thermal model as part of `iceland-firmware`
  11.A.38-3 (generic, published); the firmware fetch helper with sha256 pins; no random seed in the image.
- **Known issue F54 (accepted by you):** a rare WirePlumber abort when a camera stream stops (libcamera soft-ISP stop
  race; r156 1 of 40 cycles). Not fixed upstream; Fedora's 0.7.1-2 avoided it in 40 / 40 + 40 / 40 cycles (r152) and
  will arrive as a normal update.
- **Brightness:** `BRIGHTNESS=0` - the thermal service leaves the backlight to GNOME until the ktz8869 kernel clamp
  (a later tested change). Skin-temperature control of CPU / GPU / charging is active (stock 60 / 61 / 70 C).
- **Open, yours:** decision 3 and the first real slot marking; G3 (dry run) and G4 (second copy); the two writes
  (`userdata`, then `boot_b`); after the install the listening check and the deferred physical checks (section 0.1).
- **Known, being watched:** raw microphone clipping with the tablet upright (much lower now; the processed microphone
  is the default); SD (BT.601) video from other encoders still needs a GStreamer update (VE-601L CHECK).

### Status 12 Oct 2026, afternoon (superseded by B147; then final: golden B145 = kernel q89d9 + iceland-device 0.28-3 + iceland-firmware 11.A.38-2)

- **Final rehearsal r141 / r141u / r141ub on B145: accepted**, NO-REGRESSION against r139c / r140. New since the
  candidate: the Bluetooth -84 line gone (q89d9, 0291), the speaker make-up +9 dB (your choice) with only the
  protected speakers and the processed microphone listed, the sensors back after a resume (A52), the generic firmware
  as the `iceland-firmware` package, Fedora never offering our package names, update / rollback proven as
  rehearsal rows, hardware video encode and bit-exact decode.
- **Open, yours:** decision 3 (the permanent boot path) and the first real slot marking (enabled in the image); G3
  (dry run) and G4 (second copy); the two writes; after the install the listening check and the deferred physical
  checks (section 0.1).
- **Known, being watched:** raw microphone clipping with the tablet upright (the processed microphone is the default);
  SoundWire bus-clash lines at capture starts (rc6, no audible effect); SD (BT.601) video needs a GStreamer colour
  patch (matrix item); a leftover random seed in the image (offline check, not blocking).

### Status 12 Oct 2026, morning (install candidate: golden B143 = kernel q89d8 + iceland-device 0.28-2)

The tables below are the release-candidate-1 record of 3 Oct and stay as history. Since then (Loop 5 log; rehearsal
r139c on B143: 0 FAIL):
- **Fixed / changed:** the Wi-Fi drop of F43 (the firmware's 802.11d scan off by default, kernel 0189, q86); the Camera app (F44
  family): F54 40 camera cycles PASS with Fedora's libcamera; the Bluetooth address race with bluez 5.87
  (`iceland-bdaddr` v2); the 2 us CPU latency request is dropped while the cable is out (q89d5); RTC time kept
  in SDAM2 across Android and Linux (q89d2); power_now reported (q89d3); the middle speaker amplifiers at stock
  (q89d8); minimal holds (Fedora updates GRUB, shim, libcamera, qbootctl and firmware).
- **Open, PENDING:** the speaker loudness (iceland-device 0.28-3; measurement deferred by the owner); decision 3 (the
  permanent boot path) and the first real slot marking; G10 (update and rollback rehearsal).
- **Known, being watched:** raw microphone clipping with the tablet upright and speakers loud (the processed microphone
  is the default); a display-controller commit timeout seen once during idle dimming (r139b); SoundWire bus-clash
  lines at capture starts (known on rc6, no audible effect seen); which camera sensor module loads (the in-tree driver
  of q89d8 or the private module of the same name) is to be checked in the final rehearsal.

Status 3 Oct 2026, release candidate 1 (kernel q85 = queue 0001-0188, iceland-device 0.19, rehearsal r2i 46 / 0 / 0). The findings come from the logs of the release candidate's rehearsal (r2g, 3 Oct 02:44:
INSTALL-ACCEPT 42 PASS, 1 FAIL, 1 CHECK), consolidated as F1-F23 (`an/r2g-logs/FIX-LIST.md`, private) and grown
by the team's error ledger to F50 and B1-B18; the status column is the ledger's G3 check of release candidate 1's
rehearsal r2i (`wf/ledger/check-r2i.md`) with the main session's review (re-run `wf/docs/tools/mk-final-docs.py`).
What RC1 contains, what each run proved, its known issues (F43 Wi-Fi, F44 Camera app) and the owner's checks:
`docs/guide/RC1-NOTES.md`. "Rehearsal only" and "test only" items do not exist on the installed
tablet; "log only" items change nothing you would notice.

### Fixed during the night of 2-3 October (proven in the rehearsal boots R2-final / r2g)

| What | Before | Now | Proof |
|---|---|---|---|
| Clock at first boot | the tablet started at systemd's built-in date (March 2026): package signatures looked "not yet valid" | `iceland-clock` keeps a time stamp; the first boot starts at the image's build time, NTP takes over with Wi-Fi | r2f / r2g clock PASS |
| Sound on the installed system | no sound card: alsa-lib's install hook called a sequencer module the kernel did not have | `CONFIG_SND_SEQUENCER=m` + a modprobe softdep | r2f / r2g sound PASS (speaker sink, playback running) |
| Auto-rotate under SELinux | SELinux denied iio-sensor-proxy's QRTR socket | a small SELinux module `iceland_sensors` | r2g rotate PASS; the owner saw the screen turn |
| Firewall | firewalld could not start (nftables features missing in the kernel) | nftables config set in the kernel | r2f / r2g firewall PASS |
| First-boot presets | Fedora's preset would have disabled our units | `50-iceland.preset` | r2f presets PASS |
| Touch after a refresh-rate change | the touch firmware re-download failed after modesets | a kernel follower on the panel's enable / disable | r2f touch PASS, 0 firmware errors |
| Cameras in the image | the sensor driver was private and outside the queue | in-tree in the private kernel queue (owner, 3 Oct), stock-derived tuning in the device package, `libcamera-tools` in the image | r2g: libcamera lists 2, 10 frames each, PipeWire 2 sources |
| Kernel package verify | `rpm -V` flagged depmod's generated files | `%ghost` + depmod in `%posttrans` | r2f verify PASS |
| Forbidden package in the image | `uboot-images-armv8` came in with a dependency | excluded | r2f packages PASS |
| First sleep after boot | the pen charger's interrupt woke the first suspend | the driver waits for its start sequence before suspend | run 104 |
| Charger input cut at a hot USB-C connector | the guard could only stop charging; the system load still flowed through the connector | a stock-exact input-suspend lever, used by the guard; v3.1 in the final build | run 103 (v1 flaw found), kit 106 (v3.1: lever, guard, restore PASS) |
| U-Boot boot header values | U-Boot carried old Android version / patch values | header and AVB footer copy today's `boot_b` (17 / 2026-09) | Part A PARTA: READY FOR C0 |
| Rehearsal watchdog | never armed (the driver's maximum is 31 s) | 30 s in rehearsals; the installed system arms none (a later decision) | r2g watchdog PASS |


### The findings and their status in release candidate 1

Ledger G3 check of release candidate 1's rehearsal r2i: 62 records: PASS 51 | FAIL 7 | await 0 | n/a 4 (`wf/ledger/check-r2i.md`; r2i itself: INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK). Statuses below include the main session's review; the plain explanations of the FAILs and the known issues are in `docs/guide/RC1-NOTES.md` (sections 2a, 3a).

| Id | Area | What it is / what you would notice | Where it matters | Owner | Gate | Status in the final build |
|---|---|---|---|---|---|---|
| F1 | Cameras | GNOME Camera (Snapshot) crashes when it starts (SIGBUS in PipeWire's device monitor inside the app); the cameras themselves work | installed system | fedtest | G2 | **fixed in this build** (r2h PASS; on r2i the app started 6 times without a crash - the suite's Snapshot step failed on F44) |
| F2 | Cameras | the CMA dma-heap (32 MB) was too small for full-resolution frames (13 MP rear, 8 MP front), so the largest photo modes failed; the final build no longer exports CMA as dma-heaps, full-size buffers come from the system heap | installed system | camfix | G2 | **fixed in this build** (r2h PASS; on r2i the kernel side passed - system heap only, full-size frames; the suite missed its line by an index bug) |
| F3 | Cameras | the acceptance check read the wrong tuning-file line (libcamera loads the right file for each camera) | test only | install | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F4 | Cameras | the debugger's own camera probes (arguments, missing tool) | test only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F5 | Cameras | libcamera has no sensor data for SC1320CS / SC820CS (generic gain model, assumed delays, no flip controls): exposure and gain less exact than stock | installed system | camfix | G1 | deferred: libcamera sensor data for SC1320CS / SC820CS comes later (the cameras work with the generic model) |
| F6 | Cameras | camss warns that its test-pattern entities have no function set | log only | camfix | G3 | **fixed in this build** (r2i PASS) |
| F7 | Install rehearsal | the rehearsal's guard took the probe's extension as its limit (625 s instead of 1500 s) and ended the session early | rehearsal only | install | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F8 | First-boot setup | in rehearsals the acceptance step's test user replaces GNOME's first-boot setup (and its greeter logs a crash); the installed system must show the setup | rehearsal only | install | G2 | benign, rehearsal only (the installed system shows the first-boot setup); a new WirePlumber line on r2i (F50) is being classified |
| F9 | System | "Failed to preset all unit ... Read-only file system" lines | log only | fedtest | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F10 | System | the system user / group `tss` is missing (tpm2-tss sysusers not applied): tmpfiles and udev warnings | installed system (cosmetic) | install | G3 | **fixed in this build** (r2i PASS) |
| F11 | Wi-Fi | the regulatory country request is refused and `setregdomain` cannot determine a country; the firmware's US stays (owner decision 10) | installed system | klog | G3 | **fixed in this build** (r2i PASS) |
| F12 | Power / thermal | irqbalance cannot receive thermal messages (CONFIG_THERMAL_NETLINK not set) | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F13 | Boot | the initramfs' udevd cannot resolve the bpf system call (libseccomp missing in the initramfs) | log only | install | G3 | **fixed in this build** (r2i PASS) |
| F14 | Storage | "Failed to write bfq to queue/scheduler: Device or resource busy" on sda-sdd | installed system (the disk scheduler: 3-5 of the 6 UFS disks kept the old one at random) | install | G3 | **fixed in this build** (r2i PASS) |
| F15 | Kernel / DT | reserved-memory overlap between `cpucp` and `pdp` at 0x81200000 | log only (memory map) | klog | G3 | **fixed in this build** (r2i PASS) |
| F16a | Power | gcc / gxclkctl / gpucc reach sync_state only by the timeout, held by the GPU's GMU node (no driver of its own, by design); power-benign | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F16b | Kernel / DT | the CoreSight trace NoC stays in deferred probe (its driver is not built) | log only | klog | G3 | **fixed in this build** (r2i PASS) |
| F17 | Audio | SoundWire 7630000 port counts differ from the controller (din 4 vs 6, dout 0 vs 1) | log only (microphone path) | klog | G3 | **fixed in this build** (r2i PASS) |
| F18 | Audio | bus clashes on the headset codec's SoundWire bus, a codec parity error, the headset-detection -16 burst | installed system (headset detection) | klog | G3 | **fixed in this build** - queue 0186-0188 (kernel q85); kit 110 and r2i PASS; the USB-C jack mode (k5) stays an opt-in |
| F19 | Bluetooth | two "Frame reassembly failed (-84)" lines at power-on | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F20 | Wi-Fi / PCIe | PCIe supplies not described (dummy regulators) and about 11 probe attempts before Wi-Fi binds | installed system (boot time) | klog | G3 | **fixed in this build** (r2i PASS) |
| F21 | Kernel / DT | other dummy or missing supplies (GPU vdd / vddcx, pwrseq vddant, UFS vdd-hba / vccq2) | log only (to prove optional) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F22 | USB-C | pmic-glink "Failed to create device link" warnings | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F23 | Audio | "MultiMedia2 Playback: no backend DAIs enabled" and a quiet loopback share | log only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F24 | Boot / power | the device package said `iceland-cmdline` adds clk / pd / regulator `_ignore_unused` to every boot entry, but its call ran before the kernel's boot entry existed and failed silently, so every rehearsal booted without them - and worked fully, in the better power state. Decision (install workflow, 3 Oct): no flags; `iceland-cmdline` now removes them from every entry and `/etc/kernel/cmdline`; README, guides and package agree | installed system (power, documentation) | install | G3 | **fixed in this build** (r2i PASS) |
| F25 | Tests | the debugger suite's own false alarms (units, a serial-number read, a truncated command, a watchdog line) | test only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F26 | System | PAM setcred fails (audit res=failed) for the user@ managers of root, iceland and gnome-initial-setup | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F27 | System | GNOME Settings global-shortcuts provider (dbus-:1.N-org.gnome.Settings.GlobalShortcutsProvider) exits with failure | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2h) |
| F28 | System | login sound missing: libcanberra 'Failed to play sound: File or data not found' (sound theme not in the image?) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F29 | System | hexagonrpcd: Could not open oemconfig.so (+ 'Unsupported method') - sensor-hub daemon files | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F30 | Bluetooth | bluetoothd cannot set its default system configuration for hci0 | log only | klog | G1 | benign, confirmed by the debugger and the reviewer (r2i) |
| F31 | System | wireplumber reserve-device assertion: wp_reserve_device_own_name: assertion 'self->owner_id == 0' failed (audio device reservation) | log only (benign) | klog | G2 | benign; its probe passed on r2i; a new WirePlumber line in its subsystem (F50) is being classified |
| F32 | System | udev .link settings cannot be applied to the USB gadget usb0 (Could not set Alias=, MACAddress= ... ignoring) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F33 | System | irqbalance: No directory /sys/devices/platform/31091000.pmu/ (PMU IRQ owner without a platform device dir) | log only (benign) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F34 | System | NetworkManager: p2p-dev-wlp1s0 error setting IPv4 forwarding: Resource temporarily unavailable | log only (benign) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F35 | System | ModemManager probes a600000.usb and the WCN7860 PCIe function: not supported by any plugin (no modem on this tablet) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F36 | System | benign to confirm: GNOME first-login / offline noise (keyring socket, geolocation off, malcontent, realmd, rsyslog first run, gvfs, gsd-keyboard assertion, app warnings, polkit, portal parent window, abrt journal) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F37 | System | systemd-logind: BLS entry 'Unknown line grub_arg / grub_class / grub_users, ignoring' (x12 per boot) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F38 | Desktop | the on-screen keyboard raised an error in a modal dialog (e.g. a password prompt) | installed system | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F39 | Cameras | camera I2C bus: one GPI DMA error (-5) per boot - the camera module's EEPROM (0x58) does not answer at power-up in GPI mode | log only | camfix | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F40 | GPU | the GPU's GMU logs a delay in a fenced register write | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2h) |
| F41 | Desktop | gnome-session asks for the screensaver state before GNOME Shell offers it, once at a fresh login (GNOME behaviour) | log only | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F42 | Audio | the headset codec's SoundWire RX bus logged a bus clash and a codec parity error (r2g, r2h) | log only | klog | G0 | seen in r2g / r2h, not in kit 110 or r2i (no bus clash or parity error there); being classified (G0) |
| F43 | Wi-Fi | on the owner's network the connection drops after about 110 s and every reconnect (2.4 and 5 GHz) fails until a reboot: the Wi-Fi firmware's 802.11d scan is re-armed at every disconnect; stock switches 802.11d off | installed system | klog | G0 | **known issue of RC1** - fix k9 in loop 3 (docs/guide/RC1-NOTES.md, section 3a) |
| F44 | Cameras | the Camera app can fail to start a camera when another camera program used the other camera since login (a stale link in the camera pipeline) | installed system | camfix | G0 | **known issue of RC1** - loop 3 (camfix; docs/guide/RC1-NOTES.md, section 3a) |
| F45 | Desktop | GNOME Software can abort after a network change (an upstream GTK 4 accessibility assertion) | log only | install | G1 | benign, confirmed by the debugger and the reviewer (r2i) |
| F46 | System | benign: GNOME Shell: 'Gio.IOErrorEnum: Timeout was reached' when NetworkManager re-asks for the W... | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F47 | System | benign: gsd-xsettings: no UI scaling factor when the X11 services start on demand | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F48 | System | benign: the session's end: zram stop res=failed and 'watchdog did not stop!' at the reboot | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F49 | System | benign: GNOME Software's third-party repositories question: the authorisation was dismissed | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F50 | System | user WirePlumber startup: wp-event-dispatcher 'failed to activate item: Object activation aborted: proxy destroyed' (benign pending the debugger) | installed system | install | G0 | being classified (G0) |
| CHGSAFE-V3 | Charging | the charger input cut at a hot USB-C connector (kernel lever + battery guard) and its desktop notice | installed system (safety) | chgsafe | G3 (kit 106) | **fixed in this build** - proven in kit 106 (v3.1: the lever, the guard and the restore PASS; 219 unit checks) |
| SLEEP-Q84 | Sleep | s2idle on the consolidated kernel q84, incl. the pen charger's first-sleep fix | installed system | sleeppower | G3 | **fixed in this build** - proven in kits 106 and 108 (q84) and 110 (q85) |

Benign groups (B-ids; noise that is expected on this hardware or first boot):

| Id | What | Status |
|---|---|---|
| B1 | benign: greeter wireplumber IPC refused at session stop (FIX-LIST) (+ IPCPipe 'Failed to call async' of the same stop: to confirm, camfix) | benign (expected noise) |
| B2 | benign to confirm: alsactl no asound.state (first boot) | benign, confirmed in r2i |
| B3 | benign to confirm: colord EDID too small (DSI panel) | benign, confirmed in r2i |
| B4 | benign to confirm: gsd-usb-protection without USBGuard | benign, confirmed in r2i |
| B5 | benign to confirm: dnf / gnome-software / PackageKit offline | benign, confirmed in r2i |
| B6 | benign to confirm: gnome-shell JS errors / warnings | benign (expected noise) |
| B7 | benign to confirm: gsd-media-keys grabs | benign (expected noise) |
| B8 | benign upstream: ALSA control name truncated | benign, confirmed in r2i |
| B9 | benign upstream: rx_macro unsorted reg_defaults | benign, confirmed in r2i |
| B10 | benign upstream: GIC ITS table sizes reduced | benign, confirmed in r2i |
| B11 | benign upstream: arm-scmi no fast channel, regular messaging | benign, confirmed in r2i |
| B12 | benign upstream: SELinux checkreqprot (tmpfiles) | benign, confirmed in r2i |
| B13 | benign upstream: simple-framebuffer prefers memory-region | benign, confirmed in r2i |
| B14 | benign upstream: kauditd callbacks suppressed | benign (expected noise) |
| B15 | benign: Android bootloader reset reason (PS_HOLD reset = every Linux reboot here) | benign (expected noise) |
| B16 | ledger: info lines that only look like errors (IRQ names 'fatal' / 'overflow', SCMI max-rx-timeout, unit descriptions) | benign (expected noise) |
| B17 | benign: desktop deprecation warnings (GTK style-*.css, Adw properties, dbus eavesdropping, udev-settle pulled by upower) | benign (expected noise) |

### Long-standing limits (not bugs of this build)

- Speakers: the -12 dB cap of RC1 is gone (0.27r6: DSP stream at stock 0 dB, amplifiers at stock); speaker protection
  is the device package's own chain (no mainline driver); the make-up is +9 dB by your choice (0.28-3 onwards; the
  listening check after the install decides).
- No fast charging (SuperVOOC / PPS); bypass charging is built and reviewed but deferred (owner, 2 Oct).
- No automatic focus (libcamera's simple pipeline); the lens holds stock's start position.
- The deepest SoC sleep state (AOSS sleep) is out of reach on mainline; CX collapse is reached (95-98 % of a sleep).
- Wi-Fi stays off in sleep (owner, 2 Oct); the Wi-Fi country stays the firmware's US (owner decision 10).
- Firefox decodes video in software; GNOME's player and GNOME Web use the hardware decoder.
- Running neural networks on the NPU needs Qualcomm's QNN SDK (owner's decision).
- Need your hands once: wall chargers, a night unplugged, the pen (90 s on the magnet side), the keyboard cover, a
  USB-C monitor, USB accessories, a USB headset, the 5 GHz password.

# OnePlus Pad 4 → Fedora 44 GNOME: TODO (sorted by difficulty)

> **Status 14 Oct 2026.** Items are marked as they stand on 14 Oct. "done 13 Oct" means the install day or the
> golden B149 closed it. Items that the sources do not settle are marked "(unverified)" or left open. The feature matrix
> (`docs/features/`, page v62) has the row-by-row state, and `INSTALL-PLAN.md` has the install record.


Updated 2026-09-29. Details: [PLAN.md](PLAN.md) (v4) and [KNOWLEDGE.md](KNOWLEDGE.md) §13.
Each item shows **[priority]** (P0 = safety gate or blocker … P3 = later) and **owner**: M = Mainline (cloud),
PC = PC session, U = user. Tick items when done, in the same commit as the result. Both sessions edit this file.

Difficulty scale:
- **1 Easy:** a decision, a lookup or a config line; hours.
- **2 Moderate:** known pattern, small code/DT change, some testing; a day or two.
- **3 Hard:** new driver work, many devices involved or long debugging tails; days to weeks.
- **4 Very hard:** reverse engineering or closed parts; weeks, may not be fully solvable.

## Campaign (relay 019, the user 2026-09-29): one run per area, in this order
Audio → Display & input (pink glitches, screen) → Graphics & compute (GPU, NPU) → Power & charging → Thermal → Sleep & power saving → Connectivity → Sensors & camera → Software & packaging (reordered by the user 2026-09-29). **Boot & platform only after the user confirms the final installation.**

## 1 — Easy
- [x] [P0] PC: relay 013: audit every hardware value (sound, brightness, clocks, GPU, speaker/mic tuning, power, thermals) against Pad 4 stock (OxygenOS 11.A.38 / the user's LineageOS trees); replace placeholders - done: stock-values audit of 1,249 values, none above stock (matrix row Software and packaging)
- [x] [P0] M: relay 012 A: standing policy, so the PC runs the build → kit → judge → iterate → queue loop by itself (no tablet writes)
- [x] [P0] U: decide single boot (4e) or dual boot (4-DB) - done 13 Oct: Fedora only (decision 1)
- [x] [P0] U: if dual boot, choose the Android / Fedora (/ shared) partition sizes - not needed (Fedora only, 13 Oct)
- [x] [P0] U: accept that Android's data is wiped once (both slots share userdata) - done 13 Oct: userdata replaced, Android no longer starts
- [x] [P0] U: pick when the first write happens - done 13 Oct (write 1 at 18:31)
- [x] [P0] PC: relay 004 (align the install plan with PLAN v4; ABL `flash userdata` from docs only) - superseded by docs/INSTALL-PLAN.md (status 14 Oct)
- [ ] [P0] PC: relay 005 (recovery_a/b facts, recovery image header, LUN 0 layout) - no status in the sources (unverified); boot_b was used, recovery_b was not
- [x] [P0] PC: relay 008 part 1 (the Workstation 44 app list) - done in effect: the installed system carries the app set (33 of 33 apps open a window; the by-finger check is the owner's)
- [x] [P1] M: local dnf repo for `kernel-iceland` updates (iceland-linux `packaging/repo/make-repo.sh` + `iceland-repo-sync` in iceland-device 0.4; COPR only with the user's OK)
- [x] [P1] M: U-Boot env for dual boot (`fedora_blkmap` by partition name): iceland-u-boot a3c7ca5 (one bootcmd for both layouts)
- [x] [P1] M: dracut config (GPU and touch firmware in the initramfs), kernel options (`iceland-cmdline`) in iceland-device; `lsm=` to be checked on the image
- [x] [P1] U+PC: before writes: file-level `/data/vendor` + persist copy; GPT backup; confirm the 151-partition backup - done 13 Oct: G1 151 partitions intact, G2 stock images, G3 dry run, G4 second copy
- [x] [P2] M: 60 Hz on battery / 120 Hz on AC (`iceland-refresh`), CDSP off unless used (`iceland-npu`), in iceland-device 0.4; PC tests on the tablet
- [ ] [P2] M: power-saver profile (tuned-ppd) with stock power-saving values (needs relay 013)
- [x] [P2] M: after an Android OTA (dual boot), a helper to re-flash U-Boot into the new slot's recovery: `tools/dualboot/reflash-recovery.ps1` (only after 4-DB is approved)
- [ ] [P3] Housekeeping: KNOWLEDGE §13 in sync with PLAN v4 (PC); refresh the cloud kernel tree (M)

## 2 — Moderate
- [x] [P1] PC+U: **GNOME pink/blocky glitches** (user report 2026-09-29) - fixed by queue 0060 (the splash take-over left UBWC unset); watch the first login of later boots
- [x] [P0] M: thermal DT: skin zone `pmh0101_skin_therm` (48/50/60 °C steps, 90 °C critical), XO zone (78/80 °C, 90 °C). Candidate patch in relay 009
- [ ] [P0] PC: test and queue relay 009 (skin/XO zones) with a 15 min load kit
- [ ] [P0] M+PC: GPU trips confirmed against stock (kaanapali.dtsi already maps gpuss-N at 105 °C to `&gpu`); GPU devfreq cooling tested (glmark2, 10 min)
- [ ] [P0] PC: thermal load kits (CPU, GPU, combined, charging; 15 min each; skin ≤ 50 °C sustained)
- [ ] [P0] PC: relay 006 (stock skin gear table, thermal-engine rules, GPU trips, BCL, standby numbers)
- [ ] [P0] PC: relay 007 (reading `oplus_chg`: OTG glink message, charge stop/limit, what the firmware does alone)
- [ ] [P1] PC+U: Y10: GNOME from the RAM rootfs + the touch/pen window - GNOME runs on the installed system; touch ok; pen is an owner check
- [x] [P1] M: `kernel-iceland` rpm spec + kernel-install plugin (DTB to the ESP `dtb/qcom/…`; no GRUB `devicetree` line, to keep U-Boot's memory fixups): iceland-linux bcdab5e; test-built (aarch64, 948 modules)
- [x] [P1] M: `iceland-device` rpm v0.1 (kernel exclusion, DEFAULTKERNEL, s2idle, journald cap, upgrade block, fwupd guard, BT address unit, kernel options, dracut, Wi-Fi power save): iceland-mainline 59d170c, built with rpmbuild
- [ ] [P2] M: iceland-device additions as the hardware lands: UCM volume caps, 60 Hz on battery, charge limit, libinput quirks
- [x] [P1] M+PC: firmware into `/usr/lib/firmware/updates/` (extractor + OTA for the `super` files), never uploaded - done: iceland-firmware 11.A.38-3 (generic files, sha256-pinned fetch)
- [ ] [P1] PC: full app set in RAM (relay 008 part 2): Files, Software + Flathub, Settings, Firefox, Extensions, Tweaks, OSK - 33 of 33 apps open a window; the by-finger check is the owner's
- [x] [P1] PC: RAM rehearsal of the real Workstation 44 image with our packages - done (r158 on golden B149)
- [x] [P1] PC: build the install image (packages, `/.autorelabel`, sparse) - done 13 Oct (image from B149, sha256 prefix 2246e9a7, held until the owner's writes)
- [x] [P1] U: write Fedora (`userdata`, then boot tethered; first boot + updates) - done 13 Oct (userdata 18:31; tethered boots 20:43-20:44; first-boot setup by the owner; GNOME Software works)
- [x] [P1] U: place U-Boot (`recovery_<slot>` for dual boot, or `boot`); test rollback once - done 13 Oct: boot_b (footered v3); recovery_b not used. Rollback on the tablet: open (proven in rehearsals r142b and r146b)
- [x] [P2] PC: suspend (s2idle + RTC wake) works after the WAKE# fix (0040)
- [ ] [P2] M+PC: wake sources: power key, lid open, pogo keyboard (TLMM151), RTC, charger - power key and alarm wake ok; cover, lid and charger wake are owner checks
- [x] [P2] M: nt36536 pen: ABS resolution + stylus buttons, libinput accepts the pen
- [ ] [P2] PC+U: confirm touch and pen events; lid closing
- [ ] [P2] PC: Wi-Fi under NetworkManager; 5/6 GHz (U: an AP in range); regulatory domain
- [x] [P2] M+PC: BT address applied at boot
- [ ] [P2] PC: Bluetooth pairing under GNOME
- [ ] [P2] M: restore the Type-C graph in the DT (UCSI -> dwc3 role switch, QMP combo, WCD939x mux) - partly: UCSI and the PD contract work; DP over USB-C shows no picture (14 Oct)
- [ ] [P2] PC+U: charging measurements per charger; charge limit exposed in GNOME (if the firmware accepts it) - the 80 / 85 % limit works in GNOME; the wall-charger sitting is the owner's
- [ ] [P2] M+PC: EAS energy model, cpuidle usage, GPU idle, UFS runtime PM / auto-hibern8, dwc3 runtime suspend
- [ ] [P2] PC: power measurements vs stock (idle screen-on, video, web, radios idle) - installed idle 2.08 W (14 Oct); video and web measurements open
- [ ] [P3] Hardware video decode (Iris, `vpu40_2v.mbn`): the driver exists in infiniti
- [ ] [P3] Kernel loose ends: SoundWire port-count warnings, qnoc sync_state for the simpledrm fallback
- [ ] [P3] Suspend-then-hibernate (swap ≥ 12 GB)
- [ ] [P3] Other distros (Phase 7): the same kernel, a per-distro wrapper

## 3 — Hard
- [x] [P2] PC: **GPU acceleration validation** (relay 012 B): done for the matrix rows (Vulkan 1.4 on Mesa 26.2.4, GL 4.6; dEQP failures known). Chromium / Electron GPU acceleration: open
- [ ] [P2] PC: **NPU**: CDSP boot + `/dev/fastrpc-cdsp` + a `quic/fastrpc` offload; optional QNN HTP model run (relay 012 C); on-demand start/stop without blocking s2idle
- [ ] [P2] M: `iceland-device`: udev permissions for `/dev/fastrpc-*` once relay 012 C works
- [ ] [P0] M+PC: BCL / low-battery protection. There may be no mainline driver for the PMH0101/PMIH010x BCL, so a
      userspace guard is the fallback; test at low battery with no brown-out
- [x] [P0] M: `iceland-battery-guard`, verified against stock (iceland-device 0.3, 30 tests; research/battery-guard-verification.md)
- [x] [P0] M: battmgr: stock Pad 4 per-type charger inputs (PD 1.5 A at 9 V etc.), `charge_behaviour`, lower-only `constant_charge_current_max` (candidate, relay 015)
- [x] [P0] M: usb-therm zone (stock USB-C thermistor, 57 °C stop) candidate patch (relay 015)
- [x] [P0] PC: test and queue the relay 015 patches, then test the guard on the tablet - queued as 0053; the guard is in iceland-device
- [ ] [P0] PC+U: charging safety without the OnePlus stack: derating, termination, dual-cell safety. It depends on
      what the SoCCP firmware does alone; until proven, charge attended only with an 80 % limit
- [ ] [P1] U (4-DB only): repartition LUN 0 (shrink `userdata`, add `fedora`) with the guarded partitioner, then
      `fastboot -w`. Easy to run, high stakes
- [ ] [P2] M+PC: prove deep sleep (`qcom_stats` AOSS/CX/DDR); find what blocks it (remoteprocs, USB, PCIe/Wi-Fi)
- [ ] [P2] M+PC: resume of every device (panel + KTZ8869, touch firmware re-download, USB, Wi-Fi, BT, GPU); 20/20 cycles
- [ ] [P2] PC: 8 h overnight drain ≤ ~1 %/h (a long debugging tail)
- [x] [P2] M+PC: speakers play (TDM, 0038 + 0041–0045) and mics capture, at the ALSA level
- [x] [P1] PC: GNOME sound on a normal boot - done: devices, names and defaults PASS (r140, r141); the listening check is the owner's
- [x] [P1] PC: test the speaker gain cap (kernel patch + capped topology + UCM) - done: amplifiers at stock; make-up +9 dB (owner's choice); the listening check is the owner's
- [x] [P1] M: package UCM + Pad 4 topology in iceland-device once the cap is tested - done (iceland-device)
- [ ] [P2] M+PC: OTG enable (the OnePlus glink message), host mode, host + charging via a PD hub, reverse charging - open: no host-mode test with accessories yet (owner check)
- [ ] [P2] M+PC: DisplayPort alt mode (pmic-glink altmode + QMP combo + DP) - partly: HPD, EDID and the PD contract work; no picture on a bus-powered monitor (14 Oct)
- [ ] [P2] PC: map `super` (LP metadata) for the extractor; refresh firmware from the current slot at boot
- [x] [P3] Sensors + auto-rotate (SSC via hexagonrpcd + libssc) - done: accelerometer, compass, light and proximity; auto-rotate ok
- [ ] [P3] Pogo keyboard (the private `tinno,pogo_keyboard` UART protocol, from the downstream source)
- [ ] [P3] Pen charging (a new MT5806 driver + PMIH010x hboost + pen glink messages)
- [ ] [P3] pstore across the PS_HOLD hard reset
- [ ] [P3] Upstreaming (0025/0026/0028/0035, Pad 4 DTS, KTZ8869, TFA9865, U-Boot board): only with the user's OK - not done; the owner decides each step (0292 held)

## 4 — Very hard
- [ ] [P2] TFA9865 **speaker protection** (NXP's closed `tfa98xx.cnt` + calibration; no mainline equivalent). Until
      then the volume stays capped
- [ ] [P3] GPU turnip/Vulkan for the a840 (waiting on Mesa upstream; we can only test)
- [ ] [P3] PPS fast charging via the SC8547D charge pumps (the OnePlus glink PPS path + a charge-pump driver).
      UFCS and SuperVOOC are out of scope
- [ ] [P3] **Cameras** (plan: `research/camera-bringup.md`, PLAN 5-CAM), the hardest item overall:
  - [x] PC: C0: stock values (actuator IC, EEPROMs, LDOs, MCLK clock, power sequence) + register tables from `sensormodule.bin` + LineageOS I2C trace (relay 014) - done 30 Sep
  - [x] M: C1: DT (i2c@884000 sensors, CAMSS CSIPHY4/5 ports, at24 EEPROMs) - done
  - [x] M: C2: `sc1320cs`/`sc820cs` V4L2 drivers - done: both sensors stream (the in-tree driver is used)
  - [x] PC: C3: test pattern -> raw frames -> 5 min stream - done (raw frames and streams through libcamera)
  - [ ] M+PC: C4: VCM actuator + EEPROM calibration - partly: focus fixed (the lens holds its start position 450); no autofocus
  - [x] PC: C5: libcamera simple + softISP, stock-derived tuning, PipeWire -> Snapshot/Firefox - done with libcamera 0.7.1-2 (the Snapshot and Firefox checks are the owner's)
  - [ ] C6: PDAF, more modes, the flash as a V4L2 flash

## Suggested order
Work top-down inside **P0**, then **P1**. Where the priority is equal, do the easier item first. The fastest route to
an installed, safe Fedora GNOME:
1. the easy P0 decisions and lookups;
2. the moderate P0 thermal work;
3. the hard P0 charging and BCL work;
4. the P1 packaging and install.

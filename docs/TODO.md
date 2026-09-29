# OnePlus Pad 4 → Fedora 44 GNOME: TODO (sorted by difficulty)

Updated 2026-09-29. Details: [PLAN.md](PLAN.md) (v4) and [KNOWLEDGE.md](KNOWLEDGE.md) §13.
Each item shows **[priority]** (P0 = safety gate or blocker … P3 = later) and **owner**: M = Mainline (cloud),
PC = PC session, U = user. Tick items when done, in the same commit as the result. Both sessions edit this file.

Difficulty scale:
- **1 Easy:** a decision, a lookup or a config line; hours.
- **2 Moderate:** known pattern, small code/DT change, some testing; a day or two.
- **3 Hard:** new driver work, many devices involved or long debugging tails; days to weeks.
- **4 Very hard:** reverse engineering or closed parts; weeks, may not be fully solvable.

## Campaign (relay 019, the user 2026-09-29): one run per area, in this order
Audio → Power & charging → Thermal → Sleep & power saving → Display & input → Connectivity → Graphics & compute → Sensors & camera → Software & packaging. **Boot & platform only after the user confirms the final installation.**

## 1 — Easy
- [ ] [P0] PC: relay 013: audit every hardware value (sound, brightness, clocks, GPU, speaker/mic tuning, power, thermals) against Pad 4 stock (OxygenOS 11.A.38 / the user's LineageOS trees); replace placeholders
- [x] [P0] M: relay 012 A: standing policy, so the PC runs the build → kit → judge → iterate → queue loop by itself (no tablet writes)
- [ ] [P0] U: decide single boot (4e) or dual boot (4-DB)
- [ ] [P0] U: if dual boot, choose the Android / Fedora (/ shared) partition sizes
- [ ] [P0] U: accept that Android's data is wiped once (both slots share userdata)
- [ ] [P0] U: pick when the first write happens
- [ ] [P0] PC: relay 004 (align `phase4/INSTALL-PLAN.md` with PLAN v4; ABL `flash userdata` from docs only)
- [ ] [P0] PC: relay 005 (recovery_a/b facts, recovery image header, LUN 0 layout)
- [ ] [P0] PC: relay 008 part 1 (the Workstation 44 app list)
- [x] [P1] M: local dnf repo for `kernel-iceland` updates (iceland-linux `packaging/repo/make-repo.sh` + `iceland-repo-sync` in iceland-device 0.4; COPR only with the user's OK)
- [x] [P1] M: U-Boot env for dual boot (`fedora_blkmap` by partition name): iceland-u-boot a3c7ca5 (one bootcmd for both layouts)
- [x] [P1] M: dracut config (GPU and touch firmware in the initramfs), kernel options (`iceland-cmdline`) in iceland-device; `lsm=` to be checked on the image
- [ ] [P1] U+PC: before writes: file-level `/data/vendor` + persist copy; GPT backup; confirm the 151-partition backup
- [x] [P2] M: 60 Hz on battery / 120 Hz on AC (`iceland-refresh`), CDSP off unless used (`iceland-npu`), in iceland-device 0.4; PC tests on the tablet
- [ ] [P2] M: power-saver profile (tuned-ppd) with stock power-saving values (needs relay 013)
- [x] [P2] M: after an Android OTA (dual boot), a helper to re-flash U-Boot into the new slot's recovery: `tools/dualboot/reflash-recovery.ps1` (only after 4-DB is approved)
- [ ] [P3] Housekeeping: KNOWLEDGE §13 in sync with PLAN v4 (PC); refresh the cloud kernel tree (M)

## 2 — Moderate
- [ ] [P1] PC+U: **GNOME pink/blocky glitches** (user report 2026-09-29): isolate (relay 011: screenshot vs screen, 60 Hz, `FD_MESA_DEBUG=noubwc`, software GL), then fix
- [x] [P0] M: thermal DT: skin zone `pmh0101_skin_therm` (48/50/60 °C steps, 90 °C critical), XO zone (78/80 °C, 90 °C). Candidate patch in relay 009
- [ ] [P0] PC: test and queue relay 009 (skin/XO zones) with a 15 min load kit
- [ ] [P0] M+PC: GPU trips confirmed against stock (kaanapali.dtsi already maps gpuss-N at 105 °C to `&gpu`); GPU devfreq cooling tested (glmark2, 10 min)
- [ ] [P0] PC: thermal load kits (CPU, GPU, combined, charging; 15 min each; skin ≤ 50 °C sustained)
- [ ] [P0] PC: relay 006 (stock skin gear table, thermal-engine rules, GPU trips, BCL, standby numbers)
- [ ] [P0] PC: relay 007 (reading `oplus_chg`: OTG glink message, charge stop/limit, what the firmware does alone)
- [ ] [P1] PC+U: Y10: GNOME from `rootfs-gnome.tar.gz` in RAM + the touch/pen window
- [x] [P1] M: `kernel-iceland` rpm spec + kernel-install plugin (DTB to the ESP `dtb/qcom/…`; no GRUB `devicetree` line, to keep U-Boot's memory fixups): iceland-linux bcdab5e; test-built (aarch64, 948 modules)
- [x] [P1] M: `iceland-device` rpm v0.1 (kernel exclusion, DEFAULTKERNEL, s2idle, journald cap, upgrade block, fwupd guard, BT address unit, kernel options, dracut, Wi-Fi power save): iceland-mainline 59d170c, built with rpmbuild
- [ ] [P2] M: iceland-device additions as the hardware lands: UCM volume caps, 60 Hz on battery, charge limit, libinput quirks
- [ ] [P1] M+PC: firmware into `/usr/lib/firmware/updates/` (extractor + OTA for the `super` files), never uploaded
- [ ] [P1] PC: full app set in RAM (relay 008 part 2): Files, Software + Flathub, Settings, Firefox, Extensions, Tweaks, OSK
- [ ] [P1] PC: RAM rehearsal of the real Workstation 44 image with our packages
- [ ] [P1] PC: build the install image (packages, `/.autorelabel`, sparse)
- [ ] [P1] U: write Fedora (ABL `fastboot flash userdata`, or a guarded `dd` into `fedora`); boot tethered; first boot + updates
- [ ] [P1] U: place U-Boot (`recovery_<slot>` for dual boot, or `boot`); test rollback once
- [x] [P2] PC: suspend (s2idle + RTC wake) works after the WAKE# fix (0040)
- [ ] [P2] M+PC: wake sources: power key, lid open, pogo keyboard (TLMM151), RTC, charger
- [x] [P2] M: nt36536 pen: ABS resolution + stylus buttons, libinput accepts the pen
- [ ] [P2] PC+U: confirm touch and pen events; lid closing
- [ ] [P2] PC: Wi-Fi under NetworkManager; 5/6 GHz (U: an AP in range); regulatory domain
- [x] [P2] M+PC: BT address applied at boot
- [ ] [P2] PC: Bluetooth pairing under GNOME
- [ ] [P2] M: restore the Type-C graph in the DT (UCSI → dwc3 role switch, QMP combo, WCD939x mux)
- [ ] [P2] PC+U: charging measurements per charger; charge limit exposed in GNOME (if the firmware accepts it)
- [ ] [P2] M+PC: EAS energy model, cpuidle usage, GPU idle, UFS runtime PM / auto-hibern8, dwc3 runtime suspend
- [ ] [P2] PC: power measurements vs stock (idle screen-on, video, web, radios idle)
- [ ] [P3] Hardware video decode (Iris, `vpu40_2v.mbn`): the driver exists in infiniti
- [ ] [P3] Kernel loose ends: SoundWire port-count warnings, qnoc sync_state for the simpledrm fallback
- [ ] [P3] Suspend-then-hibernate (swap ≥ 12 GB)
- [ ] [P3] Other distros (Phase 7): the same kernel, a per-distro wrapper

## 3 — Hard
- [ ] [P2] PC: **GPU acceleration validation** (relay 012 B): GNOME on the a840, dEQP GLES subsets, glmark2/WebGL, 30 min stress, devfreq, turnip when available
- [ ] [P2] PC: **NPU**: CDSP boot + `/dev/fastrpc-cdsp` + a `quic/fastrpc` offload; optional QNN HTP model run (relay 012 C); on-demand start/stop without blocking s2idle
- [ ] [P2] M: `iceland-device`: udev permissions for `/dev/fastrpc-*` once relay 012 C works
- [ ] [P0] M+PC: BCL / low-battery protection. There may be no mainline driver for the PMH0101/PMIH010x BCL, so a
      userspace guard is the fallback; test at low battery with no brown-out
- [x] [P0] M: `iceland-battery-guard`, verified against stock (iceland-device 0.3, 30 tests; research/battery-guard-verification.md)
- [x] [P0] M: battmgr: stock Pad 4 per-type charger inputs (PD 1.5 A at 9 V etc.), `charge_behaviour`, lower-only `constant_charge_current_max` (candidate, relay 015)
- [x] [P0] M: usb-therm zone (stock USB-C thermistor, 57 °C stop) candidate patch (relay 015)
- [ ] [P0] PC: test and queue the relay 015 patches, then test the guard on the tablet
- [ ] [P0] PC+U: charging safety without the OnePlus stack: derating, termination, dual-cell safety. It depends on
      what the SoCCP firmware does alone; until proven, charge attended only with an 80 % limit
- [ ] [P1] U (4-DB only): repartition LUN 0 (shrink `userdata`, add `fedora`) with the guarded partitioner, then
      `fastboot -w`. Easy to run, high stakes
- [ ] [P2] M+PC: prove deep sleep (`qcom_stats` AOSS/CX/DDR); find what blocks it (remoteprocs, USB, PCIe/Wi-Fi)
- [ ] [P2] M+PC: resume of every device (panel + KTZ8869, touch firmware re-download, USB, Wi-Fi, BT, GPU); 20/20 cycles
- [ ] [P2] PC: 8 h overnight drain ≤ ~1 %/h (a long debugging tail)
- [x] [P2] M+PC: speakers play (TDM, 0038 + 0041–0045) and mics capture, at the ALSA level
- [ ] [P1] PC: GNOME sound on a normal boot (user: still Dummy Output, no mic): bake the UCM + capped topology into the rootfs, alsa-utils for FixedBootSequence (answer user-report-dummy-output); the UCM itself works (S9 probe)
- [ ] [P1] PC: test the speaker gain cap (kernel patch + capped topology + UCM; answer pc-026-s8-s9), then the stock cap value
- [ ] [P1] M: package UCM + Pad 4 topology in iceland-device once the cap is tested
- [ ] [P2] M+PC: OTG enable (the OnePlus glink message), host mode, host + charging via a PD hub, reverse charging
- [ ] [P2] M+PC: DisplayPort alt mode (pmic-glink altmode + QMP combo + DP)
- [ ] [P2] PC: map `super` (LP metadata) for the extractor; refresh firmware from the current slot at boot
- [ ] [P3] Sensors + auto-rotate (SSC via hexagonrpcd + libssc; untested on kaanapali)
- [ ] [P3] Pogo keyboard (the private `tinno,pogo_keyboard` UART protocol, from the downstream source)
- [ ] [P3] Pen charging (a new MT5806 driver + PMIH010x hboost + pen glink messages)
- [ ] [P3] pstore across the PS_HOLD hard reset
- [ ] [P3] Upstreaming (0025/0026/0028/0035, Pad 4 DTS, KTZ8869, TFA9865, U-Boot board): only with the user's OK

## 4 — Very hard
- [ ] [P2] TFA9865 **speaker protection** (NXP's closed `tfa98xx.cnt` + calibration; no mainline equivalent). Until
      then the volume stays capped
- [ ] [P3] GPU turnip/Vulkan for the a840 (waiting on Mesa upstream; we can only test)
- [ ] [P3] PPS fast charging via the SC8547D charge pumps (the OnePlus glink PPS path + a charge-pump driver).
      UFCS and SuperVOOC are out of scope
- [ ] [P3] **Cameras** (plan: `research/camera-bringup.md`, PLAN 5-CAM), the hardest item overall:
  - [ ] PC: C0: stock values (actuator IC, EEPROMs, LDOs, MCLK clock, power sequence) + register tables from `sensormodule.bin` + LineageOS I2C trace (relay 014)
  - [ ] M: C1: DT (i2c@884000 sensors, CAMSS CSIPHY4/5 ports, at24 EEPROMs)
  - [ ] M: C2: `sc1320cs`/`sc820cs` V4L2 drivers (chip ID, one mode each, exposure/gain, test pattern)
  - [ ] PC: C3: test pattern → raw frames → 5 min stream
  - [ ] M+PC: C4: VCM actuator + EEPROM calibration
  - [ ] PC: C5: libcamera simple + softISP, stock-derived tuning, PipeWire → Snapshot/Firefox
  - [ ] C6: PDAF, more modes, the flash as a V4L2 flash

## Suggested order
Work top-down inside **P0**, then **P1**. Where the priority is equal, do the easier item first. The fastest route to
an installed, safe Fedora GNOME:
1. the easy P0 decisions and lookups;
2. the moderate P0 thermal work;
3. the hard P0 charging and BCL work;
4. the P1 packaging and install.

# OnePlus Pad 4 → Fedora 44 GNOME: TODO (sorted by difficulty)

Updated 2026-09-28. Details: [PLAN.md](PLAN.md) (v4) and [KNOWLEDGE.md](KNOWLEDGE.md) §13.
Each item shows **[priority]** (P0 = safety gate or blocker … P3 = later) and **owner**: M = Mainline (cloud),
PC = PC session, U = user. Tick items when done, in the same commit as the result. Both sessions edit this file.

Difficulty scale:
- **1 Easy:** a decision, a lookup or a config line; hours.
- **2 Moderate:** known pattern, small code/DT change, some testing; a day or two.
- **3 Hard:** new driver work, many devices involved or long debugging tails; days to weeks.
- **4 Very hard:** reverse engineering or closed parts; weeks, may not be fully solvable.

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
- [ ] [P1] M: local dnf repo for `kernel-iceland` updates
- [x] [P1] M: U-Boot env for dual boot (`fedora_blkmap` by partition name): iceland-u-boot a3c7ca5 (one bootcmd for both layouts)
- [x] [P1] M: dracut config (GPU and touch firmware in the initramfs), kernel options (`iceland-cmdline`) in iceland-device; `lsm=` to be checked on the image
- [ ] [P1] U+PC: before writes: file-level `/data/vendor` + persist copy; GPT backup; confirm the 151-partition backup
- [ ] [P2] M: 60 Hz on battery / 120–144 Hz on AC hook; CDSP off; power-profiles-daemon config (Wi-Fi power save done in iceland-device)
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
- [x] [P1] M: `kernel-iceland` rpm spec + kernel-install plugin (DTB to the ESP `dtb/qcom/…`; no GRUB `devicetree` line, to keep U-Boot's memory fixups): iceland-linux bcdab5e; a full rpm test build is running
- [x] [P1] M: `iceland-device` rpm v0.1 (kernel exclusion, DEFAULTKERNEL, s2idle, journald cap, upgrade block, fwupd guard, BT address unit, kernel options, dracut, Wi-Fi power save): iceland-mainline 59d170c, built with rpmbuild
- [ ] [P2] M: iceland-device additions as the hardware lands: UCM volume caps, 60 Hz on battery, charge limit, libinput quirks
- [ ] [P1] M+PC: firmware into `/usr/lib/firmware/updates/` (extractor + OTA for the `super` files), never uploaded
- [ ] [P1] PC: full app set in RAM (relay 008 part 2): Files, Software + Flathub, Settings, Firefox, Extensions, Tweaks, OSK
- [ ] [P1] PC: RAM rehearsal of the real Workstation 44 image with our packages
- [ ] [P1] PC: build the install image (packages, `/.autorelabel`, sparse)
- [ ] [P1] U: write Fedora (ABL `fastboot flash userdata`, or a guarded `dd` into `fedora`); boot tethered; first boot + updates
- [ ] [P1] U: place U-Boot (`recovery_<slot>` for dual boot, or `boot`); test rollback once
- [ ] [P2] PC: suspend kit pc-025 (s2idle + RTC wake), first pass
- [ ] [P2] M+PC: wake sources: power key, lid open, pogo keyboard (TLMM151), RTC, charger
- [ ] [P2] M: nt36536 pen: report ABS resolution + stylus buttons (libinput accepts the pen)
- [ ] [P2] PC+U: confirm touch and pen events; lid closing
- [ ] [P2] PC: Wi-Fi under NetworkManager; 5/6 GHz (U: an AP in range); regulatory domain
- [ ] [P2] M+PC: BT address from wlan0's MAC at boot; pairing under GNOME
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
- [ ] [P0] PC+U: charging safety without the OnePlus stack: derating, termination, dual-cell safety. It depends on
      what the SoCCP firmware does alone; until proven, charge attended only with an 80 % limit
- [ ] [P1] U (4-DB only): repartition LUN 0 (shrink `userdata`, add `fedora`) with the guarded partitioner, then
      `fastboot -w`. Easy to run, high stakes
- [ ] [P2] M+PC: prove deep sleep (`qcom_stats` AOSS/CX/DDR); find what blocks it (remoteprocs, USB, PCIe/Wi-Fi)
- [ ] [P2] M+PC: resume of every device (panel + KTZ8869, touch firmware re-download, USB, Wi-Fi, BT, GPU); 20/20 cycles
- [ ] [P2] PC: 8 h overnight drain ≤ ~1 %/h (a long debugging tail)
- [ ] [P2] M: speakers DT link to PRIMARY_TDM_RX_0 + PC: Audio IF (TDM) subgraph m4; nobody has kaanapali audio yet
- [ ] [P2] M+PC: volume caps + UCM, headset, mics
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
- [ ] [P3] **Cameras:** SC1320CS / SC820CS sensor drivers from scratch (no datasheets), kaanapali CAMSS,
      `CAMERA_ICP`, libcamera software ISP (the hardest item overall)

## Suggested order
Work top-down inside **P0**, then **P1**. Where the priority is equal, do the easier item first. The fastest route to
an installed, safe Fedora GNOME:
1. the easy P0 decisions and lookups;
2. the moderate P0 thermal work;
3. the hard P0 charging and BCL work;
4. the P1 packaging and install.

# OnePlus Pad 4 → Fedora 44 GNOME: TODO (by priority)

Updated 2026-09-28. The source of truth for details: [PLAN.md](PLAN.md) (v4) and [KNOWLEDGE.md](KNOWLEDGE.md) §13.
Owner: **M** = Mainline (cloud), **PC** = PC session, **U** = user. Tick items when done, in the same commit as the
result. Both sessions edit this file.

## P0 — Safety gates and decisions (block the install)
- [ ] PC: answer relay 004 (align `phase4/INSTALL-PLAN.md` with PLAN v4; ABL `flash userdata` from docs only)
- [ ] PC: answer relay 005 (recovery_a/b location and size, recovery image header, ABL/AVB behaviour, LUN 0 layout)
- [ ] PC: answer relay 006 (stock skin gear table, thermal-engine rules, GPU trips, BCL, standby reference numbers)
- [ ] PC: answer relay 007 (`oplus_chg`: OTG glink message, charge stop/limit, what the firmware does alone, PPS and pen sizes)
- [ ] PC: answer relay 008 (Workstation 44 app list; Files/Software/Settings rehearsal in RAM)
- [ ] M: thermal DT: skin zone `pmh0101_skin_therm` (48/50/60 °C steps, 90 °C critical), XO zone (78/80 °C, 90 °C)
- [ ] M+PC: GPU trips confirmed against stock; GPU devfreq cooling tested (glmark2, 10 min)
- [ ] M+PC: BCL / low-battery protection (driver or a userspace guard); low-battery load test, no brown-out
- [ ] PC: thermal load kits (CPU, GPU, combined, charging; 15 min each; skin ≤ 50 °C sustained)
- [ ] PC+U: charging safety: derating on battery/connector temperature, full-charge termination, dual-cell safety
      (until it passes: charge attended only, 80 % limit)
- [ ] U: decide single boot (4e) or dual boot (4-DB)
- [ ] U: if dual boot, choose the Android / Fedora (/ shared) partition sizes
- [ ] U: accept that Android's data is wiped once (both slots share userdata)
- [ ] U: pick when the first write happens

## P1 — The Fedora install path (Phase 4)
- [ ] PC+U: Y10: GNOME from `rootfs-gnome.tar.gz` in RAM, plus the user's 30 s touch/pen window
- [ ] M: `kernel-iceland` rpm spec + kernel-install plugin (DTB to ESP `dtb/qcom/…`, BLS `devicetree`)
- [ ] M: `iceland-device` rpm (UCM volume caps, late ath12k, BT address unit, libinput quirks, logind lid, sleep hooks,
      journald cap, `excludepkgs=kernel*`, `DEFAULTKERNEL`, upgrade banner off, fwupd UEFI off)
- [ ] M: dracut config (GPU and touch firmware in the initramfs); kernel command line / BLS options; `lsm=` with selinux
- [ ] M+PC: firmware into `/usr/lib/firmware/updates/` (extractor on the tablet + OTA for the `super` files), never uploaded
- [ ] M: local dnf repo for `kernel-iceland` updates
- [ ] PC: RAM rehearsal of the real Workstation 44 image with our packages (pid1 mode)
- [ ] PC: full app set in RAM (relay 008): Files, Software + Flathub, Settings, Firefox, Extensions, Tweaks, OSK
- [ ] PC: build the install image (packages added, `/.autorelabel`, sparse via `img2simg`)
- [ ] U+PC: before writes: file-level `/data/vendor` + persist copy; GPT backup; confirm the 151-partition backup
- [ ] U (4-DB only): repartition LUN 0 (shrink `userdata`, add `fedora` [+ `shared`]) with the guarded partitioner; `fastboot -w`
- [ ] U: write Fedora (ABL `fastboot flash userdata`, or a guarded `dd` into `fedora`)
- [ ] U: boot tethered (U-Boot from the PC) → GNOME first boot → updates → a reboot loop
- [ ] U: place U-Boot: `recovery_<slot>` (dual boot) or the current slot's `boot` (single boot); test rollback once
- [ ] M: U-Boot env for dual boot (`fedora_blkmap` by partition name)

## P2 — Everyday use
- [ ] PC: suspend kit pc-025 (s2idle + RTC wake)
- [ ] M+PC: prove deep sleep (`qcom_stats` AOSS/CX/DDR counters); find what blocks it (remoteprocs, USB, PCIe/Wi-Fi)
- [ ] M+PC: resume of every device (panel + KTZ8869 re-program, touch firmware re-download, USB, Wi-Fi, BT, GPU)
- [ ] M+PC: wake sources: power key, lid open, pogo keyboard (TLMM151), RTC, charger
- [ ] PC: 20/20 suspend cycles; 8 h overnight drain ≤ ~1 %/h (compared with stock)
- [ ] M: speakers DT link to PRIMARY_TDM_RX_0 (8 × 32 bit TFA9865 slots)
- [ ] PC: Audio IF (TDM) subgraph m4 for the topology
- [ ] M+PC: volume caps + UCM, then TFA9865 speaker protection (`tfa98xx.cnt`), headset, mics
- [ ] M: nt36536 pen: report ABS resolution + stylus buttons (libinput accepts the pen)
- [ ] PC+U: confirm touch and pen events; lid closing (debounce 0034)
- [ ] PC: Wi-Fi under NetworkManager; 5/6 GHz with an AP in range (U); regulatory domain
- [ ] M+PC: BT address from wlan0's MAC at boot (confirm stock's rule); pairing under GNOME
- [ ] M: restore the Type-C graph in the DT (UCSI → dwc3 role switch, QMP combo, WCD939x mux)
- [ ] M+PC: OTG enable (the OnePlus glink message); host mode; host + charging via a PD hub; reverse charging (U plugs in)
- [ ] M+PC: DisplayPort alt mode
- [ ] PC+U: charging measurements per charger (SDP, DCP, PD, PPS, SuperVOOC brick); charge limit in GNOME (UPower)
- [ ] M+PC: system power: EAS energy model, cpuidle usage, GPU idle, 60 Hz on battery / 120–144 Hz on AC, CDSP off,
      Wi-Fi power save, BT autosuspend, UFS runtime PM/auto-hibern8, dwc3 runtime suspend, power-profiles-daemon
- [ ] PC: power measurements vs stock (idle screen-on, video, web, radios idle; target within ~20 %)
- [ ] PC: map `super` for the extractor; firmware refreshed from the current slot at boot (dual boot + OTAs)
- [ ] M: after an Android OTA (dual boot), a helper to re-flash U-Boot into the new slot's recovery

## P3 — Later / optional
- [ ] Sensors + auto-rotate (SSC via hexagonrpcd + libssc + iio-sensor-proxy)
- [ ] Hardware video decode (Iris, `vpu40_2v.mbn`)
- [ ] Pogo keyboard (the `tinno,pogo_keyboard` UART protocol, `POGOPIN_KB.bin`)
- [ ] Pen charging (MT5806 driver + PMIH010x hboost + pen glink messages)
- [ ] GPU: turnip/Vulkan when Mesa lands the a840; GPU cooling cells
- [ ] Kernel loose ends: SoundWire port-count warnings, pstore across the PS_HOLD reset, qnoc sync_state (simpledrm fallback)
- [ ] Suspend-then-hibernate (swap ≥ 12 GB)
- [ ] Cameras: SC1320CS / SC820CS drivers, CAMSS, `CAMERA_ICP`, libcamera
- [ ] PPS fast charging via the SC8547D charge pumps (optional; UFCS/SuperVOOC out of scope)
- [ ] Upstreaming (0025/0026/0028/0035, Pad 4 DTS, KTZ8869, TFA9865, U-Boot board): only with the user's OK
- [ ] Other distros (Phase 7): Arch ARM, pmOS, Debian testing, Kali, latest Ubuntu

## Housekeeping
- [ ] PC: keep KNOWLEDGE §13 in sync with PLAN v4 phase names (asked in relay 004)
- [ ] M: refresh the cloud kernel tree from `prepare.sh` before the next cloud build (it lags the queue)

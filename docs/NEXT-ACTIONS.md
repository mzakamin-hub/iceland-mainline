# Next actions (PC session, from 2026-09-29 evening)

**Working order from the user (2026-09-30 morning), after "queue them" (0054-0057 queued, iceland-linux 42c348b):**
tablet runs in this order: (1) ✅ refresh rate (0058, area-display-7), (2) ✅ GNOME pink/blocky glitches (0060, area-display-8/-9), (3) ✅ sensors (auto-rotate, accelerometer; RAM, area-sensors-1..7),
(4) GPU correctness, (5) hardware acceleration, (6) NPU (Hexagon); in parallel, prepared offline and given tablet slots
when ready: the mic noise, Wi-Fi 5 GHz / regulatory, the cameras. Battery and thermal protection are done
(area-thermal-1/-2). Runs stay automated and <= 10 min; the PC's webcam judges the screen during runs (the user's OK).
RAM boot only.

The PC session owns the project (relay 020).

Sources:
- **Status:** `docs/features/features-data.py` (the matrix; each open row has a where-to-look pointer).
- **Plan:** relay 019 (areas and exit criteria).
- **Evidence:** `docs/research/offline-prep/*.md`. These are cited claims, checked before use.

Each kit tests one area and may carry short side checks. It is judged from logs, and asks the user only for what
needs a person (eyes, hands, chargers). This file lists the concrete next step for every item that isn't working
yet, in the order they'll be done.

**Rules for every step:**
- RAM boot only.
- No firmware or identifiers in git.
- Stock values only (rule 13).
- Charge only while watched until the Power area closes.
- Boot & platform only after the user's go-ahead.

## Campaign 2 (1 Oct 2026): one combined step until green

Running history: `docs/WORKLOG.md`; results: `relay/results/area-campaign2.md`.

| Item | State | Next |
|---|---|---|
| Microphone meter | ✅ fixed: kit UCM overlay (the RAM image was stale) + `TX_DEC` 96 in the UCM (matches stock's level) | the user's look at the meter |
| NPU (CDSP) | ✅ boots from stock firmware, FastRPC unsigned PD tests pass, `libQnnHtpV81Skel.so` loads | HAP_mmap DMA handle (0x4e); QNN SDK (user); packaging |
| Encoder round trip | ✅ BT.709 input; BT.601 = GStreamer colorimetry list | patched v4l2 plugin test |
| 10-bit VP9 | open: same GStreamer cause (`bt2020-10` not in the probed list) | patched v4l2 plugin test |
| Browser on Iris | Firefox: no `h264_v4l2m2m` in Fedora's ffmpeg-free | GNOME Web test |
| Wi-Fi 5 GHz | open: regdb + country no change, hw-mode candidate at first load no change | reload vs first load; dual-MAC scan config |
| USB fix idle cost | first number: WFI 100 %, no deeper state with a data cable | A/B kernel, busy-only vote like stock |
| Camera | CAMSS probes with DT v2 (CSI-2 PHY nodes); sensors blocked by the reset pins' pinconf | pad type registers, then chip IDs + frames |

## 0. Charging safety: first, before any further kit

Every kit so far booted the OnePlus 15 charger policy: 3 A input, 4 A charge current, 12 V then 9 V PD request.
The PC port was asked for 1.2–1.9 A (stock SDP: 500 mA), and 12 V is above the stock VBUS OV of 11 V.

| Step | What | Where |
|---|---|---|
| 0.1 | Rework the relay 015 battmgr candidate into queue **0053** with the offline-review fixes (list below) | `relay/requests/015/`, `offline-prep/power.md` A6–A9, B3–B5, B12 |
| 0.2 | Build q18 = queue + 0053 and check it compiles clean | build-q18.sh |
| 0.3 | Unattended checks on the PC's USB port (SDP), in the next kit (list below) | power.md T1/T4 |
| 0.4 | ✅ 0053 queued 2026-09-29 (iceland-linux d36c1be, QUEUE-VERIFIED). Next: PD/DCP charger tests with the user watching (T2/T3/T4) | Power area |
| 0.5 | Battery guard fixes (list below), with unit tests | `packaging/iceland-device/files/iceland-battery-guard`, `tests/test_battery_guard.py` |

**0.1: the fixes to the candidate:**
- read the charger type through USB_ADAP_TYPE (7) with the driver's own mapping;
- fail low (1.5 A) when VBUS can't be read after the 9 V request;
- reject 0 for `constant_charge_current_max`;
- re-send the inhibit on every attach;
- Apple brick → the "unknown" limits;
- warn when a firmware write fails;
- log the type and limits chosen.

**0.3: what the unattended checks look for on the PC port:**
- `usb_type` SDP, `input_current_limit` 500000, USB current ≤ 550 mA;
- `inhibit-charge` gives battery current ≤ 0 within 10 s, and `auto` resumes;
- `constant_charge_current_max` lowers the current, which settles the unit question;
- writing 0 is refused.

**0.5: the guard fixes:**
- keep the state only after a write succeeds (retry otherwise);
- stop charging when the voltage can't be read;
- stop when VBUS is above 11 V;
- stop on a fast temperature rise (≥ 3 °C between samples);
- log once at startup which inputs are missing.

## 1. Display & input (area-display-2)

| Item | Next action | Needs the user |
|---|---|---|
| Black screen after a live refresh-rate change | ✅ **Fixed: queue 0058** (iceland-linux 1b63d1e): no CTL_START in the video encoder's cleanup. area-display-7 (webcam): 11 of 11 live changes across 144/120/60 Hz keep the picture, two after an s2idle, no underruns; iceland-device 0.12 turns the relight off by default. Long term: seamless DFPS | none |
| 120/60 Hz black | Every rate displays fine after an off/on; covered by the relight above | — |
| Pink glitches | ✅ **Fixed: queue 0060** (iceland-linux caac5c9): the splash take-over's MDSS reset + immediate UBWC setup (skipped while the block still read 0) left UBWC_STATIC 0x0e (bank bit 13) until the first MDSS power cycle. area-display-8 caught it with dumps; area-display-9 logged the race and 0x103e/5/1 after the fix, no glitch. Watch the first login of later boots | none (webcam) |
| Screenshot path | `gnome-screenshot` fails on GNOME 50 Wayland: use the Shell's D-Bus Screenshot through an allowed caller, or `xdg-desktop-portal` + `grim`-like capture | none |
| Pen | libinput recheck with a charged pen (tip, hover, buttons, pressure) | Charge the pen, draw |
| Backlight curve | Compare our brightness range/default with stock (panel dtsi `qcom,mdss-dsi-bl-*`, LineageOS overlay) (relay 013 item 4) | none |
| Pogo keyboard | Research: OnePlusOSS pogo driver (serdev + HID bridge); after the display fixes | later |
| Auto-rotate | Waits for the sensors (section 7) | — |

## 2. Graphics & compute (area-graphics)

| Item | Next action |
|---|---|
| GPU performance | ✅ area-graphics-1 (2026-09-29): DCVS already at 1.2 GHz under load (pinning +0 %), the stock 1100 MHz level works (DTS candidate on `gpu-tune`, in q21), autotune beats forced sysmem/gmem. Left: the heat ceiling (103 °C at 1.2 GHz in a minute → Thermal) |
| GPU correctness | ✅ area-graphics-2/-3 (2026-09-30): dEQP Vulkan 34 650 cases / 2 Fail, GLES 34 950 / 53 Fail (texture formats, ASTC, copy_image), WebGL 196 conformance pages / 3 failing, stress 0 faults, 0 GPU faults anywhere: the kernel side is clean, the failures read as Mesa gaps for the Adreno 8xx. Left: a single-worker rerun of the failures (flake vs deterministic); reports upstream only with the user's OK |
| Mesa main slower than 26.2.3 | ✅ Re-measured cooled, same session: −6.7 % GL / −1.1 % Vulkan. 26.2.3 stays; nothing to report upstream (the display-1 −42 % was heat/order) |
| CPU scaling / GNOME power modes | Capacity data (stock 1792/1894 DMIPS/MHz, coefficients 238/588) on branch `dcvs` (q21); iceland-device 0.10 tuned profiles behind tuned-ppd (see `docs/research/dcvs-tuning.md`); verified by area-power-1 → queue both DTS candidates |
| Video decode (Iris) | ✅ **Done** (queue 0062 + iceland-linux 92047dc `CONFIG_DMABUF_DEBUG=n`): bit-exact vs the AOSP VTS reference MD5s (H.264 High 240/240, HEVC 300/300, VP9 300/300, AV1 167/167); 4K H.264 450 fps / VP9 308 fps; playbin3 + Showtime pick Iris (1080p H.264 3 % vs 47 % CPU). The green picture: DMABUF_DEBUG strips importers' sg pages, msm maps from them (debug kernel q37d, area-video-4). Left: 10-bit VP9 negotiation, Firefox (Fedora FFmpeg lacks V4L2-M2M), GStreamer colorimetry 2:4:5:4 vs Iris-encoded VUI 6/1/6 (upstream later) |
| NPU (CDSP) | Stop disabling the CDSP in the kit's debug DTB (`tools/linux-ram/build.sh:69`), fix the firmware name (`cdsp.mbn` vs split `.mdt`), fix the `iceland-npu-off.service` ExecStart path, then boot the CDSP + FastRPC test (relay 012 C) |

## 3. Power & charging (after 0.x)

| Item | Next action | Needs the user |
|---|---|---|
| Charger tests | power.md T2–T6: DCP, PD (9 V decision, never 12 V), knobs, guard dry-run then live, firmware termination under load | Plug chargers, watch |
| Charge limit 85 % | ✅ guard-side limit works (area-thermal-2: +292 -> -7 mA); the SoCCP ignores opcode 0x48 (area-thermal-1). Next: a kernel software limit behind `charge_control_*` so GNOME's switch appears | none |
| Battery estimate | Report STATUS from the firmware (not forced Charging); CHARGE_NOW = capacity × charge_full; debug-kernel probe of TTE/TTF/POWER_AVG and the gauge words (power.md A2–A4, C2) | none |
| BCL | Stock PMH0101/PMIH010x BCL nodes → qcom-bcl/spmi bcl (relay 018 item 6) | none |
| Pen charging | Research the pen wireless-charge IC (odm `mt5806_firmware.bin`) and its stock driver | later |

## 4. Thermal

| Item | Next action |
|---|---|
| Skin/XO zones | ✅ branch `protect` (area-thermal-1/-2): skin 48 C loop to stock's deepest gear, 51 C gear, 70 C critical; XO stock steps. Queue with the GPU levels + CPU capacity on "queue them". Open: the start point (48 C vs stock's 50/60 C trips) after a hand-on-the-back check under load |
| USB-C connector zones | ✅ usb-therm + stock's L/R pair (ratiometric) read plausibly; check their rise under PD charging (with the charger tests) |
| GPU cooling | The skin loop caps the GPU under sustained load (area-graphics-2/-3: GPU 74-79 °C, 54-60 s throttled in 90 s); left: 125 °C critical → hot, a 30-min stress with the skin zone |

## 5. Sleep & power saving

| Item | Next action |
|---|---|
| s2idle stalls after audio, long-sleep reboot | Kit with the timer-sm8850 candidates (rpmh-rsc past-wakeup clamp, arch timer always-on) + ramoops (pc-026-s10-crashlog) + debug-hang config; one 5-min sleep with the watchdog on/off. PipeWire after resume |
| Wake by lid/keyboard/charger | `wakeup-source` on the lid gpio-key and pmic-glink/UCSI; check `/sys/power/pm_wakeup_irq` |
| 60 Hz on battery, CDSP off | Test the iceland-device units on battery (the 60/120 Hz switch now relights the panel, iceland-device 0.9). Also: ~300 mA more right after a display-on commit (the crtc's `bw_ctl` reads 0k then; area-display-3 §1) |
| Overnight drain | qcom_stats before/after, unplugged overnight; the user's OK for an unwatched night (the battery isn't charging) |

## 6. Connectivity

| Item | Next action | Needs the user |
|---|---|---|
| Wi-Fi 5/6 GHz | area-wifi-2/-3 (q30 DEBUG dbg_hw_mode, module reloads): 9-ch / 24-ch / full scans find a 5 GHz BSS in every DBS-or-SBS pass (4/4, the firmware's preferred of its only two modes 0 and 5), never in the boot-time DBS ath12k forces (0/2), DBS after a reload 2/2, single / SBS / none 0/3. Every load: the firmware rejects a country request, regulatory updates time out (3 s each), regulatory.db missing in the kit. Candidate `wififix` (preferred DBS-or-SBS) not queued. Next area-wifi-4: regdb + country, reg state per pass, boot-time A/B without reloads. `relay/results/area-wifi.md` | Wi-Fi password typed by the user (connect test only) |
| Bluetooth pairing | bluetoothctl + GNOME Settings with a device | A device to pair |
| USB host/OTG, DP alt mode | area-usb-1 (q31): DP controller + combo PHY + USB-SS switch bind, DP-1 connector present, 0 errors; accessory drivers all load on demand (uas not built); UCSI port0 roles + PD 3.0. Next: a host-mode kit (role switch kept, logs in RAM, webcam) for a slot with the user's accessories / monitor; enable CONFIG_USB_UAS. `relay/results/area-usb.md` | A hub / a monitor |

## 7. Sensors & camera

| Item | Next action |
|---|---|
| Sensors | ✅ **Working in RAM** (area-sensors-1..7): queue 0061 (ADSP FastRPC non-secure) + hexagonrpcd -s (local commit: /odm/etc/sensor) + libssc + iio-sensor-proxy 3.9 SSC (local commit: claims during discovery) + udev `81-iceland-ssc.rules` (ssc-accel ssc-proximity, ACCEL_MOUNT_MATRIX 0,1,0;-1,0,0;0,0,-1 from stock) + the private DSP tree (dsp, odm/etc/sensor, vendor sensors config, persist registry, stock socinfo values). Orientation "normal" as stock. Next: packaging (RPMs, unit, install-time extraction), the user's rotation check |
| Cameras | ✅ C0 done by the LineageOS trace (2026-09-30, `relay/results/area-camera.md`): SC1320CS 0x36 / SC820CS 0x10 / actuator 0x0c (7-bit), CSIPHY4/5 4-lane D-PHY at 1324.8 / 660 Mbps, stock power-up order and delays, every mode's register table (private, `build/camtrace/tables`), AE registers 0x3e00-02 / 0x3e07 / 0x3e09 / VTS 0x320e, black level 64 / 65, BGGR, actuator = DW9719 register map. Next: C1 DT nodes + C2 drivers (SC1320CS first), C3 first light on a RAM kit |

## 8. Software & packaging

| Item | Next action |
|---|---|
| About page | iceland-device `/etc/machine-info` (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); socinfo id 661 name in the kernel |
| iceland-device | Pin 144 Hz until 1.x is fixed; the npu-off path; the guard fixes (0.5) |
| Full GNOME app set, stock-values audit | Relay 008 list; relay 013 table |
| Mic hiss (known issue) | ✅ **Hiss fixed: queue 0059** (lpass-tx-macro: TX decimator ADPT block off on codec 2.8+, stock's no-tuning branch): floor -47 -> -63 dBFS, tone unchanged (area-audio-6/-7). Open: the first capture after boot ~5 dB higher; compare the spectrum with stock's recordings; optional stock tuning (0x41 + dtsi values, a DT binding) | GNOME meter look (optional) |
| Open candidates | area-audio-5 0001–0002 (tfa 0x62, TDM drive): one loopback side check, then 0054/0055 |

## 8b. Kit runs: the ~60 s freeze (2026-09-30)

| Item | Next action |
|---|---|
| Freeze ~60 s into Fedora | ✅ **Fixed, queued 0063** (iceland-linux ccdac5e): dwc3-qcom holds a 2 us CPU-latency request while active, as stock's dwc3-msm (`qcom,pm-qos-latency = <2>`). Cause: fast PC→tablet USB traffic (≥ ~15 MB/s) + CPU power collapse → SoC hang, hard reset (`relay/results/area-freeze.md`). area-freeze-7 with the kit QoS off: 4 × 696 MB at 36 MB/s, no power collapse, no freeze. Kits keep `USB_QOS=2` for older kernels. Left: idle power with a data cable plugged in; a busy-only vote (like stock's IRQ-rate sampling) if it costs too much |

## 9. Boot & platform (last, after the user's go-ahead)

| Item | Next action |
|---|---|
| Firmware extractor | Add the `super` step to `tools/linux-ram/fw-extract.sh`: LP metadata reader (as `build/an/lp-list.py`), read-only dm-linear or loop with offset, EROFS mounted read-only. Test on the PC against the user's partition backup (10/10 vendor/odm files match stock 11.A.38), then in a kit, read-only |
| Install + dual boot | `phase4/INSTALL-PLAN.md`, iceland-u-boot 0003; only with the user's OK |

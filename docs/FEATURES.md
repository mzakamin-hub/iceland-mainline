# OnePlus Pad 4 mainline: feature matrix

Status 30 Sep 2026 (area-display-7 done (webcam-judged): live refresh-rate changes fixed in the kernel (0058, 11 of 11); the pink glitch not reproduced this run; Linux sees the 5 GHz networks only in a 5 GHz-only scan; next (the user's order): the glitches, sensors, GPU correctness, HW acceleration, the NPU). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 37 working, 14 in progress, 18 not started, 2 not planned (71).

## Boot & platform (5/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| U-Boot booted from RAM (display, USB fastboot, UFS read, EFI) | ✅ Working | Nothing written to the tablet; fastboot flashing compiled out |  |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata |  |
| Linux 7.3-rc4 through EFI | ✅ Working | Queue 0001–0058 + infiniti |  |
| Fedora 44 running from RAM | ✅ Working | systemd as PID 1; packages through the PC |  |
| GNOME Shell 50 | ✅ Working | Autologin session in RAM |  |
| Firmware extractor (tablet's own partitions, read-only) | 🟡 In progress | modem/bluetooth work on the tablet; vendor/odm inside “super” proven offline from your partition backup (10 of 10 files match stock 11.A.38) | Add the LP-metadata reader (an/lp-list.py) + read-only EROFS mount to tools/linux-ram/fw-extract.sh; test against the backup on the PC, then in a kit |
| Fedora installed on the tablet | ⬜ Not started | Final step; needs your decisions and OK | Waits for your install decision (relay 019: Boot & platform last) |
| Dual boot with Android | ⬜ Not started | Planned; recovery re-flash helper ready | iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1 |

## Display & input (7/10 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |  |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | Fixed in the kernel (queue 0058): live rate changes keep the picture - 11 of 11 on the PC webcam across 144/120/60 Hz, two of them after a suspend, no underruns (area-display-7). The cause was a CTL_START the display driver wrote after switching the video engine off; the display off/on workaround in iceland-device is now off by default (0.12) | Long term: stock-style seamless rate switching (no modeset) |
| Backlight | ✅ Working | Brightness curve still being checked against stock |  |
| GNOME pink / blocky glitches | 🟡 In progress | Intermittent: filmed by you (whole wallpaper, 00:19) and caught once by the PC webcam (run 4: the overview right after login, pink/blue checker edges and blocky dash icons, gone after a display off/on); 0 of 48 frames in run 7 (the overview after login, 4 off/on cycles, 11 rate changes, a resume); no kernel error; DRAM bank bit ruled out | A long repeat run on the overview (many enables and session restarts) with a register dump at every state, then GNOME with FD_MESA_DEBUG=noubwc as the A/B |
| Touchscreen | ✅ Working | Confirmed by you; keeps working through display off/on cycles and suspend (area-display-2) |  |
| Pen | ✅ Working | Working per your call; not tested enough yet (area-display-1 logged 0 pen events, pen maybe not charged) | Charged pen: tip, hover, buttons, pressure in libinput debug-events; palm rejection |
| Lid switch | ✅ Working | SW_LID events on GPIO 98 (area-display-1) |  |
| Power and volume keys | ✅ Working | Power key also wakes from sleep |  |
| Pogo keyboard | ⬜ Not started | Private UART protocol | Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge |
| Auto-rotate | ⬜ Not started | Needs the sensors | SSC sensors: hexagonrpcd + libssc + iio-sensor-proxy, persist registry |

## Graphics & compute (3/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | OpenGL 4.6 / ES 3.2 on Mesa 26.2.3 (Fedora 44's newest; Mesa main is 7 % slower here); glmark2 3213 offscreen / 2345 on GNOME, DCVS already at 1.2 GHz under load; the stock 1100 MHz level added (area-graphics-1) |  |
| GNOME and Wayland drawn by the GPU | ✅ Working |  |  |
| GPU correctness, WebGL, stress | 🟡 In progress | 60-s stress steady at 394 fps, 0 faults, but 103 °C at 1.2 GHz within a minute (area-graphics-1) | dEQP subset, WebGL in a browser; the heat ceiling belongs to Thermal (GPU trips, skin zone) |
| Vulkan | ✅ Working | turnip 26.2.3: Vulkan 1.4; vkmark 19563 headless 1080p (area-graphics-1), 24562 fullscreen (display-1) |  |
| Hardware video decoding | ⬜ Not started | Driver in the tree; firmware known | Iris node disabled and no &iris override in the iceland DTS; set firmware-name vpu40_2v.mbn (driver default vpu40_p2 = ENOENT); CONFIG_VIDEO_QCOM_IRIS; gst v4l2h264dec, CPU time |
| NPU (Hexagon on the CDSP) | ⬜ Not started | Off by default; bring-up in relay 012 | CDSP disabled in every kit's debug DTB (build.sh:69); cdsp.mbn vs split .mdt names; iceland-npu-off.service ExecStart path wrong; fastrpc + quic/fastrpc unsigned PD test |

## Audio (6/9 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| DSP audio + sound card | ✅ Working |  |  |
| GNOME shows speakers and microphones | ✅ Working | Fixed: stray mixer route; appears on a fresh boot |  |
| Microphones (2) | 🟡 In progress | Known issue: a steady hiss 25–35 dB above stock, so GNOME’s meter barely moves; speech gets through | Downstream WCD939x per-rate SoundWire TX port params vs wcd939x-sdw.c / lpass-tx-macro (relay 018 9b); HIFI mode broken too |
| Speakers (top pair) | ✅ Working | You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only |  |
| All six speakers in stereo | ✅ Working | You heard all six from GNOME’s Sound test, both sides correct |  |
| Speaker volume cap | ✅ Working | −12 dB cap enforced by the kernel (queued 0051); stock value still to find |  |
| GNOME volume bar and input slider | ✅ Working | Measured: follows GNOME’s curve within ~1 dB (area-display-1) |  |
| Speaker protection (NXP container) | ⬜ Not started | Closed firmware; volume stays capped | tfa98xx.cnt from odm; TFA DSP protocol (closed); volume stays capped |
| Headset over USB-C | ⬜ Not started | No 3.5 mm jack | WCD939x USBSS mux + UCSI/typec altmode audio accessory |

## Connectivity (4/7 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | Connected by you; GNOME showed “?” until NetworkManager re-checked (a fresh check says full internet) |  |
| Wi-Fi 5 / 6 GHz | 🟡 In progress | Your 5 GHz networks are there (Android sees 2 on channel 36) and Linux receives them when the scan is limited to 5 GHz (2 BSS on 5180 MHz, also passive) - but a full scan returns only the 2.4 GHz ones, so NetworkManager never offers them (area-display-7). Region US; the firmware refuses country changes | Scan band subsets with timing to find where the full scan drops 5 GHz (ath12k / WCN7860 firmware), then fix; a 5 GHz connect test needs your password |
| Bluetooth, own address | ✅ Working |  |  |
| Bluetooth pairing in GNOME | ✅ Working | Confirmed by you (29 Sep 2026) |  |
| USB device mode / USB network | ✅ Working |  |  |
| USB host / OTG, PD hub | ⬜ Not started |  | dwc3 role switch via pmic-glink UCSI; typec sysfs; dwc3 power_lost after resume |
| DisplayPort over USB-C | ⬜ Not started |  | qmp-combo PHY + DP controller from the infiniti series; DT enable + altmode |

## Power & charging (2/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | UPower and GNOME battery |  |
| Battery time estimate | 🟡 In progress | Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area | qcom_battmgr OPLUS: STATUS forced to Charging when USB is online; instantaneous 1 Hz current; gauge word 4 is not a charge; derive CHARGE_NOW = capacity × charge_full, probe TTE/TTF/POWER_AVG (offline-prep/power.md A2–A4) |
| Charging | 🟡 In progress | Stock limits patch 0053 queued (iceland-linux d36c1be): SDP input 500 mA (494 mA measured, was 1.2–1.9 A), knobs work | Chargers with you watching (power.md T2–T6: DCP, PD 9 V never 12 V, inhibit and FCC effects below 80 %) |
| Battery safety guard (stock limits) | ✅ Working | iceland-device 0.11 guard ran live on the tablet (area-thermal-1/-2): stock JEITA regions, voltages, currents, the three USB-C connector sensors (hottest valid reading), power-off at 70 °C (stock framework) / 77 °C; 70 simulated cases pass | PD/DCP charger tests with you watching (connector sensors under charging current) |
| Charge limit (85 %, your request) | 🟡 In progress | Works: iceland-battery-guard stops charging at 85 % and resumes at 80 % (/etc/iceland/battery-guard.conf); measured +292 → −7 mA (area-thermal-2). The charger firmware ignores its own limit request, so GNOME shows no switch yet | A kernel software limit (charge_control_* through the same charge inhibit) so GNOME's Preserve Battery Health switch appears |
| Low-battery current limiting (BCL) | ⬜ Not started |  | Stock PMH0101/PMIH010x BCL nodes (relay 018 item 6); qcom-bcl-hwmon / spmi bcl |
| Pen charging | ⬜ Not started | New driver needed | Pen wireless-charge IC on the pogo/magnet side: stock driver in OnePlusOSS |
| Fast charging (SuperVOOC / PPS) | ❌ Not planned | OnePlus-proprietary; not planned |  |

## Thermal (4/5 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| CPU frequencies and CPU limits (stock) | ✅ Working | Held at 105 °C under load |  |
| Board and flash thermistors | ✅ Working |  |  |
| Skin and XO zones | ✅ Working | Skin: throttles from 48 °C down to stock's deepest gear, the gear at once at 51 °C, off at 70 °C; XO: stock's 78/80/90 °C steps. Emulated and real load checked (area-thermal-1/-2). Under sustained all-core load the skin sensor (a fast hot spot) holds CPUs at ~1.3 GHz | Your choice: keep 48 °C or start at stock's 50/60 °C trip for more sustained speed (a hand-on-the-back check); queue with the other DTS candidates |
| USB-C connector temperature zones | ✅ Working | usb-therm + stock's L/R connector pair (ratiometric, high-Z pins as stock): 28.8 / 28.9 / 33.9 °C next to a 32.1 °C board; the guard reads all three (area-thermal-2) | Check the L/R rise under PD charging current (with you watching) |
| GPU cooling | 🟡 In progress | 105 °C passive map matches stock; the GPU reaches 95–103 °C at 1.2 GHz in under a minute of Vulkan/stress, 0 throttled seconds so far (area-graphics-1) | Turn the 125 °C critical into hot (stock has no GPU shutdown trip); a longer stress with the skin zone; sustained-load throttling behaviour |

## Sleep & power saving (1/7 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Suspend (s2idle) | 🟡 In progress | 24 cycles clean; two stalls after audio activity under investigation | Stalls after audio: timer-sm8850 candidates (rpmh-rsc past-wakeup clamp, arch timer always-on); ramoops + debug-hang kernel |
| Long sleep | 🟡 In progress | One unexplained reboot after a long sleep: watchdog vs planned reboot | Reset = PSHOLD/SYSOK: watchdog vs power key; ramoops (pc-026-s10-crashlog) + one 5-min sleep with watchdog on/off |
| Wake by power key and alarm | ✅ Working |  |  |
| Wake by lid, keyboard, charger | ⬜ Not started |  | wakeup-source on gpio-keys lid, pmic-glink/UCSI; /sys/power/pm_wakeup_irq |
| 60 Hz on battery, CDSP off | 🟡 In progress | In iceland-device 0.4+; untested on the tablet | iceland-device refresh + npu-off units (fix the npu-off ExecStart path) |
| CPU scaling and GNOME power modes | 🟡 In progress | Stock CPU capacity data (1792/1894 DMIPS/MHz) and iceland-device 0.10 tuned profiles for GNOME's power modes written; area-power-1 verification pending | Queue the two DTS candidates (GPU levels, CPU capacity); then Thermal |
| Deep-sleep proof, overnight drain ≤ ~1 %/h | ⬜ Not started |  | qcom_stats before/after, rpmh-stats; overnight unplugged |

## Sensors & camera (1/4 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Rear flash LEDs | ✅ Working |  |  |
| Accelerometer, compass, light / proximity | ⬜ Not started |  | hexagonrpcd sensorspd + libssc (adsp_listener_get_in_bufs2 patch), persist registry |
| Cameras (13 MP rear, 8 MP front) | ⬜ Not started | Plan written; stock supplies, clock and resets resolved; waiting for register data | CAMSS/CCI from infiniti; relay 014 register data; research/camera-bringup.md §1b supplies/MCLK/resets |
| Haptics, modem, NFC, fingerprint | ❌ Not planned | Not on this tablet |  |

## Software & packaging (4/7 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Test-built: 948 modules, device tree, install hooks |  |
| Device package (iceland-device 0.12) | ✅ Working | Settings, battery guard 0.11 (70 °C, USB-C L/R, 85 % limit), sound, Wi-Fi region, 60/120 Hz by power source (relight off: kernel 0058 fixes rate changes), GNOME power modes; built |  |
| Local update repository | ✅ Working | Checksum-verified sync; tested |  |
| Full GNOME app set | ⬜ Not started | Relay 008 | Relay 008 package list in the RAM rootfs |
| Stock-values audit | ⬜ Not started | Relay 013 | Relay 013 table; offline-prep/*.md stock comparisons |
| GNOME About page (model, processor) | 🟡 In progress | Shows “oneplus OnePlus Pad 4” and no processor | iceland-device /etc/machine-info (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); no CPU model name in cpuinfo/lscpu: socinfo id 661 name, util-linux part 0x51/0x002 |
| Automated PC fix loop | ✅ Working | The PC session runs everything (cloud debugger handed over, relay 020) |  |

# OnePlus Pad 4 mainline: feature matrix

Status 29 Sep 2026 (area-graphics-1 and area-power-1 done (automated, under 10 min each): GPU DCVS already at the top under load, the stock 1100 MHz level and CPU capacity data added, GNOME power modes now drive Pad 4 tuned profiles; next (the user's order): battery + thermal protection, the mic, Wi-Fi, the cameras). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 33 working, 17 in progress, 19 not started, 2 not planned (71).

## Boot & platform (5/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| U-Boot booted from RAM (display, USB fastboot, UFS read, EFI) | ✅ Working | Nothing written to the tablet; fastboot flashing compiled out |  |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata |  |
| Linux 7.3-rc4 through EFI | ✅ Working | Queue 0001–0052 + infiniti |  |
| Fedora 44 running from RAM | ✅ Working | systemd as PID 1; packages through the PC |  |
| GNOME Shell 50 | ✅ Working | Autologin session in RAM |  |
| Firmware extractor (tablet's own partitions, read-only) | 🟡 In progress | modem/bluetooth work on the tablet; vendor/odm inside “super” proven offline from your partition backup (10 of 10 files match stock 11.A.38) | Add the LP-metadata reader (an/lp-list.py) + read-only EROFS mount to tools/linux-ram/fw-extract.sh; test against the backup on the PC, then in a kit |
| Fedora installed on the tablet | ⬜ Not started | Final step; needs your decisions and OK | Waits for your install decision (relay 019: Boot & platform last) |
| Dual boot with Android | ⬜ Not started | Planned; recovery re-flash helper ready | iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1 |

## Display & input (6/10 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |  |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | 🟡 In progress | Every rate works; a live rate change blanks the panel, and iceland-device 0.9 now switches the display off/on once after every change (tested live: one relight per change, also for the 60/120 Hz power-source switch); the panel and backlight read normal in the black state, so logs can't judge it (area-display-3) | Your 1-minute look (deferred): a rate change with the relight, and one with candidate 0054 (stock power sequence) alone; root cause in the msm single-commit modeset; long term stock-style seamless DFPS |
| Backlight | ✅ Working | Brightness curve still being checked against stock |  |
| GNOME pink / blocky glitches | 🟡 In progress | Back: you filmed the whole wallpaper speckled pink/cyan at 00:19 (area-power-1, kernel q21); no kernel error logged; DRAM bank bit ruled out (LPDDR5X = bit 16, as stock) | Log the DPU's UBWC decode-error status every frame in each kit; then GNOME with FD_MESA_DEBUG=noubwc as the A/B |
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
| Wi-Fi 5 / 6 GHz | 🟡 In progress | Region US; 5 GHz (28 ch) and 6 GHz (60 ch) enabled, but no 5/6 GHz network is visible where the tablet was tested: your router shows up only on 2.4 GHz (ch 1), so the connection you made was 2.4 GHz (area-display-3 scan) | Test near a 5 GHz AP (router 5 GHz radio, or a phone hotspot on 5 GHz); iw reg get (US), ath12k board-2.bin match |
| Bluetooth, own address | ✅ Working |  |  |
| Bluetooth pairing in GNOME | ✅ Working | Confirmed by you (29 Sep 2026) |  |
| USB device mode / USB network | ✅ Working |  |  |
| USB host / OTG, PD hub | ⬜ Not started |  | dwc3 role switch via pmic-glink UCSI; typec sysfs; dwc3 power_lost after resume |
| DisplayPort over USB-C | ⬜ Not started |  | qmp-combo PHY + DP controller from the infiniti series; DT enable + altmode |

## Power & charging (1/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | UPower and GNOME battery |  |
| Battery time estimate | 🟡 In progress | Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area | qcom_battmgr OPLUS: STATUS forced to Charging when USB is online; instantaneous 1 Hz current; gauge word 4 is not a charge; derive CHARGE_NOW = capacity × charge_full, probe TTE/TTF/POWER_AVG (offline-prep/power.md A2–A4) |
| Charging | 🟡 In progress | Stock limits patch 0053 queued (iceland-linux d36c1be): SDP input 500 mA (494 mA measured, was 1.2–1.9 A), knobs work | Chargers with you watching (power.md T2–T6: DCP, PD 9 V never 12 V, inhibit and FCC effects below 80 %) |
| Battery safety guard (stock limits) | 🟡 In progress | Review fixes in (iceland-device 0.8: retries, VBUS > 11 V, rise-fast, unreadable voltage); 47 simulated cases pass; tablet test pending | Tablet test with 0053's charge_behaviour / constant_charge_current_max (power.md T5) |
| Charge limit (85 %, your request) | ⬜ Not started | battmgr OnePlus variant exposes no charge_control_* files | Add the thresholds + setter to the OPLUS battmgr props; check the SoCCP honours opcode 0x48; UPower limit in iceland-device |
| Low-battery current limiting (BCL) | ⬜ Not started |  | Stock PMH0101/PMIH010x BCL nodes (relay 018 item 6); qcom-bcl-hwmon / spmi bcl |
| Pen charging | ⬜ Not started | New driver needed | Pen wireless-charge IC on the pogo/magnet side: stock driver in OnePlusOSS |
| Fast charging (SuperVOOC / PPS) | ❌ Not planned | OnePlus-proprietary; not planned |  |

## Thermal (2/5 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| CPU frequencies and CPU limits (stock) | ✅ Working | Held at 105 °C under load |  |
| Board and flash thermistors | ✅ Working |  |  |
| Skin and XO zones | 🟡 In progress | Patch ready; skin limits to be replaced by stock values | Relay 009 candidate; stock skin gear table (relay 018 item 7) for the caps |
| USB-C connector temperature zone | 🟡 In progress | Patch ready (57 °C, stock) | Candidate reads 0x2747 but stock usbtemp uses AMUX1/AMUX5 (0x274a/0x275e); needs relay 009 first to apply (power.md A12/B6/B7) |
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
| Device package (iceland-device 0.9) | ✅ Working | Settings, battery guard 0.8, sound, Wi-Fi region, 60/120 Hz by power source with the panel relight; built |  |
| Local update repository | ✅ Working | Checksum-verified sync; tested |  |
| Full GNOME app set | ⬜ Not started | Relay 008 | Relay 008 package list in the RAM rootfs |
| Stock-values audit | ⬜ Not started | Relay 013 | Relay 013 table; offline-prep/*.md stock comparisons |
| GNOME About page (model, processor) | 🟡 In progress | Shows “oneplus OnePlus Pad 4” and no processor | iceland-device /etc/machine-info (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); no CPU model name in cpuinfo/lscpu: socinfo id 661 name, util-linux part 0x51/0x002 |
| Automated PC fix loop | ✅ Working | The PC session runs everything (cloud debugger handed over, relay 020) |  |

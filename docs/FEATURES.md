# OnePlus Pad 4 mainline: feature matrix

Status 29 Sep 2026 (after the audio area closed (mic hiss a known issue) and the touchscreen confirmed by you; each open item has a where-to-look pointer; area-by-area campaign, relay 019; next: the display glitches and screen, then GPU and NPU). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 29 working, 15 in progress, 22 not started, 2 not planned (68).

## Boot & platform (5/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| U-Boot booted from RAM (display, USB fastboot, UFS read, EFI) | ✅ Working | Nothing written to the tablet; fastboot flashing compiled out |  |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata |  |
| Linux 7.3-rc4 through EFI | ✅ Working | Queue 0001–0045 + infiniti |  |
| Fedora 44 running from RAM | ✅ Working | systemd as PID 1; packages through the PC |  |
| GNOME Shell 50 | ✅ Working | Autologin session in RAM |  |
| Firmware extractor (tablet's own partitions, read-only) | 🟡 In progress | vendor/odm inside “super” not mapped yet | Map vendor/odm inside “super” (lpunpack/lpdump metadata); pc-023/024 extractor, 11 files skipped |
| Fedora installed on the tablet | ⬜ Not started | Final step; needs your decisions and OK | Waits for your install decision (relay 019: Boot & platform last) |
| Dual boot with Android | ⬜ Not started | Planned; recovery re-flash helper ready | iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1 |

## Display & input (5/10 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |  |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | 144 Hz after the DPU clock fix |  |
| Backlight | ✅ Working | Brightness curve still being checked against stock |  |
| GNOME pink / blocky glitches | 🟡 In progress | Isolation plan sent (relay 011); Mesa side checked; first display run next | GNOME scans out a 10-bit XR30 UBWC buffer, the clean console is 8-bit linear XR24 (drm state dumps): dpu_hw_sspp.c UBWC ≥ 5.0 DX-format bits vs a8xx rgba8888_lossless; the SSPP UBWC error registers; FD_MESA_DEBUG=noubwc / notile; panel DSC 1.2 + stock 0x91/0x92 init bytes (offline-prep/display.md) |
| Touchscreen | ✅ Working | Confirmed by you: GNOME used by touch during the audio runs |  |
| Pen | 🟡 In progress | GNOME accepts it; strokes not confirmed | Driver 0036 (tablet caps); check libinput debug-events strokes/pressure; palm rejection |
| Lid switch | 🟡 In progress | Closing not tested | DT gpio-key TLMM 98 (0030); evtest SW_LID + logind HandleLidSwitch |
| Power and volume keys | ✅ Working | Power key also wakes from sleep |  |
| Pogo keyboard | ⬜ Not started | Private UART protocol | Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge |
| Auto-rotate | ⬜ Not started | Needs the sensors | SSC sensors: hexagonrpcd + libssc + iio-sensor-proxy, persist registry |

## Graphics & compute (2/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | kmscube 120 fps, glmark2 1836 |  |
| GNOME and Wayland drawn by the GPU | ✅ Working |  |  |
| GPU correctness, WebGL, 30-min stress | ⬜ Not started | Relay 012 | Run on the stock gen80200 firmware set (kits use linux-firmware's); missing stock 1100 MHz OPP; dEQP/piglit availability (offline-prep/graphics.md A2/A7/A11) |
| Vulkan | ⬜ Not started | Mesa 26.2.3 has turnip for the Adreno 840; vulkaninfo/vkcube check in the display run | Mesa 26.2.3 turnip; vulkaninfo/vkcube/vkmark |
| Hardware video decoding | ⬜ Not started | Driver in the tree; firmware known | Iris node disabled and no &iris override in the iceland DTS; set firmware-name vpu40_2v.mbn (driver default vpu40_p2 = ENOENT); CONFIG_VIDEO_QCOM_IRIS; gst v4l2h264dec, CPU time |
| NPU (Hexagon on the CDSP) | ⬜ Not started | Off by default; bring-up in relay 012 | CDSP disabled in every kit's debug DTB (build.sh:69); cdsp.mbn vs split .mdt names; iceland-npu-off.service ExecStart path wrong; fastrpc + quic/fastrpc unsigned PD test |

## Audio (5/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| DSP audio + sound card | ✅ Working |  |  |
| GNOME shows speakers and microphones | ✅ Working | Fixed: stray mixer route; appears on a fresh boot |  |
| Microphones (2) | 🟡 In progress | Known issue: a steady hiss 25–35 dB above stock, so GNOME’s meter barely moves; speech gets through | Downstream WCD939x per-rate SoundWire TX port params vs wcd939x-sdw.c / lpass-tx-macro (relay 018 9b); HIFI mode broken too |
| Speakers (top pair) | ✅ Working | You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only |  |
| All six speakers in stereo | ✅ Working | You heard all six from GNOME’s Sound test, both sides correct |  |
| Speaker volume cap | ✅ Working | −12 dB cap enforced by the kernel (queued 0051); stock value still to find |  |
| Speaker protection (NXP container) | ⬜ Not started | Closed firmware; volume stays capped | tfa98xx.cnt from odm; TFA DSP protocol (closed); volume stays capped |
| Headset over USB-C | ⬜ Not started | No 3.5 mm jack | WCD939x USBSS mux + UCSI/typec altmode audio accessory |

## Connectivity (3/7 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | NetworkManager, scan, connect |  |
| Wi-Fi 5 / 6 GHz | 🟡 In progress | Region US (your choice); bands enabled, no 5/6 GHz network tested yet | Test on a 5/6 GHz AP; iw reg get (US), ath12k board-2.bin match |
| Bluetooth, own address | ✅ Working |  |  |
| Bluetooth pairing in GNOME | ⬜ Not started |  | bluetoothctl + GNOME Settings; hci_qca firmware gngbt |
| USB device mode / USB network | ✅ Working |  |  |
| USB host / OTG, PD hub | ⬜ Not started |  | dwc3 role switch via pmic-glink UCSI; typec sysfs; dwc3 power_lost after resume |
| DisplayPort over USB-C | ⬜ Not started |  | qmp-combo PHY + DP controller from the infiniti series; DT enable + altmode |

## Power & charging (1/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | UPower and GNOME battery |  |
| Battery time estimate | 🟡 In progress | Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area | qcom_battmgr OPLUS: STATUS forced to Charging when USB is online; instantaneous 1 Hz current; gauge word 4 is not a charge; derive CHARGE_NOW = capacity × charge_full, probe TTE/TTF/POWER_AVG (offline-prep/power.md A2–A4) |
| Charging | 🟡 In progress | Works; Pad 4 stock charger limits patch (9 V / 1.5 A) awaiting test | Queue still has the OnePlus 15 policy (3 A input, 12 V PDO): 1.2–1.9 A seen on SDP vs stock 500 mA. Queue relay 015 first, fixing USB_ADAP_TYPE and the fail-low 9 V error path (power.md B1–B4, C7) |
| Battery safety guard (stock limits) | 🟡 In progress | Written and simulated (30 cases); tablet test pending | Retry failed writes (cache only on success); stop on unreadable voltage and VBUS > 11 V; rise-fast rule (power.md B8/B9/B11) |
| Charge limit (80 %) | ⬜ Not started |  | charge_behaviour inhibit via OPLUS_CHG_EN, re-sent on every attach (relay 015); upstream 0x48 charge-control support unknown |
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
| GPU cooling | 🟡 In progress | Load test pending | 105 °C devfreq map matches stock; turn the 125 °C critical into hot; 30-min stress log |

## Sleep & power saving (1/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Suspend (s2idle) | 🟡 In progress | 24 cycles clean; two stalls after audio activity under investigation | Stalls after audio: timer-sm8850 candidates (rpmh-rsc past-wakeup clamp, arch timer always-on); ramoops + debug-hang kernel |
| Long sleep | 🟡 In progress | One unexplained reboot after a long sleep: watchdog vs planned reboot | Reset = PSHOLD/SYSOK: watchdog vs power key; ramoops (pc-026-s10-crashlog) + one 5-min sleep with watchdog on/off |
| Wake by power key and alarm | ✅ Working |  |  |
| Wake by lid, keyboard, charger | ⬜ Not started |  | wakeup-source on gpio-keys lid, pmic-glink/UCSI; /sys/power/pm_wakeup_irq |
| 60 Hz on battery, CDSP off | 🟡 In progress | In iceland-device 0.4+; untested on the tablet | iceland-device refresh + npu-off units (fix the npu-off ExecStart path) |
| Deep-sleep proof, overnight drain ≤ ~1 %/h | ⬜ Not started |  | qcom_stats before/after, rpmh-stats; overnight unplugged |

## Sensors & camera (1/4 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Rear flash LEDs | ✅ Working |  |  |
| Accelerometer, compass, light / proximity | ⬜ Not started |  | hexagonrpcd sensorspd + libssc (adsp_listener_get_in_bufs2 patch), persist registry |
| Cameras (13 MP rear, 8 MP front) | ⬜ Not started | Plan written; stock supplies, clock and resets resolved; waiting for register data | CAMSS/CCI from infiniti; relay 014 register data; research/camera-bringup.md §1b supplies/MCLK/resets |
| Haptics, modem, NFC, fingerprint | ❌ Not planned | Not on this tablet |  |

## Software & packaging (4/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Test-built: 948 modules, device tree, install hooks |  |
| Device package (iceland-device 0.7) | ✅ Working | Settings, battery guard, sound, Wi-Fi region; built |  |
| Local update repository | ✅ Working | Checksum-verified sync; tested |  |
| Full GNOME app set | ⬜ Not started | Relay 008 | Relay 008 package list in the RAM rootfs |
| Stock-values audit | ⬜ Not started | Relay 013 | Relay 013 table; offline-prep/*.md stock comparisons |
| Automated PC fix loop + cloud debugger | ✅ Working |  |  |

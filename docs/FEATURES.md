# OnePlus Pad 4 mainline: feature matrix

Status 29 Sep 2026 (area-display-1 done (GPU + Vulkan accelerated, lid works; a panel power cycle blanks the screen and 120/60 Hz is broken); the project is now run by the PC session alone (relay 020); each open item has a where-to-look pointer; next: the charging-safety patch, then area-display-2 (touch/panel power-on order, 144 Hz only), then GPU and NPU). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 31 working, 16 in progress, 21 not started, 2 not planned (70).

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

## Display & input (5/10 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |  |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | 🟡 In progress | 144 Hz works; switching to 120 or 60 Hz turns the screen black (area-display-1) | panel-novatek-nt36536: stock per-mode rate commands (panel dtsi / LineageOS panel driver); until then offer only 144 Hz in iceland-device |
| Backlight | ✅ Working | Brightness curve still being checked against stock |  |
| GNOME pink / blocky glitches | 🟡 In progress | Not reproduced in area-display-1 (clean at 144 Hz, 0 underruns, UBWC scanout); watch for a return | If it returns: photo + drm state, XR30 vs XR24 compositor, FD_MESA_DEBUG=noubwc/notile, SSPP UBWC error registers; DSC 1.2 + stock 0x91/0x92 (offline-prep/display.md) |
| Touchscreen | ✅ Working | Confirmed by you; 20 700 events in area-display-1. Stops after a panel power cycle | nt36536 touch resume: bootloader reset + firmware download runs after the panel init; move it before the display init (stock notifier order) or skip the reset on resume |
| Pen | 🟡 In progress | 0 events in area-display-1 (pen maybe not charged); recheck | Driver 0036 (tablet caps); libinput debug-events with a charged pen; palm rejection |
| Lid switch | ✅ Working | SW_LID events on GPIO 98 (area-display-1) |  |
| Power and volume keys | ✅ Working | Power key also wakes from sleep |  |
| Pogo keyboard | ⬜ Not started | Private UART protocol | Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge |
| Auto-rotate | ⬜ Not started | Needs the sensors | SSC sensors: hexagonrpcd + libssc + iio-sensor-proxy, persist registry |

## Graphics & compute (3/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | OpenGL 4.6 / ES 3.2 on Mesa 26.2.3; glmark2 3015 under GNOME |  |
| GNOME and Wayland drawn by the GPU | ✅ Working |  |  |
| GPU correctness, WebGL, 30-min stress | ⬜ Not started | Relay 012 | Keep linux-firmware's gen80200 sqe/gmu/aqe + the tablet's own zap (your call); A/B the stock set only as a side check; missing stock 1100 MHz OPP; dEQP/piglit availability (offline-prep/graphics.md A2/A11) |
| Vulkan | ✅ Working | turnip 26.2.3: Vulkan 1.4, vkmark 24562, vkcube 142 fps |  |
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

## Software & packaging (4/7 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Test-built: 948 modules, device tree, install hooks |  |
| Device package (iceland-device 0.7) | ✅ Working | Settings, battery guard, sound, Wi-Fi region; built |  |
| Local update repository | ✅ Working | Checksum-verified sync; tested |  |
| Full GNOME app set | ⬜ Not started | Relay 008 | Relay 008 package list in the RAM rootfs |
| Stock-values audit | ⬜ Not started | Relay 013 | Relay 013 table; offline-prep/*.md stock comparisons |
| GNOME About page (model, processor) | 🟡 In progress | Shows “oneplus OnePlus Pad 4” and no processor | iceland-device /etc/machine-info (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); no CPU model name in cpuinfo/lscpu: socinfo id 661 name, util-linux part 0x51/0x002 |
| Automated PC fix loop | ✅ Working | The PC session runs everything (cloud debugger handed over, relay 020) |  |

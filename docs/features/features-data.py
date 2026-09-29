# Single source for docs/FEATURES.md and the published feature-matrix page (docs/features/feature-matrix.html).
# Edit here, then run: python3 docs/features/build.py   (regenerates both files; republish the page afterwards).
# Rows: (feature, status, notes[, where to look for the fix]).
# status: ok (working) / part (in progress) / todo (not started) / out (not planned)

DATE = "29 Sep 2026"

# One sentence after the date in FEATURES.md.
STATUS_MD = ("area-graphics-1 and area-power-1 done (automated, under 10 min each): GPU DCVS already at the top under load, "
             "the stock 1100 MHz level and CPU capacity data added, GNOME power modes now drive Pad 4 tuned profiles; "
             "next (the user's order): battery + thermal protection, the mic, Wi-Fi, the cameras")

# The subtitle of the published page.
STATUS_HTML = ("Everything is tested by booting from RAM; nothing is installed on the tablet yet. Status as of "
               f"{DATE}: audio closed (mic hiss a known issue); GPU and Vulkan accelerated with the stock GPU levels; CPU "
               "scaling knows the big and small cores; GNOME's power modes drive Pad 4 profiles; the charging-safety patch "
               "is queued; a live refresh-rate change is worked around by a display off/on. Next: battery and thermal "
               "protection, the mic, Wi-Fi, the cameras. Work runs area by area (relay 019); Boot & platform waits for "
               "your go-ahead on the install.")

G = [
("Boot & platform", [
 ("U-Boot booted from RAM (display, USB fastboot, UFS read, EFI)", "ok", "Nothing written to the tablet; fastboot flashing compiled out"),
 ("U-Boot boot setting for single or dual boot", "ok", "Boots a “fedora” partition if present, else userdata"),
 ("Linux 7.3-rc4 through EFI", "ok", "Queue 0001–0052 + infiniti"),
 ("Fedora 44 running from RAM", "ok", "systemd as PID 1; packages through the PC"),
 ("GNOME Shell 50", "ok", "Autologin session in RAM"),
 ("Firmware extractor (tablet's own partitions, read-only)", "part", "modem/bluetooth work on the tablet; vendor/odm inside “super” proven offline from your partition backup (10 of 10 files match stock 11.A.38)", "Add the LP-metadata reader (an/lp-list.py) + read-only EROFS mount to tools/linux-ram/fw-extract.sh; test against the backup on the PC, then in a kit"),
 ("Fedora installed on the tablet", "todo", "Final step; needs your decisions and OK", "Waits for your install decision (relay 019: Boot & platform last)"),
 ("Dual boot with Android", "todo", "Planned; recovery re-flash helper ready", "iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1"),
]),
("Display & input", [
 ("Native display 3392×2400, dual DSI + DSC", "ok", "Boot splash handed over to MSM DRM"),
 ("Refresh 30 / 60 / 90 / 120 / 144 Hz", "part", "Every rate works; a live rate change blanks the panel, and iceland-device 0.9 now switches the display off/on once after every change (tested live: one relight per change, also for the 60/120 Hz power-source switch); the panel and backlight read normal in the black state, so logs can't judge it (area-display-3)", "Your 1-minute look (deferred): a rate change with the relight, and one with candidate 0054 (stock power sequence) alone; root cause in the msm single-commit modeset; long term stock-style seamless DFPS"),
 ("Backlight", "ok", "Brightness curve still being checked against stock"),
 ("GNOME pink / blocky glitches", "part", "Back: you filmed the whole wallpaper speckled pink/cyan at 00:19 (area-power-1, kernel q21); no kernel error logged; DRAM bank bit ruled out (LPDDR5X = bit 16, as stock)", "Log the DPU's UBWC decode-error status every frame in each kit; then GNOME with FD_MESA_DEBUG=noubwc as the A/B"),
 ("Touchscreen", "ok", "Confirmed by you; keeps working through display off/on cycles and suspend (area-display-2)"),
 ("Pen", "ok", "Working per your call; not tested enough yet (area-display-1 logged 0 pen events, pen maybe not charged)", "Charged pen: tip, hover, buttons, pressure in libinput debug-events; palm rejection"),
 ("Lid switch", "ok", "SW_LID events on GPIO 98 (area-display-1)"),
 ("Power and volume keys", "ok", "Power key also wakes from sleep"),
 ("Pogo keyboard", "todo", "Private UART protocol", "Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge"),
 ("Auto-rotate", "todo", "Needs the sensors", "SSC sensors: hexagonrpcd + libssc + iio-sensor-proxy, persist registry"),
]),
("Graphics & compute", [
 ("Adreno 840 GPU, GLES 3.2", "ok", "OpenGL 4.6 / ES 3.2 on Mesa 26.2.3 (Fedora 44's newest; Mesa main is 7 % slower here); glmark2 3213 offscreen / 2345 on GNOME, DCVS already at 1.2 GHz under load; the stock 1100 MHz level added (area-graphics-1)"),
 ("GNOME and Wayland drawn by the GPU", "ok", ""),
 ("GPU correctness, WebGL, stress", "part", "60-s stress steady at 394 fps, 0 faults, but 103 °C at 1.2 GHz within a minute (area-graphics-1)", "dEQP subset, WebGL in a browser; the heat ceiling belongs to Thermal (GPU trips, skin zone)"),
 ("Vulkan", "ok", "turnip 26.2.3: Vulkan 1.4; vkmark 19563 headless 1080p (area-graphics-1), 24562 fullscreen (display-1)"),
 ("Hardware video decoding", "todo", "Driver in the tree; firmware known", "Iris node disabled and no &iris override in the iceland DTS; set firmware-name vpu40_2v.mbn (driver default vpu40_p2 = ENOENT); CONFIG_VIDEO_QCOM_IRIS; gst v4l2h264dec, CPU time"),
 ("NPU (Hexagon on the CDSP)", "todo", "Off by default; bring-up in relay 012", "CDSP disabled in every kit's debug DTB (build.sh:69); cdsp.mbn vs split .mdt names; iceland-npu-off.service ExecStart path wrong; fastrpc + quic/fastrpc unsigned PD test"),
]),
("Audio", [
 ("DSP audio + sound card", "ok", ""),
 ("GNOME shows speakers and microphones", "ok", "Fixed: stray mixer route; appears on a fresh boot"),
 ("Microphones (2)", "part", "Known issue: a steady hiss 25–35 dB above stock, so GNOME’s meter barely moves; speech gets through", "Downstream WCD939x per-rate SoundWire TX port params vs wcd939x-sdw.c / lpass-tx-macro (relay 018 9b); HIFI mode broken too"),
 ("Speakers (top pair)", "ok", "You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only"),
 ("All six speakers in stereo", "ok", "You heard all six from GNOME’s Sound test, both sides correct"),
 ("Speaker volume cap", "ok", "−12 dB cap enforced by the kernel (queued 0051); stock value still to find"),
 ("GNOME volume bar and input slider", "ok", "Measured: follows GNOME’s curve within ~1 dB (area-display-1)"),
 ("Speaker protection (NXP container)", "todo", "Closed firmware; volume stays capped", "tfa98xx.cnt from odm; TFA DSP protocol (closed); volume stays capped"),
 ("Headset over USB-C", "todo", "No 3.5 mm jack", "WCD939x USBSS mux + UCSI/typec altmode audio accessory"),
]),
("Connectivity", [
 ("Wi-Fi 2.4 GHz", "ok", "Connected by you; GNOME showed “?” until NetworkManager re-checked (a fresh check says full internet)"),
 ("Wi-Fi 5 / 6 GHz", "part", "Region US; 5 GHz (28 ch) and 6 GHz (60 ch) enabled, but no 5/6 GHz network is visible where the tablet was tested: your router shows up only on 2.4 GHz (ch 1), so the connection you made was 2.4 GHz (area-display-3 scan)", "Test near a 5 GHz AP (router 5 GHz radio, or a phone hotspot on 5 GHz); iw reg get (US), ath12k board-2.bin match"),
 ("Bluetooth, own address", "ok", ""),
 ("Bluetooth pairing in GNOME", "ok", "Confirmed by you (29 Sep 2026)"),
 ("USB device mode / USB network", "ok", ""),
 ("USB host / OTG, PD hub", "todo", "", "dwc3 role switch via pmic-glink UCSI; typec sysfs; dwc3 power_lost after resume"),
 ("DisplayPort over USB-C", "todo", "", "qmp-combo PHY + DP controller from the infiniti series; DT enable + altmode"),
]),
("Power & charging", [
 ("Battery level, voltage, current, temperature, health", "ok", "UPower and GNOME battery"),
 ("Battery time estimate", "part", "Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area", "qcom_battmgr OPLUS: STATUS forced to Charging when USB is online; instantaneous 1 Hz current; gauge word 4 is not a charge; derive CHARGE_NOW = capacity × charge_full, probe TTE/TTF/POWER_AVG (offline-prep/power.md A2–A4)"),
 ("Charging", "part", "Stock limits patch 0053 queued (iceland-linux d36c1be): SDP input 500 mA (494 mA measured, was 1.2–1.9 A), knobs work", "Chargers with you watching (power.md T2–T6: DCP, PD 9 V never 12 V, inhibit and FCC effects below 80 %)"),
 ("Battery safety guard (stock limits)", "part", "Review fixes in (iceland-device 0.8: retries, VBUS > 11 V, rise-fast, unreadable voltage); 47 simulated cases pass; tablet test pending", "Tablet test with 0053's charge_behaviour / constant_charge_current_max (power.md T5)"),
 ("Charge limit (85 %, your request)", "todo", "battmgr OnePlus variant exposes no charge_control_* files", "Add the thresholds + setter to the OPLUS battmgr props; check the SoCCP honours opcode 0x48; UPower limit in iceland-device"),
 ("Low-battery current limiting (BCL)", "todo", "", "Stock PMH0101/PMIH010x BCL nodes (relay 018 item 6); qcom-bcl-hwmon / spmi bcl"),
 ("Pen charging", "todo", "New driver needed", "Pen wireless-charge IC on the pogo/magnet side: stock driver in OnePlusOSS"),
 ("Fast charging (SuperVOOC / PPS)", "out", "OnePlus-proprietary; not planned"),
]),
("Thermal", [
 ("CPU frequencies and CPU limits (stock)", "ok", "Held at 105 °C under load"),
 ("Board and flash thermistors", "ok", ""),
 ("Skin and XO zones", "part", "Patch ready; skin limits to be replaced by stock values", "Relay 009 candidate; stock skin gear table (relay 018 item 7) for the caps"),
 ("USB-C connector temperature zone", "part", "Patch ready (57 °C, stock)", "Candidate reads 0x2747 but stock usbtemp uses AMUX1/AMUX5 (0x274a/0x275e); needs relay 009 first to apply (power.md A12/B6/B7)"),
 ("GPU cooling", "part", "105 °C passive map matches stock; the GPU reaches 95–103 °C at 1.2 GHz in under a minute of Vulkan/stress, 0 throttled seconds so far (area-graphics-1)", "Turn the 125 °C critical into hot (stock has no GPU shutdown trip); a longer stress with the skin zone; sustained-load throttling behaviour"),
]),
("Sleep & power saving", [
 ("Suspend (s2idle)", "part", "24 cycles clean; two stalls after audio activity under investigation", "Stalls after audio: timer-sm8850 candidates (rpmh-rsc past-wakeup clamp, arch timer always-on); ramoops + debug-hang kernel"),
 ("Long sleep", "part", "One unexplained reboot after a long sleep: watchdog vs planned reboot", "Reset = PSHOLD/SYSOK: watchdog vs power key; ramoops (pc-026-s10-crashlog) + one 5-min sleep with watchdog on/off"),
 ("Wake by power key and alarm", "ok", ""),
 ("Wake by lid, keyboard, charger", "todo", "", "wakeup-source on gpio-keys lid, pmic-glink/UCSI; /sys/power/pm_wakeup_irq"),
 ("60 Hz on battery, CDSP off", "part", "In iceland-device 0.4+; untested on the tablet", "iceland-device refresh + npu-off units (fix the npu-off ExecStart path)"),
 ("CPU scaling and GNOME power modes", "part", "Stock CPU capacity data (1792/1894 DMIPS/MHz) and iceland-device 0.10 tuned profiles for GNOME's power modes written; area-power-1 verification pending", "Queue the two DTS candidates (GPU levels, CPU capacity); then Thermal"),
 ("Deep-sleep proof, overnight drain ≤ ~1 %/h", "todo", "", "qcom_stats before/after, rpmh-stats; overnight unplugged"),
]),
("Sensors & camera", [
 ("Rear flash LEDs", "ok", ""),
 ("Accelerometer, compass, light / proximity", "todo", "", "hexagonrpcd sensorspd + libssc (adsp_listener_get_in_bufs2 patch), persist registry"),
 ("Cameras (13 MP rear, 8 MP front)", "todo", "Plan written; stock supplies, clock and resets resolved; waiting for register data", "CAMSS/CCI from infiniti; relay 014 register data; research/camera-bringup.md §1b supplies/MCLK/resets"),
 ("Haptics, modem, NFC, fingerprint", "out", "Not on this tablet"),
]),
("Software & packaging", [
 ("Kernel package (kernel-iceland)", "ok", "Test-built: 948 modules, device tree, install hooks"),
 ("Device package (iceland-device 0.9)", "ok", "Settings, battery guard 0.8, sound, Wi-Fi region, 60/120 Hz by power source with the panel relight; built"),
 ("Local update repository", "ok", "Checksum-verified sync; tested"),
 ("Full GNOME app set", "todo", "Relay 008", "Relay 008 package list in the RAM rootfs"),
 ("Stock-values audit", "todo", "Relay 013", "Relay 013 table; offline-prep/*.md stock comparisons"),
 ("GNOME About page (model, processor)", "part", "Shows “oneplus OnePlus Pad 4” and no processor", "iceland-device /etc/machine-info (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); no CPU model name in cpuinfo/lscpu: socinfo id 661 name, util-linux part 0x51/0x002"),
 ("Automated PC fix loop", "ok", "The PC session runs everything (cloud debugger handed over, relay 020)"),
]),
]

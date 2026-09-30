# OnePlus Pad 4 mainline: feature matrix

Status 30 Sep 2026 (GPU correctness done (dEQP Vulkan + GLES, WebGL, stress: the kernel side clean, the failures are Mesa gaps for the new GPU); USB-C DisplayPort enumerates; Wi-Fi 5 GHz narrowed to the chip mode and its regulatory state; hardware video decoding under test; next (the user's order): hardware acceleration, then the NPU; in parallel the cameras, Wi-Fi 5 GHz and USB accessories with the user). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 42 working, 17 in progress, 13 not started, 2 not planned (74).

## Boot & platform (6/9 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| U-Boot booted from RAM (display, USB fastboot, UFS read, EFI) | ✅ Working | Nothing written to the tablet; fastboot flashing compiled out |  |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata |  |
| Linux 7.3-rc4 through EFI | ✅ Working | Queue 0001–0061 + infiniti |  |
| Fedora 44 running from RAM | ✅ Working | systemd as PID 1; packages through the PC |  |
| GNOME Shell 50 | ✅ Working | Autologin session in RAM |  |
| Test sessions stable | ✅ Working | The 30 Sep freezes are found and fixed: fast transfers from the PC into the tablet over USB hung the chip while its CPUs could power down (14 sessions; 7 test runs pin it down and prove the fix, queue 0063). The test kits also hold the same limit themselves, for older kernels |  |
| Firmware extractor (tablet's own partitions, read-only) | 🟡 In progress | modem/bluetooth work on the tablet; vendor/odm inside “super” proven offline from your partition backup (10 of 10 files match stock 11.A.38); vendor_dlkm (ext4) read offline too | Add the LP-metadata reader (an/lp-list.py) + read-only EROFS / ext4 mounts to tools/linux-ram/fw-extract.sh; test against the backup on the PC, then in a kit |
| Fedora installed on the tablet | ⬜ Not started | Final step; needs your decisions and OK | Waits for your install decision (relay 019: Boot & platform last) |
| Dual boot with Android | ⬜ Not started | Planned; recovery re-flash helper ready | iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1 |

## Display & input (8/11 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |  |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | Fixed in the kernel (queue 0058): live rate changes keep the picture - 11 of 11 on the PC webcam across 144/120/60 Hz, two of them after a suspend, no underruns (area-display-7). The cause was a CTL_START the display driver wrote after switching the video engine off; the display off/on workaround in iceland-device is now off by default (0.12) | Long term: stock-style seamless rate switching (no modeset) |
| Backlight | ✅ Working | Brightness curve still being checked against stock |  |
| GNOME pink / blocky glitches | ✅ Working | Fixed in the kernel (queue 0060). The PC webcam caught it at a first login (run 8) with register dumps: the display's UBWC decoder was left at its reset values (memory bank bit 13 instead of 16) because the boot-splash take-over reset the display block and programmed it before the block was out of reset; a display off/on reprogrammed it, which is why it went away. Run 9 logs the race and the corrected setup; the webcam saw no glitch again during the GPU tests (30 Sep) | Watch the first login of the next boots (it was intermittent before the fix) |
| Smooth window moves under load | 🟡 In progress | Choppy while 8 conformance-test processes ran (you, 30 Sep): the webcam showed windows drawn late, no corruption; all CPU cores were busy and the skin loop had capped the CPUs to ~1 GHz and the GPU to 342 MHz at 50 °C | Frame timing of window drags on an idle desktop; the skin-trip choice under Thermal |
| Touchscreen | ✅ Working | Confirmed by you; keeps working through display off/on cycles and suspend (area-display-2). It was dead only in the boots of the 30 Sep freeze window (0 touch interrupts) and works in every boot since | Keep an eye on the touch-interrupt count the test heartbeat now logs |
| Pen | ✅ Working | Working per your call; not tested enough yet (area-display-1 logged 0 pen events, pen maybe not charged) | Charged pen: tip, hover, buttons, pressure in libinput debug-events; palm rejection |
| Lid switch | ✅ Working | SW_LID events on GPIO 98 (area-display-1) |  |
| Power and volume keys | ✅ Working | Power key also wakes from sleep |  |
| Pogo keyboard | ⬜ Not started | Private UART protocol | Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge |
| Auto-rotate | 🟡 In progress | The orientation reaches GNOME: iio-sensor-proxy reports "normal" for the tablet in its stand, as stock Android does for that pose (mount matrix derived from stock; an iio-sensor-proxy startup race fixed) | Turn the tablet once with you watching (left / right / upside down); then the packaging above |

## Graphics & compute (4/6 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | OpenGL 4.6 / ES 3.2 on Mesa 26.2.3 (Fedora 44's newest; Mesa main is 7 % slower here); glmark2 3213 offscreen / 2345 on GNOME, DCVS already at 1.2 GHz under load; the stock 1100 MHz level added (area-graphics-1) |  |
| GNOME and Wayland drawn by the GPU | ✅ Working |  |  |
| GPU correctness, WebGL, stress | ✅ Working | dEQP (VK-GL-CTS 1.4.6.2 mustpass samples): Vulkan 34 650 cases, 2 Fail; GLES2/3/3.1 34 950 cases, 53 Fail (texture formats, ASTC, copy_image: Mesa gaps for the Adreno 8xx), 0 crashes, 0 timeouts; WebGL 1/2 on the GPU, pixel checks exact, 196 conformance pages, 3 failing (same format family); 90-s stress 0 faults, the skin loop throttles it; 0 GPU faults in every run (area-graphics-2/-3) | Single-worker rerun of the 53 GLES + 3 WebGL failures; report to Mesa only with the user's OK |
| Vulkan | ✅ Working | turnip 26.2.3: Vulkan 1.4; vkmark 19563 headless 1080p (area-graphics-1), 24562 fullscreen (display-1) |  |
| Hardware video decoding | 🟡 In progress | Working (queue 0062, area-video-1): the Pad 4's own video firmware boots and the decoder takes H.264, HEVC, VP9 and AV1: H.264, VP9 and AV1 decode bit-exact against software (60 of 60 frames each); the encoder makes H.264 and HEVC. The hardware decoder does not yet play the streams the hardware encoder made | Why the encoder's streams don't decode; a real speed test (1080p / 4K, CPU time); then GNOME's video player and Firefox using it |
| NPU (Hexagon on the CDSP) | ⬜ Not started | Item 6 in your order, after video; the ADSP's FastRPC path already works (the sensors use it) | Enable the CDSP in the kits (build.sh:69 disables it), firmware names (cdsp.mbn vs split .mdt), fastrpc on the CDSP + an unsigned-PD test program; fix the iceland-npu-off unit path |

## Audio (6/9 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| DSP audio + sound card | ✅ Working |  |  |
| GNOME shows speakers and microphones | ✅ Working | Fixed: stray mixer route; appears on a fresh boot |  |
| Microphones (2) | 🟡 In progress | Hiss fixed in the kernel (queue 0059): the mic path's adaptive block was left at its power-on setting, which lifted the noise floor; turned off as stock does without tuning. Recording floor −47 → −63 dBFS, speech level unchanged (area-audio-6/-7); the first recording after boot settles ~5 dB higher | Compare with stock's recordings (spectrum, same room); the first-recording settling; GNOME meter check with you |
| Speakers (top pair) | ✅ Working | You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only |  |
| All six speakers in stereo | ✅ Working | You heard all six from GNOME’s Sound test, both sides correct |  |
| Speaker volume cap | ✅ Working | −12 dB cap enforced by the kernel (queued 0051); stock value still to find |  |
| GNOME volume bar and input slider | ✅ Working | Measured: follows GNOME’s curve within ~1 dB (area-display-1) |  |
| Speaker protection (NXP container) | ⬜ Not started | Closed firmware; volume stays capped | tfa98xx.cnt from odm; TFA DSP protocol (closed); volume stays capped |
| Headset over USB-C | ⬜ Not started | No 3.5 mm jack. USB headsets: the USB audio driver is there and loads on demand (area-usb-1); analog USB-C headsets need the WCD939x audio-accessory mode | A host-mode kit + your headsets (USB and analog adapter); WCD939x USB-SS audio accessory through UCSI |

## Connectivity (5/8 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | Connected by you; GNOME showed “?” until NetworkManager re-checked (a fresh check says full internet) |  |
| Wi-Fi 5 / 6 GHz | 🟡 In progress | Longer scans now find a 5 GHz network in some chip modes: every time in the chip's own preferred mode (4 of 4), never in the boot-time mode Linux picks (0 of 2). The chip also rejects the country setting after every start and Linux lacks its regulatory database, so the cause is not settled yet (area-wifi-2/-3) | Regulatory database + a country in the kit, then boot-time mode A/B without reloads; a 5 GHz connect needs your password |
| Bluetooth, own address | ✅ Working |  |  |
| Bluetooth pairing in GNOME | ✅ Working | Confirmed by you (29 Sep 2026) |  |
| USB device mode / USB network | ✅ Working | The kits' link to the PC; it runs at USB 2 speed (area-usb-1) | SuperSpeed check with a USB 3 cable / port |
| Fast USB transfers into the tablet | ✅ Working | Fixed in the kernel (queue 0063): the USB driver keeps the CPUs from powering down while USB is active, as stock does, so fast transfers from a PC no longer hang the tablet: 4 x 696 MB at 36 MB/s with only the kernel's request (area-freeze-7). Tablet-to-PC runs at 40 MB/s | Measure the idle power it costs while a data cable is plugged in; stock only holds it while USB is busy |
| USB host / OTG, PD hub | ⬜ Not started | The drivers for keyboards, mice, USB headsets, USB Ethernet and USB sticks are all there and load on demand; the Type-C port reports its roles and PD 3.0 (area-usb-1). Not tried with an accessory yet: the test kits keep the port in device mode for their link to the PC | A kit that keeps the role switch + you plugging accessories in; UAS for fast USB SSDs |
| DisplayPort over USB-C | 🟡 In progress | The DisplayPort output is enabled and comes up cleanly: the controller, its PHY and the USB-C switch load without errors and GNOME's display stack sees a DP connector (area-usb-1). Not tried with a monitor yet | A USB-C monitor or dock from you |

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
| Skin and XO zones | ✅ Working | Skin: throttles from 48 °C down to stock's deepest gear, the gear at once at 51 °C, off at 70 °C; XO: stock's 78/80/90 °C steps. Emulated and real load checked (area-thermal-1/-2). Under sustained all-core load the skin sensor (a fast hot spot) holds CPUs at ~1.3 GHz; at 50 °C during the GPU tests it held the CPUs at ~1 GHz and the GPU at 342 MHz | Your choice: keep 48 °C or start at stock's 50/60 °C trip for more sustained speed (a hand-on-the-back check); queue with the other DTS candidates |
| USB-C connector temperature zones | ✅ Working | usb-therm + stock's L/R connector pair (ratiometric, high-Z pins as stock): 28.8 / 28.9 / 33.9 °C next to a 32.1 °C board; the guard reads all three (area-thermal-2) | Check the L/R rise under PD charging current (with you watching) |
| GPU cooling | 🟡 In progress | The skin loop now caps the GPU under sustained load: 90-s stress 318 → 306 and 321 → 288 fps with the GPU at 74-79 °C, 54-60 s throttled (area-graphics-2/-3); the 105 °C passive map matches stock | Turn the 125 °C critical into hot (stock has no GPU shutdown trip); a 30-min stress with the skin zone |

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

## Sensors & camera (2/4 working)

| Feature | Status | Notes | Where to look for the fix |
|---|---|---|---|
| Rear flash LEDs | ✅ Working |  |  |
| Accelerometer, compass, light / proximity | ✅ Working | Working in RAM through the ADSP sensor hub (area-sensors-4..7): BMI3x0 accelerometer, AK09919 magnetometer, STK36C01 light + proximity read live; iio-sensor-proxy (SSC build) serves them to GNOME. Needs kernel 0061, hexagonrpcd with the device's own sensor files, libssc and iio-sensor-proxy with SSC support (built here, not in Fedora) | Package hexagonrpc / libssc / iio-sensor-proxy (SSC) + the udev rule; extract the sensor files from the tablet at install |
| Cameras (13 MP rear, 8 MP front) | 🟡 In progress | Stock camera traced on LineageOS (no photo taken): both sensors' power-up order and delays, I2C addresses (rear 0x36, front 0x10, focus motor 0x0c), 4 CSI lanes each at 1324.8 / 660 Mbps, the register tables of every mode stock uses (13 MP rear, 8 MP and 2 MP front), exposure / gain registers, black level and colour order. A driver for both SmartSens sensors and the device-tree nodes are drafted from the trace (compile-tested); the focus motor uses the upstream DW9719 driver (DW9800K variant) | First-light kit (research/camera-bringup.md C3): camera branch + the sensor module, frames through libcamera; the register tables stay private |
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

# Single source for docs/FEATURES.md and the published feature-matrix page (docs/features/feature-matrix.html).
# Edit here, then run: python3 docs/features/build.py   (regenerates both files; republish the page afterwards).
# Rows: (feature, status, notes[, where to look for the fix]).
# status: ok (working) / part (in progress) / todo (not started) / out (not planned)

DATE = "1 Oct 2026"

# One sentence after the date in FEATURES.md.
STATUS_MD = ("Microphone fixed (the test image had an old sound profile without the mic gain, and the mic now matches "
             "stock's level); the NPU's DSP runs from the tablet's own firmware and loads its NPU runtime; hardware video "
             "decoding done; in progress in one combined step: camera first light, Wi-Fi 5 GHz, the last video items and "
             "the idle cost of the USB fix")

# The subtitle of the published page.
STATUS_HTML = ("Everything is tested by booting from RAM; nothing is installed on the tablet yet. Status as of "
               f"{DATE}: the microphone is fixed (the test image carried an old sound profile without the mic gain; "
               "the mic now matches stock's level), the NPU's processor starts from the tablet's own firmware, runs "
               "test programs and loads its NPU runtime, hardware video decoding works and GNOME's player uses it. "
               "In progress, as one combined step: camera first light, Wi-Fi 5 GHz, the last video items and the idle "
               "cost of the USB fix. Boot & platform waits for your go-ahead on the install.")

G = [
("Boot & platform", [
 ("U-Boot booted from RAM (display, USB fastboot, UFS read, EFI)", "ok", "Nothing written to the tablet; fastboot flashing compiled out"),
 ("U-Boot boot setting for single or dual boot", "ok", "Boots a “fedora” partition if present, else userdata"),
 ("Linux 7.3-rc4 through EFI", "ok", "Queue 0001–0061 + infiniti"),
 ("Fedora 44 running from RAM", "ok", "systemd as PID 1; packages through the PC"),
 ("GNOME Shell 50", "ok", "Autologin session in RAM"),
 ("Test sessions stable", "ok", "The 30 Sep freezes are found and fixed: fast transfers from the PC into the tablet over USB hung the chip while its CPUs could power down (14 sessions; 7 test runs pin it down and prove the fix, queue 0063). The test kits also hold the same limit themselves, for older kernels"),
 ("Firmware extractor (tablet's own partitions, read-only)", "part", "modem/bluetooth work on the tablet; vendor/odm inside “super” proven offline from your partition backup (10 of 10 files match stock 11.A.38); vendor_dlkm (ext4) read offline too", "Add the LP-metadata reader (an/lp-list.py) + read-only EROFS / ext4 mounts to tools/linux-ram/fw-extract.sh; test against the backup on the PC, then in a kit"),
 ("Fedora installed on the tablet", "todo", "Final step; needs your decisions and OK", "Waits for your install decision (relay 019: Boot & platform last)"),
 ("Dual boot with Android", "todo", "Planned; recovery re-flash helper ready", "iceland-u-boot patch 0003 (fedora_blkmap); tools/dualboot/reflash-recovery.ps1"),
]),
("Display & input", [
 ("Native display 3392×2400, dual DSI + DSC", "ok", "Boot splash handed over to MSM DRM"),
 ("Refresh 30 / 60 / 90 / 120 / 144 Hz", "ok", "Fixed in the kernel (queue 0058): live rate changes keep the picture - 11 of 11 on the PC webcam across 144/120/60 Hz, two of them after a suspend, no underruns (area-display-7). The cause was a CTL_START the display driver wrote after switching the video engine off; the display off/on workaround in iceland-device is now off by default (0.12)", "Long term: stock-style seamless rate switching (no modeset)"),
 ("Backlight", "ok", "Brightness curve still being checked against stock"),
 ("GNOME pink / blocky glitches", "ok", "Fixed in the kernel (queue 0060). The PC webcam caught it at a first login (run 8) with register dumps: the display's UBWC decoder was left at its reset values (memory bank bit 13 instead of 16) because the boot-splash take-over reset the display block and programmed it before the block was out of reset; a display off/on reprogrammed it, which is why it went away. Run 9 logs the race and the corrected setup; the webcam saw no glitch again during the GPU tests (30 Sep)", "Watch the first login of the next boots (it was intermittent before the fix)"),
 ("Smooth window moves under load", "part", "Choppy while 8 conformance-test processes ran (you, 30 Sep): the webcam showed windows drawn late, no corruption; all CPU cores were busy and the skin loop had capped the CPUs to ~1 GHz and the GPU to 342 MHz at 50 °C", "Frame timing of window drags on an idle desktop; the skin-trip choice under Thermal"),
 ("Touchscreen", "ok", "Confirmed by you; keeps working through display off/on cycles and suspend (area-display-2). It was dead only in the boots of the 30 Sep freeze window (0 touch interrupts) and works in every boot since", "Keep an eye on the touch-interrupt count the test heartbeat now logs"),
 ("Pen", "ok", "Working per your call; not tested enough yet (area-display-1 logged 0 pen events, pen maybe not charged)", "Charged pen: tip, hover, buttons, pressure in libinput debug-events; palm rejection"),
 ("Lid switch", "ok", "SW_LID events on GPIO 98 (area-display-1)"),
 ("Power and volume keys", "ok", "Power key also wakes from sleep"),
 ("Pogo keyboard", "todo", "Private UART protocol", "Private UART protocol: stock oplus pogo driver in OnePlusOSS; serdev + HID bridge"),
 ("Auto-rotate", "part", "The orientation reaches GNOME: iio-sensor-proxy reports \"normal\" for the tablet in its stand, as stock Android does for that pose (mount matrix derived from stock; an iio-sensor-proxy startup race fixed)", "Turn the tablet once with you watching (left / right / upside down); then the packaging above"),
]),
("Graphics & compute", [
 ("Adreno 840 GPU, GLES 3.2", "ok", "OpenGL 4.6 / ES 3.2 on Mesa 26.2.3 (Fedora 44's newest; Mesa main is 7 % slower here); glmark2 3213 offscreen / 2345 on GNOME, DCVS already at 1.2 GHz under load; the stock 1100 MHz level added (area-graphics-1)"),
 ("GNOME and Wayland drawn by the GPU", "ok", "Buffers from other devices (video frames, shared-memory frames) are shown correctly since DMABUF_DEBUG is off (before: GPU faults and a green picture)"),
 ("GPU correctness, WebGL, stress", "ok", "dEQP (VK-GL-CTS 1.4.6.2 mustpass samples): Vulkan 34 650 cases, 2 Fail; GLES2/3/3.1 34 950 cases, 53 Fail (texture formats, ASTC, copy_image: Mesa gaps for the Adreno 8xx), 0 crashes, 0 timeouts; WebGL 1/2 on the GPU, pixel checks exact, 196 conformance pages, 3 failing (same format family); 90-s stress 0 faults, the skin loop throttles it; 0 GPU faults in every run (area-graphics-2/-3)", "Single-worker rerun of the 53 GLES + 3 WebGL failures; report to Mesa only with the user's OK"),
 ("Vulkan", "ok", "turnip 26.2.3: Vulkan 1.4; vkmark 19563 headless 1080p (area-graphics-1), 24562 fullscreen (display-1)"),
 ("Hardware video decoding", "ok", "Works (queue 0062 + a kernel config fix): the Pad 4's own video firmware; H.264 (High profile too), HEVC up to 4K, VP9 and AV1 decode bit-exact against Android's reference decoders (VTS vectors: 240/240, 300/300, 300/300, 167/167). 4K H.264 at 450 fps, 4K VP9 at 308 fps with a tenth of the CPU time. GNOME's player (Showtime) picks it by itself: 1080p H.264 at 3 % CPU vs 47 % in software. The picture was solid green until a kernel debug option (DMABUF_DEBUG) was turned off: it stripped the page lists the GPU needs to show foreign buffers (area-video-2..5)", "10-bit VP9 (GStreamer does not negotiate it yet); Firefox decodes in software (Fedora's FFmpeg has no V4L2 hardware path)"),
 ("Hardware video encoding", "ok", "The encoder makes H.264 and HEVC; with standard HD colours (BT.709) its streams decode on the hardware decoder and in software, 60 of 60 frames (area-combo-1). With SD colours (BT.601) GStreamer's hardware decoder element refuses the stream's colour description - a GStreamer limitation, the stream itself is valid", "The GStreamer fix (test a patched plugin, upstream with your OK); a camera or screen-recorder test once the cameras work"),
 ("NPU (Hexagon on the CDSP)", "ok", "The NPU's processor (CDSP) starts from the tablet's own firmware and stays up; test programs run on it in an unsigned process (Qualcomm's open FastRPC library: calculator and multithreading tests pass), and the tablet's own NPU runtime library loads there (area-combo-1/-2). No kernel change was needed", "Running a neural network needs Qualcomm's QNN SDK for Linux (their licence: your decision); one shared-memory call of the test fails (HAP_mmap); packaging: firmware extractor for the CDSP files, the DSP file tree, a fastrpc RPM"),
]),
("Audio", [
 ("DSP audio + sound card", "ok", ""),
 ("GNOME shows speakers and microphones", "ok", "Fixed: stray mixer route; appears on a fresh boot"),
 ("Microphones (2)", "ok", "Fixed (1 Oct): the RAM test image carried an old sound profile without the microphone gain, so GNOME's input meter stayed flat; the kits now install the current profile at every boot. The mic was also 12-14 dB quieter than stock for the same sound (stock adds gain in its DSP); the profile now adds 12 dB and matches stock's recorder (speech -41.4 vs -41.9 dBFS). The meter reaches 30-50 % for speech at the tablet (area-combo-1..3). The hiss was fixed earlier (queue 0059)", "A look at the meter by you; compare a recording by ear with stock's"),
 ("Speakers (top pair)", "ok", "You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only"),
 ("All six speakers in stereo", "ok", "You heard all six from GNOME’s Sound test, both sides correct"),
 ("Speaker volume cap", "ok", "−12 dB cap enforced by the kernel (queued 0051); stock value still to find"),
 ("GNOME volume bar and input slider", "ok", "Measured: follows GNOME’s curve within ~1 dB (area-display-1)"),
 ("Speaker protection (NXP container)", "todo", "Closed firmware; volume stays capped", "tfa98xx.cnt from odm; TFA DSP protocol (closed); volume stays capped"),
 ("Headset over USB-C", "todo", "No 3.5 mm jack. USB headsets: the USB audio driver is there and loads on demand (area-usb-1); analog USB-C headsets need the WCD939x audio-accessory mode", "A host-mode kit + your headsets (USB and analog adapter); WCD939x USB-SS audio accessory through UCSI"),
]),
("Connectivity", [
 ("Wi-Fi 2.4 GHz", "ok", "Connected by you; GNOME showed “?” until NetworkManager re-checked (a fresh check says full internet)"),
 ("Wi-Fi 5 / 6 GHz", "part", "Not solved: full scans at boot still find no 5 GHz network (0 of 12), single-channel scans do. The regulatory database is now in the kits and the country can be set (no change); the hw-mode candidate at first load changes nothing either - the earlier good passes were all after a driver reload (area-combo-2/-3)", "Reload vs first load of the Wi-Fi driver, the firmware's dual-MAC scan configuration; a 5 GHz connect needs your password"),
 ("Bluetooth, own address", "ok", ""),
 ("Bluetooth pairing in GNOME", "ok", "Confirmed by you (29 Sep 2026)"),
 ("USB device mode / USB network", "ok", "The kits' link to the PC; it runs at USB 2 speed (area-usb-1)", "SuperSpeed check with a USB 3 cable / port"),
 ("Fast USB transfers into the tablet", "ok", "Fixed in the kernel (queue 0063): the USB driver keeps the CPUs from powering down while USB is active, as stock does, so fast transfers from a PC no longer hang the tablet (area-freeze-7; six more RAM sessions since without a freeze). First idle number: with a data cable in, the CPUs stay in the lightest idle state all the time", "Idle power A/B against a kernel without it; stock only holds it while USB is busy"),
 ("USB host / OTG, PD hub", "todo", "The drivers for keyboards, mice, USB headsets, USB Ethernet and USB sticks are all there and load on demand; the Type-C port reports its roles and PD 3.0 (area-usb-1). Not tried with an accessory yet: the test kits keep the port in device mode for their link to the PC", "A kit that keeps the role switch + you plugging accessories in; UAS for fast USB SSDs"),
 ("DisplayPort over USB-C", "part", "The DisplayPort output is enabled and comes up cleanly: the controller, its PHY and the USB-C switch load without errors and GNOME's display stack sees a DP connector (area-usb-1). Not tried with a monitor yet", "A USB-C monitor or dock from you"),
]),
("Power & charging", [
 ("Battery level, voltage, current, temperature, health", "ok", "UPower and GNOME battery"),
 ("Battery time estimate", "part", "Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area", "qcom_battmgr OPLUS: STATUS forced to Charging when USB is online; instantaneous 1 Hz current; gauge word 4 is not a charge; derive CHARGE_NOW = capacity × charge_full, probe TTE/TTF/POWER_AVG (offline-prep/power.md A2–A4)"),
 ("Charging", "part", "Stock limits patch 0053 queued (iceland-linux d36c1be): SDP input 500 mA (494 mA measured, was 1.2–1.9 A), knobs work", "Chargers with you watching (power.md T2–T6: DCP, PD 9 V never 12 V, inhibit and FCC effects below 80 %)"),
 ("Battery safety guard (stock limits)", "ok", "iceland-device 0.11 guard ran live on the tablet (area-thermal-1/-2): stock JEITA regions, voltages, currents, the three USB-C connector sensors (hottest valid reading), power-off at 70 °C (stock framework) / 77 °C; 70 simulated cases pass", "PD/DCP charger tests with you watching (connector sensors under charging current)"),
 ("Charge limit (85 %, your request)", "part", "Works: iceland-battery-guard stops charging at 85 % and resumes at 80 % (/etc/iceland/battery-guard.conf); measured +292 → −7 mA (area-thermal-2). The charger firmware ignores its own limit request, so GNOME shows no switch yet", "A kernel software limit (charge_control_* through the same charge inhibit) so GNOME's Preserve Battery Health switch appears"),
 ("Low-battery current limiting (BCL)", "todo", "", "Stock PMH0101/PMIH010x BCL nodes (relay 018 item 6); qcom-bcl-hwmon / spmi bcl"),
 ("Pen charging", "todo", "New driver needed", "Pen wireless-charge IC on the pogo/magnet side: stock driver in OnePlusOSS"),
 ("Fast charging (SuperVOOC / PPS)", "out", "OnePlus-proprietary; not planned"),
]),
("Thermal", [
 ("CPU frequencies and CPU limits (stock)", "ok", "Held at 105 °C under load"),
 ("Board and flash thermistors", "ok", ""),
 ("Skin and XO zones", "ok", "Skin: throttles from 48 °C down to stock's deepest gear, the gear at once at 51 °C, off at 70 °C; XO: stock's 78/80/90 °C steps. Emulated and real load checked (area-thermal-1/-2). Under sustained all-core load the skin sensor (a fast hot spot) holds CPUs at ~1.3 GHz; at 50 °C during the GPU tests it held the CPUs at ~1 GHz and the GPU at 342 MHz", "Your choice: keep 48 °C or start at stock's 50/60 °C trip for more sustained speed (a hand-on-the-back check); queue with the other DTS candidates"),
 ("USB-C connector temperature zones", "ok", "usb-therm + stock's L/R connector pair (ratiometric, high-Z pins as stock): 28.8 / 28.9 / 33.9 °C next to a 32.1 °C board; the guard reads all three (area-thermal-2)", "Check the L/R rise under PD charging current (with you watching)"),
 ("GPU cooling", "part", "The skin loop now caps the GPU under sustained load: 90-s stress 318 → 306 and 321 → 288 fps with the GPU at 74-79 °C, 54-60 s throttled (area-graphics-2/-3); the 105 °C passive map matches stock", "Turn the 125 °C critical into hot (stock has no GPU shutdown trip); a 30-min stress with the skin zone"),
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
 ("Accelerometer, compass, light / proximity", "ok", "Working in RAM through the ADSP sensor hub (area-sensors-4..7): BMI3x0 accelerometer, AK09919 magnetometer, STK36C01 light + proximity read live; iio-sensor-proxy (SSC build) serves them to GNOME. Needs kernel 0061, hexagonrpcd with the device's own sensor files, libssc and iio-sensor-proxy with SSC support (built here, not in Fedora)", "Package hexagonrpc / libssc / iio-sensor-proxy (SSC) + the udev rule; extract the sensor files from the tablet at install"),
 ("Cameras (13 MP rear, 8 MP front)", "part", "First light not reached yet (area-combo-2/-3): the camera subsystem now probes with the sensors wired through the CSI-2 PHY nodes (44 entities, both PHYs; the first wiring crashed the driver); the camera I2C bus needs the sensors' 1.8 V rail for its pull-ups; the sensors do not bind because the reset pins' pin configuration is rejected (PMIC GPIO 13 / 14). Driver and device tree from the stock trace as before; register tables private", "Read the pad type of the reset GPIOs from the tablet, fix the pin configuration, then chip IDs and raw frames"),
 ("Haptics, modem, NFC, fingerprint", "out", "Not on this tablet"),
]),
("Software & packaging", [
 ("Kernel package (kernel-iceland)", "ok", "Test-built: 948 modules, device tree, install hooks"),
 ("Device package (iceland-device 0.13)", "ok", "Settings, battery guard 0.11 (70 °C, USB-C L/R, 85 % limit), sound, Wi-Fi region, 60/120 Hz by power source (relight off: kernel 0058 fixes rate changes), GNOME power modes; built"),
 ("Local update repository", "ok", "Checksum-verified sync; tested"),
 ("Full GNOME app set", "todo", "Relay 008", "Relay 008 package list in the RAM rootfs"),
 ("Stock-values audit", "todo", "Relay 013", "Relay 013 table; offline-prep/*.md stock comparisons"),
 ("GNOME About page (model, processor)", "part", "Shows “oneplus OnePlus Pad 4” and no processor", "iceland-device /etc/machine-info (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); no CPU model name in cpuinfo/lscpu: socinfo id 661 name, util-linux part 0x51/0x002"),
 ("Automated PC fix loop", "ok", "The PC session runs everything (cloud debugger handed over, relay 020)"),
]),
]

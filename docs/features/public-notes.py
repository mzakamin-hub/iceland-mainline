# Public texts for docs/FEATURES.md (the public "what works" list); build.py reads this file.
# features-data.py stays the single full source: status and grouping come from there, and only rows with status
# "ok" are listed publicly. This file only gives those rows a user-facing description (and, where the internal name
# reads as a note to ourselves, a public name). No new claims: every text restates the row's evidence.
#
# PUBLIC: {feature name exactly as in features-data.py: "description" or ("public name", "description")}
# A working row without an entry here is listed with its internal note, cleaned of run ids; build.py warns about it.
# Keep the entries in sync when a matrix-*.py script adds, renames or re-words a working row.

PUBLIC_STATUS = ("Fedora 44 with GNOME is installed on the tablet and boots on its own (ABL -> U-Boot -> GRUB -> "
                 "kernel). Current versions: kernel 7.3.0-rc7-iceland-00436 (q89k, iceland-linux branch "
                 "iceland-7.3-rc7-next), iceland-device 0.28-16, iio-sensor-proxy 3.9-11.iceland1, "
                 "iceland-firmware 11.A.38-3, U-Boot install build v4.")

PUBLIC = {
# Boot & platform
"U-Boot (RAM boot and the install build)": (
    "U-Boot (install build and RAM boot)",
    "The stock boot loader (ABL) starts U-Boot from boot_b, and U-Boot starts Fedora through EFI. The install build "
    "(v4 since 14 Oct 2026) shows a power-on boot menu on the keys (Fedora, or the boot loader's fastboot), boots "
    "Fedora by default and never resets or powers off by itself. A RAM-boot build gives display, USB fastboot, UFS "
    "read and EFI, with fastboot flashing compiled out."),
"U-Boot boot setting for single or dual boot":
    "Boots a “fedora” partition if there is one, else the Fedora image in userdata.",
"Linux 7.3-rc7 through EFI":
    "Linux 7.3-rc7 with the Pad 4 patch queue (kernel 7.3.0-rc7-iceland-00436, iceland-linux branch "
    "iceland-7.3-rc7-next) boots through U-Boot's EFI, Fedora's shim and GRUB. It is the default kernel on the "
    "installed tablet since 15 Oct 2026.",
"Internal storage (UFS 4)":
    "UFS 4 with 4 KiB blocks in MCQ mode (9 hardware queues per LUN), about 2.3 GB/s direct read. The installed root "
    "is btrfs (zstd compression) on a loop device in userdata, and Fedora's own I/O scheduler rule applies to all six "
    "LUNs.",
"Hardware watchdog":
    "qcom_wdt with a 30 s timeout, fed by systemd: a hung system reboots by itself.",
"System cache (LLCC) and memory error counters":
    "The system cache driver (qcom-llcc) binds, and EDAC reports the memory error counters (no errors recorded).",
"Memory bandwidth monitors":
    "The three bandwidth monitors bind, and their interrupts follow the memory load.",
"Memory bus DVFS (DDR / LLCC memlat)":
    "DDR (547 to 5333 MHz) and the system cache (282 to 1350 MHz) scale with the load (tb323fu-linux's memlat "
    "series).",
"GPI DMA engines":
    "Four GPI DMA controllers serve the I2C and SPI buses.",
"Fuses (QFPROM)":
    "Read through their drivers; the GPU picks its speed bin (18 levels) from them.",
"Hardware random number generator":
    "Two hardware sources: the firmware TRNG (the default, it feeds the kernel's random pool) and qcom_hwrng. The "
    "output passes statistical checks (chi-square, FIPS 140-2).",
"Wall clock (RTC offset in SDAM2)":
    "The clock is right at boot, also offline: the PMIC's RTC belongs to the secure world, so the kernel keeps a UTC "
    "offset in the PMIC's SDAM (SuperTurtleDev's fix). NTP keeps the clock in sync.",
"Fedora 44 from RAM / the PC's disk":
    "For testing, the Fedora image boots from RAM or from a PC's disk over USB, with nothing written to the tablet.",
"GNOME Shell 50":
    "GNOME 50.5 on Fedora 44; a new install starts with GNOME's first-boot setup.",
"Test sessions stable": (
    "Stable USB sessions",
    "Long sessions over the USB link to a PC run stable: the freezes during fast USB transfers are fixed (queue "
    "0063)."),
"Firmware extractor (tablet's own partitions, read-only)":
    "iceland-fw-extract copies the GPU, video, Wi-Fi, Bluetooth, sound, touch and sensor-hub firmware read-only from "
    "the tablet's own partitions; the files match the checksum record.",
"Firmware package (iceland-firmware)":
    "iceland-firmware 11.A.38-3: the generic stock 11.A.38 firmware (and stock's decoded thermal model) as an RPM, "
    "each file sha256-pinned to our own extraction, in the public repo mzakamin-hub/iceland-firmware. Unit-specific "
    "data is never included.",
"Fedora installed on the tablet":
    "Fedora 44 installs with two partition writes: the system image into userdata and U-Boot into boot_b; nothing "
    "else is written. The tablet then boots Fedora on its own, the root is btrfs on a loop device in userdata, and "
    "Fedora marks the boot slot successful.",
# Display & input
"Native display 3392×2400, dual DSI + DSC":
    "The panel runs at its native 3392×2400 over dual DSI with DSC; the boot splash hands over to the MSM DRM driver. "
    "Since kernel 00436 the flicker in the lower quarter of the screen with automatic brightness is gone.",
"Refresh 30 / 60 / 90 / 120 / 144 Hz":
    "Live rate changes keep the picture; GPU-drawn frames are paced exactly at 60, 120 and 144 Hz.",
"Backlight":
    "Both backlight chips are programmed as on stock. GNOME's brightness slider and automatic brightness work; the "
    "thermal limit lowers only what the chips get, so the slider keeps the user's value.",
"Display wake from sleep":
    "The picture comes back after every wake from sleep (16 of 16 wakes tested), with no display timeouts at "
    "suspend entry.",
"GNOME pink / blocky glitches": (
    "No pink / blocky glitches in GNOME",
    "Fixed in queue 0060 (the compressed-buffer decoder is set up again after the splash hand-over); not seen "
    "since 30 Sep."),
"Touchscreen":
    "Works, also after display off / on and suspend.",
"Pen":
    "Works (checked on the tablet).",
"Lid switch":
    "The cover turns the screen off and on. On battery a closed cover suspends, on a charger it locks.",
"Power and volume keys":
    "The power key wakes the tablet from sleep. Without a charger a press suspends; with a charger in it locks and "
    "turns the screen off, as stock does.",
"Auto-rotate":
    "Works in tablet mode, with the panel's landscape mount matrix. While a keyboard is connected GNOME leaves tablet "
    "mode and stops rotating, as designed.",
# Graphics & compute
"Adreno 840 GPU, GLES 3.2":
    "OpenGL 4.6 / OpenGL ES 3.2 on Mesa 26.2.4, with no GPU faults in the test runs (glmark2 3213 offscreen, "
    "es2gears 119 fps in the session).",
"GNOME and Wayland drawn by the GPU":
    "GNOME and Wayland are drawn by the GPU; buffers from other devices (video, shared memory) show correctly.",
"GPU correctness, WebGL, stress":
    "dEQP: Vulkan 34,650 cases with 2 failures, GLES 34,950 cases with 53 failures, 0 crashes; 193 of 196 WebGL test "
    "pages pass; a 90 s stress run had 0 GPU faults. Firefox renders normally.",
"Vulkan":
    "Vulkan 1.4 through turnip on Mesa 26.2.4; vkcube and vkmark run.",
"Hardware video decoding":
    "H.264, HEVC up to 4K, VP9 (also 10-bit) and AV1 decode in hardware, bit-exact against Android's reference "
    "vectors. GNOME's video player uses it (1080p H.264 at 3 % CPU instead of 47 %); SD BT.601 colour is right with "
    "Fedora's GStreamer.",
"Hardware video encoding":
    "H.264 and HEVC encode in hardware (decoded back 30 of 30 frames, PSNR about 50 dB). GNOME's screen recording "
    "works on the hardware encoder with a V4L2 pipeline.",
"NPU (Hexagon on the CDSP)":
    "The CDSP runs the tablet's own firmware; FastRPC programs run in an unsigned process and the NPU runtime library "
    "loads. Idle, it sleeps without blocking deep sleep.",
# Audio
"DSP audio + sound card":
    "The ADSP-based sound card comes up at boot and stays present.",
"GNOME shows speakers and microphones":
    "Speakers and microphones appear in GNOME on a fresh boot.",
"Microphones (2)":
    "Both microphones work at stock's gain. GNOME's default input is a processed source (echo cancellation, gain "
    "control, noise suppression); the raw source is kept.",
"Echo cancellation and loopback sound test":
    "WebRTC echo cancellation runs on the default microphone source, followed by a limiter, so the processed output "
    "does not clip. An automatic loopback test (tones, sweep, speech-like) checks the whole chain.",
"All six speakers in stereo":
    "All six speakers play in stereo with the sides correct and left / right balanced.",
"Speaker protection (PipeWire chain)":
    "A protective PipeWire filter chain (150 Hz high-pass, compressor, limiter) runs in front of the six amplifiers "
    "and leaves no clipped samples.",
"GNOME volume bar and input slider":
    "Both follow GNOME's curve within about 1 dB.",
# Connectivity
"Wi-Fi 2.4 GHz":
    "Connects and reconnects after a drop; the regulatory domain is set before registration, and the Wi-Fi address "
    "is stable across boots.",
"Wi-Fi 5 / 6 GHz":
    "Connects on 5 GHz networks (Wi-Fi 6 GHz not tested yet).",
"Bluetooth, own address":
    "The controller comes up powered with the tablet's own address, also after rfkill cycles.",
"Bluetooth pairing in GNOME":
    "Pairing works from GNOME's settings, and scans find devices.",
"USB device mode / USB network":
    "USB device mode (USB 2 speed) and a USB network link to a PC work; the controller runtime-suspends when nothing "
    "is attached.",
"Fast USB transfers into the tablet":
    "Stable: the CPUs stay out of deep power-down while a USB data link is up (queue 0063).",
"CPU latency request follows the USB cable":
    "The USB controller's CPU latency request is held only while a cable is in, so the CPUs reach deep idle "
    "unplugged.",
# Power & charging
"Battery level, voltage, current, temperature, health":
    "Shown by UPower and GNOME's battery panel.",
"Battery power reading (power_now)":
    "Right: the kernel reports voltage × current, because the battery firmware's own value is unusable on this SoC "
    "(SuperTurtleDev's fix).",
"Battery time estimate":
    "A steady estimate in GNOME. Measured with the screen at 50 %: light use 14-15 h, 1080p video 15-16 h, all cores "
    "busy about 7 h, screen off but awake about 3.5 days.",
"Battery safety guard (stock limits)":
    "One guard in iceland-device applies stock's JEITA temperature regions, voltages and currents, watches the three "
    "USB-C connector sensors and powers off at stock's limits.",
"Charger input cut at a hot USB-C connector":
    "The guard cuts the charger input at a hot connector and keeps it cut (tested with an emulated 58 °C connector).",
"Charge limit (85 %, your request)": (
    "Charge limit (80 / 85 %)",
    "GNOME's 'Preserve Battery Health' works: charging stops at its 80 / 85 % thresholds (a kernel feature), with "
    "the battery guard as a second layer."),
"Bypass charging":
    "A Quick Settings toggle lets the charger power the tablet while the battery level holds; the charge limit still "
    "applies.",
"Low-battery current limiting (BCL)":
    "Stock's battery alarms and 'nearly empty' limits on the GPU and CPUs; alarms limit and release all seven zones.",
# Thermal
"CPU frequencies and CPU limits (stock)":
    "Held at stock's 105 °C under load; the limits are released 4 s after a load ends.",
"Board and flash thermistors":
    "Read and bound to stock's thermal zones.",
"Skin and XO zones":
    "Stock's skin limits (60 / 61 °C, shutdown at 70 °C), XO steps (78 / 80 / 90 °C), power-chip alarms (95 °C) and "
    "GPU / CPU trips; every trip was tested up and down by emulation.",
"Skin temperature policy (stock gears)":
    "iceland-thermal applies stock's 20 temperature gears (CPU, GPU, brightness and charging caps) on stock's "
    "shell-temperature model, with stock's screen-off table and input boost ceiling.",
"USB-C connector temperature zones":
    "usb-therm and stock's left / right connector sensors read within a few °C of the board; the battery guard "
    "watches all three.",
"GPU cooling":
    "Limited as on stock (20 of 20 checks); the hottest GPU sensor reached 98 °C under load.",
"NPU / CDSP cooling":
    "Upstream QMI cooling with stock's maps; it throttles and releases as on stock.",
# Sleep & power saving
"Suspend (s2idle)":
    "Suspend (s2idle) and resume work: the installed tablet slept 8 h 34 min overnight and resumed normally. On a "
    "charger the battery guard keeps the tablet awake on purpose.",
"Wi-Fi across sleep":
    "Wi-Fi powers off in sleep and is back about 2 s after the wake.",
"Long sleep":
    "Long sleeps work: a 22-minute sleep woke by the power key, and the installed tablet slept through the night.",
"Wake by power key and alarm":
    "Both wake the tablet.",
"60 Hz on battery (the CDSP stays running)":
    "60 Hz on battery and 120 Hz on mains (120 Hz costs about 0.7 W); the idle CDSP keeps running at almost no "
    "cost.",
"CPU scaling and GNOME power modes":
    "Stock's CPU capacities and GPU levels; GNOME's three power modes switch matching tablet profiles.",
"Deep-sleep proof, overnight drain ≤ ~1 %/h": (
    "Deep sleep, overnight drain about 0.35 %/h",
    "In sleep the SoC reaches CX and DDR collapse (95-98 % of the time in tests). Overnight unplugged on the "
    "installed tablet: 8 h 34 min at about 0.22 W, about 0.35 % per hour."),
"Per-rail power telemetry (PMIC)":
    "A hwmon driver for the PMK8850 telemetry gives energy and power of 7 rails; it costs nothing in sleep.",
# Sensors & camera
"Rear flash LEDs":
    "Both LEDs work as a torch.",
"Accelerometer, compass, light / proximity":
    "All four sensor types appear at boot through the ADSP sensor hub (hexagonrpc, libssc, iio-sensor-proxy "
    "3.9-11.iceland1). The stream stops across sleep, and the light sensor is filtered to steady values.",
"Gyroscope (sensor hub)":
    "Read through the sensor hub at about 24 Hz, with a mean near 0 rad/s at rest.",
"Cameras (13 MP rear, 8 MP front)":
    "The 13 MP rear (SC1320CS) and 8 MP front (SC820CS) cameras stream through Fedora's libcamera 0.7.1-2, with the "
    "orientation matching the display; the rear lens actuator is powered only while streaming.",
"Camera app on the installed image":
    "GNOME Camera (Snapshot) works with both cameras (40 of 40 open / close cycles clean).",
# Software & packaging
"Kernel package (kernel-iceland)":
    "kernel-iceland RPMs (current 7.3.0~rc7.iceland.00436) install and update with dnf on the installed system: a "
    "new kernel boots once as a trial and becomes the default after a confirmed boot. The camera and backlight "
    "modules are included; no firmware is inside.",
"Device package (iceland-device 0.28-7)": (
    "Device package (iceland-device)",
    "iceland-device 0.28-16 carries the tablet's settings: the battery guard, the thermal policy, the sound chain, "
    "the sensor and Bluetooth address services, the power-key handling and the power-saving boot options."),
"Update policy and minimal package holds":
    "Fedora 44 updates normally, with a read-only snapshot before each transaction and a GRUB rollback entry. Kernels "
    "and the project's packages come only from the local repository, and the release is pinned to 44.",
"Stock-values audit":
    "1,249 values compared with stock: nothing above stock in the battery, charger, thermal, CPU or GPU tables, and "
    "all six amplifiers at stock.",
"GNOME About page (model, processor)":
    "Shows “OnePlus Pad 4” and “Qualcomm Oryon × 8”.",
"Automated rehearsals (no owner steps)": (
    "Automated test runs",
    "Every test run boots from the PC and runs alone: a test user, loopback sound, camera, sensor and clock checks; "
    "every generated script passes a gate first."),
"Upstream fixes for this chip's drivers":
    "The kernel carries the upstream fixes for this SoC's drivers plus tb323fu-linux's and SuperTurtleDev's fixes; "
    "patches that broke this tablet are left out. The provenance is recorded in iceland-linux.",
"Hardware inventory (every block vs stock)":
    "112 hardware blocks compared with stock: every unbound device is explained, and a read-only test re-checks it "
    "after each kernel change.",
}

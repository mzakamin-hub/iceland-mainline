# Public texts for docs/FEATURES.md (the public "what works" list); build.py reads this file.
# features-data.py stays the single full source: status and grouping come from there, and only rows with status
# "ok" are listed publicly. This file only gives those rows a user-facing description (and, where the internal name
# reads as a note to ourselves, a public name). No new claims: every text restates the row's evidence.
#
# PUBLIC: {feature name exactly as in features-data.py: "description" or ("public name", "description")}
# A working row without an entry here is listed with its internal note, cleaned of run ids; build.py warns about it.
# Keep the entries in sync when a matrix-*.py script adds, renames or re-words a working row.

PUBLIC_STATUS = ("Fedora 44 with GNOME 50 is installed on the tablet and boots on its own (ABL -> U-Boot -> "
                 "GRUB -> kernel). Current versions: kernel 7.3.0-next-20261020-iceland-00463 (q90i, the "
                 "patch queue on linux-next next-20261020; iceland-linux branch iceland-7.3-rc7-next), "
                 "iceland-device 0.28-32, iceland-coexist 1.0-6, upower 1.91.5-1.fc44.iceland1, "
                 "iio-sensor-proxy 3.9-11.iceland1, iceland-firmware 11.A.38-6, U-Boot install build v7.")

PUBLIC = {
# Boot & platform
"U-Boot (RAM boot and the install build)": (
    "U-Boot (install build and RAM boot)",
    "The stock boot loader (ABL) starts U-Boot from boot_b, and U-Boot starts Fedora through EFI. The install build "
    "(v7 since 17 Oct 2026) shows a power-on boot menu on the keys (Fedora, BlissROM on the dual-boot layout, or "
    "the boot loader's fastboot), boots "
    "Fedora by default and never resets or powers off by itself. A RAM-boot build gives display, USB fastboot, UFS "
    "read and EFI, with fastboot flashing compiled out."),
"U-Boot boot setting for single or dual boot":
    "Boots a “fedora” partition if there is one, else the Fedora image in userdata.",
"Linux 7.4 base (linux-next) through EFI":(
    "Linux (7.4 base)",
    "Linux with the Pad 4 patch queue on linux-next next-20261020 (Linux 7.3 plus the trees queued for "
    "7.4; current kernel 7.3.0-next-20261020-iceland-00463, iceland-linux branch iceland-7.3-rc7-next, tag "
    "q90i) boots through U-Boot's EFI, Fedora's shim and GRUB."),
"Internal storage (UFS 4)":
    "UFS 4 with 4 KiB blocks in MCQ mode (9 hardware queues per LUN), about 2.3 GB/s direct read. The installed "
    "root is btrfs (zstd compression) in userdata; with iceland-device 0.28-32's device-mapper option "
    "(iceland.carrier.map=dm) TRIM reaches the flash (fstrim, btrfs discard=async). The LUNs use the none I/O "
    "scheduler.",
"Hardware watchdog":
    "qcom_wdt with a 30 s timeout, fed by systemd: a hung system reboots by itself.",
"System cache (LLCC) and memory error counters":
    "The system cache driver (qcom-llcc) binds, and EDAC reports the memory error counters (no errors recorded).",
"Memory bandwidth monitors":
    "The three bandwidth monitors bind, and their interrupts follow the memory load.",
"Memory bus DVFS (DDR / LLCC memlat)":
    "DDR (547 to 5333 MHz) and the system cache (282 to 1350 MHz) scale with the load (tb323fu-linux's memlat "
    "series). Since kernel q90i their frequencies are no longer polled every 2 ms, which saves thousands of "
    "interrupts a second at idle.",
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
    "iceland-firmware 11.A.38-6: the generic stock 11.A.38 firmware (with stock's decoded thermal model and the "
    "sensor hub registry) as an RPM, each file sha256-pinned to our own extraction, plus two GPU firmware pairs in "
    "their own directories: stock's v5.3.39 and the vendor v5.3.33 (a third-party copy, byte-identical in the other "
    "ports' repositories). In the public repo mzakamin-hub/iceland-firmware. Unit-specific data is never included.",
"Fedora installed on the tablet":
    "Fedora 44 installs with two partition writes: the system image into userdata and U-Boot into boot_b; nothing "
    "else is written. The tablet then boots Fedora on its own, the root is btrfs on a loop device in userdata, and "
    "Fedora marks the boot slot successful.",
"Dual boot BlissROM + Fedora":
    "A power-on menu (U-Boot v7) starts Fedora or BlissROM v20.1: Volume Up / Down move, Power selects, Fedora "
    "after 5 s. Fedora runs from its own fedora partition and BlissROM keeps its encrypted data in a smaller "
    "userdata, both on slot b; BlissROM's kernel comes from boot_a and starts with the ramdisk and device tree "
    "that the stock boot loader prepared. Guide and tools: docs/DUAL-BOOT.md, tools/dualboot.",
# Display & input
"Native display 3392×2400, dual DSI + DSC":
    "The panel runs at its native 3392×2400 over dual DSI with DSC; the boot splash hands over to the MSM DRM "
    "driver. Since kernel 00436 the flicker in the lower quarter of the screen with automatic brightness is gone; "
    "kernel 00453 adds fixes for the display state after a screen blank, and kernel 00519 stops the second DSI link "
    "only after both links have stopped, so the screen turns off without an underrun.",
"Refresh 30 / 60 / 90 / 120 / 144 Hz":
    "Live rate changes keep the picture, and since kernel 00511 a change between 120 and 60 Hz is made in place, "
    "without a modeset; GPU-drawn frames are paced exactly at 60, 120 and 144 Hz. A static screen drops to 30 Hz "
    "after 1 s (idle refresh) and returns at the next frame.",
"Backlight":
    "Both backlight chips are programmed as on stock. GNOME's brightness slider and automatic brightness work "
    "(automatic brightness is on by default since iceland-device 0.28-31, as on stock); the thermal limit "
    "lowers only what the chips get, so the slider keeps the user's value.",
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
    "Works in tablet mode, with the panel's landscape mount matrix, without display glitches while the sensor "
    "streams (fixed in kernel q90d). While a keyboard is connected GNOME leaves tablet mode and stops rotating, "
    "as designed; GNOME then releases the accelerometer, as it does while rotation lock is on, and the sensor "
    "hub stops streaming.",
# Graphics & compute
"Adreno 840 GPU, GLES 3.2":
    "OpenGL 4.6 / OpenGL ES 3.2 on Mesa, with no GPU faults in the test runs. Since 16 Oct 2026 the GPU runs "
    "the vendor firmware GMU v5.3.33 / SQE 0x094 (as the other ports of this chip) with GPU preemption on: in "
    "the test run 48356 preemption switches without a fenced-write failure, timeout or GPU fault. Stock's "
    "firmware v5.3.39 is also packaged and runs cleanly with preemption off. The GPU's current limiter (CLX) "
    "is on (iceland-device 0.28-32).",
"GNOME and Wayland drawn by the GPU":
    "GNOME and Wayland are drawn by the GPU; buffers from other devices (video, shared memory) show correctly.",
"GPU correctness, WebGL, stress":
    "dEQP: Vulkan 34,650 cases with 2 failures, GLES 34,950 cases with 53 failures, 0 crashes; 193 of 196 WebGL "
    "test pages pass; a 90 s stress run had 0 GPU faults. Firefox renders normally; Chromium WebGL ran 180 s "
    "without a GPU-process crash with GPU preemption on. A GPU hang is recovered: the GPU is reset and the "
    "desktop keeps running (kernel q90e and later).",
"Vulkan":
    "Vulkan 1.4 through turnip on Mesa 26.2.4; vkcube and vkmark run (vkmark about 22,000-23,600 headless).",
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
    "Connects on 5 GHz networks: an 80 MHz link at about 650-780 Mbit/s link rate, downloads above 100 Mbit/s (Wi-Fi "
    "6 GHz not tested yet).",
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
    "Shown by UPower and GNOME's battery panel. The battery energy is reported at the cell's nominal voltage (full "
    "about 53.8 Wh, design 52.05 Wh); a 30-minute check matches the integrated current within 2 %.",
"Battery power reading (power_now)":
    "Right: the kernel reports the battery current at the nominal voltage of the battery's energy values, so "
    "energy / power gives the time the charge lasts; the battery firmware's own power value is unusable on "
    "this SoC (the kernel computes it, based on SuperTurtleDev's fix).",
"Battery time estimate":
    "A steady estimate in GNOME, based on the battery's real energy; the time remaining matches charge / current "
    "and the time to full counts to the charge limit (upower 1.91.5-1.fc44.iceland1). Measured with the screen "
    "at 50 %: light use 14-15 h, 1080p video 15-16 h, all cores busy about 7 h, screen off but awake about 3.5 "
    "days.",
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
    "Suspend (s2idle) and resume work, and s2idle is the kernel's default sleep state (iceland-device 0.28-29): the "
    "installed tablet slept 8 h 34 min overnight and resumed normally. On a "
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
    "All four sensor types appear at boot through the ADSP sensor hub (hexagonrpc 1.iceland2, libssc, "
    "iio-sensor-proxy 3.9-11.iceland1). The stream stops across sleep, the light sensor is filtered to steady "
    "values, and the login screen no longer holds the light sensor.",
"Gyroscope (sensor hub)":
    "Read through the sensor hub at about 24 Hz, with a mean near 0 rad/s at rest.",
"Cameras (13 MP rear, 8 MP front)":
    "The 13 MP rear (SC1320CS) and 8 MP front (SC820CS) cameras stream through Fedora's libcamera 0.7.1-2, with the "
    "orientation matching the display; the rear lens actuator is powered only while streaming.",
"Camera app on the installed image":
    "GNOME Camera (Snapshot) works with both cameras (40 of 40 open / close cycles clean).",
# Software & packaging
"Kernel package (kernel-iceland)":
    "kernel-iceland RPMs (current 7.3.0.next.20261020.iceland.00463) install and update with dnf on the "
    "installed system: a new kernel boots once as a trial and becomes the default after a confirmed boot. The "
    "camera and backlight modules are included; no firmware is inside. The kernel and the package record a "
    "neutral build host name.",
"Device package (iceland-device 0.28-32)":(
    "Device package (iceland-device)",
    "iceland-device 0.28-32 carries the tablet's settings: the battery guard, the thermal policy, the sound "
    "chain, the sensor and Bluetooth address services, the power-key handling, the GPU firmware choice, the "
    "refresh-rate switch and the power-saving boot options (suspend-to-idle as the kernel's default, idle "
    "refresh, CLX, the display and GPU interrupts kept on CPU 0, device interrupts off the prime cores), "
    "automatic brightness by default and the device-mapper option that lets TRIM reach the flash."),
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
# 22 Oct 2026: confirmed working by the owner
"CPU firmware (SCMI CPUCP) cold-soak hang": (
    "CPU firmware after a cold start",
    "The CPU control processor's firmware (SCMI) starts cleanly, also after the tablet has cooled down (SuperTurtleDev's quirk for its first notification). Confirmed working by the owner on 22 Oct 2026."),
"Boot slot marked good from Fedora":
    "Fedora marks the A/B boot slot successful after a good boot, so the boot loader keeps booting it. Confirmed working by the owner on 22 Oct 2026.",
"Smooth window moves under load":
    "Window moves stay smooth, also under load with stock's thermal policy. Confirmed working by the owner on 22 Oct 2026.",
"Pogo keyboard":
    "The keyboard cover on the pogo pins: keys, touchpad, lamps and the keyboard backlight. Confirmed working by the owner on 22 Oct 2026.",
"Speaker level at stock (0 dB)": (
    "Speaker level",
    "The speakers play as loud as on stock, with the amplifiers at stock's settings. Confirmed working by the owner on 22 Oct 2026."),
"Headset over USB-C":
    "Headsets on the USB-C port. Confirmed working by the owner on 22 Oct 2026.",
"USB host / OTG, PD hub": (
    "USB host / OTG and hubs",
    "USB host mode on the USB-C port: keyboards, mice, USB sticks and hubs. Confirmed working by the owner on 22 Oct 2026."),
"DisplayPort over USB-C":
    "An external monitor over USB-C DisplayPort. Confirmed working by the owner on 22 Oct 2026.",
"Charging":
    "Charging with stock's input limits per charger type; the battery guard, the charge limit and the connector temperature cut stay at stock. Confirmed working by the owner on 22 Oct 2026.",
"Pen charging":
    "The pen charges on the tablet's magnetic side (wireless pen charger driver). Confirmed working by the owner on 22 Oct 2026.",
"Wake by lid, keyboard, charger":
    "Opening the cover, the keyboard and plugging or unplugging a charger wake the tablet from sleep. Confirmed working by the owner on 22 Oct 2026.",
"Full GNOME app set":
    "Fedora 44 Workstation's default GNOME apps, the on-screen keyboard and GNOME Software with Flathub. Confirmed working by the owner on 22 Oct 2026.",
}

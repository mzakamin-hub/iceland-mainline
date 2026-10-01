# Single source for docs/FEATURES.md and the published feature-matrix page (docs/features/feature-matrix.html).
# Edit here, then run: python3 docs/features/build.py   (regenerates both files; republish the page afterwards).
# Rows: (feature, status, notes[, where to look for the fix]).
# status: ok (working) / part (in progress) / todo (not started) / out (not planned)

DATE = "2 Oct 2026"

# One sentence after the date in FEATURES.md.
STATUS_MD = ("Wi-Fi finds 5 GHz networks; both cameras work through libcamera (pictures at 24 fps, offered to the desktop); "
             "hardware video is complete; the About page, GNOME's power modes and the battery time estimate work; sleep "
             "is clean over 37 cycles including a 4-minute sleep; auto-rotate turns the picture in tests and its "
             "after-boot failure is understood and worked around. In progress: packaging of the sensor programs, "
             "camera auto-exposure and focus, a 5 GHz connect")

# The subtitle of the published page.
STATUS_HTML = ("Everything is tested by booting from RAM; nothing is installed on the tablet yet. Status as of "
               f"{DATE}: Wi-Fi finds 5 GHz networks at boot; both cameras deliver pictures through libcamera at 24 fps "
               "and are offered to the desktop; hardware video decoding is complete and GNOME Web uses it; the About "
               "page, GNOME's three power modes and the battery time estimate work; sleep is clean over 37 cycles in "
               "three sessions, including a 4-minute sleep; auto-rotate turns the picture for all four orientations in "
               "tests, and why it stayed dead after a normal boot is understood and worked around. In progress: "
               "packages for the sensor programs, camera auto-exposure and focus, a 5 GHz connect. Boot & platform "
               "waits for your go-ahead on the install.")

G = [
("Boot & platform", [
 ("U-Boot booted from RAM (display, USB fastboot, UFS read, EFI)", "ok", "Nothing written to the tablet; fastboot flashing compiled out"),
 ("U-Boot boot setting for single or dual boot", "ok", "Boots a “fedora” partition if present, else userdata"),
 ("Linux 7.3-rc4 through EFI", "ok", "Queue 0001–0073 + infiniti"),
 ("Fedora 44 running from RAM", "ok", "systemd as PID 1; packages through the PC"),
 ("GNOME Shell 50", "ok", "Autologin session in RAM"),
 ("Test sessions stable", "ok", "The 30 Sep freezes are found and fixed: fast transfers from the PC into the tablet over USB hung the chip while its CPUs could power down (14 sessions; 7 test runs pin it down and prove the fix, queue 0063). A lighter version of the fix, as stock does it (only while USB is busy, queue 0064), let one freeze through in five sessions and was taken back (queue 0065)"),
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
 ("Auto-rotate", "part", "GNOME turns the picture for all four orientations and back when they are fed through the tablet's own mount-matrix path (test accelerometer; area-combo-14, -17, -18); the real sensor reads “normal” in the stand; the sensor services now start by themselves once the accelerometer really answers (2.5 s). After a normal boot GNOME never asked for the sensor: a counting bug in GNOME's window manager when a tablet's sensor is already there at login. With a small change in our sensor daemon GNOME asks and turns 4 of 4 (A/B in one session, area-combo-19). The sensor programs are still built on the tablet in each test - nothing is packaged", "Packages for the three sensor programs with our two changes; the sensor hub wants its files within about two minutes of its start (a late start found no sensors once); report the GNOME bug (your OK); one turn of the tablet with you"),
]),
("Graphics & compute", [
 ("Adreno 840 GPU, GLES 3.2", "ok", "OpenGL 4.6 / ES 3.2 on Mesa 26.2.3 (Fedora 44's newest; Mesa main is 7 % slower here); glmark2 3213 offscreen / 2345 on GNOME, DCVS already at 1.2 GHz under load; the stock 1100 MHz level added (area-graphics-1)"),
 ("GNOME and Wayland drawn by the GPU", "ok", "Buffers from other devices (video frames, shared-memory frames) are shown correctly since DMABUF_DEBUG is off (before: GPU faults and a green picture)"),
 ("GPU correctness, WebGL, stress", "ok", "dEQP (VK-GL-CTS 1.4.6.2 mustpass samples): Vulkan 34 650 cases, 2 Fail; GLES2/3/3.1 34 950 cases, 53 Fail (texture formats, ASTC, copy_image: Mesa gaps for the Adreno 8xx), 0 crashes, 0 timeouts; WebGL 1/2 on the GPU, pixel checks exact, 196 conformance pages, 3 failing (same format family); 90-s stress 0 faults, the skin loop throttles it; 0 GPU faults in every run (area-graphics-2/-3)", "Single-worker rerun of the 53 GLES + 3 WebGL failures; report to Mesa only with the user's OK"),
 ("Vulkan", "ok", "turnip 26.2.3: Vulkan 1.4; vkmark 19563 headless 1080p (area-graphics-1), 24562 fullscreen (display-1)"),
 ("Hardware video decoding", "ok", "Works (queue 0062 + a kernel config fix): the Pad 4's own video firmware; H.264 (High profile too), HEVC up to 4K, VP9 and AV1 decode bit-exact against Android's reference decoders (VTS vectors: 240/240, 300/300, 300/300, 167/167). 10-bit VP9 is bit-exact too (72 of 72 frames against the software decoder, area-combo-6) once GStreamer stops rejecting the stream's colour description - a one-line fix in its V4L2 plugin, tested as a patched plugin. GNOME's player picks the hardware by itself (1080p H.264 at 3 % CPU vs 47 %), and GNOME Web decodes H.264 on it inside its normal sandbox (area-combo-7)", "The GStreamer fix as a package or upstream (your OK); Firefox decodes in software (Fedora's FFmpeg has no V4L2 hardware path)"),
 ("Hardware video encoding", "ok", "The encoder makes H.264 and HEVC; its streams decode on the hardware decoder and in software, 60 of 60 frames, with HD colours (BT.709) and - with the GStreamer fix above - with SD colours (BT.601) too (area-combo-1, -4)", "A camera or screen-recorder test once the cameras are usable"),
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
 ("Wi-Fi 5 / 6 GHz", "part", "5 GHz networks are found now (queue 0066–0068): NetworkManager lists them at boot and every scan shows them (area-combo-10). The cause: while not connected, the Wi-Fi firmware scanned the lower 5 GHz channels on its second radio, which has no 5 GHz path on this tablet; stock tells the firmware not to do that (enable_sbs=0), mainline said nothing. Proven by switching it off, on and off again in one session (area-combo-9)", "A connect on 5 GHz needs your password (the test image has no saved Wi-Fi network); 6 GHz needs a 6 GHz access point"),
 ("Bluetooth, own address", "ok", ""),
 ("Bluetooth pairing in GNOME", "ok", "Confirmed by you (29 Sep 2026)"),
 ("USB device mode / USB network", "ok", "The kits' link to the PC; it runs at USB 2 speed (area-usb-1)", "SuperSpeed check with a USB 3 cable / port"),
 ("Fast USB transfers into the tablet", "ok", "Fixed in the kernel (queue 0063): the USB driver keeps the CPUs from powering down while a USB data link is up, so fast transfers from a PC no longer hang the tablet. Stock holds this only while USB is busy; that version (0064) idled better but froze once in five sessions, so it was taken back (0065). Cost: with a data cable to a PC the CPUs stay in their lightest idle state; on a charger or on battery nothing changes", "The real cause of the hang (stock gets away with the lighter version)"),
 ("USB host / OTG, PD hub", "todo", "The drivers for keyboards, mice, USB headsets, USB Ethernet and USB sticks are all there and load on demand; the Type-C port reports its roles and PD 3.0 (area-usb-1). Not tried with an accessory yet: the test kits keep the port in device mode for their link to the PC", "A kit that keeps the role switch + you plugging accessories in; UAS for fast USB SSDs"),
 ("DisplayPort over USB-C", "part", "The DisplayPort output is enabled and comes up cleanly: the controller, its PHY and the USB-C switch load without errors and GNOME's display stack sees a DP connector (area-usb-1). Not tried with a monitor yet", "A USB-C monitor or dock from you"),
]),
("Power & charging", [
 ("Battery level, voltage, current, temperature, health", "ok", "UPower and GNOME battery"),
 ("Battery time estimate", "ok", "Fixed in the kernel (queue 0071 / 0072). GNOME's estimate jumped or vanished because the battery said “Charging” whenever a cable was in (also while a weak PC port could not hold the load), gave a noisy one-second current and no remaining charge. Now: remaining charge = percentage × full capacity (the firmware's own counter agrees), a one-minute average current, and a status that follows it (Charging / Discharging / Not charging / Full). Tested 8 minutes with a load in the middle: status and current agree in 76 of 76 samples, the estimate stays within 4 % once idle (area-combo-13)", "On a charger up to Full, and unplugged, with you; two choices of the fix are ours, not stock's (±20 mA counts as not charging; Full at 100 % with the cable in)"),
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
 ("Suspend (s2idle)", "ok", "37 sleep cycles in three sessions on kernels with the USB fix, all woken by the clock alarm, none failed - with sound played and recorded between and during them (area-combo-12, -14, -15). The two “stalls after audio” of September ran on kernels before the USB fix and no sound had reached the hardware in them", "One recording right after a wake was cut short (once); one display warning on the way into a sleep; the sensor daemon is not restarted after a wake"),
 ("Long sleep", "ok", "The “unexplained reboot after a long sleep” was the test kit's own reboot timer (it counts time asleep), not the watchdog, which is stopped in sleep. A 4-minute sleep wakes by the clock alarm and sound works afterwards (area-combo-15); a 22-minute sleep woke by the power key (2 Oct)", "Overnight drain and deep-sleep proof (own row)"),
 ("Wake by power key and alarm", "ok", ""),
 ("Wake by lid, keyboard, charger", "todo", "", "wakeup-source on gpio-keys lid, pmic-glink/UCSI; /sys/power/pm_wakeup_irq"),
 ("60 Hz on battery, CDSP off", "part", "The refresh-rate unit's logic is proven on the real display with a simulated battery state (battery 60 Hz, mains 120 Hz, back to the start rate; area-combo-11); the NPU-off unit started a program path that is not installed - fixed in iceland-device 0.14", "One unplug with you watching; NPU off / on with the CDSP running"),
 ("CPU scaling and GNOME power modes", "ok", "Stock's CPU capacity data and GPU levels are in the kernel (queue 0054 / 0055); capacities 799 / 1024, the energy-aware scheduler runs. GNOME's three power modes switch tablet profiles as the desktop user (iceland-device 0.14): Power Saver capped at stock's efficient range, Balanced with stock's minimum speeds, Performance with the highest steps requested; a fixed load runs faster or slower accordingly (area-combo-11, 25 checks pass)", "The two top steps (4.5 / 4.6 GHz, stock's maximum) are accepted but the speed does not rise (area-combo-14): the firmware does not grant them yet; your look at the menu"),
 ("Deep-sleep proof, overnight drain ≤ ~1 %/h", "todo", "", "qcom_stats before/after, rpmh-stats; overnight unplugged"),
]),
("Sensors & camera", [
 ("Rear flash LEDs", "ok", ""),
 ("Accelerometer, compass, light / proximity", "ok", "Working in RAM through the ADSP sensor hub (area-sensors-4..7): BMI3x0 accelerometer, AK09919 magnetometer, STK36C01 light + proximity read live; iio-sensor-proxy (SSC build) serves them to GNOME. Needs kernel 0061, hexagonrpcd with the device's own sensor files, libssc and iio-sensor-proxy with SSC support (built here, not in Fedora)", "Package hexagonrpc / libssc / iio-sensor-proxy (SSC) + the udev rule; extract the sensor files from the tablet at install"),
 ("Cameras (13 MP rear, 8 MP front)", "part", "Both cameras deliver pictures. The sensors answer with stock's chip IDs and stream raw 10-bit frames (rear 4160×3120, front 3264×2448; device tree queued as 0073). The rear sensor's exposure is linear and its gain steps are known - measured with the flash LEDs as the light (area-combo-20). libcamera lists “Internal back camera” and “Internal front camera” and gives processed pictures at 24 fps; PipeWire offers both to the desktop (area-combo-21, -22). The sensor driver is ours, written from a trace of stock; its register tables stay private", "Automatic exposure (libcamera needs a gain table for these sensors; the front sensor's gain coding is not known yet); the focus motor; GNOME's Camera app on screen; how to ship the private sensor driver"),
 ("Haptics, modem, NFC, fingerprint", "out", "Not on this tablet"),
]),
("Software & packaging", [
 ("Kernel package (kernel-iceland)", "ok", "Test-built: 948 modules, device tree, install hooks"),
 ("Device package (iceland-device 0.14)", "ok", "Settings, battery guard 0.11 (70 °C, USB-C L/R, 85 % limit), sound, Wi-Fi region, 60/120 Hz by power source, GNOME power modes (stock's floors, three real steps), the About page's model name; built as an RPM on Fedora 44 on the tablet and installed there: 41 files, verify clean (area-combo-17)"),
 ("Local update repository", "ok", "Checksum-verified sync; tested"),
 ("Full GNOME app set", "todo", "Relay 008", "Relay 008 package list in the RAM rootfs"),
 ("Stock-values audit", "todo", "Relay 013", "Relay 013 table; offline-prep/*.md stock comparisons"),
 ("GNOME About page (model, processor)", "ok", "Shows “OnePlus Pad 4” and “Qualcomm Oryon × 8”, read back from the Settings page itself (area-combo-11). Model: /etc/machine-info in iceland-device 0.14. Processor: GNOME only reads the name from /proc/cpuinfo, which has none on ARM - the kernel now prints one (queue 0070, a local addition); the chip is named SM8850P (queue 0069)", "Memory reads 11.1 GiB (the boot loader's table has no memory entry); your look once"),
 ("Automated PC fix loop", "ok", "The PC session runs everything (cloud debugger handed over, relay 020)"),
]),
]

# OnePlus Pad 4 mainline: feature matrix

Status 12 Oct 2026 (install candidate = final golden B145 = kernel q89d9 (Linux 7.3-rc6 + our queue; q89d8 + the Bluetooth -84 fix) + iceland-device 0.28-3 + iceland-firmware 11.A.38-2 + Fedora 44 stable refresh (1727 packages), minimal package holds. Final rehearsal r141 on B145: no regression against r139c / r140 over 36 rows, all product rows PASS; its two FAILs (the camera module check, which a session guard stopped, and a package-version check) are test expectations. Proven since 11 Oct: update and rollback including a rollback boot, the kernel update through rpm, hardware video encode and decode, the firmware package, and the sensors after a resume (kit 144). Open: the speaker level against stock (+9 dB make-up, the owner's choice; never-above-stock is not proven by measurement, so a listening check after the install), the install image from B145 (rebuilt and held; the owner runs the two writes), the permanent boot path (decision 3) and the owner's physical checks). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 79 working, 16 in progress, 6 not started, 3 not planned (104).
Next steps: 3 fixing now, 35 owner checks, 14 can be added, 13 can be tuned (listed at the end).

## Boot & platform (16/22 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| U-Boot (RAM boot and the install build) | ✅ Working | RAM boot gives display, USB fastboot, UFS read and EFI; fastboot flashing is compiled out. The install build (iceland-u-boot 32c967f, patches 0004-0010) passed C0 #4 from boot_b (10 Oct): no reset loop, USB fastboot after 7 s, back to ABL's fastboot with no key press; every probe write was undone the same day. | Owner check: decision 3, the permanent boot path (C0 #1 used up boot_b's retry count 7 -> 0; recovery_b needs its own plan) |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata (iceland-u-boot 0003). | Nothing |
| Linux 7.3-rc6 through EFI | ✅ Working | Kernel q89d9 (7.3.0-rc6-iceland-00414-g9e7350a6ab86) = q89d8 + the Bluetooth -84 fix (9e7350a6ab); q89d8 = q89d5 + the ath12k regulatory-order fix (N3) + the middle amplifiers at stock. 0 build warnings; golden B145, final rehearsal r141 (no regression). The owner keeps rc6: no v7.3-rc7 tag yet; a trial rebase onto torvalds master picked 408 of 411 patches cleanly. | Add: the rebase onto v7.3-rc7 / v7.3 when tagged (trial rebase and build script ready); push the q89d9 branch and tag (q89d8 is pushed) |
| Internal storage (UFS 4) | ✅ Working | 4 KiB blocks, MCQ mode with 9 hardware queues per LUN, 2.3 GB/s O_DIRECT read (area-combo-96). tb323fu's clock-scaling deadlock fix (0255) is in: scaling seen with no error or hung task (r2z). Tests never write the tablet's storage. | Owner check: the installed root on UFS (after the install) |
| Hardware watchdog | ✅ Working | qcom_wdt with a 30 s timeout (kit 119); since iceland-device 0.26 systemd feeds it (RuntimeWatchdogSec 30 s, r2z PASS), so a hung installed system reboots. | Tune: qcom_wdt stops only in suspend_late, so a ~30 s device-suspend stall could fire it - watch the first suspends of the installed system |
| System cache (LLCC) and memory error counters | ✅ Working | qcom-llcc binds; EDAC reports 5 counters, 0 corrected and 0 uncorrected errors (kit 119). | Nothing |
| Memory bandwidth monitors | ✅ Working | The 3 bandwidth monitors bind and their interrupts follow a memory load (kit 119). | Nothing |
| Memory bus DVFS (DDR / LLCC memlat) | ✅ Working | tb323fu's memlat series (0120-0127) is in the kernel since q89d2: DDR follows the load from 547 to 5333 MHz and LLCC from 282 to 1350 MHz (kit 135). Its module must not be reloaded (the firmware keeps the monitors). | Tune: measure the power saving with the rail telemetry (idle, light use) |
| GPI DMA engines | ✅ Working | 4 GPI DMA controllers bind; I2C / SPI clients hold 6 channels (kit 119). | Nothing |
| Fuses (QFPROM) | ✅ Working | Read through their drivers only: the GPU picks its 18-level speed bin from them (kit 119). | Nothing |
| Hardware random number generator | ✅ Working | Two sources: the firmware TRNG (default) and qcom_hwrng. 77,824 bytes read in 30 s are statistically normal (chi-square 275 for 255 degrees of freedom, 7.9974 bits per byte); kit 119's FAIL was its own 1 MiB bar against a TRNG that gives ~2.6 KB/s. | Add: a rate-independent RNG row in the rehearsal set (our idea) |
| CPU firmware (SCMI CPUCP) cold-soak hang | 🟡 In progress | SuperTurtleDev's quirk (skip the CHANNEL_FREE ack on the CPUCP's first notification, 03be252e7197) is in the kernel since q89d2 and its check passed (kit 135). The hang it prevents appears only after a cold soak, which no test has done. | Owner check: a start after a cold soak, then a load (deferred physical check) |
| Wall clock (RTC offset in SDAM2) | ✅ Working | The PMIC RTC belongs to the secure world, so the kernel keeps a UTC offset in SDAM2 (SuperTurtleDev 7a8c303db897 + the s64 offset): the clock is right at boot even offline, no more 1970. Within 1 s of the PC in r138a, 0 s in r138b; the offset survives Android; no RTC write in r138b-r139c. The one offset change (kit 137 vs r137, +79 s in SDAM2) is explained: CONFIG_RTC_SYSTOHC=y is kept, and the 11-minute NTP sync writes the RTC. | Nothing |
| Fedora 44 from RAM / the PC's disk | ✅ Working | A B run builds the golden image on the tablet (B145: 33 PASS, 0 FAIL, 1727 packages = manifest); rehearsals boot it from the PC's disk with nothing written. Suspend is masked on every such boot (two layers + a probe guard). | Nothing |
| GNOME Shell 50 | ✅ Working | GNOME 50.5 after the Fedora 44 refresh (B141 on). Rehearsals log a test user in by autologin in the rehearsal overlay only; the install keeps the first-boot wizard. | Nothing |
| Test sessions stable | ✅ Working | The 30 Sep freezes (fast USB transfers while the CPUs powered down) are fixed in queue 0063; every B run and rehearsal since uses that link. | Nothing |
| Firmware extractor (tablet's own partitions, read-only) | ✅ Working | Every B run copies the GPU, video, Wi-Fi, Bluetooth, sound, touch and sensor-hub firmware read-only from the tablet's own partitions. After Fedora's firmware packages were unheld (B143), the extracted files still matched their checksum record. | Nothing (see Firmware package) |
| Firmware package (iceland-firmware) | 🟡 In progress | The package iceland-firmware 11.A.38-2 (278 generic files; sha256 = our extraction and stock 11.A.38) is in golden B145 and proven in r143 and r145 (FP1-FP4 PASS, rpm -V clean on both boots); the sensor registry and other unit data stay unowned. Published in the dedicated public repo mzakamin-hub/iceland-firmware (created 12 Oct 2026, public, commit c40c33e, tag + release 11.A.38-2 (RPM sha256 14833f719be4... = the package pinned in golden B145, + SRPM); MANIFEST with source + sha256 per file, vendor notices, SuperTurtleDev comparison: 3 files equal, 12 from older releases). | Add: let the installer / update path fetch iceland-firmware from the repo's releases with an sha256 pin (separate tested change, not in the held install image) |
| Fedora installed on the tablet | ⬜ Not started | Not done: the owner runs every write. Candidate: golden B145 (kernel q89d9 + iceland-device 0.28-3 + iceland-firmware 11.A.38-2 + Fedora 44's stable refresh; final rehearsal r141 with no regression). The install image is rebuilt from B145 and held (6,034,694,960 bytes; offline check 98 PASS, 1 FAIL: a 32-byte systemd random-seed file from the build boots, not unit data, owner to accept or drop); the owner runs the two writes, userdata and boot_b; U-Boot install build v3 unchanged. | Owner check: accept or drop the random-seed FAIL; decision 3 (boot path), then the two writes (docs/INSTALL-GUIDE.md), backups G4 / G5, then the two writes (docs/INSTALL-GUIDE.md) |
| Boot slot marked good from Fedora | 🟡 In progress | iceland-slot-mark (iceland-device 0.27r5 on) runs qbootctl -m once after a good boot; it is guarded off in RAM kits and rehearsals (row I1 PASS: installed, signed, skip logged, read-only dump; I1 PASS in r139b and r139c). qbootctl now comes from Fedora (0.2.2-2, floor 0.2.2). | Owner check: its first real run on the installed system |
| Dual boot with Android | ⬜ Not started | Prepared, not started: U-Boot already prefers a “fedora” partition and tools/dualboot can put U-Boot in recovery_b. Missing: shrinking userdata for a “fedora” partition (resets Android's data once), its rehearsal, and re-placing U-Boot after Android slot switches. | Owner check: decision 1, Fedora only or dual boot; then a separate partition plan with its own backup and rehearsal |
| Virtual machines (Gunyah hypervisor) | ⬜ Not started | Not carried. SuperTurtleDev imports Android's Gunyah drivers with a VM smoke test. | Add: (later) SuperTurtleDev's Gunyah import - a feature, not a fix |

## Display & input (10/13 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | The boot splash hands over to MSM DRM. | Fixing: (watch) DPU 'vblank timeout' and 'commit done -110' lines during the idle dim (r139b: 2 in F54; r139c: 0) |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | Live rate changes keep the picture (queue 0058). r139a to r139c: GPU-drawn frames and vblank exact at 60, 120 and 144 Hz with Mesa 26.2.4 (GP1 PASS in r139c). | Tune: stock-style seamless switching without a modeset; tb323fu 0110 (lower idle refresh) later |
| Backlight | ✅ Working | Both backlight chips programmed as stock's kernel does (stock-values audit). | Tune: the brightness curve against stock |
| Display wake from sleep | ✅ Working | tb323fu's DSI PHY runtime suspend over sleep (0050 + 0032) is in: the picture came back in 9 of 9 wakes (kit 135) and 7 of 7 (kit 136), with no DPU timeouts at suspend entry. | Nothing |
| GNOME pink / blocky glitches | ✅ Working | Fixed in queue 0060 (UBWC decoder set up after the splash hand-over reset); not seen since 30 Sep. | Nothing |
| Smooth window moves under load | 🟡 In progress | Choppy only under an all-core load while the skin loop capped CPU and GPU (30 Sep); the stuck CPU limits are fixed (0077). tb323fu's 160 MHz GPU floor is a no-op here (it is the lowest level). | Tune: frame timing of window drags idle and under load, together with the thermal policy choice |
| Touchscreen | ✅ Working | Confirmed by the owner; works through display off / on and suspend (area-display-2). | Nothing |
| Pen | ✅ Working | Works per the owner; not tested in depth (no pen events logged yet). | Owner check: a charged pen - tip, hover, buttons, pressure, palm rejection |
| Lid switch | ✅ Working | SW_LID on GPIO 98; the cover turned the screen off and on in r137 (owner). On battery a closed cover suspends, on a charger it locks. | Nothing |
| Power and volume keys | ✅ Working | The power key also wakes from sleep. | Nothing |
| Pogo keyboard | 🟡 In progress | Our driver (queue 0094-0097) for the cover's private one-wire 921600-baud protocol: line, detection and echo proven without a cover (area-combo-49, -52); kept in the image (owner, 11 Oct); SuperTurtleDev's LED-class backlight and re-detection fix are in (q89d8). | Owner check: attach the cover and type (keys, touchpad, lamps, backlight, wake) |
| Auto-rotate | ✅ Working | Sensor rows PASS over 10 minutes in r138b, r138c and r139; r139a's FAIL was the checker ignoring the mount matrix (the Pad 4's natural orientation is landscape), re-judged 11 of 11; C9a / C9b PASS in r139b and r139c (mount-matrix checker). GNOME's sensor counting bug is worked around (iio-sensor-proxy patch 0002). | Add: report the GNOME bug upstream (owner's OK) |
| Night Light | ❌ Not planned | Dropped by the owner (10 Oct): GNOME set no gamma table and no DSPP is assigned on this display path, so the screen only dimmed. The kit-only colour switch is not on the ship branch. | Nothing |

## Graphics & compute (7/7 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | OpenGL 4.6 / ES 3.2 on Mesa 26.2.4 (Fedora 44 refresh, B141 on): 0 GPU fault lines in r139a (GP3), refresh rows exact; glmark2 3213 offscreen on Mesa 26.2.3. The upstream CLX pair for A840 stops the GPU here and stays out. GP1-GP3 PASS in r139c: no GPU faults, es2gears 119 fps in the session, vkcube 300 frames. | Nothing |
| GNOME and Wayland drawn by the GPU | ✅ Working | Buffers from other devices (video, shared memory) show correctly since DMABUF_DEBUG is off. | Nothing |
| GPU correctness, WebGL, stress | ✅ Working | dEQP: Vulkan 34,650 cases 2 Fail, GLES 34,950 cases 53 Fail (texture formats, ASTC, copy_image), 0 crashes; WebGL 196 pages, 3 failing; 90 s stress 0 faults (area-graphics-2/-3, older Mesa). | Tune: a single-worker rerun of the 53 GLES + 3 WebGL failures on Mesa 26.2.4; report to Mesa with the owner's OK |
| Vulkan | ✅ Working | turnip on Mesa 26.2.4, Vulkan 1.4: vkcube drew 300 frames in r139a (GP2); vkmark 19563 headless / 24562 fullscreen on the earlier Mesa. | Nothing |
| Hardware video decoding | ✅ Working | The Pad 4's video firmware decodes H.264, HEVC up to 4K, VP9 (also 10-bit) and AV1 bit-exact against Android's reference decoders; GNOME's player uses it (1080p H.264 at 3 % CPU instead of 47 %). Proven on q89d8 / q89d9 (r147): bit-exact on the AOSP VTS vectors H.264 240/240, HEVC 300/300, VP9 300/300, AV1 167/167; standard-definition BT.601 streams need the GStreamer colour patch (not in the golden). | Fixing: the GStreamer V4L2 colour patch for SD BT.601 hardware decode (not in the golden); Add: the same one-line fix upstream (owner's OK); Firefox stays software (Fedora's FFmpeg has no V4L2 path) |
| Hardware video encoding | ✅ Working | H.264 and HEVC hardware encodes decode back 30 of 30 frames with BT.709 (PSNR 49.5 / 51.3 dB, r147); BT.601 needs the GStreamer colour patch. | Add: a camera or screen-recorder encode test |
| NPU (Hexagon on the CDSP) | ✅ Working | The CDSP runs the tablet's own firmware; FastRPC test programs run in an unsigned process and the NPU runtime library loads (area-combo-1/-2); idle it sleeps and CX collapse is unaffected. | Owner check: Qualcomm's QNN SDK licence (needed to run a network) |

## Audio (6/10 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| DSP audio + sound card | ✅ Working | The sound devices stay present after every r138a-r139a test step, with 0 APM / PRM timeouts. The rc6 base logs 'SWR bus clsh' and wcd9390 parity lines at capture starts (12-16 per run); sound is not affected. | Tune: the SoundWire clash / parity lines (open since r2u; the upstream N1 patch did not halve them in r139 and was dropped) |
| GNOME shows speakers and microphones | ✅ Working | Stray mixer route fixed; devices appear on a fresh boot. | Nothing |
| Microphones (2) | ✅ Working | ADC 14 (stock's maximum) and TX_DEC 98 = stock's 84 + its 14 dB DSP gain, never above stock; the processed source (WebRTC echo cancel, gain control, noise suppression) is the default, the raw one is kept. Fresh opens after idle (F55) ran in every round of r138b, r139 and r139a; r138c had 1 of 3 rounds with the PCM not running; r139b and r139c opens PASS (r139c #1 a CHECK: one slow watcher read). | Nothing (the ~14 dB left / right gap is mic placement: speaker monitor balanced at 0.0 dB; 0.28-3 device names and defaults PASS in r140 and r141) |
| Echo cancellation and loopback sound test | 🟡 In progress | Automatic loopback rows since r138b (tones, sweep, speech-like; recordings reduced to numbers, then deleted). Echo correlation 0.91, ERLE 10.9 dB in r138c and 9.4 dB in r139; with the tablet upright (r139a) ERLE -0.9 dB and 1672 clipped raw samples; r139b ERLE 37.1 dB and r139c 11.7 dB (both PASS), with 1679 and 1492 clipped raw samples upright (LP CHECK); r140 (0.28-3, +8 dB): ERLE 24 dB and no clipping after the chain; r141 (+9 dB, B145): ERLE PASS, the upright raw capture still clips (LP CHECK). | Tune: raw-capture clipping upright, re-measured with 0.28-3's make-up gain, never above stock |
| All six speakers in stereo | ✅ Working | The owner heard all six from GNOME's Sound test, sides correct; the speaker monitor is balanced (L-R 0.0 dB) and each group is loudest at its nearest mic (r139a). | Nothing |
| Speaker level at stock (0 dB) | 🟡 In progress | The old -12 dB cap was a labelled placeholder, not stock: since 0.27r6 the DSP cap is stock's 0 dB, and q89d8 sets the middle amplifiers to stock (attenuation 5, boost 0xf0): 246 of 268 amplifier fields = stock, 0 above (AK row). Earlier loopback (r138c, 1 kHz at -12 dBFS) measured +15.5 dB; an Android reference (12 Oct) put stock 17-19 dB louder, and the like-for-like re-measure (12 Oct) was INCONCLUSIVE too (the capture paths differ), so the owner chose +9 dB. THD 0.25-0.76 %. | Owner check: listen 'as loud as stock' after the install (0.28-3 at +9 dB make-up; r141 LS = INFO, never-above-stock not proven by measurement) |
| Speaker protection (PipeWire chain) | ✅ Working | A protective filter chain (150 Hz high-pass, compressor, limiter) runs in front of the six amplifiers; the extra -16 dBFS long-term cap was removed in 0.27r6. The sound stack stayed clean with it in r138b, r138c, r139, r139a, r139b and r139c (SA, AE PASS); with 0.28-3 at +9 dB (golden B145) the chain leaves 0 clipped samples (r141). | Nothing |
| Amplifier DSP protection (NXP TFA firmware) | ⬜ Not started | Closed NXP firmware and container (tfa98xx.cnt); the PipeWire chain protects instead. | Add: (later) the upstream TFA2 amplifier driver RFC (David Heidelberg), if it ever gives the amplifiers' own protection |
| GNOME volume bar and input slider | ✅ Working | Follows GNOME's curve within ~1 dB (area-display-1). | Nothing |
| Headset over USB-C | ⬜ Not started | No 3.5 mm jack. USB headsets use the normal USB audio driver; analog USB-C headsets need the WCD939x audio-accessory mode (opt-in candidate, not in the image). The headset codec's error flood is fixed (queue 0186-0188, 0192); two '-16' lines remain at boot. | Owner check: a USB headset and an analog adapter; Add: WCD939x audio-accessory mode through UCSI |

## Connectivity (6/9 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | Connects on the owner's network; F43 (no reconnect after a drop) closed with 802.11d off (queue 0189). q89d8 adds the ath12k fix that sets the regulatory domain before registration (N3 PASS in r139 and r139a); tb323fu's RX refill fix (0259) is in; the firmware's Wi-Fi address is stable across boots (r136). | Owner check: throughput and days of use |
| Wi-Fi 5 / 6 GHz | 🟡 In progress | 5 GHz networks are listed since the second radio stopped scanning them (queue 0066-0068; r2z found 5 networks). No 5 GHz connect or throughput yet: rehearsals keep no saved network. | Owner check: a 5 GHz connect + throughput; 6 GHz needs a 6 GHz access point |
| Bluetooth, own address | ✅ Working | iceland-bdaddr v2 (iceland-device 0.28-2) sets the address with the controller off and waits for the adapter to come back: r139a BTf PASS (powered, own address, 3 of 3 rfkill cycles); BTd PASS in r139b and r139c on 0.28-2 (2 setups, no lost index). v1 raced bluez 5.87 (address set inside the kernel's 2 s auto-off window, adapter never re-announced): the cause of r139's 'no powered controller'. | Nothing |
| Bluetooth pairing in GNOME | ✅ Working | Pairing confirmed (29 Sep); scans find devices when the adapter is up. The 'Frame reassembly failed (-84)' line is gone since q89d9 (BT84 PASS in r146, r146b and r141: 0 lines over 5 setups with 3 power cycles). | Nothing |
| USB device mode / USB network | ✅ Working | The link to the PC for every kit, B run and rehearsal; USB 2 speed (area-usb-1). | Owner check: SuperSpeed with a USB 3 cable / port |
| Fast USB transfers into the tablet | ✅ Working | Fixed in queue 0063: the CPUs stay out of deep power-down while a USB data link is up; stock's lighter variant froze once in five sessions and was taken back. | Tune: (research only) why stock gets away with a lighter hold; never re-ship the lighter variant (0064 froze) |
| CPU latency request follows the USB cable | ✅ Working | dwc3-qcom's 2 us CPU latency request (it kept the CPU clusters out of deep idle) is dropped while no VBUS is present (q89d5): cable out drops it, cable in holds it again (kit 137). | Owner check: the night unplugged (Deep-sleep row) |
| USB host / OTG, PD hub | ⬜ Not started | Dual-role controller and connector under UCSI; drivers for keyboards, mice, headsets, Ethernet, sticks and UAS load on demand; tb323fu's eUSB2 wake-line patch (0062) and the dwc3 lost-state fix (0104) are in. Never tried with an accessory: every test uses the port for the PC link. | Owner check: a keyboard, a stick and a hub |
| DisplayPort over USB-C | 🟡 In progress | Controller, PHY and DP audio bind; DP-1 reads disconnected; with nothing plugged DP runtime-suspends (tb323fu 0265, r2x). tb323fu 0057 (retrain on a quick replug) and 0098 are in. No monitor tried yet. | Owner check: a USB-C monitor or dock (sound over DP too) |

## Power & charging (8/11 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | UPower and GNOME's battery panel. | Nothing |
| Battery power reading (power_now) | ✅ Working | The battery firmware's own power value is bogus on kaanapali (near-constant); the kernel reports voltage x current instead (SuperTurtleDev 2201139167a5, ours since q89d3): 6 of 6 readings right (kit 135, kit 136). | Nothing |
| Battery time estimate | ✅ Working | A steady estimate from charge x capacity and a one-minute current (queue 0071 / 0072). Measured (53.8-56.7 Wh, screen 50 %): light use 14-15 h, 1080p video 15-16 h, all cores busy ~7 h, screen off but awake ~3.5 days (area-combo-69). | Owner check: the night unplugged (Deep-sleep row) |
| Charging | 🟡 In progress | As stock: input current raised in stock's steps, limits follow the charger type, rejected requests are errors (queue 0078-0080). Proven on a PC port only (500 mA, area-combo-39, -40). | Owner check: 20 minutes with the wall chargers (5 V USB-A, USB-C PD, the OnePlus charger) |
| Battery safety guard (stock limits) | ✅ Working | One guard in iceland-device with stock's JEITA regions, voltages, currents and the three USB-C connector sensors; power-off at stock's limits; the charging-safety suite passes. | Owner check: in the charger session (Charging row) |
| Charger input cut at a hot USB-C connector | ✅ Working | The guard cuts the charger input (stock's input-suspend command) at a hot connector and keeps it latched; proven with an emulated 58 °C connector (kit 106). | Owner check: H1-H3 (unplug during a cut, a 9 V charger after a release, the notices) |
| Charge limit (85 %, your request) | ✅ Working | A kernel feature (queue 0074) with the thresholds GNOME's 'Preserve Battery Health' writes (80 / 85 %); confirmed by the owner on 2 Oct; the guard's 85 / 80 % stays as a second layer. | Nothing |
| Bypass charging | ✅ Working | Ships with a Quick Settings toggle (owner's decision O1): the charger powers the tablet and the level holds; the charge limit still wins (kit 119, r2l). | Owner check: the toggle once (W1-W8) |
| Low-battery current limiting (BCL) | ✅ Working | Stock's battery alarms and 'nearly empty' limits on the GPU and CPUs (queue 0075 / 0076); emulated alarms limit and release all seven zones (area-combo-35, -37). | Owner check: one run-down to 5 % |
| Pen charging | 🟡 In progress | The wireless pen charger's driver (queue 0090-0093) is proven without a pen: chip id, 7 V request, boost on, off when unloaded (area-combo-47, -49). | Owner check: the pen on the magnet side for ~90 s |
| Fast charging (SuperVOOC / PPS) | ❌ Not planned | SuperVOOC is OnePlus-proprietary; standard PD 9 V through SuperTurtleDev's charge_boost_lite is NOT included (owner). | Nothing |

## Thermal (6/7 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| CPU frequencies and CPU limits (stock) | ✅ Working | Held at 105 °C under load; limits are released 4 s after a load ends (queue 0077, area-combo-38..40). | Nothing |
| Board and flash thermistors | ✅ Working | Read and bound to stock's zones. | Nothing |
| Skin and XO zones | ✅ Working | Skin throttles from 48 °C to stock's deepest gear, XO uses stock's 78 / 80 / 90 °C steps, the power-chip alarms limit at 95 °C (queue 0081-0083, area-combo-38, -40). | Owner check: see Skin temperature policy |
| Skin temperature policy (stock gears) | 🟡 In progress | Stock's 20-gear shell-temperature policy runs as a daemon in iceland-device (only lowers limits); with stock's 60 °C loop it did 40 % more work under a 60 s load than today's 48 °C loop (area-combo-39). | Owner check: the 60 / 61 °C loop with this policy (recommended) or 48 °C as today |
| USB-C connector temperature zones | ✅ Working | usb-therm and stock's L / R pair read within a few °C of the board; the guard reads all three (area-thermal-2). | Owner check: the L / R rise under PD charging current |
| GPU cooling | ✅ Working | Limited as on stock, 20 of 20 checks (area-combo-41); highest real GPU sensor 98 °C under load. | Nothing |
| NPU / CDSP cooling | ✅ Working | Upstream QMI TMD cooling (queue 0117-0124) with stock's maps; throttles and releases exactly as stock (area-combo-75). | Nothing |

## Sleep & power saving (7/9 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Suspend (s2idle) | ✅ Working | RAM kits on the q89d kernels: kit 137 (q89d5) suspend set PASS, kit 136 7 of 7, kit 132 the pm_test ladder and 9 of 9. Rehearsals never suspend (their root is on the PC's disk), so q89d8 itself first sleeps on the installed system. | Owner check: the first suspends on the installed system (the night unplugged: Deep-sleep row) |
| Wi-Fi across sleep | ✅ Working | Wi-Fi powers off in sleep and is back ~2 s after the wake (area-combo-99); the PCIe 'L2 entry' line at suspend is expected upstream behaviour. | Add: (later) wake-on-WLAN (kernel work, costs battery) |
| Long sleep | ✅ Working | A 22-minute sleep woke by the power key (2 Oct); the old 'reboot after a long sleep' was the test kit's own timer. | Nothing |
| Wake by power key and alarm | ✅ Working | Both wake the tablet in every suspend kit. | Nothing |
| Wake by lid, keyboard, charger | 🟡 In progress | Charger plug and unplug wake the tablet (kit 132, kit 137); the wake rules (USB / PCIe wake off; charger, cover, power key, RTC armed) PASS. The cover's wake from sleep is still CHECK (kit 132: the power key was pressed in its window). | Owner check: cover wake from s2idle (deferred physical check); decide whether the volume keys wake it |
| 60 Hz on battery (the CDSP stays running) | ✅ Working | 60 Hz on battery / 120 Hz on mains works (area-combo-11; 120 Hz costs 0.7 W). Stopping the CDSP at boot is wrong (its own vote then blocks CX collapse until reboot); a running idle CDSP costs almost nothing. The CDSP has run in every boot since 0.18 (the stop is an opt-in). | Nothing |
| CPU scaling and GNOME power modes | ✅ Working | Stock's CPU capacities and GPU levels (queue 0054 / 0055); GNOME's three power modes switch tablet profiles (iceland-device 0.14, 25 checks). | Owner check: decision O4 - the top steps (4.5 / 4.6 GHz) only in Performance |
| Deep-sleep proof, overnight drain ≤ ~1 %/h | 🟡 In progress | 98 % of a 150 s sleep in CX collapse (area-combo-64), 95 % with everything an installed boot loads (-92); PSCI OS-initiated idle active. The USB latency request now follows the cable (kit 137), but deep cluster idle with the cable out and the overnight drain are not measured. | Owner check: one night unplugged (drain per hour); Tune: cpuidle_psci_domain.allow_cluster_off=0 only if an unexplained idle reset appears (the switch is in q89d8) |
| Per-rail power telemetry (PMIC) | ✅ Working | Our hwmon driver for the PMK8850 telemetry gives energy and power of 7 rails, starts only when read and costs nothing in sleep (queue 0163-0166, area-combo-92). | Nothing |

## Sensors & camera (5/7 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Rear flash LEDs | ✅ Working | Both LED nodes work as a torch; stock's 'led-0' lights the rear camera's scene (area-combo-44). | Nothing |
| Accelerometer, compass, light / proximity | ✅ Working | hexagonrpc, libssc and iio-sensor-proxy 3.9 (our builds, held: Fedora's 3.8 has no sensor-hub support); all four types appear at boot; sensor rows PASS in r138b, r138c and r139, r139a re-judged 11 of 11; C9a / C9b PASS in r139b and r139c. Since 0.26 the sensor stream stops across a sleep. | Owner check: the reading after the first suspend on the installed system (the resume unit in 0.28-3: kit 144, 3 of 3 with it, 0 of 3 before) |
| Gyroscope (sensor hub) | ✅ Working | Read through the sensor hub: 24.4 Hz at rest, mean ~0 rad/s (r142, GY PASS; kit 119's step ran without the sensor services). The RGB colour sensor has no class in libssc. | Nothing |
| Cameras (13 MP rear, 8 MP front) | ✅ Working | Rear SC1320CS and front SC820CS stream on Fedora's stock libcamera 0.7.1-1 (our patched build dropped, owner 11 Oct) in every r138b-r139c camera row; orientation from the DT (rotation 0 / 0, queue 0191) matches the display. B145's kernel-iceland ships the in-tree sc1320cs.ko (stripped digest 052334177c5a), and our private out-of-tree build is also made. Which one loads on the installed system is not verified yet; the r141 CAMDRV FAIL came from a session guard that stopped the tablet step, not from a missing module. | Fixing: verify which sc1320cs module loads on the installed system (in-tree or our private build) and ship one; Add: SuperTurtleDev's GPL SmartSens driver as a comparison |
| Camera focus (DW9800K / DW9714V motor) | 🟡 In progress | Fixed focus: the motor is held at stock's start position (queue 0087-0089); its mode / frequency registers read back as the vendor init sets them (kit 135; r139c: 0x02 = 0x02, 0x06 = 0x80, 0x07 = 0x79) and the rear camera streams 200 frames in the focus row (r138a-r139a). No autofocus in libcamera's simple pipeline; the upstream DW9800K update breaks it (chip ID 0xfe) and stays out. | Add: autofocus once upstream libcamera's simple pipeline has it |
| Camera app on the installed image | ✅ Working | GNOME Camera (Snapshot) with both cameras; closing a camera no longer crashes WirePlumber (F54): 40 of 40 open / close cycles on stock libcamera in r138b, r138c, r139 and r139a. Image brightness is informational (r138c's dark frames were a dim room). | Owner check: sharpness and colours by eye; Tune: the simple-IPA yaml values (black level, colour); the sensor helper and static properties only through upstream libcamera |
| Haptics, modem, NFC, fingerprint | ❌ Not planned | Not on this tablet. | Nothing |

## Software & packaging (8/9 working)

| Feature | Status | Notes | Next (fixing / add / tune / owner check) |
|---|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Built from q89d9 (K2 PASS; the rpm update path proven in r146b): installonly, three kept, a trial-boot plug-in, no firmware and no private module inside. | Add: reproducible builds (pinned container + buildinfo hashes; SuperTurtleDev's idea, re-implemented) |
| Device package (iceland-device 0.28-3) | ✅ Working | 0.28-3 = 0.28-2 (the 0.27r6 content with the speaker cap at stock 0 dB, the protective chain, iceland-bdaddr v2) + the sound change (compressor make-up +9 dB, the owner's choice; limiter 0 dB in / -1 dBFS; raw speaker output renamed 'Speakers (raw, unprotected)', protected speakers the default; raw mic 'Internal microphones (raw)') + the sensors-after-resume unit + Fedora-repo excludes; 37 package tests; in golden B145, where r141 had no regression. It carries the battery guard, charge limit, thermal policy, cover, camera, sensor and update rules and the slot marking. | Nothing |
| Update policy and minimal package holds | ✅ Working | Fedora 44 updates normally, with a read-only snapshot before each transaction and a GRUB rollback entry; kernels and our packages come only from the local repository (Fedora's repos exclude kernel-iceland* and iceland-* since 12 Oct); the release is pinned to 44. Minimal holds (owner, 11 Oct; iceland-firmware added 12 Oct): kernel*, kernel-iceland, iio-sensor-proxy, hexagonrpc, libssc, iceland-device and iceland-firmware; grub2, shim, firmware, qbootctl and libcamera come from Fedora (B145 33 / 0; r141 final: update, rollback and the rollback boot PASS, incl. r142 / r142b and r141u / r141ub). | Owner check: versionlock firmware / the sensor stack on the installed system or not |
| Full GNOME app set | 🟡 In progress | Fedora 44 Workstation's default apps: 33 of 33 open a window; on-screen keyboard, GNOME Software with Flathub, GNOME Web with hardware video (area-combo-54..60). | Owner check: a 30-minute look by finger |
| Stock-values audit | ✅ Working | 1,249 values compared with stock: nothing above stock in battery, charger, thermal, CPU or GPU tables; the speaker DSP cap and all six amplifiers are now at stock, 0 fields above (q89d8, AK row). | Tune: re-run after every kernel / package change, plus the loudness row vs stock's measured level |
| GNOME About page (model, processor) | ✅ Working | Shows “OnePlus Pad 4” and “Qualcomm Oryon × 8” (queue 0069 / 0070, iceland-device 0.14). | Tune: memory reads 11.1 GiB (the boot loader's table has no memory entry) |
| Automated rehearsals (no owner steps) | ✅ Working | Since r138b every rehearsal runs alone: a test user with autologin in the rehearsal overlay only, loopback sound, camera metrics, sensor and clock rows; every generated script passes a gate first (B143 prep: 115 / 0). Since r141 the provisioning has no welcome tour, a camera portal pre-grant and an idle inhibit for the whole run. | Nothing |
| Upstream fixes for this chip's drivers | ✅ Working | q89d8 carries the upstream fixes (queue 0139-0161), the 10 Oct rc6 scan additions, tb323fu's set (0255-0265), SuperTurtleDev's SCMI, RTC and power_now fixes, and the N3 ath12k fix. Left out because they broke this tablet or did not help: the q6apm RFC, the GPU CLX pair, the DW9800K update, N1 (SoundWire) and N2 (hci_qca). | Add: drop the patches merged for 7.4 at the next rebase (re-check every rebase) |
| Hardware inventory (every block vs stock) | ✅ Working | 112 blocks compared with stock (wf/hwinv): every unbound device on the running tablet is explained; a read-only test re-checks it after each kernel change. | Nothing |

## Next steps

### Fixing now (3)

- **Native display 3392×2400, dual DSI + DSC** (Display & input): (watch) DPU 'vblank timeout' and 'commit done -110' lines during the idle dim (r139b: 2 in F54; r139c: 0)
- **Hardware video decoding** (Graphics & compute): the GStreamer V4L2 colour patch for SD BT.601 hardware decode (not in the golden)
- **Cameras (13 MP rear, 8 MP front)** (Sensors & camera): verify which sc1320cs module loads on the installed system (in-tree or our private build) and ship one

### Owner checks (35)

- **U-Boot (RAM boot and the install build)** (Boot & platform): decision 3, the permanent boot path (C0 #1 used up boot_b's retry count 7 -> 0; recovery_b needs its own plan)
- **Internal storage (UFS 4)** (Boot & platform): the installed root on UFS (after the install)
- **CPU firmware (SCMI CPUCP) cold-soak hang** (Boot & platform): a start after a cold soak, then a load (deferred physical check)
- **Fedora installed on the tablet** (Boot & platform): accept or drop the random-seed FAIL; decision 3 (boot path), then the two writes (docs/INSTALL-GUIDE.md), backups G4 / G5, then the two writes (docs/INSTALL-GUIDE.md)
- **Boot slot marked good from Fedora** (Boot & platform): its first real run on the installed system
- **Dual boot with Android** (Boot & platform): decision 1, Fedora only or dual boot; then a separate partition plan with its own backup and rehearsal
- **Pen** (Display & input): a charged pen - tip, hover, buttons, pressure, palm rejection
- **Pogo keyboard** (Display & input): attach the cover and type (keys, touchpad, lamps, backlight, wake)
- **NPU (Hexagon on the CDSP)** (Graphics & compute): Qualcomm's QNN SDK licence (needed to run a network)
- **Speaker level at stock (0 dB)** (Audio): listen 'as loud as stock' after the install (0.28-3 at +9 dB make-up; r141 LS = INFO, never-above-stock not proven by measurement)
- **Headset over USB-C** (Audio): a USB headset and an analog adapter
- **Wi-Fi 2.4 GHz** (Connectivity): throughput and days of use
- **Wi-Fi 5 / 6 GHz** (Connectivity): a 5 GHz connect + throughput; 6 GHz needs a 6 GHz access point
- **USB device mode / USB network** (Connectivity): SuperSpeed with a USB 3 cable / port
- **CPU latency request follows the USB cable** (Connectivity): the night unplugged (Deep-sleep row)
- **USB host / OTG, PD hub** (Connectivity): a keyboard, a stick and a hub
- **DisplayPort over USB-C** (Connectivity): a USB-C monitor or dock (sound over DP too)
- **Battery time estimate** (Power & charging): the night unplugged (Deep-sleep row)
- **Charging** (Power & charging): 20 minutes with the wall chargers (5 V USB-A, USB-C PD, the OnePlus charger)
- **Battery safety guard (stock limits)** (Power & charging): in the charger session (Charging row)
- **Charger input cut at a hot USB-C connector** (Power & charging): H1-H3 (unplug during a cut, a 9 V charger after a release, the notices)
- **Bypass charging** (Power & charging): the toggle once (W1-W8)
- **Low-battery current limiting (BCL)** (Power & charging): one run-down to 5 %
- **Pen charging** (Power & charging): the pen on the magnet side for ~90 s
- **Skin and XO zones** (Thermal): see Skin temperature policy
- **Skin temperature policy (stock gears)** (Thermal): the 60 / 61 °C loop with this policy (recommended) or 48 °C as today
- **USB-C connector temperature zones** (Thermal): the L / R rise under PD charging current
- **Suspend (s2idle)** (Sleep & power saving): the first suspends on the installed system (the night unplugged: Deep-sleep row)
- **Wake by lid, keyboard, charger** (Sleep & power saving): cover wake from s2idle (deferred physical check); decide whether the volume keys wake it
- **CPU scaling and GNOME power modes** (Sleep & power saving): decision O4 - the top steps (4.5 / 4.6 GHz) only in Performance
- **Deep-sleep proof, overnight drain ≤ ~1 %/h** (Sleep & power saving): one night unplugged (drain per hour)
- **Accelerometer, compass, light / proximity** (Sensors & camera): the reading after the first suspend on the installed system (the resume unit in 0.28-3: kit 144, 3 of 3 with it, 0 of 3 before)
- **Camera app on the installed image** (Sensors & camera): sharpness and colours by eye
- **Update policy and minimal package holds** (Software & packaging): versionlock firmware / the sensor stack on the installed system or not
- **Full GNOME app set** (Software & packaging): a 30-minute look by finger

### Can be added (14)

- **Linux 7.3-rc6 through EFI** (Boot & platform): the rebase onto v7.3-rc7 / v7.3 when tagged (trial rebase and build script ready); push the q89d9 branch and tag (q89d8 is pushed)
- **Hardware random number generator** (Boot & platform): a rate-independent RNG row in the rehearsal set (our idea)
- **Firmware package (iceland-firmware)** (Boot & platform): let the installer / update path fetch iceland-firmware from the repo's releases with an sha256 pin (separate tested change, not in the held install image)
- **Virtual machines (Gunyah hypervisor)** (Boot & platform): (later) SuperTurtleDev's Gunyah import - a feature, not a fix
- **Auto-rotate** (Display & input): report the GNOME bug upstream (owner's OK)
- **Hardware video decoding** (Graphics & compute): the same one-line fix upstream (owner's OK); Firefox stays software (Fedora's FFmpeg has no V4L2 path)
- **Hardware video encoding** (Graphics & compute): a camera or screen-recorder encode test
- **Amplifier DSP protection (NXP TFA firmware)** (Audio): (later) the upstream TFA2 amplifier driver RFC (David Heidelberg), if it ever gives the amplifiers' own protection
- **Headset over USB-C** (Audio): WCD939x audio-accessory mode through UCSI
- **Wi-Fi across sleep** (Sleep & power saving): (later) wake-on-WLAN (kernel work, costs battery)
- **Cameras (13 MP rear, 8 MP front)** (Sensors & camera): SuperTurtleDev's GPL SmartSens driver as a comparison
- **Camera focus (DW9800K / DW9714V motor)** (Sensors & camera): autofocus once upstream libcamera's simple pipeline has it
- **Kernel package (kernel-iceland)** (Software & packaging): reproducible builds (pinned container + buildinfo hashes; SuperTurtleDev's idea, re-implemented)
- **Upstream fixes for this chip's drivers** (Software & packaging): drop the patches merged for 7.4 at the next rebase (re-check every rebase)

### Can be tuned (13)

- **Hardware watchdog** (Boot & platform): qcom_wdt stops only in suspend_late, so a ~30 s device-suspend stall could fire it - watch the first suspends of the installed system
- **Memory bus DVFS (DDR / LLCC memlat)** (Boot & platform): measure the power saving with the rail telemetry (idle, light use)
- **Refresh 30 / 60 / 90 / 120 / 144 Hz** (Display & input): stock-style seamless switching without a modeset; tb323fu 0110 (lower idle refresh) later
- **Backlight** (Display & input): the brightness curve against stock
- **Smooth window moves under load** (Display & input): frame timing of window drags idle and under load, together with the thermal policy choice
- **GPU correctness, WebGL, stress** (Graphics & compute): a single-worker rerun of the 53 GLES + 3 WebGL failures on Mesa 26.2.4; report to Mesa with the owner's OK
- **DSP audio + sound card** (Audio): the SoundWire clash / parity lines (open since r2u; the upstream N1 patch did not halve them in r139 and was dropped)
- **Echo cancellation and loopback sound test** (Audio): raw-capture clipping upright, re-measured with 0.28-3's make-up gain, never above stock
- **Fast USB transfers into the tablet** (Connectivity): (research only) why stock gets away with a lighter hold; never re-ship the lighter variant (0064 froze)
- **Deep-sleep proof, overnight drain ≤ ~1 %/h** (Sleep & power saving): cpuidle_psci_domain.allow_cluster_off=0 only if an unexplained idle reset appears (the switch is in q89d8)
- **Camera app on the installed image** (Sensors & camera): the simple-IPA yaml values (black level, colour); the sensor helper and static properties only through upstream libcamera
- **Stock-values audit** (Software & packaging): re-run after every kernel / package change, plus the loudness row vs stock's measured level
- **GNOME About page (model, processor)** (Software & packaging): memory reads 11.1 GiB (the boot loader's table has no memory entry)

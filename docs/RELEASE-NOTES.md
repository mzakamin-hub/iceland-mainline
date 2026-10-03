# OnePlus Pad 4 - Fedora 44 GNOME: release notes of release candidate 1 (RC1)

3 Oct 2026 (docs workflow). The full RC1 notes - what each run proved, the ledger's FAILs explained, the known issues
and the owner's checks - are in `docs/guide/RC1-NOTES.md`; this page is the short version. **Nothing has been
installed on the tablet**: every result below is from RAM boots (test kits), from build runs on the tablet, and from
the install rehearsal, which boots the real install image from the PC's disk without writing the tablet. Installing is
your decision and your hands (section 6).

## 1. The build

| Piece | Version / state |
|---|---|
| Kernel | Linux 7.3-rc4 + 138 SM8850 base patches + the Pad 4 queue 0001-0188 (iceland-linux `a9b55d4`, verified against the built tree); kernel q85, release `7.3.0-rc4-iceland-00324-ge0373b2308fc` |
| Kernel package | `kernel-iceland-7.3.0~rc4.iceland.00324.ge0373b2308fc-1.fc44` (K2) and its twin `kernel-iceland-7.3.0~rc4.iceland.00324.ge0373b2308fc.1-1.fc44` (K3) for the update rehearsal; installonly, three kept; depmod outputs ghosted |
| Device package | iceland-device 0.19: the battery guard v3.1 with the charger input cut, PipeWire 1.6.8 or newer (F1), Wi-Fi regulatory domain US (F11), no TPM modules in the initramfs (F10; the tablet has no TPM), the UFS disks' scheduler set one disk at a time (F14), a kernel command line without `clk / pd / regulator_ignore_unused` (F24), the camera tuning |
| U-Boot | the install build and the rehearsal build of iceland-u-boot (v2026.10-rc5 + patches); header and AVB footer carry today's `boot_b` values (17 / 2026-09) |
| Fedora | Fedora-Workstation-Disk-44 aarch64, re-laid for the tablet's 4 KiB storage blocks, plus our packages, the sensor programs, our libcamera 0.7.1 build, the tablet's own firmware (extracted read-only, never distributed) |
| Left out | the USB-C jack mode (k5): an opt-in after a test with your headset |

New in RC1 against the q84 build: the three headset-codec fixes 0186-0188 (the codec's interrupt loop stops on a
failed read; the plug-detect work wakes the codec first; no impedance measurement on an unreadable codec), which end
the burst of about 3600 "ASoC error (-16)" lines per plug event (F18).

The proof, all on 3 Oct:

| Run | What | Result |
|---|---|---|
| kit 106 | kernel q84 in a RAM kit: the charger input cut v3.1 and sleep | the lever, the guard and the restore PASS (219 unit checks); sleep PASS |
| kit 108 | sleep on q84 | PASS (the kit's U-Boot command line still carries the `*_ignore_unused` flags: sleep without them is checked on the installed system, section 5) |
| B runs 107 / 109 | the q84 packages built and checked on the tablet | 30 / 1 (dracut: the TPM measurement unit `systemd-pcrphase`; F10 amended), then **31 PASS, 0 FAIL** |
| rehearsal r2h | the q84 install image booted from the PC's disk | **INSTALL-ACCEPT 45 PASS, 0 FAIL, 0 CHECK**; the debugger's suite 29 PASS; the Camera app works (PipeWire 1.6.9) |
| kit 110 | kernel q85 in a RAM kit | **F18 PASS** (no WCD "-16" line, the headset-detection interrupt exercised, no bus clash or parity error); F17 PASS; the first sleep after boot fixed |
| kit 111 | q85 + the USB-C jack mode (k5) | its probe PASS (USB high speed and the DisplayPort switch unaffected); kept as an opt-in |
| B run 112 | the RC1 packages built and checked on the tablet | **31 PASS, 0 FAIL**; the builder's RC check 8 / 8 |
| rehearsal r2i | the RC1 install image booted from the PC's disk | **INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK; the klog probes 14 / 14 PASS; the debugger's suite 32 PASS, 2 FAIL, 3 CHECK, 1 SKIP**; Fedora's first-boot setup on the screen |

## 2. What works

On the installed image (rehearsal r2i, 3 Oct; SELinux enforcing; the acceptance list passes without a failure or an
open check):
- **Boot chain**: U-Boot -> shim -> GRUB -> our kernel with its own device tree; the root grows to the whole `userdata`
  at first boot; every other internal partition read-only; trial boot and snapshot tooling present.
- **Fedora's first-boot setup** appears at the first start (you create your user there; no preset password).
- **Display and input**: GNOME 50 on the GPU (Adreno 840), touch, pen input, auto-rotate.
- **Sound**: the speakers through PipeWire (volume-capped, see section 4); the headset codec no longer floods the log
  (F18).
- **Wi-Fi** (2.4 / 5 / 6 GHz scans; regulatory domain US as the firmware sets it) - but see F43 in section 3: on your
  network the connection drops after about 110 s - and **Bluetooth** with the tablet's own address.
- **Battery and charging**: battery level and time estimate; GNOME's "Preserve Battery Health" with 80 / 85 % (you
  confirmed it, run 95); the battery guard with stock's limits and, new, the charger input cut at a hot USB-C connector
  (kit 106); charge alerts as desktop notifications.
- **Power modes** (Power Saver / Balanced / Performance) with stock's CPU ranges.
- **Cameras**: both sensors probe at boot and capture through libcamera with the stock-derived tuning; PipeWire offers
  both to the desktop; **GNOME's Camera app works** (F1; 6 starts without a crash in r2i) and full-size captures work
  (F2) - but see F44 in section 3.
- **Video**: hardware decoding (H.264, HEVC, VP9, AV1) in GNOME's player and GNOME Web.
- **Clock** correct from the first boot (stamp, then NTP), **firewall** running, the default apps start.
- **Update safety**: Fedora's kernels and boot loaders cannot be installed by updates; GRUB, shim and firmware held;
  Fedora pinned to 44; fwupd cannot write boot code or the storage's firmware.

In the RAM kits (not repeated in the rehearsal, whose root lives on the PC): suspend (s2idle) on q84 (kits 106 and 108)
and q85 (kit 110) with CX collapse, Wi-Fi back after every sleep, the first sleep after boot fixed (run 104), measured
battery life (light use 14-17 h, 1080p video 15-16 h, screen off awake about 3.5 days), thermal and GPU cooling as
stock, low-battery limiting, the NPU's processor, the microphones at stock's level, the lid / cover, the pogo keyboard
and pen charger drivers (without the accessories), per-rail power telemetry.

## 3. Known issues and what this build fixes

**Known issues of RC1** (details in `docs/guide/RC1-NOTES.md`, section 3a):
- **F43 Wi-Fi**: on your network the connection drops after about 110 s, and every reconnect (2.4 and 5 GHz) fails
  until a reboot. Cause found: the Wi-Fi firmware's 802.11d scan is re-armed at every disconnect; stock switches 802.11d
  off. The fix (k9) comes in loop 3.
- **F44 Camera app**: it can fail to start a camera when another camera program used the other camera since login (a
  stale link in the camera pipeline). Loop 3.
- **F45 GNOME Software** can abort after a network change: an upstream GTK 4 assertion, benign.

What was fixed against the last committed state (2 Oct evening), and every finding with its status in RC1:

### Fixed during the night of 2-3 October (proven in the rehearsal boots R2-final / r2g)

| What | Before | Now | Proof |
|---|---|---|---|
| Clock at first boot | the tablet started at systemd's built-in date (March 2026): package signatures looked "not yet valid" | `iceland-clock` keeps a time stamp; the first boot starts at the image's build time, NTP takes over with Wi-Fi | r2f / r2g clock PASS |
| Sound on the installed system | no sound card: alsa-lib's install hook called a sequencer module the kernel did not have | `CONFIG_SND_SEQUENCER=m` + a modprobe softdep | r2f / r2g sound PASS (speaker sink, playback running) |
| Auto-rotate under SELinux | SELinux denied iio-sensor-proxy's QRTR socket | a small SELinux module `iceland_sensors` | r2g rotate PASS; the owner saw the screen turn |
| Firewall | firewalld could not start (nftables features missing in the kernel) | nftables config set in the kernel | r2f / r2g firewall PASS |
| First-boot presets | Fedora's preset would have disabled our units | `50-iceland.preset` | r2f presets PASS |
| Touch after a refresh-rate change | the touch firmware re-download failed after modesets | a kernel follower on the panel's enable / disable | r2f touch PASS, 0 firmware errors |
| Cameras in the image | the sensor driver was private and outside the queue | in-tree in the private kernel queue (owner, 3 Oct), stock-derived tuning in the device package, `libcamera-tools` in the image | r2g: libcamera lists 2, 10 frames each, PipeWire 2 sources |
| Kernel package verify | `rpm -V` flagged depmod's generated files | `%ghost` + depmod in `%posttrans` | r2f verify PASS |
| Forbidden package in the image | `uboot-images-armv8` came in with a dependency | excluded | r2f packages PASS |
| First sleep after boot | the pen charger's interrupt woke the first suspend | the driver waits for its start sequence before suspend | run 104 |
| Charger input cut at a hot USB-C connector | the guard could only stop charging; the system load still flowed through the connector | a stock-exact input-suspend lever, used by the guard; v3.1 in the final build | run 103 (v1 flaw found), kit 106 (v3.1: lever, guard, restore PASS) |
| U-Boot boot header values | U-Boot carried old Android version / patch values | header and AVB footer copy today's `boot_b` (17 / 2026-09) | Part A PARTA: READY FOR C0 |
| Rehearsal watchdog | never armed (the driver's maximum is 31 s) | 30 s in rehearsals; the installed system arms none (a later decision) | r2g watchdog PASS |


### The findings and their status in release candidate 1

Ledger G3 check of release candidate 1's rehearsal r2i: 62 records: PASS 51 | FAIL 7 | await 0 | n/a 4 (`wf/ledger/check-r2i.md`; r2i itself: INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK). Statuses below include the main session's review; the plain explanations of the FAILs and the known issues are in `docs/guide/RC1-NOTES.md` (sections 2a, 3a).

| Id | Area | What it is / what you would notice | Where it matters | Owner | Gate | Status in the final build |
|---|---|---|---|---|---|---|
| F1 | Cameras | GNOME Camera (Snapshot) crashes when it starts (SIGBUS in PipeWire's device monitor inside the app); the cameras themselves work | installed system | fedtest | G2 | **fixed in this build** (r2h PASS; on r2i the app started 6 times without a crash - the suite's Snapshot step failed on F44) |
| F2 | Cameras | the CMA dma-heap (32 MB) was too small for full-resolution frames (13 MP rear, 8 MP front), so the largest photo modes failed; the final build no longer exports CMA as dma-heaps, full-size buffers come from the system heap | installed system | camfix | G2 | **fixed in this build** (r2h PASS; on r2i the kernel side passed - system heap only, full-size frames; the suite missed its line by an index bug) |
| F3 | Cameras | the acceptance check read the wrong tuning-file line (libcamera loads the right file for each camera) | test only | install | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F4 | Cameras | the debugger's own camera probes (arguments, missing tool) | test only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F5 | Cameras | libcamera has no sensor data for SC1320CS / SC820CS (generic gain model, assumed delays, no flip controls): exposure and gain less exact than stock | installed system | camfix | G1 | deferred: libcamera sensor data for SC1320CS / SC820CS comes later (the cameras work with the generic model) |
| F6 | Cameras | camss warns that its test-pattern entities have no function set | log only | camfix | G3 | **fixed in this build** (r2i PASS) |
| F7 | Install rehearsal | the rehearsal's guard took the probe's extension as its limit (625 s instead of 1500 s) and ended the session early | rehearsal only | install | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F8 | First-boot setup | in rehearsals the acceptance step's test user replaces GNOME's first-boot setup (and its greeter logs a crash); the installed system must show the setup | rehearsal only | install | G2 | benign, rehearsal only (the installed system shows the first-boot setup); a new WirePlumber line on r2i (F50) is being classified |
| F9 | System | "Failed to preset all unit ... Read-only file system" lines | log only | fedtest | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F10 | System | the system user / group `tss` is missing (tpm2-tss sysusers not applied): tmpfiles and udev warnings | installed system (cosmetic) | install | G3 | **fixed in this build** (r2i PASS) |
| F11 | Wi-Fi | the regulatory country request is refused and `setregdomain` cannot determine a country; the firmware's US stays (owner decision 10) | installed system | klog | G3 | **fixed in this build** (r2i PASS) |
| F12 | Power / thermal | irqbalance cannot receive thermal messages (CONFIG_THERMAL_NETLINK not set) | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F13 | Boot | the initramfs' udevd cannot resolve the bpf system call (libseccomp missing in the initramfs) | log only | install | G3 | **fixed in this build** (r2i PASS) |
| F14 | Storage | "Failed to write bfq to queue/scheduler: Device or resource busy" on sda-sdd | installed system (the disk scheduler: 3-5 of the 6 UFS disks kept the old one at random) | install | G3 | **fixed in this build** (r2i PASS) |
| F15 | Kernel / DT | reserved-memory overlap between `cpucp` and `pdp` at 0x81200000 | log only (memory map) | klog | G3 | **fixed in this build** (r2i PASS) |
| F16a | Power | gcc / gxclkctl / gpucc reach sync_state only by the timeout, held by the GPU's GMU node (no driver of its own, by design); power-benign | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F16b | Kernel / DT | the CoreSight trace NoC stays in deferred probe (its driver is not built) | log only | klog | G3 | **fixed in this build** (r2i PASS) |
| F17 | Audio | SoundWire 7630000 port counts differ from the controller (din 4 vs 6, dout 0 vs 1) | log only (microphone path) | klog | G3 | **fixed in this build** (r2i PASS) |
| F18 | Audio | bus clashes on the headset codec's SoundWire bus, a codec parity error, the headset-detection -16 burst | installed system (headset detection) | klog | G3 | **fixed in this build** - queue 0186-0188 (kernel q85); kit 110 and r2i PASS; the USB-C jack mode (k5) stays an opt-in |
| F19 | Bluetooth | two "Frame reassembly failed (-84)" lines at power-on | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F20 | Wi-Fi / PCIe | PCIe supplies not described (dummy regulators) and about 11 probe attempts before Wi-Fi binds | installed system (boot time) | klog | G3 | **fixed in this build** (r2i PASS) |
| F21 | Kernel / DT | other dummy or missing supplies (GPU vdd / vddcx, pwrseq vddant, UFS vdd-hba / vccq2) | log only (to prove optional) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F22 | USB-C | pmic-glink "Failed to create device link" warnings | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F23 | Audio | "MultiMedia2 Playback: no backend DAIs enabled" and a quiet loopback share | log only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F24 | Boot / power | the device package said `iceland-cmdline` adds clk / pd / regulator `_ignore_unused` to every boot entry, but its call ran before the kernel's boot entry existed and failed silently, so every rehearsal booted without them - and worked fully, in the better power state. Decision (install workflow, 3 Oct): no flags; `iceland-cmdline` now removes them from every entry and `/etc/kernel/cmdline`; README, guides and package agree | installed system (power, documentation) | install | G3 | **fixed in this build** (r2i PASS) |
| F25 | Tests | the debugger suite's own false alarms (units, a serial-number read, a truncated command, a watchdog line) | test only | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F26 | System | PAM setcred fails (audit res=failed) for the user@ managers of root, iceland and gnome-initial-setup | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F27 | System | GNOME Settings global-shortcuts provider (dbus-:1.N-org.gnome.Settings.GlobalShortcutsProvider) exits with failure | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2h) |
| F28 | System | login sound missing: libcanberra 'Failed to play sound: File or data not found' (sound theme not in the image?) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F29 | System | hexagonrpcd: Could not open oemconfig.so (+ 'Unsupported method') - sensor-hub daemon files | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F30 | Bluetooth | bluetoothd cannot set its default system configuration for hci0 | log only | klog | G1 | benign, confirmed by the debugger and the reviewer (r2i) |
| F31 | System | wireplumber reserve-device assertion: wp_reserve_device_own_name: assertion 'self->owner_id == 0' failed (audio device reservation) | log only (benign) | klog | G2 | benign; its probe passed on r2i; a new WirePlumber line in its subsystem (F50) is being classified |
| F32 | System | udev .link settings cannot be applied to the USB gadget usb0 (Could not set Alias=, MACAddress= ... ignoring) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F33 | System | irqbalance: No directory /sys/devices/platform/31091000.pmu/ (PMU IRQ owner without a platform device dir) | log only (benign) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F34 | System | NetworkManager: p2p-dev-wlp1s0 error setting IPv4 forwarding: Resource temporarily unavailable | log only (benign) | klog | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F35 | System | ModemManager probes a600000.usb and the WCN7860 PCIe function: not supported by any plugin (no modem on this tablet) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F36 | System | benign to confirm: GNOME first-login / offline noise (keyring socket, geolocation off, malcontent, realmd, rsyslog first run, gvfs, gsd-keyboard assertion, app warnings, polkit, portal parent window, abrt journal) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F37 | System | systemd-logind: BLS entry 'Unknown line grub_arg / grub_class / grub_users, ignoring' (x12 per boot) | log only (benign) | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F38 | Desktop | the on-screen keyboard raised an error in a modal dialog (e.g. a password prompt) | installed system | fedtest | G3 | resolved: the test or suite was corrected / the line explained (r2i PASS) |
| F39 | Cameras | camera I2C bus: one GPI DMA error (-5) per boot - the camera module's EEPROM (0x58) does not answer at power-up in GPI mode | log only | camfix | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F40 | GPU | the GPU's GMU logs a delay in a fenced register write | log only | klog | G3 | benign, confirmed by the debugger and the reviewer (r2h) |
| F41 | Desktop | gnome-session asks for the screensaver state before GNOME Shell offers it, once at a fresh login (GNOME behaviour) | log only | install | G3 | benign, confirmed by the debugger and the reviewer (r2i) |
| F42 | Audio | the headset codec's SoundWire RX bus logged a bus clash and a codec parity error (r2g, r2h) | log only | klog | G0 | seen in r2g / r2h, not in kit 110 or r2i (no bus clash or parity error there); being classified (G0) |
| F43 | Wi-Fi | on the owner's network the connection drops after about 110 s and every reconnect (2.4 and 5 GHz) fails until a reboot: the Wi-Fi firmware's 802.11d scan is re-armed at every disconnect; stock switches 802.11d off | installed system | klog | G0 | **known issue of RC1** - fix k9 in loop 3 (docs/guide/RC1-NOTES.md, section 3a) |
| F44 | Cameras | the Camera app can fail to start a camera when another camera program used the other camera since login (a stale link in the camera pipeline) | installed system | camfix | G0 | **known issue of RC1** - loop 3 (camfix; docs/guide/RC1-NOTES.md, section 3a) |
| F45 | Desktop | GNOME Software can abort after a network change (an upstream GTK 4 accessibility assertion) | log only | install | G1 | benign, confirmed by the debugger and the reviewer (r2i) |
| F46 | System | benign: GNOME Shell: 'Gio.IOErrorEnum: Timeout was reached' when NetworkManager re-asks for the W... | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F47 | System | benign: gsd-xsettings: no UI scaling factor when the X11 services start on demand | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F48 | System | benign: the session's end: zram stop res=failed and 'watchdog did not stop!' at the reboot | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F49 | System | benign: GNOME Software's third-party repositories question: the authorisation was dismissed | log only (benign) | install | G0 | benign (r2i PASS; the debugger / reviewer to confirm) |
| F50 | System | user WirePlumber startup: wp-event-dispatcher 'failed to activate item: Object activation aborted: proxy destroyed' (benign pending the debugger) | installed system | install | G0 | being classified (G0) |
| CHGSAFE-V3 | Charging | the charger input cut at a hot USB-C connector (kernel lever + battery guard) and its desktop notice | installed system (safety) | chgsafe | G3 (kit 106) | **fixed in this build** - proven in kit 106 (v3.1: the lever, the guard and the restore PASS; 219 unit checks) |
| SLEEP-Q84 | Sleep | s2idle on the consolidated kernel q84, incl. the pen charger's first-sleep fix | installed system | sleeppower | G3 | **fixed in this build** - proven in kits 106 and 108 (q84) and 110 (q85) |

Benign groups (B-ids; noise that is expected on this hardware or first boot):

| Id | What | Status |
|---|---|---|
| B1 | benign: greeter wireplumber IPC refused at session stop (FIX-LIST) (+ IPCPipe 'Failed to call async' of the same stop: to confirm, camfix) | benign (expected noise) |
| B2 | benign to confirm: alsactl no asound.state (first boot) | benign, confirmed in r2i |
| B3 | benign to confirm: colord EDID too small (DSI panel) | benign, confirmed in r2i |
| B4 | benign to confirm: gsd-usb-protection without USBGuard | benign, confirmed in r2i |
| B5 | benign to confirm: dnf / gnome-software / PackageKit offline | benign, confirmed in r2i |
| B6 | benign to confirm: gnome-shell JS errors / warnings | benign (expected noise) |
| B7 | benign to confirm: gsd-media-keys grabs | benign (expected noise) |
| B8 | benign upstream: ALSA control name truncated | benign, confirmed in r2i |
| B9 | benign upstream: rx_macro unsorted reg_defaults | benign, confirmed in r2i |
| B10 | benign upstream: GIC ITS table sizes reduced | benign, confirmed in r2i |
| B11 | benign upstream: arm-scmi no fast channel, regular messaging | benign, confirmed in r2i |
| B12 | benign upstream: SELinux checkreqprot (tmpfiles) | benign, confirmed in r2i |
| B13 | benign upstream: simple-framebuffer prefers memory-region | benign, confirmed in r2i |
| B14 | benign upstream: kauditd callbacks suppressed | benign (expected noise) |
| B15 | benign: Android bootloader reset reason (PS_HOLD reset = every Linux reboot here) | benign (expected noise) |
| B16 | ledger: info lines that only look like errors (IRQ names 'fatal' / 'overflow', SCMI max-rx-timeout, unit descriptions) | benign (expected noise) |
| B17 | benign: desktop deprecation warnings (GTK style-*.css, Adw properties, dbus eavesdropping, udev-settle pulled by upower) | benign (expected noise) |

## 4. Known limits (not bugs of this build)

- Speakers are capped at -12 dB: NXP's speaker protection has no mainline driver.
- No fast charging (SuperVOOC / PPS). Bypass charging is built and reviewed but deferred (your decision).
- No automatic focus (libcamera's simple pipeline); the lens holds stock's start position. libcamera's own data for
  the two sensors comes later (F5); the cameras work with its generic model.
- Analog headsets through the USB-C port need the USB-C jack mode (k5), an opt-in after a test with your headset.
- The deepest SoC sleep state (AOSS sleep) is out of reach on mainline; standby drain is measured by one night
  unplugged.
- Wi-Fi is off in sleep (your decision); the country stays the firmware's US (your decision).
- Firefox decodes video in software; the NPU needs Qualcomm's QNN SDK to run networks.
- The installed system arms no hardware watchdog (a later decision).

## 5. Checks only you can do

| Check | How long | What it shows |
|---|---|---|
| A Wi-Fi reconnect on your network after the F43 fix (loop 3) | a few minutes | the connection survives a drop and a group rekey |
| The first suspend on the installed system, then one night unplugged | a night | sleep without the `*_ignore_unused` flags (every kit still had them) and the real standby drain (target about 1 % per hour or less) |
| A real unplug while the charger input cut holds (H1) | a few minutes | that the cut and its restore behave with a real cable, not only the emulation |
| A wall charger at 9 V after a cut is released (H2) | about 15 min | that charging comes back at the charger's 9 V |
| The charge notifications (H3) | a minute | that the desktop notices read and look right |
| Typing by touch in a dialog (e.g. a password prompt) | a minute | the on-screen keyboard in a modal dialog (F38) |
| Wall chargers (5 V USB-A, USB-C PD, the OnePlus charger) | about 20 min | that the charge-current limits hold off the PC port |
| The pen on the magnet side | about 90 s | pen charging, and whether the boost follows the pen's 10 V request |
| The keyboard cover (pogo) | a few minutes | keys, touchpad, Caps Lock lamp, backlight, wake by a key |
| Wake windows (cover, power key, cable) | about 15 min | the wake sources on real hardware |
| A USB-C monitor or dock | a few minutes | DisplayPort and DP audio |
| USB accessories (keyboard, stick, hub) and a USB headset | a few minutes | host mode (the role switch is automatic) |
| The default apps by finger; colours and sharpness of the cameras; 144 Hz | 30 min | what no automated test can judge |

## 6. Your decisions for the install

Answered: Fedora only for now (dual-boot plan prepared, not done); the write-2 probe C0 first; the GPU microcode from
Fedora's `qcom-firmware`; the camera driver and stock-derived tuning in the private repositories and your image; the
Wi-Fi country US; no Wi-Fi in sleep; bypass charging later; the installed system boots without the `*_ignore_unused`
flags (the install workflow's decision, F24); the USB-C jack mode as an opt-in.

Open (the step that needs the answer in brackets; details in `docs/INSTALL-GUIDE.md` 0.4 and `docs/INSTALL-PLAN.md` 9):
1. (C0) The AVB hash footer on the install U-Boot, signed with the AOSP test key that `vbmeta_b` already chains `boot`
   with - no other partition changes. C0 cannot run without it.
2. (C0 step 0) One read-only RAM boot of the exact install U-Boot before C0 (recommended).
3. (after C0) U-Boot's permanent place: `boot_b` only if C0 shows the boot loader does not count down slot b;
   otherwise `recovery_b` (Fedora from the recovery path, or as the default with one small write to `misc`).
4. Whether an open charging / thermal gate (the wall-charger sitting, the night) blocks the install or only sets
   "charge attended, charge limit on".
5. Held boot-code updates (recommended), Fedora pinned to 44 (recommended), LibreOffice and GNOME Web in the image,
   the skin temperature limit (48 C today or stock's 60 / 61 C with the policy daemon), a day-0 snapshot and home-folder
   copies.
6. A way back to LineageOS after the install, or the return to stock OxygenOS only.
7. Later: a hardware watchdog on the installed system; dual boot (`docs/DUALBOOT-PLAN.md`; decide before write 1).

The writes themselves are yours: Part A (read only) -> C0 (write-2 probe, undone the same day) -> write 1 (`userdata`)
-> write 2 (the boot path), each with its checks, in `docs/INSTALL-GUIDE.md`. Nothing is urgent; the boot loader and
the firmware are never written, so fastboot (Volume Down + Power) always answers.

## 7. Where the evidence is

`docs/guide/RC1-NOTES.md` (RC1 in full), the feature matrix (`docs/FEATURES.md`, the published page), the work log
(`docs/WORKLOG.md`), the run log sets (`docs/tests/area-combo-*`, up to run 112), the install documents
(`docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md`), the review and the guide set (`docs/guide/`), the team plan
(`docs/TEAM-PLAN.md`) and the team's reports with the error ledger's checks (`relay/results/pc-016-020/wf/`). The
rehearsal logs (r2g, r2h, r2i) stay private; their findings are in section 3.

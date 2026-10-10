# Loop 5 notes (9-10 Oct 2026): kernel q89b on v7.3-rc6, iceland-device 0.23, libcamera iceland4

Status of the image: **CANDIDATE, still HELD** (not final). Nothing has been installed on the tablet; every result
below comes from RAM boots, build runs on the tablet and install rehearsals that boot the image from the PC's disk
without writing the tablet. Rehearsal logs stay private (journals and kernel logs carry network names); only their
summary lines are quoted here.

## The candidate build

| Part | Version | Where |
|---|---|---|
| Kernel | q89b = 7.3.0-rc6-iceland-00377-g8e90101870e4 | iceland-linux branch `iceland-7.3-rc6-q89b`, tag `q89b` (patch queue; `main` keeps the rc4 queue 0190) |
| Device package | iceland-device 0.23 (tarball sha256 94e426b0) | `packaging/iceland-device` and `audio/` of this repository |
| libcamera | 0.7.1 iceland4 (recipe SHA256SUMS 73acbeb2, patch 0006 94a3b8bb) | `relay/results/pc-016-020/wf/camfix/cand/loop5/libcamera-rpm-iceland4` |
| Golden image | B run 129 (B runs 127 / 128 kept as records) | private (PC) |

### Kernel q89b

- Base **v7.3-rc6** (a90ee4305c4a; no rc7 / 7.3 tag existed on 10 Oct).
- Our queue 0001-0190 rebased: 322 commits unchanged, 6 dropped - infiniti 0004 / 0005 / 0030 and iceland 0155 /
  0161 are upstream in rc6 (same patch-id), iceland 0077 is superseded by upstream ec0d89150a93.
- 0191-0199 (prepared as q88): camera rotation rear 0 / front 0 (0191), k10 wcd939x impedance under a TX runtime-PM
  reference (0192, F18), fastrpc double-free fix 2159430fe260 (0193), ADSP remote heap no-map (0194), PSCI OSI
  (0195-0199, Ulf Hansson's series). 0200 (3872cc6b9294) is in rc6 itself.
- 46 upstream additions 0201-0252 (dpu / dsi, Bluetooth, ath12k, gcc-kaanapali CX power domain, temp-alarm, ucsi,
  PCI, cpuidle, spi / dma / serial geni, iris, qrtr). The list with sources: iceland-linux `docs/Q89B-QUEUE.md`.
- Taken out after rehearsal r2t (q89):

| Patches | What broke |
|---|---|
| 0202-0205 audioreach / q6apm RFC | every capture read-done rejected ("RD BUFF Invalid payload size 56" x286): 15 / 15 mic opens empty |
| 0244-0245 a6xx CLX | GPU does not start (HFI GX_BW_PERF_VOTE timeout, OOB GPU_SET timeout, gpu hw init -110) |
| 0253 DW9800K driver update | "unknown device id 0xfe" (expects 0xEB): no lens, no camera |
| 0254 wcd939x per-channel switches | suspected of the SoundWire errors; r2u showed they stay without it (not guilty) |

- Build: 0 compiler warnings, W=1 clean on the changed objects, DTB = q89's (rotation 0 / 0, 12 PSCI domain idle
  state references), manifest PASS. Config = q88's + two new rc5 / rc6 defaults (ARM64_ERRATUM_3821522,
  ARM64_WORKAROUND_BROKEN_AMU_CONSTCNT).

### iceland-device 0.23 (from the frozen 0.22 tree)

1. Read failures are unknown, never the benign value (chgsafe G1, patch 5a56ca7f): battery guard, bypass service and
   thermal daemon keep their previous decision when a sysfs read fails (battmgr -110 while the ADSP stalls).
2. Microphone +2 dB: UCM TX_DEC0/1 Volume 96 -> 98 (b9d3077b), matches stock's measured level.
3. Processed microphone (micproc 5f6c8a8f): PipeWire echo-cancel with the WebRTC backend (AGC, noise suppression,
   high-pass) as the default source, the raw source kept, fail-safe to raw; `node.linger = true` so WirePlumber 0.5
   does not destroy the stream before the ALSA microphone appears (found in r2t / r2u, fixed for r2v).
4. Rehearsal guard: the nbd read probe runs in the background, the guard waits at most 20 s and logs "nbd probe stuck"
   instead of hanging in D state until its watchdog reboots the tablet silently (r2o).

Tests: README tests 28 / 0, chgsafe suite 1008 / 0.

### libcamera iceland4

Patch 0006 (F54): the simple pipeline stopped the software ISP before streamOff, so a request could be orphaned and
WirePlumber crashed on camera close. PC harness 800 cycles 0 failures; tablet 40 / 40 cycles 0 fatal (r2u, r2v).

## Sessions of loop 5

| Session | Build | Result (summary lines) |
|---|---|---|
| r2m | q87 + 0.22 | F55: 3 of 10 fresh mic opens empty, one APM timeout (the reason the image is held) |
| r2n | q87 + 0.22 | 50 / 50 fresh mic opens clean; accept 50 / 0; camera orientation wrong (owner) |
| r2o | q87 + 0.22 | F55 reproduced (#8 short, #9 empty at 226-239 s, battmgr -110); later a silent reset = guard nbd probe in D state (fixed in 0.23) |
| r2p-r2s | q87 + 0.22 | camera orientation phase 1: front frame upright unrotated -> rear 0 / front 0 |
| kit 124 | q87 + 0.22 | F55 accept-load replay in a RAM kit: 15 / 15 clean (weak: the kit lacks gnome-software / fwupd) |
| kit 126 | q88 | libcamera iceland4 rpm build on the tablet: rc 0 |
| B runs 127-129 | q89 / q89b + 0.23 | 127: 33 / 0 (after a relay-down attempt 7 / 24); 128: 33 / 0; 129: 0 FAIL (golden) |
| r2t | q89 + 0.23 + iceland4 | FAIL: no camera (0253), mic empty 15 / 15 (RFC 0202-0205), GPU init -110 (CLX) |
| r2u | q89b + 0.23 (no linger) + iceland4 | accept 51 / 0; cameras Rotation 0 / 0; F54 40 cycles 0 close-fatal; F55 replay 15 / 15, 0 APM, 0 battmgr -110; GPU up; NPU up; readfail 69 / 0 |
| r2v | q89b + 0.23 (linger) + iceland4 | F55 replay PASS (second clean); processed mic the default at boot; owner echo test: processed -29.3 dBFS rms vs raw -36.8, the owner heard the processed one better; F54 40 / 40 0 fatal; cameras 0 / 0; Bluetooth works |

Camera orientation: the owner confirmed on the tablet (10 Oct 2026) that the viewfinder and the photos match the
display with q89b's DT fix (rear 0 / front 0). Closed.

## Open items (before the image can be final)

1. A clean fresh-boot rehearsal with the fixed checkers (micgain t tolerance at 2.33-2.50 dB vs 2.0 +- 0.5, parts
   a / e / f with the package's own processed node, the journal query; the r2v mic-fix check).
2. F55: two clean replays on rc6 (r2u, r2v) - not proven fixed (intermittent on rc4: r2m 3 / 10, r2n 0 / 50, r2o 2 / 10).
3. PSCI OSI deep idle: OSI mode is active, but the idle states were not judged because the USB link holds a 2 us PM QoS
   request (dwc3-qcom); needs a cable-out run (owner).
4. SoundWire "clsh detected" and wcd9390 parity errors on the rc6 base (audio works; 0254 not the cause).
5. F18: wcd939x -16 at boot (register 0x3126, two lines, also on rc4); the headset plug test is an owner item.
6. Bluetooth "Frame reassembly failed (-84)" once per setup: cosmetic (the burst after RTS during the WCN7860 baud
   change). Candidate patches in `relay/results/pc-016-020/wf/bt84/` (0001 debug dump, 0002 discard 20 ms after RTS),
   not queued.
7. F55 RFC: a corrected series in `relay/results/pc-016-020/wf/f55rfc/patches/` (0001 the read-done struct as SPF V2,
   56 bytes, + 0002-0005 the RFC with ALIGN 4); not built (q89c, owner's call); the upstream reply draft is not sent.
8. Owner items: F18 headset plug, the cable-out idle test, wall-charger checks W1-W8, the 60 / 61 C skin trip under real
   load. Fedora 45 (release 20 Oct 2026): rebuild and rehearse before lifting the release pin.

## Update 10 Oct 2026 (commit ab): r2w, the final install package, iceland-device 0.24 / 0.25

Status of the image: **still HELD** (candidate; the final install package is built, but nothing is installed and the
install-day steps below are open). The owner runs every write.

### iceland-device 0.24 and 0.25

| Version | Tarball sha256 | What | Status |
|---|---|---|---|
| 0.24 | 63fdd58a | 0.23 + `alsa-ucm` held in fedora / updates / updates-testing (our UCM includes its shared files); `80-iceland-kernel.conf` `best=False` + `skip_broken=True` (a held libcamera makes dnf skip the pipewire-plugin-libcamera update instead of failing the transaction: the plug-in pins pipewire-libs = V-R); `/usr/bin/iceland-update-check` (read-only: offered / held back / skipped); tests/test_update_policy.py (37 checks). README tests 29 / 0, chgsafe 1049 / 0 | **in the image**, rehearsed in r2w |
| 0.25 | 1bbea0c6 | 0.24 + the processed-microphone off switch: the module carries `condition = [ { iceland.mic-processing = !false } ]` (PipeWire 1.6.9 conf.c), so a drop-in `context.properties = { iceland.mic-processing = false }` in `/etc/pipewire/pipewire.conf.d/` (all accounts) or `~/.config/pipewire/pipewire.conf.d/` (one account) turns it off; the drop-in header's wrong "empty context.modules" advice corrected. README 29 / 0, chgsafe 1052 / 0 | **NOT rehearsed**; meant to ship after the install as the first update through `iceland-local` (this also exercises update U1) |

`packaging/iceland-device` of this repository is now the 0.25 tarball's content; the image carries 0.24.

### B run 130 and the confirmation rehearsal r2w (q89b + 0.24 + libcamera iceland4)

- B run 130: 33 PASS, 0 FAIL; golden committed (175 086 overlay blocks).
- r2w, session clean (orderly end, PSHOLD / SYSOK, postsession rc 0):
  - INSTALL-ACCEPT 51 PASS, 0 FAIL, 0 CHECK; F55 replay PASS (the third clean replay in a row: 0 q6apm timeouts,
    0 Format block, 0 battmgr -110); readfail 69 / 0; Bluetooth works (3 devices; -84 once per setup).
  - Owner echo: processed -31.5 / raw -42.1 dBFS rms (processed default at boot); micgain v PASS, e PASS (ERLE
    20.8 dB, 0 clips / dropouts, CPU 7.4 %), f PASS (fail-safe: backend missing -> raw default, 0 processed nodes).
  - Update policy (part upd): all PASS - best=0, skip_broken=1, alsa-ucm and libcamera* held, the helper installed,
    the UCM files owned only by iceland-device.
  - Cameras Rotation 0 / 0.
  - Checker level: micgain t "FAIL" with the delta 2.03 dB inside +-0.75 - another condition fails (the tone is
    about 1 dB above the noise floor: noise-limited) -> checker fix; part a CHECK: processed louder, but its spread
    14.1 dB vs raw 6.2 dB (the AGC ramps up on loud speech) -> review the AGC settings.

### The final install package (PC, private)

Built 10 Oct 2026 07:25-07:32 with `wf/final/tools/run-final.sh q89b-024-b130 130 FINAL` from the B run 130 golden
(body sha256 6e54a84d99a01abf...). The package stays in WSL (`~/mainline/build/wf/final/q89b-024-b130/`): the image
holds this tablet's firmware, its stock Bluetooth address and its thermal model, so the images are never committed.
Its `MANIFEST.json`, `VERIFY.txt` and `SHA256SUMS` are in `relay/results/pc-016-020/wf/final/q89b-024-b130/`, the
tooling in `.../wf/final/tools/`, the owner's guide in `.../wf/final/GUIDE.md`, the reviewed flash script in
`.../wf/final/flashguide-r2/` (63 PASS / 0 FAIL with fake fastboot / adb).

| File | Bytes | sha256 |
|---|---|---|
| `fedora-iceland.sparse.img` (Android sparse v1, unpacks to 237 159 641 088 = userdata) | 4 865 088 816 | 44e7853423414294268f40b3f283a09a921b01bae990711a12f5f5f014b686b2 |
| `u-boot-iceland.img` (install build, no AVB footer; RAM boot only) | 536 576 | fb2bed8d947e3084d34d0934bef448d506f34412b5b16ed4e3c332a16fe95318 |
| `MANIFEST.json` (status FINAL) | 8 189 | 0c52f3b13b19f6bacdc2d0b2a5d68f500dea514bc2cce157e621f68c1e9a52b2 |
| `VERIFY.txt` | 8 910 | 1328665b41eaabe9908639004cae2ead240a6a595f69f733d285c99585d9acec |

Offline content check (`verify-image.sh`, read-only): **84 PASS, 0 FAIL** - the 80 checks of the B129 dry run
(only kernel-iceland, every exclusion file, the fwupd guard, node.linger, UCM 98, SELinux enforcing; no rehearsal
arguments, machine-id uninitialized, no ssh keys / Wi-Fi networks / pairings / user account, no network name on the
raw disk) + four for 0.24 (alsa-ucm in all three hold sections, best=False, skip_broken=True,
`/usr/bin/iceland-update-check` owned by iceland-device). iceland-device 0.24: all 95 packaged files equal the
package's digests. MANIFEST evidence: B run 130 `B-RUN: 33 PASS, 0 FAIL`, r2w `INSTALL-ACCEPT: 51 PASS, 0 FAIL, 0 CHECK`;
the kernel rpm file's header equals the installed one. The B129 dry run (NOT FINAL) was deleted after this package
verified.

### The update policy (installed system, iceland-device 0.24)

- Fedora 44 updates as normal (GNOME Software / `dnf upgrade`); before every transaction a read-only btrfs snapshot of
  the root (3 kept) with a GRUB "Roll back" entry each; `/home`, `/var`, `/boot` are not rolled back.
- Held from Fedora: all Fedora kernels and their pieces, dracut rescue / generic, akmods / dkms, fwupd's capsule
  parts, bootupd, systemd-boot, unsigned shim, U-Boot images (`80-iceland-kernel.conf`, global); from the Fedora
  repositories `grub2-*`, `shim-*`, `linux-firmware*`, `*-firmware`, `libcamera*`, `iio-sensor-proxy*`, `hexagonrpc*`,
  `libssc*` and (0.24) `alsa-ucm` (`50-iceland-fedora-hold.repo`). Protected: iceland-device, grub2-efi-aa64, shim-aa64.
- dnf5 `best=False`, `skip_broken=True` (0.24): a package that cannot update because of a hold is skipped, not a
  failed transaction; `iceland-update-check` shows what is offered, held back and skipped.
- Release pinned to 44 (`51-iceland-fedora-44-pin.repo`), the system upgrade blocked by polkit; Fedora 45 only after
  its own rehearsal (release target 20 Oct 2026).
- fwupd stays, with the UEFI capsule, SCSI and UFS plugins disabled.
- Kernels and the device package come only from the tablet's local repository `iceland-local`, filled by
  `iceland-repo-sync` (every rpm checked against the repository's SHA256SUMS); 3 kernels kept, a new kernel becomes
  the default only after it started once. The first such update is meant to be iceland-device 0.25.

### Kernel queue

iceland-linux branch `iceland-7.3-rc6-q89b`: follow-up commit tagged `q89b-1` - patches 0195-0199 (PSCI OSI) now carry
their upstream author (Ulf Hansson <ulf.hansson@oss.qualcomm.com>, from 81f1099186fd, 9e8dff8e0978, 2224d686e788,
6d3080bfe007, 65705b18162b) instead of "From: mzak"; contents equal upstream (patch-id), the trailers unchanged. The
applied tree is unchanged (TREE_AFTER_0002_iceland f1c7fa5d8607); tag `q89b` stays on the tested commit.

### Open items (after r2w)

1. **F54 camera cycles in r2w**: cycles 1-11 "stream no", 12-40 stream (29 / 40; r2v 40 / 40, r2u 39 / 40), 0 fatal:
   the first camera starts right after the orientation test did not stream for about 11 cycles -> investigate (camera
   start right after camrot phase 2 / the sensor hub?).
2. **f18-wcd**: "wcd939x ASoC error (-16)" at register 0x3125, 13 lines at 15 s (old F18 class; r2u 2, r2v 0).
3. **SoundWire** "clsh detected" 4 / wcd9390 parity 2 on the rc6 base (audio works).
4. **AGC spread** of the processed microphone (14.1 dB vs raw 6.2 dB) and the noise-limited micgain t checker.
5. **Install-day decisions and steps**: C0 (the write-2 probe) has never run; owner decisions 1 (AVB footer on the
   install U-Boot) and 3 (`boot_b`; `recovery_b` is not scripted); Part A step 6 and the AVB proof redone on the day.
6. **Update / rollback rehearsals** (U1-U3, R1b, R2b, R3, R4) not run for this kernel / package set; the return to
   stock (`flash super`, `-w`) only dry-run.
7. **Flash-script gaps** (flashguide-r2, not fixed): Write1 accepts `recovery_b` but Write2 refuses it; a 3800 mV
   battery reading stands in for "above 60 %"; the image is hashed and then re-read by path over `\\wsl.localhost`, so
   no build may run during the install.
8. PSCI OSI deep idle not judged (USB 2 us QoS; needs a cable-out run); the kernel rpm was rebuilt with the same NVR
   (bump the release next time); Bluetooth -84 cosmetic (bt84 candidates not queued); the corrected F55 RFC unbuilt.

## Update 10 Oct 2026 afternoon (commit ac): the install U-Boot, C0 #1-#4, test candidate q89c-tb, kit 132

### The install U-Boot reset loop and its fix (iceland-u-boot 32c967f, patches 0008-0010)

- **C0 #1** (12:4x, the final package's install U-Boot fb2bed8d, AVB-footered c39a24e6, in boot_b): FAIL. After one
  `fastboot reboot` the tablet showed the unlocked warning and U-Boot's text and restarted about 7 times by itself;
  ABL counted slot b from 7 down to 0 and marked it unbootable. UndoBootB at once (original boot_b 254ad805): Android
  back with its data, flags exactly as before. Lesson: the RAM boot of the exact install U-Boot (guide step C0.0) had
  been skipped - never skip it.
- **Cause**: the install U-Boot could leave by itself (a power off with the cable in powers the tablet on again; a
  reset is a new boot); each restart was a counted boot of slot b. **0008**: never reset or power off - a HOLD loop
  that waits 60 s and starts fastboot again forever, `CONFIG_PANIC_HANG`, one `scsi scan`, no `efidebug` usage text.
  RAM tests: the old U-Boot fb2bed8d and the fixed one (2bfba5f2) both PASS (no reset from ABL's fastboot).
- **C0 #2** (13:55, 0008, footered 8729065f): U-Boot runs from boot_b and HOLDS (no loop), but no USB: "dwc3 ...
  Reset Timed Out / failed to initialize core" - in a normal boot ABL does not start USB (it does only in its own
  fastboot, where every RAM test had started). **0009**: U-Boot powers USB itself as Linux does - TCSR USB2 clkref,
  PHY supplies L4F / L1D over RPMh, the PMIH0108 eUSB2 repeater on the second SPMI bus (L15B / L5B), USB30 master
  200 MHz. RAM T-a v1 (usbcold diagnostic) FAILED only on its own diagnostic step (both reset lines left asserted);
  T-a v2 PASS (fastboot from the cold state after 4 s), T-b v2 PASS (install build).
- **C0 #3** (16:17, 0009, footered cb1b707e): U-Boot fastboot enumerated on the PC 7 s after a normal boot from boot_b.
  Leaving it with the owner's keys cost 5 tries (retry 7 -> 2). **0010**: `fastboot reboot-bootloader` writes the
  reboot reason 2 into PMK8850 SDAM 2 byte 0x48 bits 1-7 (the cell of Linux's nvmem-reboot-mode and of Android's
  `adb reboot bootloader`), reads it back, resets only after the OKAY. RAM T-d PASS (ABL fastboot after 15 s, flags
  unchanged).
- **C0 #4** (17:41, v3 = 0008-0010, footered 4955ee98): PASS - boot_b -> U-Boot fastboot after 7 s (console clean)
  -> `fastboot reboot-bootloader` -> ABL fastboot after 14 s with no key press; slot b retry 7 -> 6 (only the U-Boot
  boot counted); UndoBootB -> LineageOS on slot b. Every C0 wrote only boot_b and restored it the same day.
- v3 images (sha256): install 979b40767afba37367354cfe047994acff10b21831f7664933ee30c7dc89f94c, rehearsal
  8a1b011cea5d16a82ca96eb3964b222300f8509f6bbd7962f073f6d938c3c096, usbcold (diagnostic, RAM only)
  778e979cbdbb51293b5b6a316e79acd1c7e564563a7eb4fe3f9c7a32a53e6dc8; build checks 189 / 0. The images stay on the PC;
  the queue, tooling and probes are in iceland-u-boot.
- The C0 run scripts are kept as examples under relay/results/pc-016-020/wf/final/flashguide-r2/examples/
  (`c0-loop.ps1` for C0 #3, `c0-v3.ps1` for C0 #4; no webcam). flash-iceland.ps1 now: Write1 refuses a decision 3
  other than boot_b (recovery_b is not scripted), and the G1 backup check reads `SHA256SUMS-supplement.txt` (two GPT
  partitions are named last_parti; the LUN-specific copies `<name>-<lun><index>.img` are preferred). Tests 63 / 0.

### Test candidate q89c-tb + iceland-device 0.26 (NOT the shipping build)

- Kernel q89c-tb = q89b + 0255-0265 from tb323fu-linux (Lenovo Legion Tab Gen 5, same SoC; author Joonhoe Kim):
  iceland-linux branch `iceland-7.3-rc6-q89c-tb` (d2e2078), tag `q89c-tb`. tb 0036 dropped (our f_ncm fix
  covers it), tb 0098 ported. Six of the patches carry no Signed-off-by of their author: test use only.
- iceland-device 0.26 (4d9512f4) = 0.25 + sensor stop across suspend (system-sleep hook iceland-sensors), USB / PCIe
  wakeup off (72-iceland-nowake.rules), systemd watchdog 30 s, dma-heap rule, GPU floor 160 MHz (= the lowest OPP,
  no change). A CANDIDATE: packaging/iceland-device stays 0.25; 0.26 is in relay/results/pc-016-020/wf/tb5kit/cand026
  with p1-026.py, mkp1manifest-026.py and manifest-p1-0.26.json (README tests 30 / 30, charging-safety 1093 / 0).
- **B run 131**: golden committed (B130 golden backed up first).
- **r2x** (rehearsal, 15:38): ABORTED by a tablet reset at 15:58: the test suspended the tablet (sensleep 30 s
  s2idle) with its root on NBD; it never resumed, bootloader log "Reset by PSHOLD, Hard Reset". Same signature as
  R2-final: **house rule - no suspend in a rehearsal session** (the r2y test set refuses suspend, pm_test and
  the owner windows on a rehearsal boot, `iceland.rehearsal=`). Not the kernel (no q89c-tb patch touches audio or the NBD path; config,
  DTB and command line = q89b), not 0.26. The audio DSP stall seen before it (APM CMD timeout after the mic part
  restarted PipeWire) is the old F55 family. Before the abort: btaddr same x3, qrtr x2, dp-rpm, wifi-refill, dmaheap,
  gpu-opp PASS. Parser fixes for gpu-up, the session user and wifi-scan are in the r2y set.
- **Kit 132** (RAM root, 17:15): pkg / kernel / wake rules PASS (USB + PCIe wakeup off; charger, cover, power key,
  RTC armed); pm_test freezer / devices / platform / full PASS (platform: dpu "enc35 timeout" / "frame done timed out"
  lines); **9 suspends, 9 success, 0 fail**; gdsc 0256 / 0257 PASS; ucsi 0258 PASS; sens-assign PASS; owner windows:
  cable out PASS (4 s), cable in PASS, cover CHECK (the power key was pressed in the window). ufs 0255 CHECK (no error
  or hung task under 2.28 M random reads, 317 query rounds and 3 suspends, but no clock-scaling transition). **FAIL
  sens-boot / sens-hook / sens-resume**: iio-sensor-proxy stuck "activating", no accelerometer after resume.
  Hardware sleep counter +0 in both measured suspends.
- **r2y** (rehearsal without suspend): stopped by the owner at 17:26 before results.

### Open items (after commit ac)

1. **Sensors on q89c-tb + 0.26**: iio-sensor-proxy stuck activating, no accelerometer after resume - a q89c-tb patch
   or the 0.26 sleep hook (not yet known); q89b + 0.24 is not affected.
2. **ufs 0255 not exercised**: no devfreq transition in kit 132; needs a load that makes the UFS scale.
3. **Hardware sleep +0** in kit 132's suspends (deep sleep not reached or not counted on the RAM kit).
4. **Cover wake** retest without a key press (kit 132 window was CHECK).
5. **Slot marking from Fedora**: after the install, `qbootctl -m` (Fedora package) marks slot b successful; U-Boot
   writes no GPT. Design only; the install-flow rehearsal with the v3 U-Boot is still to do.
6. **Watchdog vs suspend**: qcom_wdt stops only in suspend_late, so a device-suspend stall of about 30 s could be
   bitten by the 0.26 30 s watchdog - check before 0.26 ships.
7. r2y remainder, the tb323fu "Try" items and the SuperTurtleDev items: the next kit / rehearsal (r2z).

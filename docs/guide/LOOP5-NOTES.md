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

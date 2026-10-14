#!/usr/bin/env python3
# Docs workflow, 3 Oct 2026: writes wf/docs/RELEASE-NOTES-draft.md (committed as docs/RELEASE-NOTES.md) for release
# candidate 1 (kernel q85 + iceland-device 0.19, rehearsal r2i). The facts are those of docs/guide/RC1-NOTES.md
# (environment variables of the same name override them for a later build). The known-issues tables come from
# tools/known_issues.py (the ledger's G3 check of r2i, fix records, verdicts).
# Status 14 Oct 2026: the facts below are those of release candidate 1 (3 Oct 2026); the output is a historical document.
# Its inputs are private build folders, so the script cannot run from this repository. The installed system (13 Oct 2026)
# is described in docs/INSTALL-GUIDE.md and docs/guide/04-BUILD-YOUR-OWN.md.
import os, subprocess, sys

H = os.path.expanduser("~/mainline/build/")
OUT = H + "wf/docs/RELEASE-NOTES-draft.md"
F = {
    "KERNEL": "7.3.0-rc4-iceland-00324-ge0373b2308fc",
    "QUEUE": "0001-0188 (iceland-linux `a9b55d4`, verified against the built tree)",
    "K2": "kernel-iceland-7.3.0~rc4.iceland.00324.ge0373b2308fc-1.fc44",
    "K3": "kernel-iceland-7.3.0~rc4.iceland.00324.ge0373b2308fc.1-1.fc44",
    "DPKG": "0.19",
    "R2I": "INSTALL-ACCEPT 46 PASS, 0 FAIL, 0 CHECK; the klog probes 14 / 14 PASS; the debugger's suite 32 PASS, 2 FAIL, 3 CHECK, 1 SKIP",
}
F = {k: os.environ.get(k, v) for k, v in F.items()}
KI = subprocess.run([sys.executable, H + "wf/docs/tools/known_issues.py"], capture_output=True, text=True, check=True).stdout
NIGHT = subprocess.run([sys.executable, H + "wf/docs/tools/known_issues.py", "--night"], capture_output=True, text=True, check=True).stdout

T = f"""# OnePlus Pad 4 - Fedora 44 GNOME: release notes of release candidate 1 (RC1)

3 Oct 2026 (docs workflow). The full RC1 notes - what each run proved, the ledger's FAILs explained, the known issues
and the owner's checks - are in `docs/guide/RC1-NOTES.md`; this page is the short version. **Nothing has been
installed on the tablet**: every result below is from RAM boots (test kits), from build runs on the tablet, and from
the install rehearsal, which boots the real install image from the PC's disk without writing the tablet. (At RC1 nothing
had been installed. The owner installed Fedora 44 on 13 Oct 2026, after the final rehearsal r158; section 6 is the
decision that was taken then.)

## 1. The build

| Piece | Version / state |
|---|---|
| Kernel | Linux 7.3-rc4 + 138 SM8850 base patches + the Pad 4 queue {F['QUEUE']}; kernel q85, release `{F['KERNEL']}` |
| Kernel package | `{F['K2']}` (K2) and its twin `{F['K3']}` (K3) for the update rehearsal; installonly, three kept; depmod outputs ghosted |
| Device package | iceland-device {F['DPKG']}: the battery guard v3.1 with the charger input cut, PipeWire 1.6.8 or newer (F1), Wi-Fi regulatory domain US (F11), no TPM modules in the initramfs (F10; the tablet has no TPM), the UFS disks' scheduler set one disk at a time (F14), a kernel command line without `clk / pd / regulator_ignore_unused` (F24), the camera tuning |
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
| rehearsal r2i | the RC1 install image booted from the PC's disk | **{F['R2I']}**; Fedora's first-boot setup on the screen |

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

{NIGHT}
### The findings and their status in release candidate 1

{KI}
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
(`docs/WORKLOG.md`), the install documents (`docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md`), the review and the guide
set (`docs/guide/`) and the team plan (`docs/TEAM-PLAN.md`). The run log sets, the team's reports and the error ledger's
checks are not published. The rehearsal logs (r2g, r2h, r2i) stay private; their findings are in section 3.
"""
open(OUT, "w", encoding="utf-8", newline="\n").write(T)
print("wrote", OUT)

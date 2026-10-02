# 01 - Overview: mainline Linux and Fedora on the OnePlus Pad 4

State: 2 Oct 2026, about 22:30. Sources: `iceland-mainline/docs/FEATURES.md` (generated from
`docs/features/features-data.py`), `WORKLOG.md` entries 1-44, `docs/INSTALL-PLAN.md`, the workflow reports in
`~/mainline/build/wf/`. Every "proven" below names the test run that showed it (`area-combo-NN` = kit run NN; the log
sets are in `iceland-mainline/docs/tests/` and `~/mainline/build/area-combo-NN/`).

## 1. What the project is

The project brings an upstream Linux kernel and a normal desktop distribution to the **OnePlus Pad 4** tablet:

| Item | Value |
|---|---|
| Device | OnePlus Pad 4, model OPD2514, board codename **iceland** |
| SoC | Qualcomm Snapdragon **SM8850P**: "Kaanapali" in mainline Linux, "canoe" in Android and ABL |
| Kernel | Linux **7.3-rc4** + 138 SM8850 base patches (the OnePlus 15 "infiniti" port, same SoC) + **174 Pad 4 patches** (`iceland-linux` a88cf03, `patches/0002-iceland/0001-0174`) |
| Boot loader for Linux | **U-Boot** v2026.10-rc5 + patches (`iceland-u-boot`), started by the tablet's own boot loader (ABL) |
| Distribution | **Fedora 44 Workstation (GNOME 50)**, aarch64. The owner chose it on 28 Sep 2026 |
| Device package | `iceland-device` 0.17 in the repository. 0.18 adds the install parts, the GPU-ISP hold and "keep the CDSP running"; it is built on the tablet in the rehearsal's build runs (93, 94), and not committed yet |
| How it is tested | **RAM boot only.** The PC sends a boot image over USB (`fastboot boot`). The tablet runs Linux from memory and returns to Android at the end. Nothing has ever been written to the tablet's storage by this project |
| Planned | A permanent install into the tablet's `userdata` partition. It is designed to be unbrickable and restorable, and runs only with the owner's explicit OK for each write (see `03-BOOT-AND-PARTITIONS.md` and `07-INSTALL-REVIEW.md`) |

Three private GitHub repositories hold the work:

| Repo | Content |
|---|---|
| `iceland-linux` | the kernel patch queue, `kernel.pin`, the config fragments, `scripts/prepare.sh` and `build.sh`, the Fedora kernel package spec |
| `iceland-mainline` | plans, knowledge base, feature matrix, test log sets, firmware manifest (names only), device package, sensor packages, the RAM-kit tools |
| `iceland-u-boot` | the U-Boot patch queue, `uboot.pin`, build scripts, the diagnostic environments |

### The software stack in one picture

```
GNOME 50 (Wayland, mutter) - GNOME Camera (Snapshot), GNOME Web, Firefox, Settings (power modes, charge limit)
PipeWire + WirePlumber (>= 0.5.18 with the camera rule) | libcamera 0.7.1 (simple pipeline, GPU soft ISP, our 3 fixes)
iio-sensor-proxy 3.9 (patched) <- libssc <- hexagonrpcd   | UPower (charge thresholds) | tuned-ppd (power modes)
Mesa 26.x: freedreno (OpenGL / ES), turnip (Vulkan)        | GStreamer v4l2 (Iris video; one colorimetry patch)
iceland-device: udev rules, ALSA UCM + AudioReach topology, battery guard, thermal policy, systemd drop-ins, update rules
Fedora 44 user space (systemd, dnf5, SELinux targeted)
Linux 7.3-rc4 + infiniti (138) + Pad 4 queue (174): DRM/MSM, ath12k, qcom_battmgr, remoteproc, Iris, CAMSS, ...
U-Boot (EFI) <- ABL <- XBL / firmware (stock, untouched)
Tablet firmware (GPU zap, video, ADSP / CDSP, Wi-Fi, BT, touch, sensor-hub files): extracted from the tablet, private
```

## 2. What works today

The feature matrix has **80 rows: 61 working, 12 in progress, 5 not started, 2 not planned** (FEATURES.md, page
v41, 2 Oct; about 145 test runs since 28 Sep).

| Area | Working / rows | Highlights (run that proves it) |
|---|---|---|
| Boot & platform | 6 / 9 | U-Boot from RAM, Linux through EFI, Fedora 44 + GNOME Shell 50 from RAM, stable sessions (the USB freeze is fixed by queue 0063) |
| Display & input | 9 / 11 | 3392x2400 dual-DSI panel at 30-144 Hz (area-display-7), touch, pen input, lid switch, keys, auto-rotate (area-combo-23..26) |
| Graphics & compute | 7 / 7 | Adreno 840 with Mesa (OpenGL ES 3.2, Vulkan 1.4), hardware video decode bit-exact (H.264, HEVC, VP9 incl. 10-bit, AV1) and encode, the NPU's processor (CDSP) runs unsigned test programs (area-combo-1/-2) |
| Audio | 7 / 9 | six speakers in stereo, two microphones at stock's level (area-combo-1..3), GNOME volume and input sliders |
| Connectivity | 5 / 8 | Wi-Fi 2.4 GHz connected; 5 GHz networks found (queue 0066-0068); Bluetooth with its own address; USB device mode |
| Power & charging | 5 / 8 | battery data and time estimate, a battery safety guard with stock's limits, a charge limit (80 / 85 %: GNOME's "Preserve Battery Health" and "Maximize charge" confirmed by the owner in run 95), low-battery current limiting as stock (area-combo-35/-37) |
| Thermal | 6 / 7 | CPU, GPU, skin, XO, PMIC-alarm and NPU cooling with stock's trips and maps (area-combo-38..41, -75) |
| Sleep & power saving | 5 / 8 | s2idle suspend (37 cycles, area-combo-12/-14/-15), CX collapse in 95-98 % of a sleep (area-combo-64, -92), per-rail power telemetry |
| Sensors & camera | 3 / 4 | accelerometer, compass, light / proximity through the ADSP sensor hub; both cameras at 30 fps with GNOME Camera (area-combo-52), rear flash as torch |
| Software & packaging | 8 / 9 | kernel package, device package, local update repository, the stock-values audit (1,249 values), upstream fixes, hardware inventory |

**Measured battery life** (area-combo-69; battery 53.8-56.7 Wh; screen at 50 %): idle with the screen on at
60 Hz 3.37 W (about 16-17 h); light use 3.85 W (about 14-15 h); 1080p hardware-decoded video 3.58 W (about 15-16 h);
all cores busy 8.1 W falling to 7.7 W (about 7 h); screen off but awake 0.64 W (about 3.5 days). 120 Hz costs
0.7 W more than 60 Hz. Standby asleep has not been measured yet: it needs one night unplugged with the owner.

## 3. What is not done, and what is not possible

| Item | State | Why / what is missing |
|---|---|---|
| Fedora installed on the tablet | not started | the owner runs every write. The rehearsal's build run passed (area-combo-93, rerun -94 with device package 0.18); one more B run carries the round-6 fixes. R1 stopped in the rehearsal U-Boot; the fix is verified 15 / 15 in a U-Boot sandbox; next on the tablet: a "not gzip" test head, the B run, R1 (`docs/INSTALL-RERUN-COMMANDS.md`). AVB proven on the PC: the U-Boot for `boot_b` needs an AVB footer and has one. Owner decision: first a "write-2 probe" (U-Boot into `boot_b` while Android's data is intact, then undone). It also measures whether ABL counts down boots of `boot_b` (the flash resets the slot's flags; only Android marks a slot successful); if it does, U-Boot's permanent place becomes `recovery_b` (owner's decision) |
| Dual boot with Android | not started | owner decision (2 Oct): Fedora-only for now; a dual-boot plan with the best safety precautions is being prepared (`wf/install/DUALBOOT-PLAN.md`) |
| Speaker protection | not started | NXP's TFA protection runs in a closed protocol. The volume stays capped at -12 dB |
| Headset over USB-C | not started | USB headsets use the normal USB audio driver. Analog headsets need the codec's audio-accessory mode. USB audio offload is not possible on mainline for this chip |
| USB host / OTG | not started (untested) | the roles switch by themselves (dual-role controller, UCSI). Every test kit uses the port for the PC link, so no accessory has been tried |
| Wi-Fi 5 GHz connect, 6 GHz | in progress | 5 GHz networks are found; connecting needs the owner's password; the regulatory country is not set ("Failed to set the requested Country regulatory setting") |
| PCIe link at suspend | diagnosis running | "Timeout waiting for L2 entry" at every suspend. The hwfix workflow found the cause: ath12k resets the Wi-Fi chip at suspend, and the reset chip never answers the PCIe power-down handshake. Diagnosis kit run 97 (test-only switch) is running |
| Bypass charging | in progress | stock-like "charging off, input kept" inside the battery guard, with a GNOME Quick Settings toggle (hwfix workflow, topic C) |
| Pogo keyboard, pen charging, wake by cover / charger | in progress | drivers queued and proven without the accessory; one short session with the owner's hands remains |
| Deep sleep (AOSS sleep) | in progress | CX collapse is reached. The deepest SoC state is out of reach on mainline: the always-on processor names the secure processor, which has no mainline driver |
| Skin temperature policy | in progress | the policy daemon exists (device package 0.17). Moving the kernel's skin loop from 48 C to stock's 60 / 61 C is the owner's choice |
| Autofocus | open | the focus motor works, but libcamera's simple pipeline has no autofocus; the lens is held at stock's start position |
| Fast charging (SuperVOOC / PPS) | not planned | OnePlus-proprietary charge pumps and protocol |
| Haptics, modem, NFC, fingerprint, SD card | not on this tablet | the parts are absent (hardware inventory `wf/hwinv`) |

## 4. Safety principles (non-negotiable)

These are the owner's rules. Every procedure in these documents follows them.

1. **RAM boot only, until the owner says otherwise.** Tests use `fastboot boot` (the image lives in RAM). Nothing is
   flashed, erased, formatted, wiped, unlocked or relocked. No slot is switched. A reboot always returns to Android.
2. **No write without the owner's explicit OK, one write at a time.** The planned install writes exactly two
   partitions (`userdata` and one boot partition). Each write has its own undo and its own recorded checksum.
   Project scripts never contain `fastboot flash`, `erase`, `format`, `set_active`, `-w` or `flashing`. The only
   exception is the owner's own return-to-stock script, which the owner runs and confirms.
3. **Never write the boot firmware or the per-device data.** The tablet cannot be unbricked at home: there is no
   public emergency-download loader for it. As long as XBL / ABL and their partitions are untouched, fastboot
   (Volume Down + Power) always answers.
4. **Charging safety first.** Every current, voltage, power and temperature limit is stock's value or lower. Values
   come from the Pad 4's own stock sources (device tree, firmware logs, LineageOS logs), never from another device.
5. **Tests are automated and short** (at most about 10 minutes on the tablet). Anything that needs the owner's hands
   or eyes is deferred and listed.
6. **"Hold the tablet" stops every tablet action at once.** And since 2 Oct: **ask the owner to connect the tablet
   and wait for the owner's go before any tablet run.** The tablet is unplugged while it recharges, so no chain may
   sit waiting for adb.
7. **Privacy.**
   - Proprietary firmware, stock tuning and calibration files, the owner's backup, camera traces and the private
     camera driver are never committed or published.
   - The serial number, MAC / Bluetooth addresses and network names are masked.
   - The repositories are private; nothing is sent upstream without the owner's OK.
8. **Firmware is never distributed.** Every user extracts it from their own tablet, read-only.

## 5. Reading order

| You want to ... | Read |
|---|---|
| understand the hardware as Linux sees it | `02-HARDWARE.md` |
| understand how the tablet boots and what the install changes | `03-BOOT-AND-PARTITIONS.md` |
| build your own kernel and RAM-boot it | `04-BUILD-YOUR-OWN.md` |
| use another distribution (Debian, Arch, postmarketOS-style) | `05-PORTING-TO-OTHER-DISTROS.md` |
| know how the project got here, and its lessons | `06-PROCESS-HISTORY.md` |
| review the install before any write | `07-INSTALL-REVIEW.md`, then `docs/INSTALL-PLAN.md` and `docs/INSTALL-GUIDE.md` |
| look up a term | `GLOSSARY.md` |
| find a file | `INDEX.md` |

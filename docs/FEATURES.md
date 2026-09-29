# OnePlus Pad 4 mainline: feature matrix

Status 29 Sep 2026 (after the audio area closed (mic hiss a known issue) and the touchscreen confirmed by you; area-by-area campaign, relay 019; next: the display glitches and screen, then GPU and NPU). Everything is tested by RAM boot; nothing is installed on the tablet yet.
Legend: ✅ working · 🟡 in progress · ⬜ not started · ❌ not planned. Sorted by functionality.
Totals: 29 working, 15 in progress, 22 not started, 2 not planned (68).

## Boot & platform (5/8 working)

| Feature | Status | Notes |
|---|---|---|
| U-Boot booted from RAM (display, USB fastboot, UFS read, EFI) | ✅ Working | Nothing written to the tablet; fastboot flashing compiled out |
| U-Boot boot setting for single or dual boot | ✅ Working | Boots a “fedora” partition if present, else userdata |
| Linux 7.3-rc4 through EFI | ✅ Working | Queue 0001–0045 + infiniti |
| Fedora 44 running from RAM | ✅ Working | systemd as PID 1; packages through the PC |
| GNOME Shell 50 | ✅ Working | Autologin session in RAM |
| Firmware extractor (tablet's own partitions, read-only) | 🟡 In progress | vendor/odm inside “super” not mapped yet |
| Fedora installed on the tablet | ⬜ Not started | Final step; needs your decisions and OK |
| Dual boot with Android | ⬜ Not started | Planned; recovery re-flash helper ready |

## Display & input (5/10 working)

| Feature | Status | Notes |
|---|---|---|
| Native display 3392×2400, dual DSI + DSC | ✅ Working | Boot splash handed over to MSM DRM |
| Refresh 30 / 60 / 90 / 120 / 144 Hz | ✅ Working | 144 Hz after the DPU clock fix |
| Backlight | ✅ Working | Brightness curve still being checked against stock |
| GNOME pink / blocky glitches | 🟡 In progress | Isolation plan sent (relay 011); Mesa side checked; first display run next |
| Touchscreen | ✅ Working | Confirmed by you: GNOME used by touch during the audio runs |
| Pen | 🟡 In progress | GNOME accepts it; strokes not confirmed |
| Lid switch | 🟡 In progress | Closing not tested |
| Power and volume keys | ✅ Working | Power key also wakes from sleep |
| Pogo keyboard | ⬜ Not started | Private UART protocol |
| Auto-rotate | ⬜ Not started | Needs the sensors |

## Graphics & compute (2/6 working)

| Feature | Status | Notes |
|---|---|---|
| Adreno 840 GPU, GLES 3.2 | ✅ Working | kmscube 120 fps, glmark2 1836 |
| GNOME and Wayland drawn by the GPU | ✅ Working |  |
| GPU correctness, WebGL, 30-min stress | ⬜ Not started | Relay 012 |
| Vulkan | ⬜ Not started | Mesa 26.2.3 has turnip for the Adreno 840; vulkaninfo/vkcube check in the display run |
| Hardware video decoding | ⬜ Not started | Driver in the tree; firmware known |
| NPU (Hexagon on the CDSP) | ⬜ Not started | Off by default; bring-up in relay 012 |

## Audio (5/8 working)

| Feature | Status | Notes |
|---|---|---|
| DSP audio + sound card | ✅ Working |  |
| GNOME shows speakers and microphones | ✅ Working | Fixed: stray mixer route; appears on a fresh boot |
| Microphones (2) | 🟡 In progress | Known issue: a steady hiss 25–35 dB above stock, so GNOME’s meter barely moves; speech gets through |
| Speakers (top pair) | ✅ Working | You heard them (S17), raw ALSA and through GNOME/PipeWire; kernel fix only |
| All six speakers in stereo | ✅ Working | You heard all six from GNOME’s Sound test, both sides correct |
| Speaker volume cap | ✅ Working | −12 dB cap enforced by the kernel (queued 0051); stock value still to find |
| Speaker protection (NXP container) | ⬜ Not started | Closed firmware; volume stays capped |
| Headset over USB-C | ⬜ Not started | No 3.5 mm jack |

## Connectivity (3/7 working)

| Feature | Status | Notes |
|---|---|---|
| Wi-Fi 2.4 GHz | ✅ Working | NetworkManager, scan, connect |
| Wi-Fi 5 / 6 GHz | 🟡 In progress | Region US (your choice); bands enabled, no 5/6 GHz network tested yet |
| Bluetooth, own address | ✅ Working |  |
| Bluetooth pairing in GNOME | ⬜ Not started |  |
| USB device mode / USB network | ✅ Working |  |
| USB host / OTG, PD hub | ⬜ Not started |  |
| DisplayPort over USB-C | ⬜ Not started |  |

## Power & charging (1/8 working)

| Feature | Status | Notes |
|---|---|---|
| Battery level, voltage, current, temperature, health | ✅ Working | UPower and GNOME battery |
| Battery time estimate | 🟡 In progress | Inaccurate (your report): jumpy current reading, no charge-now value; fix in the Power area |
| Charging | 🟡 In progress | Works; Pad 4 stock charger limits patch (9 V / 1.5 A) awaiting test |
| Battery safety guard (stock limits) | 🟡 In progress | Written and simulated (30 cases); tablet test pending |
| Charge limit (80 %) | ⬜ Not started |  |
| Low-battery current limiting (BCL) | ⬜ Not started |  |
| Pen charging | ⬜ Not started | New driver needed |
| Fast charging (SuperVOOC / PPS) | ❌ Not planned | OnePlus-proprietary; not planned |

## Thermal (2/5 working)

| Feature | Status | Notes |
|---|---|---|
| CPU frequencies and CPU limits (stock) | ✅ Working | Held at 105 °C under load |
| Board and flash thermistors | ✅ Working |  |
| Skin and XO zones | 🟡 In progress | Patch ready; skin limits to be replaced by stock values |
| USB-C connector temperature zone | 🟡 In progress | Patch ready (57 °C, stock) |
| GPU cooling | 🟡 In progress | Load test pending |

## Sleep & power saving (1/6 working)

| Feature | Status | Notes |
|---|---|---|
| Suspend (s2idle) | 🟡 In progress | 24 cycles clean; two stalls after audio activity under investigation |
| Long sleep | 🟡 In progress | One unexplained reboot after a long sleep: watchdog vs planned reboot |
| Wake by power key and alarm | ✅ Working |  |
| Wake by lid, keyboard, charger | ⬜ Not started |  |
| 60 Hz on battery, CDSP off | 🟡 In progress | In iceland-device 0.4+; untested on the tablet |
| Deep-sleep proof, overnight drain ≤ ~1 %/h | ⬜ Not started |  |

## Sensors & camera (1/4 working)

| Feature | Status | Notes |
|---|---|---|
| Rear flash LEDs | ✅ Working |  |
| Accelerometer, compass, light / proximity | ⬜ Not started |  |
| Cameras (13 MP rear, 8 MP front) | ⬜ Not started | Plan written; stock supplies, clock and resets resolved; waiting for register data |
| Haptics, modem, NFC, fingerprint | ❌ Not planned | Not on this tablet |

## Software & packaging (4/6 working)

| Feature | Status | Notes |
|---|---|---|
| Kernel package (kernel-iceland) | ✅ Working | Test-built: 948 modules, device tree, install hooks |
| Device package (iceland-device 0.7) | ✅ Working | Settings, battery guard, sound, Wi-Fi region; built |
| Local update repository | ✅ Working | Checksum-verified sync; tested |
| Full GNOME app set | ⬜ Not started | Relay 008 |
| Stock-values audit | ⬜ Not started | Relay 013 |
| Automated PC fix loop + cloud debugger | ✅ Working |  |

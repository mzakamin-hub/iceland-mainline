# Next actions (PC session, from 2026-09-29 evening)

The PC session owns the project (relay 020).

Sources:
- **Status:** `docs/features/features-data.py` (the matrix; each open row has a where-to-look pointer).
- **Plan:** relay 019 (areas and exit criteria).
- **Evidence:** `docs/research/offline-prep/*.md`. These are cited claims, checked before use.

Each kit tests one area and may carry short side checks. It is judged from logs, and asks the user only for what
needs a person (eyes, hands, chargers). This file lists the concrete next step for every item that isn't working
yet, in the order they'll be done.

**Rules for every step:**
- RAM boot only.
- No firmware or identifiers in git.
- Stock values only (rule 13).
- Charge only while watched until the Power area closes.
- Boot & platform only after the user's go-ahead.

## 0. Charging safety: first, before any further kit

Every kit so far booted the OnePlus 15 charger policy: 3 A input, 4 A charge current, 12 V then 9 V PD request.
The PC port was asked for 1.2–1.9 A (stock SDP: 500 mA), and 12 V is above the stock VBUS OV of 11 V.

| Step | What | Where |
|---|---|---|
| 0.1 | Rework the relay 015 battmgr candidate into queue **0053** with the offline-review fixes (list below) | `relay/requests/015/`, `offline-prep/power.md` A6–A9, B3–B5, B12 |
| 0.2 | Build q18 = queue + 0053 and check it compiles clean | build-q18.sh |
| 0.3 | Unattended checks on the PC's USB port (SDP), in the next kit (list below) | power.md T1/T4 |
| 0.4 | Queue 0053 when 0.3 passes (TREE hash, prepare.sh), then PD/DCP charger tests with the user watching (T2/T3/T4) | Power area |
| 0.5 | Battery guard fixes (list below), with unit tests | `packaging/iceland-device/files/iceland-battery-guard`, `tests/test_battery_guard.py` |

**0.1: the fixes to the candidate:**
- read the charger type through USB_ADAP_TYPE (7) with the driver's own mapping;
- fail low (1.5 A) when VBUS can't be read after the 9 V request;
- reject 0 for `constant_charge_current_max`;
- re-send the inhibit on every attach;
- Apple brick → the "unknown" limits;
- warn when a firmware write fails;
- log the type and limits chosen.

**0.3: what the unattended checks look for on the PC port:**
- `usb_type` SDP, `input_current_limit` 500000, USB current ≤ 550 mA;
- `inhibit-charge` gives battery current ≤ 0 within 10 s, and `auto` resumes;
- `constant_charge_current_max` lowers the current, which settles the unit question;
- writing 0 is refused.

**0.5: the guard fixes:**
- keep the state only after a write succeeds (retry otherwise);
- stop charging when the voltage can't be read;
- stop when VBUS is above 11 V;
- stop on a fast temperature rise (≥ 3 °C between samples);
- log once at startup which inputs are missing.

## 1. Display & input (area-display-2)

| Item | Next action | Needs the user |
|---|---|---|
| Black screen after a refresh-rate change (cause not proven; see area-display.md §3) | Diagnostic run first: DPMS off/on at 144 Hz with the touch driver bound and unbound, 144 → 120 → 144 Hz with DPMS in between, one suspend/resume, each with DSI/DPU state + timestamps. The touch driver's role is unproven (boot shows display init → touch reset working). Then the fix: the mode-switch path and/or per-rate panel commands, or the touch/panel order if the bound DPMS run blanks | Watch the screen after each step; touch after each cycle |
| 120/60 Hz black | Short term: advertise 144 Hz only (panel driver mode list), so GNOME can't pick a broken mode. Then port stock's per-rate commands (`qcom,mdss-dsi-timing-switch-command`, per-DFPS on-commands; display.md R6-3) | Watch the screen per rate |
| Pink glitches | Not reproduced. Keep the checks ready: photo + drm state, XR24 vs XR30, `FD_MESA_DEBUG=noubwc`/`notile`, SSPP UBWC error registers. Evaluate DSC 1.2 + stock 0x91/0x92 init bytes (display.md R6-1/R6-2) against the panel | A photo if it returns |
| Screenshot path | `gnome-screenshot` fails on GNOME 50 Wayland: use the Shell's D-Bus Screenshot through an allowed caller, or `xdg-desktop-portal` + `grim`-like capture | none |
| Pen | libinput recheck with a charged pen (tip, hover, buttons, pressure) | Charge the pen, draw |
| Backlight curve | Compare our brightness range/default with stock (panel dtsi `qcom,mdss-dsi-bl-*`, LineageOS overlay) (relay 013 item 4) | none |
| Pogo keyboard | Research: OnePlusOSS pogo driver (serdev + HID bridge); after the display fixes | later |
| Auto-rotate | Waits for the sensors (section 7) | — |

## 2. Graphics & compute (area-graphics)

| Item | Next action |
|---|---|
| GPU correctness / stress | dEQP-GLES subsets (Fedora package or build), glmark2 30-min loop with devfreq + gpuss temps, WebGL in Firefox. GPU firmware: linux-firmware sqe/gmu/aqe + the tablet's zap (the user's call); A/B the stock set only as a side check. Add stock's 1100 MHz OPP (graphics.md A2) |
| Mesa main slower than 26.2.3 | Re-measure both back to back, cooled; if it holds, bisect-free check of the a8xx autotune/sysmem path; report upstream only with the user's OK |
| Video decode (Iris) | Enable the Iris node in the iceland DTS with `firmware-name = "qcom/…/vpu40_2v.mbn"` (the driver's default `vpu40_p2` is ENOENT), `CONFIG_VIDEO_QCOM_IRIS`, GStreamer v4l2 decode, CPU time |
| NPU (CDSP) | Stop disabling the CDSP in the kit's debug DTB (`tools/linux-ram/build.sh:69`), fix the firmware name (`cdsp.mbn` vs split `.mdt`), fix the `iceland-npu-off.service` ExecStart path, then boot the CDSP + FastRPC test (relay 012 C) |

## 3. Power & charging (after 0.x)

| Item | Next action | Needs the user |
|---|---|---|
| Charger tests | power.md T2–T6: DCP, PD (9 V decision, never 12 V), knobs, guard dry-run then live, firmware termination under load | Plug chargers, watch |
| Charge limit 85 % | Add `charge_control_start/end_threshold` + setter to the OPLUS battmgr variant; test whether the SoCCP honours opcode 0x48 (charger in, near 85 %); if not, a guard-side limit via `charge_behaviour`; UPower `CHARGE_LIMIT` in iceland-device | Watch while charging |
| Battery estimate | Report STATUS from the firmware (not forced Charging); CHARGE_NOW = capacity × charge_full; debug-kernel probe of TTE/TTF/POWER_AVG and the gauge words (power.md A2–A4, C2) | none |
| BCL | Stock PMH0101/PMIH010x BCL nodes → qcom-bcl/spmi bcl (relay 018 item 6) | none |
| Pen charging | Research the pen wireless-charge IC (odm `mt5806_firmware.bin`) and its stock driver | later |

## 4. Thermal

| Item | Next action |
|---|---|
| Skin/XO zones | Queue relay 009 with stock's skin gear caps (relay 018 item 7) |
| USB-C connector zones | Rebase the usb-therm candidate on HEAD (or after 009), add stock's 0x274a/0x275e channels, validate against board_therm (power.md A12/B6/B7) |
| GPU cooling | 30-min stress log (with area-graphics); 125 °C critical → hot |

## 5. Sleep & power saving

| Item | Next action |
|---|---|
| s2idle stalls after audio, long-sleep reboot | Kit with the timer-sm8850 candidates (rpmh-rsc past-wakeup clamp, arch timer always-on) + ramoops (pc-026-s10-crashlog) + debug-hang config; one 5-min sleep with the watchdog on/off. PipeWire after resume |
| Wake by lid/keyboard/charger | `wakeup-source` on the lid gpio-key and pmic-glink/UCSI; check `/sys/power/pm_wakeup_irq` |
| 60 Hz on battery, CDSP off | Test the iceland-device units (after the refresh fix; 60 Hz is broken today, so the battery rule must wait) |
| Overnight drain | qcom_stats before/after, unplugged overnight; the user's OK for an unwatched night (the battery isn't charging) |

## 6. Connectivity

| Item | Next action | Needs the user |
|---|---|---|
| Wi-Fi 5/6 GHz | Connect to a 5/6 GHz network (`iw reg get` US) | Wi-Fi credentials typed by the user |
| Bluetooth pairing | bluetoothctl + GNOME Settings with a device | A device to pair |
| USB host/OTG, DP alt mode | dwc3 role switch via UCSI; qmp-combo + DP from the infiniti series | A hub / a monitor |

## 7. Sensors & camera

| Item | Next action |
|---|---|
| Sensors | hexagonrpcd sensorspd + libssc + iio-sensor-proxy with the persist registry (the extractor provides persist, read-only) |
| Cameras | CAMSS/CCI from infiniti; relay 014 register data; `research/camera-bringup.md` |

## 8. Software & packaging

| Item | Next action |
|---|---|
| About page | iceland-device `/etc/machine-info` (HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL=Pad 4); socinfo id 661 name in the kernel |
| iceland-device | Pin 144 Hz until 1.x is fixed; the npu-off path; the guard fixes (0.5) |
| Full GNOME app set, stock-values audit | Relay 008 list; relay 013 table |
| Mic hiss (known issue) | Compare the downstream WCD939x per-rate TX port params with wcd939x-sdw.c (relay 018 9b) |
| Open candidates | area-audio-5 0001–0002 (tfa 0x62, TDM drive): one loopback side check, then 0054/0055 |

## 9. Boot & platform (last, after the user's go-ahead)

| Item | Next action |
|---|---|
| Firmware extractor | Add the `super` step to `tools/linux-ram/fw-extract.sh`: LP metadata reader (as `build/an/lp-list.py`), read-only dm-linear or loop with offset, EROFS mounted read-only. Test on the PC against the user's partition backup (10/10 vendor/odm files match stock 11.A.38), then in a kit, read-only |
| Install + dual boot | `phase4/INSTALL-PLAN.md`, iceland-u-boot 0003; only with the user's OK |

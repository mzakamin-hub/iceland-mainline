# Battery guard and charger inputs: verification against Pad 4 stock (2026-09-29)

Source: the live stock DT (`docs/device-facts/capture-20260927-2/live-fdt-redacted.dts`), nodes `oplus,comm` (l. 40196),
`oplus,wired` (l. 40170) and `oplus,mms_wired` (l. 40024). The units were checked on the tablet: `qcom-battmgr-bat`
`temp` is in tenths of °C (its thermal zone read 30000–32000 = 30–32 °C in pc-026), and `voltage_now` is in µV
(0029).

## Charger inputs (kernel, qcom_battmgr, Pad 4 only)

| | Before (inherited from the OnePlus 15) | Stock Pad 4 (now) | Source |
|---|---|---|---|
| PD voltage | 12 V, then 9 V | **9 V**, only while the battery is below 4.5 V | `cool_down_pdqc_vol_mv` max 9000, `vbatt_pdqc_to_9v_thr` 4500 |
| PD input current | 3 A | **2 A at 5 V, 1.5 A at 9 V** (13.5 W) | `input-power-mw`[PD] 13500, `pd-iclmax-ma` 2000 |
| DCP / SDP / CDP / unknown input | 3 A | **2 A / 500 mA / 1.5 A / 500 mA** (10 / 2.5 / 7.5 / 2.5 W at 5 V) | `input-power-mw` = 2500 2500 7500 10000 30000 13500 13500 [unknown SDP CDP DCP VOOC QC PD] |
| Charge current | 4 A | **PD 3300, DCP 2200, CDP 1600, SDP 600, unknown 2200 mA** | `fccmax-ma-lv/hv`, groups by type |
| VBUS range | – | 4.3–11 V (9 V is inside it) | `vbus_uv/ov_thr_mv` |

The input current is lowered to the 9 V value *before* 9 V is requested, and restored if the charger stays at 5 V.
VOOC/SVOOC adapters are reported as DCP by the firmware, so they get the DCP limits (fast charging is out of scope).

## Guard (iceland-device ≥ 0.3), region table

| Region | Battery temp | Stop above (V) | Recharge below (V) | Charge current cap (mA) |
|---|---|---|---|---|
| R0 | < −10 °C | no charging | – | 0 |
| R1 | −10 to 0 °C | 4.508 | 4.200 | 1959 |
| R2–R5 | 0 to 35 °C | 4.508 | 4.300 / 4.400 | 3300 |
| R6 | 35 to 45 °C | 4.488 | 4.380 | 3300 |
| R7 | 45 to 53 °C | 4.138 | 4.030 | **1000** (screen-on table, always used) |
| R8 | ≥ 53 °C | no charging | – | 0 |

Sources: `batt-them-thr`, `sw-over-fv-mv`, `wired-vbatdet-mv`, `led_on-fccmax-ma`. Always: stop above 4.600 V
(`vbatt-ov-thr-mv`); power off at 72.0 °C and immediately at 77.0 °C (`poweroff_high/emergency_batt_temp`); power off
below 3.300 V while discharging (`vbat_uv_thr_mv`).

**USB-C connector** (`oplus,mms_wired`, sensor `pmih010x_usb_therm` via the new usb-therm zone):
- stop at 57 °C while the battery is ≤ 50 °C, or at 69 °C above that;
- also stop when the connector is ≥ 7 / 12 / 15 °C hotter than the battery (battery ≤ 50 / 50–60 / ≥ 60 °C);
- once stopped, it stays stopped until the charger is unplugged (as stock);
- cool-down: cap 1200 mA from 54 °C (65 °C with a hot battery) or a 12 / 20 °C gap; recover below 48 / 60 °C with the
  gap below 6 / 15 °C.

## Corrections made by this check
1. **USB-C connector stop was 65 °C.** That's stock's *cool-down* level. The stop is 57 °C (69 °C with a battery
   above 50 °C), plus the gap rules and the latch.
2. **Warm-band stop was 4.130 V** (the charger float). Stock's software stop is 4.138 V, and each region has its own
   stop and recharge voltage (before, 35–45 °C and the recharge thresholds were missing).
3. **Per-region charge currents were missing** (1959 mA below 0 °C, 1000 mA at 45–53 °C). There's now a kernel knob
   (`constant_charge_current_max`, lower-only).
4. **Charger inputs were the OnePlus 15's** (12 V / 3 A / 4 A, any type). They're now the Pad 4 per-type values above.
5. **The low-voltage power-off acted on one reading.** It now needs 3 consecutive readings, so a load dip doesn't
   shut the tablet down.
6. **An unreadable battery temperature now stops charging** (it was ignored before).

## Not stock (ours), to be confirmed
- The 45 °C floor on the connector gap rules (it follows the OnePlus usbtemp code; the PC checks it in the OnePlusOSS
  source).
- 2 °C hysteresis when moving back towards the normal region.
- 3 readings before the low-voltage power-off.
- Stock's thermal "cool_down" levels (screen-on current reductions driven by the thermal HAL) aren't mirrored.

Tests: `packaging/iceland-device/tests/test_battery_guard.py` (30 cases, fake sysfs, dry-run): all pass.

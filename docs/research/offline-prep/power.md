# Offline preparation: power area (Mainline, 2026-09-29)

Reader findings from the cloud session's source analysis (kernel queue tree 0001-0052, stock live FDT, past PC results).
The three-lens verification and synthesis steps were cut off by a usage limit, so treat each item as a reader's claim
(cited, not independently re-verified) and check it on the tablet or in the source before acting.

## Reader summary

Reader A (offline): the OPLUS variant of qcom_battmgr on the Pad 4 reads battery current from word 1 of the OPLUS_GAUGE_READ (0x10000) snapshot, negated and scaled to uA, at most once per second, and exposes no averaged current, no power_now and no time_to_* (oplus_bat_props lists only 11 properties). The ±100..500 mA sign flips at 100 % on an SDP port are physically plausible (about 2.4 W of input against the system load; magnitudes are small, so it is not a sign-conversion bug) and the driver forces STATUS from "Discharging" to "Charging" whenever the USB supply is online (lines 653-661), so UPower sees "Charging" with a negative or tiny rate and produces a garbage time-to-full. The "remaining" gauge word 4 is not a charge: the raw values recovered from logged CHARGE_NOW are 5,888,254 at 40 %, 6,936,472 at 41 % and once 0x1C000000, so its identity is unknown (not found; needs a raw dump of the 128 words and the downstream oplus_chg source on the PC). The stock kernel's battery supply reported CHARGE_COUNTER=5986000 uAh at 47 % but constant/zero TIME_TO_* and POWER_NOW, so a correct estimate must come from a real remaining charge plus a correct status, not from firmware time estimates. A minimal safe kernel patch: (a) do not report "Charging" when the firmware says Discharging and the gauge current is <= 0 (report Full at 100 %, else Not charging); (b) add read-only TIME_TO_*_AVG / CHARGE_COUNTER / POWER_NOW via the BATT_* property GETs only after a tablet probe shows the Oplus firmware answers them; (c) CHARGE_NOW from the correct gauge word once identified. Relay 015 battmgr candidate: every stock number matches the live DT (input-power 2.5/2.5/7.5/10/13.5 W, pd-iclmax 2000 mA, FCC 600/1600/2200/3300 mA, 9 V only below 4.5 V), but it has three defects to fix before it is trusted: (1) it reads the charger type with USB_TYPE (6) while the OPLUS sysfs path uses USB_ADAP_TYPE (7) with the Oplus mapping, so the per-type limits may be chosen from a property the Oplus firmware never fills (fail-safe to 500 mA at worst, but PD would be crippled, and a colliding value could pick 2 A on a weak port); (2) inhibit-charge is sent once and only re-sent when the service comes up, not on a charger re-attach, while sysfs keeps showing the cached "inhibit-charge" (fail-unsafe for the guard if the firmware re-enables charging on replug; the commit text claims otherwise); (3) writing constant_charge_current_max = 0 removes the cap instead of stopping charge. Today's OPLUS battery supply accepts no writes at all (no set_property), so the guard cannot act until the patch lands. The usb-therm DT candidate maps 0x2747 correctly (ADC5_GEN4_AMUX4_THM_100K_PU(1,7) = stock pmih010x_usb_therm / usb_con_therm_adc) but stock's usbtemp protection (the 57/69 C rules) reads two other channels, usb_temp_adc_l 0x274a and usb_temp_adc_r 0x275e (AMUX1/AMUX5 GPIO 100k, scale-fn-type 5, conversion ratio 10), so the guard's connector rule would watch a different thermistor than stock does. Test plan below: 5-s sysfs logging on SDP/DCP/PD, ICL per type, inhibit/replug, FCC cap, 100 % termination, a debug-only gauge dump, upower correlation; watched charging only, with abort limits.

### A1 CURRENT_NOW is an instantaneous gauge word, negated and scaled, refreshed at most once per second; no averaged current exists in the driver (high, fact)

- Claim: The OPLUS battery current comes from word 1 of the 128-word OPLUS_GAUGE_READ snapshot: current_now = -(s32)word[1] * 1000 (gauge mA, positive = discharging, so the driver negates to the power-supply convention of positive = charging). The snapshot is re-requested at most once per second; every sysfs read of a gauge property re-uses it. No CURRENT_AVG, POWER_NOW or VOLTAGE_AVG is offered on the OPLUS battery, and words 7 and 9..127 of the snapshot are unnamed in the driver, so whether the gauge carries an averaged current is not found.
- Mainline: word[1] of the gauge snapshot, negated, x1000 (uA); 1 request/s
- Stock: stock battery psy shows CURRENT_NOW=1313 while STATUS=Charging (positive = charging, units look like mA) - capture-20260927-3/power-supply.txt:5,13
- Safety: none (read-only)
- Action: Keep the sign convention (it matches stock and pc-011/pc-026 charging readings of +293..+688 mA and +17 mA). Do not smooth in the kernel; fix the status (A2) and find a real remaining-charge word (A4) instead.
- Test: Log /sys/class/power_supply/qcom-battmgr-bat/{status,capacity,voltage_now,current_now} every 5 s at 100 % on the SDP port for 10 min; confirm the flips are +-100..600 mA (not ~4.29e9-sized), and that the sum of battery power and system load is consistent with usb voltage_now*current_now.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:129-138; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1793; /home/user/k45/drivers/power/supply/qcom_battmgr.c:505-506; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1064-1076; /home/user/k45/Documentation/ABI/testing/sysfs-class-power:79-100

### A2 STATUS is forced to "Charging" whenever the USB supply is online, hiding Discharging/Full at 100 % (high, fact)

- Claim: For the OPLUS variant the driver first requests USB_ONLINE, then BATT_STATUS, and if the firmware reports DISCHARGING while USB is online it rewrites the value to CHARGING. At 100 % on an SDP port the battery genuinely discharges part of the time (logged: STATUS=Charging CAPACITY=100 CURRENT_NOW=-272000 uA; also STATUS=Charging CAPACITY=41 CURRENT_NOW=-1329000 uA under load), so UPower is told 'charging' with a negative or near-zero rate. This, not the sign of the current, is the direct cause of the wrong GNOME estimate (inference for the UPower part: its source is unreachable from here).
- Mainline: online && firmware DISCHARGING -> CHARGING (unconditional)
- Stock: stock psy: STATUS=Charging at 47 % with CURRENT_NOW=1313 (capture-20260927-3/power-supply.txt:5,13); stock's Full handling is in oplus_chg (batt_full_para, iterm-ma 663) - not in the firmware status
- Safety: none (read-only); fail-safe
- Action: Minimal read-only patch: in the STATUS path also refresh the gauge (1-s throttled) and, when online and the firmware says DISCHARGING: report FULL if percent >= 100, CHARGING if current_now > 0, else NOT_CHARGING. Never rewrite a firmware FULL/NOT_CHARGING. Leave the USB-offline direction as is.
- Test: At 100 % on SDP and on PD: `status` must read Full (or Not charging) when current_now <= 0 for 3 consecutive 5-s samples; `upower -d` must then show state fully-charged and no time-to-full. At 40-80 % on PD: status Charging with positive current.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:653-661; /home/user/k45/drivers/power/supply/qcom_battmgr.c:579-585; /home/user/iceland-mainline/docs/tests/linux-runpc26u/S19/late-more.txt:79; /home/user/iceland-mainline/docs/tests/linux-runpc26b/F0/late-more.txt:iceland-batt 30 s line; /home/user/iceland-mainline/docs/tests/linux-runpc26e/probe/s3-probe-20260929-063955.txt:84-92

### A3 What UPower needs and what the OPLUS message space could provide (high, inference)

- Claim: UPower (inference: gitlab.freedesktop.org is blocked from this container, so its source could not be re-read) prefers the kernel's time_to_empty_now / time_to_full_now; otherwise it computes energy from charge_now (or capacity % x energy_full) and the rate from power_now or |current_now| x voltage_now, with the state taken from `status`. The sm8350/SM8550 property space that the OPLUS variant already speaks has BATT_CHG_COUNTER 14, BATT_TTF_AVG 19, BATT_TTE_AVG 20, BATT_POWER_NOW 22 and BATT_POWER_AVG 23, but the OPLUS variant never requests them, and whether the Oplus firmware answers them is not found. The stock kernel's own battery supply exposed CHARGE_COUNTER=5986000 uAh at 47 % (a real remaining charge) but TIME_TO_FULL_AVG=0, TIME_TO_FULL_NOW=0, TIME_TO_EMPTY_AVG=3600 and POWER_NOW=0 (constants), so stock had no usable firmware time estimate either; a stable estimate needs a correct status plus a real remaining charge.
- Mainline: OPLUS battery: no time_to_*, no power_now, no charge_counter; charge_now hidden (plausibility clamp)
- Stock: CHARGE_COUNTER 5986000 uAh at 47 % (OxygenOS), 6311000 uAh at 48 % (LineageOS); TIME_TO_* constant/zero
- Safety: none
- Action: Probe, do not assume: in a debug kernel request BATT_CHG_COUNTER/TTF_AVG/TTE_AVG/POWER_NOW/POWER_AVG once per minute on the OPLUS variant and print value and result. Expose (read-only) only the ones that answer with result 0 and plausible values (charge counter ~ percent x 13789 mAh).
- Test: With the debug print: at 40-60 % on PD, BATT_CHG_COUNTER should be 5.5-8.3e6 uAh and rise with charge; TTF/TTE should be seconds that shrink; log `upower -i /org/freedesktop/UPower/devices/battery_qcom_battmgr_bat` fields energy, energy-rate, time to full/empty, state every 5 s alongside.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:67-76; /home/user/k45/drivers/power/supply/qcom_battmgr.c:532-556; /home/user/iceland-mainline/docs/device-facts/capture-20260927-3/power-supply.txt:9,17,22-27; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/dumpsys-battery.txt:9-26; /home/user/k45/include/linux/power_supply.h:170-173

### A4 Gauge word 4 ("remaining") is not a remaining charge in mAh: recovered raw values 5,888,254 at 40 %, 6,936,472 at 41 %, once 0x1C000000 (high, inference)

- Claim: The driver publishes CHARGE_NOW = word[4] x 1000 (unsigned int), now clamped to 0 when it exceeds CHARGE_FULL. The logged sysfs values (before the clamp) were 1593286704 at 40 % and -1653462592 at 41 %, and once 1610612736. Solving raw x 1000 mod 2^32 with integer raw gives 5,888,254 (40 %, = 42.7 % of 13789 mAh), 6,936,472 (41 %, = 50.3 % of 13789 mAh) and 469,762,048 = 0x1C000000 (a bit pattern) - inconsistent with an RM in uAh or mAh, so the word's meaning is unknown. The pc-026 note that downstream reads the same word as batt_rm is unverified here (the OnePlusOSS source is only on the PC). Any patch exposing it as CHARGE_NOW would feed UPower wrong energy.
- Mainline: CHARGE_NOW = word[4]*1000, hidden by the plausibility clamp (0039)
- Stock: stock CHARGE_COUNTER 5986000 uAh at 47 %; stock CHARGE_NOW=4959 (unit unknown) - capture-20260927-3/power-supply.txt:17,27
- Safety: none (read-only), but a wrong CHARGE_NOW breaks the estimate
- Action: Debug-only test kernel (never queued): print the 128 words as hex once per 60 s (dev_info) and the `size` word. Identify the word that tracks percent x FCC (5.5-7.0 Ah at 40-50 %) and any word that tracks current but smoother. Ask the PC (relay 007/013) for the downstream data_buffer[] index table (oplus adsp gauge: batt_rm, average current, fcc, soh). Only then expose CHARGE_NOW/CHARGE_COUNTER.
- Test: Dump over a 10 % SoC change on PD (about 1.4 Ah); the RM candidate must change by ~1.4e6 uAh (or 1400 mAh) in step with `capacity`; word[1] vs any smoothed-current candidate compared to a 1-minute average of current_now.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:1796,1800-1805; /home/user/iceland-mainline/docs/tests/linux-runpc21/R2/linux-power.txt:18; /home/user/iceland-mainline/docs/tests/linux-runpc26b/probe/f1-probe-20260929-012952.txt:111; /home/user/iceland-mainline/relay/results/pc-026-critical-items.md:38; /home/user/k45/drivers/power/supply/qcom_battmgr.c:197-201

### A5 How the driver reports the charger type and input limit today, and what is writable (high, fact)

- Claim: On OPLUS the usb_type comes from USB_ADAP_TYPE (7), not USB_TYPE (6), mapped: values 0..8 pass through (Unknown..PD_PPS), 9 -> BrickID, 10..13 (VOOC/SVOOC) -> DCP, else Unknown. input_current_limit is read from USB_INPUT_CURR_LIMIT (5); the USB supply has no set_property, so input_current_limit is read-only. The OPLUS battery desc has no set_property/property_is_writeable at all, so charge_behaviour, constant_charge_current_max and charge_control_end_threshold do not exist for it today (charge_control_* exist only on the x1e80100/sm8550 descs, via BATTMGR_CHG_CTRL_LIMIT_EN 0x48). The DT node matches oneplus,iceland-pmic-glink first, so the OPLUS desc is used, not the sm8550 one (inference on of_match scoring).
- Mainline: usb_type via property 7 + mapping; input_current_limit read-only; battery: nothing writable
- Stock: stock usb psy: INPUT_CURRENT_LIMIT=500000 with USB_TYPE [SDP], CURRENT_NOW=494000 (capture-20260927-3/power-supply.txt usb block)
- Safety: fail-safe today only in the sense that nothing can be written; the guard cannot act
- Action: Relay 015 remains the way to get a knob. Whether the Oplus firmware also implements the upstream 0x48 charge-control message is unknown; ask the PC (relay 007 item 2) before adding charge_control_end_threshold.
- Test: On the queue kernel: `cat qcom-battmgr-usb/{usb_type,input_current_limit,current_now,voltage_now}` on SDP/DCP/PD; `ls -l qcom-battmgr-bat/` must show no charge_behaviour; writes to input_current_limit must fail with EACCES/EINVAL.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:1144-1145; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1548-1558; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1123-1131,1233-1238; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1078-1084; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1988,1993

### A6 Relay 015 candidate: charger type read with USB_TYPE (6) instead of the OPLUS path's USB_ADAP_TYPE (7) - the per-type limits may be chosen from an unfilled or differently enumerated property (high, fact)

- Claim: qcom_battmgr_iceland_setup_charger requests BATTMGR_USB_PROPERTY_GET / USB_TYPE directly. The callback stores that raw value without the Oplus mapping, whereas every sysfs read on OPLUS is redirected to USB_ADAP_TYPE and mapped. Property 6 has never been exercised on the Pad 4 (all tablet logs showing 'SDP' came through property 7). If property 6 fails or returns Unknown the patch falls back to 500 mA / 2200 mA (fail-safe for the battery, but PD charging would run at 2.5 W); if it returns an Oplus-space value that collides with POWER_SUPPLY_USB_TYPE_PD (6) or DCP (2), an SDP port could be asked for 2 A.
- Mainline: patch: property 6, unmapped
- Stock: n/a (stock reads the adapter type through its own oplus_chg stack)
- Safety: could over-draw a USB port (not the battery) on a collision; otherwise fail-safe (500 mA)
- Action: Change the request to USB_ADAP_TYPE on the OPLUS variant (same mapping as sysfs), or call the existing usb update helper; log the type chosen with dev_info so the tablet test can verify it.
- Test: With the fixed patch, on each charger: dmesg must name the type that `cat qcom-battmgr-usb/usb_type` shows, and input_current_limit must read 500000 (SDP), 1500000 (CDP), 2000000 (DCP), 2000000 at 5 V / 1500000 at 9 V (PD).
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:252-253; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1709-1715; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1144-1145

### A7 Relay 015 candidate: inhibit-charge is not re-sent on a charger re-attach; sysfs would keep showing 'inhibit-charge' while the firmware may charge again (high, fact)

- Claim: OPLUS_CHG_EN is written when charge_behaviour is set and again only in qcom_battmgr_oplus_enable (service up). qcom_battmgr_iceland_setup_charger, which runs on every attach, does not re-assert it. The get path returns the cached chg_inhibit bool, not a firmware read-back. The commit message's 'kept across charger attaches' is therefore not implemented unless the firmware itself latches CHG_EN across unplug/replug, which is not found.
- Mainline: CHG_EN sent on set and on service-up only
- Stock: n/a
- Safety: could over-charge / over-heat indirectly: the guard believes charging is stopped while it is not
- Action: Re-send OPLUS_CHG_EN = !chg_inhibit at the start of qcom_battmgr_iceland_setup_charger (every attach) and, cheaply, on every cid_work pass while usb.online; the guard should additionally verify current_now <= 0 after inhibiting and log if not.
- Test: Write inhibit-charge with a PD charger at < 80 %: current_now must go <= 0 within 10 s; unplug 10 s, replug: current_now must stay <= 0 for 60 s (not just charge_behaviour reading inhibit-charge); write auto: charging resumes.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:233-236; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:307-311; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:245-284; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:27-28,78-81

### A8 Relay 015 candidate: constant_charge_current_max = 0 removes the host cap instead of stopping charge (medium, fact)

- Claim: chg_fcc_host_ua == 0 means 'no cap' in qcom_battmgr_oplus_fcc_ua, and set_fcc accepts 0 and stores it, so a writer that means 'zero current' gets the full per-type current instead. The shipped guard never writes 0 (it inhibits for the 0-mA regions and only writes non-zero caps), so it is not exposed today, but the ABI is a trap for any other user.
- Mainline: 0 = uncapped
- Stock: stock fccmax tables use 0 for 'no charging' in regions R0/R8 (live-fdt-redacted.dts:40180-40181)
- Safety: could over-charge if a writer uses 0 to mean stop
- Action: Return -EINVAL for 0 (documented: use charge_behaviour to stop), or treat 0 as inhibit. Keep the lower-only semantics.
- Test: After the fix: `echo 0 > constant_charge_current_max` must fail (EINVAL) and not change battery current; `echo 1000000` must lower current_now to <= 1.0 A on PD at < 80 %.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:57-63; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:203-207; /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:218-223; /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:200-203

### A9 Relay 015 candidate: the uA unit of BATT_CHG_CTRL_LIM and OPLUS_USB_INPUT_CURR_LIMIT is inherited from the OnePlus 15 code and unverified on the Pad 4; the firmware today draws 1.1-1.4 A from an SDP port (high, fact)

- Claim: The inherited code sets ICL 3,000,000 and FCC 4,000,000 (uA) and the patch keeps uA. If the firmware read mA instead, every cap would be a no-op (fail-unsafe direction for the guard's derating). Tablet logs on the queue kernel show qcom-battmgr-usb CURRENT_NOW 1.14-1.39 A with USB_TYPE SDP (values step in 50 mA, so they may be an AICL setting rather than measured IBUS - inference), i.e. today the port is asked for far more than the stock 500 mA, which is the patch's motivation.
- Mainline: uA assumed; today ICL 3 A on any port
- Stock: SDP 500 mA input, 600 mA FCC; usb psy INPUT_CURRENT_LIMIT=500000 (capture-20260927-3/power-supply.txt)
- Safety: fail-unsafe if the unit is wrong (caps become no-ops); the input limits fail safe
- Action: Treat the unit as a test item, not a fact. Also have the patch dev_warn when a set returns an error (it ignores the return codes, as the inherited code did).
- Test: SDP port after the patch: usb input_current_limit reads 500000 and usb current_now <= ~520 mA. PD at < 80 %: battery current_now ~ up to 3.3 A; then `echo 1000000 > constant_charge_current_max` -> current_now <= 1.0 A within 10 s. If current does not change, stop the test (unit mismatch) and unplug.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:147-148,1844-1846; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1833-1836; /home/user/iceland-mainline/docs/tests/linux-runpc26u/S19/late-more.txt:79; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:186-196,258-262

### A10 Relay 015 candidate: attach-time window and one-shot 9 V decision (minor gaps, battery-safe) (low, fact)

- Claim: The stock limits are applied from cid_work, which polls every 2 s (5 s idle), so for up to ~5 s after attach the firmware default (5 V, 2 A) is in force. The 9 V request is evaluated once at attach (vbat < 4.5 V); stock also drops back to 5 V above 4.5 V (vbatt_pdqc_to_5v_thr = 4500). Neither exceeds the 13.5 W stock input power or the battery limits; they affect the USB port and heat, not the cells.
- Mainline: stock limits ~2-5 s after attach; 9 V decided once
- Stock: 5<->9 V switching around 4.5 V battery voltage
- Safety: none for the battery
- Action: Accept for now; note in the patch comment. Optionally re-evaluate the PDO in cid_work when voltage_now crosses 4.5 V.
- Test: PD charger at > 4.5 V battery: usb voltage_now must stay ~5 V and input_current_limit 2000000; at < 4.5 V: ~9 V and 1500000 within 5 s of attach.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:141-142,1942; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:264-266; /home/user/iceland-mainline/docs/device-facts/capture-20260927-2/live-fdt-redacted.dts:40174-40176

### A11 Relay 015 stock numbers verified against the live DT (medium, fact)

- Claim: input-power-mw = 2500 2500 7500 10000 30000 13500 13500 [unknown SDP CDP DCP VOOC QC PD]; pd-iclmax-ma = qc-iclmax-ma = 2000; fccmax-ma-lv/hv per type in the normal regions = 2200 (unknown, DCP) / 600 (SDP) / 1600 (CDP) / 3300 (VOOC, QC, PD); 9 V threshold 4500 mV; batt-them-thr -100 0 50 120 160 350 450 530 decidegC; iterm 663 mA; fv 4500/4480/4130 mV; vbatt-ov 4600 mV. The patch's table and the guard's tables match these. Note the PD row's 45-53 C current is 3300 mA in fccmax-ma-lv but 1000 mA in led_on-fccmax-ma; the guard uses the lower (screen-on) table, which is conservative.
- Mainline: as in the patch
- Stock: as quoted (OxygenOS 11.A.38 live DT)
- Safety: fail-safe
- Action: None for the numbers. Termination reference for the 100 % test: iterm 663 mA, float 4.50 V (4.48 V at 35-45 C, 4.13 V at 45-53 C).
- Test: See the test plan: compare logged currents per charger type with this table.
- Evidence: /home/user/iceland-mainline/docs/device-facts/capture-20260927-2/live-fdt-redacted.dts:40179-40181; /home/user/iceland-mainline/docs/device-facts/capture-20260927-2/live-fdt-redacted.dts:40201-40203,40216; /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:156-183; /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:41-44

### A12 usb-therm DT candidate: 0x2747 is stock's pmih010x_usb_therm, but stock's usbtemp protection (57/69 C rules) reads usb_temp_adc_l 0x274a and usb_temp_adc_r 0x275e (high, fact)

- Claim: The candidate's channel encoding is right: ADC5_GEN4_AMUX4_THM_100K_PU(1, 7) = (1<<13)|(7<<8)|0x47 = 0x2747 = stock 'pmih010x_usb_therm' / 'usb_con_therm_adc' (stock thermal zone 'usb_therm', 40.9 C in capture 3). However the stock node that implements the connector protection with usbtemp_ntc_temp_low/high = 57/69 C, oplus,virtual_buck under oplus,mms_wired, lists io-channels 0x274a 'usb_temp_adc_l' and 0x275e 'usb_temp_adc_r' (= ADC5_GEN4_AMUX1_GPIO_100K_PU(1,7) and ADC5_GEN4_AMUX5_GPIO_100K_PU(1,7)), non-ratiometric, scale-fn-type 5, with usbtemp_conversion_ratio 10. The battery-charger node lists 0x2747 separately as 'usb_con_therm_adc'. So the guard's connector rule, fed by the candidate zone, would watch a different (probably less pin-proximal - inference) thermistor than stock's rule uses.
- Mainline: one zone on 0x2747 with a 57 C passive trip
- Stock: usbtemp rules on 0x274a/0x275e (L/R connector NTCs); 0x2747 is a separate 'usb_therm' zone
- Safety: could over-heat the connector: the 57 C rule applied to a sensor that reads lower than stock's would trip late
- Action: Keep the 0x2747 zone (it is a real stock sensor), but add channels 0x274a and 0x275e (AMUX1/AMUX5 GPIO 100k pull-up, no qcom,ratiometric per stock) and zones for them; the mainline driver has no 'scale-fn-type 5' conversion, so their temperatures must be validated against 0x2747 and the battery at idle before the guard uses them. Have the guard take the maximum of the three connector readings.
- Test: Log the three channels (iio in_temp*/in_voltage* raw and processed) plus board_therm every 5 s at idle and during 20 min of PD charging; all should be ~board temperature at idle and rise together while charging; if 0x274a/0x275e cannot be converted sensibly, report the raw ADC values for the PC to map with the downstream table.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-usb-therm-zone.patch:32-38,52-63; /home/user/k45/arch/arm64/boot/dts/qcom/qcom-adc5-gen4.h:11,60,63,68; /home/user/iceland-mainline/docs/device-facts/capture-20260927-2/live-fdt-redacted.dts:40033-40034,40066,40072-40073; /home/user/iceland-mainline/docs/device-facts/capture-20260927-2/live-fdt-redacted.dts:10618-10619,10658-10672,10695-10696; /home/user/iceland-mainline/docs/device-facts/capture-20260927-3/thermal-zones.txt:89

### A13 Refresh model: every sysfs read is a glink round trip; notifications only trigger uevents; 1-s gauge throttle (medium, fact)

- Claim: Non-gauge properties issue one BATTMGR_*_PROPERTY_GET per read under a mutex (the firmware stops responding to concurrent requests); gauge properties share one 0x10000 snapshot per second. Firmware notifications NOTIF_BAT_PROPERTY/USB_PROPERTY/WLS_PROPERTY call power_supply_changed, which makes UPower re-read; no values are pushed. cid_work additionally polls CID/USB_ONLINE every 2-5 s. Logging every 5 s is safe; do not poll faster than 1 s.
- Mainline: request per read; 1 Hz gauge snapshot
- Stock: oplus,mms_gauge topic-update-interval 0x1388 = 5000 ms (live-fdt-redacted.dts:40083)
- Safety: none
- Action: Test cadence 5 s (matches stock's gauge topic interval). Note: qcom_battmgr_request returns the firmware's raw `result` word; get_property rejects only negative values, so a positive firmware error code would be read as success with stale data - log the raw result in the debug probes.
- Test: Run the 5-s logger for 20 min and check dmesg for 'invalid payload length' / 'unknown message' / -ETIMEDOUT; none expected.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:403-407; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1384-1397; /home/user/k45/drivers/power/supply/qcom_battmgr.c:423-427

#### Test Plan
- SAFETY ENVELOPE for every step: tablet in sight, battery <= 45 C, voltage_now <= 4.55 V, connector zones <= 50 C; otherwise unplug. Nothing is written to UFS or firmware storage; all knobs are volatile sysfs.
- LOGGER (all kernels), every 5 s: for P in /sys/class/power_supply/qcom-battmgr-bat: status capacity voltage_now current_now temp charge_full charge_now (if present) charge_behaviour constant_charge_current_max (if present); qcom-battmgr-usb: online usb_type voltage_now current_now input_current_limit; ucsi-source-psy-*: online voltage_now current_now usb_type; /sys/class/thermal zones of type usb-therm-thermal, battery (qcom-battmgr-bat), board_therm; plus `upower -i /org/freedesktop/UPower/devices/battery_qcom_battmgr_bat | grep -E 'state|energy|energy-rate|time to|percentage'` every 5 s (UPower re-reads on each uevent; the polled values are what GNOME shows).
- BASELINE (queue kernel, no relay 015): SDP (PC port), DCP (5 V wall) and PD, 5 min each at 40-80 %: record usb_type, input_current_limit, usb current_now, battery current_now, and the status. Expected today: input_current_limit 3000000 on every type (inherited), usb current > 500 mA on SDP.
- 100 % ESTIMATE CASE (queue kernel): at 100 % on SDP, 10 min: confirm status stays 'Charging' while current_now flips sign (A2), record upower state/time-to-full; repeat at 100 % on PD.
- RELAY 015 kernel, after fixing A6 (USB_ADAP_TYPE), A7 (re-send CHG_EN on attach) and A8 (reject 0): per charger type at 40-80 %: input_current_limit must read SDP 500000 / CDP 1500000 / DCP 2000000 / PD 2000000 at ~5 V or 1500000 at ~9 V; usb voltage_now ~9 V only when battery voltage_now < 4500000, else ~5 V; battery current_now <= the per-type FCC (600 / 1600 / 2200 / 3300 mA) within 10 s of attach; dmesg shows the type used.
- INHIBIT: `echo inhibit-charge > charge_behaviour` on PD at < 80 %: current_now <= 0 within 10 s; unplug 10 s, replug: current_now stays <= 0 for 60 s (A7); `echo auto`: current_now > 0 within 10 s; repeat on SDP.
- FCC CAP: `echo 1000000 > constant_charge_current_max` on PD at < 80 %: current_now <= 1.0 A within 10 s; `echo 3300000`: restores (never above the attach value); `echo 0`: must fail (after A8) or, on the unfixed patch, document that it un-caps; then `echo 1959000` and `echo 600000` to sample the guard's values. If a write does not change the current within 10 s, stop (unit mismatch, A9) and unplug.
- TERMINATION at full (relay 015 kernel, PD, 20 min from ~95 %): current should taper below iterm 663 mA near 4.50 V, then status Full (after A2) and current ~0 or slightly negative; voltage must never exceed 4.55 V; note the recharge behaviour (stock vbatdet 4.40 V at 5-35 C).
- WARM DERATING (firmware alone): glmark2 + CPU load on PD, 20 min, log battery temp/current: compare with the stock regions (35-45 C: 3300 mA cap and 4.48 V float; 45-53 C: 1000 mA screen-on, 4.13 V). Abort at 45 C battery. Run iceland-battery-guard in dry-run in parallel (ICELAND_GUARD_DRYRUN=1) and record its decisions.
- GAUGE DUMP (debug-only kernel, never queued): dev_info hex dump of the 128 gauge words + size every 60 s while charging from ~40 % to ~50 % on PD; identify the word that tracks percent x 13789 mAh (5.5-7.0 Ah) and any word smoother than word[1]; also request BATT_CHG_COUNTER(14), BATT_TTF_AVG(19), BATT_TTE_AVG(20), BATT_POWER_NOW(22), BATT_POWER_AVG(23) once per minute and print value + raw result (A3, A13).
- USB-THERM: with the DT candidate plus channels 0x274a/0x275e added: log the three connector channels and board_therm at idle and during PD charging; plausibility: idle ~board temperature, rising while charging; if 0x274a/0x275e read nonsense, capture raw ADC codes for the PC to map with stock's scale-fn-type 5 / conversion ratio 10.
- UPOWER CORRELATION: with the A2 status fix (and, if found, a real charge counter), at 100 % on SDP upower must show 'fully-charged' and no time-to-full; at 50 % on PD a time-to-full that changes by < 20 % between consecutive samples once current is steady.

#### Open Questions
- Which OPLUS gauge snapshot word is the remaining charge (downstream batt_rm) and in which unit, and is there an averaged-current word? Needs the PC's read of the OnePlusOSS oplus_chg adsp gauge data_buffer[] table (relay 007/013) and the debug dump.
- Does the Oplus firmware answer BATT_CHG_COUNTER / BATT_TTF_AVG / BATT_TTE_AVG / BATT_POWER_NOW property GETs on the Pad 4 (result 0, plausible values)? Not found offline.
- Does USB_TYPE (property 6) return anything on the Oplus firmware, or only USB_ADAP_TYPE (7)? Determines A6's severity.
- Does OPLUS_CHG_EN = 0 survive an unplug/replug in the firmware, and does it stop the battery current only or also suspend the input (VBUS still online, usb online still 1)?
- Are BATT_CHG_CTRL_LIM and OPLUS_USB_INPUT_CURR_LIMIT in uA on the Pad 4 firmware (A9)? Only a tablet test with current read-back can settle it.
- Does the Oplus firmware implement the upstream BATTMGR_CHG_CTRL_LIMIT_EN (0x48) start/end thresholds (a second, firmware-side stop)? Asked in relay 007 item 2, no answer recorded.
- What conversion do stock's usb_temp_adc_l/r channels (scale-fn-type 5, usbtemp_conversion_ratio 10) use, and which of the three connector thermistors sits closest to the pins? Needed before the guard's connector rule is trusted.
- UPower's exact estimate algorithm could not be re-read (gitlab.freedesktop.org blocked); confirm on the tablet with `upower -d` whether it uses time_to_* from sysfs when present.
- Is the 1.14-1.39 A 'qcom-battmgr-usb current_now' on an SDP port a measured IBUS or an AICL setting? Compare with a USB power meter if one is available.

## Reader summary

Reader B (offline) on relay 015 + iceland-battery-guard. Tree /home/user/k45 HEAD 8a008a7e2b57; stock FDT = docs/device-facts/capture-20260927-2/live-fdt-redacted.dts. (1) The queue as it boots TODAY still applies the OnePlus 15 policy: ICL 3 A, FCC 4 A, PDO 12 V then 9 V (qcom_battmgr.c:147-149, 1837-1861); pc-021 log shows INPUT_CURRENT_LIMIT=3000000 and usb CURRENT_NOW=1241000 on a PC SDP port; 12 V is above stock VBUS OV 11000 mV. The battmgr candidate fixes this, applies cleanly to HEAD (git apply --check OK), and all its numbers match stock oplus,wired. Two code issues: it classifies the charger from raw USB_TYPE (6) instead of USB_ADAP_TYPE (7) used by the driver's own sysfs path for the Oplus firmware; on a VBUS read error after the 9 V request it restores the 2 A (5 V) limit while VBUS may be 9 V. (2) The usb-therm patch does NOT apply to HEAD (needs the unqueued relay 009 candidate; verified on a scratch copy) and it binds stock's 57 C rule to pmih010x_usb_therm 0x2747 (thermal HAL sys-therm-11) while stock's usbtemp protection reads usb_temp_adc_l 0x274a / usb_temp_adc_r 0x275e. (3) The guard's tables match stock line by line and its 30 unit cases pass here, but it caches the desired state even when the sysfs write failed (a failed inhibit is never retried); a missing usb-therm zone or unreadable voltage silently disables those rules. (4) Gaps in both layers: usbtemp rise-fast rule, per-region float voltage (4.13 V at 45-53 C), termination 663 mA, dual-cell protection, BCL, poweroff below 3.2 V while charging. No ro.vendor.oplus charging props in the getprop captures (not found).

### B1 Queue today: OnePlus 15 limits (3 A / 4 A / 12 V) on the Pad 4 (high, fact)

- Claim: Without the 015 patch every charger gets ICL 3 A, FCC 4 A and a 12 V PDO request; stock SDP is 2.5 W and VBUS OV is 11 V. A PC port already delivered 1.24 A.
- Mainline: ICL 3000 mA, FCC 4000 mA, PDO 12 V
- Stock: SDP 500 mA/2.5 W, CDP 1.5 A, DCP 2 A, PD 2 A@5 V / 1.5 A@9 V, max PDO 9 V, VBUS OV 11000 mV
- Safety: could over-charge (port over-draw, 12 V above stock OV) - fail-unsafe today
- Action: Queue the battmgr candidate first (with B3/B4 fixed); until then charge only on a PD charger that offers no 12 V PDO or on a 5 V wall charger, watched.
- Test: After the patch: cat qcom-battmgr-usb/input_current_limit per charger = 500000 (SDP) / 1500000 (CDP) / 2000000 (DCP, PD@5V) / 1500000 (PD@9V); usb voltage_now never > 9.5 V.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:147-149; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1839; /home/user/iceland-mainline/docs/tests/linux-runpc21/R2/linux-more.txt:137-141; live-fdt-redacted.dts:40179,40189

### B2 battmgr candidate applies to HEAD and its values are stock-true (high, fact)

- Claim: git apply --check passes on 8a008a7e2b57. Type table SDP 2500 mW/600 mA, CDP 7500/1600, DCP 10000/2200, PD 13500/3300 capped 2000 mA, 9 V only below 4.5 V, unknown 2500/2200 all decode from oplus,wired.
- Mainline: as patch
- Stock: identical
- Safety: fail-safe (only lowers vs today)
- Action: Keep the values; note the SDP/CDP groups have no R7 reduction in stock (600/1600 flat) - the guard's 1000 mA cap at 45-53 C is min()-ed by the kernel so nothing rises.
- Test: See test plan per charger.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:152-183; live-fdt-redacted.dts:40175-40181; live-fdt-redacted.dts:40185-40186

### B3 Patch classifies the charger from raw USB_TYPE (6), not USB_ADAP_TYPE (7) (high, inference)

- Claim: qcom_battmgr_iceland_setup_charger requests USB_TYPE; the driver's sysfs path swaps USB_TYPE for USB_ADAP_TYPE on the Oplus firmware and maps it (Apple brick 9, <=13 -> DCP). The raw value's meaning on this firmware is not verified; a misclass could give 2 A on a PC port.
- Mainline: USB_TYPE (6) raw
- Stock: n/a (firmware property)
- Safety: could over-charge the port if raw type reads as DCP/PD; fail-safe if it reads unknown (500 mA)
- Action: Request USB_ADAP_TYPE in the setup path (same as the sysfs path) before queueing.
- Test: Per charger compare qcom-battmgr-usb/usb_type with the applied input_current_limit; SDP must give 500000.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:252-253; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1144-1145,1548-1558

### B4 PD 9 V error path restores the 2 A limit while VBUS may be 9 V (medium, fact)

- Claim: If USB_VOLT_NOW fails after OPLUS_SET_PDO 9 V, the code re-applies the 5 V current (2 A) -> up to 18 W vs stock 13.5 W. Also the 9 V decision is attach-time only; stock returns to 5 V at vbat >= 4.5 V.
- Mainline: 2 A on read error; no 9->5 V fallback
- Stock: 13.5 W max; 5 V again at 4.5 V
- Safety: could over-charge (power above stock, still within 2 A ICL and 11 V OV)
- Action: On ret != 0 keep the 1.5 A limit (fail low); optionally re-request 5 V from a periodic check when voltage_now >= 4.5 V.
- Test: PD charger at vbat < 4.5 V: usb voltage_now ~9 V AND input_current_limit 1500000 together; usb current_now <= 1.5 A.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:279-281; live-fdt-redacted.dts:40174

### B5 charge_behaviour / constant_charge_current_max semantics (medium, fact)

- Claim: inhibit persists across attach (setup never touches CHG_EN) and across service restart (enable writes !chg_inhibit). Writing 0 to constant_charge_current_max clears the host cap instead of setting 0; before the first attach the readback is 4 A (OnePlus 15 default). Unit of BATT_CHG_CTRL_LIM (uA?) and firmware acceptance are unverified.
- Mainline: 0 = no cap; idle readback 4000000 uA
- Stock: n/a
- Safety: fail-safe for the guard (it never writes 0); readback cosmetic
- Action: Reject 0 with -EINVAL; report 0/ENODATA before the first attach on iceland.
- Test: echo 1000000 > constant_charge_current_max with PD at < 80 %: bat current_now <= 1000 mA within 30 s; echo 5000000: readback stays at the attach value; echo inhibit-charge: current_now <= 0 in 10 s, survives unplug/replug; echo auto restores.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:57-63,73-74,207,309-311

### B6 usb-therm patch does not apply to HEAD; needs relay 009 first (high, fact)

- Claim: git apply --check fails (hunk at dts:1369); on a scratch copy relay 009 (skin/xo) then usb-therm apply with 1-line offsets. 009 itself applies to HEAD.
- Mainline: no usb-therm zone in the tree
- Stock: usb_therm zone on 0x2747 (dts:18009-18010)
- Safety: fail-safe missing input: guard's USB rules silently inactive (see B9)
- Action: Queue order: battmgr -> 009 -> usb-therm, or rebase usb-therm onto HEAD (drop the channel@144 context).
- Test: git apply --check after 009 is queued; on the tablet: thermal zone type usb-therm-thermal exists.
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-usb-therm-zone.patch:40-42; /home/user/k45/arch/arm64/boot/dts/qcom/kaanapali-oneplus-iceland.dts:1364-1371

### B7 usb-therm zone reads a different thermistor than stock's usbtemp protection (high, fact)

- Claim: Stock's 57/69 C rules (oplus,mms_wired/virtual_buck) use usb_temp_adc_l 0x274a and usb_temp_adc_r 0x275e (GPIO channels, scale-fn-type 5, non-ratiometric); 0x2747 pmih010x_usb_therm is the HAL's sys-therm-11 (125 C placeholder trips) and hal_sm8350's usb_con_therm_adc.
- Mainline: zone on ADC5_GEN4_AMUX4_THM_100K_PU(1,7) = 0x2747
- Stock: protection on 0x274a + 0x275e; 0x2747 = connector NTC read by HAL
- Safety: could over-heat if 0x2747 reads lower than the L/R sensors (57 C reached later)
- Action: Add channels ADC5_GEN4_AMUX1_GPIO_100K_PU(1,7) and AMUX5_GPIO_100K_PU(1,7) as usb-temp-l/r zones (INFERENCE: mainline's 100k ratiometric NTC conversion approximates scale-fn 5, must be checked against board_therm); guard takes max of all three. Keep 0x2747.
- Test: Idle: all three within ~5 C of board_therm; while charging on PD they rise; a value of 125000/-273000/0 = wrong channel or scale.
- Evidence: live-fdt-redacted.dts:40072-40073; live-fdt-redacted.dts:10657-10671; live-fdt-redacted.dts:10617-10619,17487-17488; /home/user/k45/arch/arm64/boot/dts/qcom/qcom-adc5-gen4.h:60-68

### B8 Guard caches state on failed writes - a failed inhibit is never retried (high, fact)

- Claim: inhibit() sets self.inhibited = on and set_fcc() sets self.fcc even when wr() returned False; the CRIT log + wall happen once (self.warned). A transient -EAGAIN (service not up) leaves the guard believing charging is stopped.
- Mainline: write once, cache regardless
- Stock: n/a (stock kernel enforces directly)
- Safety: could over-heat/over-charge: the stop is silently lost after one failed write
- Action: Cache only on success; retry every step; re-read charge_behaviour each step and re-assert; repeat the wall/CRIT every 5 min while plugged and not inhibited.
- Test: Fake sysfs with a read-only charge_behaviour: expect a retry and a log every step; on the tablet: stop the pmic-glink client briefly is not possible, so rely on the unit test.
- Evidence: /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:143-155; /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:157-163

### B9 Missing knobs: partly silent (medium, fact)

- Claim: No charge_behaviour: one CRIT + wall then silence. No constant_charge_current_max: nothing logged. No usb-therm zone: usb_stop/usb_cool return None/False (USB rules off, unlogged). Unreadable voltage: voltage rules skipped silently. Unreadable temperature: stops charging (fail-safe, OURS).
- Mainline: silent on missing zone/voltage
- Stock: stock uses gap_without_batt_temp 12/24 C (dts:40038-40039) when battery temp is missing
- Safety: fail-open for the USB and voltage rules
- Action: Log once at start which inputs exist; treat unreadable voltage like unreadable temperature (stop); warn every 5 min while plugged if the zone is absent.
- Test: Start the guard on the kernel without the zone: journal must name the missing zone.
- Evidence: /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:87-93,107-109,166-168,195-197

### B10 Guard tables verified against stock; 30/30 tests pass here (medium, fact)

- Claim: REGION_THR = batt-them-thr -100 0 50 120 160 350 450 530; SW_OVER_FV 4508x6 4488 4138 4138; VBATDET 0 4200 4300 4400x3 4380 4030 0; FCC_MA = led_on-fccmax 0 1959 3300x5 1000 0; V_OV 4600; 72.0/77.0 C; V_UV 3.3 V; USB 50/60/57/69, gaps 7/12/15, cool 54/65 gap 12/20, recover 48/60 gap 6/15, 1200 mA. Polling 5 s plugged / 15 s not; syslog ident iceland-battery-guard; unit Restart=always RestartSec=5 (covers exit 0 when the psy is not up yet). OURS: 45 C gap floor, 2 C hysteresis, 3 UV readings.
- Mainline: as listed
- Stock: identical
- Safety: none
- Action: None for the values; the research doc's table is confirmed.
- Test: python3 tests/test_battery_guard.py files/iceland-battery-guard -> FAILURES: 0 (done here).
- Evidence: /home/user/iceland-mainline/packaging/iceland-device/files/iceland-battery-guard:40-58,236; live-fdt-redacted.dts:40201,40206,40213,40216,40180,40236,40240-40241,40030-40051

### B11 Stock limits enforced by neither layer (gaps) (medium, fact)

- Claim: (a) usbtemp rise-fast: +3 C (rise_fast_temp 3) within 30/20 samples -> stop; guard polls at 5 s, no rate rule. (b) per-region charger float fv-mv 4500x6/4480/4130/4130 and sw-fv 4450x6/4430/4080 - no mainline knob; the guard's 4.138 V stop at 45-53 C is only a backstop. (c) iterm-ma 663, batt_full_para - firmware's job, unverified. (d) dual-cell: min-fcc 3400 mAh, cur_limit 2500 mA. (e) BCL pmh0101 dynamic_vbat -50:3050/2700/2500, 100:2950/2700/2500, 1000:2850/2700/2500 mV; pmih010x 3000/3000/2600, 2900/2900/2600, 2800/2800/2600 - no driver. (f) vbat_charging_uv 3200 / chg_shutdown_max 3200 mV while charging - guard only acts when Discharging. (g) non-standard battery fv 3980 / sw-over-fv 3990 / vbatdet 3680 / ibatmax 500 mA. (h) cool_down levels 1200/1500/2000 mA (thermal HAL). (i) FFC 4630 mV is fast-charge only and must stay unused.
- Mainline: not enforced
- Stock: as listed
- Safety: could over-heat (a), could over-charge at 45-53 C if the firmware has no JEITA (b)
- Action: Guard: add the rise-fast rule (>= 3 C rise between consecutive 5 s samples while plugged -> stop) and a stop when usb voltage_now > 11 V; decide (b) from the 20-min firmware test; BCL and dual-cell stay TODO items.
- Test: 20-min PD charge under load: log temp/voltage/current; expect taper to ~663 mA and Full near 4.5 V at 16-35 C; if temp crosses 45 C observe whether current/float drop without the guard (dry-run).
- Evidence: live-fdt-redacted.dts:40040-40043; live-fdt-redacted.dts:40202-40204; live-fdt-redacted.dts:40156,40160,10913,11865,40237,40247,40209-40212,40178,40221

### B12 Apple brick treated as DCP (10 W) - not a stock table entry (low, inference)

- Claim: The patch maps APPLE_BRICK_ID to DCP 2 A/2200 mA; stock's 7-entry tables have no Apple entry. A 5 W Apple brick would be over-drawn.
- Mainline: 10 W
- Stock: not found in oplus,wired
- Safety: could over-draw a small adapter (adapter-side protection)
- Action: Use the unknown limits (2.5 W) until stock's handling is shown.
- Test: Not needed for the area run (no Apple brick planned).
- Evidence: /home/user/iceland-mainline/relay/requests/015/candidate-battmgr-stock-limits-charge-inhibit.patch:168-172

#### Test Plan
- PRECONDITIONS: user present the whole time; abort and unplug if bat temp > 45 C, usb voltage_now > 9.5 V, usb current_now > limit + 10 %, bat voltage_now > 4.51 V, or any usb-therm zone > 50 C. Kernel = queue + battmgr candidate (B3/B4 fixed) [+ 009 + usb-therm]. Guard first in dry-run.
- LOGGER (run in every test, 5 s period): B=/sys/class/power_supply/qcom-battmgr-bat; U=/sys/class/power_supply/qcom-battmgr-usb; while :; do printf '%s ' "$(date +%T)"; for f in status capacity voltage_now current_now temp charge_behaviour constant_charge_current_max; do printf '%s=%s ' $f "$(cat $B/$f 2>&1)"; done; for f in online usb_type voltage_now current_now input_current_limit; do printf 'usb.%s=%s ' $f "$(cat $U/$f 2>&1)"; done; for z in /sys/class/thermal/thermal_zone*; do case $(cat $z/type) in usb-therm*|usb-temp*|board*) printf '%s=%s ' $(cat $z/type) $(cat $z/temp);; esac; done; echo; sleep 5; done | tee /tmp/chg-$(date +%s).log. Plus: journalctl -f -u iceland-battery-guard; dmesg -w | grep -i battmgr; grep . /sys/class/typec/port0/power_operation_mode /sys/class/typec/port0-partner/usb_power_delivery/source-capabilities/*/* 2>/dev/null.
- T1 PC USB port (SDP), battery 30-80 %: expect usb_type=SDP, usb.input_current_limit=500000 (readback echoes the set value: pc-021 showed 3000000), usb.current_now <= 550000, bat current_now <= 600000 uA, constant_charge_current_max=600000, usb.voltage_now 4.5-5.25 V. FAIL if current_now near 1.24 A as in pc-021.
- T2 5 V wall charger (DCP; a VOOC brick also shows DCP): usb_type=DCP, input_current_limit=2000000, usb.current_now <= 2.0 A, bat current_now <= 2200 mA, constant_charge_current_max=2200000, VBUS 4.5-5.25 V.
- T3 PD charger, battery voltage < 4.5 V (SoC <= ~80 %): usb_type=PD/PD_PPS, within ~3 s after attach usb.voltage_now 8.5-9.5 V together with input_current_limit=1500000 and usb.current_now <= 1.5 A (13.5 W); bat current_now <= 3300 mA; never 12 V (VBUS <= 11 V stock OV). Then unplug, charge to > 4.5 V (or test at > 90 %) and replug: VBUS stays 5 V, input_current_limit=2000000. Also read the UCSI source capabilities and note whether the charger offers 12 V.
- T4 Knobs (with PD, SoC < 80 %): echo inhibit-charge > $B/charge_behaviour -> bat current_now <= 0 within 10 s and usb.current_now drops; unplug + replug -> still no charge current; echo auto -> charging resumes. echo 1000000 > constant_charge_current_max -> bat current_now <= 1000 mA within 30 s (decides the BATT_CHG_CTRL_LIM unit); echo 5000000 -> readback = attach value (lower-only); echo 0 -> readback = attach value (cap cleared, document).
- T5 Guard: ICELAND_GUARD_DRYRUN=1 ICELAND_GUARD_ONESHOT=1 /usr/libexec/iceland/iceland-battery-guard -> prints 'DRYRUN: charge_behaviour <- auto' and 'constant_charge_current_max <- 3300000' (or the region's cap), nothing else. Then systemctl start iceland-battery-guard: journal shows 'charge current cap 3300 mA' once and is quiet at idle (check 10 min). Inhibit/resume: a test copy with REGION_THR[7] set below the current battery temperature -> 'charging stopped: battery xx.x C outside -10..53 C' and current_now <= 0; restore the shipped file -> 'charging allowed'. Also run the guard with the usb-therm zone absent and confirm what it logs (B9).
- T6 Firmware alone (relay 015 item 3), PD charger, glmark2 + CPU load, 20 min, guard in dry-run: expect current taper below ~663 mA (iterm-ma) and status Full near 4.5 V at 16-35 C; if battery temperature enters 45-53 C, record whether current/float drop by themselves (stock fv 4130 mV, fccmax 1000 mA); if not, the guard is required (it caps 1000 mA and stops at 4.138 V) and B11(b) becomes a P0.
- T7 usb-therm plausibility (if the zone patch is in): at idle all usb zones within ~5 C of board_therm; during T3 they rise slowly; readings of 125000, 0 or negative = wrong channel/scale (B7).
- T8 Battery-estimate data for Reader A: during T1 at 100 % log current_now at 1 s for 60 s to reproduce the sign flips; record status, charge_full 13789 mAh and whether charge_now is exposed.

#### Open Questions
- Unit and acceptance of BATTMGR BATT_CHG_CTRL_LIM by the SOCCP firmware (uA assumed; decided by T4).
- What the raw USB_TYPE (6) returns on the Oplus firmware vs USB_ADAP_TYPE (7) (B3); safest is to switch the patch to USB_ADAP_TYPE before testing.
- Does the firmware keep OPLUS_CHG_EN=0 across its own JEITA/replug events, and does it ever re-enable charging by itself? (T4 covers replug only.)
- Does the SOCCP firmware apply JEITA float/current reduction and termination alone (T6)? Nothing in the queue sets fv-mv per region.
- Which sensor stock's 57 C really applies to: the FDT says usb_temp_adc_l/r (0x274a/0x275e, scale-fn-type 5); the OnePlusOSS usbtemp source is not on this machine (not found), so the 45 C gap floor and the L/R conversion remain unverified.
- Has any earlier run with a PD charger already been driven to 12 V by the current queue? pc-026 saw 'UCSI source 5 V PD' only; no 12 V evidence found.
- usb-therm patch ordering: rebase onto HEAD or queue relay 009 first (B6)?
- Stock treatment of Apple bricks (B12) - not in oplus,wired.

## Reader summary

READER C: 85 RAM boots (pc-011 D through area-audio-5) carry a qcom-battmgr dump, all with the PC's USB port attached: every one shows the OPLUS battmgr with USB_TYPE [SDP], INPUT_CURRENT_LIMIT 3 A (written by our driver), CURRENT_MAX 900 mA, and a measured input of 1.19-1.94 A at 4.55-4.77 V, i.e. 2.4-3.9x stock's 500 mA SDP limit (stock: usb CURRENT_NOW 494 mA, INPUT_CURRENT_LIMIT 500 mA). Battery temperature stayed 27-36 degC, voltage <= 4.478 V (stock stop 4.508 V), no battmgr errors after 0028. The battery CURRENT_NOW is an uncached-at-1-Hz instantaneous gauge word (the driver negates the OPLUS word, which in stock reads -411 mA while charging), so mainline positive = charging (ABI convention) is the best-supported reading: the early boot storm pages are 80/85 negative, the settled 60 s heartbeats 53/64 positive, and at 100 % it hovers -347..+232 mA; swings of +-500 mA within a minute at constant state prove it is not averaged. The reported '1-s' flip sequence is actually four samples 30-90 s apart from two boots. STATUS is forced to Charging whenever USB is online (driver code), never Full/Discharging; TIME_TO_*, CHARGE_NOW/COUNTER, CURRENT_AVG, VOLTAGE_*_DESIGN, TECHNOLOGY are absent, so UPower derives 'time to full 4.5 h' from an instantaneous 0.617 A. No discharge, PD, CDP or DCP data exists at all; no usb/skin/vbat/BCL thermal zone exists (stock has usb, battery, vbat 2.8/2.6/2.3 V, ibat 13.5/15 A, sys-therm-2 48-61 degC, shell_*). The area run must add: a 1 Hz sysfs+upower log while charging AND while discharging (cable out, Wi-Fi ssh), a sign check by unplugging, per-charger-type attach logs with the relay 015 patch (input <= stock per type, PDO <= 9 V), a top-off/termination log at 100 %, and the usb-therm zone reading.

### C1 What the OPLUS battmgr exposes today (bat/usb/wls/ucsi), units and values (high, fact)

- Claim: qcom-battmgr-bat exposes STATUS, HEALTH, PRESENT, CYCLE_COUNT, VOLTAGE_NOW (uV since 0029), CURRENT_NOW (uA), CHARGE_FULL_DESIGN (uAh, DT since 0039), CHARGE_FULL (uAh), CAPACITY (%), TEMP (0.1 degC), STATE_OF_HEALTH (%); qcom-battmgr-usb exposes ONLINE, VOLTAGE_MAX, VOLTAGE_NOW, CURRENT_MAX, CURRENT_NOW, INPUT_CURRENT_LIMIT, USB_TYPE; a wls supply (offline) and the UCSI source psy also exist. hwmon mirrors bat/usb/wls.
- Mainline: 11 battery props; usb 4.75 V / 1.24 A typical; CHARGE_FULL 13786000-13789000 uAh; CHARGE_FULL_DESIGN 13380000 uAh (DT); SOH 100; cycle count 5
- Stock: stock battery psy (LineageOS capture) additionally: CHARGE_TYPE=Fast, VOLTAGE_OCV, VOLTAGE_MAX, TECHNOLOGY=Li-ion, CHARGE_COUNTER=6313000, TIME_TO_FULL_AVG/NOW, TIME_TO_EMPTY_AVG, POWER_NOW/AVG, CHARGE_NOW, VOLTAGE_MIN, CAPACITY_LEVEL; CHARGE_FULL_DESIGN 13380000, CHARGE_FULL 13789000, CYCLE_COUNT 0
- Safety: none
- Action: Use this list as the baseline for reader A's 'what could be exposed' work; the area run's first log is a complete `grep -r . /sys/class/power_supply/*/` plus `upower -d` at t0.
- Test: At boot with the charger in: dump all four supplies (uevent + every attribute) and `upower -d`; repeat once at 100 % and once with the cable out.
- Evidence: /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:11-22; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:34-41; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:70-80; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-extra.txt:117-118; /home/user/iceland-mainline/docs/tests/linux-runpc11/D/linux-power.txt:15-18; /home/user/iceland-mainline/relay/results/pc-018-019-takeover-features.md:71

### C2 Properties UPower/GNOME want that are missing on mainline (high, inference)

- Claim: Absent on qcom-battmgr-bat in every dump: CHARGE_NOW (dropped by 0039 because the gauge word is garbage), CHARGE_COUNTER, TIME_TO_FULL_NOW/AVG, TIME_TO_EMPTY_NOW/AVG, CURRENT_AVG, POWER_NOW, VOLTAGE_MIN_DESIGN/VOLTAGE_MAX_DESIGN, TECHNOLOGY, CAPACITY_LEVEL, and STATUS=Full. UPower therefore builds energy from CAPACITY x CHARGE_FULL x present VOLTAGE_NOW and the rate from the instantaneous CURRENT_NOW x VOLTAGE_NOW, so its time estimate follows every current spike and its energy-full wobbles with the terminal voltage.
- Mainline: no CHARGE_NOW/CHARGE_COUNTER/TIME_TO_*/CURRENT_AVG/VOLTAGE_*_DESIGN; upower at 80 %: 2.646 W = 0.617 A x 4.289 V, 'time to full 4.5 h' (20 % of 13.789 Ah x 4.289 V = 11.8 Wh / 2.646 W = 4.47 h)
- Stock: CHARGE_COUNTER 6313000 uAh at 48 % (= 48 % of ~13.15 Ah, a real remaining charge exists in the stack); TIME_TO_* present but 0/3600 (placeholders); CHARGE_NOW=4968 (unit not found)
- Safety: none
- Action: For the estimate, the smallest correct set is: a smoothed current (CURRENT_AVG or a driver-side moving average over >= 30 s used for POWER_NOW), CHARGE_NOW derived as CAPACITY x CHARGE_FULL (or the correct gauge word once identified), VOLTAGE_MAX_DESIGN/VOLTAGE_MIN_DESIGN from the DT battery node, TECHNOLOGY=Li-ion, and STATUS=Full when CAPACITY=100 and the charger is in. The area run must first record which gauge word tracks the remaining charge.
- Test: Log all 128 OPLUS gauge words (a debug dump, read-only) once per minute over a 20-30 % charge swing; the word that moves by ~137.9 mAh per % is the remaining charge (stock CHARGE_COUNTER analog).
- Evidence: /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:9-22; /home/user/iceland-mainline/relay/results/pc-026-critical-items.md:38; /home/user/iceland-mainline/docs/tests/linux-runpc26e/probe/s3-probe-20260929-063955.txt:84-92; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1791-1797; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/power-supply.txt:16-27

### C3 Sign convention of CURRENT_NOW on this firmware: mainline positive = charging (ABI), stock negative = charging (high, inference)

- Claim: The driver reports -(gauge word) x 1000. Stock (the same firmware read by the OPLUS driver) shows CURRENT_NOW=-411 mA while STATUS=Charging on a 494 mA SDP input, i.e. the OPLUS raw convention is negative-while-charging; the negation therefore yields the Linux ABI convention (positive = into the battery). The empirical distribution fits this: the early survey pages (taken ~20-25 s into the boot storm, all cores busy) are 80/85 negative (-350..-987 mA = the input-limited USB port cannot carry the boot load, the battery buffers), the settled 60 s heartbeats are 53/64 positive (+330..+690 mA at 44 % = 5.9 W in minus the system), and at 100 % the value hovers -347..+232 mA around zero (top-off vs load). Counter-evidence: the no-display runs show the largest negatives (-950/-987 mA) at the survey time, which is unexplained by display power alone; the sign has never been confirmed by a discharge (cable out) sample.
- Mainline: survey pages: 80 negative / 5 positive; 60 s heartbeats: 11 negative / 53 positive; at 100 %: -347 .. +232 mA (n~100 heartbeat samples)
- Stock: -411 mA while Charging at 48 % on a 494 mA SDP input (OPLUS convention: negative = charging); 'Max charging current: 500000' in dumpsys
- Safety: none for the firmware; a wrong sign in the guard's 'is it still charging after inhibit' check would be fail-open, so the sign must be proven before the guard relies on current_now
- Action: Treat 'positive = charging' as the working hypothesis and prove it with the cheapest possible test before any guard logic or UPower patch depends on it; also compare against the ADSP's standard BATT_CURR_NOW property in the same second (the sm8350 map reads it) to see whether the firmware offers an averaged current with a defined sign.
- Test: With ssh over Wi-Fi: log bat CURRENT_NOW/STATUS and usb ONLINE at 1 Hz, pull the USB cable for 60 s, plug it back. Pass: the value is negative (hundreds of mA, tablet load) for the whole unplugged minute and turns positive within seconds of replug; STATUS must read Discharging while unplugged. Then re-read: if the sign is the other way round, 0029/the OPLUS negation is wrong and must be flipped.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:1793; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/power-supply.txt:5-13, 54-56; /home/user/iceland-mainline/docs/tests/linux-runpc11/D/late-dmesg.txt:1007, 1224; /home/user/iceland-mainline/docs/tests/linux-runpc11/D/linux-power.txt:16; /home/user/iceland-mainline/docs/tests/linux-runpc18/ND1/linux-power.txt:16, 38; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-dmesg.txt:last line; /home/user/iceland-mainline/relay/results/pc-011-battery-gpu.md:42

### C4 CURRENT_NOW is an instantaneous 1 Hz gauge sample, not an average; the '1-s flip' sequence is actually four samples 30-90 s apart from two boots (high, fact)

- Claim: The driver re-reads the OPLUS gauge snapshot at most once per second (jiffies + HZ cache) and reports the raw word; at a constant state (100 %, same SDP port, idle GNOME) consecutive heartbeats 30-60 s apart differ by up to 580 mA, and at 44 % by up to 780 mA (-95 .. +688). No 1 Hz series exists in any log: the reported -519 / +232 / -347 / +138 mA are area-audio-4's survey page and area-audio-5's 30 s, 60 s and 120 s heartbeats.
- Mainline: 1 Hz cache, raw gauge word; spread within one boot at constant state: 44 %: -95..+688 mA; 100 %: -347..+232 mA; the USB input reading varies too (1.191-1.937 A)
- Stock: stock exposes the same instantaneous word plus a TIME_TO_EMPTY_AVG placeholder; the OPLUS stack averages in userspace/its own driver (not captured)
- Safety: none
- Action: The area run must produce the first true 1 Hz series (bat+usb current/voltage, STATUS, CAPACITY, TEMP, plus `upower -i` every 5 s) for >= 20 min charging and >= 20 min discharging so reader A can size the averaging window; any battmgr patch should expose the average as CURRENT_AVG/POWER_NOW rather than smoothing CURRENT_NOW (ABI says CURRENT_NOW is unsmoothed).
- Test: 1 Hz loop: `date +%s; cat bat/{status,capacity,voltage_now,current_now,temp} usb/{online,voltage_now,current_now,current_max,input_current_limit,usb_type}` for 20 min at ~50 % charging on a known charger, then 20 min discharging (cable out, Wi-Fi ssh, screen on, `stress-ng -c 2` for a steady load); in parallel `upower -i <bat>` every 5 s to correlate the 'time to' jumps with the current spikes.
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:496-505; /home/user/iceland-mainline/docs/tests/area-audio-4/AreaAudio4/linux-power.txt:16; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/late-dmesg.txt:1314, 1517, 1590; /home/user/iceland-mainline/relay/answers/area-audio-5.md:26-27; /home/user/iceland-mainline/docs/tests/linux-runpc21/relay-side/stream-12-202124.txt:iceland-batt lines (4 per stream)

### C5 STATUS is forced to Charging whenever USB is online; Full/Not charging/Discharging are never reported with the cable in (high, fact)

- Claim: The OPLUS branch of qcom_battmgr rewrites DISCHARGING to CHARGING when usb.online, and CHARGING to DISCHARGING when not online. Consequently all 85 survey pages and every heartbeat read STATUS=Charging, including at 100 % / 4.47 V where the net battery current is around zero, and no run ever shows Full. UPower/GNOME therefore show 'charging' with a time-to-full at 100 % and cannot show 'fully charged'.
- Mainline: STATUS=Charging in 85/85 pages and all heartbeats (44-100 %); 0 samples of Full, Not charging or Discharging
- Stock: stock reports STATUS=Charging with CHARGE_TYPE=Fast at 48 %; stock's behaviour at 100 % is not captured (not found)
- Safety: fail-safe for the firmware; misleading for the user (no 'full' indication) and it hides a charger that stopped (e.g. after a thermal stop) behind 'Charging'
- Action: Reader A: derive STATUS from the firmware word first and only fall back to the online heuristic when the firmware says Unknown; report Full at CAPACITY=100 with |current| below a threshold, and Not charging when online but the current is <= 0 for N seconds (this is also what the guard needs to verify an inhibit).
- Test: At 100 % with the charger in, log the raw firmware BATT_STATUS value (dyndbg on qcom_battmgr) next to the sysfs STATUS at 1 Hz for 10 min; then write `inhibit-charge` (relay 015 candidate) and confirm the raw status changes while sysfs still says Charging (or not).
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:640-647; /home/user/iceland-mainline/docs/tests/linux-runpc26o/S13/linux-power.txt:11, 19; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/late-dmesg.txt:1517

### C6 Only one charger type has ever been seen: the PC's USB port typed SDP, Type-C default current; no PD, CDP, DCP data exists (high, fact)

- Claim: All 85 dumps: qcom-battmgr-usb USB_TYPE=[SDP], VOLTAGE_MAX 5 V, CURRENT_MAX 900 mA; the UCSI source psy shows the partner as USB_TYPE [C] at 5 V / 100 mA (a Type-C default-USB source, no PD contract). The tablet is always cabled to the Windows PC for the NCM relay link, so no other charger and no discharge state was ever sampled. The queued driver's PDO requests (12 V, then 9 V) at every attach are therefore untested, and the SoCCP 'charger_pd' path has no evidence either way.
- Mainline: SDP only; partner 5 V / 100 mA Type-C default; PDO 12 V/9 V requests are sent but cannot be answered by this port
- Stock: same port under stock: usb VOLTAGE_NOW 4.965 V, CURRENT_NOW 494 mA, INPUT_CURRENT_LIMIT 500 mA, ucsi source 5 V / 100 mA [C]
- Safety: could over-charge (unknown): the PD path (12 V request in the queued code, 9 V cap in the candidate) has never run on this tablet
- Action: The area run needs the user with three sources: the PC port (SDP), a PD wall charger (the OnePlus one or any 9 V-capable), and a 5 V-only wall cube (DCP/CDP); each attach logged with the relay 015 patch applied and the cable/charger watched. Fail-safe rule: if the negotiated VBUS exceeds 9.5 V or the input exceeds the stock per-type limit by > 10 % for > 5 s, unplug and stop the area run.
- Test: Per source: attach, then 1 Hz log of usb VOLTAGE_NOW/CURRENT_NOW/CURRENT_MAX/INPUT_CURRENT_LIMIT/USB_TYPE, the UCSI source psy, `cat /sys/class/typec/port0-partner/usb_power_delivery/*` if present, and dyndbg of qcom_battmgr (OPLUS_SET_PDO answers) for 3 min; expected with the candidate: PD -> <= 9 V and <= 1.5 A at 9 V / 2 A at 5 V; DCP <= 2 A; CDP <= 1.5 A; SDP <= 500 mA.
- Evidence: /tmp/claude-0/-home-user/7da4e007-e5ba-51a8-aec0-c5128226301b/scratchpad/battmgr-table.txt:1-85 (derived from docs/tests/*/linux-power.txt); /home/user/iceland-mainline/docs/tests/linux-runpc11/D/linux-power.txt:73-79; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1837-1851; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-extra.txt:43-44

### C7 UNSAFE-BY-STOCK-STANDARDS: the tablet draws 1.19-1.94 A from an SDP-typed port (stock 500 mA) because the queued driver writes a 3 A input limit at every attach (high, fact)

- Claim: Every dump shows INPUT_CURRENT_LIMIT=3000000 (the OnePlus 15 value OPLUS_CHARGER_ICL_UA written by qcom_battmgr_oplus_setup_charger, together with a 4 A FCC), and the firmware obeys: measured input 1.191-1.937 A (median 1.241 A) against CURRENT_MAX=900 mA (what the firmware itself derived for the port) and against stock's 500 mA (power-mw 2500 for SDP). VBUS sags to 4.55-4.62 V when the draw reaches 1.7-1.9 A (S5-S7, ND2), a sign the source is overloaded. This is the strongest safety finding so far and it is exactly what the relay 015 candidate replaces with the stock per-type table; the candidate is untested.
- Mainline: ICL written 3 A, FCC written 4 A, PDO 12 V then 9 V requested; measured 1.24 A median / 1.94 A max at 4.55-4.77 V on an SDP port (2.4-3.9x stock)
- Stock: SDP 500 mA (2.5 W), CDP 1.5 A, DCP 2 A, PD 2 A at 5 V / 1.5 A at 9 V; FCC SDP 600 / CDP 1600 / DCP 2200 / PD 3300 mA; measured 494 mA on the same port
- Safety: could over-charge the source/cable (overdraw of a 500-900 mA port; VBUS sag observed); battery-side FCC 4 A vs stock 3300 mA max is also above stock
- Action: Treat the relay 015 candidate as the first kernel to boot in the area run and make its pass criterion 'input <= stock per type on every source'; until it passes, keep charging attended and prefer the PC port (which cannot be asked for > 5 V). Reader B should confirm the candidate also lowers FCC to the stock table and that a failed OPLUS_PROPERTY_SET leaves the firmware default (900 mA CURRENT_MAX), not 3 A.
- Test: Boot the candidate on the PC port: within 60 s usb INPUT_CURRENT_LIMIT must read 500000 and CURRENT_NOW must settle <= 500 mA (VBUS >= 4.7 V); log 1 Hz for 5 min; then repeat on the PD and 5 V wall sources (C6).
- Evidence: /home/user/k45/drivers/power/supply/qcom_battmgr.c:147-148, 1844-1846; /home/user/iceland-mainline/docs/tests/linux-runpc18/ND2/linux-power.txt:36-39; /home/user/iceland-mainline/docs/tests/linux-runpc26g/S5/linux-power.txt:36-38; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/power-supply.txt:52-56; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/dumpsys-battery.txt:6-8; /home/user/iceland-mainline/docs/research/battery-guard-verification.md:14-15, 50; /home/user/iceland-mainline/relay/requests/015-iterate-1-4.md:36-41

### C8 Battery temperature and voltage stayed inside the stock regions in every run (medium, fact)

- Claim: Across all 85 survey pages and the late pages the battery TEMP was 27.0-36.0 degC (26 pages at 30.0, one at 36.0 in Y10 at 40 %/-498 mA), VOLTAGE_NOW peaked at 4.478 V at 99 % (4.470 V at 100 %), HEALTH=Good everywhere. Stock stops charging at 4.508 V in the 0-35 degC region, 4.488 V at 35-45 degC, OV at 4.600 V; the 36.0 degC sample would already be in stock's R6 band (stop 4.488 V), still above the observed maximum. No sample exceeded a stock limit.
- Mainline: TEMP 27.0-36.0 degC; VOLTAGE_NOW max 4.478 V (99 %), 4.470 V (100 %); HEALTH Good
- Stock: stop 4.508 V (0-35 degC) / 4.488 V (35-45 degC) / 4.138 V (45-53 degC); OV 4.600 V; no charging >= 53 degC; poweroff 72/77 degC
- Safety: fail-safe so far (firmware tops off at 4.47-4.48 V, below every stock stop); but no run ever charged under load or above 36 degC, so the warm bands are untested
- Action: Keep the 4.508 / 4.488 / 4.600 V and 53 degC numbers as the pass/abort thresholds of the area run's charging-under-load log; abort and unplug at 4.50 V or 45 degC battery in the first session (one region below the stock stop) until the guard is proven on the tablet.
- Test: Charging under load (glmark2 + 4 CPU busy loops) for 20 min from ~50 % on the PD source with the candidate: 1 Hz bat TEMP/VOLTAGE/CURRENT; pass = temperature rise < 10 K, voltage never > 4.50 V, current reduced by the firmware when TEMP crosses 35.0 degC (stock R6) if it gets there.
- Evidence: /tmp/claude-0/-home-user/7da4e007-e5ba-51a8-aec0-c5128226301b/scratchpad/battmgr-table.txt:derived: TEMP histogram; /home/user/iceland-mainline/docs/tests/linux-runpc24j/Y10/linux-power.txt:15-20; /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:15, 19-20; /home/user/iceland-mainline/docs/research/battery-guard-verification.md:23-33

### C9 Thermal zones: mainline has a battery zone (no trips) and the charger PMIC die; no usb, skin/shell, vbat or BCL/ibat zone yet (medium, fact)

- Claim: The latest zone list (63 zones) contains qcom-battmgr-bat (30.0 degC, no trips, no cooling), pmih0108-thermal (charger PMIC die, 37 degC, trips 95/115/145 degC), pmh0101-thermal, board-thermal and flash-thermal (0032), but no usb/connector zone, no skin/shell zones, no vbat or ibat/BCL zones. Stock has type=usb (2800 = 28.00 degC in its units), type=battery, vbat with 2.8/2.6/2.3 V passive trips, pmih010x-ibat-lvl0/1 at 13.5/15 A, pmh0101/pmih010x-bcl-lvl0-2, shell_front/frame/back, and sys-therm-2 with 48/49/50/60/61/90 degC trips. The relay 015 usb-therm candidate would add the first of these.
- Mainline: battery zone 30.0 degC without trips; pmih0108 37 degC; no usb/skin/vbat/ibat/bcl zones
- Stock: usb 28.00 degC zone; battery 31.1 degC; vbat 2.8/2.6/2.3 V; ibat 13.5/15 A; sys-therm-2 48/49/50/60/61 degC; shell_* virtual zones
- Safety: fail-safe today only because the guard reads the battery temp directly; the connector-temperature stop (57 degC stock) has no input until the usb-therm zone lands
- Action: Include the usb-therm candidate in the same kernel as the limits candidate and log its zone next to board-thermal and pmih0108; the guard's connector rule stays disabled (fail-safe = 'no reading -> no charging' is too strict for a missing zone, so gate it on the zone existing).
- Test: At idle: usb-therm within +-3 K of board-thermal; during the 20 min charging-under-load log it must rise monotonically with the input power and stay far below 57 degC; verify the ADC channel by touching nothing else (a swapped channel would track the board, not the connector).
- Evidence: /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-thermal.txt:52, 59-62; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/thermal-zones.txt:55, 56-60, 61-63, 70, 89, 91; /home/user/iceland-mainline/relay/results/pc-026-critical-items.md:40; /home/user/iceland-mainline/relay/requests/015-iterate-1-4.md:46-48

### C10 No battmgr/pmic-glink errors or timeouts in any run since 0028; PD availability of the SoCCP has no evidence (low, fact)

- Claim: With dyndbg enabled on qcom_battmgr, pmic_glink, altmode and ucsi_glink in most kits, the only pmic-glink diagnostics ever logged are the pre-0028 race (rpmsg_dev_probe -517/-19, 'no pmic_glink device to attach to'), the harmless 'Failed to create device link ... a600000.usb' and 'UCSI version unknown'. No 'invalid fuel gauge snapshot length', no request timeout, no -ENODATA appears in the survey dmesgs or in the full 2220-line S3 session log. Nothing in any log speaks to a PD contract ('charger_pd'): not found.
- Mainline: 0 battmgr warnings/timeouts in 85 boots; 'UCSI version unknown' x2; device-link warning x6
- Stock: n/a (the charger firmware log channel PMIC_LOGS_SOCCP_APPS is not read on mainline; KNOWLEDGE.md:434)
- Safety: none
- Action: Keep dyndbg on qcom_battmgr/pmic_glink/ucsi_glink for the area kits and add the UCSI partner PD capabilities to the survey; consider reading the SoCCP charger ulog channel (read-only) later for PD evidence.
- Test: Area run survey: `dmesg | grep -i 'battmgr\|pmic_glink\|ucsi'` at t+60 s and at the end; `ls /sys/class/typec/port0-partner/` with a PD charger attached.
- Evidence: /home/user/iceland-mainline/docs/tests/linux-runpc26e/probe/s3-dmesg-live.txt:473-474, 1301-1786; /home/user/iceland-mainline/relay/results/pc-010-survey.md:74-79; /home/user/iceland-mainline/relay/results/pc-011-battery-gpu.md:50-56; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1782-1787

### C11 CHARGE_NOW: gauge word 4 is not a charge (two distinct garbage values), while stock's stack does have a real remaining charge (medium, fact)

- Claim: Word 4 x 1000 read 1593286704 in almost every boot and -1653462592 in two (F5, Y1), independent of the 39-44 % state, so 0039 correctly hides it. Stock's CHARGE_COUNTER (6313000 uAh at 48 %) shows the OPLUS stack computes a remaining charge (~13.15 Ah x 48 %); stock's CHARGE_NOW=4968 has an unknown unit and does not equal 48 % of any capacity here.
- Mainline: word 4 = 1593286704 or -1653462592 (garbage); CHARGE_NOW hidden since 0039
- Stock: CHARGE_COUNTER 6313000 uAh at 48 %; CHARGE_NOW 4968 (unit not found)
- Safety: none
- Action: Until the right word is found, derive CHARGE_NOW = CAPACITY x CHARGE_FULL / 100 in the driver (monotone, good enough for UPower) and let the area run's 128-word dump identify a real remaining-charge word (C2 test).
- Test: Same as C2: 128-word snapshot once per minute across a 20 % swing; also compare against stock's charge counter by capturing the LineageOS/OxygenOS battery psy at the same percentage if the user boots stock in between (read-only adb).
- Evidence: /home/user/iceland-mainline/docs/tests/linux-runpc11/D/linux-power.txt:18-19; /home/user/iceland-mainline/docs/tests/linux-runpc19/F5/linux-power.txt:18; /home/user/iceland-mainline/relay/results/pc-016-020/batt-info.py:2-5; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/power-supply.txt:9, 16, 27

### C12 Discharge behaviour, percentage drift and the estimate while unplugged have never been observed (high, fact)

- Claim: Because the relay link is the USB cable, the tablet was online (USB) in 100 % of samples; the longest single boot with battery samples is the S2/S3 GNOME session (~17 min, 78-80 %). CAPACITY advanced 40 -> 44 % and 78 -> 100 % only between sessions (charged in Android); no within-boot percentage change, no discharge curve, no 'time to empty' from UPower exists.
- Mainline: 0 discharge samples; 0 within-boot CAPACITY changes; upower seen once (80 %, charging)
- Stock: stock TIME_TO_EMPTY_AVG=3600 placeholder (power-supply.txt:24); no stock discharge curve captured either
- Safety: none directly; the guard's low-voltage power-off (3.3 V) and BCL behaviour are untestable without a discharge
- Action: The area run needs Wi-Fi ssh (NetworkManager with the user's credentials, pc-026 has wlp1s0) so the cable can come out; plan a 20-30 min discharge at a steady load and a 1 Hz log, then a replug; never let it drop below 20 % in the first session.
- Test: Cable out, screen on, `stress-ng -c 2` or glmark2: 1 Hz bat log + `upower -i` every 5 s for 20 min; expected: CAPACITY falls monotonically ~1 % per 4-8 min, CURRENT_NOW sign constant (negative under the C3 hypothesis), STATUS=Discharging, UPower 'time to empty' within +-30 % of (CAPACITY x 13.79 Ah / |I|) once smoothed.
- Evidence: /tmp/claude-0/-home-user/7da4e007-e5ba-51a8-aec0-c5128226301b/scratchpad/battmgr-table.txt:1-85; /home/user/iceland-mainline/relay/results/pc-026-critical-items.md:75, 97, 103; /home/user/iceland-mainline/relay/results/area-audio.md:112

### C13 Minor deltas vs stock: cycle count 5 vs 0, CHARGE_FULL 13786 vs 13789 mAh, percent from SOC/100 (low, fact)

- Claim: Mainline reads CYCLE_COUNT=5 from gauge word 5 where stock's battery psy reported 0; CHARGE_FULL alternates 13789000/13786000 uAh between boots (stock 13789000); CAPACITY is the gauge SOC word divided by 100 (a 0.01 % resolution the firmware offers and the driver discards).
- Mainline: cycles 5; CHARGE_FULL 13786-13789 mAh; CAPACITY integer %
- Stock: cycles 0 (psy) ; CHARGE_FULL 13789 mAh; CAPACITY 48 at the capture
- Safety: none
- Action: No action; the 0.01 % SOC resolution could feed a smoother UPower percentage if reader A wants it (not required).
- Test: None beyond the C2 word dump.
- Evidence: /home/user/iceland-mainline/docs/tests/area-audio-5/AreaAudio5/linux-power.txt:14, 18; /home/user/iceland-mainline/docs/device-facts/lineage-20260928/power-supply.txt:17-19; /home/user/k45/drivers/power/supply/qcom_battmgr.c:1795

#### Test Plan
- T0 Baseline dump at boot (every area kit, automatic): all four power supplies' full attribute set + `upower -d` + `dmesg | grep -i 'battmgr\|pmic_glink\|ucsi'` at t+60 s; the same again at the end of the session (closes C1/C10).
- T1 Sign check (first thing, needs Wi-Fi ssh): 1 Hz log of bat STATUS/CURRENT_NOW/VOLTAGE_NOW and usb ONLINE; unplug the cable for 60 s, replug. Pass: negative current and STATUS=Discharging while unplugged, positive after replug (closes C3; if reversed, the 0029 negation is wrong and must be flipped before anything depends on it).
- T2 Relay 015 limits candidate on the PC port (SDP): within 60 s of boot INPUT_CURRENT_LIMIT must read 500000 and usb CURRENT_NOW must settle <= 500 mA with VBUS >= 4.7 V; 5 min 1 Hz log. Abort if the input stays > 900 mA (closes C7 for SDP). This is a safety fix: run it before any other charging test.
- T3 Per-source attach logs with the candidate (user present, cable watched): PD wall charger, 5 V-only cube (DCP/CDP), PC port; per source 3 min of usb VOLTAGE_NOW/CURRENT_NOW/CURRENT_MAX/INPUT_CURRENT_LIMIT/USB_TYPE, the UCSI source psy, `/sys/class/typec/port0-partner/usb_power_delivery/*`, dyndbg OPLUS_SET_PDO answers. Pass: PD <= 9 V, <= 2 A at 5 V / <= 1.5 A at 9 V; DCP <= 2 A; CDP <= 1.5 A; SDP <= 0.5 A. Abort/unplug rule: VBUS > 9.5 V or input > stock + 10 % for > 5 s (closes C6/C7).
- T4 Charging 1 Hz series for the estimate: 20 min from ~50 % on the PD source, screen on, idle GNOME: bat + usb 1 Hz, `upower -i` every 5 s; record how the 'time to full' jumps track the current spikes (sizes the averaging window; closes C4).
- T5 Discharge 1 Hz series: cable out, Wi-Fi ssh, steady load (`stress-ng -c 2` or glmark2), 20-30 min, stop at 20 %: same log + `upower -i`; pass = monotone CAPACITY, constant sign, STATUS=Discharging, UPower time-to-empty plausible (closes C12).
- T6 Top-off/termination at 100 %: with the charger in, 10 min 1 Hz log of bat STATUS/CURRENT_NOW/VOLTAGE_NOW and the raw firmware BATT_STATUS (dyndbg); note whether the firmware ever reports Full and whether the voltage stays <= 4.48 V (closes C5/C8 top end).
- T7 Gauge word identification: a read-only dump of all 128 OPLUS gauge words once per minute during T4 and T5; the word changing by ~137.9 mAh per % is the remaining charge; also capture the ADSP's standard BATT_CURR_NOW/BATT_CHG_COUNTER/BATT_TTF_AVG properties in the same second to see whether an averaged current exists (closes C2/C11).
- T8 Charging under load (only after T2/T3 pass, guard running in dry-run with logging): glmark2 + 4 CPU busy loops for 20 min on the PD source from ~50 %: 1 Hz bat TEMP/VOLTAGE/CURRENT + usb-therm/board/pmih0108 zones; abort and unplug at 4.50 V or 45 degC battery or 50 degC connector in the first session (stock stops are 4.508 V / 53 degC / 57 degC) (closes C8/C9).
- T9 usb-therm candidate check: at idle within +-3 K of board-thermal; rises with input power in T8; the zone exists before the guard's connector rule is enabled (closes C9).
- T10 Inhibit knob (relay 015 item 1): with the charger in, write `inhibit-charge` to charge_behaviour; pass = usb CURRENT_NOW drops to the system load and bat CURRENT_NOW turns negative within 5 s; `auto` restores; survives unplug/replug (needs T1's sign result first).

#### Open Questions
- Is the OPLUS gauge current word really OPLUS-signed (negative = charging) on the Pad 4's QBG gauge, so that the driver's negation gives ABI positive = charging? The distribution supports it but the no-display runs (-950/-987 mA at the survey time) do not fit cleanly; only T1 settles it.
- Why do the no-native-display runs (pc-018 ND1/ND3, pc-019 FD1) show the largest negative battery currents at the survey time, and why did ND2 draw 1.937 A at 4.552 V from the same PC port? (sampling-time difference vs a real load difference; not found in the logs)
- Does the firmware ever report STATUS=Full or Not charging on its own, or is it always 'lazy' as the driver comment says? (no raw BATT_STATUS value was ever logged)
- Which gauge word (if any) carries the remaining charge that stock reports as CHARGE_COUNTER=6313000 uAh, and what is stock's CHARGE_NOW=4968 unit?
- Does the ADSP standard property set (BATT_CURR_NOW, BATT_CHG_COUNTER, BATT_TTF_AVG/TTE_AVG, BATT_POWER_NOW) answer on this SoCCP firmware next to the OPLUS gauge read, giving an averaged current for free?
- What does the PC's USB port actually advertise (USB 3 SDP 900 mA per CURRENT_MAX vs a Type-C 1.5 A/3 A Rp)? The UCSI source psy says 100 mA [C]; a PD sink log with a real charger is needed to learn how the SoCCP negotiates.
- Does a failed OPLUS_PROPERTY_SET (e.g. firmware rejecting the ICL) leave the firmware at its own CURRENT_MAX-derived limit (900 mA) or at the last host value? (needed for the fail-safe argument of the candidate)
- Stock's behaviour at 100 % (termination voltage, recharge threshold, Full status) was not captured; only the 48 % snapshot exists.

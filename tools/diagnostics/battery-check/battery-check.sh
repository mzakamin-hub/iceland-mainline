#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
#
# battery-check.sh - READ-ONLY check of the battery reporting on the OnePlus Pad 4 (iceland) under mainline
# Linux: qcom_battmgr (kernel) -> /sys/class/power_supply -> UPower -> GNOME.
#
# Usage (as root, e.g. sudo):
#   sudo bash battery-check.sh                  10 min, a sample every 10 s, on battery (charger unplugged)
#   sudo bash battery-check.sh --minutes 20     longer run (better coulomb count)
#   sudo bash battery-check.sh --charger        the same while a charger is in (sign, input, charge limit)
#   sudo bash battery-check.sh --minutes 0      one snapshot only (dumps + the static checks)
#   options: --minutes N (default 10)  --interval S (default 10, 5..120)  --charger  --help
#
# What it does: dumps every power_supply property and UPower's view of the battery, then samples the battery,
# the USB input and UPower every S seconds for N minutes, and prints a PASS / CHECK / FAIL table:
#   internal consistency (power_now vs voltage_now x current_now, charge_now vs capacity, full vs design,
#   the sign of the current vs the status, temperature, UPower's energy scale, rate and time estimates),
#   the coulomb count (integrated current vs the change of charge_now and of capacity) and the integrated power.
#
# Safety / privacy (by construction):
#   - writes NOTHING outside /var/tmp/battery-check-<time>/ (no sysfs write, no charging setting is touched;
#     the only commands run are cat / upower -i / upower -e / upower --version / dmesg / date / sleep / python3);
#   - reads no debugfs and no regmap file at all;
#   - prints and stores no serial number, no MAC / BD address and no network name (serial lines are dropped,
#     anything that looks like a MAC address is masked, only the tablet's own battery / line-power devices of
#     UPower are dumped, never peripherals).
# Make sure that nothing heavy starts or stops during the run (the check measures the load).

set -u
export LC_ALL=C

MINUTES=10
INTERVAL=10
MODE=battery
while [ $# -gt 0 ]; do
	case "$1" in
	--minutes) MINUTES="${2:-}"; shift 2 ;;
	--minutes=*) MINUTES="${1#*=}"; shift ;;
	--interval) INTERVAL="${2:-}"; shift 2 ;;
	--interval=*) INTERVAL="${1#*=}"; shift ;;
	--charger) MODE=charger; shift ;;
	-h|--help) sed -n '2,27p' "$0"; exit 0 ;;
	*) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
	esac
done
case "$MINUTES" in ''|*[!0-9]*) echo "--minutes needs a whole number" >&2; exit 2 ;; esac
case "$INTERVAL" in ''|*[!0-9]*) echo "--interval needs a whole number" >&2; exit 2 ;; esac
[ "$INTERVAL" -ge 5 ] && [ "$INTERVAL" -le 120 ] || { echo "--interval must be 5..120 s" >&2; exit 2; }
[ "$MINUTES" -le 600 ] || { echo "--minutes must be at most 600" >&2; exit 2; }
command -v python3 >/dev/null || { echo "python3 is needed for the analysis" >&2; exit 2; }
[ "$(id -u)" -eq 0 ] || echo "note: not root - the kernel log part will be empty (run with sudo)" >&2

PS=/sys/class/power_supply
BAT=$PS/qcom-battmgr-bat
USB=$PS/qcom-battmgr-usb
[ -d "$BAT" ] || BAT=$(for d in "$PS"/*; do [ "$(cat "$d/type" 2>/dev/null)" = Battery ] && { echo "$d"; break; }; done)
[ -n "$BAT" ] && [ -d "$BAT" ] || { echo "no battery power supply found under $PS" >&2; exit 1; }

STAMP=$(date +%Y%m%d-%H%M%S)
OUT=/var/tmp/battery-check-$STAMP
umask 022
mkdir -p "$OUT" || { echo "cannot create $OUT" >&2; exit 1; }

# mask anything that looks like a MAC / BD address (aa:bb:cc:dd:ee:ff, AA_BB_..., aa-bb-...) and drop serial lines
mask() {
	sed -E -e '/[Ss][Ee][Rr][Ii][Aa][Ll]/d' \
		-e 's/[0-9A-Fa-f]{2}([:_-][0-9A-Fa-f]{2}){5}/XX:XX:XX:XX:XX:XX/g'
}

# one sysfs value, with a timeout (qcom_battmgr answers a read from the ADSP; a stalled ADSP must not hang us)
rd() { timeout 3 cat "$1" 2>/dev/null | head -c 200 | tr -d '\n'; }

# every readable attribute file of every power supply (no subdirectories, no serial_number)
dump_supplies() {
	local d f n
	for d in "$PS"/*; do
		echo "### $(basename "$d")"
		for f in "$d"/*; do
			n=$(basename "$f")
			[ -f "$f" ] && [ -r "$f" ] || continue
			case "$n" in uevent|serial_number|*serial*) continue ;; esac
			printf '%s=%s\n' "$n" "$(rd "$f")"
		done
		echo
	done | mask
}

# UPower: only the tablet's own battery, its line-power supplies and the display device (no peripherals)
upower_paths() {
	upower -e 2>/dev/null | grep -E '/(battery_qcom[^/]*|line_power_[^/]*|DisplayDevice)$'
}
upower_dump() {
	upower --version 2>/dev/null | head -2
	local p
	for p in $(upower_paths); do
		echo "### $p"
		timeout 10 upower -i "$p" 2>/dev/null
	done
	echo "### daemon"
	timeout 10 upower -d 2>/dev/null | sed -n '/^Daemon:/,$p'
}

BATP=$(upower -e 2>/dev/null | grep -E '/battery_qcom[^/]*$' | head -1)
[ -n "$BATP" ] || BATP=$(upower -e 2>/dev/null | grep -E '/battery_BAT|/battery_' | grep -v -E 'hid|dev_|headset|mouse|keyboard' | head -1)

echo "battery-check: mode $MODE, $MINUTES min, a sample every $INTERVAL s; output in $OUT"
echo "  battery $(basename "$BAT"), UPower device ${BATP:-<none>}"
{
	echo "mode=$MODE minutes=$MINUTES interval=$INTERVAL start=$(date -Is)"
	echo "kernel=$(uname -r)"
	rpm -q iceland-device upower 2>/dev/null
} > "$OUT/run-info.txt"

dump_supplies > "$OUT/supplies-start.txt"
upower_dump 2>&1 | mask > "$OUT/upower-start.txt"
# the battery's own uevent (all properties in one read), masked
timeout 3 cat "$BAT/uevent" 2>/dev/null | mask > "$OUT/bat-uevent-start.txt"

BATPROPS="status capacity voltage_now current_now power_now charge_now charge_full charge_full_design energy_now energy_full energy_full_design voltage_max_design voltage_min_design temp health cycle_count state_of_health charge_behaviour charge_control_start_threshold charge_control_end_threshold constant_charge_current_max"
USBPROPS="online present voltage_now current_now input_current_limit usb_type"

sample() {
	local p
	echo "=== t=$(date +%s.%N)"
	for p in $BATPROPS; do [ -e "$BAT/$p" ] && echo "bat.$p=$(rd "$BAT/$p")"; done
	if [ -d "$USB" ]; then
		for p in $USBPROPS; do [ -e "$USB/$p" ] && echo "usb.$p=$(rd "$USB/$p")"; done
	fi
	echo "=== t2=$(date +%s.%N)"
	if [ -n "$BATP" ]; then
		timeout 10 upower -i "$BATP" 2>/dev/null | grep -E '^\s+(state|energy|energy-full|energy-full-design|energy-rate|voltage|percentage|time to empty|time to full|capacity|charge-cycles):' | sed -E 's/^\s+/up./'
	fi
}

N=$(( MINUTES * 60 / INTERVAL ))
[ "$MINUTES" -eq 0 ] && N=0
: > "$OUT/samples.txt"
sample >> "$OUT/samples.txt"
i=0
next=$(date +%s)
while [ "$i" -lt "$N" ]; do
	next=$(( next + INTERVAL ))
	now=$(date +%s)
	[ "$next" -gt "$now" ] && sleep $(( next - now ))
	sample >> "$OUT/samples.txt"
	i=$(( i + 1 ))
	if [ $(( i % 6 )) -eq 0 ] || [ "$i" -eq "$N" ]; then
		printf '  sample %d / %d: %s %s%%, %s uA\n' "$i" "$N" "$(rd "$BAT/status")" "$(rd "$BAT/capacity")" "$(rd "$BAT/current_now")"
	fi
done

dump_supplies > "$OUT/supplies-end.txt"
upower_dump 2>&1 | mask > "$OUT/upower-end.txt"
if [ "$(id -u)" -eq 0 ]; then
	dmesg 2>/dev/null | grep -i -E 'battmgr|pmic_glink|charge limit' | tail -60 | mask > "$OUT/kernel-log.txt"
fi

python3 -I - "$OUT" "$MODE" <<'PY' | tee "$OUT/report.txt"
import re, sys, statistics as st

out, mode = sys.argv[1], sys.argv[2]

def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

def dur(s):
    """UPower's '14.2 hours' / '35.0 minutes' / '50 seconds' / '1.2 days' -> seconds"""
    if not s:
        return None
    m = re.match(r'([\d.]+)\s*(second|minute|hour|day)', s)
    if not m:
        return None
    return float(m.group(1)) * {"second": 1, "minute": 60, "hour": 3600, "day": 86400}[m.group(2)]

samples = []
cur = None
for line in open(out + "/samples.txt", errors="replace"):
    line = line.rstrip("\n")
    if line.startswith("=== t="):
        cur = {"t": float(line[6:])}
        samples.append(cur)
        continue
    if line.startswith("=== t2=") or cur is None:
        continue
    if line.startswith("up."):
        k, _, v = line[3:].partition(":")
        cur["up." + k.strip()] = v.strip()
    elif "=" in line:
        k, _, v = line.partition("=")
        cur[k] = v

def g(s, k):
    return num(s.get(k))

rows = []
def row(name, verdict, detail):
    rows.append((name, verdict, detail))

if not samples:
    print("no samples - nothing to check")
    sys.exit(1)

s0, s1 = samples[0], samples[-1]
T = s1["t"] - s0["t"]
online = [g(s, "usb.online") for s in samples]
n_online = sum(1 for o in online if o == 1)
print()
print("battery-check report (%s mode, %d samples over %.1f min)" % (mode, len(samples), T / 60))
print()

# 1. presence
need = ["status", "capacity", "voltage_now", "current_now", "power_now", "charge_now", "charge_full", "temp"]
missing = [p for p in need if s0.get("bat." + p, "") == ""]
row("properties present", "PASS" if not missing else "FAIL",
    "all of %s" % ", ".join(need) if not missing else "missing or unreadable: " + ", ".join(missing))

# 2. units / scaling plausibility
probs = []
def rng(key, lo, hi, unit, scale):
    v = g(s0, key)
    if v is None:
        return
    if not (lo <= v <= hi):
        probs.append("%s=%g (expected %g..%g %s)" % (key, v, lo, hi, unit))
rng("bat.voltage_now", 3.0e6, 4.7e6, "uV", 1)
rng("bat.current_now", -10e6, 10e6, "uA", 1)
rng("bat.charge_full", 5e6, 20e6, "uAh", 1)
rng("bat.charge_now", 0, 20e6, "uAh", 1)
rng("bat.capacity", 0, 100, "%", 1)
rng("bat.temp", -200, 700, "0.1 C", 1)
v0, i0 = g(s0, "bat.voltage_now"), g(s0, "bat.current_now")
row("units / scaling", "PASS" if not probs else "FAIL",
    "V %.3f V, I %+.0f mA, full %.0f mAh, now %.0f mAh, T %.1f C" % (
        (v0 or 0) / 1e6, (i0 or 0) / 1e3, (g(s0, "bat.charge_full") or 0) / 1e3,
        (g(s0, "bat.charge_now") or 0) / 1e3, (g(s0, "bat.temp") or 0) / 10) if not probs else "; ".join(probs))

# 3. power_now vs V x I (same sample)
errs, signs_bad = [], 0
for s in samples:
    v, i, p = g(s, "bat.voltage_now"), g(s, "bat.current_now"), g(s, "bat.power_now")
    if None in (v, i, p):
        continue
    vi = v * i / 1e6
    errs.append(abs(p - vi) / max(abs(vi), 50000.0))
    if p != 0 and vi != 0 and (p > 0) != (vi > 0):
        signs_bad += 1
if errs:
    worst = max(errs)
    verdict = "PASS" if worst <= 0.05 and not signs_bad else ("CHECK" if worst <= 0.15 and not signs_bad else "FAIL")
    row("power_now = V x I", verdict, "worst deviation %.1f %% (median %.1f %%), sign mismatches %d of %d" % (
        100 * worst, 100 * st.median(errs), signs_bad, len(errs)))
else:
    row("power_now = V x I", "CHECK", "power_now, voltage_now or current_now unreadable")

# 4. charge_now / charge_full vs capacity
d = []
for s in samples:
    c, f, cap = g(s, "bat.charge_now"), g(s, "bat.charge_full"), g(s, "bat.capacity")
    if None not in (c, f, cap) and f > 0:
        d.append(100 * c / f - cap)
if d:
    w = max(d, key=abs)
    row("charge_now/full vs capacity", "PASS" if all(-0.5 <= x <= 1.5 for x in d) else ("CHECK" if abs(w) <= 3 else "FAIL"),
        "charge_now/charge_full - capacity: worst %+.2f points (capacity is the gauge SoC rounded down)" % w)
else:
    row("charge_now/full vs capacity", "CHECK", "no charge_now / charge_full / capacity")

# 5. full vs design
f, dsg = g(s0, "bat.charge_full"), g(s0, "bat.charge_full_design")
if f and dsg:
    r = f / dsg
    vd = "PASS" if 0.80 <= r <= 1.10 else ("CHECK" if 0.70 <= r <= 1.15 else "FAIL")
    note = "" if abs(dsg - 13380000) < 1000 else "; design is not stock's 13380 mAh"
    if note:
        vd = "CHECK" if vd == "PASS" else vd
    row("charge_full vs design", vd, "full %.0f mAh / design %.0f mAh = %.3f%s" % (f / 1e3, dsg / 1e3, r, note))
else:
    row("charge_full vs design", "CHECK", "charge_full_design not exposed")

# 6. energy scale: kernel energy_* (if any) and UPower's conversion voltage
e_now, e_full = g(s0, "bat.energy_now"), g(s0, "bat.energy_full")
c_now, c_full = g(s0, "bat.charge_now"), g(s0, "bat.charge_full")
if e_full and c_full:
    vk = e_full / c_full
    row("kernel energy_full / charge_full", "PASS" if 3.6 <= vk <= 4.0 else "FAIL",
        "%.3f V (a nominal voltage is 3.6..4.0 V)" % vk)
else:
    row("kernel energy_* properties", "INFO", "not exposed: UPower converts charge to energy itself")
up_ef = num((s0.get("up.energy-full") or "").split(" ")[0])
up_efd = num((s0.get("up.energy-full-design") or "").split(" ")[0])
vmax = g(s0, "bat.voltage_max_design")
if up_ef and c_full:
    vu = up_ef / (c_full / 1e6)
    est = c_full / 1e6 * 3.89
    vd = "PASS" if 3.6 <= vu <= 4.0 else ("CHECK" if vu <= 4.2 else "FAIL")
    row("UPower energy scale", vd,
        "energy-full %.2f Wh = charge_full x %.3f V%s; with a ~3.89 V nominal it would be ~%.1f Wh (%+.0f %%)" % (
            up_ef, vu, " (= voltage_max_design)" if vmax and abs(vu - vmax / 1e6) < 0.01 else "", est,
            100 * (up_ef / est - 1)))
    if up_efd:
        row("UPower energy-full-design", "INFO", "%.2f Wh (stock design 13380 mAh)" % up_efd)
else:
    row("UPower energy scale", "CHECK", "no UPower battery device or no charge_full")

# 7. status vs the sign of the current (and the charger)
bad, detail = 0, {}
for s in samples:
    stt, i, cap, on = s.get("bat.status"), g(s, "bat.current_now"), g(s, "bat.capacity"), g(s, "usb.online")
    if stt is None or i is None:
        continue
    ok = True
    if stt == "Discharging":
        ok = i < 0
    elif stt == "Charging":
        ok = i > 0 and on != 0
    elif stt == "Not charging":
        ok = i == 0 and on != 0
    elif stt == "Full":
        ok = (cap or 0) >= 99 and on != 0
    if on == 0 and stt != "Discharging":
        ok = False
    if not ok:
        bad += 1
        detail.setdefault(stt, (i, on))
stats = sorted(set(s.get("bat.status", "?") for s in samples))
row("status vs current sign", "PASS" if bad <= 2 else ("CHECK" if bad <= len(samples) // 10 + 2 else "FAIL"),
    "%d of %d samples off; statuses seen: %s%s" % (bad, len(samples), ", ".join(stats),
        ("; e.g. " + ", ".join("%s with I=%+.0f mA online=%s" % (k, v[0] / 1e3, v[1]) for k, v in detail.items()))
        if detail else ""))

# 8. mode vs charger
if mode == "battery":
    row("charger unplugged (battery mode)", "PASS" if n_online == 0 else "CHECK",
        "USB online in %d of %d samples%s" % (n_online, len(samples),
            "" if n_online == 0 else " - unplug for the discharge checks, or use --charger"))
else:
    row("charger present (charger mode)", "PASS" if n_online >= 0.9 * len(samples) else "CHECK",
        "USB online in %d of %d samples" % (n_online, len(samples)))

# 9. temperature
temps = [g(s, "bat.temp") / 10 for s in samples if g(s, "bat.temp") is not None]
if temps:
    lo, hi = min(temps), max(temps)
    row("battery temperature", "PASS" if 10 <= lo and hi <= 45 else ("CHECK" if 0 <= lo and hi <= 50 else "FAIL"),
        "%.1f .. %.1f C (stock charges 0..53 C, powers off at 70 C)" % (lo, hi))

# 10. voltage limits
vs = [g(s, "bat.voltage_now") / 1e6 for s in samples if g(s, "bat.voltage_now")]
if vs:
    vmx = max(vs)
    row("battery voltage limits", "PASS" if 3.3 <= min(vs) and vmx <= 4.508 else ("CHECK" if vmx <= 4.6 else "FAIL"),
        "%.3f .. %.3f V (stock: power-off 3.30 V, float 4.50 V, stop above 4.508 V, over-voltage 4.60 V)" % (min(vs), vmx))

# integrals (trapezoid) over the run
def integ(fn):
    tot, used = 0.0, 0
    for a, b in zip(samples, samples[1:]):
        x, y = fn(a), fn(b)
        if x is None or y is None:
            continue
        tot += (x + y) / 2 * (b["t"] - a["t"])
        used += 1
    return tot, used

if len(samples) >= 3 and T >= 120:
    q, used = integ(lambda s: g(s, "bat.current_now"))            # uA*s
    q_mah = q / 3.6e6
    dq = None
    if g(s0, "bat.charge_now") is not None and g(s1, "bat.charge_now") is not None:
        dq = (g(s1, "bat.charge_now") - g(s0, "bat.charge_now")) / 1e3   # mAh
    # 11. coulomb count vs charge_now
    if dq is not None:
        big = max(abs(q_mah), abs(dq))
        if big < 15:
            row("coulomb count vs charge_now", "CHECK",
                "too little charge moved (integrated %+.1f mAh, charge_now %+.1f mAh): run longer" % (q_mah, dq))
        else:
            err = abs(dq - q_mah) / big
            same = (dq > 0) == (q_mah > 0)
            row("coulomb count vs charge_now", "PASS" if same and (err <= 0.15 or abs(dq - q_mah) <= 5) else
                ("CHECK" if same and err <= 0.35 else "FAIL"),
                "integrated current %+.1f mAh, charge_now changed %+.1f mAh (%.0f %% apart; charge_now has %.1f mAh steps)" % (
                    q_mah, dq, 100 * err, (g(s0, "bat.charge_full") or 0) / 1e3 / 10000))
    # 12. capacity drop vs coulomb count
    dcap = (g(s1, "bat.capacity") or 0) - (g(s0, "bat.capacity") or 0)
    full_mah = (g(s0, "bat.charge_full") or 0) / 1e3
    if full_mah:
        exp_pts = q_mah / full_mah * 100
        if abs(exp_pts) < 2 and abs(dcap) < 2:
            row("capacity change vs coulomb count", "INFO",
                "capacity %+d points, integrated current is %+.2f points (1 point = %.0f mAh): too short to judge" % (
                    dcap, exp_pts, full_mah / 100))
        else:
            row("capacity change vs coulomb count", "PASS" if abs(dcap - exp_pts) <= 1.5 else
                ("CHECK" if abs(dcap - exp_pts) <= 3 else "FAIL"),
                "capacity %+d points, integrated current %+.2f points" % (dcap, exp_pts))
    # 13. integrated power_now vs integrated V x I
    e_p, _ = integ(lambda s: g(s, "bat.power_now"))
    e_vi, _ = integ(lambda s: (g(s, "bat.voltage_now") * g(s, "bat.current_now") / 1e6)
                    if g(s, "bat.voltage_now") is not None and g(s, "bat.current_now") is not None else None)
    if e_vi:
        err = abs(e_p - e_vi) / max(abs(e_vi), 1.0)
        row("integrated power_now vs V x I", "PASS" if err <= 0.03 else ("CHECK" if err <= 0.10 else "FAIL"),
            "%+.3f Wh vs %+.3f Wh; mean battery power %+.2f W; effective voltage %.3f V" % (
                e_p / 3.6e9, e_vi / 3.6e9, e_vi / T / 1e6, (e_vi / q) if q else 0))
    # 14. UPower energy change vs integrated power
    ue0 = num((s0.get("up.energy") or "").split(" ")[0])
    ue1 = num((s1.get("up.energy") or "").split(" ")[0])
    if ue0 is not None and ue1 is not None and e_vi:
        due = ue1 - ue0
        row("UPower energy change vs V x I", "INFO",
            "UPower %+.3f Wh, integrated V x I %+.3f Wh (UPower moves with charge x its conversion voltage)" % (
                due, e_vi / 3.6e9))
else:
    row("coulomb count / integrals", "INFO", "skipped (snapshot run or under 2 minutes)")

# 15. UPower rate vs V x I
ratios, vimp = [], []
for s in samples:
    r = num((s.get("up.energy-rate") or "").split(" ")[0])
    v, i = g(s, "bat.voltage_now"), g(s, "bat.current_now")
    if r is None or v is None or i is None or i == 0:
        continue
    vi = abs(v * i) / 1e12
    if vi < 0.2:
        continue
    ratios.append(r / vi)
    vimp.append(r / (abs(i) / 1e6))
if ratios:
    m = st.median(ratios)
    vd = "PASS" if 0.92 <= m <= 1.08 else ("CHECK" if 0.8 <= m <= 1.25 else "FAIL")
    note = ""
    if vmax and abs(st.median(vimp) - vmax / 1e6) < 0.02 and vd == "PASS" and abs(m - 1) > 0.02:
        vd, note = "CHECK", "; UPower multiplies |I| by voltage_max_design, not by voltage_now"
    row("UPower rate vs |V x I|", vd,
        "median ratio %.3f over %d samples (%.2f .. %.2f); UPower's rate / |I| = %.3f V%s" % (
            m, len(ratios), min(ratios), max(ratios), st.median(vimp), note))
else:
    row("UPower rate vs |V x I|", "CHECK", "no usable sample (no UPower rate or |V x I| under 0.2 W)")

# 16. UPower state / percentage vs kernel
up_state = {"Discharging": "discharging", "Charging": "charging", "Full": "fully-charged", "Not charging": "pending-charge"}
agree = tot = pagree = 0
for s in samples:
    k, u = s.get("bat.status"), s.get("up.state")
    if k and u:
        tot += 1
        agree += up_state.get(k) == u
    pc, cap = num((s.get("up.percentage") or "").rstrip("%")), g(s, "bat.capacity")
    if pc is not None and cap is not None and abs(pc - cap) <= 1:
        pagree += 1
if tot:
    row("UPower state = kernel status", "PASS" if agree >= 0.8 * tot else "CHECK", "%d of %d samples" % (agree, tot))
    row("UPower percentage = capacity", "PASS" if pagree >= 0.9 * tot else "CHECK", "%d of %d samples" % (pagree, tot))

# 17. time estimates: UPower's vs charge_now / |I|
tdev = []
for s in samples:
    i, c, f = g(s, "bat.current_now"), g(s, "bat.charge_now"), g(s, "bat.charge_full")
    tte, ttf = dur(s.get("up.time to empty")), dur(s.get("up.time to full"))
    if i is None or c is None or i == 0:
        continue
    if tte and i < 0:
        tdev.append(tte / (c / abs(i) * 3600))
    elif ttf and i > 0 and f:
        tdev.append(ttf / ((f - c) / i * 3600))
if tdev:
    m = st.median(tdev)
    row("UPower time vs charge / |I|", "PASS" if 0.85 <= m <= 1.15 else ("CHECK" if 0.6 <= m <= 1.5 else "FAIL"),
        "median ratio %.2f over %d samples (UPower polls the rate every 30 s; ours is the same 1-min mean)" % (m, len(tdev)))
else:
    row("UPower time vs charge / |I|", "INFO", "UPower gave no time estimate in the samples")

# 18. charger mode: input, PD cap, charge limit
if mode == "charger" and n_online:
    pin, over_lim, vb = [], 0, []
    for s in samples:
        if g(s, "usb.online") != 1:
            continue
        uv, ua, lim = g(s, "usb.voltage_now"), g(s, "usb.current_now"), g(s, "usb.input_current_limit")
        if uv is not None:
            vb.append(uv / 1e6)
        if uv is not None and ua is not None:
            pin.append(uv * abs(ua) / 1e12)
        if ua is not None and lim and abs(ua) > lim * 1.10 + 50000:
            over_lim += 1
    if vb:
        row("VBUS", "PASS" if max(vb) <= 9.6 else "FAIL", "%.2f .. %.2f V (no 12 V; 9 V only with PD)" % (min(vb), max(vb)))
    if pin:
        row("input power", "PASS" if max(pin) <= 20.5 else ("CHECK" if max(pin) <= 22 else "FAIL"),
            "%.2f .. %.2f W (cap: 20 W with USB-PD)" % (min(pin), max(pin)))
    row("input current within its limit", "PASS" if over_lim == 0 else "CHECK",
        "%d samples above input_current_limit + 10 %%" % over_lim)
    end = g(s0, "bat.charge_control_end_threshold")
    start = g(s0, "bat.charge_control_start_threshold")
    if end is not None and end < 100:
        held_bad = sum(1 for s in samples if g(s, "usb.online") == 1 and (g(s, "bat.capacity") or 0) >= end
                       and s.get("bat.status") == "Charging")
        above = sum(1 for s in samples if (g(s, "bat.capacity") or 0) >= end)
        row("charge limit %d / %d %%" % (start or 0, end), "PASS" if held_bad <= 2 else "FAIL",
            "%d samples at or above the end threshold, %d of them still Charging (2 allowed: the 5 s poll)" % (
                above, held_bad))
    else:
        row("charge limit", "INFO", "no limit set (end threshold %s)" % s0.get("bat.charge_control_end_threshold", "?"))
    behav = s0.get("bat.charge_behaviour", "")
    if behav:
        row("charge_behaviour", "INFO", behav)

# static facts
row("cycle count / state of health", "INFO", "%s cycles, SOH %s %% (gauge words 5 and 8; stock reads its cycle count elsewhere)" % (
    s0.get("bat.cycle_count", "?"), s0.get("bat.state_of_health", "?")))

w1 = max(len(r[0]) for r in rows)
print("%-*s  %-6s %s" % (w1, "check", "result", "numbers"))
print("-" * (w1 + 60))
for n, v, d in rows:
    print("%-*s  %-6s %s" % (w1, n, v, d))
print()
nf = sum(1 for r in rows if r[1] == "FAIL")
nc = sum(1 for r in rows if r[1] == "CHECK")
npass = sum(1 for r in rows if r[1] == "PASS")
print("verdict: %d PASS, %d CHECK, %d FAIL" % (npass, nc, nf))
if nf:
    print("  FAIL: " + "; ".join(r[0] for r in rows if r[1] == "FAIL"))
if nc:
    print("  CHECK: " + "; ".join(r[0] for r in rows if r[1] == "CHECK"))
print("files: %s (samples.txt, supplies-*.txt, upower-*.txt, report.txt)" % out)
PY

echo "done: $OUT"

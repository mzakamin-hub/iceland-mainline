#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# als-modes.sh - OnePlus Pad 4 (iceland): which sensor-hub (SSC) stream causes the
# lower-quarter LCD flicker (any SSC stream: ALS or accel), plus the accel stream rate.
#
# Read-only on the system: no partition, registry, package or config change; no
# service is stopped. It only starts its own short ssccli clients (one at a time,
# each ends by itself via --timeout) and reads single debugfs files:
#   /sys/kernel/debug/regulator/regulator_summary
#   /sys/kernel/debug/interconnect/interconnect_summary
#   /sys/kernel/debug/dri/<n>/<encoder>/status   (DPU vsync / underrun counters, memory only)
#   /sys/kernel/debug/qcom_stats/adsp             (ADSP sleep stats from SMEM, if present)
#   /proc/interrupts (display / ADSP lines only)
# No regmap register files, no /dev/mem, no TLMM reads.
#
# Optional --bwpin (off by default): adds two modes that TEMPORARILY pin the DPU
# clock / bandwidth votes high through the DPU's own debugfs knobs
# (dri/<n>/debug/core_perf/perf_mode = 2 fixed) to test the DDR / bandwidth theory.
# The original values are restored on exit (trap), also on Ctrl-C.
#
# Usage (on the tablet, screen on, GNOME session, automatic brightness OFF,
# nothing else using sensors: close monitor-sensor; CONNECT THE KEYBOARD so mutter
# leaves tablet mode and releases its accelerometer claim - else 'idle' is not idle):
#   sudo bash als-modes.sh                # accel rate print + 7 modes, 15 s each
#   sudo bash als-modes.sh --bwpin        # + 2 modes with DPU votes pinned high
#   sudo bash als-modes.sh --secs 20      # longer modes
#   sudo bash als-modes.sh --no-accel     # skip the accel stream-rate print
#   sudo bash als-modes.sh --auto         # no prompts (answers recorded as '-')
# Output: /var/tmp/als-modes-<time>/ (summary.txt is the short result).

set -u
SECS=15; BWPIN=0; AUTO=0; ACCEL=1
while [ $# -gt 0 ]; do
	case "$1" in
		--secs) SECS="$2"; shift ;;
		--bwpin) BWPIN=1 ;;
		--auto) AUTO=1 ;;
		--no-accel) ACCEL=0 ;;
		*) echo "unknown option $1"; exit 2 ;;
	esac
	shift
done
[ "$(id -u)" = 0 ] || { echo "run with sudo (debugfs needs root)"; exit 2; }
SSCCLI=/usr/bin/ssccli
[ -x "$SSCCLI" ] || { echo "no $SSCCLI (package libssc)"; exit 2; }

OUT=/var/tmp/als-modes-$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUT" || exit 2
SUM=$OUT/summary.txt
DBG=/sys/kernel/debug
log() { echo "$*" | tee -a "$SUM"; }

# ---- restore on exit -------------------------------------------------------
CHILD=""          # pid of the one ssccli client (through timeout) we started
PERF=""           # core_perf dir, set only when --bwpin changed something
ORIG_MODE=""; ORIG_CLK=""; ORIG_IB=""; ORIG_AB=""
restore() {
	if [ -n "$CHILD" ] && kill -0 "$CHILD" 2>/dev/null; then
		kill "$CHILD" 2>/dev/null; wait "$CHILD" 2>/dev/null
	fi
	CHILD=""
	if [ -n "$PERF" ]; then
		echo "$ORIG_CLK" > "$PERF/fix_core_clk_rate" 2>/dev/null
		echo "$ORIG_IB" > "$PERF/fix_core_ib_vote" 2>/dev/null
		echo "$ORIG_AB" > "$PERF/fix_core_ab_vote" 2>/dev/null
		echo "$ORIG_MODE" > "$PERF/perf_mode" 2>/dev/null
		echo "restored DPU core_perf: $(cat "$PERF/perf_mode" 2>/dev/null), fix clk/ib/ab $(cat "$PERF/fix_core_clk_rate" "$PERF/fix_core_ib_vote" "$PERF/fix_core_ab_vote" 2>/dev/null | tr '\n' ' ')"
		PERF=""
	fi
}
trap 'restore' EXIT
trap 'echo; echo "interrupted - restoring"; exit 130' INT TERM HUP

ask() {   # ask "question" -> REPLY (y/n/u or '-')
	REPLY="-"
	[ "$AUTO" = 1 ] && return
	local a=""
	while :; do
		printf '%s [y/n/u] ' "$1" > /dev/tty
		read -r a < /dev/tty || { a=u; break; }
		case "$a" in y|n|u) break ;; esac
	done
	REPLY=$a
}
pause() { [ "$AUTO" = 1 ] && return; printf '%s (Enter) ' "$1" > /dev/tty; read -r _ < /dev/tty; }

# ---- snapshots ----------------------------------------------------------------
ENC=$(find $DBG/dri -mindepth 3 -maxdepth 3 -name status 2>/dev/null | grep -v '/debug/' | sort)
snap_counters() {   # $1 = file
	{
		for f in $ENC; do
			s=$(head -c 2000 "$f" 2>/dev/null)
			case "$s" in intf:*) echo "$f $s" ;; esac
		done
		[ -r $DBG/qcom_stats/adsp ] && sed 's/^/adsp: /' $DBG/qcom_stats/adsp
		grep -i -E 'dpu|mdss|dsi|msm_drm|adsp|glink|smp2p|qrtr' /proc/interrupts | awk '{s=0; for(i=2;i<=NF;i++){ if($i ~ /^[0-9]+$/) s+=$i; else break }; $1=$1; print "irq", $0 " SUM=" s}' | sed 's/  */ /g'
	} > "$1" 2>/dev/null
}
snap_votes() {      # $1 = prefix
	cat $DBG/regulator/regulator_summary > "$1.regulators" 2>/dev/null
	cat $DBG/interconnect/interconnect_summary > "$1.icc" 2>/dev/null
}
underruns() { grep -o 'underrun: *[0-9]*' "$1" | awk '{s+=$2} END{print s+0}'; }
vsyncs() { grep -o 'vsync: *[0-9]*' "$1" | awk '{s+=$2} END{print s+0}'; }
adspcount() { awk '/adsp: *Count/{print $NF; exit}' "$1"; }

# ---- preflight --------------------------------------------------------------------
log "als-modes $(date '+%F %T'), kernel $(uname -r), libssc $(rpm -q libssc 2>/dev/null), iio-sensor-proxy $(rpm -q iio-sensor-proxy 2>/dev/null)"
log "services: hexagonrpcd* $(systemctl is-active 'hexagonrpcd*' 2>/dev/null | tr '\n' ' ')/ iio-sensor-proxy $(systemctl is-active iio-sensor-proxy 2>/dev/null)"
for p in HasAccelerometer AccelerometerOrientation HasAmbientLight HasProximity; do
	log "  proxy $p = $(busctl --system get-property net.hadess.SensorProxy /net/hadess/SensorProxy net.hadess.SensorProxy $p 2>/dev/null)"
done
others=$(ps -C monitor-sensor,ssccli -o pid=,comm= 2>/dev/null)
[ -n "$others" ] && log "WARNING: other sensor clients are running (close them for a clean idle mode): $others"
ask "is the keyboard connected (mutter then releases the accelerometer)?"; log "keyboard connected: $REPLY"
log "DPU encoder status files: $(echo $ENC | tr '\n' ' ')"
log "screen brightness: $(cat /sys/class/backlight/*/actual_brightness 2>/dev/null | head -1)"

# ---- 1. sensor list (each sensor ~1 s; the flicker may show briefly) -----------------------
log ""
log "== sensor list (default sensor per type as libssc picks it; each streams ~1 s)"
for s in accelerometer light proximity magnetometer gyroscope compass; do
	G_MESSAGES_DEBUG=all timeout 12 $SSCCLI --sensor $s --timeout 1 > "$OUT/list-$s.txt" 2>&1
	info=$(grep -a -E "Discovered|  name:|  vendor:|  stream-type:|  sample-rate:|No '|Unable" "$OUT/list-$s.txt" | sed 's/^.*: \(Discovered\|  \)//' | tr -s ' ' | tr '\n' ';' | cut -c1-300)
	log "  $s: ${info:-no info} samples=$(grep -a -c measurement "$OUT/list-$s.txt")"
done
sleep 3

# ---- 2. accel stream rate (cheap check that the hub streams) ----------------------------
if [ "$ACCEL" = 1 ]; then
	log ""
	log "== accel stream rate: 10 s accelerometer through ssccli"
	timeout 25 $SSCCLI --sensor accelerometer --timeout 10 > "$OUT/accel-raw.txt" 2>&1 &
	CHILD=$!
	wait "$CHILD" 2>/dev/null; CHILD=""
	awk -v secs=10 '/Accelerometer sensor measurement/{
		for(i=1;i<=NF;i++){ split($i,kv,"="); if(kv[1]=="X")x=kv[2]+0; if(kv[1]=="Y")y=kv[2]+0; if(kv[1]=="Z")z=kv[2]+0 }
		if(n==0){x0=x;x1=x;y0=y;y1=y;z0=z;z1=z}
		if(x<x0)x0=x; if(x>x1)x1=x; if(y<y0)y0=y; if(y>y1)y1=y; if(z<z0)z0=z; if(z>z1)z1=z; n++ }
		END{ if(n==0){print "  samples=0 -> the hub did NOT stream the accelerometer"; exit}
		printf "  samples=%d (%.1f Hz)  X %.2f..%.2f  Y %.2f..%.2f  Z %.2f..%.2f m/s2\n", n, n/secs, x0,x1,y0,y1,z0,z1 }' "$OUT/accel-raw.txt" | tee -a "$SUM"
	grep -a -m3 -i -E 'unable|error|fail' "$OUT/accel-raw.txt" | sed 's/^/  ssccli: /' | tee -a "$SUM"
	sleep 3
fi

# ---- 3. flicker modes ----------------------------------------------------------------------
# mode table: name | ssccli sensor ('-' = none) | pin DPU votes (0/1)
MODES="idle|-|0 accelerometer|accelerometer|0 light|light|0 proximity|proximity|0 magnetometer|magnetometer|0 gyroscope|gyroscope|0 idle-again|-|0"
if [ "$BWPIN" = 1 ]; then
	PD=$(ls -d $DBG/dri/*/debug/core_perf 2>/dev/null | head -1)
	if [ -n "$PD" ] && [ -w "$PD/perf_mode" ]; then
		MODES="$MODES accelerometer+dpu-pinned|accelerometer|1 light+dpu-pinned|light|1"
	else
		log "--bwpin: no DPU core_perf debugfs, pinned modes skipped"
	fi
fi

pin_on() {
	PERF=$PD
	ORIG_MODE=$(grep -o '[0-9]*' "$PERF/perf_mode"); ORIG_CLK=$(cat "$PERF/fix_core_clk_rate")
	ORIG_IB=$(cat "$PERF/fix_core_ib_vote"); ORIG_AB=$(cat "$PERF/fix_core_ab_vote")
	cat "$PERF/max_core_clk_rate" > "$PERF/fix_core_clk_rate"
	cat "$PERF/max_core_ab" > "$PERF/fix_core_ib_vote"
	cat "$PERF/max_core_ab" > "$PERF/fix_core_ab_vote"
	echo 2 > "$PERF/perf_mode"
	log "  DPU pinned: clk $(cat $PERF/fix_core_clk_rate) ib/ab $(cat $PERF/fix_core_ib_vote) kBps (applies from the next frame commit: keep moving a window)"
}

log ""
log "== flicker modes, $SECS s each. Move a window over the lower quarter of the screen during each mode."
printf '%-26s %8s %8s %8s %8s  %s\n' mode samples vsync+ underrn+ adsp-wk flicker | tee -a "$SUM"
TABLE=""
n=0
for m in $MODES; do
	n=$((n+1))
	name=${m%%|*}; rest=${m#*|}; sensor=${rest%%|*}; pin=${rest#*|}
	p=$OUT/mode$n-$name
	sleep 2
	snap_counters "$p.before"
	[ "$pin" = 1 ] && pin_on
	echo; echo ">>> mode $n running now ($name) - watch the lower quarter for $SECS s"
	if [ "$sensor" != "-" ]; then
		timeout $((SECS + 15)) $SSCCLI --sensor "$sensor" --timeout "$SECS" > "$p.ssccli" 2>&1 &
		CHILD=$!
	fi
	sleep $(( SECS / 2 )); snap_votes "$p.during"
	if [ -n "$CHILD" ]; then wait "$CHILD" 2>/dev/null; CHILD=""; else sleep $(( SECS - SECS / 2 )); fi
	snap_counters "$p.after"
	[ "$pin" = 1 ] && restore
	samples="-"; [ "$sensor" != "-" ] && samples=$(grep -a -c measurement "$p.ssccli")
	du=$(( $(underruns "$p.after") - $(underruns "$p.before") ))
	dv=$(( $(vsyncs "$p.after") - $(vsyncs "$p.before") ))
	a0=$(adspcount "$p.before"); a1=$(adspcount "$p.after"); da="-"; [ -n "$a0" ] && [ -n "$a1" ] && da=$((a1 - a0))
	ask "mode $n ($name): flicker in the lower quarter?"
	printf '%-26s %8s %8s %8s %8s  %s\n' "$n $name" "$samples" "$dv" "$du" "$da" "$REPLY" | tee -a "$SUM"
	if [ "$sensor" != "-" ] && [ -f "$OUT/mode1-idle.during.regulators" ]; then
		{ echo "### mode $n $name vs idle: regulator_summary"; diff "$OUT/mode1-idle.during.regulators" "$p.during.regulators"
		  echo "### mode $n $name vs idle: interconnect_summary"; diff "$OUT/mode1-idle.during.icc" "$p.during.icc"
		  echo "### mode $n $name: irq before / after"; grep '^irq' "$p.before"; grep '^irq' "$p.after"; } > "$p.diff" 2>&1
	fi
done

log ""
log "== AP-side vote changes while streaming (note: rpmh votes of the ADSP itself are NOT visible here)"
for d in "$OUT"/mode*.diff; do
	[ -f "$d" ] || continue
	r=$(sed -n '/regulator_summary/,/interconnect_summary/p' "$d" | grep -c '^[<>]')
	i=$(sed -n '/interconnect_summary/,/irq before/p' "$d" | grep -c '^[<>]')
	log "  $(basename "$d" .diff): regulator lines changed $r, interconnect lines changed $i"
done
log "dmesg (last 3 min, display / remoteproc / sensors, test-harness lines excluded):"
dmesg --since '-3min' 2>/dev/null | grep -v iceland-combo | grep -i -E 'dpu|dsi|underrun|vblank|timeout|adsp|remoteproc|fastrpc|qrtr|icc|interconnect' | tail -n 15 | sed 's/^/  /' | tee -a "$SUM"
log ""
log "done: $OUT (summary.txt is the short result; the mode*.diff files show the vote diffs)"

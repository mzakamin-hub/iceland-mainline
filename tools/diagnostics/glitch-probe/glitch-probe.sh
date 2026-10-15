#!/bin/bash
# glitch-probe.sh - OnePlus Pad 4 (iceland): lower-quarter flicker / tearing that shows while a
# sensor streams through iio-sensor-proxy (auto brightness, auto-rotate, monitor-sensor).
#
# PROBE ONLY. Read-only on the system, plus runtime-only actions that are undone by a trap:
#   - a tracefs instance (instances/glitchprobe-<pid>) with display / commit / irq events;
#     removed on exit (the global trace buffer is not touched);
#   - its own short sensor clients (monitor-sensor, ssccli), a D-Bus call loop and a GTK motion window
#     (glitch-storm.sh), each ended by timeout and by the trap;
#   - an idle inhibitor (gnome-session-inhibit) so the screen does not blank by itself in phase A;
#   - phase B: one screen blank / unblank through mutter's DisplayConfig PowerSaveMode
#     (3 = off for 6 s, then 0 = on); if refused: loginctl lock-session, the same again, unlock;
#   - optional A/B switches, each only for its own stage and restored right after it:
#       --ab-irq       pin the MDSS interrupt (its GIC parent) to the biggest CPU
#                      (/proc/irq/N/smp_affinity_list, old value written back)
#       --ab-qos       hold /dev/cpu_dma_latency = 0 (fd closed afterwards = released)
#       --ab-hwcursor  mutter DebugControl InhibitHwCursor = true (old value written back),
#                      only when mutter exposes that property.
# It never reads register files: no regmap 'registers', no dri/*/kms (disp snapshot), no
# debug/sspp regsets, no danger/safe status, no crc/ files, no /dev/mem, no TLMM.
# The debugfs files it reads are memory-only: dri/<n>/state, framebuffer, crtc-*/status,
# crtc-*/state, encoder-*/status, debug/core_irq, debug/core_perf/*, debug/vbif/*,
# interconnect/interconnect_summary, pm_genpd/pm_genpd_summary, qcom_stats/adsp.
# dri/<n>/state and crtc-*/status take the modeset locks for a moment, so they are read only
# between stages, never during an observation window.
#
# Usage (on the tablet, GNOME session, screen on; no input needed after the start):
#   sudo bash glitch-probe.sh --auto --ab-irq --ab-qos --ab-hwcursor
#   --auto: no prompts (answers recorded as u), also the default without a terminal. Each stage
#   (except base-static) runs glitch-motion.py, a maximized GTK window redrawing every frame,
#   started and stopped by PID. The verdict comes from objective metrics (analysis.txt).
#   options: --phase A|B|AB --secs N (15) --blank dbus|none (dbus: mutter PowerSaveMode; if
#            refused: loginctl lock-session, PowerSaveMode again, unlock-session; never the
#            power key, never suspend) --extra --ab-in-a --storm-hz N --no-trace --no-motion --out DIR
# Best run right after a fresh boot + login, before the screen has blanked once.
# Output: /var/tmp/glitch-probe-<time>/ ; summary.txt + analysis.txt are the short result.

set -u
umask 022
VERSION=2
SECS=15; PHASES=AB; BLANK=dbus; EXTRA=0; AB_IRQ=0; AB_QOS=0; AB_HWC=0; AB_IN_A=0
STORM_HZ=20; TRACE=1; AUTO=0; OUT=""; MOTION=1
while [ $# -gt 0 ]; do
	case "$1" in
		--secs) SECS="$2"; shift ;;
		--phase) PHASES="$2"; shift ;;
		--blank) BLANK="$2"; shift ;;
		--extra) EXTRA=1 ;;
		--ab-irq) AB_IRQ=1 ;;
		--ab-qos) AB_QOS=1 ;;
		--ab-hwcursor) AB_HWC=1 ;;
		--ab-in-a) AB_IN_A=1 ;;
		--storm-hz) STORM_HZ="$2"; shift ;;
		--no-trace) TRACE=0 ;;
		--auto) AUTO=1 ;;
		--no-motion) MOTION=0 ;;
		--out) OUT="$2"; shift ;;
		-h|--help) sed -n '2,40p' "$0"; exit 0 ;;
		*) echo "unknown option $1 (see --help)"; exit 2 ;;
	esac
	shift
done
case "$PHASES" in A|B|AB) ;; *) echo "--phase A|B|AB"; exit 2 ;; esac
case "$BLANK" in dbus|none) ;; *) echo "--blank dbus|none"; exit 2 ;; esac
# no terminal to answer on -> automatic (no prompts, answers recorded as u)
{ [ -t 0 ] && [ -r /dev/tty ]; } || AUTO=1
case "$SECS" in ''|*[!0-9]*) echo "--secs N"; exit 2 ;; esac
case "$STORM_HZ" in ''|*[!0-9]*) echo "--storm-hz N"; exit 2 ;; esac

# ---- roots (GP_ROOT is only for the PC fixture test; empty on the tablet) -------------------
R=${GP_ROOT:-}
SYS=$R/sys; PROC=$R/proc; DEVD=$R/dev
DBG=$SYS/kernel/debug
TRC=$SYS/kernel/tracing
[ -d "$TRC/instances" ] || TRC=$DBG/tracing
HERE=$(cd "$(dirname "$0")" && pwd)
if [ -z "$R" ] && [ "$(id -u)" != 0 ]; then echo "run with sudo (debugfs / tracefs need root)"; exit 2; fi
[ -n "$OUT" ] || OUT=$R/var/tmp/glitch-probe-$(date +%Y%m%d-%H%M%S)
mkdir -p "$OUT" || exit 2
SUM=$OUT/summary.txt
log() { echo "$*" | tee -a "$SUM"; }
say() { if [ "$AUTO" = 1 ]; then echo "$*"; else echo "$*" > /dev/tty; fi; }

# ---- session user / bus -----------------------------------------------------------------------
U=${SUDO_USER:-}
[ -n "$U" ] && [ "$U" != root ] || U=$(loginctl list-sessions --no-legend 2>/dev/null | awk '$3!="gdm" && $3!="root"{print $3; exit}')
UID_U=$(id -u "$U" 2>/dev/null || echo "")
UBUS="unix:path=$R/run/user/$UID_U/bus"
UPFX=()                # command prefix that runs a program as the session user
if [ -n "$U" ] && [ -n "$UID_U" ]; then
	if [ -n "$R" ]; then UPFX=(env DBUS_SESSION_BUS_ADDRESS="$UBUS")
	else
		WL=$(ls /run/user/"$UID_U"/ 2>/dev/null | grep -m1 -E '^wayland-[0-9]+$')
		UPFX=(runuser -u "$U" -- env DBUS_SESSION_BUS_ADDRESS="$UBUS" XDG_RUNTIME_DIR="/run/user/$UID_U" WAYLAND_DISPLAY="${WL:-wayland-0}")
	fi
fi
as_user() { [ ${#UPFX[@]} -gt 0 ] || return 127; "${UPFX[@]}" "$@"; }

# ---- state to restore -------------------------------------------------------------------------
CHILDREN=""          # pids of timeout-wrapped loads
INH_PID=""           # idle inhibitor
TI=""                # tracefs instance dir
IRQ_PINNED=""        # "irq|old_list"
QFD=""               # cpu_dma_latency fd
HWC_OLD=""           # "service|path|old"
PSM_SET=0            # PowerSaveMode was set to off by us
kill_children() {
	local p
	for p in $CHILDREN; do kill "$p" 2>/dev/null; done
	for p in $CHILDREN; do wait "$p" 2>/dev/null; done
	CHILDREN=""
}
irq_restore() {
	[ -n "$IRQ_PINNED" ] || return 0
	local irq=${IRQ_PINNED%%|*} old=${IRQ_PINNED#*|}
	echo "$old" > "$PROC/irq/$irq/smp_affinity_list" 2>/dev/null
	log "  restored irq $irq affinity to $(cat "$PROC/irq/$irq/smp_affinity_list" 2>/dev/null)"
	IRQ_PINNED=""
}
qos_release() {
	[ -n "$QFD" ] || return 0
	eval "exec $QFD>&-"
	QFD=""
	log "  released cpu_dma_latency"
}
hwc_restore() {
	[ -n "$HWC_OLD" ] || return 0
	local svc=${HWC_OLD%%|*} rest=${HWC_OLD#*|}
	local path=${rest%%|*} old=${rest#*|}
	as_user busctl --user set-property "$svc" "$path" org.gnome.Mutter.DebugControl InhibitHwCursor b "$old" 2>/dev/null
	log "  restored mutter InhibitHwCursor=$old"
	HWC_OLD=""
}
restore() {
	kill_children
	drmdbg_off
	irq_restore
	qos_release
	hwc_restore
	if [ "$PSM_SET" = 1 ]; then
		as_user busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
			org.gnome.Mutter.DisplayConfig PowerSaveMode i 0 2>/dev/null
		PSM_SET=0
	fi
	if [ -n "$INH_PID" ]; then kill "$INH_PID" 2>/dev/null; wait "$INH_PID" 2>/dev/null; INH_PID=""; fi
	if [ -n "$TI" ] && [ -d "$TI" ]; then
		echo 0 > "$TI/tracing_on" 2>/dev/null
		for f in "$TI"/events/*/*/enable; do [ -f "$f" ] && echo 0 > "$f" 2>/dev/null; done
		echo > "$TI/trace" 2>/dev/null
		rmdir "$TI" 2>/dev/null
		TI=""
	fi
}
trap 'restore' EXIT
trap 'echo; echo "interrupted - restoring"; exit 130' INT TERM HUP

ask() {   # ask "question" "choices" -> REPLY
	REPLY="-"
	[ "$AUTO" = 1 ] && { REPLY=u; return; }
	local a="" ch=${2:-ynu}
	while :; do
		printf '%s [%s] ' "$1" "$(echo "$ch" | sed 's/./&\//g; s/\/$//')" > /dev/tty
		read -r a < /dev/tty || { a=u; break; }
		case "$a" in ?) case "$ch" in *"$a"*) break ;; esac ;; esac
	done
	REPLY=$a
}
pause() { [ "$AUTO" = 1 ] && return; printf '%s (Enter) ' "$1" > /dev/tty; read -r _ < /dev/tty; }

# ---- discovery --------------------------------------------------------------------------------
DRI=""
for d in "$DBG"/dri/*; do
	[ -d "$d/debug/core_perf" ] && { DRI=$d; break; }
done
ENC_ST=""; CRTC_ST=""; CRTC_STATE=""
if [ -n "$DRI" ]; then
	for f in "$DRI"/*/status; do
		case "${f#"$DRI"/}" in debug/*) continue ;; esac
		case "$(basename "$(dirname "$f")")" in
			crtc-*) CRTC_ST="$CRTC_ST $f"; [ -f "$(dirname "$f")/state" ] && CRTC_STATE="$CRTC_STATE $(dirname "$f")/state" ;;
			*) ENC_ST="$ENC_ST $f" ;;
		esac
	done
fi
pids_of() {   # exact comm match
	local d c
	for d in "$PROC"/[0-9]*; do
		[ -r "$d/comm" ] || continue
		read -r c < "$d/comm" 2>/dev/null || continue
		[ "$c" = "$1" ] && echo "${d##*/}"
	done
}
WATCH_COMMS="gnome-shell gsd-power iio-sensor-prox hexagonrpcd dbus-broker dbus-broker-lau Xwayland monitor-sensor ssccli gsd-color tuned"
# the MDSS interrupt: the 'msm' handler and the GIC parent of the MDSS node (from the DT)
MSM_IRQ=$(awk -F: '/ msm$|[[:space:]]msm[[:space:]]*$/{gsub(/ /,"",$1); print $1; exit}' "$PROC/interrupts" 2>/dev/null)
MDSS_SPI=""
for n in "$PROC"/device-tree/soc@0/display-subsystem@* "$PROC"/device-tree/soc@0/mdss@* "$PROC"/device-tree/soc/display-subsystem@*; do
	[ -f "$n/interrupts" ] || continue
	MDSS_SPI=$(od -An -tu1 -v "$n/interrupts" 2>/dev/null | tr -s ' \n' ' ' | awk '{ if (NF>=8 && $1==0 && $2==0 && $3==0 && $4==0) print ($5*16777216+$6*65536+$7*256+$8)+32 }')
	break
done
MDSS_IRQ=""
if [ -n "$MDSS_SPI" ]; then
	for k in "$SYS"/kernel/irq/*; do
		[ -f "$k/hwirq" ] || continue
		if [ "$(cat "$k/hwirq" 2>/dev/null)" = "$MDSS_SPI" ] && grep -qi gic "$k/chip_name" 2>/dev/null; then MDSS_IRQ=${k##*/}; break; fi
	done
fi
IRQ_CPU=$(cat "$PROC/irq/${MDSS_IRQ:-${MSM_IRQ:-none}}/effective_affinity_list" 2>/dev/null | cut -d, -f1 | cut -d- -f1)
BIGCPU=$(for c in "$SYS"/devices/system/cpu/cpu[0-9]*; do [ -f "$c/cpu_capacity" ] && echo "$(cat "$c/cpu_capacity") ${c##*cpu}"; done | sort -n | tail -1 | awk '{print $2}')

# ---- snapshots -----------------------------------------------------------------------------------
snap_locked() {   # files that take modeset locks: only between stages. $1 = prefix
	local f
	{ [ -n "$DRI" ] && cat "$DRI/state"; } > "$1.drm-state" 2>/dev/null
	{ [ -n "$DRI" ] && cat "$DRI/framebuffer"; } > "$1.drm-fb" 2>/dev/null
	{ for f in $CRTC_ST $CRTC_STATE; do echo "### $f"; cat "$f"; done; } > "$1.crtc" 2>/dev/null
}
snap_counters() { # memory-only counters. $1 = file
	local f c s p d b t st vc ic pu tc
	{
		echo "### uptime $(cat "$PROC/uptime" 2>/dev/null)"
		for f in $ENC_ST; do echo "### $f"; cat "$f"; done
		if [ -n "$DRI" ]; then
			echo "### core_irq"; cat "$DRI/debug/core_irq"
			for f in "$DRI"/debug/core_perf/*; do [ -f "$f" ] && echo "core_perf/${f##*/}: $(cat "$f")"; done
			for f in "$DRI"/debug/vbif/*; do [ -f "$f" ] && echo "vbif/${f##*/}: $(cat "$f")"; done
		fi
		echo "### interrupts"
		awk -v a="${MDSS_IRQ:-x}:" -v b="${MSM_IRQ:-x}:" '$1==a || $1==b || tolower($0) ~ / msm$|mdss|dsi|dpu|kgsl|gpu|adreno|glink|smp2p|ipcc|qrtr|adsp|apr|fastrpc|ipi|arch_timer|ufs|pcie|wlan|nt36|novatek|touch|spi|geni|pogo/' "$PROC/interrupts" | \
			awk '{s=0; for(i=2;i<=NF;i++){ if($i ~ /^[0-9]+$/) s+=$i; else break }; $1=$1; print "irq", $0 " SUM=" s}'
		echo "### cpuidle"
		for c in "$SYS"/devices/system/cpu/cpu[0-9]*; do
			for s in "$c"/cpuidle/state*; do
				[ -f "$s/usage" ] && echo "cpuidle ${c##*/} ${s##*/} $(cat "$s/name") usage=$(cat "$s/usage") time=$(cat "$s/time") above=$(cat "$s/above" 2>/dev/null) below=$(cat "$s/below" 2>/dev/null)"
			done
		done
		echo "### cpu"; grep '^cpu' "$PROC/stat"
		echo "### freq"
		for p in "$SYS"/devices/system/cpu/cpufreq/policy*; do [ -f "$p/scaling_cur_freq" ] && echo "freq ${p##*/} cur=$(cat "$p/scaling_cur_freq") gov=$(cat "$p/scaling_governor" 2>/dev/null)"; done
		for d in "$SYS"/class/devfreq/*; do [ -f "$d/cur_freq" ] && echo "devfreq ${d##*/} cur=$(cat "$d/cur_freq") gov=$(cat "$d/governor" 2>/dev/null)"; done
		echo "### procs (pid comm utime stime vol_ctxsw invol_ctxsw)"
		for c in $WATCH_COMMS; do
			for p in $(pids_of "$c"); do
				st=$(sed 's/^.*) //' "$PROC/$p/stat" 2>/dev/null)
				vc=$(awk '/^voluntary_ctxt_switches/{print $2}' "$PROC/$p/status" 2>/dev/null)
				ic=$(awk '/^nonvoluntary_ctxt_switches/{print $2}' "$PROC/$p/status" 2>/dev/null)
				pu=$(awk '/^Uid:/{print $2}' "$PROC/$p/status" 2>/dev/null)
				echo "proc $p $c uid=$pu $(echo "$st" | awk '{print "utime=" $12 " stime=" $13}') vcs=$vc ics=$ic"
			done
		done
		echo "### gnome-shell threads (tid comm policy rtprio cpu schedstat=run_ns wait_ns slices)"
		for p in $(pids_of gnome-shell); do
			for t in "$PROC/$p"/task/*; do
				tc=$(cat "$t/comm" 2>/dev/null)
				st=$(sed 's/^.*) //' "$t/stat" 2>/dev/null)
				echo "thr $p ${t##*/} [$tc] $(echo "$st" | awk '{print "policy=" $39 " rtprio=" $38 " cpu=" $37}') schedstat=$(tr ' ' ',' < "$t/schedstat" 2>/dev/null)"
			done
		done
		echo "### runtime pm (display)"
		for d in "$SYS"/bus/platform/devices/*; do
			case "${d##*/}" in *dsi*|*mdss*|*display*|*disp*) ;; *) continue ;; esac
			[ -f "$d/power/runtime_status" ] && echo "rpm ${d##*/} $(cat "$d/power/runtime_status") active_ms=$(cat "$d/power/runtime_active_time" 2>/dev/null) suspended_ms=$(cat "$d/power/runtime_suspended_time" 2>/dev/null)"
		done
		echo "### misc"
		echo "suspend_success $(cat "$DBG/suspend_stats" 2>/dev/null | awk '/^success/{print $2}') $(cat "$SYS/power/suspend_stats/success" 2>/dev/null)"
		for b in "$SYS"/class/backlight/*; do [ -f "$b/actual_brightness" ] && echo "backlight ${b##*/} $(cat "$b/brightness") $(cat "$b/actual_brightness")"; done
		[ -r "$DBG/qcom_stats/adsp" ] && sed 's/^/adsp: /' "$DBG/qcom_stats/adsp"
		for t in "$SYS"/class/thermal/cooling_device*; do [ -f "$t/cur_state" ] && echo "cool ${t##*/} $(cat "$t/type") $(cat "$t/cur_state")"; done
		for c in "$SYS"/class/devcoredump/devcd*; do [ -e "$c" ] && echo "devcoredump ${c##*/} $(readlink -f "$c/failing_device" 2>/dev/null)"; done
	} > "$1" 2>/dev/null
}
snap_mid() {      # $1 = prefix
	cat "$DBG/interconnect/interconnect_summary" > "$1.icc" 2>/dev/null
	cat "$DBG/pm_genpd/pm_genpd_summary" > "$1.genpd" 2>/dev/null
}

# ---- tracefs instance ----------------------------------------------------------------------------
EVENTS="dpu/dpu_crtc_vblank_cb dpu/dpu_crtc_complete_flip dpu/dpu_crtc_complete_commit dpu/dpu_kms_commit
dpu/dpu_kms_wait_for_commit_done dpu/dpu_enc_kickoff dpu/dpu_enc_rc dpu/dpu_enc_frame_done_cb
dpu/dpu_enc_frame_done_cb_not_busy dpu/dpu_enc_frame_done_timeout dpu/dpu_crtc_frame_event_cb
dpu/dpu_crtc_frame_event_done dpu/dpu_crtc_frame_event_more_pending dpu/dpu_enc_underrun_cb
dpu/dpu_perf_crtc_update dpu/dpu_core_perf_update_clk dpu/dpu_cmd_release_bw dpu/dpu_crtc_enable
dpu/dpu_crtc_disable dpu/dpu_crtc_disable_frame_pending dpu/dpu_crtc_vblank_enable
dpu/dpu_enc_phys_vid_irq_enable dpu/dpu_enc_phys_vid_irq_disable dpu/dpu_enc_wait_event_timeout
dpu/dpu_core_irq_register_callback dpu/dpu_core_irq_unregister_callback dpu/dpu_hw_ctl_trigger_pending_flush
dpu/dpu_hw_ctl_update_pending_flush dpu/dpu_enc_enable dpu/dpu_enc_disable dpu/dpu_plane_disable
dpu/dpu_perf_set_qos_luts dpu/dpu_perf_set_danger_luts
drm_msm_atomic/msm_atomic_commit_tail_start drm_msm_atomic/msm_atomic_commit_tail_finish
drm_msm_atomic/msm_atomic_flush_commit drm_msm_atomic/msm_atomic_wait_flush_start
drm_msm_atomic/msm_atomic_wait_flush_finish drm_msm_atomic/msm_atomic_async_commit_start
drm/drm_vblank_event drm/drm_vblank_event_queued drm/drm_vblank_event_delivered
interconnect/icc_set_bw"
trace_setup() {
	[ "$TRACE" = 1 ] || return 0
	[ -d "$TRC/instances" ] || { log "tracefs instances not found - trace off"; TRACE=0; return 0; }
	TI=$TRC/instances/glitchprobe-$$
	mkdir "$TI" 2>/dev/null || { log "cannot create $TI - trace off"; TI=""; TRACE=0; return 0; }
	# PC fixture only: a fake tracefs has no event tree of its own
	[ -n "$R" ] && [ -d "$R/trace-template" ] && cp -r "$R/trace-template/." "$TI/"
	echo 0 > "$TI/tracing_on"
	echo 8192 > "$TI/buffer_size_kb" 2>/dev/null
	local e n=0 miss=""
	for e in $EVENTS; do
		if [ -f "$TI/events/$e/enable" ]; then echo 1 > "$TI/events/$e/enable" && n=$((n+1)); else miss="$miss ${e#*/}"; fi
	done
	# the MDSS interrupt entry / exit and the idle states of the CPU that takes it
	if [ -f "$TI/events/irq/irq_handler_entry/enable" ]; then
		local flt=""
		for i in $MDSS_IRQ $MSM_IRQ; do flt="${flt:+$flt || }irq == $i"; done
		if [ -n "$flt" ]; then
			echo "$flt" > "$TI/events/irq/irq_handler_entry/filter" 2>/dev/null
			echo 1 > "$TI/events/irq/irq_handler_entry/enable" && n=$((n+1))
		fi
	fi
	if [ -n "$IRQ_CPU" ] && [ -f "$TI/events/power/cpu_idle/enable" ]; then
		echo "cpu_id == $IRQ_CPU" > "$TI/events/power/cpu_idle/filter" 2>/dev/null
		echo 1 > "$TI/events/power/cpu_idle/enable" && n=$((n+1))
	fi
	log "trace instance ${TI#$R} with $n events${miss:+ (absent:$miss)}"
}
trace_start() { [ -n "$TI" ] || return 0; echo > "$TI/trace"; echo 1 > "$TI/tracing_on"; }
trace_stop() {  # $1 = file
	[ -n "$TI" ] || return 0
	echo 0 > "$TI/tracing_on"
	cat "$TI/trace" > "$1" 2>/dev/null
	if [ -n "$R" ]; then   # PC fixture only
		if [ -f "$R/trace-sample-$(basename "$1" .trace).txt" ]; then cat "$R/trace-sample-$(basename "$1" .trace).txt" > "$1"
		elif [ -f "$R/trace-sample.txt" ]; then cat "$R/trace-sample.txt" > "$1"; fi
	fi
	echo "# per-cpu overrun: $(cat "$TI"/per_cpu/cpu*/stats 2>/dev/null | awk '/^overrun/{s+=$2} END{print s+0}')" >> "$1"
}

# ---- loads ----------------------------------------------------------------------------------------
run_bg() { "$@" & CHILDREN="$CHILDREN $!"; }
run_bg_out() { local f=$1; shift; "$@" > "$f" 2>&1 & CHILDREN="$CHILDREN $!"; }
load_start() {    # $1 = kind, $2 = stage prefix
	case "$1" in
		base|base-static) ;;
		proxy-light|ab-*) run_bg_out "$2.client" timeout -k 3 "$SECS" "${UPFX[@]}" monitor-sensor --light ;;
		proxy-accel) run_bg_out "$2.client" timeout -k 3 "$SECS" "${UPFX[@]}" monitor-sensor --accel ;;
		proxy-light-tty) say "    (monitor-sensor output follows in this terminal for $SECS s)"
				 run_bg timeout -k 3 "$SECS" "${UPFX[@]}" monitor-sensor --light ;;
		storm) run_bg timeout -k 3 "$SECS" "${UPFX[@]}" bash "$HERE/glitch-storm.sh" "$STORM_HZ" "$SECS" "$2.client" ;;
		ssccli-light) run_bg_out "$2.client" timeout -k 3 $((SECS + 10)) ssccli --sensor light --timeout "$SECS" ;;
	esac
}

motion_start() {  # $1 = stage prefix; synthetic motion, killed by PID with the other loads
	[ "$MOTION" = 1 ] || return 0
	run_bg_out "$1.motion" timeout -k 3 $((SECS + 3)) "${UPFX[@]}" python3 -I "$HERE/glitch-motion.py" $((SECS + 2))
	sleep 2
}

# ---- A/B switches ---------------------------------------------------------------------------------
ab_on() {         # $1 = kind ; sets the switch for this stage only
	case "$1" in
		ab-irq)
			local irq=${MDSS_IRQ:-$MSM_IRQ}
			[ -n "$irq" ] && [ -n "$BIGCPU" ] && [ -w "$PROC/irq/$irq/smp_affinity_list" ] || { log "  ab-irq: no MDSS irq / big cpu - skipped"; return 1; }
			IRQ_PINNED="$irq|$(cat "$PROC/irq/$irq/smp_affinity_list")"
			if echo "$BIGCPU" > "$PROC/irq/$irq/smp_affinity_list" 2>/dev/null; then
				log "  ab-irq: irq $irq -> cpu $BIGCPU (effective $(cat "$PROC/irq/$irq/effective_affinity_list" 2>/dev/null))"
			else
				log "  ab-irq: the kernel refused the affinity of irq $irq - skipped"; IRQ_PINNED=""; return 1
			fi ;;
		ab-qos)
			[ -w "$DEVD/cpu_dma_latency" ] || { log "  ab-qos: no $DEVD/cpu_dma_latency - skipped"; return 1; }
			exec {QFD}> "$DEVD/cpu_dma_latency" || { QFD=""; return 1; }
			printf '\0\0\0\0' >&"$QFD"
			log "  ab-qos: cpu_dma_latency 0 held (shallowest idle only)" ;;
		ab-hwcursor)
			local svc path old
			for svc in org.gnome.Mutter.DebugControl org.gnome.Shell org.gnome.Mutter; do
				for path in /org/gnome/Mutter/DebugControl; do
					old=$(as_user busctl --user get-property "$svc" "$path" org.gnome.Mutter.DebugControl InhibitHwCursor 2>/dev/null | awk '{print $2}')
					[ -n "$old" ] && break 2
				done
			done
			[ -n "$old" ] || { log "  ab-hwcursor: mutter has no DebugControl.InhibitHwCursor - skipped"; return 1; }
			if as_user busctl --user set-property "$svc" "$path" org.gnome.Mutter.DebugControl InhibitHwCursor b true 2>/dev/null; then
				HWC_OLD="$svc|$path|$old"; log "  ab-hwcursor: InhibitHwCursor true (was $old)"
			else
				log "  ab-hwcursor: set refused - skipped"; return 1
			fi ;;
	esac
	return 0
}
ab_off() { irq_restore; qos_release; hwc_restore; }

# ---- one stage ------------------------------------------------------------------------------------
TABLE=$OUT/table.txt
printf '%-3s %-22s %7s %7s %6s %8s %8s %8s  %s\n' ph stage vsync+ underr+ fdtmo+ proxyCS+ shellCS+ mdssirq+ glitch > "$TABLE"
sumfield() { grep -o "$2: *[0-9]*" "$1" 2>/dev/null | awk '{s+=$NF} END{print s+0}'; }
proccs() {  # $1 file, $2 comm -> vcs+ics sum
	awk -v c="$2" '$1=="proc" && $3==c { for(i=4;i<=NF;i++){ split($i,kv,"="); if(kv[1]=="vcs"||kv[1]=="ics") s+=kv[2] } } END{print s+0}' "$1" 2>/dev/null
}
irqsum() { awk -v n="$2" '$1=="irq" && $2==n":" { for(i=NF;i>0;i--) if($i ~ /^SUM=/){ split($i,kv,"="); print kv[2]; exit } }' "$1" 2>/dev/null; }
stage() {   # $1 = phase, $2 = kind
	local ph=$1 kind=$2 n p ans=-
	NSTAGE=$((NSTAGE+1)); n=$NSTAGE
	p=$OUT/$ph-$(printf '%02d' "$n")-$kind
	sleep 2
	snap_locked "$p.pre"
	snap_counters "$p.before"
	case "$kind" in ab-*) ab_on "$kind" || { log "  stage $kind skipped"; return; } ;; esac
	say ""
	say ">>> phase $ph stage $n: $kind - $SECS s (synthetic motion: ${MOTION/#1/on}; hands off)"
	[ "$kind" = base-static ] || motion_start "$p"
	date '+%s' > "$p.t0"
	trace_start
	load_start "$kind" "$p"
	sleep $((SECS / 2)); snap_mid "$p.mid"
	sleep $((SECS - SECS / 2))
	kill_children
	trace_stop "$p.trace"
	case "$kind" in ab-*) ab_off ;; esac
	snap_counters "$p.after"
	journalctl --since "@$(cat "$p.t0")" -o short-monotonic --no-pager 2>/dev/null | grep -v iceland-combo | \
		grep -i -E 'dpu|dsi|drm|msm|vblank|underrun|timeout|cursor|kms|atomic|frame|flip|sensor|iio|ssc|light|hexagon|qrtr|fastrpc|mutter|gnome-shell' | tail -n 60 > "$p.journal"
	ask "phase $ph stage $n ($kind): glitch / flicker seen?"; ans=$REPLY
	echo "$ans" > "$p.answer"
	local dv du dt dpc dsc dirq a b
	dv=$(( $(sumfield "$p.after" vsync) - $(sumfield "$p.before" vsync) ))
	du=$(( $(sumfield "$p.after" underrun) - $(sumfield "$p.before" underrun) ))
	dt=$(( $(sumfield "$p.after" frame_done_cnt) - $(sumfield "$p.before" frame_done_cnt) ))
	dpc=$(( $(proccs "$p.after" iio-sensor-prox) - $(proccs "$p.before" iio-sensor-prox) ))
	dsc=$(( $(proccs "$p.after" gnome-shell) - $(proccs "$p.before" gnome-shell) ))
	a=$(irqsum "$p.before" "${MDSS_IRQ:-${MSM_IRQ:-x}}"); b=$(irqsum "$p.after" "${MDSS_IRQ:-${MSM_IRQ:-x}}")
	dirq=-; [ -n "$a" ] && [ -n "$b" ] && dirq=$((b - a))
	printf '%-3s %-22s %7s %7s %6s %8s %8s %8s  %s\n' "$ph" "$n-$kind" "$dv" "$du" "$dt" "$dpc" "$dsc" "$dirq" "$ans" | tee -a "$TABLE"
}
run_phase() {   # $1 = A|B
	local k
	for k in base-static base proxy-light storm ssccli-light; do stage "$1" "$k"; done
	if [ "$EXTRA" = 1 ]; then stage "$1" proxy-accel; stage "$1" proxy-light-tty; fi
	if [ "$1" = B ] || [ "$AB_IN_A" = 1 ]; then
		[ "$AB_IRQ" = 1 ] && stage "$1" ab-irq
		[ "$AB_QOS" = 1 ] && stage "$1" ab-qos
		[ "$AB_HWC" = 1 ] && stage "$1" ab-hwcursor
		if [ "$AB_IRQ$AB_QOS$AB_HWC" != 000 ]; then stage "$1" proxy-light; fi
	fi
}

# ---- drm debug window + devcoredumps --------------------------------------------------------------
# drm.debug is a runtime module parameter; it is set only for the blank window and the old value
# is written back (also by the trap). 0x16 = DRIVER | KMS | ATOMIC (no VBL: one line per vblank).
DRMDBG_F=$SYS/module/drm/parameters/debug
DRMDBG_OLD=""
DRMDBG_MASK=${GP_DRM_DEBUG:-0x16}
drmdbg_on() {
	[ "$DRMDBG_MASK" = 0 ] && return 0
	[ -w "$DRMDBG_F" ] || { log "drm.debug not writable - no debug lines"; return 0; }
	DRMDBG_OLD=$(cat "$DRMDBG_F")
	echo "$DRMDBG_MASK" > "$DRMDBG_F" && log "drm.debug $DRMDBG_OLD -> $DRMDBG_MASK for the blank window"
}
drmdbg_off() {
	[ -n "$DRMDBG_OLD" ] || return 0
	echo "$DRMDBG_OLD" > "$DRMDBG_F"
	log "drm.debug restored to $(cat "$DRMDBG_F")"
	DRMDBG_OLD=""
}
COPIED_CD=""
coredumps() {   # $1 = label. Copies display devcoredumps not copied yet. Read only: the data file
		# is never written, so the dump stays pending (a write would free it).
	local c dev name
	for c in "$SYS"/class/devcoredump/devcd*; do
		[ -r "$c/data" ] || continue
		name=${c##*/}
		case " $COPIED_CD " in *" $name "*) continue ;; esac
		dev=$(readlink -f "$c/failing_device" 2>/dev/null)
		case "$dev" in *display*|*mdss*|*dsi*) ;; *) log "devcoredump $name from ${dev##*/} (not display) - left alone"; COPIED_CD="$COPIED_CD $name"; continue ;; esac
		# the msm display snapshot holds register blocks and kernel log-like text only; the
		# mask below still blanks MAC-like and serial-like tokens in case a line carries one
		head -c 67108864 "$c/data" 2>/dev/null | \
			sed -E 's/([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}/xx:xx:xx:xx:xx:xx/g; s/(serial[^0-9a-zA-Z]*)[0-9a-zA-Z]+/\1MASKED/Ig' > "$OUT/$1-$name.devcoredump.txt"
		log "devcoredump $name from ${dev##*/} ($1): $(wc -c < "$OUT/$1-$name.devcoredump.txt") bytes -> $1-$name.devcoredump.txt; first lines: $(grep -a -m3 -i -E 'kms|module|time|underrun|timeout|reason' "$OUT/$1-$name.devcoredump.txt" | tr '\n' ' ' | cut -c1-200)"
		COPIED_CD="$COPIED_CD $name"
	done
}

# ---- blank / unblank between phase A and B -----------------------------------------------------
blank_cycle() {
	local p=$OUT/blank r0 r1 ok=0
	snap_counters "$p.before"
	trace_start
	date '+%s' > "$p.t0"
	drmdbg_on
	if [ "$BLANK" = dbus ]; then
		if as_user busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
				org.gnome.Mutter.DisplayConfig PowerSaveMode i 3 2>"$p.err"; then
			PSM_SET=1
			say ">>> screen OFF for 6 s through mutter (PowerSaveMode 3) - do not touch the tablet"
			sleep 6
			as_user busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
				org.gnome.Mutter.DisplayConfig PowerSaveMode i 0 2>>"$p.err" && PSM_SET=0
			sleep 4
			ok=1
			log "blank: mutter PowerSaveMode 3 -> 0 done"
		else
			log "blank: mutter refused PowerSaveMode ($(head -c 200 "$p.err")) - lock-session, then again"
			SID=$(loginctl show-user "$U" -p Display --value 2>/dev/null); loginctl lock-session $SID 2>>"$p.err"; sleep 3
			if as_user busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
					org.gnome.Mutter.DisplayConfig PowerSaveMode i 3 2>>"$p.err"; then
				PSM_SET=1; sleep 6
				as_user busctl --user set-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
					org.gnome.Mutter.DisplayConfig PowerSaveMode i 0 2>>"$p.err" && PSM_SET=0
				ok=1; log "blank: PowerSaveMode 3 -> 0 done while locked"
			else
				log "blank: refused again - no blank (phase B = current state)"
			fi
			loginctl unlock-session $SID 2>>"$p.err"; sleep 4
			log "blank: session unlocked again (loginctl unlock-session)"
		fi
	fi
	sleep 2
	drmdbg_off
	trace_stop "$p.trace"
	snap_counters "$p.after"
	# kernel lines of the blank window (drm debug lines included while the mask was set)
	if [ -n "$R" ]; then cat "$R/dmesg-sample.txt" > "$p.dmesg" 2>/dev/null
	else dmesg --since "@$(cat "$p.t0")" 2>/dev/null | grep -v iceland-combo > "$p.dmesg"; fi
	log "blank: kernel lines $(wc -l < "$p.dmesg") (blank.dmesg); dpu/dsi errors: $(grep -c -i -E 'underrun|frame done timeout|reset|timeout|error' "$p.dmesg")"
	coredumps blank
	r0=$(awk '$1=="suspend_success"{print $2 $3}' "$p.before"); r1=$(awk '$1=="suspend_success"{print $2 $3}' "$p.after")
	[ "$r0" != "$r1" ] && log "blank: a system suspend happened during the blank (suspend_stats changed) - phase B is 'after s2idle'"
	grep -c 'dpu_crtc_disable:' "$p.trace" 2>/dev/null | sed 's/^/blank: dpu_crtc_disable events: /' | tee -a "$SUM"
	grep -c 'dpu_crtc_enable:' "$p.trace" 2>/dev/null | sed 's/^/blank: dpu_crtc_enable events: /' | tee -a "$SUM"
	log "blank: underrun_cb $(grep -c 'dpu_enc_underrun_cb:' "$p.trace" 2>/dev/null) frame_done_timeout $(grep -c 'dpu_enc_frame_done_timeout:' "$p.trace" 2>/dev/null) irq-wait timeouts $(grep -c 'dpu_enc_wait_event_timeout:' "$p.trace" 2>/dev/null) perf/clk updates $(grep -c -E 'dpu_perf_crtc_update:|dpu_core_perf_update_clk:' "$p.trace" 2>/dev/null)"
	grep -E 'dpu_core_perf_update_clk:|dpu_perf_crtc_update:' "$p.trace" 2>/dev/null | tail -n 6 | sed 's/^ */  /' | tee -a "$SUM" > /dev/null
	[ "$ok" = 1 ] || log "blank: none (phase B then equals the current state)"
}

# ---- preflight ------------------------------------------------------------------------------------
NSTAGE=0
log "glitch-probe v$VERSION $(date '+%F %T'), kernel $(uname -r), uptime $(cut -d' ' -f1 "$PROC/uptime" 2>/dev/null) s"
log "packages: $(rpm -q mutter gnome-shell mesa-dri-drivers iio-sensor-proxy libssc iceland-device 2>/dev/null | tr '\n' ' ')"
log "session user: ${U:-?} uid ${UID_U:-?}; dri: ${DRI#$R}; encoders:$(echo "$ENC_ST" | sed "s#$R##g"); crtcs:$(echo "$CRTC_ST" | sed "s#$R##g")"
log "mdss irq: msm=${MSM_IRQ:-?} gic-parent=${MDSS_IRQ:-?} (spi+32=${MDSS_SPI:-?}) on cpu ${IRQ_CPU:-?}; biggest cpu ${BIGCPU:-?}"
log "cmdline: $(tr ' ' '\n' < "$PROC/cmdline" 2>/dev/null | grep -E '^(msm|cpuidle|rcu|rcutree|nohz|irqaffinity|isolcpus|drm)' | tr '\n' ' ')"
for m in dpu_idle_refresh_ms dpu_idle_refresh_hz enable_preemption; do
	[ -f "$SYS/module/msm/parameters/$m" ] && log "  msm.$m = $(cat "$SYS/module/msm/parameters/$m")"
done
log "drm vblank offdelay: $(cat "$SYS/module/drm/parameters/vblankoffdelay" 2>/dev/null)"
log "services: iio-sensor-proxy $(systemctl is-active iio-sensor-proxy 2>/dev/null) hexagonrpcd $(systemctl is-active 'hexagonrpcd*' 2>/dev/null | tr '\n' ' ') tuned $(tuned-adm active 2>/dev/null | sed 's/.*: //') launchboost $(systemctl is-active iceland-launchboost 2>/dev/null) refresh $(systemctl is-active iceland-refresh 2>/dev/null)"
log "gsettings: ambient-enabled=$(as_user gsettings get org.gnome.settings-daemon.plugins.power ambient-enabled 2>/dev/null) orientation-lock=$(as_user gsettings get org.gnome.settings-daemon.peripherals.touchscreen orientation-lock 2>/dev/null) experimental=$(as_user gsettings get org.gnome.mutter experimental-features 2>/dev/null)"
for p in $(pids_of gnome-shell); do
	log "  gnome-shell $p uid $(awk '/^Uid:/{print $2}' "$PROC/$p/status") env: $(tr '\0' '\n' < "$PROC/$p/environ" 2>/dev/null | grep -E '^(MUTTER|CLUTTER|COGL|MESA|FD_|GSK|__GL|XDG_SESSION_TYPE)' | tr '\n' ' ')"
done
for p in $(pids_of gsd-power); do log "  gsd-power $p uid $(awk '/^Uid:/{print $2}' "$PROC/$p/status") (uid of gdm = greeter copy)"; done
log "sensor clients already running: $(for c in monitor-sensor ssccli; do pids_of $c; done | tr '\n' ' ')"
for pr in HasAmbientLight HasAccelerometer LightLevel AccelerometerOrientation; do
	log "  proxy $pr = $(busctl --system get-property net.hadess.SensorProxy /net/hadess/SensorProxy net.hadess.SensorProxy $pr 2>/dev/null)"
done
log "mutter DebugControl: $(as_user busctl --user introspect org.gnome.Mutter.DebugControl /org/gnome/Mutter/DebugControl 2>/dev/null | awk '/property/{printf "%s=%s ", $1, $4}' || true)"
journalctl -b -o short-monotonic --no-pager 2>/dev/null | grep -v iceland-combo | \
	grep -i -E 'vblank timeout|commit done|frame done|underrun|dpu error|dsi.*(err|timeout)|Cursor update failed|drmModeAtomicCommit|light sensor|AccessDenied' | tail -n 40 > "$OUT/journal-boot.txt"
log "boot journal display lines: $(wc -l < "$OUT/journal-boot.txt") (journal-boot.txt)"
coredumps preflight
ask "how do you hold the tablet now (l = landscape, long edge horizontal; p = portrait)?" lpu; ORIENT=$REPLY
log "orientation: $ORIENT"
ask "is a Bluetooth / pogo keyboard connected (GNOME tablet mode off)?"; log "keyboard: $REPLY"
ask "has the screen blanked (or the tablet slept) since this boot?"; log "blank since boot: $REPLY"
log "mode: $([ "$AUTO" = 1 ] && echo automatic || echo interactive); synthetic motion: $MOTION ($(python3 -I -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk' 2>/dev/null && echo 'GTK 4 via python3-gobject' || echo 'GTK 4 via python3-gobject MISSING - motion falls back to GTK 3 or none'))"
if [ -n "$(for c in monitor-sensor ssccli; do pids_of $c; done)" ]; then
	log "WARNING: close the running monitor-sensor / ssccli first for a clean baseline"
fi
say ""
say "Automatic brightness should be OFF for this probe (Settings > Displays). The probe starts"
say "its own sensor clients. In every stage, drag a window around for the whole time."
pause "Ready?"

# keep the screen from blanking by itself (phase A must stay 'fresh')
if command -v gnome-session-inhibit > /dev/null 2>&1 || [ -n "$R" ]; then
	if [ ${#UPFX[@]} -gt 0 ]; then
		"${UPFX[@]}" gnome-session-inhibit --inhibit idle --reason glitch-probe sleep 100000 > /dev/null 2>&1 &
		INH_PID=$!
	fi
fi

trace_setup
snap_locked "$OUT/start"
snap_counters "$OUT/start.counters"

case "$PHASES" in *A*) log ""; log "== phase A (current state)"; run_phase A ;; esac
case "$PHASES" in *B*)
	log ""; log "== screen blank / unblank ($BLANK)"
	[ "$BLANK" != none ] && blank_cycle
	log ""; log "== phase B (after the blank)"; run_phase B ;;
esac

if [ -n "$TI" ]; then echo 0 > "$TI/tracing_on"; fi
snap_locked "$OUT/end"
coredumps end
log ""
cat "$TABLE" >> "$SUM"
if command -v python3 > /dev/null 2>&1 && [ -f "$HERE/glitch-analyze.py" ]; then
	python3 -I "$HERE/glitch-analyze.py" "$OUT" > "$OUT/analysis.txt" 2>&1
	log ""; log "== analysis (analysis.txt)"; sed -n '1,80p' "$OUT/analysis.txt" | tee -a "$SUM" > /dev/null
	sed -n '1,40p' "$OUT/analysis.txt"
fi
chown -R "${U:-root}" "$OUT" 2>/dev/null
log ""
log "done: ${OUT#$R} - summary.txt + analysis.txt are the short result (the folder has no serials or network names)"

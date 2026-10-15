#!/bin/bash
# issue-scan.sh - READ-ONLY issue scan of the installed Fedora 44 on the OnePlus Pad 4 ("iceland", SM8850).
#
# Usage:  sudo bash issue-scan.sh [--boots N] [--since TIME] [--save-devcoredump]
#         bash issue-scan.sh --fixture DIR          (PC test: classify recorded logs, no system access)
#
#   --boots N     boots to scan: the current one and N-1 before it (default 2, at most 20)
#   --since TIME  only journal entries since TIME (journalctl syntax, e.g. "2026-10-15 08:00", "-2h", "today")
#   --save-devcoredump  also keep a masked copy of each pending DISPLAY / GPU device core dump (msm) in
#                 raw/devcoredump-devcdN-DEVICE.txt for an upstream report: it only reads the dump (the kernel
#                 frees it 5 min after it was made or when its data file is written; this scan never writes it)
#   --fixture DIR classify DIR/journal-b0.txt (journalctl -o short-monotonic), DIR/journal-b1.txt ...,
#                 or DIR/dmesg-b0.txt (dmesg format), plus the optional DIR/err-b0.txt (priority err lines,
#                 always classified) and DIR/sys.tsv (scan-check lines: SEV<TAB>CATEGORY<TAB>MESSAGE)
#
# What it scans: the kernel log (oops / BUG / WARN / call traces deduplicated by their first frame, lockdep, hung
# tasks, RCU stalls, lockups, timeouts and -110 / -71 / -5, firmware loads, probe failures, display / GPU / audio /
# Wi-Fi / Bluetooth / USB-C / storage / thermal / remoteproc / clock / power-domain lines), suspend / resume (a
# section comparing the lines before and after the most recent "PM: suspend exit", device times per cycle),
# deferred and driverless devices, remoteprocs, failed system and user units, restart loops, core dumps, SELinux
# denials, journal errors per unit, the desktop / sound / sensor / network daemons, dnf errors, rpm -V of the
# project's packages, disk space, btrfs device errors, memory pressure, OOM kills, thermal zones, the battery and the
# kernel taint flags. Every finding is classed KNOWN (a row of known-issues.tsv), NEW or INFO.
#
# Output: /var/tmp/issue-scan-<time>/report.txt (masked, safe to paste) and raw/ (masked data files).
# Safety: reads only. No writes outside /var/tmp/issue-scan-*, no service restarts, no module loads, no sysfs /
# debugfs writes, no debugfs regmap / register / clk / regulator summary files, no /dev/mem, no TLMM, no storage
# writes. Every external command runs under a timeout; a missing tool skips its check.
# Masked: MAC / Bluetooth addresses, IP addresses, Wi-Fi network and connection names, user names, host name,
# serial numbers, e-mail addresses; NetworkManager connection files and keys are never read.

set -u
export LC_ALL=C
umask 077
VERSION="1.1 (16 Oct 2026)"
BOOTS=2
SINCE=""
FIXTURE=""
SAVEDC=""

usage() { sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'; }
need() { [ $# -ge 2 ] || { echo "issue-scan: $1 needs a value" >&2; exit 2; }; }
while [ $# -gt 0 ]; do
	case "$1" in
	--boots)     need "$@"; BOOTS=$2; shift 2 ;;
	--boots=*)   BOOTS=${1#*=}; shift ;;
	--since)     need "$@"; SINCE=$2; shift 2 ;;
	--since=*)   SINCE=${1#*=}; shift ;;
	--fixture)   need "$@"; FIXTURE=$2; shift 2 ;;
	--save-devcoredump) SAVEDC=1; shift ;;
	--fixture=*) FIXTURE=${1#*=}; shift ;;
	-h|--help)   usage; exit 0 ;;
	*) echo "issue-scan: unknown argument: $1 (see --help)" >&2; exit 2 ;;
	esac
done
case "$BOOTS" in ''|*[!0-9]*) echo "issue-scan: --boots needs a number" >&2; exit 2 ;; esac
[ "$BOOTS" -ge 1 ] && [ "$BOOTS" -le 20 ] || { echo "issue-scan: --boots must be 1..20" >&2; exit 2; }
if [ -n "$FIXTURE" ]; then
	[ -d "$FIXTURE" ] || { echo "issue-scan: fixture directory not found: $FIXTURE" >&2; exit 2; }
	FIXTURE=$(cd "$FIXTURE" && pwd)
elif [ "$(id -u)" != 0 ]; then
	echo "issue-scan: run it with sudo (the journal, debugfs and the audit log need root)" >&2; exit 1
fi

HERE=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
KNOWNSRC="$HERE/known-issues.tsv"

# ---------------------------------------------------------------- output directory (the only place written)
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="/var/tmp/issue-scan-$STAMP"
[ -n "$FIXTURE" ] && OUT="/var/tmp/issue-scan-fixture-$STAMP"
[ -e "$OUT" ] && OUT="$OUT-$$"
mkdir "$OUT" && mkdir "$OUT/raw" "$OUT/.work" || { echo "issue-scan: cannot create $OUT" >&2; exit 1; }
WORK="$OUT/.work"
RAW="$OUT/raw"
FIXED="$WORK/fixed"
: > "$FIXED"
cleanup() {
	rm -f "$FIXED"
	[ -n "${KEEPWORK:-}" ] || rm -rf "$WORK"
	if [ -n "${SUDO_UID:-}" ] && [ -n "${SUDO_GID:-}" ]; then chown -R "$SUDO_UID:$SUDO_GID" "$OUT" 2>/dev/null; fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

START=$SECONDS
DEADLINE=$((SECONDS + 170))
left() { echo $((DEADLINE - SECONDS)); }
note() { printf '[%3ds] %s\n' "$((SECONDS - START))" "$*" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }
: > "$WORK/notes"
addnote() { echo "$*" >> "$WORK/notes"; }
if have timeout; then
	TO() {
		local t=$1 rc; shift
		timeout -k 3 "$t" "$@"; rc=$?
		if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then echo "timeout after ${t} s: $*" >> "$WORK/notes"; fi
		return "$rc"
	}
else
	addnote "the 'timeout' tool is missing: commands run without a time limit"
	TO() { shift; "$@"; }
fi
for t in journalctl systemctl gawk; do have "$t" || addnote "tool missing: $t"; done
AWK=""
if have gawk; then AWK=gawk; elif awk --version 2>/dev/null | grep -q 'GNU Awk'; then AWK=awk; fi

# ---------------------------------------------------------------- awk programs
cat > "$WORK/mask.awk" <<'EOF_MASK'
# mask.awk: replaces private values; FF = file with fixed strings (one per line, longest first)
BEGIN { n = 0; if (FF != "") { while ((getline l < FF) > 0) if (length(l) >= 3) fx[++n] = l; close(FF) } }
# brep: replace matches of re whose neighbours are not in the class bad
function brep(s, re, repl, bad,    out, st, ln, b, a) {
	out = ""
	while (match(s, re)) {
		st = RSTART; ln = RLENGTH
		if (ln < 1) break
		b = (st > 1) ? substr(s, st - 1, 1) : ""
		a = substr(s, st + ln, 1)
		if ((b != "" && b ~ bad) || (a != "" && a ~ bad)) out = out substr(s, 1, st + ln - 1)
		else out = out substr(s, 1, st - 1) repl
		s = substr(s, st + ln)
	}
	return out s
}
function frep(s, f, repl,    out, p, b, a, L) {
	out = ""; L = length(f)
	while ((p = index(s, f)) > 0) {
		b = (p > 1) ? substr(s, p - 1, 1) : ""
		a = substr(s, p + L, 1)
		if ((b != "" && b ~ /[A-Za-z0-9_]/) || (a != "" && a ~ /[A-Za-z0-9_]/)) out = out substr(s, 1, p + L - 1)
		else out = out substr(s, 1, p - 1) repl
		s = substr(s, p + L)
	}
	return out s
}
{
	s = $0
	for (i = 1; i <= n; i++) if (index(s, fx[i])) s = frep(s, fx[i], "<masked>")
	if (s ~ /[Ss]erial|iSerial|serialno/)
		s = gensub(/(SerialNumber|Serial Number|serial_number|serial-number|serialno|iSerial|[Ss]erial)([=: ]+)[^ ,;)'"]+/, "\\1\\2<masked>", "g", s)
	if (s ~ /[0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f][:-]/)
		s = brep(s, "[0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f][:-][0-9A-Fa-f][0-9A-Fa-f]", "XX:XX:XX:XX:XX:XX", "[0-9A-Fa-f:-]")
	if (s ~ /[0-9]\.[0-9]+\.[0-9]+\.[0-9]/)
		s = brep(s, "[0-9][0-9]?[0-9]?[.][0-9][0-9]?[0-9]?[.][0-9][0-9]?[0-9]?[.][0-9][0-9]?[0-9]?", "x.x.x.x", "[A-Za-z0-9_.-]")
	if (s ~ /[0-9A-Fa-f]:[0-9A-Fa-f]|::/) {
		s = brep(s, "([0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?:){7}[0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?", "<ipv6>", "[A-Za-z0-9_:.]")
		s = brep(s, "[0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?(:[0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?)*::[0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?(:[0-9A-Fa-f][0-9A-Fa-f]?[0-9A-Fa-f]?[0-9A-Fa-f]?)*", "<ipv6>", "[A-Za-z0-9_:.]")
	}
	if (s ~ /@/) s = gensub(/[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.(com|net|org|io|dev|de|uk|fi|ee|edu|gov|me|info|co|eu|ch|fr|se|no|nl|app)([^A-Za-z0-9]|$)/, "<email>\\3", "g", s)
	if (s ~ /\/home\//) gsub(/\/home\/[^\/ :'",;)]+/, "/home/<user>", s)
	if (s ~ /[Ss][Ss][Ii][Dd]/) s = gensub(/([Ss][Ss][Ii][Dd][=: ]+)('[^']*'|"[^"]*"|[^ ,;]+)/, "\\1<masked>", "g", s)
	if (s ~ /onnection '/) s = gensub(/([Cc]onnection )'[^']*'/, "\\1'<masked>'", "g", s)
	if (s ~ /[Hh]ostname/) { gsub(/[Hh]ostname set to <[^>]*>/, "Hostname set to <masked>", s); s = gensub(/([Hh]ostname[=: ]+)'[^']*'/, "\\1'<masked>'", "g", s) }
	print s
}
EOF_MASK

cat > "$WORK/classify.awk" <<'EOF_CLASSIFY'
# classify.awk - groups, classes and reports the findings.
# Input files are given with assignments in between: mode=j|d|s win=NAME force=0|1 FILE ...
#   mode j: journalctl -o short-monotonic lines (kernel lines have the identifier "kernel")
#   mode d: dmesg lines "[time] message"
#   mode s: scan-check lines "SEV<TAB>CATEGORY<TAB>MESSAGE"
#   force=1: a file of priority err..emerg lines; such lines are classified even without an error word
# Variables: KNOWNF (the cleaned known-issues table), OUTD (output directory), W0 (the current window name)
function addk(re, name, sev) { nkd++; kdre[nkd] = re; kdn[nkd] = name; kds[nkd] = sev }
function addc(re, name) { nct++; ctre[nct] = re; ctn[nct] = name }
function norm(s) {
	if (s ~ /avc: +denied/) gsub(/ (pid|tid|ino|name|dev|path|ses|auid|uid|gid|cmdline|exe)=("[^"]*"|[^ ]+)/, "", s)
	gsub(/0x[0-9a-fA-F]+/, "0xN", s)
	gsub(/[0-9a-fA-F]{8,}/, "H", s)
	gsub(/[0-9]+/, "N", s)
	gsub(/[ \t]+/, " ", s)
	return substr(s, 1, 220)
}
function kfind(src, full,    i) {
	for (i = 1; i <= nk; i++) {
		if (ksc[i] != "a" && ksc[i] != src) continue
		if (full ~ kre[i]) return i
	}
	return 0
}
function record(win, seq, ts, src, ident, msg, sev, cat,    full, key, lf, i) {
	full = (src == "j") ? ident ": " msg : msg
	key = src "|" norm(full)
	if (!(key in gc)) {
		gc[key] = 0; gex[key] = substr(full, 1, 300); gsrc[key] = src; gident[key] = ident
		gfw[key] = win; gts[key] = ts
		i = kfind(src, full)
		if (i) { gcl[key] = kcl[i]; gid[key] = kid[i]; grow[key] = krow[i]; gst[key] = kst[i]; gnote[key] = knote[i]; kseen[i] += 0 }
		else { gcl[key] = "NEW"; gid[key] = "-"; grow[key] = ""; gst[key] = ""; gnote[key] = "" }
		gki[key] = i
		lf = tolower(full)
		if (src == "s") { gsev[key] = sev; gcat[key] = cat; gkind[key] = "check" }
		else {
			for (i = 1; i <= nkd; i++) if (lf ~ kdre[i]) { gsev[key] = kds[i]; gkind[key] = kdn[i]; break }
			for (i = 1; i <= nct; i++) if (lf ~ ctre[i]) { gcat[key] = ctn[i]; break }
		}
	}
	gc[key]++; gw[key, win]++
	if (gki[key]) kseen[gki[key]]++
	nfind[win]++
	if (win == W0 && src != "s") { nl0++; l0s[nl0] = seq; l0k[nl0] = key }
}
function flush_trace() {
	if (!tp) return
	record(twin, tseq, tts, "k", "kernel", "TRACE " substr(thdr, 1, 160) " | first frame: " (tframe == "" ? "?" : tframe), "", "")
	tp = 0
}
function framesym(m,    s, mod) {
	s = m; sub(/^ +/, "", s); sub(/^\[<[0-9a-f]+>\] /, "", s)
	mod = ""
	if (match(s, /\[[A-Za-z0-9_]+\]/)) mod = " " substr(s, RSTART, RLENGTH)
	sub(/\+0x.*$/, "", s)
	return s mod
}
function wlist(key,    i, s) {
	s = ""
	for (i = 1; i <= nwin; i++) if ((key, wins[i]) in gw) s = s (s == "" ? "" : " ") wins[i] ":" gw[key, wins[i]]
	return s
}
function crank(key) { return gcl[key] == "NEW" ? 0 : (gcl[key] == "KNOWN" ? (gst[key] ~ /regression/ ? 1 : 2) : 3) }
function srank(key) { return gsev[key] == "CRIT" ? 0 : (gsev[key] == "HIGH" ? 1 : (gsev[key] == "MED" ? 2 : 3)) }
function line(key, w,    c, s) {
	c = gcl[key]; if (c == "KNOWN" && gst[key] ~ /regression/) c = "KNOWN!"
	s = sprintf("  %-6s %-4s %6d  %-14s %-13s %-15s %s", c, gsev[key], gc[key], substr(wlist(key), 1, 14), gcat[key], gid[key], substr(gex[key], 1, w))
	return s
}
function sorted(arr,    k, n) {   # fills SK[1..n] with group keys of arr[] in report order
	delete ORD; delete SK
	for (k in arr) ORD[sprintf("%d%d%09d %s", crank(k), srank(k), 999999999 - gc[k], k)] = k
	n = asorti(ORD, IDX)
	for (k = 1; k <= n; k++) SK[k] = ORD[IDX[k]]
	return n
}
BEGIN {
	FS = "\n"
	nk = 0
	while ((getline l < KNOWNF) > 0) {
		if (l ~ /^#/) continue
		n = split(l, f, "\t"); if (n < 4 || f[4] == "") continue
		nk++; kid[nk] = f[1]; kcl[nk] = f[2]; ksc[nk] = f[3]; kre[nk] = f[4]; krow[nk] = f[5]; kst[nk] = f[6]; knote[nk] = f[7]
	}
	close(KNOWNF)
	DETK = "error|fail|timed out|timeout|time out|unable|cannot|can't|could not|couldn't|invalid|not found|missing|refus|(^|[^a-z])bad([^a-z]|$)|warn|bug:|oops|panic|deferred probe|mismatch|overflow|underrun|unhandled|unknown|unexpected|denied|(^|[^a-z])faults?([^a-z]|$)|(^|[^a-z])stall|lockup|blocked for more than|(^|[^a-z])hung([^a-z]|$)|clsh|parity|(^|[^a-z])recover(ed|ing)?([^a-z]|$)|hangcheck|throttl|critical|crash|corrupt|abort|not responding|should not be|forcing sync_state|pending due to|overlap|dummy regulator|not ready|no such|unsupported|not supported|reject|emergency|out of memory|(^|[^a-z])oom([^a-z]|$)|oom-kill|killed process|\\(-[0-9]+\\)|returned -[0-9]|ret(urn)?[ :=]+-[0-9]|= -[0-9]|: -[0-9]+$|rc[ =:]+-[0-9]|status -[0-9]|err(or|no)?[ :=]+-[0-9]|-e(timedout|proto|io|inval|nodev|noent|busy|again|nomem|perm|acces|opnotsupp|nxio|probe_defer|nospc|rofs|connrefused|pipe)([^a-z]|$)"
	DETJ = DETK "|segfault|dumped core|core dump|assertion|traceback|exception|sigabrt|sigsegv|sigbus|killed"
	EXCL = "iceland-combo|^booting linux|kernel command line:|command line parameters: |adding to iommu group|cut here|skipped, unmet condition|condition check resulted|[]] +(info|debug) [a-z]+ [a-z_]+[.]cpp:"
	MODCONT = "^ *([a-z0-9_]+([(][A-Z]+[)])? )*[a-z0-9_]+([(][A-Z]+[)])?( [[]last unloaded: [^]]*[]])?$"
	SYSLIFE = "^(Starting|Started|Listening on|Stopping|Stopped|Reached target|Finished|Mounting|Mounted|Created slice|Removed slice|Closed|Condition check|Activating|Activated|Successfully activated) "
	PMRE = "PM: |Freezing |Restarting tasks|Filesystems sync|returned -?[0-9]+ after [0-9]+ usecs"
	HDR = "^(WARNING: |BUG: |Unable to handle kernel|Internal error: |Kernel panic|kernel BUG at|INFO: task .* blocked for more than|INFO: rcu|rcu: INFO: |watchdog: BUG: soft lockup|Watchdog detected hard LOCKUP|NMI backtrace for cpu|UBSAN: |list_(add|del) corruption|refcount_t: |general protection fault)"
	FRAMEL = "^ *(\\[<[0-9a-f]+>\\] )?[A-Za-z0-9_.$]+\\+0x[0-9a-f]+/0x[0-9a-f]+"
	REGL = "^ *(x[0-9]+ *: |pc : |lr : |sp : |pstate: |Modules linked in:|Hardware name:|CPU: [0-9]+ (UID|PID)|Tainted: |Workqueue: |Code: |---\\[ end trace|-+\\[ cut here|Call trace:|Mem abort info:|Data abort info:| +(ESR|EC|SET|FnV|EA|S1PTW|FSC|ISV|CM|WnR|Access size|SAS|SSE|SRT|SF|AR|TnD|TagAccess|GCS|Xs) = |user pgtable:|\\[[0-9a-f]+\\] (pgd|user address)|Sending NMI from CPU|<TASK>|</TASK>|=+$|-> #[0-9]|Chain exists of:| +Possible unsafe locking scenario|other info that might help|stack backtrace:| +lock\\(| +\\*\\*\\* DEADLOCK| +CPU[0-9]+ +CPU[0-9]+| +-+ +-+|[0-9]+ locks? held by| +#[0-9]+: )"
	GENF = "^(show_stack|dump_stack|dump_stack_lvl|__dump_stack|dump_backtrace|__warn|warn_slowpath[a-z_]*|report_bug|bug_handler|call_break_hook|brk_handler|bug_brk_handler|do_debug_exception|el1_dbg|el1_brk64|el1h_64_sync_handler|el1h_64_sync|el1_abort|do_mem_abort|die|panic|nmi_cpu_backtrace|nmi_trigger_cpumask_backtrace|arch_trigger_cpumask_backtrace|__die|die_kernel_fault|__do_kernel_fault|do_page_fault|do_translation_fault|lockdep_[a-z_]*|print_circular_bug|check_noncircular|__lock_acquire|lock_acquire|validate_chain|check_prev_add|_printk|vprintk[a-z_]*|printk|__ubsan[a-z_]*|ubsan_[a-z_]*|refcount_warn_saturate|__list_add_valid[a-z_]*|__list_del_entry_valid[a-z_]*|rcu_dump_cpu_stacks|print_cpu_stall|check_cpu_stall|rcu_sched_clock_irq|rcu_pending|update_process_times|tick_[a-z_]*|hrtimer_[a-z_]*|__hrtimer_[a-z_]*|handle_softirqs|__do_softirq|irq_exit[a-z_]*|el1_interrupt|el1h_64_irq[a-z_]*|gic_handle_irq|call_on_irq_stack|do_interrupt_handler|sched_show_task|show_regs|__show_regs|__schedule|schedule|schedule_timeout|schedule_preempt_disabled|wait_for_completion[a-z_]*|io_schedule)$"
	# kinds (first match on the lower-case line; TRACE lines start with "trace ")
	addk("^trace .*(unable to handle|internal error|oops|kernel bug|bug: |panic|general protection|corruption|ubsan|refcount_t)", "oops", "CRIT")
	addk("^trace .*(soft lockup|hard lockup)", "lockup", "CRIT")
	addk("^trace .*(rcu|stall)", "rcu-stall", "CRIT")
	addk("^trace .*blocked for more than", "hung-task", "CRIT")
	addk("^trace .*(locking|lock state|suspicious rcu|lock held|unlock balance)", "lockdep", "CRIT")
	addk("^trace .*nmi backtrace", "nmi-backtrace", "MED")
	addk("^trace .*warning", "warn-trace", "HIGH")
	addk("^trace ", "trace", "HIGH")
	addk("kernel panic|internal error|unable to handle kernel|kernel bug at|^bug: ", "oops", "CRIT")
	addk("soft lockup|hard lockup|blocked for more than|detected stalls|self-detected stall", "hang", "CRIT")
	addk("possible circular locking|recursive locking|inconsistent lock state|suspicious rcu usage", "lockdep", "CRIT")
	addk("out of memory|oom-kill|invoked oom-killer|oom_reaper|killed process [0-9]+|systemd-oomd.*kill", "oom", "HIGH")
	addk("i/o error|blk_update_request|medium error|buffer i/o|btrfs.*(error|corrupt|csum failed|errs:)|ext4-fs error|transaction aborted|forced readonly|remounting filesystem read-only", "storage-io", "HIGH")
	addk("(smmu|iommu).*([^a-z]faults?([^a-z]|$)|unhandled|unexpected)|context fault|translation fault", "iommu-fault", "HIGH")
	addk("code=dumped|dumped core|segfault|sigsegv|sigabrt|sigbus|core-dump|crashed|crash detected|fatal error|watchdog bite|wdog bite|(^|[^a-z])fatal([^a-z]|$)", "crash", "HIGH")
	addk("hangcheck|hang detected|gpu hang|recovering|recover(ed)? (gpu|from)|gpu fault|gmu.*([^a-z]fault|timeout|fail)|page fault", "gpu-fault", "HIGH")
	addk("underrun|vblank timeout|frame done|commit done|pp done|timeout pending", "display-timeout", "MED")
	addk("direct firmware load|request_firmware|failed to load firmware|firmware.*(fail|error|not found)", "firmware", "MED")
	addk("deferred probe pending|probe.*fail|failed to probe|probe of .* failed", "probe", "MED")
	addk("failed with result|failed to start|start request repeated too quickly|entered failed state", "unit-failed", "MED")
	addk("avc: +denied|user_avc", "selinux-denial", "MED")
	addk("timed out|timeout|time out|-110([^0-9]|$)|etimedout", "timeout", "MED")
	addk("-71([^0-9]|$)|eproto", "eproto", "MED")
	addk("(err(or)?|ret(urn(ed)?)?|failed|status|rc)[ :=(]*-5([^0-9]|$)|\\(-5\\)|: -5$|-eio([^a-z]|$)", "eio", "MED")
	addk("clsh|parity", "bus-error", "MED")
	addk("throttl|critical temperature|trip point|overheat|thermal shutdown|emergency|over-?temperature", "thermal", "MED")
	addk("assertion|traceback|exception", "assertion", "MED")
	addk("denied|permission", "denied", "LOW")
	addk("unknown|unhandled|unexpected|unsupported|not supported", "unknown", "LOW")
	addk("warn", "warning", "LOW")
	addk(".", "error", "LOW")
	# subsystems (first match)
	addc("camss|camera|csiphy|csid|libcamera|v4l2|videodev|subdev|sc1320|sc820|dw9|884000\\.i2c|snapshot", "camera")
	addc("iris|venus|video-codec", "video")
	addc("adreno|gmu|a8xx|a6xx|msm_gpu|gpu|hangcheck|recover_worker|fence|kgsl|freedreno|turnip|mesa|3d37000|gpucc|gxclkctl", "gpu")
	addc("dpu|drm|dsi|msm_dp|dp_|mdss|panel|crtc|enc[0-9]|encoder|kms|backlight|ktz8869|mutter|edid|display", "display")
	addc("soundwire|swr|wcd9|wsa|q6apm|qcom-apm|asoc|snd|alsa|lpass|audio|_macro|tfa98|pipewire|wireplumber|pulse|ucm", "audio")
	addc("ath12k|wlan|wlp|wifi|wi-fi|cfg80211|mac80211|wpa_supplicant|regulatory|setregdomain", "wifi")
	addc("bluetooth|hci[0-9]|hci_qca|btqca|bluetoothd|bluez", "bluetooth")
	addc("xhci|dwc3|ucsi|typec|type-c|pmic_glink|pmic-glink|altmode|eusb2|repeater|usbss|usb", "usb")
	addc("pcie|pci |pwrseq|pwrctrl", "pcie")
	addc("battmgr|power_supply|power-supply|charger|charging|battery|upower|fuel|pen_charger|mt5806", "power-supply")
	addc("dracut|initramfs|grub|loader/entries|bootloader|abl-boot|kernel-install", "boot")
	addc("ufs|scsi|(^|[^a-z])sd[a-z]|blk|block|i/o error|btrfs|ext4|xfs|nvme|mmc|loop[0-9]|bfq|disk", "storage")
	addc("thermal|cooling|throttl|tsens|lmh|temperature|therm", "thermal")
	addc("remoteproc|rproc|q6v5|adsp|cdsp|soccp|glink|qrtr|rpmsg|fastrpc|hexagonrpc|smp2p|pdr|servreg|pmic_logs", "remoteproc")
	addc("iio|sensor|ssc|accel|monitor-sensor", "sensors")
	addc("iommu|smmu", "iommu")
	addc("regulator|clk|clock|gdsc|genpd|power domain|pm_domain|interconnect|icc|sync_state|rpmh|qnoc|bcm-voter|devlink|supplier", "clk-power")
	addc("psci|cpuidle|cpufreq|scmi|cpucp|cpu[0-9]|(^|[^a-z])cpu([^a-z]|$)|gic|its@|irq", "cpu-irq")
	addc("firmware", "firmware")
	addc("pm: |suspend|resume|s2idle|freez|wakeup", "suspend")
	addc("selinux|avc:|audit", "selinux")
	addc("gnome-|gsd-|gdm|gtk|gjs|xwayland|xdg-desktop-portal|nautilus|tracker", "desktop")
	addc("networkmanager|nm-|dhcp|dns|firewalld|nftables|avahi|chronyd", "network")
	addc("dnf|rpm|packagekit|flatpak", "packages")
	addc("systemd|udev|logind|dbus|polkit|pam", "systemd")
	addc("memory|oom|psi", "memory")
	addc(".", "other")
	nwin = 0; nl0 = 0; npm = 0; tp = 0
}
FNR == 1 { if (!(win in seenw)) { seenw[win] = 1; wins[++nwin] = win }; prevmsg = "" }
force == 1 { forced[$0] = 1; nforced[win]++; next }
mode == "s" {
	n = split($0, f, "\t"); if (n < 3) next
	nscan[win]++
	record(win, FNR, "", "s", "scan", f[3], f[1], f[2]); next
}
{
	raw = $0; ts = ""; ident = "kernel"
	if (mode == "j") {
		if (raw ~ /^-- /) next
		if (match(raw, /^\[ *[0-9]+\.[0-9]+\] /)) { ts = substr(raw, 2, RLENGTH - 3); gsub(/ /, "", ts); rest = substr(raw, RLENGTH + 1) }
		else rest = raw
		p = index(rest, " "); if (p == 0) next
		rest = substr(rest, p + 1)
		p = index(rest, ": ")
		if (p == 0) { ident = "?"; msg = rest } else { ident = substr(rest, 1, p - 1); msg = substr(rest, p + 2) }
		sub(/\[[0-9]+\]$/, "", ident)
	} else {
		if (match(raw, /^\[[^]]*\] ?/)) { ts = substr(raw, 2, RLENGTH - 2); sub(/\] ?$/, "", ts); gsub(/^ +/, "", ts); msg = substr(raw, RLENGTH + 1) }
		else msg = raw
	}
	src = (ident == "kernel") ? "k" : "j"
	seq = ++wseq[win]; nlines[win]++
	if (src == "k") {
		if (win == W0) {
			if (msg ~ /PM: suspend entry/) { lastentry = seq; nentry++ }
			if (msg ~ /PM: suspend exit/) { lastexit = seq; lastexit_ts = ts; nexit++; if (!firstexit) firstexit = seq }
			if (msg ~ PMRE) { npm++; pmm[npm] = msg; pmt[npm] = ts }
		}
		# call traces: one record per trace, keyed by its header and its first non-generic frame
		if (msg ~ HDR) {
			if (tp && tframe == "" && seq - tseq < 40 && msg ~ /^(Internal error: |Kernel panic|general protection)/) { prevmsg = msg; next }
			flush_trace(); tp = 1; thdr = msg; tframe = ""; tct = 0; twin = win; tseq = seq; tts = ts; tlast = seq
			prevmsg = msg; next
		}
		if (msg ~ /^Modules linked in:/) lastmod = seq
		if (msg ~ /^Call trace:/) {
			if (!tp && tlast && seq - tlast < 80) next
			if (!tp) { tp = 1; thdr = "call trace after: " prevmsg; tframe = ""; twin = win; tseq = seq; tts = ts }
			tct = 1; next
		}
		if (tp) {
			if (seq - tseq > 80) flush_trace()
			else if (tframe == "" && msg ~ /^pc : /) { s = framesym(substr(msg, 6)); split(s, a, " "); if (a[1] !~ GENF) tframe = s }
			else if (tframe == "" && tct && msg ~ FRAMEL) { s = framesym(msg); split(s, a, " "); if (a[1] !~ GENF) tframe = s }
			if (tp && tframe != "") flush_trace()
		}
		if (msg ~ FRAMEL || msg ~ REGL) next
		if (lastmod && seq - lastmod < 8 && msg ~ MODCONT) next
		prevmsg = msg
	}
	lm = tolower(msg)
	if (!(raw in forced)) {
		if (src == "k" && lm !~ DETK) next
		if (src == "j" && lm !~ DETJ) next
	}
	if (lm ~ EXCL) next
	if (src == "j" && ident == "systemd" && msg ~ SYSLIFE && lm !~ /fail|error/) next
	record(win, seq, ts, src, ident, msg, "", "")
}
END {
	flush_trace()
	W = 112
	# ---- groups.tsv
	G = OUTD "/groups.tsv"
	print "class\tsev\tcount\twhere\tcategory\tkind\tid\tsource\tfirst_time\trow\tstatus\texample" > G
	n = sorted(gc)
	for (i = 1; i <= n; i++) ALL[i] = SK[i]
	for (i = 1; i <= n; i++) { k = ALL[i]
		print gcl[k] "\t" gsev[k] "\t" gc[k] "\t" wlist(k) "\t" gcat[k] "\t" gkind[k] "\t" gid[k] "\t" gsrc[k] "\t" gts[k] "\t" grow[k] "\t" gst[k] "\t" gex[k] > G }
	close(G)
	# ---- summary
	S = OUTD "/summary.txt"
	for (k in gc) { cg[gcl[k]]++; cl[gcl[k]] += gc[k]; if (gcl[k] == "NEW") cs[gsev[k]]++; if (gcl[k] == "KNOWN" && gst[k] ~ /regression/) nreg++ }
	print "Windows scanned (b0 = current boot, b-1 = the boot before, now = scan checks):" > S
	for (i = 1; i <= nwin; i++) printf "  %-5s %7d log lines, %6d finding lines%s\n", wins[i], nlines[wins[i]] + 0, nfind[wins[i]] + 0, (wins[i] == "now" ? " (scan checks)" : "") > S
	printf "\nNEW    %4d groups (CRIT %d, HIGH %d, MED %d, LOW %d), %d lines\n", cg["NEW"], cs["CRIT"], cs["HIGH"], cs["MED"], cs["LOW"], cl["NEW"] > S
	printf "KNOWN  %4d groups, %d lines; %d of them are rows marked regression-if-seen (class KNOWN!)\n", cg["KNOWN"], cl["KNOWN"], nreg > S
	printf "INFO   %4d groups, %d lines (look like errors, are not)\n\n", cg["INFO"], cl["INFO"] > S
	printf "  %-6s %-4s %6s  %-14s %-13s %-15s %s\n", "CLASS", "SEV", "COUNT", "WHERE", "CATEGORY", "ID", "FIRST EXAMPLE (masked)" > S
	shown = 0; sk = 0; sr = 0
	for (i = 1; i <= n; i++) { k = ALL[i]
		if (gcl[k] == "NEW") { if (shown < 45) { print line(k, W) > S; shown++ } else sk++ }
	}
	if (sk) print "  ... " sk " more NEW groups in raw/groups.tsv" > S
	for (i = 1; i <= n; i++) { k = ALL[i]; if (gcl[k] == "KNOWN" && gst[k] ~ /regression/) print line(k, W) > S }
	shown = 0
	delete KO; for (k in gc) if (gcl[k] == "KNOWN" && gst[k] !~ /regression/) KO[k] = 1
	m = sorted(KO)
	for (i = 1; i <= m && i <= 20; i++) print line(SK[i], W) > S
	if (m > 20) print "  ... " m - 20 " more KNOWN groups (section 8 and raw/groups.tsv)" > S
	close(S)
	# ---- kernel section
	K = OUTD "/sec-kernel.txt"
	print "2.1 Call traces (oops / BUG / WARN / lockdep / stalls; deduplicated by header and first frame)" > K
	nt = 0
	for (i = 1; i <= n; i++) { k = ALL[i]; if (gsrc[k] == "k" && gex[k] ~ /^TRACE /) { print line(k, 150) > K; nt++ } }
	if (!nt) print "  none" > K
	split("oops hang lockdep oom storage-io iommu-fault crash gpu-fault", hk, " ")
	print "\n2.2 Kernel lines by subsystem (NEW first; INFO groups counted only)" > K
	split("camera video gpu display audio wifi bluetooth usb pcie power-supply boot storage thermal remoteproc sensors iommu clk-power cpu-irq firmware suspend selinux memory other", co, " ")
	for (c = 1; c in co; c++) section(K, "k", co[c])
	close(K)
	J = OUTD "/sec-journal.txt"
	print "5.6 User-space journal findings by subsystem (NEW first; INFO groups counted only)" > J
	split("camera video gpu display audio wifi bluetooth usb pcie power-supply boot storage thermal remoteproc sensors iommu clk-power cpu-irq firmware suspend selinux desktop network packages systemd memory other", cj, " ")
	for (c = 1; c in cj; c++) section(J, "j", cj[c])
	print "\n5.7 Watched daemons (finding groups / lines in the scanned boots)" > J
	split("gnome-shell mutter gsd- gdm gnome-session pipewire wireplumber iio-sensor-proxy hexagonrpcd NetworkManager wpa_supplicant bluetoothd upowerd iceland- kernel", wd, " ")
	for (d = 1; d in wd; d++) {
		ng = 0; nn = 0; nkn = 0; nlin = 0
		for (k in gc) if (gsrc[k] == "j" && index(gident[k], wd[d]) == 1) { ng++; nlin += gc[k]; if (gcl[k] == "NEW") nn++; if (gcl[k] == "KNOWN") nkn++ }
		if (wd[d] != "kernel") printf "  %-18s %3d groups (NEW %d, KNOWN %d), %d lines\n", wd[d] (wd[d] ~ /-$/ ? "*" : ""), ng, nn, nkn, nlin > J
	}
	close(J)
	# ---- scan checks
	C = OUTD "/sec-checks.txt"
	nc = 0
	for (i = 1; i <= n; i++) { k = ALL[i]; if (gsrc[k] == "s") { print line(k, 140) > C; nc++; if (gcl[k] != "NEW" && gnote[k] != "") print "           -> " grow[k] ": " gnote[k] > C } }
	if (!nc) print "  none" > C
	close(C)
	# ---- known rows seen
	R = OUTD "/sec-known.txt"
	printf "  %-16s %-5s %6s  %-26s %s\n", "ID", "CLASS", "LINES", "STATUS", "ROW / NOTE" > R
	ns = 0
	for (i = 1; i <= nk; i++) if (kseen[i] > 0) { ns++; printf "  %-16s %-5s %6d  %-26s %s - %s\n", kid[i], kcl[i], kseen[i], substr(kst[i], 1, 26), krow[i], knote[i] > R }
	printf "  (%d of %d known-issue rows matched; the others were not seen)\n", ns, nk > R
	close(R)
	# ---- suspend / resume
	P = OUTD "/sec-suspend.txt"
	printf "Current boot: %d 'PM: suspend entry', %d 'PM: suspend exit' lines.\n", nentry, nexit > P
	pmcycles(P)
	if (!nexit) { print "No resume in the current boot: nothing to compare." > P; close(P); exit }
	if (lastentry > lastexit) print "NOTE: the last suspend entry has no exit after it (a failed or ongoing suspend)." > P
	for (i = 1; i <= nl0; i++) { k = l0k[i]; s = l0s[i]
		if (!(k in fseq)) fseq[k] = s
		if (s > lastexit) aft[k]++
		else if (lastentry && s >= lastentry && lastentry <= lastexit) dur[k]++
		else bef[k]++ }
	printf "\n3.2 Seen only AFTER the most recent resume (line %d, time %s) - resume-only problems:\n", lastexit, lastexit_ts > P
	delete X; for (k in aft) if (!(k in bef) && !(k in dur)) X[k] = 1
	m = sorted(X); for (i = 1; i <= m; i++) printf "%s  [after %d]\n", line(SK[i], W), aft[SK[i]] > P
	if (!m) print "  none" > P
	print "\n3.3 Logged during the most recent suspend / resume transition (entry .. exit):" > P
	delete X; for (k in dur) X[k] = 1
	m = sorted(X); for (i = 1; i <= m && i <= 40; i++) printf "%s  [during %d]\n", line(SK[i], W), dur[SK[i]] > P
	if (!m) print "  none" > P
	print "\n3.4 First seen after the first resume of this boot (not already in 3.2):" > P
	delete X; for (k in fseq) if (fseq[k] > firstexit && !((k in aft) && !(k in bef) && !(k in dur))) X[k] = 1
	m = sorted(X); for (i = 1; i <= m && i <= 40; i++) print line(SK[i], W) > P
	if (!m) print "  none" > P
	print "\n3.5 Seen before AND after the most recent resume (counts before / during / after):" > P
	delete X; for (k in aft) if (k in bef) X[k] = 1
	m = sorted(X); for (i = 1; i <= m && i <= 30; i++) printf "%s  [%d / %d / %d]\n", line(SK[i], 90), bef[SK[i]], dur[SK[i]] + 0, aft[SK[i]] > P
	if (!m) print "  none" > P
	close(P)
}
function section(F, src, cat,    k, i, m, nn, ni, nkk, nlin, ids) {
	delete X
	for (k in gc) if (gsrc[k] == src && gcat[k] == cat && gex[k] !~ /^TRACE /) X[k] = 1
	m = sorted(X); if (!m) return
	nn = 0; ni = 0; nkk = 0; nlin = 0; ids = ""
	for (i = 1; i <= m; i++) { k = SK[i]; nlin += gc[k]; if (gcl[k] == "NEW") nn++; else if (gcl[k] == "INFO") { ni++; if (index(ids, gid[k] " ") == 0) ids = ids gid[k] " " } else nkk++ }
	printf "\n-- %s: NEW %d, KNOWN %d, INFO %d groups; %d lines\n", cat, nn, nkk, ni, nlin > F
	shown = 0
	for (i = 1; i <= m; i++) { k = SK[i]
		if (gcl[k] == "NEW" && shown < 30) { print line(k, 112) > F; shown++ }
		else if (gcl[k] == "KNOWN" && shown < 42) { print line(k, 112) > F; shown++ } }
	if (m - ni > shown) print "  ... " m - ni - shown " more (raw/groups.tsv)" > F
	if (ni) print "  INFO: " ni " groups (" ids ")" > F
}
function pmnum(s, re,    t) { if (match(s, re)) { t = substr(s, RSTART, RLENGTH); gsub(/[^0-9.]/, "", t); return t } return "" }
function pmcycles(P,    i, c, m, t, dev, us, n, j, best, bk) {
	c = 0
	for (i = 1; i <= npm; i++) {
		m = pmm[i]
		if (m ~ /PM: suspend entry/) { c++; cyts[c] = pmt[i]; cyok[c] = "no exit" }
		if (!c) continue
		if (m ~ /PM: suspend exit/) cyok[c] = (cyok[c] == "no exit" ? "ok" : cyok[c])
		if (m ~ /Wakeup pending|aborting|Some devices failed|failed to suspend|returns -[0-9]/) { cyok[c] = "ABORT/FAIL"; cyfail[c] = substr(m, 1, 100) }
		if (m ~ /Freezing user space processes completed/) cyfz[c] = pmnum(m, "elapsed [0-9.]+")
		if (m ~ /PM: suspend of devices complete/) cysu[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /PM: late suspend of devices complete/) cyla[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /PM: noirq suspend of devices complete/) cyno[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /PM: noirq resume of devices complete/) cyrn[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /PM: early resume of devices complete/) cyre[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /PM: resume of devices complete/) cyrr[c] = pmnum(m, "after [0-9.]+")
		if (m ~ /returned -?[0-9]+ after [0-9]+ usecs/) {
			dev = m; sub(/^call +/, "", dev); sub(/ returned.*$/, "", dev)
			us = pmnum(m, "after [0-9]+ usecs"); sub(/\.$/, "", us)
			pd[c, dev] = us + 0; pdn[c] = 1 }
	}
	if (!c) return
	print "\n3.1 Suspend cycles of the current boot (times in ms; freeze in s; last 10 cycles):" > P
	printf "  %-5s %-12s %-8s %8s %8s %8s %8s %8s %8s %8s\n", "cycle", "entry time", "result", "freeze", "suspend", "late", "noirq", "r-noirq", "r-early", "resume" > P
	for (i = (c > 10 ? c - 9 : 1); i <= c; i++) {
		printf "  %-5d %-12s %-8s %8s %8s %8s %8s %8s %8s %8s\n", i, substr(cyts[i], 1, 12), substr(cyok[i], 1, 8), cyfz[i], cysu[i], cyla[i], cyno[i], cyrn[i], cyre[i], cyrr[i] > P
		if (cyfail[i] != "") print "        first failure line: " cyfail[i] > P
	}
	if (pdn[c]) {
		print "  slowest devices of the last cycle (pm_print_times lines, usecs):" > P
		for (j = 1; j <= 12; j++) { best = -1; bk = ""
			for (t in pd) { split(t, xx, SUBSEP); if (xx[1] != c || (t in used)) continue; if (pd[t] > best) { best = pd[t]; bk = t } }
			if (bk == "") break
			used[bk] = 1; split(bk, xx, SUBSEP); printf "    %10d  %s\n", best, substr(xx[2], 1, 90) > P }
	} else print "  per-device times: not logged (they need /sys/power/pm_print_times = 1 before the suspend; this scan does not set it)" > P
}
EOF_CLASSIFY

mask() {
	if [ -n "$AWK" ]; then "$AWK" -v FF="$FIXED" -f "$WORK/mask.awk"
	else
		sed -E 's/([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}/XX:XX:XX:XX:XX:XX/g; s/([0-9]{1,3}\.){3}[0-9]{1,3}/x.x.x.x/g; s#/home/[^/ ]+#/home/<user>#g' |
			{ if [ -s "$FIXED" ]; then grep -v -F -f "$FIXED"; else cat; fi; }
	fi
}
# sysf SEV CATEGORY MESSAGE: one scan-check finding (classified with the log lines)
sysf() { printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$WORK/sys.raw"; }
: > "$WORK/sys.raw"
sec() { SECF="$WORK/sec-$1.txt"; : > "$SECF"; }
say() { printf '%s\n' "$*" >> "$SECF"; }
sayf() { cat >> "$SECF"; }
rd() { local v; v=$(TO 5 cat "$1" 2>/dev/null | tr -d '\0' | head -c 200) || v=""; printf '%s' "$v"; }
# save_devcd DIR DEVICE DRIVER: --save-devcoredump. Reads DIR/data (reading never frees the dump; writing would) into
# raw/, masked, at most 64 MiB. Only msm display / GPU dumps (text: registers and the atomic state); other drivers'
# dumps (Wi-Fi, remoteproc) can hold firmware memory with private values and are not copied.
save_devcd() {
	local d=$1 name=$2 drv=$3 f
	case "$drv:$name" in
	msm_dpu:*|msm:*|adreno:*|*:*.display-controller|*:*.gpu) ;;
	*) say "    not saved: only display / GPU dumps are copied (a ${drv:-?} dump may hold firmware memory)"; return 0 ;;
	esac
	f="$RAW/devcoredump-${d##*/}-$name.txt"
	TO 60 cat "$d/data" 2>/dev/null | head -c 67108864 | tr -d '\0' | mask > "$f"
	if [ -s "$f" ]; then say "    saved (masked, read only - the dump stays until the kernel frees it): raw/${f##*/}, $(wc -c < "$f") bytes, sha256 $(sha256sum < "$f" | cut -c1-16)"
	else rm -f "$f"; say "    could not be read (gone already?)"; fi
}

# ---------------------------------------------------------------- the strings to mask
build_mask() {
	local f="$WORK/fixed.in" g
	: > "$f"
	if have nmcli; then
		TO 10 nmcli -g NAME connection show 2>/dev/null | sed 's/\\:/:/g' >> "$f"
		TO 10 nmcli -g UUID connection show 2>/dev/null >> "$f"
		TO 10 nmcli -g SSID device wifi list --rescan no 2>/dev/null | sed 's/\\:/:/g' >> "$f"
	fi
	{ hostname 2>/dev/null; cat /etc/hostname 2>/dev/null; sed -n 's/^PRETTY_HOSTNAME=//p' /etc/machine-info 2>/dev/null | tr -d '"'; } >> "$f"
	[ -n "${SUDO_USER:-}" ] && echo "$SUDO_USER" >> "$f"
	if have getent; then
		getent passwd 2>/dev/null | awk -F: '$3 >= 1000 && $3 < 60000 { print $1; split($5, g, ","); if (g[1] != "") print g[1] }' >> "$f"
	else
		awk -F: '$3 >= 1000 && $3 < 60000 { print $1; split($5, g, ","); if (g[1] != "") print g[1] }' /etc/passwd 2>/dev/null >> "$f"
	fi
	have loginctl && TO 5 loginctl list-users --no-legend 2>/dev/null | awk '{ print $2 }' >> "$f"
	for g in /sys/devices/soc0/serial_number /proc/device-tree/serial-number /sys/firmware/devicetree/base/serial-number; do
		[ -r "$g" ] && { tr -d '\0' < "$g"; echo; } >> "$f"
	done
	have lsblk && TO 5 lsblk -dno SERIAL 2>/dev/null >> "$f"
	tr ' ' '\n' < /proc/cmdline 2>/dev/null | sed -n 's/^androidboot\.serialno=//p' >> "$f"
	# never mask project / generic words or interface names
	ls /sys/class/net 2>/dev/null > "$WORK/ifnames"
	awk 'NR == FNR { skip[$0] = 1; next }
	     { sub(/^[ \t]+/, ""); sub(/[ \t]+$/, "") }
	     length($0) >= 3 && !skip[$0] && tolower($0) !~ /^(root|kernel|fedora|iceland|localhost|localhost\.localdomain|user|users|system|admin|gdm|none|unknown|test|guest|default|lo|wlan0|wlp1s0|usb0)$/ { print length($0) "\t" $0 }' \
		"$WORK/ifnames" "$f" | sort -t "$(printf '\t')" -k1,1rn -k2,2 | cut -f2- | awk '!seen[$0]++' > "$FIXED"
	rm -f "$f"
}

# ---------------------------------------------------------------- the known-issue table (invalid patterns are skipped)
prepare_known() {
	: > "$WORK/known.tsv"
	[ -r "$KNOWNSRC" ] || { addnote "known-issues.tsv not found next to the script: every finding reads NEW"; return; }
	[ -n "$AWK" ] || return
	local l re bad=0
	while IFS= read -r l; do
		case "$l" in '#'*|'') continue ;; esac
		re=$(printf '%s\n' "$l" | cut -f4)
		[ -n "$re" ] || continue
		if printf '%s\n' "$re" | "$AWK" '{ r = $0; if ("x" ~ r) {} }' 2>/dev/null; then printf '%s\n' "$l" >> "$WORK/known.tsv"
		else bad=$((bad + 1)); addnote "known-issues.tsv: invalid pattern skipped: $(printf '%s' "$l" | cut -f1)"; fi
	done < "$KNOWNSRC"
	KNOWNROWS=$(wc -l < "$WORK/known.tsv")
}

# ---------------------------------------------------------------- collection: logs
CLARGS=()
collect_logs() {
	local i w avail n
	SARG=(); [ -n "$SINCE" ] && SARG=(--since "$SINCE")
	if [ -n "$FIXTURE" ]; then
		for i in $(seq 0 19); do
			w=b0; [ "$i" -gt 0 ] && w="b-$i"
			if [ -r "$FIXTURE/journal-b$i.txt" ]; then
				mask < "$FIXTURE/journal-b$i.txt" > "$WORK/jall-$w"
				[ -r "$FIXTURE/err-b$i.txt" ] && { mask < "$FIXTURE/err-b$i.txt" > "$WORK/jerr-$w"; CLARGS+=("win=$w" "mode=j" "force=1" "$WORK/jerr-$w"); }
				CLARGS+=("win=$w" "mode=j" "force=0" "$WORK/jall-$w")
				grep -E '^\[ *[0-9.]+\] [^ ]+ kernel: ' "$WORK/jall-$w" > "$RAW/kernel-$w.txt"
			elif [ -r "$FIXTURE/dmesg-b$i.txt" ]; then
				mask < "$FIXTURE/dmesg-b$i.txt" > "$WORK/dmesg-$w"
				CLARGS+=("win=$w" "mode=d" "force=0" "$WORK/dmesg-$w")
				cp "$WORK/dmesg-$w" "$RAW/kernel-$w.txt"
			fi
		done
		NBOOTS=$(printf '%s\n' "${CLARGS[@]+"${CLARGS[@]}"}" | grep '^win=' | sort -u | grep -c .)
		return
	fi
	avail=0
	if have journalctl; then avail=$(TO 30 journalctl --list-boots --no-pager -q 2>/dev/null | grep -c .); fi
	n=$BOOTS; [ "$avail" -lt "$n" ] && n=$avail
	[ "$avail" -lt "$BOOTS" ] && addnote "journal holds $avail boot(s); $BOOTS asked (a volatile journal keeps only the current boot)"
	NBOOTS=$n
	for ((i = 0; i < n; i++)); do
		[ "$(left)" -gt 60 ] || { addnote "time budget: boots from b-$i on skipped"; break; }
		w=b0; BA=(-b); [ "$i" -gt 0 ] && { w="b-$i"; BA=(-b "-$i"); }
		note "journal of boot $w"
		TO 90 journalctl "${BA[@]}" "${SARG[@]+"${SARG[@]}"}" -o short-monotonic --no-pager -q 2>/dev/null | mask > "$WORK/jall-$w"
		TO 30 journalctl "${BA[@]}" "${SARG[@]+"${SARG[@]}"}" -p 0..3 -o short-monotonic --no-pager -q 2>/dev/null | mask > "$WORK/jerr-$w"
		TO 30 journalctl "${BA[@]}" "${SARG[@]+"${SARG[@]}"}" -p 0..3 -o json --output-fields=_SYSTEMD_UNIT,_SYSTEMD_USER_UNIT,SYSLOG_IDENTIFIER,PRIORITY,_TRANSPORT --no-pager -q 2>/dev/null > "$WORK/jjson-$w"
		TO 30 journalctl "${BA[@]}" "${SARG[@]+"${SARG[@]}"}" -p 0..4 -o short-monotonic --no-pager -q 2>/dev/null | mask > "$RAW/journal-warn-$w.txt"
		grep -E '^\[ *[0-9.]+\] [^ ]+ kernel: ' "$WORK/jall-$w" > "$RAW/kernel-$w.txt"
		CLARGS+=("win=$w" "mode=j" "force=1" "$WORK/jerr-$w" "win=$w" "mode=j" "force=0" "$WORK/jall-$w")
	done
	if [ "$NBOOTS" -eq 0 ] || [ ! -s "$WORK/jall-b0" ]; then
		addnote "no journal available: the kernel ring buffer (dmesg) is scanned instead"
		if have dmesg; then TO 20 dmesg 2>/dev/null | mask > "$WORK/dmesg-b0"; cp "$WORK/dmesg-b0" "$RAW/kernel-b0.txt"; CLARGS=("win=b0" "mode=d" "force=0" "$WORK/dmesg-b0"); NBOOTS=1; fi
	fi
}

# ---------------------------------------------------------------- collection: system checks (never in fixture mode)
check_context() {
	sec context
	say "Kernel:       $(uname -r 2>/dev/null)   (uptime $(awk '{ printf "%d h %02d min", $1 / 3600, ($1 % 3600) / 60 }' /proc/uptime 2>/dev/null))"
	say "System:       $(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-?}")"
	if have rpm; then
		say "Packages:     $(TO 20 rpm -q --qf '%{NAME}-%{VERSION}-%{RELEASE}  ' iceland-device iio-sensor-proxy libssc hexagonrpc iceland-firmware 2>/dev/null | sed 's/package \([^ ]*\) is not installed/\1: not installed /g')"
		say "Kernels:      $(TO 20 rpm -q --qf '%{VERSION}-%{RELEASE} ' kernel-iceland 2>/dev/null)"
	fi
	say "Command line: $(cat /proc/cmdline 2>/dev/null)"
	have getenforce && say "SELinux:      $(TO 5 getenforce 2>/dev/null)"
	say "Journal:      $(if [ -d /var/log/journal ]; then echo persistent; else echo volatile; fi), $NBOOTS boot(s) scanned${SINCE:+, since $SINCE}"
}

check_devices() {
	local d bus name drv compat ma mods m st n=0 nu=0 rest wfs
	sec devices
	say "4.1 Deferred probes (/sys/kernel/debug/devices_deferred)"
	if [ -r /sys/kernel/debug/devices_deferred ]; then
		TO 5 cat /sys/kernel/debug/devices_deferred 2>/dev/null > "$WORK/deferred"
		if [ -s "$WORK/deferred" ]; then
			sed 's/^/  /' "$WORK/deferred" | sayf
			while IFS= read -r d; do name=${d%%[[:space:]]*}; rest=${d#"$name"}; sysf MED probe "deferred: $name$(echo "$rest" | tr -s ' \t' ' ')"; done < "$WORK/deferred"
		else say "  none"; fi
	else say "  not readable (debugfs not mounted?)"; addnote "devices_deferred not readable"; fi

	say ""; say "4.2 Devices without a bound driver (only those with a modalias or a DT compatible; buses / names that never bind are left out)"
	: > "$WORK/unbound"
	for d in /sys/bus/*/devices/*; do
		[ -e "$d" ] || continue
		bus=${d#/sys/bus/}; bus=${bus%%/*}; name=${d##*/}
		case " cpu clockevents clocksource event_source workqueue container node memory nvmem soc genpd machinecheck edac iommu cec media gpio wmi nvmem-layout dax coresight iio memory_tiering pwrseq " in *" $bus "*) continue ;; esac
		case "$bus:$name" in i2c:i2c-[0-9]*|serial:serial[0-9]*|soundwire:sdw-master*|mhi:mhi[0-9]*|typec:port[0-9]*|spi:spi[0-9]*|scsi:host[0-9]*|scsi:target[0-9]*|spmi:spmi-[0-9]*) continue ;; esac
		n=$((n + 1))
		[ -e "$d/driver" ] && continue
		compat=""; [ -r "$d/of_node/compatible" ] && compat=$(tr '\0' ',' < "$d/of_node/compatible" 2>/dev/null)
		ma=""; [ -r "$d/modalias" ] && ma=$(head -c 300 "$d/modalias" 2>/dev/null)
		[ -z "$ma" ] && [ "$bus" = auxiliary ] && ma=$(sed -n 's/^MODALIAS=//p' "$d/uevent" 2>/dev/null)
		[ -z "$ma" ] && [ -z "$compat" ] && continue
		wfs=""; [ -r "$d/waiting_for_supplier" ] && [ "$(cat "$d/waiting_for_supplier" 2>/dev/null)" = 1 ] && wfs=" waiting_for_supplier"
		mods="none"
		if [ -n "$ma" ] && have modprobe; then
			mods=""
			for m in $(TO 5 modprobe -R "$ma" 2>/dev/null | sort -u); do
				st="not loaded"; [ -d "/sys/module/${m//-/_}" ] && st="loaded"
				mods="$mods${mods:+,}$m($st)"
			done
			[ -n "$mods" ] || mods="none"
		fi
		nu=$((nu + 1))
		echo "unbound: $bus:$name compat=,$compat modalias=${ma:--} module=$mods$wfs" >> "$WORK/unbound"
	done
	say "  $n devices on driver buses, $nu without a driver that could have one:"
	sed 's/^unbound: /  /' "$WORK/unbound" | sayf
	while IFS= read -r d; do
		case "$d" in *"(not loaded)"*|*"(loaded)"*) sysf MED probe "$d" ;; *) sysf LOW probe "$d" ;; esac
	done < "$WORK/unbound"

	say ""; say "4.3 Remote processors"
	for d in /sys/class/remoteproc/remoteproc*; do
		[ -e "$d" ] || { say "  none"; break; }
		name=$(rd "$d/name"); st=$(rd "$d/state")
		say "  ${d##*/}: $name state=$st recovery=$(rd "$d/recovery")"
		case "$st" in running|attached) [ "$name" = soccp ] && sysf LOW remoteproc "remoteproc: $name state=$st" ;;
		*) sysf HIGH remoteproc "remoteproc: $name state=$st" ;; esac
	done
	say "  (this tablet has no modem; ADSP and CDSP should run, the SoCCP is attached)"

	say ""; say "4.4 Pending device core dumps (/sys/class/devcoredump)"
	m=0
	for d in /sys/class/devcoredump/devcd*; do
		[ -e "$d" ] || continue
		m=1; name=$(basename "$(readlink -f "$d/failing_device" 2>/dev/null)")
		drv=$(basename "$(readlink -f "$d/failing_device/driver" 2>/dev/null)")
		say "  ${d##*/}: failing device $name (driver ${drv:-?})"; sysf HIGH crash "devcoredump: a pending crash dump of $name"
		[ -n "$SAVEDC" ] && save_devcd "$d" "$name" "$drv"
	done
	if [ "$m" = 0 ]; then say "  none"; else
		say "  (a dump lives 5 min after it was made, so it is recent; the number counts every dump since the boot."
		say "  msm display dumps (9801000.display-controller) are made at the first underrun of an enable, a frame-done"
		say "  timeout or a CTL reset failure - not by the vblank / commit-done timeouts alone)"
		[ -z "$SAVEDC" ] && say "  (run with --save-devcoredump to keep a copy of a display / GPU dump in raw/ for an upstream report)"
	fi

	say ""; say "4.5 Sound cards (/proc/asound/cards)"
	if grep -q ' \[' /proc/asound/cards 2>/dev/null; then grep ' \[' /proc/asound/cards | sed 's/^/  /' | sayf
	else say "  NO sound card"; sysf HIGH audio "sound: no sound card registered"; fi

	say ""; say "4.6 Display connectors"
	for d in /sys/class/drm/card*-*; do
		[ -e "$d/status" ] || continue
		say "  ${d##*/}: $(rd "$d/status"), enabled=$(rd "$d/enabled"), dpms=$(rd "$d/dpms")"
	done
	for d in /sys/kernel/debug/dri/*/state; do
		[ -r "$d" ] && TO 5 head -c 200000 "$d" 2>/dev/null | mask > "$RAW/drm-state-$(basename "$(dirname "$d")").txt"
	done

	say ""; say "4.7 Network and radio state (no names)"
	have nmcli && TO 10 nmcli -t -f DEVICE,TYPE,STATE device 2>/dev/null | sed 's/^/  /' | sayf
	have rfkill && TO 5 rfkill -n -o TYPE,SOFT,HARD 2>/dev/null | sed 's/^/  rfkill: /' | sayf
	[ -d /sys/class/bluetooth/hci0 ] || { say "  no Bluetooth adapter hci0"; sysf MED bluetooth "bluetooth: no adapter hci0"; }
}

check_units() {
	local u uid user out c
	sec units
	say "5.1 Failed units"
	if have systemctl; then
		out=$(TO 15 systemctl --failed --no-legend --plain --no-pager 2>/dev/null | awk '{ print $1 }')
		if [ -n "$out" ]; then for u in $out; do say "  system: $u"; sysf HIGH systemd "failed-unit: $u (system)"; done; else say "  system: none"; fi
		if have loginctl; then
			while read -r uid user; do
				[ -n "$uid" ] && [ "$uid" -ge 1000 ] 2>/dev/null || continue
				[ -S "/run/user/$uid/bus" ] || { say "  user session uid $uid: no session bus"; continue; }
				out="__fail"
				if have runuser; then out=$(TO 10 runuser -u "$user" -- env XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user --failed --no-legend --plain --no-pager 2>/dev/null) || out="__fail"
				elif have sudo; then out=$(TO 10 sudo -u "$user" XDG_RUNTIME_DIR="/run/user/$uid" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$uid/bus" systemctl --user --failed --no-legend --plain --no-pager 2>/dev/null) || out="__fail"; fi
				[ "$out" = "__fail" ] && { out=$(TO 10 systemctl --user -M "$user@" --failed --no-legend --plain --no-pager 2>/dev/null) || out="__fail"; }
				if [ "$out" = "__fail" ]; then say "  user session uid $uid: not readable"; continue; fi
				out=$(printf '%s\n' "$out" | awk 'NF { print $1 }')
				if [ -n "$out" ]; then for u in $out; do say "  user $uid: $u"; sysf HIGH systemd "failed-unit: $u (user session)"; done; else say "  user session uid $uid: none"; fi
			done < <(TO 5 loginctl list-users --no-legend 2>/dev/null | awk '{ print $1, $2 }')
		fi
		say ""; say "  iceland units:"
		TO 10 systemctl list-units 'iceland-*' --all --no-legend --plain --no-pager 2>/dev/null | awk '{ printf "    %-44s %s %s %s\n", $1, $2, $3, $4 }' | sayf
	else say "  systemctl missing"; fi

	say ""; say "5.2 Units restarted by systemd (journal 'Scheduled restart job')"
	c=0
	for f in "$WORK"/jall-*; do
		[ -r "$f" ] || continue
		grep -h 'Scheduled restart job, restart counter is at' "$f" 2>/dev/null |
			sed -E 's/^.*: ([^: ]+): Scheduled restart job, restart counter is at ([0-9]+).*$/\1 \2/' |
			awk -v w="${f##*/jall-}" '{ n[$1]++; if ($2 > mx[$1]) mx[$1] = $2 } END { for (u in n) print w, u, n[u], mx[u] }'
	done > "$WORK/restarts"
	if [ -s "$WORK/restarts" ]; then
		while read -r w u n mx; do
			say "  $w: $u restarted $n time(s) (counter up to $mx)"; c=1
			if [ "$n" -ge 3 ]; then sysf MED systemd "restart: $u restarted $n times in one boot"; else sysf LOW systemd "restart: $u restarted $n time(s) in one boot"; fi
		done < "$WORK/restarts"
	fi
	[ "$c" = 0 ] && say "  none"

	say ""; say "5.3 Core dumps (coredumpctl, newest 30)"
	if have coredumpctl; then
		TO 20 coredumpctl list --no-pager --no-legend -q ${SINCE:+--since "$SINCE"} 2>/dev/null | tail -n 30 | mask > "$RAW/coredumps.txt"
		if [ -s "$RAW/coredumps.txt" ]; then
			sed 's/^/  /' "$RAW/coredumps.txt" | sayf
			awk 'NF >= 8 { e = $(NF-1); s = $(NF-3); k = e " " s; n[k]++; t[k] = $2 " " $3 } END { for (k in n) print n[k] "\t" t[k] "\t" k }' "$RAW/coredumps.txt" |
				while IFS="$(printf '\t')" read -r n t k; do sysf HIGH crash "coredump: $k (x$n, last $t)"; done
		else say "  none"; fi
	else say "  coredumpctl missing"; fi

	say ""; say "5.4 SELinux denials (ausearch -m avc,user_avc -ts boot; grouped)"
	if have ausearch; then
		TO 30 ausearch -m avc,user_avc -ts boot -i 2>/dev/null | mask > "$WORK/avc"
		c=$(TO 30 ausearch -m avc,user_avc -ts today 2>/dev/null | grep -c 'type=.*AVC')
		awk '/avc: *denied|USER_AVC/ {
			p = ""; if (match($0, /\{ [^}]*\}/)) p = substr($0, RSTART, RLENGTH)
			cm = ""; if (match($0, / comm=[^ ]+/)) cm = substr($0, RSTART + 1, RLENGTH - 1)
			sc = ""; if (match($0, / scontext=[^ ]+/)) { sc = substr($0, RSTART + 10, RLENGTH - 10); n = split(sc, a, ":"); sc = (n >= 3) ? a[3] : sc }
			tc = ""; if (match($0, / tcontext=[^ ]+/)) { tc = substr($0, RSTART + 10, RLENGTH - 10); n = split(tc, a, ":"); tc = (n >= 3) ? a[3] : tc }
			cl = ""; if (match($0, / tclass=[^ ]+/)) cl = substr($0, RSTART + 1, RLENGTH - 1)
			pm = ""; if (match($0, / permissive=[01]/)) pm = substr($0, RSTART + 1, RLENGTH - 1)
			k = "denied " p " " cm " scontext=" sc " tcontext=" tc " " cl " " pm; cnt[k]++ }
			END { for (k in cnt) print cnt[k] "\t" k }' "$WORK/avc" | sort -rn > "$WORK/avc-groups"
		say "  today: ${c:-0} AVC records; this boot, grouped:"
		if [ -s "$WORK/avc-groups" ]; then
			sed 's/^/  /' "$WORK/avc-groups" | head -n 30 | sayf
			while IFS="$(printf '\t')" read -r n k; do sysf MED selinux "avc: $k (x$n)"; done < "$WORK/avc-groups"
		else say "  none"; fi
	else say "  ausearch missing (denials in the kernel log are classified in section 2)"; fi

	say ""; say "5.5 Journal priority err..emerg by unit (count per boot)"
	for f in "$WORK"/jjson-*; do
		[ -s "$f" ] && [ -n "$AWK" ] || continue
		"$AWK" -v w="${f##*/jjson-}" '
		function fld(n,    r) { r = "\"" n "\":\"[^\"]*\""; if (match($0, r)) return substr($0, RSTART + length(n) + 4, RLENGTH - length(n) - 5); return "" }
		{ u = fld("_SYSTEMD_UNIT"); uu = fld("_SYSTEMD_USER_UNIT"); id = fld("SYSLOG_IDENTIFIER"); tr = fld("_TRANSPORT"); p = fld("PRIORITY")
		  if (tr == "kernel") k = "kernel"; else if (uu != "") k = "user:" uu; else if (u != "") k = u; else k = "(" id ")"
		  sub(/@[0-9]+\.service$/, "@N.service", k); sub(/^user:app-.*-[0-9]+\.scope$/, "user:app-*.scope", k); sub(/session-[0-9]+\.scope/, "session-N.scope", k)
		  c[k]++; pr[k, p]++ }
		END { for (k in c) printf "%d\t%s\t%s\temerg-crit %d, err %d\n", c[k], w, k, pr[k,0] + pr[k,1] + pr[k,2], pr[k,3] }' "$f" 2>/dev/null
	done | sort -rn | head -n 30 | mask | awk -F'\t' '{ printf "  %-5s %6d  %-50s %s\n", $2, $1, $3, $4 }' | sayf

	say ""; say "5.8 Package manager (latest package changes; dnf log errors; dnf itself is not run: it writes its own log)"
	if have rpm; then TO 20 rpm -qa --last 2>/dev/null | head -n 12 | sed 's/^/  /' | sayf; fi
	for f in /var/log/dnf5.log /var/log/dnf.log; do
		[ -r "$f" ] || continue
		TO 10 tail -n 4000 "$f" 2>/dev/null | grep -E -i 'error|failed|problem|protected|conflict' |
			sed -E 's/^[0-9T:+.-]+ *//; s/^\[[0-9]+\] *//' | mask | sort | uniq -c | sort -rn | head -n 15 > "$WORK/dnferr"
		if [ -s "$WORK/dnferr" ]; then
			say "  ${f##*/} (last 4000 lines), error lines grouped:"; sed 's/^/  /' "$WORK/dnferr" | sayf
			while read -r n rest; do sysf MED packages "dnf-log: $(printf '%s' "$rest" | cut -c1-160) (x$n)"; done < "$WORK/dnferr"
		fi
	done

	say ""; say "5.9 rpm -V of the project's packages (running kernel only)"
	if have rpm; then
		{ TO 20 rpm -qa --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' 'iceland-*' 'iio-sensor-proxy*' 'libssc*' 'hexagonrpc*' 2>/dev/null
		  TO 20 rpm -qf "/lib/modules/$(uname -r)/vmlinuz" 2>/dev/null | grep -v 'not owned'; } | sort -u > "$WORK/pkgs"
		c=0
		while read -r p; do
			[ -n "$p" ] || continue
			if [ "$(left)" -lt 25 ]; then addnote "time budget: rpm -V skipped from $p on"; break; fi
			TO 60 rpm -V "$p" 2>&1 | tr -s ' ' ' ' > "$WORK/rpmv"
			if [ -s "$WORK/rpmv" ]; then
				c=1; say "  $p:"; mask < "$WORK/rpmv" | sed 's/^/    /' | head -n 40 | sayf
				while IFS= read -r l; do
					case "$l" in missing*) sysf HIGH packages "rpm-verify: ${p%%-[0-9]*}: $l" ;;
					*" c /"*) sysf LOW packages "rpm-verify: ${p%%-[0-9]*}: $l" ;;
					*) sysf MED packages "rpm-verify: ${p%%-[0-9]*}: $l" ;; esac
				done < <(mask < "$WORK/rpmv")
			fi
		done < "$WORK/pkgs"
		say "  verified: $(tr '\n' ' ' < "$WORK/pkgs")"
		[ "$c" = 0 ] && say "  no differences"
	fi
}

check_resources() {
	local f l t z typ v n p a mx s cur max
	sec resources
	say "6.1 Disk space and inodes"
	if have df; then
		TO 10 df -P -T -x tmpfs -x devtmpfs -x squashfs -x efivarfs -x overlay 2>/dev/null | mask > "$WORK/df"
		sed 's/^/  /' "$WORK/df" | sayf
		awk 'NR > 1 { u = $6; sub(/%/, "", u); if (u + 0 >= 97) print "HIGH\t" $7 "\t" u; else if (u + 0 >= 90) print "MED\t" $7 "\t" u }' "$WORK/df" |
			while IFS="$(printf '\t')" read -r s mnt u; do sysf "$s" storage "disk: $mnt is $u% full"; done
		TO 10 df -P -i -x tmpfs -x devtmpfs -x squashfs -x efivarfs -x overlay 2>/dev/null |
			awk 'NR > 1 { u = $5; sub(/%/, "", u); if (u + 0 >= 90) print $6 "\t" u }' | while IFS="$(printf '\t')" read -r mnt u; do sysf MED storage "disk: $mnt inodes $u% used"; done
	fi
	say ""; say "6.2 btrfs (device stats, read only)"
	if have btrfs && have findmnt; then
		TO 5 findmnt -n -t btrfs -o SOURCE,TARGET 2>/dev/null | sed 's/\[[^]]*\]//' | awk '!s[$1]++ { print $2 }' | head -n 3 > "$WORK/btrfs-mnts"
		while read -r mnt; do
			[ -n "$mnt" ] || continue
			TO 15 btrfs device stats "$mnt" 2>&1 | mask > "$WORK/bstats"
			sed 's/^/  /' "$WORK/bstats" | sayf
			awk '$NF ~ /^[0-9]+$/ && $NF > 0 { print }' "$WORK/bstats" | while read -r k v; do sysf HIGH storage "btrfs-stats: $k $v"; done
			TO 15 btrfs filesystem df "$mnt" 2>/dev/null | sed 's/^/  /' | sayf
			TO 15 btrfs scrub status "$mnt" 2>/dev/null | grep -E -i 'status|error|started|duration' | sed 's/^/  scrub: /' | sayf
		done < "$WORK/btrfs-mnts"
		[ -s "$WORK/btrfs-mnts" ] || say "  no btrfs mounted"
	else say "  btrfs / findmnt missing"; fi

	say ""; say "6.3 Memory and pressure (PSI)"
	grep -E '^(MemTotal|MemAvailable|SwapTotal|SwapFree|CmaTotal|CmaFree):' /proc/meminfo 2>/dev/null | sed 's/^/  /' | sayf
	have swapon && TO 5 swapon --show --noheadings 2>/dev/null | sed 's/^/  swap: /' | sayf
	for p in cpu memory io; do
		[ -r "/proc/pressure/$p" ] || { say "  PSI $p: not available"; continue; }
		while read -r l; do
			say "  PSI $p: $l"
			a=$(printf '%s' "$l" | sed -n 's/.*avg300=\([0-9.]*\).*/\1/p'); t=${l%% *}
			case "$p:$t" in
			memory:some) awk -v a="$a" 'BEGIN { exit !(a > 5) }' && sysf MED memory "psi: memory some avg300=$a" ;;
			memory:full) awk -v a="$a" 'BEGIN { exit !(a > 1) }' && sysf MED memory "psi: memory full avg300=$a" ;;
			io:some) awk -v a="$a" 'BEGIN { exit !(a > 10) }' && sysf MED storage "psi: io some avg300=$a" ;;
			io:full) awk -v a="$a" 'BEGIN { exit !(a > 5) }' && sysf MED storage "psi: io full avg300=$a" ;;
			cpu:some) awk -v a="$a" 'BEGIN { exit !(a > 50) }' && sysf LOW cpu-irq "psi: cpu some avg300=$a" ;;
			esac
		done < "/proc/pressure/$p"
	done
	say "  OOM kills: see section 2 (kind oom) and 5.6 (systemd-oomd)"

	say ""; say "6.4 Thermal zones (>= 95 C or read errors are findings) and active cooling states"
	n=0; mx=""
	for z in /sys/class/thermal/thermal_zone*; do
		[ -e "$z/type" ] || continue
		typ=$(rd "$z/type"); v=$(TO 3 cat "$z/temp" 2>&1 | head -c 120); n=$((n + 1))
		case "$v" in
		-[0-9]*|[0-9]*)
			printf '%s\t%s\n' "$v" "$typ" >> "$WORK/temps"
			if [ "$v" -ge 105000 ] 2>/dev/null; then sysf HIGH thermal "thermal: $typ at $((v / 1000)) C"
			elif [ "$v" -ge 95000 ] 2>/dev/null; then sysf MED thermal "thermal: $typ at $((v / 1000)) C"; fi ;;
		*) sysf LOW thermal "thermal: $typ temperature read failed: $(printf '%s' "$v" | sed 's/^.*: //')" ;;
		esac
	done
	say "  $n zones; the ten hottest (C):"
	[ -s "$WORK/temps" ] && sort -rn "$WORK/temps" | head -n 10 | awk -F'\t' '{ printf "    %6.1f  %s\n", $1 / 1000, $2 }' | sayf
	say "  cooling devices not at state 0:"
	for z in /sys/class/thermal/cooling_device*; do
		[ -e "$z/type" ] || continue
		cur=$(rd "$z/cur_state"); max=$(rd "$z/max_state")
		[ -n "$cur" ] && [ "$cur" != 0 ] && say "    $(rd "$z/type"): $cur / $max"
	done

	say ""; say "6.5 Power supplies (read only; values as the kernel reports them)"
	for f in /sys/class/power_supply/*; do
		[ -e "$f/type" ] || continue
		l=""; typ=$(rd "$f/type")
		for a in type status online capacity health voltage_now current_now power_now temp charge_full charge_full_design cycle_count usb_type charge_type input_current_limit charge_control_end_threshold; do
			[ -r "$f/$a" ] || continue
			v=$(TO 5 cat "$f/$a" 2>&1 | head -c 80 | tr '\n' ' '); v=${v% }
			case "$v" in *"cat: "*) sysf LOW power-supply "power-supply: ${f##*/} $a read failed: ${v##*: }"; v="ERR" ;; esac
			l="$l $a=$v"
			if [ "$typ" = Battery ]; then
				case "$a" in
				capacity) { [ "$v" -lt 0 ] || [ "$v" -gt 100 ]; } 2>/dev/null && sysf MED power-supply "battery: capacity $v out of range" ;;
				voltage_now) { [ "$v" -lt 3000000 ] || [ "$v" -gt 4600000 ]; } 2>/dev/null && sysf MED power-supply "battery: voltage_now $v uV out of 3.0-4.6 V" ;;
				temp) { [ "$v" -lt 0 ] || [ "$v" -gt 500 ]; } 2>/dev/null && sysf MED power-supply "battery: temp $v (0.1 C) out of 0-50 C" ;;
				health) case "$v" in Good|Unknown|ERR|"") ;; *) sysf MED power-supply "battery: health $v" ;; esac ;;
				esac
			fi
		done
		say "  ${f##*/}:$l"
	done

	say ""; say "6.6 Kernel taint and CPU state"
	t=$(cat /proc/sys/kernel/tainted 2>/dev/null || echo 0)
	if [ "${t:-0}" != 0 ]; then
		s=""
		set -- P "proprietary module" F "module force-loaded" S "SMP unsafe / out of spec" R "module force-unloaded" M "machine check" B "bad page" U "taint requested by user space" D "kernel died (oops / BUG)" A "ACPI table overridden" W "kernel warning (WARN)" C "staging driver" I "firmware bug workaround" O "out-of-tree module" E "unsigned module" L "soft lockup" K "live patched" X "auxiliary" T "struct randomisation" N "in-kernel test" J "fwctl"
		v=0
		while [ $# -ge 2 ]; do
			if [ $(( (t >> v) & 1 )) = 1 ]; then
				s="$s$1"
				case "$1" in D|L) sysf CRIT kernel "taint: $1 ($2)" ;; M|B|W) sysf HIGH kernel "taint: $1 ($2)" ;; *) sysf LOW kernel "taint: $1 ($2)" ;; esac
			fi
			v=$((v + 1)); shift 2
		done
		say "  tainted=$t flags=$s"
		for f in /sys/module/*/taint; do v=$(cat "$f" 2>/dev/null); [ -n "$v" ] && say "    module $(basename "$(dirname "$f")"): $v"; done
	else say "  not tainted"; fi
	v=$(cat /sys/devices/system/cpu/online 2>/dev/null); p=$(cat /sys/devices/system/cpu/possible 2>/dev/null)
	say "  CPUs online $v of $p"
	[ -n "$v" ] && [ "$v" != "$p" ] && sysf MED cpu-irq "cpu: online CPUs $v, possible $p"
	say "  cpuidle: driver $(rd /sys/devices/system/cpu/cpuidle/current_driver), governor $(rd /sys/devices/system/cpu/cpuidle/current_governor)"
	for f in /sys/devices/system/cpu/cpu0 /sys/devices/system/cpu/cpu7; do
		[ -d "$f/cpuidle" ] || continue
		l=""
		for z in "$f"/cpuidle/state*; do l="$l $(rd "$z/name"):usage=$(rd "$z/usage"),rejected=$(rd "$z/rejected")"; done
		say "  ${f##*/}:$l"
	done
	for f in /sys/devices/system/cpu/cpufreq/policy*; do
		[ -d "$f" ] || continue
		say "  ${f##*/}: cur $(rd "$f/scaling_cur_freq") max $(rd "$f/scaling_max_freq") of $(rd "$f/cpuinfo_max_freq") kHz, governor $(rd "$f/scaling_governor")"
	done
	for f in /sys/class/devfreq/*; do [ -r "$f/cur_freq" ] && say "  devfreq ${f##*/}: $(rd "$f/cur_freq") Hz ($(rd "$f/governor"))"; done

	say ""; say "6.7 Suspend statistics and wakeup sources"
	for f in /sys/power/suspend_stats/*; do [ -f "$f" ] && say "  suspend_stats/${f##*/} = $(rd "$f")"; done
	f=$(rd /sys/power/suspend_stats/fail); [ -n "$f" ] && [ "$f" != 0 ] && sysf MED suspend "suspend: $f failed suspend attempt(s) since boot (last failed device: $(rd /sys/power/suspend_stats/last_failed_dev))"
	say "  pm_print_times = $(rd /sys/power/pm_print_times), mem_sleep = $(rd /sys/power/mem_sleep)"
	for z in /sys/class/wakeup/wakeup*; do
		[ -r "$z/wakeup_count" ] || continue
		printf '%s\t%s\t%s\n' "$(rd "$z/wakeup_count")" "$(rd "$z/event_count")" "$(rd "$z/name")"
	done 2>/dev/null | sort -rn | head -n 10 | awk -F'\t' '$1 > 0 || NR <= 5 { printf "  wakeup source %-40s wakeups %s, events %s\n", $3, $1, $2 }' | sayf
}

# ---------------------------------------------------------------- run
note "issue-scan $VERSION -> $OUT"
if [ -z "$FIXTURE" ]; then build_mask; fi
prepare_known
collect_logs
if [ -z "$FIXTURE" ]; then
	check_context
	note "devices"; check_devices
	note "units, core dumps, SELinux, packages"; check_units
	note "resources"; check_resources
else
	sec context
	say "FIXTURE MODE: classifying the recorded logs in $(basename "$FIXTURE")/ (no system access, no scan checks)"
	say "Files: $(cd "$FIXTURE" && ls | tr '\n' ' ')"
	[ -r "$FIXTURE/sys.tsv" ] && cat "$FIXTURE/sys.tsv" >> "$WORK/sys.raw"
fi
mask < "$WORK/sys.raw" > "$WORK/sys.tsv"
[ -s "$WORK/sys.tsv" ] && CLARGS+=("win=now" "mode=s" "force=0" "$WORK/sys.tsv")

note "classifying"
if [ -n "$AWK" ] && [ ${#CLARGS[@]} -gt 0 ]; then
	TO 120 "$AWK" -f "$WORK/classify.awk" -v KNOWNF="$WORK/known.tsv" -v OUTD="$WORK" -v W0=b0 "${CLARGS[@]}" 2> "$WORK/classify.err" ||
		addnote "the classifier failed: $(head -c 300 "$WORK/classify.err")"
	[ -r "$WORK/groups.tsv" ] && cp "$WORK/groups.tsv" "$RAW/groups.tsv"
else
	addnote "classification skipped (GNU awk missing or no input)"
fi
cp "$WORK/sys.tsv" "$RAW/scan-checks.tsv" 2>/dev/null

# ---------------------------------------------------------------- report
REPORT="$OUT/report.txt"
part() { [ -s "$WORK/$1" ] && cat "$WORK/$1" || echo "  (not available)"; }
{
	echo "ISSUE SCAN - OnePlus Pad 4 (iceland), installed Fedora     issue-scan $VERSION"
	echo "Date: $(date '+%Y-%m-%d %H:%M %Z')   Run time: $((SECONDS - START)) s   Known-issue rows: ${KNOWNROWS:-0}"
	echo "Classes: NEW = not in known-issues.tsv (look at these first); KNOWN = recorded issue (KNOWN! = a row marked"
	echo "regression-if-seen: it was fixed and came back); INFO = looks like an error, is not one. SEV: CRIT > HIGH > MED > LOW."
	echo "WHERE: b0 = current boot, b-1 = the boot before, now = scan checks; counts are lines. Private values are masked."
	echo
	part sec-context.txt
	echo
	echo "======================================================================== 1. SUMMARY"
	part summary.txt
	echo
	echo "======================================================================== 2. KERNEL LOG"
	part sec-kernel.txt
	echo
	echo "======================================================================== 3. SUSPEND / RESUME"
	echo "(compares the lines before and after the most recent 'PM: suspend exit' of the current boot)"
	part sec-suspend.txt
	if [ -z "$FIXTURE" ]; then
		echo
		echo "======================================================================== 4. DEVICES AND DRIVERS"
		part sec-devices.txt
		echo
		echo "======================================================================== 5. USER SPACE"
		part sec-units.txt
	else
		echo
		echo "======================================================================== 5. USER SPACE"
	fi
	echo
	part sec-journal.txt
	if [ -z "$FIXTURE" ]; then
		echo
		echo "======================================================================== 6. RESOURCES AND STATE"
		part sec-resources.txt
	fi
	echo
	echo "======================================================================== 7. SCAN-CHECK FINDINGS, CLASSIFIED"
	part sec-checks.txt
	echo
	echo "======================================================================== 8. KNOWN-ISSUE ROWS SEEN"
	part sec-known.txt
	echo
	echo "======================================================================== 9. NOTES"
	if [ -s "$WORK/notes" ]; then sed 's/^/  /' "$WORK/notes"; else echo "  none"; fi
	echo "  raw files (masked): $(cd "$RAW" && ls | tr '\n' ' ')"
	echo "  full list of groups: raw/groups.tsv; the report is masked and meant to be pasted; check raw/ before sharing it."
} | mask > "$REPORT"
note "done in $((SECONDS - START)) s: $REPORT"
echo "$REPORT"

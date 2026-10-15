# issue-scan

A read-only issue scan of the installed Fedora 44 on the OnePlus Pad 4. It sorts every error-like line of the kernel
log and the journal, and the results of a set of system checks, into groups and marks each group KNOWN (a row of
`known-issues.tsv`), INFO (looks like an error, is not one) or NEW.

```
sha256sum -c SHA256SUMS
sudo bash issue-scan.sh                     # the current and the previous boot
sudo bash issue-scan.sh --boots 3           # three boots
sudo bash issue-scan.sh --since "-2h"       # only journal entries of the last two hours (journalctl syntax)
sudo bash issue-scan.sh --save-devcoredump  # also a masked copy of a pending display / GPU crash dump
```

It prints the report path, `/var/tmp/issue-scan-<date>-<time>/report.txt`; `raw/` holds the data files. A run
usually takes well under a minute.

## What it scans

- Kernel log of each boot: oops / BUG / WARN / call traces (one group per header and first real frame), lockdep, hung
  tasks, RCU stalls, timeouts, firmware loads, probe failures, display, GPU, audio, Wi-Fi / Bluetooth, USB-C / power
  supply, storage, thermal, cpuidle, remoteproc, clocks / regulators / power domains, IOMMU faults.
- Suspend / resume: device times per cycle, and the lines that appear only after the most recent resume.
- Devices: deferred devices, devices without a driver (against the expected list), remoteprocs, pending device core
  dumps, the sound card, display connectors, radios.
- User space: failed units, restart loops, core dumps, SELinux denials, journal errors per unit, dnf errors, `rpm -V`
  of the project's packages.
- State: disk space, btrfs device errors, memory pressure, thermal zones, the battery, kernel taint, cpufreq / cpuidle,
  suspend statistics, wakeup sources.

## Reading the report

Section 1 lists the NEW groups first, by severity and count, then KNOWN! (fixed before, seen again), then KNOWN.
WHERE names the boots (b0 = current, b-1 = the one before) and "now" (the system checks).

## Safety and privacy

Reads only: writes nothing outside `/var/tmp/issue-scan-*`, starts or restarts no service, loads no module, writes no
sysfs or debugfs file and reads no register file, `/dev/mem` or TLMM pad. Every command has a timeout; a missing tool
skips its check. Masked in the report and in `raw/`: MAC and Bluetooth addresses, IP addresses, Wi-Fi network and
connection names, user and real names, the host name, serial numbers, e-mail addresses and `/home/<user>`.
NetworkManager connection files are never read. Look through `raw/` before sharing it.

## Testing on a PC

`bash issue-scan.sh --fixture DIR` classifies recorded logs (`DIR/journal-b0.txt` from `journalctl -o
short-monotonic`, or `DIR/dmesg-b0.txt`, plus optional `err-b0.txt` and `sys.tsv`) without touching the system.

## Adding a known issue

One TAB-separated line in `known-issues.tsv`: id, class (KNOWN / INFO), scope (k kernel, j journal as
"ident: message", s system check, a any), a POSIX extended regex, the feature-matrix row, status, note. The first
matching row wins; an invalid pattern is skipped and named in the report.

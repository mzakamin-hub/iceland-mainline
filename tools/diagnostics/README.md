# Diagnostic tools for the tablet

Small scripts to run on a OnePlus Pad 4 with the installed Fedora 44. Copy a folder to the tablet, check it with
`sha256sum -c SHA256SUMS` and run the script with `sudo bash`. Each one writes its results to `/var/tmp/<tool>-<time>/`.

| Folder | What it does | Changes the system |
|---|---|---|
| [issue-scan](issue-scan/) | scans the kernel log, the journal and the system state for known and new issues | no (read only) |
| [battery-check](battery-check/) | checks the battery reporting from the kernel up to UPower over a timed run | no (read only) |
| [glitch-probe](glitch-probe/) | measures the display path while the lower-quarter flicker can occur | runtime only, undone at exit |
| [als-modes](als-modes/) | streams one sensor-hub sensor at a time to find which one goes with the flicker | runtime only, undone at exit |
| [keep-only-current](keep-only-current/) | removes every kernel and root snapshot except the running ones | yes, after a typed confirmation |

The reports mask MAC / Bluetooth addresses and serial numbers. Read a report before you share it.

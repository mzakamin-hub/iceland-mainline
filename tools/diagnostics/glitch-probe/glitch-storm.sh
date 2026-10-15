#!/bin/bash
# glitch-storm.sh HZ SECS OUTFILE - part of glitch-probe: D-Bus load WITHOUT any sensor.
# Runs as the session user. HZ times per second it makes one property read on the session bus
# that gnome-shell's (mutter's) main thread answers, and one on the system bus that
# iio-sensor-proxy's main loop answers (GetAll: no Claim, so no sensor starts streaming).
# Read-only D-Bus calls; ends by itself after SECS seconds.
set -u
HZ=${1:-20}; SECS=${2:-15}; OUTF=${3:-/dev/null}
[ "$HZ" -gt 0 ] 2>/dev/null || HZ=20
PERIOD=$(awk -v h="$HZ" 'BEGIN{printf "%.4f", 1/h}')
END=$(( $(date +%s) + SECS ))
n=0; fs=0; fy=0
while [ "$(date +%s)" -lt "$END" ]; do
	busctl --user get-property org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig \
		org.gnome.Mutter.DisplayConfig PowerSaveMode > /dev/null 2>&1 || fs=$((fs+1))
	busctl --system call net.hadess.SensorProxy /net/hadess/SensorProxy org.freedesktop.DBus.Properties \
		GetAll s net.hadess.SensorProxy > /dev/null 2>&1 || fy=$((fy+1))
	n=$((n+1))
	sleep "$PERIOD"
done
echo "storm: $n rounds at ${HZ} Hz target over ${SECS} s; session-bus failures $fs, system-bus failures $fy" > "$OUTF"

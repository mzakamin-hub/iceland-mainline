# glitch-probe

Finds which part of the path causes the flicker / tearing in the lower quarter of the screen while a sensor streams
(automatic brightness, auto-rotate, `monitor-sensor`): the display engine (fetch underruns, late or overlapping CTL
flushes, frame-done / vsync accounting), the CPU side (display interrupt latency, idle depth), the compositor (missed
frames, cursor plane), the touch / panel side, or the sensor path itself (iio-sensor-proxy against a direct `ssccli`
client against a plain D-Bus load with no sensor). It measures the fresh state (phase A) and the state after one
screen blank (phase B).

## Run

Restart the tablet, log in, turn automatic brightness off and keep the screen on. Copy this folder to the tablet and
run it from a terminal; it needs no input after the start and takes about 6 minutes:

```
sudo bash glitch-probe.sh --auto --ab-irq --ab-qos --ab-hwcursor
```

A maximized test window (`glitch-motion.py`, GTK) animates during each stage. Between phase A and B the probe turns
the screen off for 6 s and on again by itself (mutter's PowerSaveMode; if mutter refuses: lock the session, the same
again, unlock). It never uses the power key and never suspends. If the screen has already blanked once since the boot,
add `--phase B`. Other options: `--secs N`, `--blank none`, `--extra`, `--no-trace`, `--no-motion`, `--out DIR`
(see `--help`).

## Stages (15 s each)

| Stage | What runs |
|---|---|
| base-static | nothing streams, no motion window |
| base | nothing streams (this and every later stage runs the motion window) |
| proxy-light | `monitor-sensor --light` through iio-sensor-proxy |
| storm | D-Bus property reads at 20 Hz to mutter and iio-sensor-proxy, no sensor |
| ssccli-light | the light sensor straight from the sensor hub, no proxy |
| `--extra` | + proxy-accel, + monitor-sensor printing into the terminal |
| phase B `--ab-irq` | proxy-light with the display interrupt on the biggest CPU (restored after) |
| phase B `--ab-qos` | proxy-light with `/dev/cpu_dma_latency` = 0 held (released after) |
| phase B `--ab-hwcursor` | proxy-light with mutter's hardware cursor off (only if mutter offers it) |
| phase B proxy-light | once more without the switches |

## Output

`/var/tmp/glitch-probe-<time>/`: `summary.txt` (preflight, per-stage table) and `analysis.txt` (from
`glitch-analyze.py`) are the short result. `analysis.txt` ends with a verdict per stage (GLITCH-EVIDENCE / SUSPECT /
CLEAN / NO-DATA from underruns, frame-done timeouts, CTL flush overlaps, new display crash dumps, missed
presentations, late latches and interrupt jitter) and one line on the display clock vote after the blank. The folder
also holds the per-stage traces and counters, the blank's trace and kernel lines, and masked copies of display crash
dumps. `python3 glitch-analyze.py /var/tmp/glitch-probe-<time>` re-runs the analysis.

## Safety

Read only, except runtime actions that a trap undoes (also on Ctrl-C): its own tracefs instance, its own short sensor
/ D-Bus clients and motion window (stopped by PID), an idle inhibitor, one screen off / on, and the three optional A/B
switches, each only for its own stage. No package, configuration, partition or setting change. It never opens
register files (no regmap `registers`, no display register snapshots, no `/dev/mem`, no TLMM); files that take the
display's modeset locks are read only between stages. `drm.debug` is raised only for the blank window and written
back right after it. Display crash dumps are read, never written (the dump stays pending); MAC- and serial-like
tokens are masked in the copies.

## Files

`glitch-probe.sh` (the probe), `glitch-analyze.py` (the analyzer, Python standard library), `glitch-storm.sh` (the
no-sensor D-Bus load), `glitch-motion.py` (the motion window: python3-gobject with GTK 4, else GTK 3), `SHA256SUMS`.

Tested on a PC with a full fixture run (fake /sys, /proc, debugfs, tracefs, stub commands and a synthetic trace),
including the A/B switches and their restore; not yet run on the tablet.

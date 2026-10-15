# als-modes

Finds which sensor-hub (SSC) stream goes with the flicker in the lower quarter of the screen: it streams one sensor
at a time with `ssccli` (accelerometer, light, proximity, magnetometer, gyroscope) between two idle modes, and records
the display's vsync / underrun counters, the ADSP wake-ups and the regulator / interconnect votes of each mode.

Before the run: GNOME session with the screen on, automatic brightness off, `monitor-sensor` closed, and the keyboard
connected (GNOME then releases the accelerometer, so the idle modes are really idle).

```
sudo bash als-modes.sh              # the accelerometer stream rate + 7 modes of 15 s; asks after each mode
sudo bash als-modes.sh --secs 20    # longer modes
sudo bash als-modes.sh --auto       # no questions (answers recorded as '-')
sudo bash als-modes.sh --bwpin      # + 2 modes with the display's clock / bandwidth votes pinned high
```

Output: `/var/tmp/als-modes-<time>/`; `summary.txt` is the short result, the `mode*.diff` files show the vote changes.

Safety: no package, configuration or partition change and no service stopped. It reads single debugfs summary files
(regulators, interconnects, the display encoders' counters, ADSP sleep stats), never register files, `/dev/mem` or
TLMM pads. `--bwpin` writes the display driver's own debugfs perf knobs for two modes and restores them at exit, also
on Ctrl-C. Needs `ssccli` from the `libssc` package.

`0001-libssc-sample-rate-test-knob.patch` is a diagnosis-only patch for libssc (base 54dd13e): the environment variable
`LIBSSC_SAMPLE_RATE=min|max|<Hz>` makes `ssccli` / iio-sensor-proxy request the lowest, the highest or a given rate
instead of the first advertised one. It is not part of the project's libssc package.

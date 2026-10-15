# battery-check

A read-only check of the battery reporting on the OnePlus Pad 4: `qcom_battmgr` (kernel) ->
`/sys/class/power_supply` -> UPower -> GNOME.

```
sudo bash battery-check.sh                  # 10 min, a sample every 10 s, charger unplugged
sudo bash battery-check.sh --minutes 30     # a longer run gives a better coulomb count
sudo bash battery-check.sh --charger        # the same with a charger plugged in
sudo bash battery-check.sh --minutes 0      # one snapshot only
```

It dumps every power-supply property and UPower's view of the battery, samples them for the chosen time and prints a
PASS / CHECK / FAIL table: power_now against voltage x current, charge against capacity, full against design, the
energy scale UPower uses, the status against the sign of the current, temperature and voltage limits, the coulomb
count (integrated current against the change of charge_now), UPower's rate and time estimates, and in charger mode
the input voltage, input power and charge limit. Keep the load steady during the run: the check measures it.

Output: `/var/tmp/battery-check-<time>/` (`report.txt`, `samples.txt`, the property dumps).

Safety: writes nothing outside that folder, changes no charging setting, reads no debugfs or register file. Serial
numbers are dropped and MAC-like values masked; only the tablet's own battery and line-power devices are dumped.
Needs `python3` and `upower`.

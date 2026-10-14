# CPU / GPU scaling on the Pad 4: the stock references and what mainline uses (2026-09-29)

Status (14 Oct 2026): the GPU level table, the CPU capacity values and the GNOME power modes were verified in the
earlier kernel runs (q20, q21). Since then:
- iceland-device 0.28-8 adds the stock boost ceiling on input (stock raises the big-core cap by about one level during an
  input boost) and the stock screen-off thermal table. These are PC-tested only: rehearsal rows TS1-TS3 (boost at
  gear 3 or more, screen-off read) are not run yet.
- The installed system (13 Oct evening) runs the stock 20-gear policy in iceland-thermal. Stock's table caps the big cores
  to 1.86 GHz from a 33 C shell estimate and to 1.63 GHz from 35 C. The measured caps and gears are in the reference
  note (section 5, thermal on the installed system).
- The GPU runs Mesa 26.2.4 on the installed system (the 26.2.3 figure below is the 29 Sep run).
- The GNOME profile mapping is in the device package; whether it is unchanged in 0.28-8 is unverified.
- Power on the installed system at idle (14 Oct, 60 s report): 2.08 W average at 120 Hz with one Electron app
  open. The 10.7 W reading of the first evening (13 Oct) had a load cause: first-day work, an Electron GPU crash loop,
  and Wi-Fi power save switched off for a test.

The user's question: should the GPU and CPUs scale with usage and with GNOME's power setting, and can a governor be
built for this tablet from OxygenOS / LineageOS values? Answer: the scaling itself is the kernel's (schedutil on the
SCMI cpufreq driver, devfreq on the GPU), and both already run stock's frequency tables. What was missing is listed
below with its stock source. Values only; no stock file is committed.

## Sources

| Source | What it gives | Where read |
|---|---|---|
| Stock 11.A.38 base DTBs (`vendor_boot_a`, 14 FDTs, the Pad 4 = "CanoeP SoC") | per-CPU `capacity-dmips-mhz`, `dynamic-power-coefficient`; the kgsl level table | the user's private partition backup, carved on the PC (private dir) |
| Stock `init.kernel.post_boot-canoe*.sh` | WALT tunables; the schedutil fallback branch (governor, frequency floors, RT clamp) | `vendor_a` carved from `super.img` (private) |
| LineageOS 24.0 capture (2026-09-28) | cpufreq tables per cluster (`walt` governor), cooling devices | the raw capture (not published); decoded in `docs/device-facts/README.md` |
| Stock `powerhint.xml`, `perf/*.xml` | perf-HAL boost hints (opaque resource ids, no governor values) | private |
| Mainline kernel tree (29 Sep: 7.3-rc4 + queue) | `kaanapali.dtsi` CPU nodes (SCMI perf domains, no capacity data), msm GPU devfreq | the PC's kernel source tree |

## CPU

| Item | Stock value | Mainline before | Now |
|---|---|---|---|
| cpufreq table, cluster 0 (cpu0-5) | 384000 … 3628800 kHz (28 steps) | the same (SCMI perf domain 0) | — |
| cpufreq table, cluster 1 (cpu6-7) | 768000 … 4396800 kHz (27 steps) | the same (SCMI perf domain 1) | — |
| `capacity-dmips-mhz` | 1792 (cpu0-5), 1894 (cpu6-7) | **absent → every core capacity 1024**, no `SD_ASYM_CPUCAPACITY`, no EAS | DTS candidate (branch `dcvs`, kernel q21; re-check for q89g: unverified) |
| `dynamic-power-coefficient` | 238 (cpu0-5), 588 (cpu6-7) | absent (the SCMI driver registers its own energy model, so this is stock alignment) | same candidate |
| governor | WALT (out of tree); stock's own fallback = **schedutil** | schedutil | schedutil (profiles) |
| `scaling_min_freq` | fallback: 614400 / 864000 kHz (another branch: 787200 / 864000) | table minimum 384000 / 768000 | balanced 614400 / 864000; performance 787200 / 864000; power saver 384000 / 768000 |
| `sched_util_clamp_min_rt_default` | 0 (post_boot "reset the RT boost") | 1024 | 0 (profiles) |
| efficient-range edges (Power Saver caps) | `zone_max_util_pct` 2611200 (cluster 0); `smart_freq ipc_freq_levels` 3513600 first level (cluster 1) | uncapped | Power Saver max 2611200 / 3513600 |
| input boost | WALT input_boost 864000 kHz / 100 ms | none (no equivalent) | not as WALT input boost; 0.28-8 adds the stock boost ceiling on input (PC-tested, see status) |
| `sched_pelt_multiplier` | 1 | 1 | — |

With 1792 × 3.6288 GHz vs 1894 × 4.3968 GHz the small cores get about 78 % of a big core's capacity, so the scheduler
knows which cluster is which: misfit tasks migrate up, and energy-aware placement can run on the SCMI energy model
(31 / 32 performance states with power values, already registered).

## GPU

| Item | Stock value | Mainline |
|---|---|---|
| level table (speed bin 0xfc) | 160 … 1200 MHz, 18 levels incl. **1100 MHz** (TURBO_L2, ACD 0x88295ffd), bus index 9 (16.5 GB/s) at 1000/1050 MHz | 17 levels; 1100 missing and 12.45 / 20.83 GB/s at 1000 / 1050 → DTS candidate (`gpu-tune`, in q20/q21), verified in area-graphics-1 |
| initial level | 222 MHz | devfreq starts at the top and settles |
| DCVS | kgsl's own (no DT tunables beyond the table) | devfreq `simple_ondemand`, up 50 % / down 10 %, 50 ms, boost on wake; goes to 1.2 GHz under load at once (area-graphics-1: pinning gained 0 %) |
| thermal | 105 °C passive → GPU cooling (stock and mainline); stock 125 °C "hot" monitor only, mainline adds a 125 °C critical | Thermal area |

## GNOME power modes

Fedora 44 here runs **tuned-ppd**, so GNOME's Power Saver / Balanced / Performance select tuned profiles
(`/etc/tuned/ppd.conf`: powersave / balanced (+ balanced-battery) / throughput-performance). Fedora's profiles set
x86 knobs (EPB/EPP, platform_profile) that don't exist on this SoC, so the switch did nothing. iceland-device 0.10
(the first version with these files; the current package is 0.28-8) ships `iceland-balanced`, `iceland-balanced-battery`, `iceland-powersave`, `iceland-performance` with the values
above and `iceland-power-profiles apply` remaps tuned-ppd to them (between marker lines, `reset` removes them).
`throughput-performance`'s pinned `performance` governor is deliberately not used: the GPU already reaches 103 °C at
1.2 GHz in a minute of load, so pinning adds heat, not speed.

## Verification

- area-graphics-1 (q20): the 1100 MHz level works; DCVS already at the top under load; Mesa 26.2.3 > main (the
  installed system now runs Mesa 26.2.4).
- area-power-1 (q21): capacity 78 % / 100 %, `SD_ASYM_CPUCAPACITY`, energy model, the three GNOME modes switching
  the profiles (sysfs read back), one busy thread landing on a big core, eight threads raising both clusters, idle
  back to the floors.

# Stock display power, bandwidth and CPU thermal (OnePlus Pad 4, 11.A.38)

Read on the user's PC on 2026-09-28 by the PC relay session (see [relay/](../../relay/README.md)). The sources stay on
the PC and are not committed:

- `merged-stock.dts`: the stock base DTB with the "iceland-O IN" overlay merged, from the DSU capture of 2026-09-28 03:00
  (WSL `~/android/captures/dsu-stock-20260928-0300/`).
- `live-screen-on-20260928-031810.txt`: stock Android with the screen on (`C:\platform-tools\`), including the
  regulator summary.
- `thermal-zones.txt` and `cooling-devices.txt` from the same capture.

## RPMh rails: names used by the stock kernel

| Stock regulator | RPMh resource | Boot proxy vote |
|---|---|---|
| `pmh0110_g_s5_level` | `cx.lvl` | – |
| `pmh0110_d_s7_level` | `mmcx.lvl` | **0x180 (384 = TURBO)** |
| `pmh0110_f_s9_level` | `mxc.lvl` | **0x180** |
| `pmh0110_f_s9_mmcx_voter_level` | `mxc.lvl`, parent supply = MMCX | – (downstream helper that keeps MXC ≥ MMCX) |
| `pmh0110_i_s10_level` | `mx.lvl` | **0x180** |

MMCX, MXC and MX all carry `qcom,proxy-consumer-enable` with `qcom,proxy-consumer-voltage = <0x180 0xffff>`. The stock
kernel therefore holds all three at TURBO from probe until its proxy votes are dropped late in boot. ABL's splash runs in
that state.

## Screen on, stock Android: who votes for what

This is from the regulator summary (use counts). These are APPS-side votes only. The display CRM/CESTA hardware can vote
on its own (`qcom,disp_crm-crmc` on dispcc, `qcom,mdss-disable-cesta-hw-sleep` on the display node), so a count of 0
means the kernel doesn't vote. It doesn't mean the rail is off.

| Rail | Use | Display consumers |
|---|---|---|
| MMCX (`d_s7`) | 3 | `9800000.qcom,mdss_mdp-mmcx` 1, `9ba2000.clock-controller-vdd_mm` (dispcc) 1 + 1 |
| MX (`i_s10`) | 4 | **`9ba2000.clock-controller-vdd_mx` (dispcc) 1**; GCC `100000` holds the rest |
| MXC (`f_s9`) | **0** | none. All 13 `*_vdd_mm_mxc_voter` handles (camcc `956d000`, `20f0000`, `24f0000`) and every `vdd_mxc` are 0 |
| CX (`g_s5`) | 1 | GCC |

Display regulators that were on: `soc:qcom,dsi-display-primary-vddio` on `pmh0101_l12` (1.9 V, 220 mA). The DSI controllers'
`vdda-1p2` (both links) are on `pmh0110_d_l1` (1.2 V). The DSI PHYs' `vdda-0p9` (both) are on `pmh0110_d_l3` (0.88 V). The
DSI PHY GDSCs `9ac1000`/`9ac4000` were on.

## Stock DT consumers

- **dispcc** `clock-controller@9ba2000` (`qcom,canoe-dispcc`): `vdd_mm-supply` = MMCX and **`vdd_mx-supply` = MX**. It
  has **no MXC supply**. Child `qcom,canoe-dispcc_mx` @ 0x9ba4000.
  By contrast, camcc @ 0x956d000 has `vdd_mm`, `vdd_mx`, `vdd_mxc` and `vdd_mm_mxc_voter`.
- **mdss_mdp** @ 0x9800000: `mmcx-supply` only.
  - Clock rates: vsync 19.2 MHz, lut and ssip **650 MHz**. This confirms the "650 MHz MDP = TURBO" finding from test 5.
- **MDP interconnects** `qcom,sde-data-bus0`, `qcom,sde-ebi-bus` and `qcom,sde-reg-bus` (downstream units are kBps):
  - `qcom,sde-ib-bw-vote = <2500000 0 800000>`;
  - `qcom,sde-min-core-ib-kbps = <2500000>` (2.5 GB/s), `qcom,sde-min-llcc-ib-kbps = <0>`, `qcom,sde-dram-channels = <4>`;
  - `qcom,sde-max-bw-low-kbps` / `-high-kbps` = 21 400 000 / 30 200 000.
- For scale: scanning out 3392×2400×4 B takes 1.95 GB/s at 60 Hz, 3.91 GB/s at 120 Hz and 4.69 GB/s at 144 Hz.

## Compared with Linux test 6

`linux-run6/linux-genpd.txt`: `mmcx on 384`, while `mx`, `mx_ao`, `mxc`, `mxc_ao` and `cx` were all `off-0`.
`linux-interconnect.txt`: `qnm_mdp` was 0/0. The stock data shows that the rail dispcc needs besides MMCX is **MX, not
MXC**.

## CPU thermal (stock)

Every `cpu-X-Y-Z` zone has the same trips; `cpullc-*` has the same set without the 105 °C one:

| Trip | °C | Hysteresis | Type |
|---|---|---|---|
| `thermal-hal-config` | 105 | 5 | passive (the userspace HAL acts on it) |
| `cpuN-emerg0-cfg` | 112 | 4 | passive → kernel cooling map to CPU pause devices |
| `cpuN-emerg0-1-cfg` | 114 | 6 | passive → kernel cooling map |
| `reset-mon-cfg` | 125 | 0 | hot |
| `thermal-engine-config` | 135 | 1 | passive (userspace) |

Cooling devices: `cpufreq-cpu0` (27 states), `cpufreq-cpu6` (28 states), `pause-cpuN` and `thermal-pause-*`, and also
`display-fps` (16), `kgsl`/`gpu` (17), `ddr-cdev` and `ufs`.

With DSU busy, the CPU zones read **66–80 °C**. That is the starting point for any passive trip.

Other kaanapali trees have no passive CPU trips either. infiniti-mainline master / `vlinkz/development` and the XEC tree
(Xlie-Electronic-Customs/linux) only have hot and critical trips, so the stock table above is the only reference.

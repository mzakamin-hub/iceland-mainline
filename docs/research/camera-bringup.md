# Camera bring-up plan, OnePlus Pad 4 (from the sources we have)

Status 2026-09-29: not started. Camera is the hardest item (TODO difficulty 4). Rule 13 applies: every value comes
from Pad 4 stock (OxygenOS 11.A.38 captures and partitions, the user's LineageOS trees, OnePlusOSS OPD2514).

## 1. What the sources already give us

**Hardware (live stock DT capture 2, relay 002, odm `lib64/camera`):**

| | Rear ("icelandmain") | Front ("icelandfront") |
|---|---|---|
| Sensor | SmartSens **SC1320CS**, 13 MP | SmartSens **SC820CS**, 8 MP |
| Bus / address | **GENI I2C `i2c@884000` (QUP2)**, 0x6c; *not* the CCI | the same bus, 0x20 |
| CSI | **CSIPHY 4** (`csiphy-sd-index = 4`) | **CSIPHY 5** (`csiphy-sd-index = 5`) |
| MCLK | camcc clock index 0x11, **19.2 MHz** (`clock-rates = 19200000`) | the same |
| Reset | PMH0110 GPIO **14** (`CAM_RESET1_1P8`) | PMH0110 GPIO **13** |
| Supplies (stock min=max) | cam_vana **2.8 V** (600 mA), cam_vdig **1.2 V** (120 mA), cam_vio **1.8 V** (300 mA), cam_vaf 2.8 V | vio 1.8 V, vana 2.8 V, vdig 1.2 V |
| Power domain | camcc domain 5 (stock `power-domains = <camcc 5>`, TITAN top) | the same |
| Extras | actuator `qcom,cam-i2c-actuator` at **0x18** (vio + vaf); EEPROM (0x50/0x58); PDAF; the flash is `back_pmic_flash` (our 0031 LEDs) | EEPROM |
| Orientation | yaw 180, pitch 0, roll 90 | yaw 180, pitch 0, roll 90 |
| Chip-ID hint | `ftm_setting_compatible = <0x52 0x3107 0x02 0x02 0xc658>`: a factory ID check (register 0x3107, 2 bytes, 0xc658?), to confirm on the bus | – |
| Tuning / modes (stock userspace) | `com.qti.sensormodule.icelandmain.bin` (register tables + modes), `com.qti.sensor.icelandmain.so`, `com.qti.tuned.icelandmain.bin`, `awb_parameter_icelandmain.bin` | the same with `icelandfront` |

**Kernel side we already carry (infiniti in queue 0001):**
- kaanapali **CAMSS** (`qcom,kaanapali-camss` `isp@9253000`, `csiphy/csid/vfe_res_kaanapali`, interconnects);
- **CCI** nodes (not needed here, since the sensors are on GENI I2C);
- camcc.

Upstream is reviewing "CAMSS RDI-only on kaanapali" (CSIPHY, CSID, TFE; v15, needs a `qdss_debug_xo` clock;
relay 010 compares it with infiniti's version). **RDI-only** means raw Bayer frames straight to memory. Qualcomm's
image processing (IFE/IPE/BPS and the `CAMERA_ICP` firmware) isn't usable on mainline, so processing is done by
libcamera's **software ISP** (CPU/GPU).

**Not available anywhere:** mainline drivers for SC1320CS / SC820CS or the actuator IC. Downstream, the kernel driver
is Qualcomm's generic `cam_sensor`; the sensor **register sequences live in the userspace `sensormodule.bin`**.

## 1b. Resolved from the stock DT (Mainline, 2026-09-29), mapped to our DT labels

| Stock | Value | Our DT |
|---|---|---|
| cam_vana (both sensors) | `pmh0101_l14`, 2.8 V, 600 mA | `vreg_l14b_2p8` |
| cam_vaf (rear actuator) | `pmh0101_l16`, 2.8 V, 120 mA | `vreg_l16b_2p8` |
| cam_vdig (both) | `pmh0110_f_l1`, 1.2 V, 120 mA | `vreg_l1f_1p2` |
| cam_vio (both, actuator) | `pmh0110_f_l2`, 1.8 V, 300 mA | `vreg_l2f_1p8` |
| **MCLK** `cam_clk` | **`<&rpmhcc RPMH_DIV_CLK1>`** at 19.2 MHz, output on **PMK8850 GPIO 2, function func2** (`cam_sensor_main_mclk1_active`: output-enable; suspend: high-Z). **Not** a camcc MCLK. | `&rpmhcc RPMH_DIV_CLK1` (in clk-rpmh for kaanapali) + a `pmk8850_gpios` gpio2 func2 pin state |
| Reset, rear | PMH0110 **SID 6** GPIO 14 (`CAM_RESET1_1P8`), drive 2, low in suspend | `&pmh0110_g_e0_gpios 14` |
| Reset, front | PMH0110 SID 6 GPIO 13 | `&pmh0110_g_e0_gpios 13` |
| Power domain | `<&camcc 5>` (camcc@956d000) | `&camcc` index 5 (check its name in the kaanapali camcc binding) |
| Actuator | `qcom,cam-i2c-actuator` @0x18, supplies vio + vaf; IC name not in the DT | to find in the sensormodule/.so (relay 014) |

Still needed from relay 014 (C0): the power-up order and delays, the register tables, the CSI lane count and link
frequency, the EEPROM sizes, and the actuator IC.

## 2. Plan (every step RAM boot only; the PC's automated loop, relay 012, runs the kits)

**C0. Collect the missing stock values (PC, read-only).**
1. From the stock DT: the actuator node details (the IC's name if present), the EEPROM nodes (addresses, sizes,
   power), the camcc clock name behind index 0x11, the PMIC LDOs behind cam_vana/vdig/vio/vaf, the pinctrl states
   for MCLK and reset, and the power-up/down sequence and delays (`cam_sensor` power settings in the sensormodule).
2. **Register tables:** parse `com.qti.sensormodule.icelandmain/front.bin` (CHI sensor-module format: init, mode,
   stream-on/off, exposure/gain registers, CSI lanes, link frequency, line length and frame length) with a small parser
   written from the format's structure. Cross-check by **tracing the stock camera under LineageOS** (root, read-only):
   ftrace `cam_cci`/`i2c` events, or the camera driver's debug log, while the camera app opens each sensor. Record
   every write, each mode's lane count and data rate, the chip-ID read, and the actuator and EEPROM accesses.
3. The OnePlusOSS camera sources (OPD2514) for anything board-specific (power sequencing quirks).

**C1. Kernel plumbing in the Pad 4 DT (M, candidate patches).**
- On `i2c@884000` (enable it): the `sc1320cs@6c` and `sc820cs@20` nodes with clocks (camcc MCLK at 19.2 MHz),
  supplies (the stock LDOs and voltages), `reset-gpios` (PMH0110 14/13), `orientation`/`rotation` from the stock
  yaw/roll, and a `port` endpoint to CAMSS CSIPHY4 / CSIPHY5 with the stock `data-lanes` and `link-frequencies`.
- Enable `&camss` with the two CSIPHY ports; camcc; the camera power domain. Stock power-domain and interconnect
  values only.
- The EEPROM as `at24` nodes (read-only, `read-only;`) at the stock addresses; the actuator node once its IC is known.

**C2. Sensor drivers (M; the hardest part).** Write `drivers/media/i2c/sc1320cs.c` and `sc820cs.c` as V4L2 subdev
drivers in the style of the upstream SmartSens / OmniVision / GalaxyCore raw-Bayer drivers:
- the chip-ID check;
- power on/off with the stock sequence;
- one mode each to start (the stock full- or binned-resolution 30 fps RAW10), using the captured register tables;
- exposure, analogue/digital gain, vblank/hblank, flip, and a **test pattern**;
- `link-frequency` and `pixel-rate` from stock.
Other modes come later. The register tables stay in the driver as data derived from our own capture of the device's
behaviour, with the source noted.

**C3. First light (PC kits, judged from files).**
1. Probe: the chip ID is read over I2C, both sensors bind, and `media-ctl -p` shows sensor → CSIPHY → CSID →
   VFE-RDI.
2. **Test pattern first:** capture raw frames with `v4l2-ctl`/`yavta` from the RDI video node. A correct pattern
   proves the CSI lanes, link frequency and CAMSS without any image-quality question.
3. A real frame: raw10 dumped and converted on the PC (a debayer script), checking exposure and orientation.
4. Frame-rate and stability: 5 min of streaming, no CSID errors or SMMU faults; power off and on repeatedly.

**C4. Focus and calibration (M+PC).**
- The actuator: a V4L2 VCM driver for the stock IC (many are already upstream, e.g. the dw9714/ak7375 families;
  pick by the IC found in C0), exposed as `V4L2_CID_FOCUS_ABSOLUTE`.
- The EEPROM/OTP read via nvmem: module ID, AWB and lens-shading calibration, AF calibration. It feeds the libcamera
  tuning file.

**C5. Userspace (PC, on the Fedora rootfs).**
- libcamera's **simple pipeline handler with the software ISP** (the path the Snapdragon X laptops use with CAMSS):
  `cam -l`, `cam -c1 --capture`, `qcam`;
- a libcamera tuning file per sensor, built from the stock `tuned`/`awb_parameter` data and the EEPROM calibration
  (rule 13: AWB, colour matrix and black level from stock), not from generic defaults;
- the PipeWire camera portal, so **GNOME Snapshot** and Firefox WebRTC work;
- the orientation reported correctly for the tablet's landscape layout.

**C6. Later / optional.** PDAF (rear), more modes (4K video, high fps), GPU-assisted software ISP performance, and the
flash LED (0031) linked to the rear sensor as a V4L2 flash subdevice. Qualcomm's hardware ISP (IPE/BPS/`CAMERA_ICP`)
stays out of scope: there's no mainline support.

## 3. Risks and effort
- **Register tables** are the key risk. If `sensormodule.bin` resists parsing, the LineageOS I2C trace gives the
  sequence anyway, but only for the modes the stock app uses.
- There's no datasheet, so gain/exposure register semantics are inferred from the traces (vary exposure in the stock
  app and diff the writes).
- Image quality will be below stock (software ISP, basic tuning). Video calls and snapshots are the realistic target.
- Effort: C0–C3 is days to a couple of weeks; C4–C5 adds a similar amount.

## 4. Exit criteria
Both cameras stream in GNOME Snapshot and Firefox at a usable resolution and 30 fps; the rear camera has working
autofocus; colours use the stock-derived tuning; there are no faults over 5 min; the cameras power off when unused
(no s2idle blocker).

# 02 - The hardware as Linux sees it

State: 2 Oct 2026, about 22:30. Kernel queue 0001-0174 (`iceland-linux` a88cf03, head "Input: nt36536: do not log the
panel wait deferral as an error"). Main sources:
`iceland-mainline/docs/reference/pad4-hardware-boot-partitions.md` (28 Sep), the hardware inventory
`~/mainline/build/wf/hwinv/INVENTORY.md` (112 rows, tablet run area-combo-70), the stock-values audit
`wf/audit/REPORT.md`, `docs/FEATURES.md`, `docs/BOOT-LOG-PLAN.md`, `docs/KNOWLEDGE.md` section 4.

**How to read the status column.**

| Status | Meaning |
|---|---|
| **proven** | seen working on the tablet; the run is named |
| **bound** | a driver binds, but no test has shown the function |
| **queued, needs owner** | the driver is in the queue and proven without the accessory; one hand test remains |
| **not described** | the hardware exists, but our device tree has no node for it |
| **no mainline driver** | no mainline driver exists |
| **absent** | the part is not fitted on this tablet |

Where a value comes from stock, the stock source is the Pad 4's own device tree, firmware or Android logs, as
recorded in `docs/device-facts/` (the raw stock trees themselves are private and not in the repositories).

## 1. Identity

| Item | Value | Source |
|---|---|---|
| Model / codename | OnePlus Pad 4, OPD2514, `iceland` (the codename is shared with the Pad 3 Pro and an OPPO Pad 5 Pro family) | reference doc section 1 |
| Board variant | project 25978, "iceland-O IN" overlay (the IN battery-gauge variant) | ABL command line (device-facts) |
| SoC | SM8850P "CanoeP", soc_id 661, revision 2.0; Linux compatible `qcom,kaanapali`; ABL / fastboot product `canoe` | socinfo (queue 0069 names it SM8850P), `fastboot getvar product` |
| Stock software | OxygenOS 11.A.38 (Android 16, Google GKI 6.12.58 + 594 vendor modules). The test tablet runs LineageOS 24.0 (unofficial, slot b) between tests | reference doc section 7 |
| Boot loader | Qualcomm ABL (OnePlus build), A/B, boot image header v4, AVB 1.3, unlocked ("orange") | `fastboot getvar`, device-facts |

## 2. The SoC blocks

The kernel is mainline v7.3-rc4. On top of it come the **infiniti series** (138 patches, the OnePlus 15 port of the
same SoC, `patches/0001-infiniti/`: Kaanapali clocks fixes, GPU, Iris, CAMSS, QCE, DP, ADC5 Gen4, WCN7860, the
OnePlus charger variant of `qcom_battmgr`) and the **Pad 4 series** (`patches/0002-iceland/0001-0174`). "Base"
below means mainline + infiniti; a number is a Pad 4 queue patch.

| Block | Linux driver (DT node) | Source | Status (evidence) |
|---|---|---|---|
| CPUs: 8 Qualcomm Oryon cores; cluster 0 = CPUs 0-5 (0.384-3.629 GHz), cluster 1 = CPUs 6-7 (0.768-4.397 GHz) | `scmi-cpufreq` over the CPUCP firmware (2 SCMI performance domains), schedutil | base; stock capacities 799 / 1024 and energy model 0055 | **proven** (area-combo-11, hwinv R70). Stock's top steps 4.5 / 4.6 GHz are accepted but not granted by the firmware (area-combo-14) |
| CPU idle, cluster low-power modes | PSCI cpuidle (WFI, cpu-sleep-0, cluster states) | base | **proven**: s2idle; CX collapse in 98 % of a 150 s sleep (area-combo-64) |
| GPU: Adreno 840 (gen8 "gen80200"), 18 MiB GMEM, 160 MHz-1.2 GHz in 18 levels | `msm` (a6xx/a8xx family), GMU, GPU SMMU | base + 0011 (GMU address), 0054 (stock levels), 0144-0149 (upstream A8x GMU / RPMh vote fixes) | **proven**: Mesa freedreno OpenGL ES 3.2 / OpenGL 4.6, turnip Vulkan 1.4; dEQP and WebGL results in FEATURES (area-graphics-1..3) |
| Video: Iris VPU 4.0 | `qcom-iris` (`/dev/video0` decoder, `/dev/video1` encoder) | base + 0062 (DT enable) + 0157-0160 (upstream fixes) | **proven**: H.264 / HEVC / VP9 (incl. 10-bit) / AV1 decode bit-exact, H.264 / HEVC encode (results-video-2, area-combo-6) |
| Display: MDSS 13.0 / DPU, UBWC 6.0, 2 x DSI + 2 x DSI PHY, DSC 1.2 | `msm` DPU + DSI | base + 0001, 0006, 0025-0027, 0035, 0058, 0060, 0114, 0138, 0151 | **proven** at 30 / 60 / 90 / 120 / 144 Hz (area-display-7) |
| DisplayPort over USB-C (QMP combo PHY) | `msm` DP | base + 0133-0134 | **bound** (DP-1 "disconnected", DP audio joins the sound card, area-combo-73/-78); never tried with a monitor |
| Camera subsystem: CAMSS (CSID / VFE Gen4), CSIPHY 4 and 5 | `qcom-camss`, `phy-qcom-mipi-csi2` | base + 0073, 0128 | **proven** with both sensors (area-combo-46, -50, -52). Loaded on demand (udev coldplug); the hardware ISP (ICP / IPE / JPEG) has **no mainline driver**: libcamera's software ISP is used instead |
| Hexagon ADSP (audio, sensor hub, FastRPC) | `qcom_q6v5_pas` + GPR / APM / PRM, FastRPC | base + 0018, 0061, 0170 (stock's 12 MiB FastRPC heap) | **proven** (sound, sensors). Started after its firmware is reachable (section 8) |
| Hexagon CDSP (NPU) | `qcom_q6v5_pas`, FastRPC on the CDSP | base + 0117-0124 (cooling over QMI TMD) | **proven**: unsigned test programs and the tablet's NPU runtime library load (area-combo-1/-2); cooling (area-combo-75). **Do not stop it** at run time: a stop leaves its CX vote behind until the next reboot (area-combo-66/-67) |
| SoCCP (charger and USB-PD co-processor) | `qcom_q6v5_pas` in attach mode (started by the boot chain) | base | **proven** (attached; pmic_glink channels) |
| SPSS (secure processor) | - | **no mainline driver** | offline on stock too; it is the reason the deepest sleep state (AOSS sleep) is out of reach (wf/deepsleep) |
| Modem / GNSS | - | **absent** on SM8850P | - |
| PCIe0 (to the Wi-Fi chip, Gen3 x2) | `pcie-qcom`, `pci-pwrctrl-pwrseq` | base + 0040 (WAKE# polarity), 0113 (no hot-plug slot bit) | **proven**; the link goes down in sleep since 0113. Open: "Timeout waiting for L2 entry" at every suspend (BOOT-LOG-PLAN P1-d). Diagnosis (wf/bootfix topic A): without wake-on-WLAN, ath12k's suspend resets the WLAN SoC, and the reset chip never answers PME_Turn_Off; the controller logs the timeout and continues, and ath12k reloads its firmware on resume. Stock keeps the WLAN firmware alive. Test-only kit run 97 is running. The 14 probe deferrals are the power-control driver waiting for `pci-pwrctrl-pwrseq` |
| USB: DWC3 dual-role, M31 eUSB2 PHY, eUSB2 repeater (in PMIH0108), QMP USB3-DP combo PHY | `dwc3-qcom`, `phy-qcom-m31-eusb2`, `phy-qcom-eusb2-repeater`, `phy-qcom-qmp-combo` | base + 0063 / 0065 (CPU-latency hold while USB is up), 0109-0112 (stock repeater tuning), 0153-0154, 0162 (f_ncm flush retry) | **proven** in device mode (the test link, USB 2 speed). Host mode works by design (UCSI role switch) but is untested with an accessory |
| UFS 4.0 host + QMP UFS PHY + inline crypto | `ufs-qcom`, `phy-qcom-qmp-ufs`, `qcom-ice` | base + 0099 (stock UFS PHY supply), 0171 (MCQ, multi-queue) | **proven** (read-only use; HS-G5 x2). MCQ since 0171: 9 queues, a 256 MiB direct read at 2.3 GB/s (area-combo-96) |
| RPMh (RSC, power domains, regulators, BCM) | `qcom_rpmh`, `rpmhpd`, `qcom-rpmh-regulator` | base + 0084-0085 (PMH0101 level shifters) | **proven**. Mainline sends only active-set votes: a vote Linux holds stays in force while the SoC sleeps (wf/audit, wf/deepsleep) |
| AOSS / AOP, PDC, IPCC, SMP2P, SMEM | `qcom_aoss`, `qcom-pdc`, `qcom-ipcc`, `smp2p`, `smem` | base | **proven** (remote processors, wake interrupts) |
| Sleep statistics | `qcom_stats` (RPMh stats) | base | **bound** on demand; used by the deep-sleep tests |
| SMEM DRAM information (872-byte layout) | `qcom_smem` | 0172 (backport of the upstream Glymur DRAM-info support, author kept), 0173 (a 32-bit overflow fix) | **proven**: the DRAM frequency plan is parsed (area-combo-96). Its highest-bank-bit field is 0, so the UBWC table value 16 stays in use, which is stock's value too |
| Temperature sensors: 7 x TSENS v2 | `qcom-tsens` | base + 0156 (trip clamp widened so stock's 125 C trips are programmed as they are) | **proven** |
| Interconnects (13 NoCs) | `qcom` icc-rpmh | base | **proven**. Boot votes are released only at the deferred-probe timeout, because the GPU's GMU node never gets a driver of its own: `CONFIG_FW_DEVLINK_SYNC_STATE_TIMEOUT=y` (0125-0138 config) |
| LLCC system cache + EDAC | `llcc-qcom`, `qcom_edac` | base, `EDAC_QCOM=m` | **bound** |
| Bandwidth monitors: 2 x bwmon4 (CPU / LLCC), bwmon5 (DDR) | `qcom-bwmon` | base + 0125-0126 (Kaanapali bwmon5) | **proven** (132 updates, area-combo-78) |
| Crypto engine (QCE + BAM) | `qce` (auxiliary bus) | base | **bound** (loaded on demand) |
| TRNG, QFPROM fuses, IMEM / SCMI shared memory | `qcom-rng`, `qfprom`, `sram` | base, `CONFIG_SRAM=y` | **bound** |
| Watchdog (APSS WDT, emulated by the Gunyah hypervisor) | `qcom-wdt` | base, `WATCHDOG_SYSFS=y` | **bound** (the kits pet it) |
| TrustZone interfaces | `qcom_scm`, QTEE (`qcomtee`) | base | SCM **proven**; QSEECOM-style trusted apps have **no mainline driver** |
| CoreSight trace, EUD, EVA / CVP engine | - | not described / no driver | debug-only or disabled on stock too |

## 3. The board

| Part | Bus / address (Linux view) | Driver | Source | Status (evidence) |
|---|---|---|---|---|
| Panel: CSOT XN251 LCD, 13.2", **3392x2400** landscape-native, two DSI links of 1696x2400, DSC, video mode | DSI0 + DSI1 | `panel-novatek-nt36536` (upstream driver + Pad 4 mode) | 0002, 0007, 0103 (stock 144 Hz porch), 0108 (stock reset sequence) | **proven** 30-144 Hz |
| Backlight: 2 x Kinetic KTZ8869 (master + slave, shared enable line on TLMM 1) | I2C 0x11 on two buses | `ktz8869_iceland` | 0004-0005, 0024, 0102, 0168 (I/O supply optional, as stock has none); `CONFIG_GPIO_SHARED_PROXY=y` | **proven** (2..4095; stock's normal range ends at 3542, above is its sunlight boost: an owner decision, wf/audit) |
| Touch + active pen: Novatek NT36536 TDDI (no flash: firmware loaded into its SRAM at every probe) | SPI (QUP4) + TLMM 158 | `nt36536` touch driver | 0009-0010, 0036-0037, 0174 (the panel-wait deferral no longer logged as an error) | **proven** touch; pen working per the owner, little tested |
| Pen wireless charger: Maxic MT5806 + an hBoost in PMIH0108 | I2C 0x2b behind PMH0101 level shifters 3 / 4 | `mt5806_pen_charger` + pmic_glink hBoost client | 0090-0093 | **queued, needs owner**: proven without a pen (area-combo-47/-49); one 90 s pen session remains |
| Pogo keyboard cover (private protocol, one data line, 921600 baud) | GENI UART QUP3 SE4 (`1990000`; BT is `1994000`) | `oneplus-pogo-keyboard` (serdev) | 0094-0097 | **queued, needs owner**: proven without a cover (area-combo-49/-52) |
| Speakers: 6 x NXP TFA9865 on TDM (8 x 32 bit, 48 kHz) | I2C 0x34 / 0x36 / 0x37 on two buses | `tfa9865` (simple driver) + AudioReach TDM | 0014-0015, 0038-0051, 0104 | **proven** (all six, stereo); volume capped at -12 dB because speaker protection has **no mainline driver** |
| Codec: Qualcomm WCD9395 (SoundWire RX / TX) + USB-SS audio switch | SoundWire; switch at I2C 0x0e | `wcd939x`, `wcd939x-usbss` | base + 0052, 0059, 0107, 0169 (VA macro DMIC rate) | **proven** microphones; analog USB-C headset untested |
| Microphones (2) | WCD9395 TX path | UCM profile (+12 dB as stock's DSP adds) | `audio/ucm/` | **proven** (area-combo-1..3) |
| Rear camera: SmartSens SC1320CS 13 MP; front: SC820CS 8 MP | GENI I2C bus `884000` (stock uses this bus, not CCI): rear 0x36, front 0x10 | a **private** sensor driver (built from a trace of stock; not in the queue) | DT 0073, 0086 | **proven** at 30 fps (area-combo-46/-50/-52) |
| Camera bus level shifters (PMH0101 LS1B / LS2B, RPMh XOB resources) | RPMh | `qcom-rpmh-regulator` | 0084-0086 | **proven**: without them the bus only worked while the sensor hub streamed |
| Focus motor: Dongwoon DW9800K | I2C 0x0c | `dw9719` (+ I/O supply) | 0087-0089 | **proven**; held at stock's start position (no autofocus in libcamera's simple pipeline) |
| Camera EEPROMs (OTP data) | I2C rear 0x58, front 0x51 | `at24` (+ I/O supply) | 0129-0131 | **proven** readable (4096 B, area-combo-78); unused by libcamera |
| Rear flash: PMH0101 flash LED, two dies | SPMI | `leds-qcom-flash` | 0031 | **proven** as torch (one node lights the scene) |
| Sensors: Bosch BMI3x0 accel / gyro, AKM AK0991x magnetometer, Sensortek STK36C01 light / RGB / proximity, ROHM BU52053NVX hall | all behind the **ADSP sensor hub** (SSC) | user space: `hexagonrpcd` + `libssc` + `iio-sensor-proxy` 3.9 | packaging/sensors | **proven** accel / compass / light / proximity (area-combo-23/-26); gyro and RGB offered by the hub but unused |
| Hall / lid switch | TLMM 98, active low | `gpio-keys` SW_LID | 0030, 0115-0116 | **proven** (cover wake from sleep since 0116) |
| Keys | power = PMK8850 PON; volume up = PON RESIN; volume down = PMH0101 GPIO 6 via gpio-keys (hwinv J02) | `pm8941-pwrkey`, `gpio-keys` | base | **proven** |
| Wi-Fi 7: Qualcomm WCN7860 "peach" hw2.0 (PCIe 17cb:110e), board_id 0xff | PCIe0 + the WCN power sequencer | `ath12k` (module, loaded late) | base + 0066-0068 (no SBS, as stock's `enable_sbs=0`), 0082, 0139-0143, 0167 (the power sequencer's inputs as stock: L2G 1.8 V now voted) | **proven** 2.4 GHz connect; 5 GHz found; country setting fails (BOOT-LOG-PLAN P1-c) |
| Bluetooth (same chip) | GENI UART `1994000`, 3.2 Mbaud | `hci_uart` + `btqca` | base | **proven** incl. pairing; the address comes from a file written at install (`iceland-bdaddr`) |
| Battery + charger: 13,380 mAh design (about 13,786 mAh full measured), charger firmware on the SoCCP | pmic_glink (`oneplus,iceland-pmic-glink`), UCSI | `qcom_battmgr` (OnePlus variant), `ucsi_glink` | base + 0013, 0028-0029, 0039, 0053, 0057, 0071-0072, 0074, 0078-0080, 0098, 0137 | **proven** on the PC port: stock's charging steps, the charge limit, the time estimate; wall chargers need one owner session |
| Fast-charge pumps (2 x SC8547D), battery authentication (Maxim 1-wire) | I2C / GPIO 88 | - | - | **no mainline driver** (OnePlus-proprietary; fast charging not planned) |
| Haptics, NFC, fingerprint, IR, FM, SD slot, RGB LED | - | - | - | **absent** (hwinv section K-M) |

## 4. Power: PMICs, rails, protection

**PMICs on SPMI** (reference doc 6.10, hwinv B01-B06):

| PMIC (SPMI SID) | Linux uses it for |
|---|---|
| PMK8850 (0) | power key / RESIN, RTC (alarm wake), ADC5 Gen4 thermistors, SDAM (reboot reason), **power telemetry** (0163-0166: per-rail energy and power of 7 bucks: CPU clusters, GPU, NPU, MXC, CX, MMCX) |
| PMH0101 (1) | LDOs / bucks via RPMh, temperature alarm, BCL, flash LED, level shifters LS1-LS4 (camera and pen-charger I2C) |
| PMH0110 x 4 (3 / 5 / 6 / 8, rails `_d`, `_f`, `_g`, `_i`) | regulators, GPIOs, temperature alarms (cooling maps 0081-0083) |
| PMH0104 (9) | regulators `_j`, temperature alarm |
| PMIH0108 (7) | eUSB2 repeater, BCL, the second temperature alarm (0127), the hBoost for the pen charger |
| PMD8028, PMR735D, PM8010 x 2 | reference-board PMICs in stock's tree, **not fitted** |

**Rails the audit set to stock** (wf/audit, queued 0099-0101, proven in area-combo-50/-52/-58):

| Rail | Consumer | Value now | Stock |
|---|---|---|---|
| L4G | UFS PHY core supply | 0.912 V fixed | 0.912 V |
| L12B | panel I/O | 1.896 V fixed (the regulator step nearest 1.9 V that does not exceed it) | 1.9 V |
| BOB1 | microphone bias; input of the 2.8-3.1 V LDOs | at least 3.288 V (32 mV steps from 3.0 V) | 3.296 V vote |
| BOB2 | - | 3.000 V (mainline's table starts there; inside stock's range) | 2.720 V vote |
| L1D 1.2 V, L3D 0.88 V | DSI / PHY supplies | held while used (stock votes them off in its sleep set; mainline cannot express "on awake, off asleep", so "always on" was rejected) | - |

**Battery and charging protection.**

| Layer | What it does | Source |
|---|---|---|
| Charger firmware on the SoCCP | runs the charge cycle | stock firmware |
| Kernel (`qcom_battmgr` OnePlus variant) | stock's input-current steps (AICL), per-charger-type limits, the charge limit (start 80 % / end 85 %) | 0074, 0078-0080 |
| Kernel BCL | low-battery current limiting: three alarm levels per PMIC plus a "nearly empty" sensor as thermal zones with stock's GPU / CPU caps | 0075-0076 |
| Device package battery guard | stock's JEITA regions, voltages and currents, three USB-C connector temperature sensors; power-off at 70 C (stock framework) / 77 C | iceland-device |
| Device package thermal policy | the charge-current cap from stock's skin gears | `iceland-thermal` |

Every limit is stock's or lower: the audit found nothing above stock in the charger tables.

**Thermal design** (FEATURES "Thermal", proven in area-combo-38..41, -75):

| Zone | Trips and actions |
|---|---|
| CPU | passive 105 C, then 112 / 114 C (stock), critical 125 C. Fix 0077: the step-wise governor no longer keeps a stale limit |
| GPU | a 105 C loop stepping 1200 -> 160 MHz, power-off at 125 C (stock's thermal service does the same) |
| Skin (a fast hot spot) | 48 C throttle, 51 C deepest gear, 70 C off. Stock uses 60 / 61 C together with a shell-temperature policy (the device package's daemon); which to use is the owner's choice |
| XO | stock's 78 / 80 / 90 C steps |
| PMIC alarms | 95 C: GPU from 826 MHz down, each CPU group to its lowest speed (0081-0083) |
| Board / flash thermistors, three USB-C connector thermistors | ADC5 Gen4 channels (all present, area-combo-70) |
| NPU (CDSP) | cooling over QMI TMD with stock's three maps (0117-0124) |

## 5. Memory and storage

| Item | Value | Source / evidence |
|---|---|---|
| RAM | **12 GB**. ABL passes 20 memory segments (11.50 GiB usable; one segment has size 0: never boot a DT without ABL's real `/memory`); GNOME shows 11.1 GiB | `ddr_info=6\|8\|1\|5\|12` on the stock command line; KNOWLEDGE section 4. DDR type code 8 in stock's tree, LPDDR5 in mainline's SMEM naming (offline analysis, not verified on the tablet) |
| Reserved memory | 68 stock reserved-memory nodes; key ones in KNOWLEDGE section 4 (splash 0xfc800000, the hypervisor's regions) | device-facts |
| Storage | UFS 4.0, Samsung KLUEG4RHKF (256 GB class), HS-G5 x 2 lanes, **6 LUNs** (sda-sdf), **4096-byte logical blocks** on every LUN | U-Boot run 4; area-combo-45 kernel log (`61853696 4096-byte logical blocks`) |
| LUN order | can change between boots: always address partitions by GPT name (partlabel) | KNOWLEDGE section 12 |

The 4 KiB block size matters for any disk image you write: a stock distribution image laid out for 512-byte
sectors does not boot as it is (`03-BOOT-AND-PARTITIONS.md` section 4).

## 6. Partitions (generic layout)

151 partitions on 6 LUNs. Sizes are the model's layout (identical on every Pad 4 with this firmware); they come from
the partition listing of the owner's backup and the LineageOS capture. No GUIDs or device-unique values here.
**Written by our plan** marks the only two partitions the install ever writes. Everything else is never written.

| LUN (size) | Partitions | Role | Linux / our plan |
|---|---|---|---|
| sda (~253 GB, the user LUN) | `ssd`, `persist` (128 MiB), `misc`, `keystore`, `frp`, `vbmeta_system_a/_b`, `vbmeta_vendor_a/_b`, `metadata` (64 MiB), `rawdump`, `splash_odm`, `hybridswap`, `super` (14.6 GB: Android's dynamic system, vendor, odm partitions), `userdata` (237,159,641,088 bytes, the last partition) | Android data and system; per-device calibration in `persist` | `persist`, `super` (vendor / odm inside) are **read** once for firmware and sensor data. **`userdata` is written by our plan** (write 1: the Fedora disk image) |
| sdb / sdc (8 MiB each) | `xbl`, `xbl_config`, `tme_*`, `multiimg*`, `apdp` (slot a on sdb, slot b on sdc) | primary boot loader set | never touched |
| sdd (12 MiB) | `cdt`, `ddr` (DDR training), `engineering_cdt_a/_b`, `ocdt`, `dinfo` | per-device configuration | never touched |
| sde (~2 GB, A/B firmware and boot set) | per slot: `uefi`, `abl`, `aop*`, `tz*`, `hyp*`, `devcfg`, `qupfw`, `shrm`, `cpucp*`, `keymaster`, `modem` (FAT: ADSP / CDSP / Wi-Fi firmware), `bluetooth` (FAT), `dsp` (ext4: DSP libraries), `soccp*`, `boot` (96 MiB), `init_boot` (8 MiB), `vendor_boot` (96 MiB), `dtbo` (24 MiB), `vbmeta` (64 KiB), `recovery` (100 MiB), `pvmfw`, ...; singletons: **`efisp` (3 MiB)**, `devinfo` (unlock state), `storsec`, `uefivarstore`, `secdata`, `logfs`, `toolsfv`, ... | the firmware chain and Android's boot set | `modem_a`, `bluetooth_a`, `dsp_a` are **read** for firmware. **One boot partition of the active slot (`boot_b` today) is written by our plan** (write 2: U-Boot) |
| sdf (~461 MB) | `oplusreserve1/2/3/5`, `nonmodemst1/2`, `DRIVER`, `ompdt` | OnePlus reserve, per-device data | never touched |

**A/B.** The firmware and boot partitions come in `_a` / `_b` pairs. ABL boots the active slot (`b` on the test
tablet) and keeps per-slot flags: `slot-successful`, `slot-retry-count`, `slot-unbootable`. Both slots hold the
same 11.A.38 firmware since LineageOS's `copy-partitions` step on 28 Sep. **Anti-rollback:** firmware older than
11.A.38 must never be flashed or booted.

**`efisp`.** A 3 MiB singleton partition on LUN 4 (sde).
- By its name it is an *EFI System Partition*, and it sits among the firmware partitions. On Qualcomm platforms it
  belongs to the boot firmware's own UEFI stage (`uefi_a/_b`, which runs before ABL), not to Android. Android does
  not mount it.
- The project has never inspected its contents (an open read-only check, `07-INSTALL-REVIEW.md` R-7).
- **Our plan does not use it:** it is on the never-write list with the rest of the firmware.
  - Its 3 MiB is too small for shim, GRUB and a device tree (several MB together).
  - It has no A/B pair.
  - It is not ours.
- Our EFI System Partition is a FAT32 partition **inside the Fedora disk image** in `userdata`, rebuilt with 4096-byte
  sectors by the image builder. U-Boot reaches it through a block map of `userdata` (`03-BOOT-AND-PARTITIONS.md`
  section 4).
- One side effect to know: U-Boot's EFI boot manager sees every UFS partition, `efisp` included, before the Fedora
  disk. That is why the review suggests an explicit boot option.

## 7. Firmware: what the kernel loads and where it comes from

Linux needs the tablet's own signed firmware. **It is never distributed**: every user extracts it from their own
tablet, read-only. Names below are the ones the device tree's `firmware-name` properties and the mainline drivers
ask for (the board DT uses the prefix `qcom/kaanapali/iceland/`; `firmware/manifest.tsv` and the 28 Sep reference
still say `qcom/kaanapali/OnePlus/iceland/`, which is stale).

| Linux path (under `/lib/firmware`) | Taken from (partition: path) | Notes |
|---|---|---|
| `qcom/gen80200_sqe.fw`, `qcom/gen80200_gmu.bin`, `qcom/gen80200_aqe.fw` | the kits: upstream linux-firmware (GMU v5.3.23). The tablet's `vendor` partition has its own copies (GMU v5.3.39, proven in pc-010 / pc-012) | **Decided by the owner (2 Oct): linux-firmware's set (v5.3.23) goes into the installed image**, as in every kit since pc-024. Fedora ships it xz-compressed (hence `FW_LOADER_COMPRESS_XZ`) |
| `qcom/kaanapali/iceland/gen80200_zap.mbn` | `vendor` (in `super`): `/firmware/` | signed per device family; the GPU's secure mode needs it |
| `qcom/kaanapali/iceland/vpu40_2v.mbn` | `vendor`: `/firmware/` | Iris video |
| `qcom/kaanapali/iceland/adsp.mbn`, `adsp_dtb.mbn` | `modem_a` (FAT): `/image/adsp.mdt` + `.bNN` | split images squashed into one `.mbn` |
| `qcom/kaanapali/iceland/cdsp.mbn`, `cdsp_dtb.mbn` | `modem_a`: `/image/cdsp.mdt` + `.bNN` | NPU |
| `ath12k/WCN7860/hw2.0/amss.bin`, `m3.bin`, `aux_ucode.bin`, `qdss.cfg` | `modem_a`: `/image/peach/` (`amss20.bin`, `phy_ucode20.elf`, `aux_ucode20.elf`, `qdss_trace_config_v2.cfg`) | `qdss.cfg` is required: the chip waits for it |
| `ath12k/WCN7860/hw2.0/board.bin`, `regdb.bin` | `odm` (in `super`): `/etc/wifi/peach/bdwlan.elf`, `regdb.bin` | board_id 0xff |
| `qca/brhbtfw20.mbn`, `qca/brhbtnv20.*` | `bluetooth_a` (FAT): `/image/` | not the `gngbt*` names other lists use |
| `novatek/novatek_nt36536_fw.bin` | `odm`: `/firmware/tp/25926/FW_NT36536_HUAXING.img` | header stripped (`firmware/convert-nt36536.py`) |
| `qcom/kaanapali/OnePlus-Pad4-tplg.bin` | built from source (AudioReach m4 + our overlay) | public, shipped in the device package |
| sensor hub tree (`/usr/share/qcom/kaanapali/OnePlus/iceland/`) | `dsp_a`, vendor sensor configs, `persist` sensor registry, odm sensor configs | served to the ADSP by `hexagonrpcd`; private |
| `soccp` | already running from the boot chain; Linux only attaches | no file needed |

**Tools.**
- `iceland-fw-extract`: the install workflow's on-device extractor, `wf/install/cand/fwx/` with its list
  `fw-list.tsv`. It sets each source partition read-only before opening it. Checked on the owner's backup: 23 of 23
  items, 627 files identical to what the kits load.
- `tools/linux-ram/fw-extract.sh`: the older busybox version for the RAM kits.

## 8. Built in or module, and what must be in the initramfs

From `docs/BOOT-LOG-PLAN.md` (boot logs of area-combo-92 / -93) and `configs/distro-neutral.config`:

- **Built in:** what is needed before the root file system exists.
  - clocks, power domains, RPMh, interconnects, pinctrl, regulators, the SMMU;
  - UFS and its PHY, the block layer, ext4 / btrfs / vfat;
  - the early framebuffer (`simpledrm`) and the panel / backlight path (`DRM_MSM=y`, `DRM_PANEL_NOVATEK_NT36536=y`,
    `BACKLIGHT_KTZ8869_ICELAND=y`, `GPIO_SHARED_PROXY=y`);
  - pmic_glink;
  - the pogo keyboard;
  - EFI stub support;
  - for the rehearsal: the USB gadget and NBD.
- **Modules,** loaded by udev from their aliases: everything that needs firmware from the root file system (the
  remote processors, GPU microcode users, Wi-Fi, Bluetooth, video, cameras, audio), plus drivers that are only useful
  on demand (crypto, CAMSS, telemetry).
  - Built in, they would probe before the firmware is reachable and fail. `remoteproc` does not retry: "Direct
    firmware load ... failed with error -2" for `adsp.mdt` / `cdsp.mdt` at 19 s (BOOT-LOG-PLAN P1-a).
  - Modules also keep the kernel usable by any distribution and allow reloading in tests.
- **The rule for an initramfs:** either keep `qcom_q6v5_pas` (and other firmware users) out of it, so that they load
  after `switch_root` when `/lib/firmware` is the real one, or put their firmware into the initramfs too. Without
  the ADSP there is no sound and no sensors. The battery does **not** depend on it: its data travels over the SoCCP's
  pmic_glink channel (`PMIC_RTR_SOCCP_APPS`, hwinv O03), and the kits read the battery at 30 s while the ADSP was
  still offline (BOOT-LOG-PLAN P1-a, corrected 2 Oct).
- **The install's answer** (wf/install round 6, not yet run on the tablet):
  - dracut `omit_drivers` for the drivers that need root firmware (the remote processors, ath10k / 11k / 12k,
    Iris / Venus, Bluetooth UART);
  - `add_drivers` for `pwrseq_qcom_wcn` and `pci_pwrctrl_pwrseq` (ends the PCIe probe deferrals early);
  - the GPU microcode trio (`gen80200_sqe` / `gmu` / `aqe`, linux-firmware's set by the owner's decision) in the
    initramfs. MSM is built in and loads it when it binds; the first golden image lacked it (finding B4).
  - Acceptance lines `adsp`, `cdsp`, `fwload`, `gpu`, `pcieprobe` check all of it.
- **Kit vs installed boot.** The RAM kits unpack the module tree after boot and load an early list. Since 2 Oct they
  also re-trigger udev for driverless devices ("coldplug"), as an installed boot does. Without that, the sound card
  waited for the DP audio codec and never appeared (runs 83 / 87).

## 9. Hardware inventory summary

`wf/hwinv/INVENTORY.md` compares 112 hardware blocks from stock's device tree, modules and logs with what mainline
binds (tablet run area-combo-70, before the quick wins):

| Status | Rows |
|---|---|
| working | 52 |
| bound, not proven | 11 |
| bound, not needed | 1 |
| described, not bound | 6 |
| disabled in our DT | 2 |
| not described | 12 |
| no mainline driver | 14 |
| not on this tablet | 13 |

The quick-wins workflow then closed several gaps (queue 0125-0138, area-combo-78: 16 of 16): bwmon5, the second
PMIH0108 temperature alarm, the camera EEPROMs, the charger log on the SoCCP channel, IMEM / SRAM, EDAC, the
watchdog in sysfs, DisplayPort and DP audio, the unused WSA audio macros switched off, and autoload of QCE / CAMSS /
`qcom_stats`.

The blocks without a mainline driver are:
- speaker protection;
- fast charging and the battery authentication IC;
- the hardware camera ISP and the EVA engine;
- the secure processor (SPSS);
- vendor display extras;
- Gunyah VM services;
- some ADSP channels (BT SoundWire offload, MHI satellite, sleep monitor);
- vendor DCVS.

Every unbound device on the running tablet is explained in the inventory.

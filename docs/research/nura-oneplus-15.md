# Nura wiki: OnePlus 15 (oneplus-infiniti), with what it means for the Pad 4

**Source:** https://wiki.nura.eco/wiki/OnePlus_15_(oneplus-infiniti), revision 107471, last edited 2026-09-27 18:42.
The cloud container is blocked from wiki.nura.eco, so the text comes from a page saved by the user on 2026-09-28.
Wiki content is licensed [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Credits on the page:
postmarketOS mainlining by idusergod and FantomTchi7 (Telegram), UEFI by [robotix](https://github.com/Robotix22).

Part 1 is the page content, restructured into tables. Part 2 maps every item to the Pad 4 and our plan. Part 3 is the
action list.

## Part 1 — Page content

**Status banner:** tested with Nura, but the device package is not in the Nura repositories yet, so it can't be
selected in pmbootstrap.

| Field | Value |
|---|---|
| Codename | `oneplus-infiniti`; models CPH2747 (EU/Global), CPH2745 (India), CPH2749 (USA), PLK110 (China); 2025; handset |
| Chipset | Snapdragon 8 Elite Gen 5 (SM8850-AC). CPU 2× 4.61 GHz Oryon L + 6× 3.63 GHz Oryon M (3rd gen). GPU Adreno 840 |
| Display | 2772x1272 @ 165 Hz, 6.78" LTPO AMOLED |
| Storage / RAM | 256/512/1024 GB UFS 4.1; 12/16 GB LPDDR5X-5333 |
| Software | OxygenOS 16 (shipped and latest); ColorOS optional. FOSS bootloader: yes (Mu-Silicium) |
| Nura | category **testing**; pre-built images **no**; mainline **yes**; pmOS kernel **7.3-rc4** |

**Feature matrix:**

| Group | Feature | Status |
|---|---|---|
| Basics | Flashing (pmbootstrap flasher) | Broken |
| | USB networking | Partial |
| | Internal storage | Works |
| | Battery | Works |
| | Screen | Works |
| | Touchscreen | Works |
| Multimedia | 3D acceleration | Works |
| | Audio | Broken |
| | Camera | Broken |
| | Camera flash | Works |
| | IR TX | Broken |
| Connectivity | Wi-Fi | Works |
| | Bluetooth | Works |
| | GPS | Broken |
| | NFC | Works |
| Modem | Calls, SMS, mobile data | Broken |
| Misc | FDE (unl0kr) | Broken |
| | USB OTG | Partial |
| | HDMI/DP | Broken |
| | Fingerprint | Broken |
| Sensors | Accelerometer, magnetometer, ambient light, proximity, hall, haptics, barometer | all Broken |

**U-Boot:**

| Item | Status |
|---|---|
| Primary bootloader (replace ABL) | Broken |
| Secondary (chainloaded by ABL) | **Works** |
| Mainline U-Boot | Works |
| Boot from internal storage | Partial |
| USB host | Untested |
| USB peripheral | Untested |
| Display | Works |
| Buttons | Untested |

**Owners:** DragonX256 (Global 12/256, primary), FantomTchi7 (16/1024, dual-boot OxygenOS + NixOS), MaxShevPovar
(CN 12/256), Namnam1105 (12/256, about to contribute; NixOS + Android), Pentiumpro, Piecuu, Titago (IN 16/512,
PixelOS 16.2 + NixOS).

**Flash modes** (need an unlocked bootloader):

| Mode | How |
|---|---|
| Recovery | Power + Volume Up, `fastboot reboot recovery` or `adb reboot recovery` |
| FastbootD | no key combination; `fastboot reboot fastboot` or `adb reboot fastboot` |
| Bootloader | Power + Volume Down, `fastboot reboot bootloader` or `adb reboot bootloader` |

The Installation section is empty.

**Component table** (Y works / N doesn't / P partial / ? unclear / blank = no driver yet):

| Component | Model | Compatible | Status | Notes |
|---|---|---|---|---|
| SoC | SM8850-AC (kaanapali) | `qcom,sm8850` | Y | |
| GPU | Adreno 840 | `qcom,adreno-840.0` | Y | |
| UFS | UFS 4.1 PHY | `qcom,kaanapali-qmp-ufs-phy` | Y | |
| PMICs | PM8010 (partial: SID 0xc / "_m" only), PMH0101, PMH0104, PMH0110, PMIH0108, PMK8850, PMR735D | | Y | |
| Battery | 7300 mAh | `oplus,mms_gauge`, `oplus,virtual_gauge` | Y | |
| Charger | VOOC/SuperVOOC | `oplus,adsp-voocphy` | N | |
| Wireless charging | NU1669 Rx | `oplus,rx-nu1669` | – | no upstream driver |
| Wireless-charging alignment | MKH100A magnetic cover/attach | `oplus,magcvr_mkh100a` | – | no upstream driver |
| Power key | PMK8850 PON KPDPWR | `qcom,pmk8350-pwrkey` | Y | |
| Volume down | PMH0101 GPIO 6 | `gpio-keys` | Y | |
| Volume up | PMK8850 PON RESIN | `qcom,pmk8350-pwrkey` | Y | |
| Panel | OnePlus AA601 OLED DSI | `oneplus,aa601-p-7-a0020` | Y | only 2772x1272@165 Hz so far |
| Touch | Synaptics S3910 SPI | `synaptics-s3910` | Y | |
| Fingerprint | optical SPI | `oplus,fp_spi` | – | no upstream driver |
| USB / OTG | USB-C 3.2 (HS/SS PHY + DP QMP PHY) | `qcom,kaanapali-dwc3` | P | USB, OTG and usbnet work **only with external USB-PD power** |
| Wi-Fi / BT | FastConnect 7900, WCN788x (PCIe) | `pci17cb,110e` | Y | |
| Modem | Snapdragon X85 | `qcom,kaanapali-mpss-pas` | P | comes up and sees the SIM; IPA doesn't work |
| NFC | NXP SN220T | `nxp,nxp-nci-i2c` | Y | |
| GNSS | modem QMI location | `qcom,memshare-peripheral` (gps) | N | |
| IR | SPI | `oplus,kookong_ir_spi` | N | |
| Codec | WCD939x (SoundWire) | `qcom,wcd939x-codec` | N | |
| Speaker amps | NXP TFA9874 ×2 (i2c0) | `nxp,tfa9874` | N | |
| Cameras | IMX906 main, OV50D ultra-wide, S5KJN5 tele, IMX709 front | | – | no upstream drivers |
| Flash / torch | PMH0101 flash LED | `qcom,pmh0101-flash-led`, `qcom,spmi-flash-led` | Y | |
| Accel/gyro, baro, compass | | | N | |
| Proximity / ALS | AMS/ScioSense TOF8806 (I2C) | `ams,tof8806` | – | no upstream driver |
| Hall | oplus_magic_buttom (GPIO) | `gpio-keys` | N | |
| Haptics | linear motor | | N | |

**UEFI (Mu-Silicium):**

| Item | Status |
|---|---|
| Display (framebuffer) | Y |
| UFS | Y |
| Side buttons | Y |
| USB host | N |
| USB device | Y |
| USB PD | N |
| Mass storage | Y |
| Direct Linux boot | Y |

**U-Boot components:**

| Item | Status | Notes |
|---|---|---|
| Chainloading | Y | Android boot image chainloaded by ABL; stock bootloader chain untouched |
| Display / console | Y | |
| UFS | P | read-only by design; write and erase compiled out for safety |
| GPT | Y | |
| Linux boot | Y | sysboot/extlinux; NixOS with a raw initrd tested |

**See also:**
- [XEC kernel](https://github.com/Xlie-Electronic-Customs/linux) (the page says 7.2)
- [XEC firmware](https://github.com/Xlie-Electronic-Customs/linux-firmware-oplus-infiniti)
- downstream [kernel](https://github.com/OnePlusOSS/android_kernel_oneplus_sm8850) and
  [modules + DT](https://github.com/OnePlusOSS/android_kernel_modules_and_devicetree_oneplus_sm8850)
- [Mu-Silicium status](https://github.com/Project-Silicium/Mu-Silicium/blob/main/Status.md#oneplus-15)
- [U-Boot (infiniti-mainline)](https://github.com/infiniti-mainline/u-boot)

## Part 2 — What each item means for the Pad 4

The Pad 4 facts below come from our captures and the PC relay results (`relay/results/pc-*`) as of 2026-09-28.

### Platform and boot

| OnePlus 15 item | Pad 4 | Use for us |
|---|---|---|
| U-Boot chainloaded by ABL works; UFS read-only; Linux via extlinux | same design, **verified** on the Pad 4 (diag runs 3–4, Linux tests 2–7b, pc-001..011). We boot Linux through `bootefi` instead of extlinux | Confirms the architecture. The OnePlus 15 route (extlinux) is a simpler fallback if EFI ever gives trouble. |
| U-Boot **USB peripheral: untested**; buttons untested | **USB fastboot in U-Boot works on the Pad 4** (run 4). Buttons untested | Something we could contribute back later (only with the user's OK). Test U-Boot buttons (vol-down = PMH0101 GPIO 6 on both devices). |
| Primary bootloader (replace ABL): broken | not attempted, not planned | Keep ABL stock (a hard rule anyway). |
| Mu-Silicium UEFI: direct Linux boot, USB device, mass storage; no USB host or PD | no Pad 4 port | Fallback only (see research/gts6l-tab-s6.md). **Mass storage** could be useful for recovery or installing later. |
| pmbootstrap flashing broken; no device package; no prebuilt images | we have to write `device-oneplus-iceland` ourselves (Phase 4) | There's no `device-oneplus-infiniti` to copy (checked by the PC through the GitLab API). Base it on the infiniti deviceinfo pattern plus our U-Boot flow, and include the pmbootstrap "flash U-Boot to boot_a + image to userdata" steps ourselves. |
| pmOS kernel 7.3-rc4 | our base is also 7.3-rc4 + infiniti master | Same base, so fixes transfer directly. |
| Flash modes: Power+VolDown = bootloader, Power+VolUp = recovery, FastbootD has no combo | the same OnePlus ABL | Already used in our scripts' recovery hints. |

### PMICs, keys, power

| OnePlus 15 item | Pad 4 (stock DT, capture 2) | Use for us |
|---|---|---|
| PMICs PM8010 (partial, SID 0xc only), PMH0101, PMH0104, PMH0110, PMIH0108, PMK8850, PMR735D | stock DT has pm8010, pmh0101, pmh0104, pmh0110, pmk8850, pmr735d and `pmih010x@7` (PMIH0108 family) | Same PMIC set: infiniti's PMIC DT applies. Watch for the PM8010 "_m only" limit if a camera or other rail comes from PM8010. |
| Power key PON KPDPWR; volume up = PON RESIN | stock `qcom,pmk8350-pwrkey` + `qcom,pmk8350-resin` | Same. |
| Volume down = PMH0101 GPIO 6 (gpio-keys) | stock gpio-keys `volume_down` on PMH0101 GPIO 6 (`0x6ef 0x06`) | Same line. |
| Battery `oplus,mms_gauge`/`virtual_gauge`; charger VOOC `oplus,adsp-voocphy` broken | battery data works over pmic-glink with the OPLUS battmgr (pc-011 D). IN variant: QBG + DS28E30 authenticator | We are at the same level. Fast charging (SuperVOOC) is not expected on mainline; the charge limit and charge control go through battmgr. XEC's "OnePlus PMIC GLINK power supply" + UCSI compatibles (df4c73f22d08, b37305f86536, ba1bfa9fcb74) are the reference if our battmgr variant falls short. |
| USB/OTG only with external USB-PD power | our USB NCM (peripheral) works on battery. Host/OTG not tried | **Expect the same OTG limit** (VBUS/role through pmic-glink/UCSI and the ADSP charger firmware). Test OTG with and without a PD charger in Phase 3; the Tab S6 host notes apply too. |
| Wireless charging NU1669, alignment MKH100A: no driver | the Pad 4 has a wireless pen charger (MT5806 at 25-002b) instead | No overlap. Pen charging needs its own MT5806 work (Phase 5, pen). |
| Haptics broken; XEC added `qcom-hv-haptics` for pmih0108 | stock `qcom,hv-haptics@f000` and both `pmih010x-swr-haptics` are **disabled** | The Pad 4 appears to have **no haptics motor**. Skip haptics. |
| Flash LED works (`qcom,pmh0101-flash-led`) | stock `led-controller@ee00` `qcom,pmh0101-flash-led`, 2 flash channels (sources 1+4, 2+3), 500 mA each | **Easy win:** copy the OnePlus 15 flash-LED DT for the Pad 4 rear flash (check that the channel mapping matches the stock values). |

### Display, touch, GPU

| OnePlus 15 item | Pad 4 | Use for us |
|---|---|---|
| AA601 OLED, only one mode (2772x1272@165) works | NT36536 dual-DSI + DSC LCD. **Native display works at 120 Hz** (pc-007) | Ahead of the OnePlus 15. Other modes (144/90/60…) come next. The stock porch table is in relay/PC.md. |
| Synaptics S3910 SPI touch | NT36536 TDDI touch; firmware runs (pc-008) | Different chip. |
| GPU works (3D) | the GPU powers up (pc-011 B). Mesa not tried yet | The OnePlus 15 proves Adreno 840 + Mesa works on 7.3-rc4. XEC's GPU commits (speedbin + QFPROM c8a4e0c4b072/72df466c281d, corrected `opp-peak-kBps` 79d2d4bf0fc7, GPU `firmware-name` 29a65e59e72) are candidates if our GPU hits OPP or bandwidth trouble. |
| HDMI/DP broken | DP not tried | Not a blocker. infiniti has qmp-combo + DP in our queue; expect work. |

### Connectivity

| OnePlus 15 item | Pad 4 | Use for us |
|---|---|---|
| FastConnect 7900 / WCN7860 `pci17cb,110e` works | same chip id `17cb:110e`. Wi-Fi scan and BT work (pc-010/011) | Same level. The XEC firmware repo ships `ath12k/WCN7860/hw2.0/qdss.cfg`; our ath12k already sends a QDSS config (pc-009). Check whether `qdss.cfg` should be in our manifest. |
| NFC NXP SN220T | no NFC in the Pad 4 stock DT | n/a |
| Modem X85 (IPA broken), GPS via modem | SM8850P has **no modem**; Pad 4 GPS status unknown | n/a. Don't port XEC's IPA/mpss changes. |
| IR blaster | none | n/a |

### Audio, cameras, sensors

| OnePlus 15 item | Pad 4 | Use for us |
|---|---|---|
| Audio broken (WCD939x + 2× TFA9874) | WCD9395 + **6× TFA9865**. The ADSP and audio DSP services are up; no sound card yet (pc-011 A) | **Nobody has kaanapali audio yet.** We have to build it: map220v's sound nodes + TFA9865 driver, an AudioReach topology (infiniti `OnePlus-Infiniti.m4` as the template) and UCM. Volume stays capped until speaker protection (`tfa98xx.cnt`) works. XEC ships `tfa98xx.cnt` under `qcom/kaanapali/OnePlus/Infiniti/`; the Pad 4 file is in /odm (our manifest). |
| Cameras: no sensor drivers (IMX906, OV50D, S5KJN5, IMX709); flash works | Pad 4 sensors at i2c9 0x20 / 0x6c (models not identified yet) | Camera sensor drivers are the long pole on both devices. XEC firmware has `CAMERA_ICP.mbn`/`CAMERA_ICP_1.mbn`, which the kaanapali CAMSS needs. **Add the Pad 4 equivalents to the manifest** when cameras start. Identify the Pad 4 sensors from the stock camx configs on the PC. |
| All sensors broken (SSC) | bmi3x0, ak0991x, stk36c01 behind SSC | Same situation. Path: hexagonrpcd + libssc (troikoss / Tab S6 notes). |
| Hall = `gpio-keys` (broken) | bu52053nvx on TLMM98 → `SW_LID` | We need a gpio-keys `SW_LID` node. The OnePlus 15 "broken" is theirs; ours is a plain GPIO key. |
| Fingerprint, proximity/ALS (TOF8806) | no fingerprint; ALS is stk36c01 via SSC | n/a |
| XEC firmware `evass.mbn` (EVA/CVP) | stock has `cvp_region`; firmware present on stock | Not needed for our goal (computer-vision DSP). |
| FDE with unl0kr broken | | For Phase 7 encryption: make sure the on-screen unlock (unl0kr/plymouth) works with our display and touch. Not a blocker. |

## Part 3 — Actions taken into our plan

1. **Flash LED:** port the OnePlus 15 `pmh0101` flash-LED node to the Pad 4 DTS, with the stock channel map (led-0 = sources 1+4, led-1 = 2+3, 500 mA max). Phase 3, small.
2. **Lid:** add gpio-keys `SW_LID` on TLMM98 (already planned; the OnePlus 15 hall entry confirms the gpio-keys pattern).
3. **Haptics:** dropped. The Pad 4 stock DT has them disabled.
4. **USB OTG:** test host mode on battery and with external PD power. Expect the OnePlus 15 limitation.
5. **Firmware manifest:** check whether `ath12k/WCN7860/hw2.0/qdss.cfg` is needed. Add camera `CAMERA_ICP*.mbn` when CAMSS starts.
6. **GPU:** if Mesa shows OPP or bandwidth issues, take XEC's GPU speedbin/QFPROM/opp-peak commits.
7. **pmOS package:** write `device-oneplus-iceland` from scratch (no upstream OnePlus 15 package exists).
8. **Audio:** plan for being first on kaanapali (topology from source, UCM, volume cap).
9. **U-Boot:** our U-Boot USB fastboot result is new information for the wiki's "untested" row. Test the buttons.
   Any wiki edit or contact with the maintainers needs the user's OK.

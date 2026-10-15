# OnePlus Pad 4 (`iceland`, OPD2514) — hardware, boot chain and partition reference

For mainline Linux, U-Boot and any low-level work. Written 2026-09-28 from everything measured so far; updated for the
installed state (section 3 and the status block below).

Status: Fedora 44 GNOME installs on the tablet with two writes: the Fedora disk image into `userdata` and the footered
U-Boot install build into `boot_b`. The tablet then boots Fedora from `boot_b`, through U-Boot's EFI boot manager and
the Fedora GRUB and shim in `userdata`; Fedora marks the slot successful after a good boot (iceland-device 0.28-8 and
newer). Sections 0, 3, 4 (the userdata and boot rows), 5 (the closing note), 6 (the camera, USB, Wi-Fi and battery
notes), 7 and 9 to 10 describe the installed state. The rest describes the hardware as measured on 28 Sep and is still
right unless a note says otherwise. The raw partition backups, the stock package and the captures are kept off the
repository; their paths are not written here.

**Sources and markers:** [measured] on this tablet (stock OxygenOS capture, DSU root capture, LineageOS 24.0 runtime, mainline RAM
boots) · [source] read from the stock 11.A.38 images / decoded stock DTs / OnePlusOSS `oneplus/sm8850_b_16.0_pad_4` source · [inferred],
verify first.

**Companion documents:**
- mainline project: `mzakamin-hub/iceland-mainline` → `docs/guide/` (hardware, boot, build), `docs/device-facts/`
  (decoded stock facts: memory map, reserved memory, I2C/SPI, regulators; the raw captures are not published), `firmware/manifest.tsv`.
- LineageOS side: the PC's own handover and action logs (not published).

---

## 0. One-page summary

| Item | Value |
|---|---|
| Model / codename | OnePlus Pad 4, **OPD2514**, `iceland` (codename shared with OnePlus Pad 3 Pro OPD2513 and OPPO Pad 5 Pro) |
| This unit | project **25978** (0x657a), board string **OP657AL1**, overlay **"iceland-O IN"**, SKU 23, region 167, PCB **0x28** [measured] |
| SoC | **SM8850P "CanoeP"** (Snapdragon 8 Elite Gen 5), `soc_id` 661 / `qcom,msm-id` 0x295, revision 2.0; mainline name **kaanapali**, Android platform **canoe** [measured] |
| CPU | 8 cores: CPUs 0–5 up to 3.6288 GHz (policy0), CPUs 6–7 up to 4.3968 GHz on stock policy6 (LineageOS reported cpuinfo max 4.61 GHz) [measured] |
| GPU | Adreno **840** (`gen80200`, `qcom,adreno-44050a01`, chip_id 0xfc44050a31, 18 MiB GMEM, 1.2 GHz max) [measured] |
| RAM | **12 GB** (`ddr_info=6|8|1|5|12`; ABL `/memory` = 20 segments, 11.50 GiB visible) [measured] |
| Storage | UFS 4.x, Samsung **KLUEG4RHKF-F0H1**, HS-G5 ×2, 6 LUNs, host `1d84000.ufshc` [measured] |
| Display | CSOT **XN251** LCD, 13.2", **3392×2400 landscape-native** (2 DSI links × 1696), DSC 1.2, video mode, 30–144 Hz, NT36536 TDDI [measured] |
| Touch / pen | Novatek **NT36536** TDDI on SPI19 (QUP4), no-flash (firmware in SRAM each boot); active pen via the same IC; pen charger **MT5806** [measured] |
| Audio | 6× NXP **TFA9865** amps (TDM, 8×32 bit), **WCD9395** codec (SoundWire), WCD939x USB-SS mux [measured] |
| Cameras | rear SmartSens **SC1320CS** 13 MP (+AF, EEPROM, PDAF), front **SC820CS** 8 MP; PMH0101 flash LED (two dies) [measured] |
| Wireless | **WCN7860** hw2.0 "peach": Wi-Fi 7 on PCIe0 (ath12k), BT on GENI UART; no modem/GNSS/NFC [measured] |
| Battery | **13,380 mAh** design (full 13,789 mAh reported), 80 W SUPERVOOC via 2× SC8547D; gauge/auth differ by variant [measured] |
| Sensors | on the ADSP (SSC): Bosch **bmi3x0** accel/gyro, AKM **ak0991x** mag, Sensortek **stk36c01** ALS/RGB/proximity, ROHM **bu52053nvx** hall [measured] |
| Accessories | pogo-pin keyboard (UART), OnePlus Stylo (MT5806 wireless charging, NT36536 pen protocol) |
| Boot | Qualcomm ABL (OnePlus build), A/B, boot header **v4**, Gunyah hypervisor, AVB 1.3, bootloader **unlocked** ("orange") [measured] |
| Stock kernel | Google **prebuilt GKI 6.12.58** (`ab15213644`) + 594 OnePlus/Qualcomm vendor modules [source] |
| Firmware | OxygenOS **11.A.38** (`OPD2514_16.0.10.501(EX01)`), anti-rollback — never older [measured] |
| Installed system | Fedora 44 GNOME from `userdata`, booted through `boot_b` (U-Boot install build). Kernel 7.3.0-rc7 (`kernel-iceland`); firmware package 11.A.38-3; device package `iceland-device` |

---

## 1. Identity and board variants

| Project | Board string | dtbo model | Device | Notes |
|---|---|---|---|---|
| 25978 (0x657a) | OP657AL1 | "iceland-O EU" / "iceland-O IN" | **OnePlus Pad 4** | EU/IN = battery-gauge hardware variants, not software regions; **this unit = IN** [measured] |
| 25927 (0x6547) | OP6547L1 | "iceland-O" | OnePlus Pad 3 Pro (China) | in OSS source, not in our builds |
| 25926 (0x6546) | — | "iceland" | (OPPO Pad 5 Pro family) | its tp/sensor/misc dtsi files are reused by all iceland boards |
| 25977 (0x6579) | — | "iceland-O O EU" | unknown | **only in the stock dtbo, not in OnePlusOSS** [source] |

- `oplus,hw-id` (PCB revisions) accepted by the overlay: EVB1, EVB2, EVB3, T0, EVT1, EVT2, DVT1, DVT2, PVT1 [source]. `PcbVersion` on the kernel
  command line (this unit **0x28** [measured]) decides behaviour below/above EVT1 (= 24) — e.g. KTZ8869 LCD bias by GPIO (< EVT) or by register (≥ EVT).
- `oplus,gauge-id = <1>` (platform gauge) in the IN board dtsi [source].
- Base DTB match: `qcom,msm-id = <0x295 0x20000 …>`, `qcom,board-id = <0x08 0x00>` — a DTB booted directly by ABL must carry them [measured].
- Stock ABL picked dtbo entry **6** (stock 10-entry dtbo); our LineageOS shared canoe dtbo → entry **13**; vendor_boot DTB index 10 [measured].
- Region: stock `my_region.type=ROW_all`; regional props `odm/etc/25978/build.{ROW,EU,IN,NA,default}.prop` [source].

## 2. SoC, memory, storage

- **SoC** `qcom,canoep` / `qcom,canoe-mtp` (live DT model `Qualcomm Technologies, Inc. Canoe MTP,iceland-O IN`) [measured]. Gunyah hypervisor
  (`androidboot.hypervisor.version=gunyah`, protected VMs supported) [measured].
- **RAM map:** ABL `/memory` has 20 segments including a **size-0 segment (#8)** — never boot ABL-direct with a zero-size memory node
  (PrestarLin OnePlus 15 lesson → EDL). Largest low segment for loading: 0xa6400000–0xc3dd0000 [measured]. Full table + 68 stock reserved-memory
  nodes: mainline `docs/device-facts/README.md`. Splash framebuffer **0xfc800000, 0x2b00000, 3392×2400 a8r8g8b8, stride 13568** [measured].
- **UFS LUNs** [measured] (sizes in bytes): sda 253,352,738,816 (userdata, super, persist…), sdb 8,388,608 (xbl_a set), sdc 8,388,608 (xbl_b set),
  sdd 12,582,912 (cdt/ddr), sde 2,067,791,872 (A/B firmware + boot set), sdf 461,373,440 (oplusreserve*, nonmodemst*).
  LUN enumeration order can change between boots → **mount by partlabel** [measured].

## 3. Boot chain and bootloader

```
PBL (ROM) → XBL (xbl_a/b on LUN sdb/sdc, + xbl_config) → TZ / Gunyah (hyp) / AOP / CPUCP / TME; SoCCP started by the boot chain
          → UEFI (uefi_a/b) → ABL (abl_a/b, OnePlus build; fastboot lives here) → boot (kernel) + vendor_boot (DTBs + vendor ramdisk)
            + init_boot (generic ramdisk) + dtbo (overlays) → kernel
```

**Installed chain (13-14 Oct 2026)** [measured]:
1. ABL starts `boot_b`, checks its AVB footer (footer sha256 prefix `4955ee98`; the unfootered U-Boot install build v3 is `979b4076`,
   540,672 bytes) and counts the tries for slot b.
2. U-Boot v3 looks for a `fedora` partition (none), then runs `bootefi bootmgr` on the whole disk image in `userdata`. It falls
   back to fastboot if nothing is found. The install build does not reset or power off by itself, brings USB up without ABL,
   and reboots into the boot loader on `fastboot reboot-bootloader`.
3. `userdata` holds the Fedora 44 disk image (the image's sha256 prefix is `2246e9a7`; 6,732,251,564 bytes as sparse pieces; it
   unpacks to 237,159,641,088 bytes). Its EFI programs are Fedora's shim and GRUB (aarch64). Partition 3 is the root; the rest
   of the layout is unverified.
4. GRUB loads `kernel-iceland` (BLS entry) with `dtb/qcom/kaanapali-oneplus-iceland.dtb` and the initramfs.
5. The root is btrfs (`compress=zstd:1`, no quotas) on a loop device (`/dev/loop0`, set up by the dracut-iceland-carrier initramfs)
   backed by `userdata`. The storage LUNs are read-only to the running system through `iceland-storage-ro`, except the boot LUN for
   the one `qbootctl -m` call.

Slot marking: ABL keeps a successful flag, an unbootable flag and a retry count per slot. Every normal power-on of a slot that is
not successful counts one try. Only Android or Fedora's `qbootctl -m` marks a slot successful; U-Boot does not. On the installed
system `iceland-slot-mark` runs `qbootctl -m` once after a good boot. iceland-device 0.28-7 skipped it (its guard refused the
loop root); 0.28-8 and newer accept a loop root backed by `userdata`, make the boot LUN writable only for the one
`qbootctl -m` call, and log both.

Install checks: a full backup of the 151 partitions and the stock images, checked; a return-to-stock dry run; a second
copy on another disk. The install is Fedora only (no dual boot).

**ABL fastboot** (`getvar`) [measured]: `product=canoe`, `hw-revision=20000`, `variant=SM8 UFS`, `secure=yes`, `unlocked=yes`,
`is-userspace=no` (ABL fastboot; fastbootd is in recovery), `max-download-size=805306368`, slots a/b with `slot-retry-count` 5 and
`slot-successful`, battery voltage readable.

**Measured behaviours** [measured]:
- `fastboot boot <header-v4 image>` (RAM boot) is **accepted** — the mainline project boots U-Boot and Linux this way; nothing is written.
  A DT appended after a gzip kernel is dropped by ABL → keep the DT inside the gzip stream (`kernel = gzip(u-boot.bin)`).
- `fastboot flash <partition>_a/_b` and `fastboot reboot recovery` work on the unlocked bootloader (`set_active` exists but has not
  been used on this tablet [inferred]; slot b was marked with `qbootctl` on 14 Oct, see section 3). LineageOS installs by flashing boot/init_boot/vendor_boot/dtbo/recovery, then sideloading the OTA zip in
  recovery; later updates are sideloaded and land on the other slot, which then becomes active.
- Key combos: **Volume Down + Power** → fastboot (bootloader). Recovery via `fastboot reboot recovery`.
- Reboot from a mainline kernel is a PS_HOLD **hard** reset (DDR cold init, PonReason 0x11) → pstore/ramoops don't survive; the reset
  source is in Android's `/proc/bootloader_log` (`PM: Reset by …`, `Reset Type`, `PonReason`).
- **EDL** (Qualcomm 9008): no OnePlus-signed SM8850 firehose is available → treat EDL as **no recovery**; fastboot is the floor.
- Unlock = Developer options → OEM unlocking + `fastboot flashing unlock` (wipes). **Never relock** with anything non-stock installed.

**Verified boot** [measured]: AVB 1.3, `androidboot.verifiedbootstate=orange`, `vbmeta.device_state=unlocked`, veritymode disabled (unlocked).
LineageOS's upstream sm8850-common builds the top-level vbmeta with `--flags 3`; with it Android 17 first-stage init lacks
`androidboot.vbmeta.*` → our LineageOS build uses `--flags 1` (Akshay Kakatkar's change). Irrelevant for mainline (no Android userspace).

**Boot image formats** [source]:
| Image | Content |
|---|---|
| `boot` (96 MiB) | header v4, **kernel only** (stock: raw arm64 Image 41,236,992 B, GKI 6.12.58) |
| `init_boot` (8 MiB) | generic Android ramdisk |
| `vendor_boot` (96 MiB) | header v4, page 4096; LZ4-legacy vendor ramdisk (18.8 MB, 499 modules); **14 base DTBs** (7.6 MB; Alor/Canoe/CanoeP variants); bootconfig |
| `dtbo` (24 MiB partition) | DT table, stock **10 entries** (14,489,612 B + AVB footer) |
| `recovery` (100 MiB) | recovery ramdisk (LineageOS recovery has kernel_size 0 → uses boot's kernel) |
| `vbmeta`, `vbmeta_system`, `vbmeta_vendor` | AVB metadata (64 KiB each) |

**Kernel command line** (stock vendor_boot) [source]: `video=vfb:640x400,bpp=32,memsize=3072000 log_buf_len=2M nosoftlockup console=ttynull
qcom_geni_serial.con_enabled=0 bootconfig buildvariant=user` — the GENI serial console is **disabled** (no UART console on stock).
**Bootconfig** [source]/[measured]: `androidboot.hardware=qcom memcg=1 usbcontroller=a600000.dwc3 load_modules_parallel=true
hypervisor.protected_vm.supported=true hypervisor.version=gunyah vendor.qspa=true serialconsole=0`; ABL adds `androidboot.prjname=25978`,
`product.hardware.sku=23`, `bootdevice=1d84000.ufshc`, `baseband=apq`, `dtbo_idx`, `dtb_idx`, `vbmeta.*`, `slot_suffix`, and on the
command line `oplusboot.prjname/sku/oplus_region=167`, `device_info.ddr_info`, panel `mdss_dsi_panel_XN251_P_D_A0024_vid` PanelID
0x00AC8000 PCB 0x28, touch `novatek,nf_nt36536` [measured].

**Anti-rollback (ARB)** — the only real brick risk:
- Every LineageOS OTA writes **40 firmware partitions** (below) from 11.A.38. Flashing any older firmware (e.g. 11.A.32) can hard-brick.
- [measured] Found on this tablet: before `copy-partitions`, the **inactive slot b still held 11.A.32 firmware** (factory state). Never
  `set_active` to a slot whose firmware is older; LineageOS's `copy-partitions-20220613-signed.zip` copies the active slot's firmware to
  the other slot (done: 40/40 identical on a/b since 2026-09-28).
- Mainline work never needs to touch firmware partitions.

## 4. Partitions (all 151, by LUN) [measured]

Sizes in bytes. A/B pairs listed once as `name_a/_b`. **[never write] = never write** (firmware / calibration / security),
**[back up first] = back up before any wipe** (per-device, not in any download).

**LUN sda (253.35 GB — user LUN)**
| Partition | Size | Role |
|---|---|---|
| ssd (sda1) | 8,192 | secure storage descriptor [never write] |
| **persist** (sda2) | 134,217,728 | sensor/Wi-Fi/BT calibration, DRM keys [back up first][never write] |
| misc (sda3) | 1,048,576 | bootloader message / A/B control |
| keystore (sda4), frp (sda5) | 524,288 each | [never write] |
| vbmeta_system_a/_b (sda6/7), vbmeta_vendor_a/_b (sda8/9) | 65,536 each | AVB chained |
| metadata (sda10) | 67,108,864 | FBE metadata keys (formatting data wipes it) |
| rawdump (sda11) | 268,435,456 | crash dumps |
| splash_odm (sda12) | 34,226,176 | OEM splash |
| hybridswap (sda13) | 1,073,741,824 | OnePlus swap |
| **super** (sda14) | 14,612,955,136 | dynamic partitions (group `qti_dynamic_partitions`, 14,608,760,832) |
| **userdata** (sda15) | 237,159,641,088 | Android data (FBE) on the original device. Since 13 Oct it holds the whole Fedora 44 disk image (section 3); Android no longer starts |

**LUN sdb / sdc (8 MiB each — XBL set, a on sdb, b on sdc)** [never write]: xbl (3,670,016), xbl_config (471,040), multiimgqti, multiimgoem
(32,768 each), apdp (sdb5) / apdpb (sdc5) (262,144), tme_seq_patch (8,192), tme_fw (1,048,576), tme_config (131,072),
xbl_ac_config (131,072); last_parti (sdc10, 2,555,904).

**LUN sdd (12 MiB)** [back up first][never write]: ALIGN_TO_128K_1, **cdt** (131,072 — configuration data table), **ddr** (1,048,576 — DDR training),
engineering_cdt_a/_b (1,048,576), ocdt (131,072), **dinfo** (16,384).

**LUN sde (2.07 GB — A/B firmware and boot set)**
| Partition (_a / _b) | Size | Role |
|---|---|---|
| uefi | 5,242,880 | UEFI firmware [never write] |
| aop, aop_config | 524,288 each | always-on processor [never write] |
| tz, tz_ac_config, tz_qti_config | 8,388,608 / 262,144 / 204,800 | TrustZone [never write] |
| hyp, hyp_ac_config | 8,388,608 / 262,144 | Gunyah hypervisor [never write] |
| modem | 367,001,600 | FAT image: ADSP/CDSP firmware, Wi-Fi `peach/` (no cellular modem on SM8850P) [never write] |
| bluetooth | 12,582,912 | BT firmware `brhbtfw20.*` [never write] |
| abl | 1,048,576 | ABL / fastboot [never write] |
| dsp | 77,594,624 | DSP libraries [never write] |
| keymaster, spuservice, devcfg, qupfw, shrm, cpucp, cpucp_dtb, featenabler, imagefv, uefisecapp, oplus_sec, secretkeeper, pdp, pdp_cdb | various | firmware [never write] |
| soccp, soccp_debug, soccp_dcd | 8,388,608 / 524,288 / 24,576 | SoCCP (charger/USB-PD co-processor) firmware [never write] |
| dcp | 8,388,608 | [never write] |
| xbl_ramdump | 2,097,152 | [never write] |
| splash | 34,226,176 | boot logo |
| **boot** | 100,663,296 | kernel (stock and LineageOS). Since 13 Oct, slot b holds the U-Boot install build v3 (section 3) |
| **init_boot** | 8,388,608 | generic ramdisk |
| **vendor_boot** | 100,663,296 | DTBs + vendor ramdisk |
| **dtbo** | 25,165,824 | DT overlays |
| **vbmeta** | 65,536 | AVB top level |
| **recovery** | 104,857,600 | recovery |
| pvmfw, pvmfw_signed | 1,048,576 each | protected-VM firmware |
| qtvm_dtbo | 5,242,880 | Trusted-UI VM overlays |
| qweslicstore | 262,144 | licences [back up first] |
| oplus_storagefw | 10,485,760 | UFS firmware updates [never write] |
| qmcs (singleton) | 134,217,728 | |
Singletons on sde: efisp 3,145,728; **devinfo** 4,096 (unlock state) [never write]; toolsfv 1,048,576; logfs 8,388,608; storsec 131,072 [never write];
uefivarstore 524,288 [never write]; secdata 28,672 [never write]; mdcompress 20,971,520; connsec 131,072; tzsc 131,072; spunvm 33,554,432 [never write];
xbl_sc_test_mode 65,536; xbl_sc_logs 131,072; dpm 8,192; apdp_full 262,144.

**LUN sdf (461 MB — OnePlus reserve)** [back up first][never write]: ALIGN_TO_128K_2; **oplusreserve1** 8,388,608; **oplusreserve2** 268,435,456;
oplusreserve3 67,108,864; oplusreserve5 67,108,864; **nonmodemst1/2** 2,097,152 each; DRIVER 33,554,432; ompdt 4,194,304.
No `modemst1/2`, `fsg`, `fsc` (Wi-Fi-only) [measured].

**The 40 firmware partitions every ROM zip flashes** [source]: abl aop aop_config bluetooth cpucp cpucp_dtb devcfg dsp engineering_cdt
featenabler hyp hyp_ac_config imagefv keymaster modem multiimgoem multiimgqti oplus_sec pdp pdp_cdb qupfw secretkeeper shrm soccp
soccp_dcd soccp_debug splash spuservice tme_config tme_fw tme_seq_patch tz tz_ac_config tz_qti_config uefi uefisecapp xbl
xbl_ac_config xbl_config xbl_ramdump.

**super contents** [source] (11.A.38): system, system_ext, product, vendor, odm, **vendor_dlkm** (ext4, 151.6 MB, 454 modules), **system_dlkm**
(EROFS uncompressed, 14.8 MB, 104 GKI modules, flat in `/lib/modules/`), and OnePlus `my_bigball`, `my_carrier`, `my_engineering`,
`my_heytap`, `my_manifest`, `my_product`, `my_region` (52.9 MB), `my_stock` (2.08 GB).

**Backups:** a full raw backup of all 151 partitions (sha256-verified against the device) + GPT head/tail of every LUN, taken 27 Sep
and kept off the repository (location not published) [measured]. userdata raw is FBE-encrypted → the `/data/vendor` files (TEE) were copied at
file level before Android was erased for the Linux install (13 Oct).

## 5. Firmware files (where Linux gets them) [measured]

| Linux name (mainline manifest) | Stock source |
|---|---|
| `qcom/gen80200_{sqe.fw,gmu.bin,aqe.fw}`, `…/gen80200_zap.mbn`, `…/vpu40_2v.mbn` | `/vendor/firmware/` |
| `…/adsp.mbn`, `adsp_dtb.mbn`, `cdsp.mbn`, `cdsp_dtb.mbn`, `adspr.jsn` | `modem_a:/image/` (split `.mdt` + `.bNN`) |
| `…/soccp.mbn` | raw `soccp_a` partition (already running at boot; Linux only attaches) |
| `ath12k/WCN7860/hw2.0/{amss.bin,m3.bin,aux_ucode.bin,qdss.cfg}` | `modem_a:/image/peach/{amss20.bin,phy_ucode20.elf,aux_ucode20.elf,qdss_trace_config_v2.cfg}` — **qdss.cfg is mandatory** |
| `ath12k/WCN7860/hw2.0/{board.bin,regdb.bin}` | `/odm/etc/wifi/peach/{bdwlan.elf,regdb.bin}` (board_id 0xff) |
| `qca/brhbtfw20.mbn`, `qca/brhbtnv20.bin` | `bluetooth_a:/image/` (**not** the `gngbt*` names some lists use) |
| `novatek/novatek_nt36536_fw.bin` | `/odm/firmware/tp/25926/FW_NT36536_HUAXING.img` minus its header (see §6.2) |
| `tfa98xx.cnt` (3,702 B) | `/odm/firmware/tfa98xx.cnt` (speaker protection) |
| `mt5806_firmware.bin` | `/odm/firmware/wireless_pen/25978/` |
| `POGOPIN_KB.bin` | `/odm/firmware/` (keyboard OTA) |
| `CAMERA_ICP.mdt`/`CAMERA_ICP_1.mdt` + `.bNN`, EVA | `/vendor/firmware/` |
Destination convention: `qcom/kaanapali/OnePlus/iceland/`.

Publication: the generic Pad 4 firmware blobs (ADSP, CDSP, SOCCP, GPU, Wi-Fi / BT, touch, camera
and VPU) are published in the dedicated firmware repository `iceland-firmware`, with the source and sha256 of each file in its
manifest (release 11.A.38-2 holds 278 generic files; 11.A.38-3 adds the decoded generic thermal model). Unit-specific data (the
calibration, the key material, the partition carves, the serial and the addresses) is never published. For any other file, extract
it from the user's own device or OTA.

## 6. Hardware blocks

### 6.1 Display and backlight
- **Panel** "XN251 p d dsc video mode panel" (CSOT), `qcom,mdss-dsi-panel-type = dsi_video_mode`, **2 DSI controllers/PHYs** (`<0 1>`),
  each **1696×2400** → 3392×2400; 24 bpp; traffic `non_burst_sync_event`; base timing 120 Hz, **clock 1,364,039,570 Hz** [source].
- **DSC** v1.2, slice **848×20**, 2 slices/packet, 1 encoder, 8 bpc, **8 bpp**, block prediction [source].
- **Reset sequence** `<1 10>, <0 5>, <1 10>` (level, ms); `oplus,reset_custom`: with touch gesture-wake active the reset is pulsed low
  twice so the TDDI restarts [source].
- **Per-rate porches (stock 11.A.38 dtbo, per DSI link)** [source] — DFPS type `dfps_immediate_porch_mode_both_hv_porch`:

  | Hz | 120 | **144** | 90 | 60 | 50 | 48 | 30 |
  |---|---|---|---|---|---|---|---|
  | hfp | 50 | **32** | 210 | 50 | 210 | 210 | 50 |
  | hbp | 52 | **20** | 160 | 52 | 160 | 160 | 52 |
  | hpw | 32 | **16** | 80 | 32 | 80 | 80 | 32 |
  | vfp | 26 | 26 | 26 | 2726 | 2010 | 2196 | 8126 |
  | vbp | 272 | 52 | 52 | 272 | 52 | 52 | 272 |
  | vpw | 2 | 2 | 2 | 2 | 2 | 2 | 2 |

  (OnePlusOSS 16.0.6.103 has hfp 34 at 144 Hz; the stock 11.A.38 value is 32.) Mainline prunes 144 Hz as `CLOCK_HIGH` (~1261 MHz) — the
  per-rate porches above are what stock uses; reference implementation: LineageOS sm8850-modules commit
  "qcom: display: Support per refresh rate H/V porch DFPS". (14 Oct: 144 Hz works on the installed system, with
  30 to 144 Hz live switching; the idle refresh is still off.)
- **Supplies** [measured]/[source]: vddio `pmh0101_l12` **1.9 V** (the shared canoe regulator dtsi caps L12B at 1.8 V → must be raised), DSI
  `vdda-1p2` `pmh0110_d_l1`, DSI PHY `vdda-0p9` `pmh0110_d_l3`. Rails for scanout: MMCX + MX (+ MXC) at TURBO while ABL's 650 MHz MDP runs;
  hold **both** MDSS GDSCs (`MDSS_CORE`, `MDSS_CORE_INT2`).
- **Backlight**: 2× Kinetic **KTZ8869** — master **i2c14 @0x11** (`ktz8869-i2c-master`, QUP3 `1984000`), slave **i2c15 @0x11**
  (`ktz8869-i2c-salve`, QUP3 `1988000`); HWEN **TLMM 1** (shared by both → `CONFIG_GPIO_SHARED_PROXY=y` on 7.3+); LCD bias ENP **TLMM 14**,
  ENN **TLMM 15** (used before EVT; later boards set the bias over I2C registers); `oplus,bl-use-ktz8869-ic-ctrl`; brightness 2–4095,
  `bl_ctrl_external` [measured]/[source]. ABL leaves BL_DIMMING 0x44 on both, slave BL_CFG2 0x8d / BL_OPTION2 0x77 [measured].
- **DP**: `DSI-1` panel + `DP-1` (USB-C DisplayPort alt mode, via QMP combo PHY) exist on stock [measured].
- Splash framebuffer: see §2.

### 6.2 Touch and pen (NT36536 TDDI)
- `novatek,nf_nt36536` on **spi19.0** (QUP4 SE `1a80000`, wrapper `1ac0000`), IRQ **TLMM 158**; input devices `touchpanel`,
  `touchpanel_kpd`, `touchpanel_pen` (stock driver) / `NVTCapacitiveTouchScreen`, `NVTCapacitivePen` (mainline) [measured].
- **No flash**: firmware is written to SRAM at every probe; the IC resets with the panel (TDDI) → touch must follow panel power/reset;
  stock couples them through the display driver's touch-notify (`TP_BASIC`): with gesture-wake on, the panel keeps its supply [measured]/[source].
- Reported: PID **0x5F9A**, abs range **33920×24000**, sensor grid 60×40, pen supported [measured].
- **Firmware versions** [measured]: stock dtbo embeds **0x15** (`firmware-data-0`, 258,048 B); OnePlus's GPL OSS DT embeds **0x13** (what
  LineageOS ships); mainline loads **0x15** from the stock file. `/odm/firmware/tp/25926/FW_NT36536_HUAXING.img` = 80-byte `FwUp!`
  header (LE u32 length at 0x0c, embedded name) + 258,048-byte Novatek image + 128-byte trailer; the stock kernel driver refuses the
  signed file and falls back to the DT copy. `_FAE.img` is a factory build (fw 0x01) — writing `/proc/touchpanel/tp_fw_update` 0/1
  loads it into RAM (don't); 2 refuses the signed file [measured].
- DT properties used by the Pad 4 ([source] `oplus/tp/iceland-oplus-tp-25926.dtsi`): `touchpanel,pen_max_diff = <14500>`,
  `touchpanel,other-pencil-pressure`, `pen_support`, `pen_support_opp`, `black_gesture_support`, `black_gesture_indep_support`,
  `smart_gesture_support`, prevention (palm/grip) v4.x tunables. Stock procfs: `/proc/touchpanel/double_tap_enable` (DT2W),
  `double_tap_enable_indep`, `gesture_support`.
- **Pen charger** MediaTek **MT5806** wireless TX, `oplus,wls-tx-mt5806`, **i2c25 @0x2b** (QUP I2C `984000`, wrapper `9c0000`),
  firmware `mt5806_firmware.bin` [measured].

### 6.3 Pogo-pin keyboard [source] (`oplus_pogo_kb/iceland-oplus-pogopin-kb.dtsi`)
- `tinno,pogo_keyboard` over a **high-speed GENI UART** `qcom,qup_uart@1990000` (QUP3 SE4, `GCC_QUPV3_WRAP3_S4_CLK`, GIC SPI **586**),
  `ttyHS5`, wake byte **0xFD**, auto-suspend disabled. [inferred] This is the pogo UART, **not** Bluetooth (BT is `1994000`).
- GPIOs: UART TX **TLMM 22** (`qup3_se4_l2`), RX **TLMM 23**, wake **TLMM 151**, TX enable **PMH0110_D GPIO 6**, pogo power
  **PMH0110_F GPIO 12**.
- Firmware `POGOPIN_KB.bin` (OTA over the link), touchpad 2560×1440 (resolution 24/25), keyboard names per model
  ("OnePlus Pad 4 Smart Keyboard"). Stock input `pogo_wakeup` (virtual, 8286:8002) [measured]. The keyboard is expected to appear as HID
  **22d9:3869** — [inferred] only from the keylayout `Vendor_22d9_Product_3869.kl` carried over from erhai; not observed in the early tests.
  (14 Oct: the keyboard driver works with the cover attached; the keys, touchpad, backlight and wake check is open.)
- No mainline driver (vendor UART protocol → would need a serdev driver).

### 6.4 Audio
- **Speakers**: 6× NXP **TFA9865** (`tfa,tfa98xx-v6`) — i2c0 (QUP1 `a80000`) @0x34/0x36/0x37 and i2c22 (QUP4 `1a8c000`)
  @0x34/0x36/0x37 [measured]; protection data `tfa98xx.cnt`. Stock back end **TDM-LPAIF-RX-PRIMARY, 48 kHz, 8 ch × 32 bit**; V/I feedback
  TDM-LPAIF-TX-PRIMARY 8 ch; receiver profile MI2S-RX-PRIMARY 2 ch [measured]/[source].
- **Codec**: **WCD9395** over SoundWire (RX + TX), headset jack + buttons (`canoe-mtp-snd-card Headset/Button Jack`), mics on
  CODEC_DMA-LPAIF_RXTX-TX-3, VA mics on LPAIF_VA-TX-0 [measured].
- **USB-SS audio switch** WCD939x `wcd939x_i2c` **i2c3 @0x0e** (QUP1 `a8c000`) [measured].
- LPASS LPI pinctrl `pinctrl@7760000` must probe before SoundWire (mainline) [measured]. Stock uses AudioReach/AGM + ACDB (no topology file).
- Loaded-but-unbound on stock: `oplus_audio_aw882xx` (second-source amp driver).

### 6.5 Cameras and flash
- CCI (`cci0..2` @941b000/941c000/941d000); stock also exposes them as QUP2 **i2c9** (`884000`) [measured]:
  rear **SC1320CS** @0x6c (EEPROM @0x58, actuator/VCM @0x18, PDAF), front **SC820CS** @0x20 (EEPROM @0x50); MCLK 19.2 MHz. No mainline
  sensor drivers [measured].
- **Flash LED** `qcom,pmh0101-flash-led` (`led-controller@ee00`): two dies — warm/yellow on sources 1+4, white on 2+3, led-2 all four;
  500 mA torch, 2 A flash, 1.28 s; sysfs `yellow:flash-0`, `white:flash-1`, `amber:flash-2` [measured]. Flash thermistor on PMH0101 ADC (§6.10).
- ISP firmware `CAMERA_ICP*`; camera heaps `camera_region@99600000`, `camera_2_region@99e00000` [measured].
- 14 Oct: both sensors stream through Fedora 44's libcamera 0.7.1-2 (software ISP; open and close 40 of 40). Focus is fixed at the
  stock start position (450, kernel K7); there is no autofocus. Camera into the hardware encoder does not negotiate (open).

### 6.6 Sensors, hall, cover
- All physical sensors sit on the **ADSP Sensor Core (SSC)** — Linux needs hexagonrpcd/libssc, not I²C drivers [measured]:
  `bmi3x0` accel + gyro (Bosch), `ak0991x` mag (AKM), `stk36c01` ALS + RGB + proximity (Sensortek, wake-up prox), `bu52053nvx` hall
  (ROHM, wake-up). The other 28 stock sensors are OnePlus/QTI fusion (rotation vector, pedometer, pick-up, device_orient, lay_detect…).
- **Lid/cover switch**: hall output on **TLMM 98**, active-low, wake-capable → `gpio-keys` `SW_LID`, debounce 15 ms (LineageOS DT,
  verified: cover closes/opens the screen; reads "in high" with the cover open) [measured]. 14 Oct: the lid switch works on the installed
  system; wake from sleep by the cover is still open. Stock sensor config source:
  `odm/etc/sensor/config/kaanapali_mtp_bu52053nvx_0.json` (`dri_irq_num` 98).
- Magnetic-cover helper modules loaded on stock: `oplus_magcvr` (ak09973 / mxm1120 / mkh100a) — not needed for `SW_LID`.
- Stock `ro.oplus.fusionlight=true` (ALS correction in OnePlus sensor stack).

### 6.7 Battery, charging, power path
- **Battery**: design 13,380 mAh, Li-ion; stock reports `oplus battery`; `oplus,dual_cells_protection` present [measured]/[source].
- **Charger/PD MCU**: **SoCCP** runs battery management + USB-PD; Linux talks to it over **pmic-glink** (`PMIC_RTR_SOCCP_APPS`):
  `qcom-battmgr` battery/USB supplies, UCSI `ucsi-glink` (PD, PD_PPS source) [measured]. (The battmgr units were checked on the tablet: the
  battery temperature is in tenths of a degree Celsius and the voltage in microvolts.)
- 14 Oct: battery reporting, the time estimate and the charge limit (80 / 85 %) work on the installed system; a battery safety guard
  (stock regions, connector cut) is in iceland-device. Charging with the wall chargers is still to be checked.
- **Fast charge** [source]: 80 W SUPERVOOC (`oplus,vooc_project = 7`, `vooc_power_max_w 80`, charge-pump max IBUS 5.3 A, IBAT OC 16 A),
  plus OnePlus PPS/UFCS; 2× **SC8547D** charge pumps — **i2c12 @0x6a** (QUP2 `890000`) and **i2c24 @0x6a** (QUP I2C `980000`) [measured], driven on
  stock by the APPS-side `oplus_chg_v2`/voocphy (no mainline driver; basic charging via SoCCP works without them).
- **Gauge / authentication by variant** [source]/[measured]:
  - **IN (this unit)**: Qualcomm QBG platform gauge + **Maxim DS28E30** 1-wire authenticator, bit-banged on **TLMM 88** (TLMM regs
    0x0F158000/0x0F158004); DT sets `oplus,debug_bypass_ic` → the stock driver reports "authenticated" without talking to the IC.
  - **EU**: external **TI bq27541** gauge **@0x55** on I²C (its pinctrl uses TLMM 64/65; exact bus [inferred] check `oplus-chg-iceland-ext_gauge.dtsi`).
- ADSP-side I²C (pmic-glink debug bus `i2c@104`): `cps4061` @0x30, 2× `smb1501` @0x68/0x69 (SMB1501 charge pumps) [measured] — function of the
  CPS4061 on this board not verified [inferred].
- Charge profile [source]: `batt_full_temp = <-100 160 350 410>` (d°C) + `batt_full_para` (11.A.38 stock values); BCL dynamic vbat thresholds
  2500/2600 mV on pmh0101/pmih010x; `fccmax` has 7 modes (no 12 V QC/PD on Pad 4).

### 6.8 USB
- DWC3 **`a600000`** (`usbcontroller=a600000.dwc3`), USB-C 3.2; eUSB2 PHY (M31) + **eUSB2 repeater on PMIH0108** (stock override:
  device-mode register **0x57 = 0x03**); QMP combo PHY (USB3 + DP); role switch / orientation via SoCCP UCSI (`typec` `port0`) [measured]/[source].
- Mainline: NCM gadget works; UCSI registration resets the bus once (harmless) [measured].
- 14 Oct: USB device mode works (USB 2 speed). DisplayPort over USB-C: hot plug and EDID work with a bus-powered 4K
  monitor; there is no picture yet.

### 6.9 Wi-Fi and Bluetooth (WCN7860 "peach")
- 14 Oct: Wi-Fi 2.4 GHz works on the installed system (about 390 Mbit/s down in a speed test to a nearby server); the 5 GHz networks are
  listed.
- **Wi-Fi** on **PCIe0**, Gen3 ×2: RC `17cb:0123`, device **`17cb:110e`**, hw2.0, chip_id 0x2, **board_id 0xff**, firmware
  `WLAN.GNG.2.0-01536` [measured]. Stock DT specifics [source]: **`drop-l3k`** (board has no L3K rail → don't vote the PDC mode), **`msix-match-addr = <0x3000>`**
  (cnss2), tablet cnss overlay `tablet-canoe-peach-cnss-overlay.dtsi`. `cnss_wlan_region` 32 MiB (dynamic reserved memory).
  Mainline ath12k scans 2.4/5/6 GHz; an intermittent reset when loaded early is still open (load late).
- **Bluetooth** on GENI UART **`1994000.serial`**, 3.2 Mbaud, powered through the WCN PMU; `hci_uart` + `btqca`, firmware
  `BTFW.BRAHMA.2.0.1-00204` (`brhbt*`) [measured]. BD address: stock prop `persist.vendor.service.bdroid.bdaddr` ([measured] equals the stock MAC under
  LineageOS).

### 6.10 PMICs, rails, thermal, buttons
- **PMICs on SPMI** [measured]: **PMK8850** (SID 0: PON/power key, RESIN, RTC `rtc_pm8xxx`, ADC5 Gen4 host), **PMH0101** (SID 1: flash LED,
  BCL, L12 panel vddio, thermistor AMUX), **PMH0110** ×4 (SIDs 3/5/6/8 → `_d`/`_f`/`_g`/`_i` rails/GPIOs), **PMH0104** (SID 9);
  **PMIH0108/PMIH010x** (eUSB2 repeater, BCL, HV haptics block; SPMI bus/SID [inferred] not captured); `pmd802x@4` on spmi-1 is declared but
  **not fitted** (4 harmless WARNs on stock too) [measured].
- **Buttons** [measured]: power = PMK8850 PON `pwrkey` (KEY_POWER); volume down = PON `resin` (KEY_VOLUMEDOWN); volume up = `gpio-keys`
  (KEY_VOLUMEUP, **TLMM 101** active-low in the canoe MTP base DT [inferred] verify on the live DT) + `SW_LID` (§6.6).
- **Thermal** [measured]: 92–93 thermal zones; stock CPU trips 105 °C (HAL passive), 112/114 °C (kernel passive → CPU pause), 125 hot,
  135 critical; board thermistors on PMH0101 ADC5 Gen4 (`pmh0101_board_therm` AMUX THM5, `pmh0101_flash_therm` AMUX1 GPIO1, 100k
  pull-up) with passive trips at 125 °C in the Pad 4 DT [source]; BCL level 1/2 → GPU cooling states 3/5 [source]; OnePlus skin "gears" in
  `odm/etc/temperature_profile/sys_thermal_control_config.xml`.
- 14 Oct: the installed system runs the stock 20-gear thermal policy (iceland-thermal). The skin loop and the caps were measured on the tablet.
- **Vibrator**: none fitted (stock has none; `qcom_hv_haptics` loads unbound) [measured]. **IR / FM / NFC / GNSS / cellular**: not fitted
  (`oplus_sensor_kookong_ir_spi`, `radio_i2c_rtc6226_qca` load but bind nothing) [measured].

### 6.11 Remote processors
| rproc | Address | Firmware | State (stock/Lineage) |
|---|---|---|---|
| adsp | `3000000` | `adsp.mdt` (+dtb) from modem_a | running — audio, sensors (SSC), pmic-glink channel via SoCCP |
| cdsp | `32300000` | `cdsp.mdt` (+dtb) | running (NPU/compute) |
| soccp | `a3380000` | `soccp_a` partition, started by the boot chain | **attached** (Linux must attach, not load) |
| spss | `188101c` | `spss1p.mdt` | offline |
| modem | — | — | **absent** on SM8850P (delete the node) |
[measured] GPU (Adreno 840), video (Iris, `vpu40_2v`), EVA/CVP and camera ICP are separate firmware users (§5).

## 7. Stock kernel and modules [source]

- Kernel `6.12.58-android16-6-g7704a1ae279b-ab15213644-4k` = **unmodified Google GKI** (kleaf, clang 19.0.1). Vendor modules vermagic
  `6.12.58-android16-6-o-gb191ae497114-4k` (matched by KMI CRCs).
- **1,057 modules**: vendor_ramdisk **499** (`modules.load` 142 first-stage, `.recovery` 485, blocklist 62), vendor_dlkm **454**
  (`modules.load` 621 lines with duplicates, blocklist 62, `system_dlkm.modules.blocklist` 10), system_dlkm **104** (83 loaded).
  594 unique vendor module names; 685 loaded on a running stock tablet.
- Families (vendor, by count): qcom 35, oplus_network 30, **oplus_bsp_tp 25** (drivers for every OnePlus touch IC — only NT36536 binds),
  oplus_bsp_dfr 22 (telemetry), coresight 16, gh (Gunyah) 12, msm 11, rmnet 10, phy 10…
- **Bound on the Pad 4** (from the I²C/SPI/rproc maps above): `oplus_bsp_tp_nt36536_noflash` (+ tp_common/custom/novatek_common/notify),
  `oplus_audio_tfa98xx_v6`, `msm_drm` (+ KTZ8869 inside it), `oplus_chg_v2` (SC8547D, Maxim), `oplus_wireless_pen_mt5806`,
  `oplus_bsp_pogo_keyboard`, `wcd939x_dlkm`/`wcd_usbss_i2c`, `camera` (sensors via CCI), `cnss2` (Wi-Fi), `btpower`, `leds_qcom_flash`,
  `qti_pmic_glink`/`ucsi_qti_glink`/`altmode_glink`, `ufs_qcom`, `msm_kgsl`, `msm_video`, `msm_eva`, `rtc_pm8xxx`.
  (Stock module names; the installed system uses the mainline queue instead.)
- LineageOS builds all vendor modules from source (6.12.81, LineageOS sm8850 repos) — the Pad 4-specific source (NT36536, MT5806,
  KTZ8869, TFA v6.14.2, DFPS HV porch, prevention v4.5, pogo keyboard, Maxim bypass) is public in `mzakamin-hub/android_kernel_oneplus_sm8850-modules`
  and the DTs in `…-devicetrees` — useful as readable references for mainline drivers.

**Mainline equivalents** (state at 7.3-rc4 + infiniti + Pad 4 series; the 14 Oct kernel is 7.3-rc7, queue q89g, and the state column
is updated where a 14 Oct note says so):
| Block | Mainline driver | State |
|---|---|---|
| Panel | `panel-novatek-nt36536` (`csot,xn251`, upstream by Pengyu Luo + Pad 4 mode) | [measured] 30 to 144 Hz with live switching (14 Oct) |
| Backlight | KTZ8869 driver (map220v) | [measured] |
| Touch/pen | Novatek NT36536 (map220v) | [measured] touch works (14 Oct); pen works |
| Speakers | TFA9865 (map220v) + q6 TDM | playback works; PipeWire protection chain; the listening check is open (14 Oct) |
| Codec | `wcd939x` + SoundWire | [measured] binds |
| Wi-Fi / BT | `ath12k` / `hci_uart`+`btqca` | [measured] scan / hci0 |
| Battery / PD | `qcom_battmgr` (OPLUS) + `ucsi_glink` via SoCCP | [measured] (units to check) |
| USB | dwc3-qcom, M31 eUSB2, eUSB2 repeater, QMP combo | [measured] gadget |
| GPU | msm a8xx (gen80200) | [measured] powers up |
| Flash LED | `leds-qcom-flash` | [measured] rear flash works (14 Oct) |
| Lid | `gpio-keys` SW_LID TLMM 98 | [measured] lid switch works (14 Oct) |
| Sensors | hexagonrpcd + libssc + iio-sensor-proxy 3.9 | [measured] accelerometer, compass, light / proximity; gyroscope through the hub (14 Oct) |
| Cameras | SC1320CS / SC820CS | [measured] stream through libcamera 0.7.1-2; focus fixed, no autofocus (14 Oct) |
| Pogo keyboard, MT5806, SC8547D, Maxim | none | vendor-only |

## 8. What the LineageOS work adds for mainline (actionable)

Status (14 Oct 2026): the items below were the to-do list of 28 Sep. Items 1 (144 Hz), 2 (the lid switch) and 3 (the 1.9 V panel
rail) are in the 14 Oct build (the display and input rows of the feature matrix). Items 4 to 9 were not re-checked for this note
(unverified).
1. **144 Hz**: stock per-rate porches (§6.1 table, note 144 Hz hfp **32**) + the HV-porch DFPS logic → reference commit in
   `mzakamin-hub/android_kernel_oneplus_sm8850-modules` ("Support per refresh rate H/V porch DFPS").
2. **Lid**: exact node from `iceland-canoe-common.dtsi`: `gpios = <&tlmm 98 GPIO_ACTIVE_LOW>`, `EV_SW`/`SW_LID`, wakeup, debounce 15.
3. **Panel vddio**: L12B must allow 1.9 V (commit "oplus: iceland: Allow 1.9 V on L12B").
4. **WLAN**: `drop-l3k`, `msix-match-addr 0x3000` (stock dtbo) — check the ath12k/PCIe equivalents.
5. **Touch firmware**: 0x15 (stock file, header stripped) vs 0x13 (OnePlus GPL copy) — both work; 0x15 is what stock runs.
6. **Battery**: IN variant = QBG + Maxim (bypass flag set by OnePlus); EU = bq27541 @0x55 — a mainline DT should not assume one gauge.
7. **Pogo UART** is `1990000` (QUP3 SE4); BT is `1994000` — don't mix them up.
8. **eUSB2 repeater**: stock device-mode override reg 0x57 = 0x03.
9. **BCL / charge thresholds**: stock values above, if battery protection is added.

## 9. Safety rules for any low-level work
1. Never write the 40 firmware partitions, `persist`, `oplusreserve*`, `nonmodemst*`, `cdt`/`ddr`/`dinfo`, `devinfo`, security partitions.
2. Never boot or activate a slot whose firmware is older than 11.A.38; keep both slots identical (`copy-partitions`).
3. Never relock the bootloader with non-stock images. No public EDL firehose → fastboot is the only way back.
4. Prefer RAM boot (`fastboot boot`); a Linux install goes into `userdata`, with Android's `/data/vendor` and `persist` saved first.
5. Keep the verified stock package and the 151-partition backup off the repository (their locations are not published). The
   return-to-stock path (not run) uses both; it is the only documented way back (stock 11.A.38).

## 10. Where the raw data is
All the private locations below are on the PC and are not published; their paths are not written here.

| What | Where |
|---|---|
| Stock OTA and the unpacked images, stock kernel and modules | the PC (private) |
| Stock runtime capture (dumpsys, sensors, input, modules, bugreport + dmesg) | the PC (private) |
| LineageOS runtime capture and reports | the PC (private) |
| Full partition backup and GPT | the PC (private; not published) |
| Stock package for the return to stock | the PC (private; not published) |
| Decoded stock facts, memory map, I2C/SPI/GPIO/regulator/IRQ/clock notes | `mzakamin-hub/iceland-mainline` `docs/device-facts/` (the raw captures are not published) |
| OnePlusOSS Pad 4 source (modules + DT) | the OnePlusOSS repository, branch `oneplus/sm8850_b_16.0_pad_4`; staged DTs on the PC |
| Pad 4 DTs as built (LineageOS) | the LineageOS sm8850 device trees (`oplus/iceland*`, `oplus/tp`, `oplus/oplus_chg`, `oplus/oplus_pogo_kb`, the XN251 panel DTs) |

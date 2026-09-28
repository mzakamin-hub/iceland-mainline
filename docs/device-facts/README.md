# Device facts — OnePlus Pad 4 (OPD2514, project 25978, IN variant)

Source: `capture-20260927-1/` (DSU GSI root, first capture run; stopped after `gpio.txt`, see note).
Note: capture 1 used `od -tx4`, which prints each big-endian DT cell byte-swapped; values below are decoded.

## RAM (`/memory` reg, ABL-provided) — 20 segments, 11.50 GiB

`memory-map.txt` = the same cells in DT order (2 address + 2 size cells per segment), ready for
`fdtput -t x <dtb> /memory@a0000000 reg $(cat memory-map.txt)` — only for boots that bypass U-Boot's memory fixup.

| # | start | end | size |
|---|---|---|---|
| 1 | 0x81960000 | 0x81a00000 | 0.6 MiB |
| 2 | 0x81a60000 | 0x81c00000 | 1.6 MiB |
| 3 | 0x81cf4000 | 0x81d00000 | 0.0 MiB |
| 4 | 0x82478000 | 0x824a0000 | 0.2 MiB |
| 5 | 0xc4800000 | 0xd7800000 | 304.0 MiB |
| 6 | 0xd79c0000 | 0xd7a00000 | 0.2 MiB |
| 7 | 0xd7c00000 | 0xd8000000 | 4.0 MiB |
| 8 | 0xd8800000 | 0xd8800000 | 0.0 MiB |
| 9 | 0xe25a0000 | 0xff800000 | 466.4 MiB |
| 10 | 0x880000000 | 0x8af8fe000 | 761.0 MiB |
| 11 | 0x8b0000000 | 0x8b8100000 | 129.0 MiB |
| 12 | 0x980000000 | 0xb00000000 | 6144.0 MiB |
| 13 | 0x8c0000000 | 0x980000000 | 3072.0 MiB |
| 14 | 0x82600000 | 0x82700000 | 1.0 MiB |
| 15 | 0x82800000 | 0x99500000 | 365.0 MiB |
| 16 | 0x9959c000 | 0x99600000 | 0.4 MiB |
| 17 | 0x9ce80000 | 0x9fc80000 | 46.0 MiB |
| 18 | 0x9ffe0000 | 0xa0050000 | 0.4 MiB |
| 19 | 0xa0910000 | 0xa1380000 | 10.4 MiB |
| 20 | 0xa6400000 | 0xc3dd0000 | 473.8 MiB |

Segment 8 has size 0 (as reported by ABL).

## Reserved memory (stock, 68 nodes)

| start | size | name | flags |
|---|---|---|---|
| 0x0 | 0x0 (0.00 MiB) | `demura_region_0` |  |
| 0x0 | 0x0 (0.00 MiB) | `demura_region_1` |  |
| 0x80000000 | 0xe00000 (14.00 MiB) | `gunyah_hyp_region@80000000` | no-map |
| 0x80e00000 | 0x400000 (4.00 MiB) | `reserved_region@80e00000` | no-map |
| 0x81200000 | 0x200000 (2.00 MiB) | `cpucp_pdp_region@81200000` | no-map |
| 0x81a00000 | 0x60000 (0.38 MiB) | `xbl_dtlog_region@81a00000` | no-map |
| 0x81c00000 | 0x60000 (0.38 MiB) | `aop_image_region@81c00000` | no-map |
| 0x81c60000 | 0x20000 (0.12 MiB) | `aop_cmd_db_region@81c60000` | no-map |
| 0x81c80000 | 0x74000 (0.45 MiB) | `aop_tme_uefi_merged_region@81c80000` | no-map |
| 0x81ce4000 | 0x10000 (0.06 MiB) | `botloader_mem@0x81CE4000` |  |
| 0x81d00000 | 0x200000 (2.00 MiB) | `smem_region@81d00000` | no-map |
| 0x81f00000 | 0x100000 (1.00 MiB) | `pdp_ns_shared_region@81f00000` | no-map |
| 0x82000000 | 0x380000 (3.50 MiB) | `cpucp_scandump_region@82000000` | no-map |
| 0x82380000 | 0x20000 (0.12 MiB) | `adsp_mhi_region@82380000` | no-map |
| 0x823a0000 | 0x40000 (0.25 MiB) | `soccp_sdi_region@823a0000` | no-map |
| 0x823e0000 | 0x80000 (0.50 MiB) | `pmic_minii_dump_region@823e0000` | no-map |
| 0x82460000 | 0x18000 (0.09 MiB) | `qup_fw_region@82460000` | no-map |
| 0x824a0000 | 0x100000 (1.00 MiB) | `pvm_fw_region@824a0000` | no-map |
| 0x82700000 | 0x100000 (1.00 MiB) | `tz_stat_region@82700000` | no-map |
| 0x82800000 | 0x2000000 (32.00 MiB) | `qdss_apps_region@82800000` | reusable |
| 0x84a00000 | 0x5500000 (85.00 MiB) | `dsm_partition_1_region@84a00000` | no-map |
| 0x89f00000 | 0xa80000 (10.50 MiB) | `dsm_partition_2_region@89f00000` | no-map |
| 0x8aa00000 | 0xeb00000 (235.00 MiB) | `mpss_region@8aa00000` | no-map |
| 0x99500000 | 0x80000 (0.50 MiB) | `q6_mpss_dtb_region@99500000` | no-map |
| 0x99580000 | 0x10000 (0.06 MiB) | `ipa_fw_region@99580000` | no-map |
| 0x99590000 | 0xa000 (0.04 MiB) | `ipa_gsi_region@99590000` | no-map |
| 0x9959a000 | 0x2000 (0.01 MiB) | `gpu_microcode_region@9959a000` | no-map |
| 0x99600000 | 0x800000 (8.00 MiB) | `camera_region@99600000` | no-map |
| 0x99e00000 | 0x800000 (8.00 MiB) | `camera_2_region@99e00000` | no-map |
| 0x9a600000 | 0x800000 (8.00 MiB) | `video_region@9a600000` | no-map |
| 0x9ae00000 | 0x700000 (7.00 MiB) | `cvp_region@9ae00000` | no-map |
| 0x9b500000 | 0x1900000 (25.00 MiB) | `cdsp_region@9b500000` | no-map |
| 0x9ce00000 | 0x80000 (0.50 MiB) | `q6_cdsp_dtb_region@9ce00000` | no-map |
| 0x9fc80000 | 0x40000 (0.25 MiB) | `spu_secure_shared_memory_region@9fc80000` | no-map |
| 0x9fcc0000 | 0x40000 (0.25 MiB) | `spu_secure_shared_memory_region@9fcc0000` | no-map |
| 0x9fd00000 | 0x2e0000 (2.88 MiB) | `spss_region_region@9fd00000` | no-map |
| 0xa0050000 | 0x80000 (0.50 MiB) | `dcp_dtb_region@a0050000` | no-map |
| 0xa00d0000 | 0x300000 (3.00 MiB) | `dcp_region@a00d0000` | no-map |
| 0xa03d0000 | 0x500000 (5.00 MiB) | `soccp_region@a03d0000` | no-map |
| 0xa08d0000 | 0x40000 (0.25 MiB) | `soccp_dtb_region@a08d0000` | no-map |
| 0xa1380000 | 0x80000 (0.50 MiB) | `q6_adsp_dtb_region@a1380000` | no-map |
| 0xa1400000 | 0x5000000 (80.00 MiB) | `adspslpi_region@a1400000` | no-map |
| 0xa7f00000 | 0x8000 (0.03 MiB) | `device_info_mem@0xA7F00000` |  |
| 0xc3dd0000 | 0xa30000 (10.19 MiB) | `hypervisor_extended_heap_region@0xc3dd0000` | no-map |
| 0xd7800000 | 0x1c0000 (1.75 MiB) | `xbl_ramdump_region@d7800000` | no-map |
| 0xd7a00000 | 0x200000 (2.00 MiB) | `global_sync_region@d7a00000` | no-map |
| 0xd8000000 | 0x800000 (8.00 MiB) | `tz_merged_region@d8000000` | no-map |
| 0xf3800000 | 0x4000000 (64.00 MiB) | `trust_ui_vm_region@f3800000` | reusable |
| 0xf7c00000 | 0x4c00000 (76.00 MiB) | `oem_vm_region@f7c00000` | reusable |
| 0xfc800000 | 0x2b00000 (43.00 MiB) | `splash_region` |  |
| 0xff800000 | 0x800000 (8.00 MiB) | `llcc_lpi_region@ff800000` | no-map |
| 0x880000000 | 0x6000000 (96.00 MiB) | `lcp_dare_region` | reusable |
| dynamic | 0xc00000 (12.00 MiB) | `adsp_heap_region` | reusable |
| dynamic | 0x400000 (4.00 MiB) | `cdsp_eva_region` | reusable |
| dynamic | 0x2000000 (32.00 MiB) | `cnss_wlan_region` | reusable |
| dynamic | 0x1000 (0.00 MiB) | `debug_kinfo_region` | no-map |
| dynamic | 0x5e00000 (94.00 MiB) | `dump_mem_region` |  |
| dynamic | 0x0 (0.00 MiB) | `fastrpc_far_region` |  |
| dynamic | 0x2400000 (36.00 MiB) | `linux,cma` | reusable |
| dynamic | 0xc800000 (200.00 MiB) | `non_secure_display_region` | reusable |
| dynamic | 0x1000000 (16.00 MiB) | `qmc_dma_region` | reusable |
| dynamic | 0x1400000 (20.00 MiB) | `qseecom_region` | reusable |
| dynamic | 0x2000000 (32.00 MiB) | `qseecom_ta_region` | reusable |
| dynamic | 0x240000 (2.25 MiB) | `ramoops-region` | no-map |
| dynamic | 0x1000000 (16.00 MiB) | `sp_region` | reusable |
| dynamic | 0x1000000 (16.00 MiB) | `va_md_mem_region` | reusable |
| dynamic | 0x800000 (8.00 MiB) | `vm_comm_mem_region` | reusable |

## Display

- Panel `mdss_dsi_panel_XN251_P_D_A0024_vid`, PanelID 0x00AC8000, PCB 0x28; touch `novatek,nf_nt36536` (cmdline).
- DRM DSI-1: **3392x2400** (landscape-native), modes 30/48/50/60/90/120/144 Hz video mode; DP-1 present (disconnected).
- Splash framebuffer (ABL): `splash_region` **0xfc800000, size 0x2b00000 (43 MiB)** — same base as OnePlus 15 → U-Boot simplefb base.
  3392x2400x4 = 31 MiB; exact stride to be confirmed on first U-Boot boot.

## Live device tree (capture 2)

`capture-20260927-2/live-fdt-redacted.dtb` (+ decompiled `.dts`, 44,174 lines) = stock base DTB with the
"iceland-O IN" overlay applied by ABL; serial number overwritten with X.
- `model = "Qualcomm Technologies, Inc. Canoe MTP,iceland-O IN"`, compatible `qcom,canoe-mtp / qcom,canoep`.
- `qcom,msm-id = <0x295 0x20000 0x294 0x10000 …>` (this unit: 0x295 = SM8850P, rev 2.0), `qcom,board-id = <0x08 0x00>`
  → values a direct-ABL boot DTB must carry.

## Boot / identity

- Slot `_a`, ABL `oplusboot.verifiedbootstate=orange`, `oplusboot.prjname=25978`, `oplusboot.sku=23`, `oplus_region=167`.
- `device_info.ddr_info=6|8|1|5|12` (12 GB).
- Stock cmdline disables the geni console (`qcom_geni_serial.con_enabled=0`, `console=ttynull`).
- Bluetooth address present in stock props (`persist.vendor.service.bdroid.bdaddr`) — redacted here; source for the
  real BD address in Phase 6.

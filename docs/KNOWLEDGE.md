# OnePlus Pad 4 mainline Linux — knowledge base

This file holds everything learned and decided on this project up to **2026-09-28 evening** (it includes the PC relay
results pc-001..pc-011). It is written so that a person or an
agent with no other context can pick up the work. Related files:
- [../PROJECT.md](../PROJECT.md): short index and links
- [../CHANGELOG.md](../CHANGELOG.md): history by commit
- [PLAN.md](PLAN.md): plan v3
- [RESEARCH.md](RESEARCH.md): plan v2 and the full discovery notes
- [tests/README.md](tests/README.md): every tablet run

Contents:
1. Goal and scope
2. Standing rules
3. Repositories and layout
4. The device: verified facts
5. Research: what each reference project gave us
6. Architecture and decisions
7. Kernel: iceland-linux
8. U-Boot: iceland-u-boot
9. Linux RAM-boot debug image
10. Tablet test history
11. Problems hit and how they were solved
12. Lessons and traps
13. Current state, open issues, next steps
14. How to reproduce the work
15. Conversation timeline
16. Environment notes
17. PC relay and what the PC session found

---

## 1. Goal and scope

- **Device:** OnePlus Pad 4.
  - Codename `iceland`, model OPD2514, project 25978 (0x657a "iceland-O IN", Indian variant).
  - SoC: Qualcomm SM8850P (`kaanapali`; `canoe`/`canoep` in Qualcomm DTs). Adreno 840. 12 GB RAM.
  - Stock firmware OxygenOS 11.A.38 on slot a. Slot b had 11.A.32 firmware; since 2026-09-28 the user runs a private
    LineageOS 24.0 build from slot b, and slot b's firmware partitions are hash-identical to slot a and to the
    11.A.38 backup (checked by the PC relay). Kits RAM-boot through the active slot and never switch slots.
  - Bootloader unlocked (orange state). A/B slots.
  - Stock boot images are header v4 (boot + vendor_boot).
- **The user has:** a full backup of all 151 partitions, the stock 11.A.38 package, and a proven rollback loop. A DSU GSI with root was used for the captures.
- **Goal:** mainline Linux through **ABL → U-Boot → EFI → systemd-boot or GRUB → our kernel + DTB → distro**.
- **Distro scope (plan v3):**
  - Tier 1: pmOS (renamed **Nura** on 2026-09-27), Fedora, Arch Linux ARM.
  - Tier 2: Debian testing, Kali, latest non-LTS Ubuntu.
  - Not supported: Debian stable and Ubuntu LTS. Their Mesa and hexagonrpcd are too old for Adreno 840.
- **"One kernel for all distros":** the user asked for it; we judged it not realistic as one binary. It became **one kernel source + one config**, packaged per distro (rpm / PKGBUILD / deb / apk).
  - Both SELinux and AppArmor are built in; `lsm=` is set in each distro's boot entry.
  - The long-term real answer is **upstream**: once Pad 4 support is in mainline, distro kernels boot it.
- The earlier LineageOS track (a previous chat) is paused. This project is mainline only.

## 2. Standing rules (from the user; they must persist)

1. **All work lives on GitHub in private repos.** Nothing goes on the user's PC unless they ask, so local work isn't disturbed. Building is done in the cloud container and, when approved, in GitHub Actions.
2. **GPL compliance:**
   - Forks keep upstream history and authorship. Ported commits keep the original author.
   - Our commits carry `Signed-off-by`. SPDX headers are kept, and new files get one.
   - Every binary records its source commits in `BUILD_INFO`.
3. **Proprietary firmware is never committed or uploaded**, not even to private repos or CI artifacts.
   - Repos hold only the manifest (name, source, sha256) and extractors.
   - `map220v/iceland-firmware` has no licence; it is used as a list of file names only.
4. The capture's `private\` folder (serials, MACs, raw data) is **never uploaded**. If the user sends it by mistake, delete it from the container.
5. **The agent never flashes, unlocks, wipes or switches slots.** The user runs every tablet command.
6. **Test scripts are failsafe:** RAM boot only (`fastboot boot`) and allowlisted commands only.
   - fastboot: `devices`, `getvar`, `boot`, `reboot`, and `oem console` with no argument.
   - adb: `devices`, `get-state`, `reboot bootloader`, `shell getprop <name>`.
   - HTTP: read-only survey pages and `/cgi-bin/reboot` on 172.16.42.1.
   - U-Boot is built with `CONFIG_FASTBOOT_FLASH` disabled.
7. Nothing is published, and no maintainer (map220v, infiniti-mainline, pmOS…) is contacted, without asking the user.
8. **Hard stops (ask the user first):** any write to the tablet (first planned in Phase 4), slot switching, firmware that isn't from this tablet's 11.A.38, and publishing. (Slot b now runs LineageOS with firmware hash-identical to slot a, so it is no longer a hazard in itself, but kits never switch slots.)
9. **Commits:**
   - author `mzak <mzak.amin@gmail.com>`;
   - `Signed-off-by: mzak <mzak.amin@gmail.com>`;
   - trailers `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` and `Claude-Session: https://claude.ai/code/session_019xY37rECnXqaJ2NjLcnjJF`;
   - no model identifiers in repo files;
   - no PRs unless asked.
10. The user runs Windows (PowerShell 5.1 by default) with platform-tools. The tablet is plugged into that PC, not into the cloud container.
11. **Since 2026-09-28 the PC session runs tablet kits itself, unattended**, at the user's request. It runs
    `tools/relay/run-kit-auto.ps1`, which answers `RUN` and `-` to the screen questions. Before running, it checks that
    the sha256 values match, the allowlists are unchanged and the kit boots from RAM only. A kit that would write to the
    tablet is never run; the user is asked instead. **So every kit must log the screen and hardware state itself**
    (scanout sampler, `iceland-*` kernel lines, survey pages). Nobody is looking at the screen.
12. The PC also builds kernels and kits itself (WSL). Both sessions push to the same repos. Always `git pull --rebase`
    before pushing, and never rewrite shared history.

## 3. Repositories and layout

All repos belong to GitHub user **mzakamin-hub** and are private. The cloud session's working copies are under `/home/user`.

### iceland-mainline (umbrella)
https://github.com/mzakamin-hub/iceland-mainline
- `PROJECT.md` (index) and `CHANGELOG.md`
- `docs/PLAN.md` (v3), `docs/RESEARCH.md` (v2 + discovery), `docs/KNOWLEDGE.md` (this file)
- `docs/device-facts/`:
  - captures 1–3; `README.md` with the decoded facts; `memory-map.txt`;
  - stock DTs of this unit; `iceland-O-IN-fixups.txt` (202 symbols the stock overlay binds).
- `docs/tests/`:
  - `README.md` (run log);
  - survey folders: `uboot-run4/`, `linux-run5/`, `linux-run6/`, `linux-run7/`, `linux-run7b/`, and the PC kits
    `linux-runpc1*` … `linux-runpc11/` (subfolders per image, `session.log`);
  - `uboot-diag-run3-summary.json`.
- `docs/research/`: `gts6l-tab-s6.md` (Galaxy Tab S6 evaluation), `nura-oneplus-15.md` (the Nura OnePlus 15 page
  mapped to the Pad 4).
- `docs/device-facts/stock-display-power.md` (stock rails, bandwidth, thermal) and `lineage-20260928/` (read-only
  probe of the running LineageOS).
- `relay/`: `README.md` (protocol), `PC.md` (what the PC has), `requests/`, `results/` (000, 001, pc-001…pc-011 with
  their build scripts).
- `tools/relay/`: `pc-watch.sh` (PC poller), `run-kit-auto.ps1` (unattended run), `run-kit-long.ps1` (late page fetch).
- `firmware/manifest.tsv` + `README.md`: stock paths, sizes, sha256, corrected by the PC runs:
  - BT uses the stock names `qca/brhbtfw20.mbn` and `qca/brhbtnv20.bin`;
  - Wi-Fi `board.bin`/`regdb.bin` come from **odm** `etc/wifi/peach/`;
  - `qdss.cfg` = modem `image/peach/qdss_trace_config_v2.cfg` (**required**).
  - `firmware/convert-nt36536.py` unwraps the OnePlus touch firmware container.
- `tools/capture/`: `device-capture.sh` (runs on the tablet under root), `capture.ps1` (Windows), `capture.sh`, `README.md`. Read-only; redacts serials and MACs. Also `probe.sh` + `probe-device.sh` (PC): a read-only root probe of a running Android, streamed over `adb shell -T` and redacted.
- `tools/linux-ram/`:
  - `build.sh`, `init`, `cgi-page`, `cgi-reboot`, `modules-debug.list`, `fetch-iw.sh`, `msmparam.c` + `build-msmparam.sh` (see section 9 for the options);
  - `run-linux.ps1`: a template. `package.sh` fills in the image hashes and the list of runs (label, image, note); one session boots each image in turn.
- `artifacts/` (gitignored, cloud only): test kits `uboot-test-1`, `uboot-diag-2..4`, `linux-test-1..7` (+ .zip) and the run results the user sent back.

### iceland-linux (kernel)
https://github.com/mzakamin-hub/iceland-linux
- `kernel.pin`:
  - upstream `v7.3-rc4` 93f51579e7df (tree 1dc395d6);
  - infiniti master 10650ae7bef4;
  - `TREE_AFTER_0001_infiniti=6e2c9712…`, `TREE_AFTER_0002_iceland=6a7b5768…` (as of e0b025a).
- `patches/0001-infiniti/` (138), `patches/0002-iceland/` (28).
- `debug-patches/` holds test-only patches that prepare.sh never applies:
  - 0001: the sync_state hack;
  - 0002: `iceland-dbg:` GDSC/genpd/sync_state prints;
  - 0003: panel DCS power-mode print.
- `scripts/prepare.sh`: clone, `git am` each series, check the tree hash after each one. It needs a real clone (`.git` directory), not a worktree.
- `scripts/build.sh`:
  - defconfig + `sm8850.config` + `configs/distro-neutral.config`;
  - strict check against `configs/required.config`;
  - output to `dist/`: Image, dtb, BUILD_INFO. LLVM/clang 18 in the cloud; the PC builds with the LineageOS
    prebuilt Android clang 22 (`clang-r596125`) in WSL (no sudo, no Ubuntu clang, no zstd, so modules are installed
    with `CONFIG_MODULE_COMPRESS_ALL=`).
- `docs/PORT-LOG.md`: what happened to each of map220v's 40 commits.
- `.github/workflows/build.yml`: `workflow_dispatch` only.
- Commits:

  | Commit | Change |
  |---|---|
  | b94d38b | v7.2 + map220v queue (superseded) |
  | e7db143 | 7.3-rc4 + infiniti rebase |
  | f237d15 | CI |
  | c17f732 | framebuffer described |
  | 27326fe | MMCX TURBO |
  | 2728bb9 | MXC TURBO |
  | fe964f7 | MX TURBO too; `debug-patches/` (sync_state hack for test 7b) |
  | 05031dc | **framebuffer holds the MDSS INT2 GDSC: white screen fixed** (0022) — PC |
  | f0162e1, d7c9f52 | CPU thermal trips 105/112/114 °C + cpufreq cooling maps, mirroring stock (0023) — PC |
  | cc85322 | config: ADC5 Gen4 driver + thermal monitor — PC |
  | f9bc5e2 | **native display works** (0024–0027 + `CONFIG_GPIO_SHARED_PROXY=y`) — PC |
  | e0b025a | pmic_glink attaches a SoCCP channel that comes up first: battery data (0028) — PC |

### iceland-u-boot
https://github.com/mzakamin-hub/iceland-u-boot
- `uboot.pin`:
  - U-Boot `v2026.10-rc5` a06e89ab0;
  - infiniti `main` bce42004f;
  - mkbootimg LineageOS mirror 808ecd09;
  - `BOOT_OS_VERSION=16.0.0`, `BOOT_OS_PATCH_LEVEL=2026-08` (stock values, for anti-rollback).
- `patches/0001-infiniti/`, 14 patches:
  - text offset, blkmap hex, fastboot IN dequeue fix;
  - **pass the previous bootloader's memory map**;
  - PMIC arb v8, pmic gpio fixes, PMH0101;
  - Kaanapali GCC, RPMh clock stubs, M31 eUSB2 PHY, QMP UFS SM8750;
  - OnePlus 15 board, EFI from userdata.
- `patches/0002-iceland/`:
  - 0001: Pad 4 board (DTS, defconfig, `board/qualcomm/iceland.env`, `qcom,msm-id <0x295 0x20000>`, `qcom,board-id <8 0>`);
  - 0002: configs (no fastboot flash; console record + `oem console`).
- `scripts/prepare.sh`, `scripts/build.sh`: header v4, kernel = gzip(u-boot.bin).
- `tools/test-uboot.ps1`: the first test.
- `tools/diag/`: `build-diag.sh`, `run-diag.ps1`, `C-fastboot.env`, `D-normal.env`, `E-info.env`, `L-efi.env`.
  - Diagnostic images use USB PID 0xd00d (ABL's own), so a Windows driver can bind.

### Cloud working directories (lost when the container is reclaimed; everything that matters is pushed)
- Kernel:
  - `/home/user/iceland-src`: git kernel tree, branch `iceland-7.3` = infiniti/master + the Pad 4 series (the cloud copy may lag behind the queue; rebuild it from `prepare.sh`).
  - `/home/user/build-src`: detached build worktree.
  - `/home/user/iceland-out`: kernel build output, `dist/`.
- U-Boot: `/home/user/uboot-src` (source); `/tmp/ub-test` (prepared tree); `/tmp/ub-out` and `/tmp/ub-diag` (outputs, including the mkbootimg checkout).
- Debug image: `/tmp/linux-ram-7`.

## 4. The device: verified facts

### ABL / identity
- fastboot product `canoe`, ABL `hw-revision 20000`, `variant SM8 UFS`, `secure yes`, `max-download-size 805306368`.
- The live DT model is `Qualcomm Technologies, Inc. Canoe MTP,iceland-O IN`, compatible `qcom,canoe-mtp`, `qcom,canoep`.
- `qcom,msm-id = <0x295 0x20000 …>` (0x295 = SM8850P, rev 2.0); `qcom,board-id = <8 0>`. A DTB booted directly by ABL must carry these.
- Stock cmdline: `oplusboot.prjname=25978`, `sku=23`, `oplus_region=167`, `ddr_info=6|8|1|5|12`. The geni console is disabled (`console=ttynull`).
- dtbo has 10 overlays; this unit uses the "iceland-O IN" one (0x657a). vendor_boot has 14 SoC DTBs; this unit uses "CanoeP v2".

### Memory
- ABL `/memory`: **20 segments, 11.50 GiB** (table in `device-facts/README.md`; `memory-map.txt` is ready for fdtput).
  - Segment 8 has size 0.
  - The largest low segment usable for loading is **0xa6400000–0xc3dd0000**.
- 68 stock reserved-memory nodes. Key ones:
  - `splash_region` **0xfc800000, size 0x2b00000**;
  - `llcc_lpi` 0xff800000;
  - `gunyah_hyp` 0x80000000;
  - `adsp_mhi` 0x82380000; `global_sync` 0xd7a00000 (both XN=2 in the hypervisor, so they must be reserved);
  - `hypervisor_extended_heap` 0xc3dd0000;
  - `mpss` (modem, unused on SM8850P).
- ramoops is placed at **0xff300000** (0x400000) in our debug DT. That space is inside the 0xe25a0000–0xff800000 segment, below llcc_lpi.
- U-Boot relocates itself to 0xaffdc8000. Its fastboot download buffer is at **0xc6000000**.

### Display
- Panel `XN251` (CSOT), NT36536 TDDI, dual DSI, **3392x2400 landscape-native**, video mode, 30–144 Hz. DSC is used.
- ABL framebuffer: **0xfc800000, 3392x2400, a8r8g8b8, stride 13568**. Verified on the tablet: U-Boot test B made it white, and the U-Boot console shows on it.
- Backlight: two KTZ8869 chips, i2c14 @0x11 (master) and i2c15 @0x11 (slave). HWEN on TLMM1.
- ABL runs the MDP at **650 MHz**, which needs **MMCX TURBO** in the kaanapali OPP table.
- **Stock power facts** (from the PC; see [device-facts/stock-display-power.md](device-facts/stock-display-power.md)):
  - stock dispcc `9ba2000` has `vdd_mm` = MMCX and **`vdd_mx` = MX**; it has **no MXC supply**;
  - with the screen on, stock APPS votes MMCX (mdss_mdp, dispcc) and MX (dispcc); **MXC has 0 votes**;
  - at boot, MMCX, MXC and MX are all proxy-held at 0x180 (TURBO), and ABL's splash runs in that state;
  - so the second rail the framebuffer needs is **MX**. (Test 7b later showed that the rails were not the cause of the white screen.)
- **The white screen cause (pc-001):**
  - ABL leaves **both** dispcc GDSCs on: `MDSS_CORE` and **`MDSS_CORE_INT2`** (id 1, gdscr 0xb000, 0x9bad000).
  - Stock canoe-sde also uses both: `core_gdsc` and `core_int2_gdsc`.
  - When the framebuffer, dispcc's last consumer, probes (~10.7–15 s), dispcc's genpd `sync_state` runs
    `of_genpd_sync_state()`, which powers off every domain nobody holds. **`pd_ignore_unused` doesn't cover this path.**
  - INT2 went off and the scanout died ("white right after the text stops"). Holding INT2 from the framebuffer
    (0022) and from MDSS (0026/0027) fixes it.
- **Native display (pc-007):**
  - MSM DRM drives 3392x2400 @ 120 Hz over dual DSI + DSC, INTF_1 and INTF_2 in lockstep, no underruns.
  - Panel DCS power mode 0x9e; KTZ8869 backlight 2047/4095; `fb0 = msmdrmfb`.
  - Modes 120/90/60/30 Hz. **144 Hz is pruned** as `CLOCK_HIGH` (pixel clock 1261 MHz); stock uses per-rate porches.
  - DSI reads on link 0 return -ENODATA, which is normal for the non-master link.
- **KTZ8869:**
  - ABL leaves BL_DIMMING 0x44 on both ICs, and on the slave BL_CFG2 0x8d / BL_OPTION2 0x77. The driver now
    programs ABL's values per IC and writes only what differs (0024).
  - Both ICs share TLMM 1 as HWEN. Since 7.3, gpiolib shares it through `gpio-shared-proxy`, which must be built in
    (`CONFIG_GPIO_SHARED_PROXY=y`) or `enable-gpios` defers forever.
- **DPU splash:** mainline `dpu_boot_splash()` only knew command-mode autorefresh, so it reset the video-mode splash.
  0025 also counts a DSI INTF whose timing engine is on.
- Stock MDP interconnect: data bus ib minimum 2 500 000 kBps (`sde-min-core-ib-kbps`), reg bus 800 000. Scanout needs about 1.95 GB/s at 60 Hz and 3.9 GB/s at 120 Hz.
- Stock panel supplies: vddio `pmh0101_l12` 1.9 V; DSI `vdda-1p2` `pmh0110_d_l1`; DSI PHY `vdda-0p9` `pmh0110_d_l3`.
- Panel per-rate porches: refresh `<120 144 90 60 50 48 30>`, hfp `<50 34 210 50 210 210 50>`, vfp `<26 26 26 2726 2010 2196 8126>`.

### Storage / USB
- UFS: **HS-G5 x2**, Samsung KLUEG4RHKF-F0H1, 6 LUNs (LUN0 = 235.9 GB with userdata). The GPT reads fine in U-Boot.
- USB: dwc3 at `usb@a600000`, eUSB2 PHY (M31) via PMIH0108. Role switch via pmic-glink/UCSI, removed for bring-up. The NCM gadget binds at ~8.8 s.
- Watchdog `17600000.watchdog` binds without a reset (`CONFIG_WATCHDOG_SYSFS` is off). RNG `10c3000.rng` and
  reboot-mode work.
- **Reset type:** our reboot is a PS_HOLD **hard** reset (DDR cold init, `PonReason=0x11`). `reboot mode=warm`
  doesn't change it (the boot chain sets PS_HOLD to hard; stock uses a vendor driver). So ramoops/pmsg don't survive
  our reboots. The reset reason comes from Lineage's `/proc/bootloader_log` instead.

### Peripherals (stock I2C/SPI map)
- Amplifiers: TFA98xx (TFA9865) at 0-0034/36/37 and 22-0034/36/37. In mainline these show up as i2c 0 and 4 (bus numbers differ).
- Charge pumps: SC8547D at 12-006a and 24-006a. Pen charger: MT5806 at 25-002b. USB-SS mux: WCD939x at 3-000e.
- Cameras on i2c9 (qup2 @884000): sensors 0x20 and 0x6c, EEPROMs 0x50/0x58, actuator 0x18.
- ADSP-side (over pmic-glink): cps4061 @0x30, smb1501 @0x68/0x69.
- Touch: spi19.0 `nf_nt36536` on qup4 @1a80000. IRQ on TLMM158.
  - The driver waits for the panel.
  - Firmware is downloaded into the IC's SRAM at every boot (no flash): `Update firmware success`, `fw_ver=0x15`,
    PID 0x5F9A, abs 33920x24000, a 60x40 grid, and a pen.
  - It registers `NVTCapacitiveTouchScreen` and `NVTCapacitivePen`. A real touch hasn't been confirmed yet.
  - Stock `FW_NT36536_HUAXING.img` = an 80-byte `FwUp!` header (LE u32 length at 0x0c, name
    `tp/25926/FW_NT36536_HUAXING.img`) + the 258048-byte Novatek image + a 128-byte trailer. The `_FAE.img` is a
    different, factory build.
- Wi-Fi: WCN7860 hw2.0 "peach" on PCIe0 (Gen3 x2), 17cb:110e, chip_id 0x2, board_id 0xff, firmware
  WLAN.GNG.2.0-01536.
  - `wlan0` works and scans (self-managed, country US; 2.4, 5 and 6 GHz enabled). 5/6 GHz reception isn't confirmed yet.
  - The firmware waits for a **QDSS config** before init (infiniti 0065/0066), so `qdss.cfg` is required.
- Bluetooth: WCN7860 on GENI UART `1994000.serial` at 3.2 Mbaud through the WCN PMU. `hci_uart` + `btqca` work with no
  kernel changes, firmware `BTFW.BRAHMA.2.0.1-00204`.
- Battery over pmic-glink **via SoCCP** (`PMIC_RTR_SOCCP_APPS`), works with 0028:
  - `qcom-battmgr-bat` reports %, voltage, current, temperature and health; `-usb` reports SDP 4.757 V; UCSI `port0`.
  - The battery values look like mV/mA while the USB ones are µV/µA: **check the battmgr scaling**.
  - Stock design capacity is 13380 mAh.
- ADSP boots from stock split `adsp.mdt` + `.bNN` (firmware-name override): GPR, glink, q6apm and LPASS macros up.
- SoCCP: `qcom_q6v5_pas` attaches to the running SoCCP; no firmware is loaded.
- GPU: Adreno 840 `qcom,adreno-44050a01` (gen80200) binds and loads sqe/gmu/aqe ("GMU firmware v5.3.39").
  - `MSM_GET_PARAM`: chip_id 0xfc44050a31, gmem 18 MiB, max_freq 1.2 GHz, the timestamp advances. So the GPU powers up.
  - The `vdd`/`vddcx` supplies are missing in the DT (dummy regulators).
- Audio: the RX/TX SoundWire controllers wait for the **LPASS LPI pinctrl** `pinctrl@7760000`
  (`qcom,sm8750-lpass-lpi-pinctrl`; module `pinctrl-sm8650-lpass-lpi` not loaded). The sound card
  (`qcom,kaanapali-sndcard`) says "WCD Playback: codec dai not found". One `qcom-apm CMD timeout` was seen.
- Stock (from the LineageOS probe): a pogo keyboard (`tinno,pogo_keyboard`, `POGOPIN_KB.bin` from odm, a
  `pogo_wakeup` input); `canoe-mtp-snd-card` CODEC_DMA LPAIF_RXTX RX 0-3/5 playback; rfkill `bt_power`.
- Lid switch: TLMM98 (not yet in the DTS). It reads `in high` with the cover open.
- Remoteprocs:
  - adsp and cdsp run on stock (split `.mdt`/`.bNN` files in `modem_a:/image`);
  - **soccp is started by the boot chain** (it has its own `soccp_a` partition);
  - spss is offline;
  - SM8850P has **no modem**.

### Firmware locations (the manifest has 21 files)
- GPU `gen80200_{sqe,gmu,aqe,zap}` and `vpu40_2v.mbn`: `/vendor/firmware`.
- ADSP/CDSP, jsn and Wi-Fi: `/vendor/firmware_mnt/image` (the modem_a FAT partition).
  - Wi-Fi is under `peach/`: `amss20.bin`, `phy_ucode20.elf`, `aux_ucode20.elf`, `regdb.bin`, `bdwlan.*`.
- **Bluetooth: `brhbtfw20.mbn` and `brhbtnv20*.bin`** in `/vendor/bt_firmware/image` (bluetooth_a).
  - btqca asks for `gngbt*`, so the manifest renames them (`qca/gngbtfw20.mbn`, `qca/gngbtnv20.bin` from `brhbtnv20_in.bin`).
- Touch: `/odm/firmware/tp/25926/FW_NT36536_HUAXING.img`, which becomes `novatek/novatek_nt36536_fw.bin`.
- `tfa98xx.cnt` (speaker protection) and the pen firmware `mt5806_firmware.bin`: `/odm/firmware`.
- The destination path convention is `qcom/kaanapali/OnePlus/iceland/` (pmOS style).
- The Bluetooth address is in the stock prop `persist.vendor.service.bdroid.bdaddr`. It is redacted in the repo, and will be used for the real BD address in Phase 6.

### Thermal (found by the Linux survey)
- Upstream kaanapali CPU zones had only 120/125 °C trips. **Fixed (0023):** every CPU zone now has the stock
  105/112/114 °C passive trips with cpufreq cooling maps (the LLC zones get 112/114).
- Under 8 pinned busy loops: 67–78 °C at the start, 105 °C within about 4–6 s, then **held at 105–106 °C** at about
  1.9–2.5 GHz (little) and 2.9–3.1 GHz (big). Keep the trips in every kit.
- ADC5 Gen4 works (config fixed), but the Pad 4 DTS has **no ADC channels or ADC-TM zones** for the board
  thermistors (skin, XO, PA…). The stock DT has them, and skin-based throttling needs them (Phase 5). Stock also
  has OnePlus skin "gears" (`odm/etc/temperature_profile/sys_thermal_control_config.xml`).
- Stock CPU zones use 105 °C (HAL, passive), 112 and 114 °C (kernel passive, mapped to CPU pause), 125 °C (hot) and 135 °C.
  - Cooling devices: cpufreq-cpu0 (27 states), cpufreq-cpu6 (28), pause-cpuN, display-fps, gpu, ddr, ufs.
  - The CPU zones read 66–80 °C under DSU load.
  - No kaanapali mainline tree (infiniti, XEC) has passive CPU trips, so the stock table is the only reference.

### Other facts from the PC's older notes
- **No modemst/fsg/fsc** partitions.
- **No L3K rail** (stock `drop-l3k`), so the WCN7860 PDC mode must not be voted.
- The IN variant uses QBG plus a Maxim DS28E30 1-wire battery authenticator. The EU variant uses an I2C bq27541.
- Hall sensor bu52053nvx on TLMM98 → `SW_LID`.
- SSC sensors: bmi3x0, ak0991x, stk36c01 (ALS/RGB/proximity).
- NT36536 TDDI: touch must follow panel power and reset. Stock pulses reset low twice when gesture-wake keeps touch powered.
- Backup location on the PC: `C:\OnePlusPad4\backups\20260927-1933-unknown` (151 partitions plus GPT head and tail of every LUN). Stock package: `C:\OnePlusPad4\stock-11.A.38\`.

## 5. Research: what each reference project gave us

| Source | Use |
|---|---|
| **map220v/sm8850-mainline** `iceland-7.2` @bc3e5fc8 | The only public Pad 4 mainline work. DTS (1494 lines), DSI1, KTZ8869 driver, NT36536 panel and touch, TFA9865, OPLUS battmgr, GMU address fix, Gunyah-crash reservations. Gaps: no lid switch, empty `/chosen`, no msm-id, no camera/video/DP/sensors, no ramoops. |
| map220v/iceland-firmware | File name list (no licence). Its `gngbt*` names differ from the real `brhbt*`. |
| **infiniti-mainline/linux** (OnePlus 15, same SoC, what pmOS/Nura uses) | 138 SoC commits on 7.3-rc4: carve-outs, remoteproc/GPR fixes, GPU, gpucc/gcc/dispcc fixes, crypto/TRNG, Iris, CAMSS, qmp-combo + DP, ADC5 Gen4, SMMU, UFS lanes, qcomtee, DSC 1.2, TFA9866, OPLUS battmgr. **Primary base, as the user asked.** |
| **infiniti-mainline/u-boot** `main` | Kaanapali U-Boot. Its key feature is the of_fixup that passes ABL's memory map to the OS. The OnePlus 15 boots with `bootcmd=run userdata_blkmap; bootefi bootmgr; fastboot usb 0` and a disk image in userdata. |
| infiniti-mainline/firmware-oneplus-infiniti, audioreach-topology, minkipc | Firmware packaging layout; the `.m4` topology template; the QTEE supplicant (needs the `/data/vendor` TA files, which are lost when userdata is wiped). |
| pmaports / wiki.nura.eco | pmaports has **no** `device-oneplus-infiniti` (checked by the PC through the GitLab API), so we write `device-oneplus-iceland` from scratch. The wiki page was saved by the user (see the Nura row below). |
| **troikoss/gts9wifi-fedora** + wiki (Tab S9, SM8550, Fedora) | The method: find the **missing layer** first (kernel driver / firmware / userspace bridge / app). Also: `BT_HCIUART=m` and `ATH1xK=m` so they probe after the rootfs firmware; exact firmware names; sleep hooks in `/usr/lib/systemd/system-sleep`; UCM volume cap until speaker protection works; installer safety; BD address via fdtput. |
| aaronsb/sm-x800-linux (Tab S8+, pmOS) | The `device-facts/` idea, firmware manifest TSV, distro-neutral split (ADR-004), `consoleblank=0`, `serialN` aliases, the dwc3 `power_lost` patch, root by partlabel, and the lesson that simplefb needs clocks and power-domains. |
| Project-Silicium/Mu-Silicium | Kaanapali UEFI for the OnePlus 15. Reference memory/config maps. It was the fallback if U-Boot failed; **dropped in plan v3** because U-Boot works. |
| PrestarLin/oneplus15-mainline | CI pattern: arm64 runner, merge_config, grep the config, BUILD_INFO. Lesson: booting with a size-0 `/memory` crashes into **EDL** — never boot ABL-direct without the real memory map. |
| [Bentlybro/gts6l-mainline-linux](https://github.com/Bentlybro/gts6l-mainline-linux) (Galaxy Tab S6, SM8150; blog on bentlybro.com) | Samsung ABL → Aloha UEFI → systemd-boot: does **not** replace U-Boot for us (OnePlus ABL has fastboot). Lessons: firmware carve-outs must be HLOS-owned per the stock map; PSCI off/reset may hang (PS_HOLD); simpledrm-only as the display fallback; Fedora sleep/RPM traps. See [research/gts6l-tab-s6.md](research/gts6l-tab-s6.md) |
| Nura wiki: OnePlus 15 (oneplus-infiniti), rev 107471 (saved by the user; the cloud can't reach it) | Full page + a Pad 4 mapping in [research/nura-oneplus-15.md](research/nura-oneplus-15.md). OnePlus 15 at 7.3-rc4: screen/touch/GPU/Wi-Fi/BT/NFC/battery/flash work; USB/OTG only with external PD; audio, cameras, sensors, DP, haptics broken. Pad 4 actions: flash LED node, SW_LID, no haptics (disabled in stock), OTG power test, qdss.cfg, write device-oneplus-iceland ourselves, be first on kaanapali audio |
| LeeSiWal/y700-linux (Lenovo Y700 gen 4, same SoC tablet) | Address checks (GMU @3d37000 matches map220v). The thermal trap. The hexagonrpcd `get_in_bufs2` gap. Its BT firmware is also `brh*`. |
| skb8/linux-sm8750 | Low value. Main lesson: starting the ADSP killed simplefb on SM8750, so start remoteprocs one at a time. |
| torvalds/linux, u-boot/u-boot, LineageOS mkbootimg mirror | Upstream bases and tools. |

## 6. Architecture and decisions

```
ABL (stock, untouched)
  -> U-Boot: boot_a later; RAM boot (`fastboot boot`) during bring-up
       iceland DTS, simplefb, UFS, keys, fastboot; cannot write storage
  -> blkmap userdata -> EFI boot manager -> systemd-boot/GRUB
  -> our kernel + our DTB + the distro's initramfs -> distro rootfs in userdata (Android erased; Phase 4, needs the user's OK)
```
- The OS lives in userdata as a whole-disk image (ESP + root), like the OnePlus 15 pmOS setup. U-Boot never writes it.
- Boot-critical drivers are built into the kernel: UFS, PHYs, clk/pinctrl/icc, simpledrm, ext4/btrfs/xfs/vfat, dm-crypt. So any initramfs, or none, reaches root.
- `BT_HCIUART=m` and `ATH12K=m`, so they probe after the rootfs firmware is available.
- `CONFIG_EFI_ZBOOT=n`.
- The DTB ships with the kernel package (`/usr/lib/modules/<kver>/dtb/`) and is picked up by the loader's `devicetree` line or by U-Boot's `fdtfile=qcom/kaanapali-oneplus-iceland.dtb`.
- Firmware is extracted from the user's own tablet; one tree serves all distros.
- Device files (UCM, udev, units) go in one FHS tree under `/usr/lib`.
- Per distro, only three things differ: the package wrapper, the initramfs hook, and the loader entry.

**Order of work (plan v3):**

| Phase | Work |
|---|---|
| 1 | U-Boot (done) |
| 2 | First Linux shell from RAM (done) |
| 3 | Core hardware over RAM boot (**mostly done**: thermal ✅, native display ✅, touch firmware ✅, Wi-Fi ✅, BT ✅, battery ✅; open: UFS read-only mount, a real touch, lid, BD address, the firmware extractor) |
| 4 | pmOS install (first write to the tablet; needs the user's OK) |
| 5 | GPU, audio, suspend, sensors, video, DP, cameras, pen |
| 6 | Upstreaming, alongside phases 3–5 |
| 7 | More distros |

**Decisions made along the way:**
- Rebased from Linux 7.2 + map220v to **7.3-rc4 + infiniti + the ported Pad 4 series**. infiniti already has most SoC work; porting forward is smaller than backporting about 100 commits.
- The Pad 4 panel was added to the **upstream** `panel-novatek-nt36536` driver (by Pengyu Luo) as `csot,xn251` with `init_sends_pps`, instead of map220v's own driver.
- map220v's "DSI sync on DSI0" commit was dropped, and the native display works without it (upstream sync on DSI1).
- battmgr uses infiniti's OPLUS support with `oneplus,iceland-pmic-glink`.
- The modem remoteproc and smp2p-modem nodes are deleted.
- U-Boot packaging is header v4 with kernel = gzip(u-boot.bin), so the DT stays inside the gzip stream.
- Linux is started by U-Boot through **EFI** (`bootefi`), not bootm.
- The first Linux userspace is a tiny busybox initramfs with a USB NCM network and HTTP survey pages, not pmOS yet: fewest moving parts.

## 7. Kernel: iceland-linux

### 0002-iceland series (21 patches)
- 0001–0018: map220v, ported with the original authors. The port log has one row per original commit.
  - DSI1 nodes, Pad 4 DT, sm8850.config;
  - KTZ8869 driver + nodes;
  - DPU compressed-width fix;
  - panel (our commit, NEW: into the upstream driver) + node;
  - touch driver + node;
  - GMU address, cache info;
  - battmgr OPLUS (ported onto infiniti);
  - TFA9865 driver + sound nodes;
  - usb-role-switch removed;
  - llcc_lpi reserved (Gunyah crash); adsp_mhi and global_sync reserved.
- 0019 (ours): match the upstream NT36536 driver (`csot,xn251`, vsp/vsn).
- 0020 (ours): drop the modem remoteproc.
- 0021 (ours): **describe ABL's splash framebuffer.** Current content:
  ```
  chosen { #address-cells=<2>; #size-cells=<2>; ranges;
    framebuffer@fc800000 { compatible="simple-framebuffer"; reg=<0 0xfc800000 0 0x2b00000>;
      width=<3392>; height=<2400>; stride=<(3392*4)>; format="a8r8g8b8";
      clocks = GCC_DISP_HF_AXI_CLK, DISP_CC_MDSS_{AHB,MDP,MDP_LUT,VSYNC,ESC0,ESC1}_CLK;
      power-domains = <&rpmhpd RPMHPD_MMCX>, <&rpmhpd RPMHPD_MXC>, <&dispcc DISP_CC_MDSS_CORE_GDSC>;
      required-opps = <&rpmhpd_opp_turbo>, <&rpmhpd_opp_turbo>;
      memory-region = <&cont_splash_mem>; }; };
  reserved-memory { cont_splash_mem: splash-region@fc800000 { reg=<0 0xfc800000 0 0x2b00000>; no-map; }; };
  ```
  The DSI byte and pixel clocks were removed: they were enabled as orphans at rate 0.
- The framebuffer power-domains are now MMCX, **MX**, MXC and the GDSC, with TURBO required-opps on the three rails.
- Test 7b builds were A `7.3.0-rc4-iceland-00159-g66113519fa7f` and B `…-00160-g1a9d60630ec7` (A + hack). Later kernels are built by the PC from the queue (0022–0028); see `relay/results/pc-*` for exact versions.

### 0022–0028 (PC session, 2026-09-28)
- 0022: the framebuffer also holds `DISP_CC_MDSS_CORE_INT2_GDSC` (no required-opp).
- 0023: CPU thermal trips mirroring stock.
- 0024: `ktz8869_iceland` programs ABL's values per IC.
- 0025: `drm/msm/dpu` also keeps a video-mode boot splash.
- 0026: `drm/msm/mdss` attaches all power domains of the MDSS.
- 0027: the Pad 4 MDSS lists both GDSCs.
- 0028: `soc: qcom: pmic_glink` attaches a channel that comes up before the platform device.
  - The first fix (return -EPROBE_DEFER) was wrong: a failed rpmsg probe destroys the endpoint, and SoCCP never
    reopens the glink channel.
- Config additions: `CONFIG_GPIO_SHARED_PROXY=y`, `CONFIG_QCOM_SPMI_ADC5_GEN3=m`, `CONFIG_QCOM_SPMI_ADC_TM5_GEN3=m`.

### Config
- `distro-neutral.config`, 74 lines:
  - EFI stub, UFS/fs/dm built in;
  - simpledrm + fbcon;
  - cgroups/namespaces, SELinux + AppArmor + Landlock + Yama, BPF, nftables;
  - zram as a module; BT_HCIUART and ATH12K as modules.
- `required.config`: 16 symbols that must end up set, or the build fails.

## 8. U-Boot: iceland-u-boot

- Normal environment (`iceland.env`): `bootcmd=run userdata_blkmap; bootefi bootmgr; fastboot usb 0`, `fdtfile=qcom/kaanapali-oneplus-iceland.dtb`. stdout goes to serial and vidconsole; stdin to serial and button-kbd.
- Diagnostic environments:

  | Env | What it does |
  |---|---|
  | A | reset (proves U-Boot runs) |
  | B | white screen (proves the framebuffer) |
  | C | fastboot |
  | D | normal boot |
  | E | info dump |
  | **L** | fastboot, then Linux through EFI |

- L's cmdline: `console=tty0 log_buf_len=4M earlycon=efifb keep_bootcon ignore_loglevel loglevel=8 clk_ignore_unused pd_ignore_unused regulator_ignore_unused rdinit=/init efi=debug`.
- L's `fastboot_bootcmd`:
  1. read the header v2 kernel and ramdisk sizes at 0xc6000008 and 0xc6000010;
  2. kernel at 0xc6001000; ramdisk and dtb follow, each rounded up to 4 KiB;
  3. `bootefi kaddr:ksz raddr:rsz daddr`.
- `fastboot oem console` returns the U-Boot log (CONSOLE_RECORD).
- The current diag L image is `diag-L-efi.img`, sha256 `e6ce0748…e696`, built from iceland-u-boot c9aeab2.

## 9. Linux RAM-boot debug image (iceland-mainline `tools/linux-ram/`)

- Command: `build.sh KERNEL_DIST KERNEL_OUT MKBOOTIMG_DIR OUT_DIR`.
- **Debug DTB:** the Pad 4 DTB (the script checks the framebuffer node is present) plus these edits:
  - `usb@a600000` set to `dr_mode=peripheral`, `usb-role-switch` removed;
  - disabled: MDSS, GPU, the remoteprocs d00000/6800000/26300000, pcie@1c00000, pmic-glink, both KTZ8869 nodes;
  - added ramoops@ff300000 (reg 0x400000, record 0x80000, console 0x200000, pmsg 0x80000).
- **Initramfs:** busybox-static 1.36.1-6ubuntu3.1 arm64 (sha256 d96535e0…eafc pinned; source on Launchpad).
  - `init` mounts proc, sys, dev, configfs, debugfs and pstore. It keeps a timeline every 5 s and saves dmesg copies at 20, 45 and 90 s.
  - USB NCM gadget 18D1:4EE1, serial `iceland-debug`.
  - usb0 is 172.16.42.1; udhcpd hands out 172.16.42.2.
  - busybox httpd on port 80, and telnetd (debug shell).
  - It never mounts UFS.
- **CGI pages** (`/cgi-bin/<name>`, timed):
  - logs: dmesg, timeline, pstore;
  - device: info, unbound, deferred, buses, irq;
  - power and clocks: genpd, interconnect, regulators, clocks, power, thermal;
  - pins: gpio, pinctrl;
  - plus reboot.
  - Headers use **CRLF** (needed for Windows PS 5.1).
- **Boot image:** header v2, page 4096, base 0xa6400000, kernel_offset 0x8000, ramdisk_offset 0x04000000, dtb_offset 0x03f00000.
- **Tablet script `run-linux.ps1`:**
  1. Checks the sha256 and boot header of both images.
  2. adb or fastboot, then `fastboot boot diag-L-efi.img` (U-Boot).
  3. `fastboot boot linux-iceland-debug.img` into U-Boot's fastboot.
  4. Waits for the USB network, then downloads every page with a raw TCP HTTP client.
  5. Asks what the screen shows: text / black / **white** / …
  6. Reboots over HTTP, records the boot reason after the reboot, and zips everything as `linux-<date>.zip`.
- **Options added by the PC** (`build.sh` env vars; `/etc/kit.conf` read by `init`):

  | Option | What it does |
  |---|---|
  | `MODDIR` / `MODLIST` | modules in dependency order in `/lib/modules/NNN-*.ko` (`modules-debug.list` = default set) |
  | `FWDIR` | local firmware tree into the initramfs; never shared, noted in BUILD_INFO |
  | `WIFI=1` | keeps PCIe0 on in the debug DTB |
  | `ENABLE=` | nodes kept enabled |
  | `ADSP_MDT=1` | ADSP firmware-name override |
  | `CPULOAD=1` | the guarded CPU load test (refuses without passive trips, aborts at 110 °C) |
  | `DRMDEBUG=1` | drm.debug for 40 s |
  | `PMSG_ANDROID=1` | pmsg-only ramoops at stock Android's zone 0xa_ffe00000 |
  | `IWDIR` | pinned Ubuntu `iw`, via `fetch-iw.sh` |
  | `EXTRA_BINS` | extra binaries (e.g. `msmparam`) |
  | `KITCONF` | the `/etc/kit.conf` to embed |

  `kit.conf` keys: `WATCHDOG`, `AUTOREBOOT_AT`, `LATE_MODS`/`LATE_AT`, `BTSTATE`, `IWSCAN_AT` (no names),
  `ADSP_START_AT`, `GPU_OPEN_AT`, `REBOOT_MODE`, `BATTSTATE`, `AUDIOSTATE_AT`.
- **`init` monitors:**
  - the **scanout sampler**: dispcc GDSCRs, DPU INTF_1/INTF_2 frame and line counters, MDP `INTR_STATUS`
    vsync/underrun, and `iceland-scan: verdict …` lines;
  - touch IRQ counts, the lid level, regulator snapshots at 20/50 s, and `ignore_loglevel=N` + console loglevel 4.
    The console loglevel matters: diag L's fixed cmdline has `ignore_loglevel keep_bootcon`, so a debug flood draws
    on two big consoles until the watchdog resets.
- **Pages added:** `drm`, `extra`, `more` (socinfo without the serial, remoteproc, BT, iw summary, power supplies,
  Type-C, IIO, GPU, audio), and `kmsg` (a live stream for up to 150 s).
- **Note:** U-Boot diag L uses its **own fixed cmdline**; the boot image cmdline is ignored. Kit variants therefore
  use initramfs files or `kit.conf`, not cmdline flags.
- **Packaging a kit:** `tools/linux-ram/package.sh KIT_DIR diag-L-efi.img README.txt A=<build.sh out>=<note> [B=…]`. It writes `linux-<label>.img`, `BUILD_INFO-<label>` and `run-linux.ps1` with the hashes and runs filled in, then zips everything.
- Linux test 7 debug image: sha256 `a82db7f8…0b3f`; DTB `2f3620e0…5a04`.

## 10. Tablet test history

| # | Test | Result |
|---|---|---|
| U1 | U-Boot, header v4 with gzip(nodtb) + DT appended | ABL says `Booting OKAY` but the screen stays on the fastboot logo: U-Boot died |
| D2 | Diag A/B/C/D, same packaging | All stuck. ABL drops the data after the gzip stream on v4, so U-Boot lost its DT |
| D3 | Packaging gzip(u-boot.bin) | **U-Boot runs.** A rebooted itself; B turned the screen white (framebuffer right); C showed U-Boot text and the gadget 18D1:D00D appeared (no Windows driver yet) |
| D4 | C/E/D, Windows driver bound to U-Boot's gadget | **Phase 1 done:** fastboot works, `oem console` log retrieved, UFS HS-G5 x2 and GPT read, DRAM matches the DT; normal boot falls back to fastboot |
| L1 | Linux through bootm | `XIP Kernel Image to c6001000`: the kernel ran in place from an unaligned buffer (arm64 needs 2 MB alignment), so there was no output. Fixed by booting through EFI |
| L2 | Diag L, bootefi | **Linux runs.** Text scrolled, then went black. USB NCM came up at ~30 s; the single report page timed out; the HTTP reboot worked |
| L3 | + regulator_ignore_unused, KTZ8869 disabled | White screen and no USB. The display pipeline was released |
| L4 | + DT framebuffer votes, ramoops | White or black. USB at ~37 s. **Every page failed** because of bare-LF CGI headers on PS 5.1 |
| L5 | Full survey (16 pages) | No oops. simpledrm voted MMCX **SVS** under the 650 MHz MDP, and DSI clocks were orphans. Also found the TFA9865s, unbound modules and the thermal trips |
| L6 | MMCX TURBO, no DSI clocks | White at 20–30 s. **MXC off** after rpmhpd sync_state (~22 s); `qnm_mdp` interconnect vote 0 |
| L7 | + MXC TURBO (iceland-linux 2728bb9) | Kit sent, then superseded before it was run: the stock data showed dispcc needs **MX** |
| L7b | A = MMCX+MX+MXC TURBO (fe964f7); B = A + sync_state disabled (`debug-patches/0001`) | **Both white.** Rails all at 384 and bandwidth kept, but `disp_cc_mdss_core_int2_gdsc` off-0. Rails and bandwidth ruled out |
| pc-001 | + framebuffer holds INT2 (debug prints + scanout sampler) | **Fixed**: INT2 held, scanout alive at 120 Hz through ≥75 s; the control run lost INT2 at 15.45 s via dispcc sync_state |
| pc-002/003 | CPU passive trips + cooling maps, then the stock 105/112/114 values; load test | Held at 105–106 °C under full load; display alive |
| pc-004 | modules in the initramfs | All load. Touch waits for the panel. ADC5 Gen4 needed a config fix. `qce-core` ends the qnoc sync_state wait (1 underrun window, then clean) |
| pc-005..007 | native display (MDSS + dual DSI + NT36536 + KTZ8869) | **Works at 120 Hz** after 0024–0027 + the GPIO shared proxy |
| pc-008 | touch firmware (converted stock image) | SRAM download ok, `fw_ver=0x15`, touch + pen input devices; no touch event tested |
| pc-009 | Wi-Fi (ath12k WCN7860) | `wlan0` up after `qdss.cfg`; loading early reset the tablet in 2 runs (open) |
| pc-010 | 5-run session | **BT works, Wi-Fi scan works**, SoCCP attaches, ADSP boots, pmic-glink race found, GPU binds; the early Wi-Fi reset not reproduced |
| pc-011 | 5-run session | **Battery data**, GPU powers up (`msmparam`), audio up to the LPI pinctrl; warm reboot isn't possible |

## 11. Problems hit and how they were solved

| Area | Problem | Fix |
|---|---|---|
| Capture | `/proc/device-tree` is a symlink | read `/sys/firmware/devicetree/base` |
| Capture | `od -tx4` swapped the big-endian cells | `od -tx1` (capture 1 values decoded by hand) |
| Capture | pinctrl names with `:` broke `adb pull` on Windows | sanitize the names, transfer with tar |
| Capture | `adb` "not recognized as a cmdlet" even next to the script | look up an explicit path: script dir, cwd, PATH |
| Capture | identifiers in the output | serial and MAC redaction; `private\` folder never uploaded; one received by mistake was deleted |
| Build | switching branches in the source tree broke a running build | build in a detached worktree |
| Build | `format-patch -o` path is relative to `-C` | use absolute output paths |
| Build | `pipefail` + `grep -q` gives a false failure (SIGPIPE) | rewrote the check |
| Build | `prepare.sh` in a git worktree tried to re-clone | use `git clone --shared` for verification |
| Build | `pkill -f` killed its own shell | PID files |
| U-Boot | the DT appended after the gzip stream is dropped by ABL | kernel = gzip(u-boot.bin) |
| U-Boot | Windows showed U-Boot's gadget as "Error" | use PID 0xd00d and bind the Android bootloader driver to that instance |
| Script | the mock took a forced reboot as "U-Boot runs" | added the question "did it restart BY ITSELF?" |
| Linux | bootm XIP from an unaligned buffer | EFI boot (diag L) |
| Linux | QEMU EFI smoke test ran out of memory with 3 GB | use 8 GB |
| Linux | the sandbox blocks private IPs | the mock server uses 127.0.0.1; `icetest` cmdline gives a virtual NIC |
| Linux | PS 5.1 HttpWebRequest rejects bare-LF headers | CRLF headers + a raw TCP client |
| Display | black: unused regulators and the backlight switched off | `regulator_ignore_unused`; KTZ8869 disabled |
| Display | white: pipeline released | framebuffer node with clocks, GDSC and rail votes |
| Display | white: MMCX at SVS under the 650 MHz MDP | TURBO |
| Display | white at ~22 s: MXC dropped by sync_state | MXC TURBO vote (L7), not the real cause |
| Display | white right after the text stops: dispcc genpd sync_state powers off INT2 (ignores `pd_ignore_unused`) | hold INT2 (0022; MDSS 0026/0027) |
| Display | MSM DRM reset the video-mode splash | 0025 |
| Display | KTZ8869 master deferred forever with no reason printed | `CONFIG_GPIO_SHARED_PROXY=y` (shared HWEN) |
| Display | ABL's KTZ8869 values differ from the driver's | 0024: program ABL's values |
| Wi-Fi | stuck after `qdss.cfg: -2` | ship stock `qdss_trace_config_v2.cfg` as `qdss.cfg` |
| Wi-Fi | console flood, then watchdog reset | `ignore_loglevel=N` + console loglevel 4 in init |
| Battery | pmic-glink channel lost in a probe race (SoCCP comes up instantly) | 0028: attach the early channel in `pmic_glink_probe()` |
| Thermal | load-test guard checked only trip 0 | check every passive trip |
| Config | ADC5 Gen4 driver never enabled | cc85322 |
| Script | no "white" choice in the screen question | added `w` |

## 12. Lessons and traps

- ABL accepts `fastboot boot` of header v4 images, so the whole bring-up can happen in RAM. Android stays intact and a kernel can be tested in about a minute.
- Header v4 packing: a DT appended after the gzip kernel is lost, so keep the DT inside the gzip.
- On arm64, start Linux from U-Boot with **bootefi**: the EFI stub relocates the kernel. `earlycon=efifb` gives output from the first line.
- **simple-framebuffer on kaanapali** needs all of these, or the display is released or underpowered:
  - the display clocks;
  - **both** MDSS GDSCs (`MDSS_CORE` and `MDSS_CORE_INT2`);
  - MMCX + MX + MXC at TURBO (650 MHz MDP).
- **genpd provider sync_state (`of_genpd_sync_state`) ignores `pd_ignore_unused`.** It powers off every domain
  nobody holds as soon as the provider's last consumer probes. Anything ABL leaves on without a DT consumer will be
  cut. Look for this first when something dies right after a probe.
- rpmhpd's sync_state runs early (~11.5 s); qnoc's runs once `qce-core` binds, or never. simpledrm has no
  interconnect support, so the MDP bandwidth depends on other voters until MSM DRM takes over.
- **Log, don't look:** kits run unattended. Put the state in dmesg and `timeline` (scanout counters, `iceland-*`
  lines), and fetch late pages.
- Stock names win: BT `brhbt*`, Wi-Fi BDF from **odm**, `qdss.cfg` required.
- Windows PowerShell 5.1: use CRLF HTTP headers or a raw socket client. Some Windows PCs have no `adb` on PATH.
- Never boot ABL-direct without the real `/memory`: a size-0 memory node leads to EDL (PrestarLin).
- Thermal: add passive cooling before load (Y700: 100 °C in 2 s).
- Starting the ADSP may kill simplefb (SM8750 report). Enable remoteprocs one at a time.
- Bluetooth firmware is `brhbt*` and btqca loads it under those names. Wi-Fi uses the ELF BDF `bdwlan.elf` from odm (board_id 0xff).
- A distro loads ath12k early (udev). Until the early-load reset is understood, load it late (a service after USB).
- The userdata raw backup is FBE-encrypted, so the `/data/vendor` TEE files must be copied at file level before Android is erased.
- UFS LUN order can change between boots: always mount by partlabel.
- troikoss rule: find the missing layer first (driver / firmware / userspace bridge / app).

## 13. Current state, open issues, next steps

**State (2026-09-28 evening, all over RAM boot, nothing written to the tablet):**
- ✅ U-Boot; Linux 7.3-rc4 from RAM through EFI; USB NCM + survey pages.
- ✅ Display: ABL splash kept, then **native MSM DRM at 120 Hz**; KTZ8869 backlight.
- ✅ CPU thermal (stock trips, tested under load).
- ✅ Touch firmware runs (touch and pen devices registered; a real touch isn't confirmed yet).
- ✅ Wi-Fi (`wlan0`, scan), ✅ Bluetooth (`hci0`), ✅ battery/USB data over pmic-glink (SoCCP).
- ✅ ADSP boots, SoCCP attaches, the GPU powers up.
- ⚠️ Audio: stops at the LPASS LPI pinctrl / SoundWire; no card yet.

**Open issues:**
1. **Early Wi-Fi load resets the tablet**, intermittently (2 resets, 11 clean runs; cause unknown). The reset reason is
   captured from the bootloader log.
2. **battmgr units:** the battery looks like mV/mA while USB is µV/µA. Check the scaling for the SoCCP firmware.
3. **144 Hz** is pruned (pixel clock 1261 MHz). It needs stock per-rate porches / DFPS.
4. **qnoc sync_state** drops boot bandwidth once `qce-core` binds (one underrun window under simpledrm). Native MSM DRM
   votes its own bandwidth, so this matters only for the simpledrm fallback.
5. GPU `vdd`/`vddcx` supplies are missing in the DT.
6. No board-thermistor ADC channels / ADC-TM zones (skin temperature) yet.
7. pmsg/ramoops don't survive (PS_HOLD hard reset).

**Next steps:**
1. **Audio:** load `pinctrl-sm8650-lpass-lpi` (LPASS LPI pinctrl) → SoundWire → WCD9395 → sound card. Then an
   AudioReach topology (the infiniti `.m4` as the template) and UCM, with **volume capped** until TFA9865 speaker
   protection (`tfa98xx.cnt`) works. Nobody has kaanapali audio yet.
2. **Touch:** confirm real touch and pen events (needs a human touch, or an input-event log during a user session).
3. **GPU:** Mesa (freedreno/turnip) test; add the vdd supplies; XEC speedbin/opp-peak commits if needed.
4. **Small DT items:**
   - rear **flash LED** (pmh0101 flash-led, stock channel map);
   - **lid** gpio-keys `SW_LID` on TLMM98;
   - board thermistor ADC channels + ADC-TM zones from the stock DT;
   - no haptics (disabled in stock).
5. **BT address** from persist (stock prop `persist.vendor.service.bdroid.bdaddr`).
6. **UFS read-only mount** test, then the **firmware extractor** (from `firmware/manifest.tsv`; it can be tested on
   the PC's unpacked OTA).
7. **USB OTG** on battery and with external PD (on the OnePlus 15, OTG works only with PD).
8. **Phase 4 preparation** (needs the user's OK):
   - write `device-oneplus-iceland` from scratch (there's no OnePlus 15 package in pmaports);
   - file-level copy of `/data/vendor` + persist;
   - ath12k loaded late until the reset is understood.
9. Later: DP, cameras (sensors at i2c9 0x20/0x6c, CAMERA_ICP firmware), sensors (SSC via hexagonrpcd), suspend.

**Other notes:**
- The kernel CI workflow exists but is only run by hand. Kernels are built in the cloud container and on the PC (WSL).
- **Cross-session:** the user's local Windows Claude session can message this cloud session, but this cloud session **cannot reply**. The send is refused with "this cloud session cannot message other sessions yet". Hand-offs to the PC go through the **relay in this repo** (section 17).

## 14. How to reproduce the work (cloud)

```sh
# kernel
git clone git@github.com:mzakamin-hub/iceland-linux && cd iceland-linux
scripts/prepare.sh ../src                  # applies 159 patches, checks both tree hashes
scripts/build.sh ../src ../out             # -> ../out/dist/{Image,kaanapali-oneplus-iceland.dtb,BUILD_INFO}

# U-Boot
git clone git@github.com:mzakamin-hub/iceland-u-boot && cd iceland-u-boot
scripts/prepare.sh ../uboot && scripts/build.sh ../uboot ../ub-out
tools/diag/build-diag.sh ../uboot ../ub-diag   # -> dist/diag-{C,D,E,L}.img (L = Linux via EFI)

# debug Linux image
git clone git@github.com:mzakamin-hub/iceland-mainline && cd iceland-mainline
tools/linux-ram/build.sh ../out/dist ../out ../ub-diag/mkbootimg ../linux-ram
# kit: diag-L-efi.img + linux-iceland-debug.img + run-linux.ps1 (hashes filled in) + README.txt
```
Tools needed: clang/LLVM 18, aarch64-linux-gnu gcc (for U-Boot), dtc/fdtput, python3, dpkg-deb, gzip, zip.
On the PC (WSL) the kits are built with the scripts in `relay/results/pc-*/` (for example `build-pc.sh`,
`make-kit*.sh`), Android clang 22, and `MODDIR`/`FWDIR` etc. (section 9).

**User side (Windows):**
1. Unzip the kit into platform-tools.
2. Run `powershell -ExecutionPolicy Bypass -File .\run-linux.ps1` and type `RUN`.
3. Answer the questions and send back the zip.

**Recovery:** any reboot, or holding Power for about 15 s, returns to stock Android. Nothing is ever written to the tablet.

## 15. Conversation timeline

1. Started from a LineageOS prompt. The user redirected to mainline for the Pad 4 and shared the planning docs 00–03 and repo links.
2. Discovery of all the linked repos (map220v, infiniti, troikoss guide, aaronsb). The user asked for "planning only" while researching.
3. The user asked to build on the pmOS OnePlus 15 work, and chose U-Boot like the OnePlus 15. pmaports is to be read on the PC.
4. The target became "one mainline kernel for any rootfs". More sources studied: Mu-Silicium, PrestarLin, y700-linux, linux-sm8750.
5. The plan was accepted on condition of GPL-compliant private GitHub repos and no work on the PC. The user loaded DSU root, connected GitHub (`mzakamin-hub`) and created the three repos.
6. Capture script sent. Fixed the adb path. Three captures produced the device facts and the firmware manifest.
7. U-Boot bring-up: failsafe test, the stuck-on-logo diagnosis, diagnostic runs 2–4, the packaging fix. Phase 1 done.
8. The user asked whether one kernel for all distros is realistic. Answer: not as one binary, so plan v3 with tiers and upstreaming early.
9. Linux tests 1–6: XIP fix, EFI boot, black, white, the PS 5.1 header fix, full survey, MMCX then MXC votes. The user asked for full-log probing (done: 16 pages) and a "white" option (added).
10. The user asked for a changelog and an MD pointing to all repos (CHANGELOG.md, PROJECT.md).
11. A connection test came from the user's local Windows Claude session. The reply failed (see section 13). The PC session then pushed the relay protocol, the PC inventory and the stock display-power facts (commit 6bafce1).
12. Linux test 7 kit sent.
13. The user asked for this full knowledge file.
14. Stock data showed dispcc needs MX, so test 7b (A = MX vote, B = sync_state hack) was sent through relay 001. The
    PC ran it: both white.
15. The PC, asked by the user to iterate unattended, found the INT2 GDSC cause (pc-001). It then did CPU thermal
    (pc-002/003), modules (pc-004), the native display (pc-005..007), touch firmware (pc-008), Wi-Fi (pc-009),
    BT/scan/ADSP/SoCCP (pc-010), and battery/GPU/audio groundwork (pc-011).
16. The user asked to evaluate the Galaxy Tab S6 (bentlybro) method: keep U-Boot (`research/gts6l-tab-s6.md`).
17. The user uploaded the Nura OnePlus 15 page, mapped in `research/nura-oneplus-15.md`. Relay 002 sync sent.
18. The user asked to update this file with everything the PC did, and to make sure the PC session uses all of this knowledge (relay 003).

## 16. Environment notes (cloud session)

- The container is reclaimed when idle. Everything important is pushed to GitHub; `artifacts/` and the build trees are temporary.
- Some sites are blocked: gitlab.postmarketos.org, wiki.nura.eco (`*.nura.eco`). Private IPs are blocked from the sandbox.
- Session: `session_019xY37rECnXqaJ2NjLcnjJF`.

## 17. PC relay and what the PC session found

**The relay** ([../relay/README.md](../relay/README.md)) is how this cloud session hands work to the Claude session on the user's Windows PC.
- **Asking:** Mainline commits `relay/requests/NNN-slug.md` on `main`.
  - Frontmatter: `id`, `kind: tablet-run | pc-lookup`, `title`, and for tablet runs `bundle`, `bundle_sha256` and `results_dir`.
  - Bundles go on the orphan branch `relay-bundles`, or under `relay/bundles/` on `main` if a branch can't be pushed.
- **PC side:** `tools/relay/pc-watch.sh` polls `origin/main` every 90 s.
  - For `pc-lookup` it answers read-only and writes `relay/results/NNN-slug.md`.
  - For `tablet-run` it stages the bundle in `C:\platform-tools`. Since 2026-09-28 it also **runs the kit itself,
    unattended** (`run-kit-auto.ps1`), after checking the hashes and allowlists; see rule 11.
  - The PC also originates its own kits (`pc-NNN`), built in WSL, and records them in `relay/results/pc-NNN-*.md`.
  - It commits the survey pages into `results_dir` together with the result file, then messages Mainline.
  - Result `status`: `done`, `failed`, `declined` or `waiting-user`.
- The same rules apply: no flashing, allowlisted RAM boot only, no firmware or private data committed.

**What the PC has** ([../relay/PC.md](../relay/PC.md)):
- Windows 11 and WSL2 Ubuntu 24.04 with `gh` signed in. A LineageOS build often runs there, so heavy jobs need the user's OK.
- **Stock 11.A.38:** the full OTA and every partition unpacked, the stock GKI 6.12.58 kernel and modules. The firmware extractor can be tested against this without the tablet.
- DSU captures, including a merged stock DT and a screen-on regulator dump.
- Source trees: OnePlusOSS sm8850 modules and devicetree (OPD2514), the downstream kernel, LineageOS trees, and saved Nura wiki pages. The cloud can't reach wiki.nura.eco; the PC can.

**Research the PC added** ([../relay/results/000-pc-knowledge.md](../relay/results/000-pc-knowledge.md)):
- infiniti master and U-Boot main are unchanged from our pins.
- infiniti `vlinkz/development` has 2 extra commits: an IMEM syscon binding and kaanapali reboot mode.
- **Xlie-Electronic-Customs/linux** (XEC, the tree the Nura OnePlus 15 page links) has several useful commits:
  - OnePlus pmic-glink power supply and UCSI;
  - HV haptics for pmih0108;
  - GPU speedbin, QFPROM and opp-peak fixes;
  - SoCCP minidump and remoteproc elf64;
  - the eUSB2 repeater slew setting and the M31 config;
  - the dispcc MDP RCG no-park fix, which our queue already has.
- **pmaports has no OnePlus 15 package**, and the Nura wiki says "packaged = no". The OnePlus 15 wiki (kernel 7.3-rc4):
  - works: screen, touch, GPU, Wi-Fi/BT, NFC, battery, UFS;
  - partial: USB (only when externally powered);
  - doesn't work: audio.
  - Its firmware repo is `Xlie-Electronic-Customs/linux-firmware-oplus-infiniti`.
- Our ABL memory map also has a size-0 segment (#8). This is harmless through U-Boot EFI, but any direct-ABL boot must avoid it (the PrestarLin EDL lesson).

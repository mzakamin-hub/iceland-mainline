# OnePlus Pad 4 mainline Linux — knowledge base

This file holds everything learned and decided on this project up to **2026-09-28 evening** (it includes the PC relay
results pc-001..pc-015; both sessions keep it current, see relay 003). It is written so that a person or an
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
- **Target OS (plan v4, user's decision 2026-09-28): Fedora 44 Workstation (GNOME), aarch64**, installed into
  userdata, booted through U-Boot → EFI → GRUB with our `kernel-iceland` rpm. See [PLAN.md](PLAN.md) Phase 4.
- Other distros are later and optional (Phase 7): Arch Linux ARM and pmOS (renamed **Nura** on 2026-09-27; it needs
  our own device package), then Debian testing, Kali, latest non-LTS Ubuntu. Not supported: Debian stable and
  Ubuntu LTS (Mesa too old for the Adreno 840).
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

13. **Every hardware value comes from Pad 4 stock sources** (user, 2026-09-29). This covers sound (mixer
    paths, gains, volume caps), speaker and mic tuning (TFA9865 `tfa98xx.cnt`, stock UCM/mixer_paths/ACDB), brightness
    (KTZ8869 registers, curve, min/max), clocks and OPPs, GPU (OPP table, devfreq, zap), power (charging limits,
    regulators, idle and suspend), and thermals (trips, hysteresis, cooling steps).
    - **Allowed sources, in this order:** this unit's stock OxygenOS 11.A.38 (live DT captures, the OTA partitions on
      the PC: vendor, odm, `/odm/etc`, `/vendor/etc`); the user's LineageOS trees for the Pad 4 on the PC
      (`device/oneplus/iceland`, `sm8850-common`, the OnePlus SM8850 devicetrees/modules with the iceland overlays);
      the OnePlusOSS sources for OPD2514.
    - Values from other devices (the OnePlus 15, reference boards, upstream defaults) are allowed **only** as a
      labelled placeholder until the stock value is found.
    - Every such value in a patch or config names its source (file/node/property) in a comment or the commit message.
    - Mainline and the PC both follow this; the PC's automated loop (relay 012) too.

14. **Wi-Fi regulatory domain = US** (user, 2026-09-29): the owner is in Egypt, but the self-managed ath12k firmware
    refuses EG ("Failed to set the requested Country regulatory setting") and runs US/DFS-FCC, which enables
    2.4/5/6 GHz (6 GHz: 59 of 60 channels). The user decided: **don't investigate EG; use US**, so 6 GHz works with
    the same bands. `/etc/iceland/wifi-country` = `US` (installer and kits), applied by `iceland-wifi-country.service`.

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
- Partitions for dual boot: `recovery_a` (LUN 4 entry 27) and `recovery_b` (entry 70) are 100 MiB each; `boot_a` entry 12; `init_boot_a` 8 MiB; LUN 0: `super` entry 14, `userdata` entry 15 (235.9 GB).
- 68 stock reserved-memory nodes. Key ones:
  - `splash_region` **0xfc800000, size 0x2b00000**;
  - `llcc_lpi` 0xff800000;
  - `gunyah_hyp` 0x80000000;
  - `adsp_mhi` 0x82380000; `global_sync` 0xd7a00000 (both XN=2 in the hypervisor, so they must be reserved);
  - `hypervisor_extended_heap` 0xc3dd0000;
  - `mpss` (modem, unused on SM8850P).
- ramoops is placed at **0xff300000** (0x400000) in our debug DT. That space is inside the 0xe25a0000–0xff800000 segment, below llcc_lpi.
- U-Boot relocates itself to the top of RAM. Its **EFI runtime** region is 0xa_ffdc0000–0xa_ffdcffff (the EFI system
  table is at 0xa_ffdc8fc0), and its image and page tables are above that (boot-services memory, free after
  ExitBootServices). Its fastboot download buffer is at **0xc6000000**, 256 MiB.
- Stock Android (Lineage) puts a dynamic ramoops at 0xa_ffdc0000: 0x40000 console, then a 0x200000 pmsg zone at
  0xa_ffe00000, no ECC. The debug DTB can use only the pmsg zone (`PMSG_ANDROID=1`), because U-Boot's runtime region
  overlaps the console zone. Our reboots are PS_HOLD hard resets with a DDR cold init, so it has never survived.

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
- Audio (pc-012):
  - The LPASS LPI pinctrl (`pinctrl@7760000`, `qcom,sm8750-lpass-lpi-pinctrl`, module `pinctrl-sm8650-lpass-lpi`) lets
    the RX/TX SoundWire controllers probe once the ADSP runs.
  - The **WCD9395** codec (`qcom,wcd9395-codec`, `audio-codec` node) binds both SoundWire devices
    (`sdw:2:0:0217:010e:00:4`, `sdw:3:0:0217:010e:00:3`).
  - All six TFA9865 amps probe (mainline i2c 0 and 4, at 0x34/0x36/0x37).
  - The TX SoundWire logs "din-ports (4) mismatch with controller (6)" and "dout-ports (0) mismatch with controller (1)";
    the DT port counts are worth a check.
  - The card `qcom,kaanapali-sndcard` (model `OnePlus-Pad4`) has three links:
    - Primary MI2S Playback (cpu port 16): the six TFA9865s;
    - WCD Playback (RX_CODEC_DMA_RX_0, 113);
    - WCD Capture (TX_CODEC_DMA_TX_3, 120).
  - It fails with "tplg firmware loading `qcom/kaanapali/OnePlus-Pad4-tplg.bin` failed -2". An **AudioReach topology**
    is needed. Stock uses ACDB/AGM, so none exists.
  - **pc-017:** with upstream's Kaanapali topology (`linux-msm/audioreach-topology` 993a17d `SM8550-HDK.m4`, built as
    `OnePlus-Pad4-tplg.bin`, sha256 66e01a76…b81b) the card **registers**: `0 [OnePlusPad4]: kaanapali - OnePlus-Pad4`,
    PCMs MultiMedia1/2/6 playback (C0D0/C0D1/C0D5), MultiMedia3/4 capture (C0D2/C0D3), compress MultiMedia5 (C0D4),
    input "OnePlus-Pad4 Headset Jack". Nothing played yet.
  - One `qcom-apm CMD timeout [1001021]` is seen right after the ADSP comes up.
  - **Stock back ends** (odm `resourcemanager.xml` / `backend_conf.xml`, 11.A.38):
    - speaker → **TDM-LPAIF-RX-PRIMARY**, 48 kHz, 8 ch, 32 bit (6× TFA9865; the "TFA Stop" control takes 6 values);
    - V/I feedback → TDM-LPAIF-TX-PRIMARY, 8 ch;
    - handset ("receiver" profile) → MI2S-LPAIF-RX-PRIMARY, 2 ch; CPS feedback → MI2S-LPAIF-TX-PRIMARY;
    - headphones → CODEC_DMA-LPAIF_RXTX-RX-0; handset/speaker/headset mics → CODEC_DMA-LPAIF_RXTX-TX-3;
    - VA mics → CODEC_DMA-LPAIF_VA-TX-0.

    So the DT's speaker link (Primary MI2S RX) differs from stock. Mainline 7.3 has the TDM pieces: `q6tdm_ops`
    (2/4/8/16 slots, 16/32 bit), `sc8280xp.c` PRIMARY_TDM_RX_0 with DT slots, and AudioReach
    `MODULE_ID_AUDIO_IF_SINK` 0x0700117C (`PARAM_ID_AUDIO_IF_INTF_CFG`, TDM mode 0, tokens 262-276). The topology repo
    has no m4 macro for it yet.
- Rear flash LED (relay 002): `led-controller@ee00`, `qcom,pmh0101-flash-led`, with **two dies**:
  - warm/yellow on sources 1+4;
  - white on sources 2+3;
  - led-2 drives all four;
  - 500 mA torch, 2 A flash, 1.28 s.
- Cameras (relay 002), on CCI (stock `cci0..2` @941b000/941c000/941d000):
  - rear **SmartSens SC1320CS** (13 MP) at 0x6c, with actuator, EEPROM and PDAF;
  - front **SmartSens SC820CS** (8 MP) at 0x20, with EEPROM;
  - MCLK 19.2 MHz. Neither has a mainline driver.
  - Firmware: `/vendor/firmware/CAMERA_ICP.mdt`/`CAMERA_ICP_1.mdt` + `.bNN`.
- Stock (from the LineageOS probe): a pogo keyboard (`tinno,pogo_keyboard`, `POGOPIN_KB.bin` from odm, a
  `pogo_wakeup` input); `canoe-mtp-snd-card` CODEC_DMA LPAIF_RXTX RX 0-3/5 playback; rfkill `bt_power`.
- Lid switch: TLMM98, BU52053NVX hall output, active low (stock requests an edge IRQ "lid" on it; LineageOS DT uses
  `gpio-keys` SW_LID with debounce 15 ms). It reads `in high` with the cover open. **In the queue as 0030**
  (pc-019: SW_LID = 0 with the cover open; closing still to be tested; a `debounce-interval = <15>` is worth adding).
- Rear flash LED: **in the queue as 0031** (pc-019: `yellow:flash-0` / `white:flash-1` registered).
- Battery units: **0029** reports the Oplus gauge in µV/µA (pc-019: `VOLTAGE_NOW=3857000`, `CURRENT_NOW=435000`).
- **LineageOS session reference** (2026-09-28, `docs/reference/pad4-hardware-boot-partitions.md`, from the user's
  `C:\OnePlusPad4\knowledge\05-Hardware-Boot-Partitions-Reference.md`): identity/variants, boot chain, all 151
  partitions with never-write/back-up marks, firmware sources, every hardware block. New for mainline:
  - **144 Hz** stock per-rate porches per DSI link (120/144/90/60/50/48/30 Hz): hfp 50/32/210/50/210/210/50,
    hbp 52/20/160/52/160/160/52, hpw 32/16/80/32/80/80/32, vfp 26/26/26/2726/2010/2196/8126, vbp 272/52/52/272/52/52/272,
    vpw 2. 144 Hz hfp is **32** on 11.A.38 (OnePlusOSS 16.0.6.103 has 34). DFPS `dfps_immediate_porch_mode_both_hv_porch`;
    reference commit "qcom: display: Support per refresh rate H/V porch DFPS" in
    `mzakamin-hub/android_kernel_oneplus_sm8850-modules`.
  - `qcom,qup_uart@1990000` (QUP3 SE4, SPI 586, ttyHS5, wake byte 0xFD) is the **pogo keyboard** UART
    (`tinno,pogo_keyboard`), not Bluetooth (BT = 1994000). Pogo GPIOs: TX TLMM22, RX TLMM23, wake TLMM151, TX enable
    PMH0110_D gpio6, power PMH0110_F gpio12; `POGOPIN_KB.bin`.
  - KTZ8869 bias ENP TLMM14 / ENN TLMM15 only before EVT (PcbVersion < 24); this unit (PCB 0x28) sets the bias over I2C.
  - Battery variants: IN (this unit) = QBG gauge + Maxim DS28E30 on TLMM88 with `oplus,debug_bypass_ic`; EU = TI
    bq27541 @0x55. 80 W SUPERVOOC via 2× SC8547D (i2c12/i2c24 @0x6a), `vooc_project` 7.
  - WLAN stock DT: `drop-l3k`, `msix-match-addr = <0x3000>`. eUSB2 repeater stock device-mode override reg 0x57 = 0x03.
  - Panel vddio L12B needs **1.9 V** (the shared canoe dtsi caps it at 1.8 V).
  - Volume up may be `gpio-keys` on TLMM 101 in the canoe MTP base DT (verify).
  - ARB trap: before copy-partitions the inactive slot b held 11.A.32 firmware; now 40/40 identical on a/b. Never
    `set_active` to an unsynced slot. Tablet state: slot b = LineageOS test build, slot a = LineageOS build 3.
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
  - btqca (7.3) requests them **under the stock names**, `qca/brhbtfw20.mbn` and `qca/brhbtnv20.bin` (this unit uses the
    generic `.bin` NVM). The old `gngbt*` rename (from map220v's list) was wrong; the manifest was fixed in e3f0af0.
- Touch: `/odm/firmware/tp/25926/FW_NT36536_HUAXING.img`, which becomes `novatek/novatek_nt36536_fw.bin`.
- `tfa98xx.cnt` (speaker protection) and the pen firmware `mt5806_firmware.bin`: `/odm/firmware`.
- The destination path convention is `qcom/kaanapali/OnePlus/iceland/` (pmOS style).
- The Bluetooth address is in the stock prop `persist.vendor.service.bdroid.bdaddr`. It is redacted in the repo, and will be used for the real BD address in Phase 6.

### Thermal (found by the Linux survey)
- Upstream kaanapali CPU zones had only 120/125 °C trips. **Fixed (0023):** every CPU zone now has the stock
  105/112/114 °C passive trips with cpufreq cooling maps (the LLC zones get 112/114).
- Under 8 pinned busy loops: 67–78 °C at the start, 105 °C within about 4–6 s, then **held at 105–106 °C** at about
  1.9–2.5 GHz (little) and 2.9–3.1 GHz (big). Keep the trips in every kit.
- **Stock thermistor map** (live DT capture 2, ADC5 Gen4 `vadc@9000`) and stock policy:
  - `sys-therm-0` = `pmk8850_xo_therm` (0x44): trips 78/80 °C → CPU pause + cluster caps; 90 °C hot.
  - `sys-therm-1` = `pmk8850_xoagg_therm` (0x4b).
  - **`sys-therm-2` = `pmh0101_skin_therm` (0x144): the skin sensor**, userspace steps at 48/49/50/60/61 °C, 90 °C.
    It read 54 °C under DSU load.
  - `sys-therm-3..7` = `cam_flash` (0x145), `wlan` (0x146), `pa_therm_1` (0x147), `qtm` (0x14b), `pa_therm_2` (0x149).
  - `sys-therm-8` = `pmih010x_wls_therm`/`subboard_temp_adc` (0x274d).
  - `sys-therm-9` = `pmih010x_batt_therm` (0x2744).
  - `sys-therm-11` = `pmih010x_usb_therm` (0x2747).
  - `sys-therm-12` = `pmih010x_batt_therm_2` (0x274c; reads 95.7 °C, probably not fitted).
  - Other stock zones: `cpu-hw-trip-0/1` (LMh, 95 °C); BCL `pmh0101-bcl-lvl0..2`, `pmih010x-ibat-lvl0/1`,
    `pmih010x-bcl-lvl0..2`, `vbat`, `socd`; the Oplus virtual `shell_front/frame/back`; `chg_cp_therm`, `usb_therm`,
    `battery`.
  - Stock cooling devices: cpufreq-cpu0 (27) / cpu6 (28), cpu-cluster0/1, cpu-hotplug*/pause-cpu*, `gpu`/`kgsl` (17),
    `display-fps` (16), `panel0-backlight` (255), `ddr-cdev`, `ufs` (2), `cdsp*`.
  - The Pad 4 plan for all of this is PLAN Phase 5-PM A.
- ADC5 Gen4 works (config fixed), but the Pad 4 DTS has **no ADC channels or ADC-TM zones** for the board
  thermistors (skin, XO, PA…). The stock DT has them, and skin-based throttling needs them (Phase 5). Stock also
  has OnePlus skin "gears" (`odm/etc/temperature_profile/sys_thermal_control_config.xml`).
- Stock CPU zones use 105 °C (HAL, passive), 112 and 114 °C (kernel passive, mapped to CPU pause), 125 °C (hot) and 135 °C.
  - Cooling devices: cpufreq-cpu0 (27 states), cpufreq-cpu6 (28), pause-cpuN, display-fps, gpu, ddr, ufs.
  - The CPU zones read 66–80 °C under DSU load.
  - No kaanapali mainline tree (infiniti, XEC) has passive CPU trips, so the stock table is the only reference.

### Charging and USB-C power (stock live DT)
- **The stock OnePlus kernel stack does the fast charging; the SoCCP firmware does the basics.**
  - SuperVOOC: `oplus,vooc`, `vooc_power_max_w = 80`, `voocphy_support = 3`.
  - PPS: `oplus,pps_charge`, target 11 V, 5 A.
  - UFCS: `oplus,ufcs_charge`, 11 V, 6.1 A.
  - The OnePlus layers use **2× `oplus,sc8547d` charge pumps** on APPS I2C (12-006a and 24-006a; IRQ TLMM3 on one of them)
    plus `virtual_*` ICs over pmic-glink. None of this exists on mainline.
- `oplus,wired` normal PD/QC settings:
  - ICL 2 A; 5→9 V switch at vbatt 4.5 V;
  - input-power table 2.5 / 2.5 / 7.5 / 10 / 30 / 13.5 / 13.5 W;
  - cool-down tables at 5–9 V, 1.2–2 A; VBUS OV 11 V / UV 4.3 V.
- `oplus,dual_cells_protection`: min FCC 3400 mA, current limit 2.5 A, SOC-jump threshold 35. It's a **dual-cell
  pack**. The OnePlus kernel supervises it, so cell safety without that stack has to be confirmed (PLAN 5-PM C).
- Pen charging: `oplus,wls-tx-mt5806` at 25-002b (IRQ TLMM169, control GPIOs on PMIH010x), powered by the PMIH010x
  **hboost at 7 V** (`qcom,pen_is_supply_by_hboost`), plus `oplus,wireless_pen_glink` messages.
- The charger firmware log channel is `PMIC_LOGS_SOCCP_APPS` (`qcom,charger-ulog-glink`), useful for charging kits.
- The plan is PLAN Phase 5-PM C.

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
| [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) (the user's reference link) | Branches `iceland-7.1`, `iceland-7.2`, `iceland-7.2-rc2`. `iceland-7.2` is still **bc3e5fc8** (checked 2026-09-29), the exact commit our `0002-iceland` series was ported from (PORT-LOG in iceland-linux). Nothing new to take; recheck before each rebase. |
| [CodeLinaro `clo/linux-kernel/kernel-qcom`, branch `kaanapali`](https://git.codelinaro.org/clo/linux-kernel/kernel-qcom/-/tree/kaanapali) | Qualcomm's own mainline-based kaanapali integration tree (the Nura SM8850 page lists it as the community kernel). It's the reference for SoC features our queue lacks: BCL/thermal, audio (TDM/SoundWire/LPI), SoCCP/battmgr charge control, UCSI/altmode/DP, suspend/idle states, camera and video. **Blocked from the cloud container; the PC reads it (relay 010).** |
| [lore.kernel.org: `kaanapali`](https://lore.kernel.org/all/?q=kaanapali) | The upstream mailing-list record of kaanapali series. The cloud can't reach lore, but a web search found these 2026 series via the ratatoskr.run mirror: qcrypto + BAM v2.0.0 ([v2](https://ratatoskr.run/linux-devicetree/2026/05/9004753/t)), CAMSS RDI-only (CSIPHY/CSID/TFE, needs `qdss_debug_xo`; [v15](https://ratatoskr.run/lkml/2026/07/17287528/t)), CCI + CAMSS DT ([link](https://ratatoskr.run/linux-devicetree/2026/05/8036667/t)), GPU DT for the Adreno 840 (a8x, 3 slices; [link](https://ratatoskr.run/linux-arm-kernel/2026/07/17221530/t)), SoCCP DT (the RISC-V MCU for Type-C and charging; [v2](https://ratatoskr.run/linux-devicetree/2026/07/17234914/t)), and the earlier DT series (QUP serial, ADSP/CDSP + fastrpc/smp2p, audio, multimedia clocks; [v3](https://ratatoskr.run/lkml/2026/01/3369417/t)). Use it to see what's merged or in review before writing our own; the PC does a full sweep (relay 010). |
| map220v/iceland-firmware | File name list (no licence). Its `gngbt*` names differ from the real `brhbt*`. |
| **infiniti-mainline/linux** (OnePlus 15, same SoC, what pmOS/Nura uses) | 138 SoC commits on 7.3-rc4: carve-outs, remoteproc/GPR fixes, GPU, gpucc/gcc/dispcc fixes, crypto/TRNG, Iris, CAMSS, qmp-combo + DP, ADC5 Gen4, SMMU, UFS lanes, qcomtee, DSC 1.2, TFA9866, OPLUS battmgr. **Primary base, as the user asked.** |
| **infiniti-mainline/u-boot** `main` | Kaanapali U-Boot. Its key feature is the of_fixup that passes ABL's memory map to the OS. The OnePlus 15 boots with `bootcmd=run userdata_blkmap; bootefi bootmgr; fastboot usb 0` and a disk image in userdata. |
| [Xlie-Electronic-Customs/linux-firmware-oplus-infiniti](https://github.com/Xlie-Electronic-Customs/linux-firmware-oplus-infiniti) (OnePlus 15 firmware, the repo the Nura page links; `main` 7197ab48bccc, 2026-09-19; **no licence, no README**, so names and layout only, never redistribute) | 18 files plus linux-firmware-style `Makefile`, `copy-firmware.sh`, `dedup-firmware.sh`: `ath12k/WCN7860/hw2.0/{amss,aux_ucode,board,m3,regdb}.bin` + **`qdss.cfg`**, `qcom/gen80200_{sqe,gmu,aqe}`, and `qcom/kaanapali/OnePlus/Infiniti/{gen80200_zap,CAMERA_ICP,CAMERA_ICP_1,evass,vpu40_2v}.mbn` + `tfa98xx.cnt`. No audio topology, no ADSP/CDSP/SoCCP. Compared with the Pad 4 11.A.38 files by git blob hash (PC, 2026-09-28): only `qdss.cfg` (6245 B) and `gen80200_aqe.fw` are **identical**. Everything else differs (other versions, OnePlus 15-signed zap/ICP/EVA/VPU, a tfa98xx.cnt for other speakers: 6118 B vs the Pad 4's 3702 B). The Pad 4 uses its own stock files; this repo confirms the file set, the `qcom/kaanapali/OnePlus/<Device>/` layout, and that `qdss.cfg` is needed. |
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
| 2 | First Linux shell from RAM ✅ |
| 3 | Core hardware over RAM boot (**mostly done**: thermal ✅, native display ✅, touch firmware ✅, Wi-Fi ✅, BT ✅, battery ✅; open: UFS read-only mount, a real touch, lid, BD address, the firmware extractor) |
| 4 | **Fedora 44 GNOME install** (4a RAM rehearsal in progress; 4b packages; 4c image; 4d/4e writes need the user's OK) |
| 5-PM | **Sleep/standby (s2idle to AOSS sleep, ≤ ~1 %/h, lid/key/keyboard wake) + thermal matched to the Pad 4 (skin 48/50/60 °C steps, XO 78/80 °C, GPU, BCL, charging) + power management (PD charging safety, charge limit, OTG/host/DP alt mode, EAS, 60 Hz on battery, CDSP off, measured vs stock)**; thermal and charging safety gate the install |
| 4-DB | **Dual boot Android + Fedora** (option): U-Boot in `recovery_<slot>` (Power+VolUp / `adb reboot recovery` → Fedora; normal boot → Android); Fedora in a `fedora` partition carved from userdata (repartition + one Android wipe, user's OK) |
| 5 | Remaining hardware on Fedora (the PC's "B" order) |
| 6 | Upstreaming, alongside phases 3–5 |
| 7 | Other distros, optional |

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
  | `DT_DEL_NODES` / `DT_DEL_PROPS` | experiments: remove debug-DTB nodes / `node:prop` properties |
  | `LATE_MODS` / `LATE_AT` | modules held back and loaded at that uptime (in dependency order) |
  | `ALSADIR` | pinned Ubuntu `amixer` + libasound + ALSA config, via `fetch-alsa.sh` (read-only mixer listing) |

  `kit.conf` keys:
  - `WATCHDOG`: the busybox daemon on `/dev/watchdog0`, 60 s;
  - `AUTOREBOOT_AT`: sysrq reboot at that uptime, so every run returns to Android;
  - `BTSTATE`, `IWSCAN_AT` (scan summary: counts, frequency, signal; no names or BSSIDs);
  - `ADSP_START_AT`: ADSP firmware held under `/lib/firmware/late` until then, then `echo start`;
  - `GPU_OPEN_AT`: runs `msmparam`;
  - `REBOOT_MODE`: `/sys/kernel/reboot/mode`; `warm` has no effect here;
  - `BATTSTATE`, `AUDIOSTATE_AT`;
  - `DYNDBG`: `;`-separated dynamic-debug queries, re-applied after the late modules;
  - `PGLINK_UNBIND_AT` / `PGLINK_BIND_AT`: the pmic-glink hold/attach harness (pc-013);
  - `HEARTBEAT=N`: a kernel-log line every N s (10 s after 90 s), so a stream shows when the system stopped (pc-016);
  - `NET_FIRST=1` (+ `NET_WAIT`, `EARLY_MODS`): USB network before the module list; the modules load only once the PC
    reads `kmsgall` (or after `NET_WAIT` s). `EARLY_MODS` (e.g. `qcom-wdt`) load before the network (pc-016).
- **Page `kmsgall`:** `cat /dev/kmsg` (the whole log from its first line, then live, up to 900 s; kmsg record format
  `prio,seq,usec,flags;msg`). Opening it creates `/tmp/pc-stream` (what `NET_FIRST` waits for).
- **Runner hook:** `run-linux.ps1` calls an optional `After-Android` function once Android is back.
  `tools/relay/run-kit-long.ps1` uses it to:
  - save the reset lines of Lineage's `/proc/bootloader_log` (`reset-after.txt`); the full log stays private in
    `C:\OnePlusPad4\captures\bootloader-logs`;
  - save `/sys/fs/pstore`;
  - set adbd back to non-root.

  The same wrapper streams the `kmsg` page into `late-kmsg.txt` during its wait (`-Wait 90..120`).

  Since pc-016 `tools/relay/run-kit-early.ps1` is used instead. It keeps two recorders running for the whole session
  (moved into the run folder as `relay-side/` at the end):
  - `usb-timeline.txt`: every change of the tablet's USB devices with the PC time (ABL/U-Boot fastboot, NCM, Android);
  - `stream-NN-HHmmss.txt`: `kmsgall`, opened as soon as 172.16.42.1 answers (~1.4 s after the NCM device appears),
    ending with the time of the last data and the reason. A reconnect gets the whole log again.

  Its late pages are fetched only if the tablet still answers (no 4-minute timeouts after a reset).
- Kits are built in WSL by `make-kitNN.sh` scripts (kept in the PC build dir), with per-variant firmware trees, module
  lists and `kit.conf`, then packaged with `package.sh`.
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
| pc-012 | fix v2 (0028); A = SoCCP race order + ADSP + full audio, B = **integration** | **B: everything works in one boot** (display, touch fw, Wi-Fi at boot + scan, BT, battery, ADSP, GPU); audio reaches the card and stops at the missing topology. **A reset early** (no USB network) |
| pc-013 | kernel + DEBUG prints; A = pmic-glink hold/attach harness, B = pc-012 A again, C = integration again | **Fix v2 proven:** the channel is held (27 s) and attached on bind (107 s) with battery data 2 s later; C hit the race naturally and it was held and attached 1 s later. **B reset early again** |
| pc-014 | bisect: A = audio modules late (95 s), B = no WCD9395 codec | **A reset early** (so it isn't the audio modules loading); B fine |
| pc-015 | bisect: A = SoCCP stack at boot only (control), B = no USB-C connector graph + orientation GPIO, C = no orientation GPIO, D = SoCCP at 20 s | A, C, D fine; **B reset early**. The resets span 4 different setups, so it's a timing race around the early pmic-glink clients. Results in `relay/results/pc-013-015-early-reset.md` |
| pc-016 | rate + live log (`kmsgall` from ~1.4 s after NCM, USB timeline): A = control ×4, N = network first ×4 | **A3 and N4 reset** (2/8). **N4 streamed:** the kernel hung 1.3 s after the pmic-glink attach, where the MSM DRM takeover from the firmware framebuffer starts; reset ~10 s later. Every N run: USB link drop at the attach (harmless) |
| pc-017 | sound card with a topology: A = integration, B = audio only; both SoCCP at 20 s | **B: sound card registered** (`kaanapali - OnePlus-Pad4`, 5 PCMs + compress + headset jack) with upstream's Kaanapali topology. **A reset early**, so SoCCP at 20 s is no workaround. Results in `relay/results/pc-016-017-live-log-audio.md` |
| pc-018 | DEBUG kernel (USB-C, MSM takeover breadcrumbs, sync_state lines): N ×5, ND ×3 | 0 of 8 reset. USB link drop at the attach = UCSI bus reset (QMP not power-cycled). The takeover follows the NVT touch deferral by 25 ms; pc-016 N4 died within ms of it, so the hang is at the start of `msm_mdss_take_over_splash` |
| pc-019 | q-next (battmgr µV/µA, lid switch, flash LED) + DEBUG: F ×6, FD ×2 | **battmgr units, lid (open = 0), flash LEDs work → queued 0029-0031** (iceland-linux fda405c); mixer lists 223 controls. 0 of 8 reset (0 of 16 with the pc-018/019 debug kernels: the prints likely hide the race). `relay/results/pc-018-019-takeover-features.md` |
| pc-020 | pc-019 + 150 ms-paced breadcrumbs through the takeover + MDSS IRQ log: F ×8 | **2 of 8 reset (F3, F7), both caught:** the last line is `firmware framebuffer removed`, the "150 ms after" line never comes. The SoC dies in the pause right after the framebuffer releases its rails (MMCX TURBO → LOW_SVS under the 650 MHz MDP) and clocks (LUT, VSYNC, ESC0/1 gated), before the DPU votes its own. `relay/results/pc-020-021-handover-hang.md` |
| pc-021 | pc-020 kernel + DTB candidates: R = MDSS holds MMCX TURBO (×6 run), K = MDSS holds LUT/VSYNC/ESC (not run); q-next2 DT items; persist read-only | **R4 reset at the MDSS reset step** (1 of 6), so rails/clocks are not it. Lining up the init's `/dev/mem` scanout sampler (0.5 s ticks) with the breadcrumbs: every caught crash has a tick in the fatal window. **Thermistors read 29-31 °C, persist mounts ro (no bt_nv file).** Stopped early |
| pc-022 | pc-020's kernel and setup, only the `/dev/mem` sampler off (`SCAN=0`): S ×6 | **0 of 6** (vs 3 of 14 with the sampler on the same kernel). **The early reset is closed: it was the kit's own sampler.** No kernel change; `SCAN=0` is automatic for native-display kits |
| pc-023 | lean kernel try-144b (queue 0001-0034 + dpu `clk_inefficiency_factor` 100): H ×4; `UFSRO_AT=25` on persist/modem_a/bluetooth_a + `FWEXTRACT=1` | **144 Hz: the CRTC runs the stock 144 Hz timing, no underrun (4 of 4) → 0035.** **Firmware extractor: 11 files from modem_a/bluetooth_a (vfat, read-only) with matching sha256**, 11 skipped (super/raw). `relay/results/pc-023-024-144hz-extractor-fedora.md` |

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
| Battery | the first fix (-EPROBE_DEFER) lost the channel for good | a failed rpmsg probe destroys the endpoint, which closes the glink channel; hold it instead (v2 = 0028) |
| Audio | SoundWire waited for `pinctrl@7760000` | load `pinctrl-sm8650-lpass-lpi` (+ `snd-soc-wcd939x`, `-sdw`) |
| Audio | card fails at `snd_soc_component_probe` -2 | `qcom/kaanapali/OnePlus-Pad4-tplg.bin` built from `linux-msm/audioreach-topology` `SM8550-HDK.m4` (upstream's Kaanapali topology) with a pinned alsatplg: the card registers (pc-017) |
| Early reset | no log: the tablet died before the USB network was up | the `kmsgall` live stream opened at once by `run-kit-early.ps1` + `NET_FIRST=1` (modules load only once the PC is streaming) + `HEARTBEAT` |
| Early reset | "SoCCP stack at 20 s" looked like a workaround (pc-015 D) | it isn't (pc-017 A reset): the display takeover follows the pmic-glink **platform device** probe, not the SoCCP channel |
| PC tooling | Windows `Get-ChildItem` shows 0 bytes for a stream file that is still open | open the file (`[IO.File]::Open(..., 'ReadWrite')`) to see its real length |
| PC tooling | the relay log is UTF-8 when the runner is started from PowerShell 7 (UTF-16 from Windows PowerShell) | `save-run.sh` checks the BOM |
| PC tooling | the masking scripts carried the device serial as a regex; one was pushed in 5077790 | scripts read it from `~/mainline/build/.serial` (local, never committed) since pc-019's save; history not rewritten |
| Early reset | the debug prints hide the race (0 of 16 resets with the pc-018/019 kernels) | keep debug kernels lean; compare fix candidates against the pc-013 baseline |
| PC tooling | new `wsl.exe` commands time out (`Wsl/Service 0x8007274c`) while the user's LineageOS build fills WSL memory (~19 GB) | the `\\wsl.localhost` share still works; wait and retry; never `wsl --shutdown` (it would kill that build) |
| GPU | debugfs `gpu` answered ENODEV | not a failure: the a8xx code has no `gpu_state_get`; use `msmparam` (MSM_GET_PARAM) instead |
| PC tooling | a Git Bash `tail -F` on `run.log` made the runner's `Add-Content` fail | read logs with PowerShell `Get-Content` only |
| PC tooling | files edited from Windows (`\\wsl.localhost`) lose the exec bit (`env: Permission denied`) | `chmod 755` before building |
| PC tooling | PowerShell mangles inline `bash -lc` quoting (`$`, quotes, `|`, heredocs) | put commands in script files |
| PC tooling | WSL 9p read of `/mnt/c` gave "Cannot allocate memory" once | retry the copy |
| PC tooling | busybox `watchdog` keeps stdout open, so `$(watchdog …)` would block PID 1 | redirect to files, never command substitution |
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
- **Rootfs-in-RAM (pid1 mode): the kernel firmware loader's root moves with PID 1.** The userspace init shares
  its `fs_struct` with the kernel's init task (`kernel_init` is forked with `CLONE_FS`), so a `chroot` by PID 1
  changes the root that `request_firmware()` resolves paths against. After the shim exec-chroots systemd, every
  later firmware request looks inside the rootfs (pc-026 S1: the ADSP "not found" although the shim had moved
  the files into place). The shim binds the kit's `/lib/firmware` over `/rootfs/lib/firmware` before the chroot.
- **A suspend that returns at once with no message: read `pm_wakeup_irq` (needs `PM_SLEEP_DEBUG`).** On the Pad 4
  it was the PCIe0 WAKE# GPIO declared with the wrong polarity (`GPIO_ACTIVE_HIGH` on an active-low, pulled-up
  line): a level IRQ "active" the whole time PCIe is on (pc-026 S1). A bare kit without PCIe slept fine, which
  pointed away from the kernel for a while.
- Probes: `cmd < <(sleep N)` for programs that watch stdin (kmscube, cage); a pipeline `sleep N | cmd` waits for
  the whole sleep. A relay `-Wait` ends the session, not the kit's `AUTOREBOOT_AT`. Never suspend the tablet
  while `rootfstar` streams (the hand-back breaks; the probes keep the previous tarball on a failed gzip check).
- PC side: `wsl.exe ... bash -lc '...'` goes through Windows argv parsing - a `\"` in the command loses its
  backslash and silently changes an inline sed/python; put such text in files (Write tool) and run them.
- Starting the ADSP may kill simplefb (SM8750 report). Enable remoteprocs one at a time.
- Bluetooth firmware is `brhbt*` and btqca loads it under those names. Wi-Fi uses the ELF BDF `bdwlan.elf` from odm (board_id 0xff).
- A distro loads ath12k early (udev). Until the early-load reset is understood, load it late (a service after USB).
- The userdata raw backup is FBE-encrypted, so the `/data/vendor` TEE files must be copied at file level before Android is erased.
- UFS LUN order can change between boots: always mount by partlabel.
- troikoss rule: find the missing layer first (driver / firmware / userspace bridge / app).
- **A failed rpmsg probe closes a glink channel** (the endpoint is destroyed), and the remote may never reopen it. So
  never return -EPROBE_DEFER from an rpmsg probe on glink.
- **SoCCP is attached, not booted** (`early_boot`): its channels appear the moment `qcom_q6v5_pas` probes, so races
  that ADSP firmware loading used to hide become real. `qcom_sysmon` needs a QRTR socket, so SoCCP attach and the
  pmic-glink platform device both wait for `qrtr` and then race.
- Every run can end in an unexplained reset. Lineage's `/proc/bootloader_log` gives the reset source
  (`PM: Reset by …`, `Reset Type`, `PonReason`); `sys.boot.reason` is always a stale "bootloader". pstore does not
  survive (PS_HOLD hard reset).
- **Unattended kits need a way back:** a watchdog daemon plus an auto reboot at 240 s. The runner waits 150 s for the
  network and 180 s for adb.
- If a crash happens before the USB network is up, use `NET_FIRST=1` (the modules wait for the PC's `kmsgall`
  stream) rather than `LATE_MODS`, which changes what races with what.
- `debugfs dri/*/gpu` ENODEV doesn't mean the GPU failed; ask the driver (`msmparam`).
- **Stream first, then load.** With `NET_FIRST=1` the PC reads the live log before any module loads, so an early hang
  is recorded up to its last ~0.1 s. The kmsg lines printed in the very last moments may not get out: bracket
  suspects with breadcrumbs.
- **The display takeover comes 1.3 s after the pmic-glink platform device probes** (that probe kicks the deferred
  probes: KTZ8869 master → panel → DSI → msm_dpu). Moving the SoCCP stack later does not move it.
- **UCSI init resets the USB bus:** 8 ms after "Registered UCSI interface" the host issues a bus reset and the gadget
  re-enumerates (full speed, then high speed); Windows may drop the NCM TCP connections. Harmless, but a live stream
  must reconnect. The QMP orientation does not change (the PHY is not power-cycled).
- The SoCCP altmode notifications repeat every ~3.3 s (orientation 1, mux 1, svid 0xff00) and each one calls
  `typec_switch_set` (a no-op when nothing changes).
- Stock speakers are **Primary TDM** (8 × 32 bit), not Primary MI2S; see §4 audio.
- **Never poke display (or any driver-owned) registers from userspace once the driver owns them.** The kit's
  `/dev/mem` scanout sampler (pc-001) read the DPU INTF registers every 0.5 s; a tick while the MSM driver held the
  MDSS in reset, or right after the framebuffer's clocks were gated, hung the AHB and the SoC hard-reset ~1 s later.
  That was the whole "early reset" (pc-009..021, ~1 in 4). Debug prints only shifted the phase between the ticks
  and the takeover, hence the "heisenbug". `build.sh` now sets `SCAN=0` for native-display kits. When a crash
  correlates with a boot phase, list every asynchronous actor (userspace samplers, timers, workers) before blaming
  the kernel.
- **Two samples are not a location.** pc-020's two caught crashes both sat after the framebuffer removal, so the
  rail/clock story looked complete; the third sample (pc-021 R4) fell elsewhere and broke it. Test a mechanism with
  a variant that should move or remove the crash before writing the fix.

## 13. Current state, open issues, next steps

**State (2026-09-28 evening, all over RAM boot, nothing written to the tablet):**
- ✅ U-Boot; Linux 7.3-rc4 from RAM through EFI; USB NCM + survey pages.
- ✅ Display: ABL splash kept, then **native MSM DRM at 120 Hz**; KTZ8869 backlight.
- ✅ CPU thermal (stock trips, tested under load).
- ✅ Touch firmware runs (touch and pen devices registered; a real touch isn't confirmed yet).
- ✅ Wi-Fi (`wlan0`, scan), ✅ Bluetooth (`hci0`), ✅ battery/USB data over pmic-glink (SoCCP).
- ✅ ADSP boots, SoCCP attaches, the GPU powers up.
- ✅ **Integration boot (pc-012 B, pc-013 C):** all of the above works together in one boot.
- ✅ **Sound card registers** (pc-017) with upstream's Kaanapali AudioReach topology: 5 PCMs + compress + headset
  jack. ⚠️ Nothing played yet; the speakers need Primary TDM (stock) and volume caps first.
- ✅ **The "early reset" is gone (pc-022):** it was the kit's `/dev/mem` display sampler; integration boots are
  now clean back to back.
- ✅ Battery units (0029), lid switch + debounce (0030/0034), flash LEDs (0031), board/flash thermistors (0032),
  eUSB2 tuning (0033); persist read-only mount; queue = 0001-0034 (iceland-linux 9d29f72).
- Target OS: **Fedora 44 with GNOME** (user). ✅ Fedora 44 boots to systemd `running` in RAM (pc-024 Y7),
  ✅ **the Adreno 840 renders through Mesa's freedreno** (pc-024 Y8: `Adreno (TM) 840`, GLES 3.2, Mesa 26.2.3,
  DCVS 160 MHz-1.2 GHz), ✅ **Wayland: cage/wlroots at 120 Hz, glmark2 1836** and ✅ **GNOME Shell 50.5
  (mutter) runs as the Wayland display server with gdm autologin** (pc-024 Y9) - see §13 item 12.
- **Critical items on the GNOME rootfs (pc-026, 2026-09-29, `relay/results/pc-026-critical-items.md`):**
  ✅ cpufreq (SCMI, schedutil, stock's tables) + cpuidle (PSCI WFI/cpu-sleep) + GPU/UFS devfreq;
  ✅ 63 thermal zones with stock trips and cooling devices (CPU, GPU devfreq, ath12k);
  ✅ battery/USB data over battmgr (design capacity + a garbage remaining word fixed in the queue candidate);
  ✅ Wi-Fi (ath12k up at boot, NetworkManager scan, 2.4 GHz seen; a connection needs the user's credentials);
  ✅ Bluetooth (hci0 with the tablet's own address, scan; pairing needs the user);
  ✅ the pen accepted by libinput (0036/0037); ✅ GNOME at 144 Hz;
  ✅ **suspend** (root cause found in pc-026 S1): the PCIe0 WAKE# GPIO (TLMM 104) was declared
  `GPIO_ACTIVE_HIGH` while the line is active low (pulled up, pinctrl `wake-n`), so the root port's dedicated
  wake IRQ fired at once whenever PCIe was on; with that wake disabled s2idle held for the RTC alarm (26 s) and
  everything came back - DT fix on the queue candidate (0038), verified in S2;
  ✅ suspend confirmed in pc-026 S2 with the fix: five s2idle cycles of 27-29 s each, RTC wake, with GNOME,
  Bluetooth and Wi-Fi active; ✅ standby (the shell blanks the DSI panel: DPMS off, backlight off, and back);
  ⚠️ **after real suspend cycles CPU 7 stalled in a deep idle state 2.5 min later** (S2: `rcu_preempt detected
  stalls`, NMI unanswered, watchdog reset) - under test (S3: stall watch after one cycle; then the big cores'
  deepest idle state after resume);
  ✅ S3: no CPU stall in 6 min after one s2idle cycle (the S2 stall stays a watch item after multiple cycles);
  ⚠️ **S10 (q9 kernel = queue 0001-0045): the tablet hard-reset after its first s2idle cycle**
  (`/proc/bootloader_log`: "Reset Type: Hard Reset", PonReason 0x11). The live stream shows the cycle DID
  resume (suspend exit at 87.7 s); the log went silent ~8 s later and the reset came ~26 s after that. Same
  class as the S2 CPU 7 idle stall (q6-era kernel, no audio patches) → most likely **one CPU not waking from
  idle after an s2idle cycle** (2 events in ~15 cycles), not the audio queue. The idle states equal the stock
  live DT exactly. Under test in S11: post-resume idle depth capped by the CPU latency QoS (1000 µs = C4 only,
  5000 µs = + cluster, none = + system), per-CPU liveness checks, USB IRQ/stream/watchdog pinned to CPU 0;
  ✅ **S11: 24 bare s2idle cycles (6 capped at 1000 µs, 6 at 5000 µs, 12 uncapped) - no stuck CPU, no RCU
  stall**, with thousands of runtime system-state entries after resume. A bare cycle does not reproduce the
  stall; next: what S10 did before suspending (UCM/PipeWire/audio/Wi-Fi) on the debug-hang kernel + ramoops
  (Mainline answer pc-026-s10-crashlog), so a reset leaves a log;
  ⚠️ **SOUND IS NOT CONFIRMED - the user reports no sound (2026-09-29 13:46).** Every speaker result below is
  log-level (graphs start, aplay/pw-play rc=0, amplifier status 0x7eaf → 0x7eef); nobody has heard it, and GNOME
  only ever showed "Dummy Output" (the UCM profile was never persisted). **S12 measured it acoustically (mics
  record while the speakers play, `an/loopback.py`): silent.** Cause 1 (fixed): a saved alsactl state routed
  MultiMedia1 into RX_CODEC_DMA_RX_0 too (graph 113 AR_ENOTEXIST → every MM1 prepare failed → "Dummy Output");
  route off → WirePlumber shows the speakers + mics; UCM FixedBootSequence now forces it off; clean state handed
  back. Cause 2 (open): the ADSP consumes the stream ~3-10× faster than real time (a 10-s play ends in ~1 s)
  although the amplifiers power up and unmute correctly while it runs. **S13: cause 2 found and fixed** - the
  stream graph's MFC output stayed 2 ch/16 bit while the TDM endpoint takes 8 ch/32 bit (exactly 8.00× the
  byte rate); the speaker device subgraph now has its own MFC ([MFC]→[LOG]→[TDM SINK]) → 1.00× real time.
  **Still silent (cause 3, decoded in S14 with the TFA986x field map from the Goodix/NXP tfa98xx driver):** the
  amplifiers' PLL never locks - reg 11 CLKS = 0, PLLS = 0; reg 10 NOCLK = 1, CLKOOR = 1 ("external clock out of
  range": the 0x7eaf → 0x7eef flip read as "clock stable" since S6); reg 12 MANSTATE = 1. The per-amplifier
  tables program a 2-slot I2S-like frame (reg 20: TDMSLOTS 0, TDMNBCK 0, TDMFSPOL 1/0 splitting L/R groups;
  reg 21: TDMSPKS 0) - the MI2S design they came from - while the port sends stock's 8 × 32-bit TDM frame.
  Fix = stock's TDM field values (TDMSLOTS/TDMNBCK/TDMSPKS/TDMFSPOL) from the stock TFA container (read-only
  pull from Android, private) decoded with the field map;
  ⚠️ **sound - root cause found (S3 analysis, fix under test in S4):** the card is up on the ADSP after the
  hand-over (kit firmware bound over the rootfs's `/lib/firmware`; the DT link on stock's `PRIMARY_TDM_RX_0`),
  the front-end graph opens, but **the speaker back-end graph is rejected at `APM_CMD_GRAPH_OPEN` because the
  stock ADSP firmware has no Audio Interface (QAIF) module** (0x0700117C/D, what mainline 7.3's TDM support and
  linux-firmware's Kaanapali MTP topology use): its static module table (`an/adsp-modules.py` over the adsp.bNN
  segments) holds the classic I2S/PCM/**TDM (0x0700100E/F)**/codec-DMA/DP endpoints, and the stock ACDB
  (`an/acdb-scan.py`; the file itself stays private) references `MODULE_ID_TDM_SINK` 95× and Audio-IF 0×. The
  probe-time `GET_SPF_STATE` timeout is harmless (5 s too early; the PRM's identical query is answered). Stock
  TDM settings from the ACDB: LPAIF 0, intf 0, sync internal, ctrl data-out enable, slot mask 0xff, 8 × 32 bit,
  long sync mode, no inversion, 1-cycle data delay; endpoint format 48 kHz/32-bit/8 ch. Fix, step by step:
  kernel `tdm-sink` (classic TDM modules + `PARAM_ID_TDM_INTF_CFG` 0x0800101B in audioreach, topology loader,
  graph-open error logged) + `module_tdm.m4`/`subgraph-device-tdm-playback.m4` → **S4: the graph is accepted
  (open, media format, prepare), START returns error 1**; `tdm-clk` (q6prm TDM clock ids 0x200.., DT
  `&q6apmbedai { dai@18 { … "bclk" } }` like the OnePlus 15's MI2S) → **S5: the PRM grants the 12.288 MHz bit
  clock (ftrace-verified chain), START still error 1**; `tdm-fmt` (BE fixup S32_LE / 8 ch = the stock endpoint
  format, + 6/8-channel default maps) → **✅ S6 (07:59): playback on PRIMARY_TDM_RX_0 completes, no DSP error,
  all six TFA9865 report a stable clock (status 0x7eaf → 0x7eef)** - the ALSA path to the speakers works;
  not yet confirmed by ear, and the stereo stream is spread over the 8 slots with a 7.1 map (stock: custom
  per-amplifier channels) → follow-ups: channel layout, volume controls, UCM, PipeWire. Queue 0038-0045
  (`queue-tdm2.sh`). **✅ S7 (08:19): the microphones capture** (hw:0,2, both channels, room sound) - no kernel
  change, only the right controls: `ADC1 MUX=CH1_AMIC1`, `ADC2 MUX=CH2_AMIC5`, `ADC1/2 Switch=1`,
  **`ADC1_MIXER Switch=1`, `ADC2_MIXER Switch=1`** (the DAPM switches the probes had missed), `TX SMIC MUX0=
  SWR_MIC0`, `TX SMIC MUX1=SWR_MIC1` (the v9.2 TX macro's input names), `TX DEC0/1 MUX=SWR_MIC`, `TX_AIF1_CAP
  Mixer DEC0/1=1`, `MultiMedia3 Mixer TX_CODEC_DMA_TX_3=1`. The codec-DMA "EIO" was never a DSP fault: the DSP
  graphs ran, the codec DAPM chain was unpowered (packet dumps + widget dumps in `docs/tests/linux-runpc26i`).
  WCD headphone path: `HPHL_RDAC Switch`/`HPHR_RDAC Switch` were the missing bits (no jack on the Pad 4; parked).
  **✅ User space (S9):** the UCM profile for card "OnePlusPad4" (`audio/ucm/OnePlus-Pad4/`: HiFi verb, Speaker =
  MultiMedia1→PRIMARY_TDM_RX_0, Mic = MultiMedia3←TX_CODEC_DMA_TX_3 with the S7 controls) is taken by
  WirePlumber 0.5.17: profile HiFi active, sink "Built-in Audio Speakers", source "Built-in Audio Internal
  microphones"; pw-play and pw-record work (clean capture). **Never set `TX0/TX1 MODE = ADC_HIFI`** (stock's
  value): on mainline it turns the capture into full-scale noise; the boot default (untouched) is clean. Rootfs
  facts: pipewire 1.6.9 + wireplumber + pipewire-alsa/pulse present, `alsaucm`/`diffutils` absent, dnf without
  proxy (pass `--setopt=proxy=`). The rootfs hand-back (rootfstar) fails gzip -t since S8 - to fix; the profile
  must be installed into the rootfs (post script / hand-back) to persist.
  Second issue (resolved as above): the WCD playback and the
  mic capture get `EIO` after ~1 s with no DSP error = no buffer completions (ALSA `wait_for_avail` timeout) -
  data-flow/clocking on the codec-DMA paths, S4 samples the PCM status. Front ends take S16 stereo 48 kHz only;
  mics: WCD9395 analog mics → TX macro → `TX_CODEC_DMA_TX_3`; ✅ `upower` works with `PrivateUsers=no` under
  the chroot hand-over (S3). Never unbind/bind the GPR/APM devices in-session (port idr dropped, replies lost).

**Open issues:**
1. ✅ **Early reset - closed (pc-022): it was the kit's own `/dev/mem` display sampler, not the kernel.** History:
   ~1 in 4 in every native-display setup (pc-012 A .. pc-017 A). pc-016 N4's "last line" was an artefact (the live
   stream dies at the UCSI bus reset and reconnects). pc-020's paced breadcrumbs caught two crashes after the
   firmware framebuffer removal; pc-021 R4 (MMCX held by the MDSS) crashed at the MDSS reset step instead, which
   ruled out the rail/clock story. Lining up the init's scanout sampler (a `/dev/mem` read of the DPU INTF
   registers every 0.5 s, since pc-001) with the breadcrumbs shows a tick inside the fatal window in all three: the
   MDSS in reset, or the framebuffer's LUT/VSYNC/ESC clocks just gated → AHB hang → PS_HOLD reset ~1 s later.
   pc-022 = pc-020's kernel and setup with `SCAN=0`: **0 of 6** (3 of 14 with the sampler). `build.sh` sets
   `SCAN=0` for `NATIVE_DISPLAY=1` kits. The `fix-handover` msm_kms.c patch (DPU holds its clocks/rail across the
   removal) is not needed and stays out of the queue. Details: `relay/results/pc-020-021-handover-hang.md`.
2. ✅ **Early Wi-Fi load reset** (pc-009): the same sampler, most likely (2 resets while it was ticking); no
   reset in 30+ runs since Wi-Fi loads with the SoCCP stack.
3. ✅ **battmgr units:** fixed in 0029 (the Oplus gauge gives mV/mA).
4. ✅ **144 Hz works (pc-023 H1):** `dpu_crtc_mode_valid` pruned it (1261 MHz × 1.05 / 2 = 662 MHz > the 650 MHz
   core clock; the stock timing needs 630.5 MHz per mixer). With `clk_inefficiency_factor = 100` in the kaanapali
   catalog (branch `try-144b`, to queue as 0035 after the 4 runs) the CRTC runs `3392x2400 144 1261347 3392 3460
   3492 3532 2400 2426 2428 2480` with no underrun in dmesg.
5. **qnoc sync_state** drops boot bandwidth once `qce-core` binds. It matters only for the simpledrm fallback.
6. GPU `vdd`/`vddcx` supplies: cosmetic (the GMU powers the GPU; upstream kaanapali boards list none).
7. ✅ Board and flash thermistors + zones: 0032 (pc-021: 29-31 °C).
8. pmsg/ramoops don't survive (PS_HOLD hard reset). Crash logs come only from the live stream: use `kmsgall` with
   `run-kit-early.ps1`, and `NET_FIRST=1` for anything that happens during module loading.
9. SoundWire TX port-count mismatch warnings (DT vs controller).

**Pending list (shared; worked top-down, RAM boot only, nothing written to the tablet):**
1. **Finish the early-reset investigation** (#1):
   1. ✅ rate: ~1 in 4 (pc-016: 2 of 8; pc-017 A);
   2. ✅ early live log (`kmsgall` + `run-kit-early.ps1` + `NET_FIRST`); N4 caught the hang at the display takeover;
   3. ✅ pc-018/019: the hang is at the start of the MSM splash takeover (see open issue #1);
   4. ✅ pc-020: two crashes caught after the framebuffer removal; pc-021 R4: one at the MDSS reset;
   5. ✅ pc-022: **closed - the kit's `/dev/mem` sampler; 0 of 6 with it off.** No kernel patch.
2. **Audio:**
   1. ✅ topology + card registration (pc-017; upstream's Kaanapali topology as `OnePlus-Pad4-tplg.bin`);
   2. ✅ mixer listing: 223 controls (pc-019, `amixer -c 0 contents`, read only);
   3. speakers: DT speaker link on PRIMARY_TDM_RX_0 (8 × 32 bit, TFA9865 slots; branch tdm-spk) ✅ card + route;
      the Audio IF (QAIF) module is **absent from the stock ADSP** → classic `MODULE_ID_TDM_SINK` in the kernel
      (branch tdm-sink) and the topology (`module_tdm.m4`), stock ACDB settings - S4;
   4. volume caps, then UCM; no playback before that (TFA9865 protection needs `tfa98xx.cnt`).
3. ✅ **battmgr units**: 0029 (the Oplus gauge gives mV/mA; now ×1000), tested in pc-019.
4. **Small DT items:**
   - ✅ lid `gpio-keys` `SW_LID` on TLMM98 (0030) + 15 ms debounce (0034; closing untested);
   - ✅ rear flash LED (0031);
   - ✅ board + flash thermistors and zones (0032, pc-021);
   - ✅ eUSB2 repeater `qcom,tune-usb2-preem = 3` (stock's 0x57 = 0x03; 0033);
   - GPU `vdd`/`vddcx`: cosmetic, dropped; panel vddio L12B: already 1.8-1.896 V (the nearest 8 mV step to
     stock's 1.9 V); WLAN `drop-l3k` / `msix-match-addr`: downstream cnss2 properties with no mainline equivalent.
5. ✅ **UFS read-only mount** (pc-021/022: `UFSRO_AT`, by GPT name, `BLKROSET` + `ro,noload`; persist listed) →
   **firmware extractor** `tools/linux-ram/fw-extract.sh` (manifest-driven, modem_a/bluetooth_a vfat) tested in
   pc-023 (running); vendor/odm need the `super` partition mapped (later).
6. **BT address.** pc-022 looked at persist read-only: `bluetooth/` is empty (no `bt_nv.bin`), `wlan/` has only
   config files (no MAC file). So stock derives the addresses from the WCN7860's own OTP (ath12k reports wlan0's
   MAC) and the vendor property. Next: set the BD address at boot from wlan0's MAC (stock's rule, to be confirmed
   under LineageOS: `getprop persist.vendor.service.bdroid.bdaddr` vs `ip link show wlan0`) with `btmgmt
   public-addr` or the DT `local-bd-address` filled by a boot script.
7. **Touch/pen events and lid events:** need a person at the tablet. Add an input-event logger to a kit and ask the
   user for a 30 s touch/lid window.
8. **5/6 GHz Wi-Fi reception:** needs a 5 GHz AP in range (ask the user), or check the reported frequencies once one
   is.
9. **144 Hz** (#4): per-rate porches/DFPS in the panel driver (a kernel change, test through a kit).
10. **Suspend (s2idle)** with an RTC wake, as a late step in a kit: needs the watchdog + auto-reboot safety.
11. **USB OTG** on battery and with external PD (needs the user and the debug DTB's USB role changed).
12. **Phase 4 preparation.** Target OS (user, 2026-09-28 20:38): **Fedora with GNOME** (aarch64) - not
    postmarketOS (no pmaports device package), not Debian/Ubuntu. RAM first: a small official Fedora aarch64 rootfs
    (the Container Base tarball, which has systemd) as the initramfs behind the kit's busybox shim (USB NCM network,
    report pages, live kmsg), `switch_root` into it, nothing written; extra packages added on the tablet at RAM-boot
    time through a proxy on the PC (the WSL host has no dnf). The install = the official Fedora Workstation aarch64
    raw image into userdata as a whole-disk image (U-Boot blkmap + EFI boot manager + GRUB) with our kernel/DTB,
    only with the user's OK. GNOME acceleration: **Mesa 26.0 has initial freedreno (OpenGL) support for Adreno
    gen8 incl. a840/Kaanapali** (Phoronix, "Mesa 26.0 lands initial support for Adreno Gen 8"; the kernel side is
    the "drm/msm/adreno: Introduce Adreno 8xx family support" series, in our 7.3 tree); turnip (Vulkan) is
    still landing. **Fedora 44 ships Mesa 26.0.3 (43 has 25.2.4), so Fedora 44 is the release to use**;
    llvmpipe is the fallback. **Done in RAM (pc-024, 2026-09-28 evening):** the Fedora 44 Container Base userland
    runs on our kernel (bash 5.3.9, glibc 2.43, dnf5 5.4.1) in a chroot beside the kit's shim; dnf5 installs
    packages through `tools/relay/usb-proxy.py` on the PC (systemd + NetworkManager + openssh-server in 15 s; the
    kit sets the clock from `KIT_TIME`, the PMIC RTC reads 1970); the page `rootfstar` hands the installed rootfs
    back to the PC (110 MB) and `phase4/make-rootfs.sh` rebuilds the next boot from it. Pitfall: `switch_root`
    into the rootfs resets the tablet ~45 s later (the shim's safety jobs lose their tools); `ROOTFS_MODE=pid1`
    (exec chroot systemd as PID 1, the initramfs stays the real root, `/rootfs` bind-mounted on itself) is the
    way: **pc-024 Y7 (21:29): systemd 259.9 boots Fedora 44 to `running` on the tablet in RAM** (journald, udev,
    NetworkManager, sshd; `an/fedora-ssh.sh` logs in from WSL), `iceland-dnf.service` installs packages through
    the PC (71 in 18 s), `kmscube` renders on the MSM KMS - on llvmpipe in Y7 (the kit's DTB kept `gpu@3d00000`
    disabled). **Y8 (21:48): with the GPU node enabled and the gen8 firmware in the kit (`qcom/gen80200_{sqe,gmu,
    aqe}` from linux-firmware + the tablet's own signed `qcom/kaanapali/iceland/gen80200_zap.mbn`, kit tree
    `fw24`, never committed) the a840 binds, `Loaded GMU firmware v5.3.23`, and Mesa reports `freedreno` /
    `Adreno (TM) 840` (GLES 3.2, Mesa 26.2.3), GMU DCVS 160 MHz-1.2 GHz, no GPU error** - GPU acceleration for
    GNOME is available. Probe traps: kmscube over ssh needs a silent stdin (`kmscube … < <(sleep 60)`, not a
    pipeline), and the runner's `-Wait` ends the session (not `AUTOREBOOT_AT`). **Y9 (22:08): Wayland works -
    `seatd` + `cage` (wlroots) on the MSM KMS with the GLES2 renderer "Adreno (TM) 840", 3392x2400 @ 120 Hz,
    `glmark2-es2-wayland` full screen score 1836; kmscube 119.99 fps (vsync). Then, in the same boot, a lean
    GNOME set (458 pkgs, 357 MiB, ~6 min through the proxy) + gdm autologin: GNOME Shell 50.5 (mutter) runs as
    the Wayland display server on `/dev/dri/card1` with a GBM renderer and a high-priority EGL context, logind
    session on seat0, gsd daemons up** - after adding `systemd-pam` (pam_systemd, missing from the Container
    Base lineage → no logind session / user manager / session bus → "Unable to run session message bus",
    "Session never registered") and `dbus-daemon`. The rootfs came back as `rootfs-gnome.tar.gz` (653 MB, on
    the PC). `ROOTFS_URL` lets the shim fetch it at boot (port 8000): **Y10 = that boot** (kit `linux-Y10.img`).
    Input: libinput ignores the pen (see plan B.5); the touch screen is a libinput device. See `phase4/README.md`, `phase4/INSTALL-PLAN.md`,
    `relay/results/pc-023-024-144hz-extractor-fedora.md`:
    - file-level copy of `/data/vendor` + persist;
    - ath12k loaded late until the resets are understood.
13. Later: DP, cameras (SC1320CS/SC820CS need new drivers; CAMERA_ICP firmware), sensors (SSC via hexagonrpcd), video.

**Plan (2026-09-28 22:05; the user asked for all pending hardware bring-up in it; RAM boot only, one kit per
item, judged from logs, results saved after each; anything that writes to the tablet waits for the user's OK):**
- **A. Phase 4 - Fedora 44 GNOME:** Y9 = Wayland on the a840 (`seatd` + `cage` + `glmark2-es2-wayland` from the
  kit's post-install hook) and, in the same long boot (`AUTOREBOOT_AT=1800`, runner `-Wait 1700`), `dnf5 group
  install gnome-desktop` through the proxy, a gdm autologin user, `systemctl start gdm` judged from the journal
  (gnome-shell/mutter renderer lines), the rootfs handed back (`rootfstar` → `rootfs-gnome.tar.gz`) → Y10 boots it
  via `ROOTFS_URL` (GNOME session in RAM; touch/pen judged from libinput/mutter logs, with a 30 s window from the
  user) → the install (`phase4/INSTALL-PLAN.md`: Workstation 44 image into userdata, our kernel/DTB, the firmware
  set from the extractor manifest; **needs the user's OK**).
- **User's order 2026-09-29 01:0x: the critical items first - battery, power management, thermals, sleep
  states, standby, sound, speakers, mic, Wi-Fi, Bluetooth - "debug and fix till finalized", device-referenced
  values only, RAM only; the install last.** Status in the State list above and in
  `relay/results/pc-026-critical-items.md`.
- **B. Hardware bring-up still pending, in order** (items above by number):
  1. **Suspend/resume** (#10): ✅ kernel level (pc-025: s2idle + RTC alarm, 2 of 2, display/touch/USB back);
     ⚠️ on the GNOME rootfs every attempt ends within 1-2 s (pc-026 F0/S1; "Wakeup pending" only while ath12k
     tears down; with Wi-Fi unbound and the power-supply wakeups disabled it still returns at once without a
     message). Next: `PM_SLEEP_DEBUG` kernel + the bisect (BT off, gdm off, Wi-Fi off, ftrace of
     `wakeup_source_activate`), then the device that wakes it.
  2. **Wi-Fi:** load ath12k with the rest again (the reset was the sampler, open issue #2), 5/6 GHz when an AP is in
     range (#8, user), regulatory domain; NetworkManager Wi-Fi under Fedora (Y10+).
  3. **Bluetooth address** (pending #6): BD address from wlan0's MAC at boot (confirm stock's rule under LineageOS
     with read-only adb `getprop`); `btmgmt public-addr` / `local-bd-address`; pairing under GNOME.
  4. **Audio** (pending #2): ⚠️ NOT AUDIBLE per the user (13:46) - the primary TDM playback completes at the
     ALSA level (pc-026 S6: classic TDM sink, PRM bit clock, 32-bit/8-ch back end; queue 0038-0045), but no
     sound has been heard; S12 measured silence (acoustic loopback): stray MM1 route fixed, stream not paced in
     real time (TDM endpoint not outputting) open; pending: per-amplifier channel layout (stock:
     custom channels 48-56 on the 8 slots), volume caps, UCM/PipeWire, **mic + WCD codec paths** (EIO without a
     DSP error, RX SoundWire bus clash - S7 with the packet-dump kernel), headset;
     the TFA9865 `tfa98xx.cnt` protection before any playback; mics.
  5. **Touch, pen, lid events** (#7): an input-event logger kit, or GNOME's libinput logs in Y10; the lid switch
     closing (0030/0034) and the pen. **Found in Y9 (cage's log):** libinput accepts the touch screen
     (`NVTCapacitiveTouchScreen`) but **ignores the pen** - "NVTCapacitivePen: libinput bug: missing tablet
     capabilities: btn-stylus resolution" → the nt36536 driver must report ABS_X/ABS_Y resolution (and the
     stylus buttons) for the pen device (`input_abs_set_res`); a kernel change, test through a kit.
  6. **USB:** host/OTG role (#11: DTB role switch, needs the user + PD), DisplayPort alt mode over USB-C
     (pmic-glink altmode + DP in the DPU, #13), charging limits/thermal.
  7. **GPU extras:** turnip (Vulkan) once Mesa lands a840, GPU cooling (`#cooling-cells`), the cosmetic
     `vdd`/`vddcx` supplies (open issue #6).
  8. **Video (Iris), cameras (SC1320CS/SC820CS + CAMERA_ICP), sensors (SSC through fastrpc/hexagonrpcd),
     haptics, the keyboard accessory** (#13).
  9. **Storage/firmware:** `super` mapped for the vendor/odm firmware in the extractor (pending #5), the file-level
     `/data/vendor` + persist copies at the install; UFS is written only at the install, with the user's OK.
  10. **Kernel loose ends:** 144 Hz per-rate porches/DFPS (#9), SoundWire port-count warnings (open #9), qnoc
      sync_state for simpledrm (open #5), pstore across PS_HOLD (open #8); queue 0001-0035 kept ready for review.

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
19. The user told the PC session to "keep autonomous as long as it's only a RAM boot". The PC then built and ran
    pc-010..pc-015 by itself:
    - pc-010: BT, Wi-Fi scan, ADSP, SoCCP;
    - pc-011: battery, GPU;
    - pc-012/013: integration, pmic-glink fix v2 (0028, iceland-linux e0b025a);
    - pc-012..015: the early-reset bisect.
20. The PC answered relays 002 (qdss.cfg, flash LED, cameras) and 003 (shared knowledge), and folded pc-012..015 into
    this file.
21. The user asked both sessions to save all knowledge and progress, keep a pending list and work through it until
    done: **RAM boot only, never flash anything that could brick**. The pending list is §13 above.

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

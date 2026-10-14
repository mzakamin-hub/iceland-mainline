# OnePlus Pad 4 mainline — research notes (discovery 2026-09-27, formerly PLAN v2)

> **Status 14 Oct 2026.** This note is the discovery of 27 Sep and plan v2, kept as history. The phases in its "Plan"
> section are superseded by `PLAN.md` (status block of 14 Oct). The feature matrix has the row-by-row state. In short:
> the install is done; the speakers, microphones, display, GPU, video, sensors and camera streaming work; the open items
> are those listed in `INSTALL-PLAN.md`, `TODO.md` and the matrix. Names of relay folders, scripts and logs are PC names
> and are not published.


## Context
Goal: one mainline kernel (+ DTB, firmware, U-Boot) for the OnePlus Pad 4 that boots **any** arm64 rootfs —
Fedora, Ubuntu/Debian, Arch, pmOS, Kali, … (pmOS only as the first debug rootfs because of its bring-up tooling).
LineageOS track paused; this plan supersedes `03-Mainline-Port-Plan.md` v1 using fresh discovery of the linked repos.
Tablet: bootloader unlocked, full 151-partition backup, stock 11.A.38 package + rollback loop proven (#108), slot b = 11.A.32 firmware (do not use).
Rule: agent never flashes/boots/wipes; user runs every tablet command.

## Discovery findings (2026-09-27)

### A. map220v/sm8850-mainline `iceland-7.2` @ bc3e5fc8 (still branch head) — our base
DTS `arch/arm64/boot/dts/qcom/kaanapali-oneplus-iceland.dts` (1494 lines) already enables:
- Display: MDSS + DSI0/DSI1 dual-DSI, panel `oneplus,iceland-nt36536` (reset TLMM171, TE gpio86), DSC forced v1.1 (v1.2 → slice errors); modes 144/120/90/60/30. avdd/avee = fake always-on fixed regulators.
- Backlight: KTZ8869 a/b @0x11 on i2c14/i2c15, HWEN TLMM1 (`drivers/video/backlight/ktz8869_iceland.c`, 211 lines, global slave ptr, remove() NULL bug, bias not a regulator).
- Touch: spi19 `novatek,NVT-ts-spi`, irq TLMM158, fw `novatek/novatek_nt36536_fw.bin`; vendor driver ~3.7k lines, pen X/Y/pressure/tilt, no tap-to-wake, panel-follower hook.
- UFS, USB (eUSB2 via PMIH0108, role via pmic-glink/UCSI), WCD939x USBSS mux, PCIe0 WCN7860 (ath12k) + pwrseq, BT uart18 (**hardcoded BD addr**).
- Remoteprocs adsp/cdsp/soccp, fw `qcom/kaanapali/iceland/*.mbn`; modem regions deleted (SM8850P has no modem).
- GPU Adreno 840 enabled, zap `qcom/kaanapali/iceland/gen80200_zap.mbn`, sqe/gmu/aqe in `qcom/`.
- Audio: sndcard "OnePlus-Pad4", 6× TFA9865 (i2c0/i2c22 @0x34/36/37) on Primary MI2S, static register tables, **no speaker protection**; WCD9395.
- Battery: `oplus,kaanapali-pmic-glink` → qcom_battmgr OPLUS variant.
- Reserved memory: 30 regions (merged tz/aop nodes) vs stock 45.
**Gaps:** no lid switch (TLMM98), empty `/chosen` (no simplefb/stdout-path), no `qcom,msm-id`/`board-id`, no camera/iris video/DP/sensors, fixed DCS brightness, no ramoops node, map220v publishes no boot docs.
Firmware repo map220v/iceland-firmware: file list/layout = our manifest (ath12k WCN7860 hw2.0, novatek fw, qca BT gngbt*, gen80200 sqe/gmu/aqe, kaanapali/iceland adsp/cdsp/soccp/zap/vpu40_2v, AudioReach `OnePlus-Pad4-tplg.bin`). No license/README → we extract our own from 11.A.38.

### B. troikoss Porting Guide (Tab S9 Wi-Fi SM8550, Fedora) — the method we adopt
1. **Layering rule:** before any work, identify the missing layer: kernel driver (check mainline first) / firmware (never writable, extract) / userspace bridge (usual answer) / app integration.
2. **Boot chain from stock format** (header v4): `boot` = Image + appended DTB; `vendor_boot` = initramfs + **cmdline + bootconfig** (its DTB is what ABL loads); `dtbo` zeroed → DeviceTreeAppended fallback; `vbmeta` zeroed/flags 2. Cmdline changes = reflash bundle. Verify live FDT, not the file.
3. Sizes via `blockdev --getsize64` on device; installer: check codename/model/sizes, boot-chain only, typed confirmation, no auto-reboot; keep rollback bundle.
4. Kernel: mainline + small patch set + out-of-tree drivers; vendor source = reference. Test bindings by probing; recover bindings from stock dtbo `__fixups__`; in-DT I2C address sweep; verify Kconfig edits landed; iterate with modules; live DSP firmware load.
5. Firmware: exact blob names (vpu `ENOENT` trap), pinned sha256, fail loudly; payloads contain unused files.
6. Rootfs: root-owned `/` (tmpfiles), `tar --xattrs`, rpm setugids.
7. Userspace: coprocessor daemons after peers; sleep hooks in `/usr/lib/systemd/system-sleep/`; `RemainAfterExit=yes`; broken resume mimics feature bugs.
8. Audio = UCM + amp firmware; no volume before protection.
9. Verify: prove by running, CPU time not wall time, rotation by eye, harness-not-the-bug.
10. Sweep sibling ports first: siblings solve blob questions; you solve boot chain + rootfs. (For us: map220v = device
    drivers/blobs list, pmOS OnePlus 15 = boot chain/packaging/SoC fixes, troikoss = method + desktop stack.)

### C. aaronsb/sm-x800-linux (Tab S8+, SM8450, pmOS) — process + tooling reference
- Boot: ABL → **uniLoader** (shields mainline DT from Samsung ABL's DTBO application; kernel+DTB+initramfs embedded;
  `mkbootimg --header_version 4`, stock ramdisk, **stock os_version/os_patch_level kept for anti-rollback**). Lessons for
  our U-Boot: ABL hands over with **MMU off → alignment-safe code** (`-mstrict-align`, byte memcpy, reset-loop cause);
  loader must supply real `/memory` (size-0 placeholder dies) and `/chosen`; simplefb needs clocks + power-domains;
  DTB copy must not overlap carve-outs. Verify whether OnePlus ABL applies dtbo onto the handed DTB (erase/zero dtbo test).
- Rootfs in userdata (nested GPT pmOS image); **UFS LUN order changes between boots → always partlabel**.
- ADR-004 (distro-neutral split): core = kernel pin + patches + DTS + fragments, `files/` tree + install manifest, firmware
  manifest, boot tool, one version manifest; distros = thin (pmOS reference, ALARM second via pacstrap snapshot,
  `root=PARTLABEL=`, mkinitcpio firmware hook). → mirrors our architecture.
- Firmware "cartridge-dump": repo ships extractor only; `tools/fw-manifest.tsv` (name/source/glob/dest/tier
  initramfs|rootfs/class/status) + `fw-harvest.sh`; `make stage-fw` hard-fails if GPU zap missing from initramfs;
  on-device `fw-extract.sh` by partlabel; sensors registry from vendor + **persist** (factory calibration).
  WiFi/BT from linux-firmware when board-2.bin matches (vendor BDFs crashed ath11k) → check ath12k board-2 for WCN7860 iceland.
- Traps to pre-empt: DPMS-off silent hang → `consoleblank=0` + console-blank unit fallback; DPU vblank timeouts on resume;
  amp PLL runtime-suspend bug → udev keep-awake; topology rebuilt (`tools/mk-tplg.py`, correct serial line);
  **UCM volume cap** until protection fw; `serialN` aliases or geni serial fails and blocks interconnect sync_state;
  BT addr from persistent partition via udev oneshot `btmgmt public-addr`; **dwc3 host power_lost patch** after suspend
  (check on SM8850); suspend via `systemctl start systemd-suspend.service` over ssh; conservative charger limits.
- Tooling to copy: self-checking ordered `Makefile` (`make check` names next step), `tools/mkpatch` (generated patches,
  header names the upstream commit that obsoletes it), deploy guard against mismatched kernel build, `device-facts/`
  stock captures, runbooks, issue/variant-report templates.
### D. nura wiki (postmarketOS was renamed **Nura** on 2026-09-27; wiki.nura.eco = old pmOS wiki)
- wiki.nura.eco / nura.eco / images.nura.eco / gitlab are **blocked** from this container → read on the PC together with
  pmaports (Phase 0 step 1): OnePlus 15 page (feature matrix, install steps, ABL quirks), SM8850 SoC page.
- New from GitHub: infiniti-mainline also has **audioreach-topology** (`OnePlus-Infiniti.m4`, 2026-09-26 → template for an
  iceland `.m4`; map220v ships a prebuilt `OnePlus-Pad4-tplg.bin` — prefer a source `.m4`), **minkipc** (QTEE supplicant on
  mainline, TA files from Android `/data/vendor` — note: erased when userdata is overwritten), **libfprint** (goodix UDFPS,
  not applicable to Pad).
- No public Pad 4 / iceland mainline work anywhere besides map220v. Downstream SM8850 devicetree repos contain phones only;
  Pad overlays/project-id come from our own stock dtbo (already imported in the LineageOS track).
### D2. pmOS OnePlus 15 (`oneplus-infiniti`) work = PRIMARY BASE (user directive)
Plan principle: `device-oneplus-iceland` / kernel / `firmware-oneplus-iceland` / U-Boot are derived from the
infiniti work (same SoC, same OnePlus ABL); Pad 4 deltas come from map220v DTS/drivers.
**Access caveat:** gitlab.postmarketos.org + wiki.postmarketos.org are blocked from this container → real pmaports
`device-oneplus-infiniti` deviceinfo/APKBUILDs and wiki known-issues must be read from the user's PC (Phase 0 task).
What was read (github.com/infiniti-mainline, the upstream pmOS consumes):
- **U-Boot `main`** (vlinkz, v2026.10-rc5 +14): Kaanapali GCC/RPMh clocks, M31 eUSB2, PMIC arb v8, PMH0101, pinctrl,
  **of_fixup: passes ABL's `/memory` to OS FDT + EFI map** (solves reserved-memory/zero-RAM problem), blkmap, fastboot fix.
  `configs/infiniti_defconfig` (qcom_defconfig + DTS, env file, fastboot buf 0xc6000000, VIDEO_SIMPLE, BUTTON_GPIO, no FS writes,
  EFI_VARIABLE_NO_STORE). Env: `bootcmd=run userdata_blkmap; bootefi bootmgr; fastboot usb 0` — OS = full disk image
  (pmOS_boot+pmOS_root) written into **userdata**, booted via EFI (systemd-boot), never written by U-Boot.
  DTS `arch/arm/dts/kaanapali-oneplus-infiniti.dts` 243 lines: simplefb @0xfc800000 (ABL splash), memory ranges, UFS,
  eUSB2+dwc3 peripheral, SPMI PON/resin/vol-down.
  Boot image: `gzip u-boot-nodtb.bin; cat .gz dtb > Image.gz-dtb; mkbootimg --kernel … --pagesize 4096 --base 0x80000000`;
  `fastboot flash boot`; stock vendor_boot kept; `fastboot erase dtbo` optional. Stock chain never modified.
  Alt branch `eykc/oneplus-15`: read-only extlinux from a FAT partition, UFS PWM (slow, expected).
- **Kernel `infiniti-mainline/linux` master** = v7.3-rc4 +138 (vlinkz). SoC-level commits **missing in map220v**:
  ~25 firmware reserved-memory carveouts + ADSP size fix, q6v5_pas handover/sysmon fixes, GPR/apr fixes, GPU cooling trips,
  gpucc CX GDSC, gcc PCIe fixes, clk-branch/dispcc fixes, QCE crypto + TRNG, **Iris video**, **full CAMSS/CCI/CSI2 PHY**,
  ADC5 Gen4 + haptics, **qmp-combo USB3+DP PHY + DP controller**, SMMU MDSS client, UFS lane clocks, geni console fix,
  qcomtee large shm, DSC 1.2 fixes, cluster PD split, rpmh-stats. Conflicts to reconcile: GMU @3d6c000 (infiniti) vs
  @3d37000 (map220v); CPU perf via scmi_perf power-domains vs clocks. map220v-only: `mdss_dsi1` + PHY (dual DSI).
- **firmware-oneplus-infiniti**: pmOS-style Makefile (`install -Dm644` lib/ usr/), `lib/firmware/qcom/kaanapali/OnePlus/Infiniti/*`,
  `usr/share/qcom/kaanapali/OnePlus/infiniti/{sensors,socinfo}` (hexagonrpcd). Pad 4 = same set + cdsp, novatek fw, gngbt BT, tplg.
- **PrestarLin/oneplus15-mainline** (read in full; 3 files, 2 commits): GitHub Actions on `ubuntu-24.04-arm` runner
  builds infiniti `eykc/oneplus-15` (v7.0) with `defconfig` + 13-line `kaanapali.config` merged via `merge_config.sh`
  (DRM/MSM, panel, dispcc, LLCC, UFS, USB configfs built in), greps `.config` to prove symbols landed, packages
  Image + dtbs + config + BUILD_INFO (kernel commit, CI commit, run URL), rolling `mainline-latest` prerelease.
  Key lesson: boot tool "SfbKernelBoot/mainlinedebug" does not patch `/memory` → size-0 → early crash → **EDL (9008)**.
  Fix: `fdtput -t x $DTB /memory@a0000000 reg $(cat memory-map.txt)` with the **21 usable-RAM segments copied cell-by-cell
  from the stock Android FDT** (OnePlus 15 values, 2-cell addr/size, up to 0xa_0000_0000+). For iceland (12 GB) the
  equivalent must come from our own `/proc/device-tree/memory*/reg` (DSU root) — never reuse OP15 values.
  → Adopt: (a) CI pattern (arm64 runner, fragment merge + grep check, BUILD_INFO provenance) for our kernel;
  (b) `memory-map.txt` + fdtput step as **mandatory safety step for any boot where U-Boot's of_fixup is not in the path**
  (diagnostic direct-ABL boots). With U-Boot `main`, of_fixup passes ABL's map instead — verify in live FDT.
### F. Project-Silicium/Mu-Silicium (UEFI, EDK2/Project Mu) — SECONDARY / reference
- `Silicon/Qualcomm/KaanapaliPkg` (SM8850-AC/-5-AC/-1-AD) + `Platforms/OnePlus/infinitiPkg` **Active**: UEFI display
  (ABL framebuffer 0xFC800000), UFS, buttons, USB device + **UFS mass storage**; no USB host/Windows. Linux via **DT**
  (DTB baked into firmware via DtPlatformDxe; GRUB/systemd-boot `devicetree` can override); pmOS reported with FantomTchi7 kernel.
- Output = header-v4 boot image (BootShim + FD + stock DTB) → `fastboot boot`/`boot_a`, no vendor_boot. Uses Qualcomm
  proprietary DXE drivers extracted from stock `xbl`/`uefi` (UEFIReader); EFI vars RAM-only; memory map from
  `uefiplat.cfg` (MemoryMapLib) + RAM partition table at runtime → OS gets a proper UEFI memory map.
- No iceland/Pad port. Port = copy infinitiPkg + our xbl/uefi dump + iceland DTB + framebuffer 2400×3392 + DXE/APRIORI lists.
- **Verdict:** primary stays U-Boot (open source, DTB from ESP, no firmware-version-matched blobs). Use Mu-Silicium for:
  (1) reference data — SM8850 memory/configuration maps (`infinitiPkg/Library/{MemoryMapLib,ConfigurationMapLib}`),
  GIC addresses, stock OP15 DTB (`Resources/DTBs/infiniti.dts`, msm-id 0x294/0x295, board-id 8) to cross-check iceland;
  (2) **fallback boot path** if U-Boot bring-up stalls (iceland port, RAM-boot, UFS mass-storage for installs/recovery).
  Windows not possible today (no Kaanapali ACPI).

### G. LeeSiWal/y700-linux (Lenovo Legion Y700 gen-4 TB323FU — **same SM8850 "canoe"/kaanapali**, Adreno 840v2)
- NOT mainline: Ubuntu 26.04 on stock GKI 6.12 + ~144 vendor modules, custom `init_boot_a` ramdisk, root on microSD;
  boot chain/kernel do not transfer. Value = **same-SoC hardware facts on a tablet**:
- DT/address cross-check: kgsl `3d00000`, **`gmu@3d37000`** (matches map220v, not infiniti's 3d6c000 → keep map220v value
  unless proven otherwise), PCIe `1c00000`, pmk8850 vadc, QUP SPI touch, BT UART `1994000`, ADSP `3000000`.
- Firmware locations on SM8850 vendors: GPU gen80200 in vendor `/firmware`; Wi-Fi/ADSP/jsn in `modem_a:/image` (FAT);
  BT in `bluetooth_a` (FAT) → our extractor needs FAT readers for `modem_a`/`bluetooth_a` + vendor ext4/erofs. (Y700 BT is
  `brh*`; Pad 4 per map220v is `gngbt*` — confirm Pad 4 name from `bluetooth_a`, check btqca support.)
- **Thermal trap:** prime cores 66→100 °C in ~2 s at 4.6 GHz and CPU zones have **no cooling device** without Android's
  thermal-engine → our DTS must bind cpufreq/GPU cooling maps to CPU/GPU trips (infiniti GPU trips + add CPU maps) before
  any sustained load; `cpufreq` sane default governor.
- ADC5 Gen4 (connector/battery thermal zones) needed → infiniti ADC5 Gen4 commits in patch queue (already listed).
- Audio: working AudioReach graph (shared-mem EP → PCM conv → I2S sink, LPAIF primary, SD1, 32-bit, GC/ACDB container type)
  = concrete reference for our topology; speakers only after protection.
- Sensors: hexagonrpcd **`adsp_listener_get_in_bufs2` gap** for >256 B registry writes (same issue troikoss patched) → include
  patch; SSC via QRTR node 5.
- Battery: charge-limit not enforced without Android → expose via `charge_control_end_threshold` / userspace.
- Two USB-C ports share one dwc3 on Y700 (Pad 4 has one port — n/a). Touch Novatek TDDI host-downloaded fw tied to panel
  events (same as Pad 4); pen needs resolution props for libinput. Turnip/Mesa 26.2 knows Adreno 840 (0x44050a31);
  FEX + Steam ARM64 run → Phase 8 userspace target.

### H. skb8/linux-sm8750 (OnePlus 13 "dodge", SM8750) — low value
- Single branch on 7.2-rc1; **no SoC/driver commits** (all SoC files byte-identical to upstream/map220v); DTS doesn't
  compile; no Pad 3 (erhai) content. Not a code source.
- Adopt only: (1) one "boot.img-derived requirements" doc (`docs/device-facts/bootimg-derived.md`) with real values from
  stock boot/vendor_boot/dtbo + `/proc/device-tree`; (2) its "what to collect" checklist for Phase 1;
  (3) **warning from sm8750-mainline (index986) DTS: enabling ADSP killed simple-framebuffer** → keep display
  clocks/power-domains on simplefb (+ `clk_ignore_unused pd_ignore_unused`) until MDSS takes over; enable remoteprocs one at a time.
- Better SM8750 sibling sources if needed: sm8750-mainline/linux (`OnePlus-13-WIP`), OnePlusOSS sm8750 modules/devicetree
  (Pad 3 overlays) — reference only.

### E. troikoss repo + Hardware-Notes (Tab S9 Wi-Fi, SM8550, Fedora)
- Kernel: tarball 7.2-rc3 + `kernel/prepare.sh` (pmOS-APKBUILD-style: patches `--forward`, DTS copy, sed OOT drivers into
  Kconfig, `merge_config.sh` base + fragment, `LLVM=1 olddefconfig`). Probe-critical = `=y` (no autoload); **`BT_HCIUART=m`
  on purpose** (built-in probes before rootfs firmware, hci_qca never retries); `ATH1xK=m`.
- Reusable SoC patches to check vs SM8850: pcie0 pipe-mux unpark, **wcn pwrseq cold-reset via AOP** (+ `qcom,wlan-pdc-init`),
  ADSP "handover" log-flood quieting (dmesg 99.98 %), ignore ABL `console=null`, DP/USB-C msm-dp + tcpm retained role,
  qcomtee, sc8280xp MI2S dai fmt.
- Initramfs: dracut `hostonly=no` + GPU fw `install_items` + usbnet debug hook. Rootfs: `dnf --installroot` in fedora arm64
  container, builds libssc / pd-mapper / hexagonrpcd(+patches) / iio-sensor-proxy(`-Dssc-support`), ownership fix, preset
  file (first-boot `preset-all` otherwise disables everything).
- Firmware staging: pinned URL/path + SHA-256, fatal on mismatch; exact blob names (vpu); `bdftool.py` board-2.bin ABI slot.
- Installer safety: identity props, partlabel, exact sizes, typed `DESTROY`, never format/reboot.
- Kernel RPM lesson → **diverge**: ship DTB in package (`/usr/lib/modules/<kver>/dtb/`), let kernel-install/BLS / GRUB /
  systemd-boot pick new kernels on the ESP; persistent module-signing key or `MODULE_SIG=n` (their per-run key pairs
  bundle↔RPM); cmdline in loader entries.
- Hardware traps (G = SoC-generic): ABL handoff leaves panel DDIC dead → one-shot pm_test suspend revive (S pattern, check
  NT36536 TDDI); DT2W needs wakeup-source + rails on (G); pen palm rejection 250 ms (S); amp protection fw fatal-if-missing,
  UCM per-amp volume cap, no-mixer soft volume (G); Wi-Fi firmware *family* + board-2 exact match + self-managed regdomain
  (5 GHz needed `CFG80211_CERTIFICATION_ONUS`) + PCIe re-enumerate recover unit (G); BT addr → **fdtput into DTB on ESP**
  (in our chain: U-Boot fixup or ESP DTB) (G); GPU fw in initramfs, mdt vs mbn (G); iris loads fw on first open, stateful
  M2M only, mpv `v4l2m2m-copy` (G); SSC: hexagonrpcd rootpd+sensorspd `-R`, writable persist registry, restart after resume
  via `/usr/lib/systemd/system-sleep` waiting on list-jobs (G); camss one failing sensor blocks all, in-DT I2C sweep (G);
  **battmgr unusable there because ADSP fw lacks `charger_pd`** → check early on iceland (map220v uses OPLUS battmgr, likely OK);
  s2idle `mem_sleep_default=s2idle` (G); mem-reclaim of dead downstream carve-outs (G).
- Overlay templates to port (renamed): UCM tree, sleep hook + libexec wait logic, adsp-boot/wait units, hexagonrpcd drop-ins,
  vendor/persist mount units, udev mount-matrix/devfreq/fastrpc rules, logind lid, journald cap, zram, preset.


## Decisions (user, 2026-09-27)
- Boot path: **U-Boot chainloaded by ABL, OnePlus 15 style** — U-Boot boot.img in `boot_a`, distro disk image in `userdata`
  (Android erased), EFI/systemd-boot, fastboot fallback. Direct-ABL is only a diagnostic fallback.
- pmaports `device-oneplus-infiniti` (deviceinfo/APKBUILDs/wiki known issues) to be read **on the user's PC** in Phase 0.

- Target: **one mainline kernel for every rootfs** (Fedora, Ubuntu/Debian, Arch, pmOS, Kali, …). Device support lives
  in kernel + DTB + firmware + a small distro-neutral userspace overlay; distros are thin packaging wrappers.

## Architecture — "one kernel, any rootfs"
```
ABL (stock, untouched) → boot_a: U-Boot boot.img (iceland DTS, simplefb, UFS, keys, fastboot)
  → blkmap userdata → EFI boot manager → \EFI\BOOT\BOOTAA64.EFI (systemd-boot or GRUB, distro's choice)
    → our kernel Image + our DTB (kaanapali-oneplus-iceland.dtb) + distro-generated initramfs → distro rootfs
```
| Layer | Owned by | Distro-specific? |
|---|---|---|
| U-Boot boot.img | us (fork of infiniti-mainline/u-boot `main`) | no — flashed once |
| Kernel Image + DTB + modules | us (map220v base + infiniti SoC fixes) | no — one build; packaged as rpm/deb/pkg/apk wrappers + plain tarball |
| Firmware | extracted from the user's own 11.A.38 partitions, pinned sha256 | no — one `lib/firmware` tree |
| Device overlay (UCM, udev hwdb, hexagonrpcd/sensors config, sleep hooks, systemd units) | us | no — FHS paths under `/usr/lib` (troikoss: `/etc` sleep hooks are inert) |
| Initramfs | distro tool (dracut / initramfs-tools / mkinitcpio / mkinitfs) | yes — plugin/hook adds UFS + firmware |
| Bootloader entry | systemd-boot `devicetree` key or GRUB `devicetree` | yes — template per loader |
| Rootfs + desktop | distro | yes |

Kernel packaging: DTB shipped in `/usr/lib/modules/<kver>/dtb/` + copied to ESP by kernel-install/loader hooks;
persistent module-signing key (or `MODULE_SIG=n`); cmdline in loader entries (`root=PARTLABEL=`/UUID, `mem_sleep_default=s2idle`).
Kernel config rules for rootfs neutrality (exception: `BT_HCIUART=m`, `ATH12K=m` — must probe after rootfs firmware): boot-critical drivers **built in** (UFS qcom, PHYs, pinctrl/clk/icc/rpmh,
GENI, simpledrm, ext4/btrfs/xfs/vfat, dm/dm-crypt) so any initramfs (or none) reaches root; union of distro needs
(systemd, cgroup v2, namespaces/containers, SELinux + AppArmor + Landlock compiled in, BPF, nftables, squashfs/overlayfs,
zram, EFI stub, module compression zstd + signing optional); `CONFIG_EFI_ZBOOT` off/on per loader test. Validate with
`systemd`'s `README` kernel requirements and distro config checkers (e.g. Docker `check-config.sh`).
DTB delivery: U-Boot passes the kernel DTB loaded from the ESP (`fdtfile=qcom/kaanapali-oneplus-iceland.dtb`) or the
loader's `devicetree` directive; U-Boot's own minimal DTB must never reach Linux (verify live FDT: `/proc/device-tree/model`).

## Where the work lives (user directive, 2026-09-27)
- **All work in private GitHub repos**, built in this cloud container / GitHub Actions (arm64 runners). Nothing is
  written to the user's PC/WSL unless the user asks. Tablet commands are the only thing run locally, by the user.
- GitHub is **not connected** to this session yet (no repos listed, no `gh`). User: connect at claude.ai/connect-github,
  create empty **private** repos (proposed names below), then they are attached here with push access.
- Proposed private repos (one per GPL component, keeps licences clean):
  | Repo | Content | Licence |
  |---|---|---|
  | `iceland-linux` | kernel fork: map220v `iceland-7.2` history + infiniti patch queue as commits | GPL-2.0 (upstream COPYING, SPDX headers kept) |
  | `iceland-u-boot` | fork of infiniti-mainline/u-boot `main` + iceland DTS/defconfig/env | GPL-2.0+ (U-Boot Licenses/) |
  | `iceland-mainline` | umbrella: docs, plan, device-facts, firmware **manifest + extractor (no blobs)**, overlay, distro wrappers, image builder, CI, hwcheck | GPL-2.0-or-later for scripts; overlay files per origin |
  | (later) `iceland-audioreach-topology`, `iceland-hexagonrpcd` patches | forks | upstream licences (BSD-3 / GPL-3) |
- **GPL compliance rules:**
  1. Forks keep full upstream history and authorship (no squash of others' commits); map220v/infiniti commits cherry-picked
     with original author + `(cherry picked from commit …)`; our commits carry `Signed-off-by:` (DCO) in upstream style.
  2. Every file keeps its SPDX header; new files get one; out-of-tree drivers imported from vendor GPL sources (OnePlusOSS)
     keep their copyright lines.
  3. Every binary we build (Image, dtb, modules, U-Boot boot.img, images) records the exact source commit (BUILD_INFO) so
     corresponding source is always reproducible; release artifacts only ever attached next to the tagged source.
  4. **Proprietary firmware is never committed or uploaded** (not even to private repos or CI artifacts): repos hold only
     the manifest (names, sha256, source partition) and the extractor; firmware is extracted from the user's own device/OTA
     at install time. map220v/iceland-firmware (no licence) is used only as a file-name list.
  5. Third-party non-GPL pieces (Mu-Silicium BSD, Qualcomm DXE binaries) not vendored; reference only.
  6. Repos stay private; any publication or contact with maintainers only after the user asks.
- Decided: user creates 3 empty private repos (`iceland-linux`, `iceland-u-boot`, `iceland-mainline`) after connecting
  GitHub; I attach them (push access) and work only there. Phase 1 capture = my read-only script, run once by the user
  on the PC, output uploaded by the user to `iceland-mainline`.
- First actions after approval (cloud only): write the capture script + README into `iceland-mainline` (so the user can
  run it while DSU is loaded), then Phase 0 (kernel fork + patch queue + CI, U-Boot fork, firmware manifest, tooling).
- DSU root is available on the tablet now (user, 2026-09-27) → Phase 1 capture runs when the user chooses to execute the
  capture script (committed to `iceland-mainline/the debug tooling (removed 13 Oct, not published)`, read-only, output uploaded to the private repo minus
  anything secret/blob). The tablet is attached to the user's PC, not this container.

## Plan
Rules: agent never flashes/boots/wipes; user runs every tablet command; one variable per experiment; every boot logged in
`logs/<date>-<n>/` (image sha256, cmdline, result). Repo `iceland-mainline/` layout (troikoss-style):
`u-boot/` (pin + patches) · `kernel/` (pin map220v + patch queue from infiniti) · `firmware/` (manifest + extractor) ·
`overlay/` (distro-neutral files) · `distro/{pmos,fedora,debian,arch,kali}/` (thin wrappers) · `image/` (disk-image builder)
· `tools/` · `docs/` · gitignored `artifacts/`, `logs/`.

### Phase 0 — Workspace & facts (PC only, no tablet)
1. Preferably in the cloud (user allowlists `*.nura.eco`, `gitlab.postmarketos.org` in the environment network policy;
   otherwise user pastes files): clone pmaports (Nura GitLab), read `device-oneplus-infiniti`, `linux-*infiniti*`, `firmware-oneplus-infiniti`,
   `u-boot-*`; read wiki.nura.eco OnePlus 15 + SM8850 pages (feature matrix, install steps, known issues incl. USB/external
   power, RAM-boot) → `docs/pmos-infiniti.md`. (Alternatively allowlist `*.nura.eco` / `gitlab.postmarketos.org` in the
   cloud environment's network policy.)
2. Pin sources: map220v `iceland-7.2` bc3e5fc8; infiniti-mainline/linux master; infiniti-mainline/u-boot `main` bce42004.
3. Kernel patch queue: cherry-pick infiniti SoC-level commits missing in map220v (list in D2), in groups
   (reserved-memory → remoteproc/GPR → clocks/GPU → USB-C/DP → iris → CAMSS → crypto/ADC); reconcile GMU address and
   scmi_perf wiring; keep map220v dual-DSI. Build with `LLVM=1` defconfig + sm8850.config + `distro-neutral.config`
   merged by `merge_config.sh`, then grep `.config` for every required symbol (PrestarLin CI pattern; troikoss "silent
   sed no-op" trap). Output bundle carries BUILD_INFO (kernel/CI commits). Optional CI on a GitHub arm64 runner (private
   until the user approves publishing).
4. Tooling (aaronsb): `Makefile` with `make check`, `tools/mkpatch`, `version-manifest`, deploy guard; `docs/device-facts/`.
5. Firmware manifest (aaronsb TSV format: name/source/glob/dest/tier/class/status; `stage-fw` hard-fails without GPU zap)
   from map220v/iceland-firmware list → source partition/path in 11.A.38 (mapped in the cloud from the official
   OPD2514_11.A.38 OTA if downloadable there — scratch only, never committed — else from the Phase 1 on-device listing),
   pinned sha256, fail loudly; path convention `qcom/kaanapali/OnePlus/iceland/` (pmOS style) with DTS updated to match.
   Include hexagonrpcd `usr/share/qcom/kaanapali/OnePlus/iceland/{sensors,socinfo}` from persist/vendor.
   Readers: vendor ext4/erofs, `modem_a` + `bluetooth_a` FAT images (Y700 layout on the same SoC).
Exit: reproducible kernel + DTB + modules + firmware tree; `dtbs_check` clean for the iceland DTS.

### Phase 1 — Evidence (tablet on Android, read-only, via existing DSU root)
`/proc/device-tree` (applied stock overlay), `/proc/iomem`, clk/regulator summaries, gpio dump, I2C map, remoteproc fw names,
ABL splash framebuffer address/size/stride (for U-Boot simplefb), **stock `/proc/device-tree/memory*/reg` → 
`memory-map.txt` for iceland (PrestarLin method; EDL-avoidance for any direct boot)**, copy of `xbl`/`uefi`
partitions from the existing backup + extracted `uefiplat.cfg` (Mu-Silicium fallback input, reference memory map), stock dtbo `__fixups__` → cross-check map220v DTS;
reconcile 45 stock reserved regions vs map220v 30 vs infiniti carveouts. BT/Wi-Fi MAC location (bluetooth/persist).
Before userdata is ever overwritten: file-level copy (root) of `/data/vendor` TEE/TA files (needed by minkipc/QTEE on
mainline; the raw userdata backup is FBE-encrypted and useless for this) and of `/mnt/vendor/persist` sensors registry.
Exit: evidence folder + reviewed reserved-memory patch + simplefb parameters.

### Phase 2 — U-Boot for iceland (RAM boot first)
Add `arch/arm/dts/kaanapali-oneplus-iceland.dts` (from infiniti's 243-line DTS: simplefb for 2400×3392 dual-DSI splash,
UFS, eUSB2/dwc3, PON/resin + vol-down PMH0101 gpio6), `configs/iceland_defconfig`, `board/qualcomm/iceland.env`
(same bootcmd; set `fdtfile`). Boot.img keeps stock `os_version`/`os_patch_level` (anti-rollback); build alignment-safe
(ABL hands over MMU-off); test whether ABL applies dtbo to the handed DTB (aaronsb uniLoader lesson). Build boot.img per `doc/board/qualcomm/board.rst`. User: `fastboot boot u-boot.img`
(nothing written). Answers: RAM boot allowed? header v4 OK? simplefb visible? UFS/GPT seen? fastboot fallback works?
If RAM boot refused → user flashes `boot_a` only, rollback = stock boot_a image (proven loop, 2 min).
Fallback if U-Boot stalls (clocks/UFS): port Mu-Silicium infinitiPkg → icelandPkg (needs Phase 1 dump of `xbl`/`uefi`
+ `uefiplat.cfg`), same EFI → distro flow, DTB supplied by the loader's `devicetree` directive.
Cross-check U-Boot memory ranges against Mu-Silicium `MemoryMapLib.c` (same SoC) and our stock FDT.
Exit: U-Boot console on panel, `part list scsi 0` shows userdata, fastboot from U-Boot works.

### Phase 3 — First Linux boot (distro-neutral debug image)
Minimal GPT disk image (ESP + ext4 root) built by `image/` from a tiny rootfs (pmOS via pmbootstrap first — best
debug initramfs + USB networking). Cmdline `clk_ignore_unused pd_ignore_unused console=tty0`, display driver off,
simpledrm; USB ECM gadget (not RNDIS), powered hub. User flashes image to userdata **after confirming Android loss +
backup of persist/oplusreserve** (already in the 151-partition backup).
Exit: SSH over USB, dmesg saved, live FDT = our DTB.

### Phase 4 — Core platform
cpufreq/idle, thermals: **CPU + GPU cooling maps bound to trips before any load test** (Y700: 100 °C in ~2 s), UFS root, USB role, keys, **lid (add TLMM 98 SW_LID gpio-key to DTS)**, remoteprocs
adsp/cdsp/soccp enabled **one at a time** (SM8750 precedent: ADSP start killed simplefb), battmgr battery/charging (**first confirm ADSP/SOCCP firmware exposes `charger_pd`** — troikoss
trap; full-charge check), pstore/ramoops node, rpmh-stats, `serialN` aliases (geni/BT), USB host resume (dwc3 power_lost
patch if needed), ADSP handover log quieting, `mem_sleep_default=s2idle`.
Exit: stable boot, battery sane, thermal zones present.

### Phase 5 — Display & input
Native DSI + NT36536 panel (map220v), KTZ8869 (fix remove() NULL, bias as regulator), DCS/backlight brightness,
refresh modes, DSC 1.2 fixes from infiniti; touch (firmware from odm), TDDI power ordering, tap-to-wake, pen buttons,
palm rejection. Exit: GNOME/KDE/Phosh usable by touch, screen off/on keeps touch.

### Phase 6 — Wireless
ath12k WCN7860 (board data/regdb from our firmware, drop-l3k check), BT hci_qca with **real BD address from persist**
(replace hardcoded `local-bd-address`; deliver via U-Boot DT fixup or fdtput on the ESP DTB — troikoss pattern), `BT_HCIUART=m`
+ `ATH12K=m`, wcn pwrseq cold-reset/PDC init if cold start fails, PCIe re-enumerate recover unit, ath12k board-2.bin
exact-match check, self-managed regdomain (5/6 GHz). Exit: Wi-Fi + BT with stable MACs.

### Phase 7 — Audio
6× TFA9865 + WCD9395, AudioReach topology built from source (`OnePlus-Iceland.m4` modelled on infiniti-mainline
audioreach-topology `OnePlus-Infiniti.m4`; map220v `OnePlus-Pad4-tplg.bin` as known-good reference), UCM profile in `overlay/`; volume capped until
speaker protection (tfa98xx.cnt from odm) is working. Exit: safe speaker playback, headset, BT audio.

### Phase 8 — GPU, video, USB-C DP
Adreno 840 (zap/sqe/gmu in initramfs via each distro's hook), Mesa freedreno/turnip; iris VPU (`vpu40_2v.mbn`, verify real
decode by CPU time); qmp-combo + DP alt-mode. Exit: 3D accel, HW decode measured, external display.

### Phase 9 — Sensors & cameras
hexagonrpcd + libssc + iio-sensor-proxy (persist registry), restart after resume, rotation checked by eye; CAMSS/CCI from
infiniti, identify Pad 4 sensors (stock camx), I2C sweep, libcamera. Exit: auto-rotate + ALS; one camera streaming.

### Phase 10 — Power management
Suspend/resume first-class; hooks in `/usr/lib/systemd/system-sleep/`. Exit: repeated suspend/resume, no regressions.

### Phase 11 — Multi-distro images & installer
`image/build.sh --distro {pmos,fedora,ubuntu,debian,arch,kali}`: bootstrap rootfs with the distro's own tool
(pmbootstrap / dnf --installroot / debootstrap or mmdebstrap / pacstrap / Kali live-build or debootstrap kali-rolling),
add our kernel package + firmware + overlay, run distro initramfs tool with our hook, install systemd-boot (or GRUB)
entry with `devicetree`, create GPT (ESP vfat + root), pack with `--xattrs`, fix ownership (troikoss tmpfiles trap).
Per-distro kernel packaging: `distro/<name>/` wraps the same Image/modules/DTB (kernel-iceland rpm, linux-image-iceland deb,
linux-iceland PKGBUILD, pmOS linux-oneplus-iceland APKBUILD). Kernel updates via distro package → loader entry updated,
no reflash (U-Boot stays). Installer: checks fastboot product `canoe`/unlocked/partition sizes, flashes only `boot_a`
(U-Boot) + `userdata`, typed confirmation, no auto-reboot, rollback bundle kept.
Exit: same kernel build boots ≥3 distros (pmOS, Fedora, Ubuntu) with identical hardware feature results.

### Phase 12 — Upstreaming
DTS + drivers to linux-arm-msm and iceland U-Boot DTS/defconfig upstream, coordinated with map220v and infiniti-mainline;
pmaports device package. Ask the user before any contact or publication.

## Hard stops (ask the user)
Any flash or RAM boot · slot switching · slot b before it has 11.A.38 · writing userdata (erases Android) ·
partitions other than boot_a/userdata · firmware not from this tablet's 11.A.38 · publishing / contacting maintainers.

## Verification
- Build: kernel + dtbs + modules reproducible (sha256 stable across two clean builds); `make dtbs_check` for iceland DTS;
  U-Boot boots in QEMU is not possible (SoC) → verify boot.img structure with `unpack_bootimg`.
- Per boot: log image hashes, `/proc/device-tree/model` = "OnePlus Pad 4", `dmesg` saved, firmware load lines checked by
  exact filename (no silent fallback).
- Feature exits measured on device (CPU time for decode, eye for rotation, repeated suspend cycles).
- Distro neutrality: feature checklist script (`tools/hwcheck.sh`, POSIX sh, no distro deps) run on each distro image;
  results must match.

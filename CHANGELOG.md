# Changelog

Work on mainline Linux for the OnePlus Pad 4 (`iceland`). Newest first. The repositories and references are listed in
[PROJECT.md](PROJECT.md). Every tablet run is in [docs/tests/README.md](docs/tests/README.md).

Repos: [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) ·
[iceland-linux](https://github.com/mzakamin-hub/iceland-linux) ·
[iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) (all private).

## 2026-09-28 — Linux on the tablet (Phase 2, in progress)

### Display: keeping the ABL framebuffer alive
The framebuffer console shows kernel text, then the panel goes black or white. Each test removed one cause:

| Test | Symptom | Cause found | Fix |
|---|---|---|---|
| 2 | black after the text | unused regulators and the backlight turned off | `regulator_ignore_unused`; both KTZ8869 backlight nodes disabled in the debug DT (iceland-u-boot 35cb950, iceland-mainline 7a39818) |
| 3 | white, no USB | display pipeline released (the DT had no framebuffer with votes) | Pad 4 DT describes ABL's splash framebuffer: clocks, MDSS GDSC, MMCX vote, `cont_splash_mem` no-map (iceland-linux c17f732) |
| 5 | white | simpledrm voted MMCX **SVS**, but ABL runs the MDP at 650 MHz = **TURBO**; orphan DSI byte/pixel clocks | MMCX TURBO, DSI clocks dropped (iceland-linux 27326fe) |
| 6 | white at 20–30 s | at the deferred-probe timeout (~22 s) rpmhpd sync_state switches off rails nobody votes for: **MXC went off** (on kaanapali, MMCX has no MXC parent). The `qnm_mdp` interconnect vote is also 0. | MXC TURBO vote (iceland-linux 2728bb9, test 7). Stock data from the PC then showed dispcc needs **MX**, so test 7 was replaced by **test 7b**: A = MMCX+MX+MXC votes (fe964f7), B = A + sync_state disabled (debug patch). The MDP bandwidth vote comes next if needed. |

### Linux debug image and tablet script (iceland-mainline `tools/linux-ram/`)
- `run-linux.ps1` can now boot several Linux images in one session, going back to Android in between, with results in one folder per image. `package.sh` builds a kit from U-Boot diag L plus labelled images. Dry-run against the mock tablet: A and B both completed using only allowlisted commands.
- The PC relay is in use: `relay/requests/001-linux-test-7b.md`, with the bundle on branch `relay-bundles`.
- 359c8f7: first Linux RAM boot through U-Boot fastboot:
  - header v2 image with the kernel, a debug DTB and a busybox initramfs;
  - USB NCM network (tablet 172.16.42.1; the PC gets 172.16.42.2 by DHCP);
  - busybox httpd with report CGI pages, and a reboot CGI.
- 24ca3b9: boot through U-Boot EFI (diag L). Linux test 1 showed bootm ran the kernel in place (XIP) from the unaligned buffer at 0xc6001000.
- 7a39818: timed report pages; panel power and backlight kept on.
- 9fd5ee4: ramoops at 0xff300000 and a `pstore` page, so the log survives a warm reset. The framebuffer node now comes from the Pad 4 DT.
- 728c0a0: fixed the report download on Windows PowerShell 5.1:
  - CGI headers now use CRLF;
  - the script uses a raw TCP HTTP client (PS 5.1 rejects bare-LF headers).
- 24b0d42: full hardware survey in one run, 16 pages:
  dmesg, timeline, info, unbound, deferred, genpd, interconnect, regulators, clocks, gpio, pinctrl, irq, thermal, buses, power, pstore.
- f16e720: Linux test 5 survey. Also found:
  - six TFA9865 amps on i2c 0/4;
  - touch SPI, ADC, watchdog, crypto and audio need modules;
  - **CPU thermal zones have only 120/125 °C trips and no passive cooling**, which must be fixed before any load.
- 9833de2: "white" answer added to the screen questions.
- Linux test 6 survey saved in `docs/tests/linux-run6/`.

### Kernel (iceland-linux)
- e7db143: rebased on **Linux 7.3-rc4 + infiniti-mainline** (OnePlus 15, same SoC):
  - `0001-infiniti`: 138 commits, tree hash verified against infiniti master 10650ae7bef4.
  - `0002-iceland`: the map220v Pad 4 series ported with authors kept, plus our commits.
  - Our commits: the panel added to the upstream `panel-novatek-nt36536` driver as `csot,xn251`; battmgr uses infiniti's OPLUS variant (`oneplus,iceland-pmic-glink`); modem remoteproc and smp2p deleted (SM8850P has no modem); the DSI0-sync commit dropped for now.
  - Builds with 0 warnings as `7.3.0-rc4-iceland-00158`.
- f237d15: manual-only CI workflow (`workflow_dispatch`).
- `scripts/prepare.sh`: `git am` with a tree-hash check after each series.
- `scripts/build.sh`: defconfig + `sm8850.config` + `distro-neutral.config`, a strict check of the required config, and dist output with BUILD_INFO.
- c17f732, 27326fe: framebuffer description and power votes (see the table above).

### U-Boot (iceland-u-boot)
- 85f8b49, 35cb950, c9aeab2: diag environment **L**. U-Boot fastboot receives a header v2 Linux image; `fastboot_bootcmd` parses the header and runs `bootefi kernel ramdisk dtb`. Cmdline: `earlycon=efifb`, `*_ignore_unused`, `log_buf_len=4M`.

## 2026-09-28 — U-Boot runs on the tablet (Phase 1 done)
- 82df40f: U-Boot patch queue:
  - base v2026.10-rc5 + 14 infiniti-mainline patches;
  - Pad 4 board: DTS, defconfig, environment, `qcom,msm-id 0x295/0x20000`, `board-id 8`;
  - **fastboot flash disabled**, console record + `fastboot oem console` enabled.
- 6b7e79d, 2fe73e4: failsafe RAM-boot test script and a one-shot diagnostic run. They only use allowlisted commands.
- U-Boot test 1 and diag run 2: ABL accepts the RAM boot, but U-Boot died because ABL drops a DT appended after the gzip stream.
- e1fa2c9: tested three ways of handing U-Boot its DT.
- 0e645fc: packaging changed to **header v4, kernel = gzip(u-boot.bin)**. Diag run 3:
  - U-Boot runs;
  - framebuffer 0xfc800000, 3392x2400 confirmed;
  - the USB gadget appears (VID/PID 18D1:D00D).
- Diag run 4, with the Windows driver bound to U-Boot's gadget:
  - fastboot works from Windows (`product oneplus-iceland`); `oem console` log retrieved;
  - UFS HS-G5 x2 (Samsung KLUEG4RHKF), 6 LUNs, GPT read;
  - DRAM banks match the DT;
  - normal boot falls back to fastboot as designed.
- 672bd15, 53139ed: test logs.

## 2026-09-28 — Plan v3
- 68d8b5b: plan v3 ([docs/PLAN.md](docs/PLAN.md)):
  - built on the results verified on the tablet;
  - faster order of work: RAM-boot Linux through U-Boot, pmOS only until the hardware works, upstream as we go;
  - realistic distro scope: one kernel source and config packaged per distro; Tier 1 pmOS / Fedora / Arch ARM; Tier 2 Debian testing / Kali / latest Ubuntu; Debian stable and Ubuntu LTS not supported (Mesa too old for Adreno 840);
  - Mu-Silicium fallback dropped.

## 2026-09-27 — Device facts, firmware manifest
- 00afc4a, a718977: plan v2 and read-only capture tools for Android with DSU root (`tools/capture/`).
- 0bafbbb, a4192c1, a6bd734: captures 1–3 in `docs/device-facts/`:
  - ABL memory map (20 segments, 11.5 GiB), 68 reserved regions;
  - display framebuffer, I2C/SPI map, remoteprocs, firmware locations;
  - live and stock DTs, iceland-O-IN fixups.
  - Capture scripts fixed along the way: devicetree path, endianness, Windows-safe names, tar transfer, adb lookup, serial and MAC redaction.
- 106d125: firmware manifest. 21 files, with the stock 11.A.38 source and sha256 for each. No blobs are committed.

## 2026-09-27 — Discovery and repositories
- Studied the reference projects listed in [PROJECT.md](PROJECT.md): map220v, infiniti-mainline, pmOS/Nura OnePlus 15, troikoss, aaronsb, Mu-Silicium, PrestarLin, Y700, SM8750. Notes are in [docs/RESEARCH.md](docs/RESEARCH.md).
- Created the three private repos.
- b94d38b (iceland-linux): first patch queue, v7.2 + map220v `iceland-7.2` (40 commits). It was superseded by the 7.3-rc4 rebase.

## Next
1. Run Linux test 7b (relay request 001): A = MX vote, B = A + sync_state disabled. If the panel still turns white, add the MDP interconnect vote.
2. Load modules in the debug initramfs (touch SPI, ADC, TFA9865…).
3. Add CPU passive thermal trips and cooling maps before any load.
4. Firmware extractor, run once by the user.
5. Phase 3 hardware bring-up, in the order of [docs/PLAN.md](docs/PLAN.md).

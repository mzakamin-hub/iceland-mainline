# OnePlus Pad 4 mainline Linux — project index

**Device:** OnePlus Pad 4, codename `iceland`, model OPD2514, SoC Qualcomm SM8850P
(`kaanapali`/`canoe`), stock firmware 11.A.38, bootloader unlocked, A/B.

**Goal:** a mainline kernel and U-Boot that boot current arm64 distros through EFI:
- Tier 1: pmOS, Fedora, Arch Linux ARM
- Tier 2: Debian testing, Kali, latest Ubuntu

The plan is in [docs/PLAN.md](docs/PLAN.md). History is in [CHANGELOG.md](CHANGELOG.md). Everything learned so far is in [docs/KNOWLEDGE.md](docs/KNOWLEDGE.md).

## Current state (2026-09-28)

| Stage | State |
|---|---|
| ABL accepts a RAM boot (`fastboot boot`) | ✅ nothing is written to the tablet |
| U-Boot on the tablet (display, USB fastboot, UFS, log over USB) | ✅ Phase 1 done |
| Linux 7.3-rc4 starts through U-Boot EFI; earlycon on the panel | ✅ |
| USB network (NCM), HTTP survey pages, HTTP reboot | ✅ |
| Framebuffer console stays on | ❌ the panel turns white after 20–30 s; a fix is in progress (MXC rail vote) |
| Native display, touch, Wi-Fi, battery, audio, GPU… | not started (Phase 3 onwards) |

## Our repositories (private, GitHub user `mzakamin-hub`)

| Repo | Contents | Licence |
|---|---|---|
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this repo) | plan, research, device facts, test log, firmware manifest (no blobs), capture tools, Linux RAM-boot debug image tools | GPL-2.0-or-later (scripts) |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | kernel patch queue: upstream v7.3-rc4 + `0001-infiniti` (138) + `0002-iceland` (21); config fragments; build/prepare scripts; manual CI | GPL-2.0 |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | U-Boot patch queue: v2026.10-rc5 + infiniti-mainline (14) + Pad 4 board; build scripts; failsafe tablet test and diagnostic scripts | GPL-2.0+ |

The repos hold only sources and scripts; proprietary firmware is never committed. Every binary we build records its source
commits in `BUILD_INFO`.

### Where to find things

| What | Where |
|---|---|
| Plan v3 (current) | [docs/PLAN.md](docs/PLAN.md) |
| Discovery notes, plan v2 | [docs/RESEARCH.md](docs/RESEARCH.md) |
| Device facts: memory map, reserved memory, I2C/SPI map, stock and live DTs | [docs/device-facts/](docs/device-facts/) |
| Tablet test log (every run) | [docs/tests/README.md](docs/tests/README.md) |
| Linux survey logs | [docs/tests/linux-run5/](docs/tests/linux-run5/), [docs/tests/linux-run6/](docs/tests/linux-run6/) |
| U-Boot logs | [docs/tests/uboot-run4/](docs/tests/uboot-run4/) |
| Firmware manifest (names, stock source, sha256) | [firmware/manifest.tsv](firmware/manifest.tsv) |
| Read-only capture scripts (Android + DSU root) | [tools/capture/](tools/capture/) |
| Linux RAM-boot debug image + tablet script | [tools/linux-ram/](tools/linux-ram/) |
| Kernel pin, patches, configs, port log | iceland-linux: `kernel.pin`, `patches/`, `configs/`, `docs/PORT-LOG.md` |
| U-Boot pin, patches, diagnostic environments | iceland-u-boot: `uboot.pin`, `patches/`, `tools/diag/` |

### Pinned sources

| Component | Pin |
|---|---|
| Linux | [torvalds/linux](https://github.com/torvalds/linux) `v7.3-rc4` (93f51579e7df) |
| infiniti kernel | [infiniti-mainline/linux](https://github.com/infiniti-mainline/linux) master 10650ae7bef4 |
| Pad 4 kernel series | ported from [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) `iceland-7.2` bc3e5fc8 (authors kept) + our commits |
| U-Boot | [u-boot/u-boot](https://github.com/u-boot/u-boot) `v2026.10-rc5` (a06e89ab0) |
| infiniti U-Boot | [infiniti-mainline/u-boot](https://github.com/infiniti-mainline/u-boot) `main` bce42004f |
| mkbootimg | [LineageOS/android_system_tools_mkbootimg](https://github.com/LineageOS/android_system_tools_mkbootimg) 808ecd09 |
| Debug initramfs busybox | Ubuntu `busybox-static` 1.36.1-6ubuntu3.1 arm64 (sha256 pinned; [source](https://launchpad.net/ubuntu/+source/busybox/1.36.1-6ubuntu3.1)) |

## Reference projects (read, not vendored)

| Project | Used for |
|---|---|
| [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) (`iceland-7.2`) | Pad 4 DTS and drivers: dual DSI + NT36536 panel, KTZ8869 backlight, Novatek touch, TFA9865 audio, OPLUS battmgr |
| [map220v/iceland-firmware](https://github.com/map220v/iceland-firmware) | list of firmware file names only (no licence, not used as a source) |
| [infiniti-mainline/linux](https://github.com/infiniti-mainline/linux) | OnePlus 15 (same SoC) kernel: SoC fixes, carve-outs, remoteproc, Iris, CAMSS, DP, ADC5 Gen4… |
| [infiniti-mainline/u-boot](https://github.com/infiniti-mainline/u-boot) | Kaanapali U-Boot: clocks, eUSB2, PMIC, ABL memory-map fixup, fastboot |
| [infiniti-mainline/firmware-oneplus-infiniti](https://github.com/infiniti-mainline/firmware-oneplus-infiniti) | firmware packaging layout (pmOS style) |
| [infiniti-mainline/audioreach-topology](https://github.com/infiniti-mainline/audioreach-topology) | `OnePlus-Infiniti.m4` as the template for a Pad 4 topology |
| pmaports `device-oneplus-infiniti` (pmOS / Nura GitLab) and [wiki.nura.eco](https://wiki.nura.eco) OnePlus 15 and SM8850 pages | pmOS packaging and known issues (blocked from the cloud container; to read on the PC) |
| [troikoss/gts9wifi-fedora](https://github.com/troikoss/gts9wifi-fedora) (and its wiki: Porting Guide, Hardware Notes) | porting method ("find the missing layer"), Fedora packaging, hardware traps |
| [aaronsb/sm-x800-linux](https://github.com/aaronsb/sm-x800-linux) | device-facts, firmware manifest format, distro-neutral split, pitfalls |
| [Project-Silicium/Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium) | SM8850 memory/config maps for cross-checks (UEFI fallback dropped in plan v3) |
| [PrestarLin/oneplus15-mainline](https://github.com/PrestarLin/oneplus15-mainline) | CI pattern (fragment merge, config grep, BUILD_INFO); `/memory` EDL lesson |
| [LeeSiWal/y700-linux](https://github.com/LeeSiWal/y700-linux) | Lenovo Y700 gen 4 (same SoC tablet): address cross-checks, thermal and sensor traps |
| [skb8/linux-sm8750](https://github.com/skb8/linux-sm8750) | SM8750 notes (ADSP start killed simplefb) |

## Safety rules (standing)

- Only the user runs tablet commands. The agent never flashes, unlocks, wipes or switches slots.
- Test scripts only RAM-boot (`fastboot boot`) and use allowlisted fastboot, adb and HTTP commands. U-Boot is built without fastboot flash.
- Proprietary firmware is never committed or uploaded. The capture `private\` folder is never uploaded.
- All repos stay private. Nothing is published and no maintainer is contacted without the user's OK.
- Commits: `mzak <mzak.amin@gmail.com>` with `Signed-off-by`. Other people's commits keep their authorship.

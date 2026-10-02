# Documentation plan - OnePlus Pad 4 ("iceland") mainline Linux

Workflow "docs", started 2 Oct 2026 (evening). Owner of this folder: the documentation / SME agent. Everything here
is a draft for the main session to review and commit; nothing in this folder is committed by the agent.

## Audiences

| Audience | Needs | Style |
|---|---|---|
| A. General Linux user who owns a Pad 4 | understand what works, build their own kernel + image from our trees, RAM-boot it safely, collect logs; later install | guide style: numbered steps, prerequisites, expected output, warning boxes, "proven / not yet proven" markers |
| B. Developer / maintainer (incl. future model sessions) | exact file paths, run names, patch numbers, the method, the reasons behind decisions | precise, with references (`area-combo-NN`, queue numbers, repo paths) |
| C. The owner | the install review, open decisions, the state in one page | short, decision-oriented |

## Conventions used in every document

- Status words: **proven** (seen on the tablet, run name given), **PC-checked** (built / tested on the PC only),
  **planned** (written down, not built), **untested**, **not possible on mainline** (reason given).
- Every hardware value carries its source: our files (repo path), a run (`area-combo-NN`), or stock (DT / firmware
  log / LineageOS logcat as recorded in our device-facts). Upstream facts cite the kernel tree path or the public
  specification by name.
- Device-unique values are never written: serial, Bluetooth / MAC addresses, SSIDs, partition GUIDs, the backup's
  hashes, user names in paths outside the project. Written as `xx` where a placeholder is needed.
- No proprietary content: no firmware, no ACDB / XML / TFA files, no camera register tables or traces, no bulk stock
  device tree tables. Vendor documentation is summarised in our own words, never quoted.
- Any command that writes the tablet's storage appears only inside a WARNING block, with the project's "only with
  the owner's OK / at your own risk" framing, and never inside a script.

## The document set

| File | Audience | Purpose |
|---|---|---|
| `INDEX.md` | all | where to find what (documents, repos, run logs, workflow folders) |
| `01-OVERVIEW.md` | A, C | what the project is, what works today (matrix numbers), what does not, the safety principles |
| `02-HARDWARE.md` | A, B | the SM8850 and the Pad 4 as Linux sees them: block by block with driver status, rails, thermal, RAM / UFS, partitions (generic), firmware sources, `efisp` |
| `03-BOOT-AND-PARTITIONS.md` | A, B | stock boot chain, A/B, AVB, our RAM boot, the planned install chain (U-Boot / EFI / shim / GRUB), why it stays unbrickable and restorable |
| `04-BUILD-YOUR-OWN.md` | A | step by step: prerequisites, trees, `prepare.sh` + `kernel.pin`, configs, build, firmware from your own tablet (read only), device package, a safe RAM boot, tests, logs |
| `05-PORTING-TO-OTHER-DISTROS.md` | A, B | Debian in detail (kernel package, firmware, initramfs-tools vs dracut, the device package mapped to Debian packaging, sensors, libcamera, WirePlumber), Arch / postmarketOS briefly, what is Fedora-specific |
| `06-PROCESS-HISTORY.md` | B, C | phases and campaigns with dates, the workflow / agent method, key findings and decisions, the lessons (hard-won rules), where the evidence lives |
| `07-INSTALL-REVIEW.md` | C, B | independent review of INSTALL-PLAN.md, INSTALL-GUIDE.md and `wf/install` tooling incl. the B run and R1: findings by severity, consistency, suggestions |
| `GLOSSARY.md` | all | terms (ABL, AVB, LUN, SoCCP, pmic_glink, CX collapse, kit, run, workflow ...) |

## Outlines

### 01-OVERVIEW
1. The project in one paragraph (device, SoC, kernel base, distro, RAM boot, planned install keeping Android restorable).
2. What works today: feature-matrix counts and the rows grouped by area (display, input, audio, power, sleep,
   connectivity, cameras, video / GPU, sensors, packaging, install); measured battery life.
3. What is not done / not possible on mainline (with the reason).
4. Safety principles: RAM boot only, the two-partition write surface of the plan, never flash without the owner's
   OK, charging safety first, privacy, "hold the tablet".
5. Where to go next (reading order).

### 02-HARDWARE
1. Identity (model, codename, SoC names kaanapali / canoe / SM8850P), what "proven" means here.
2. SoC blocks: CPU clusters and cpufreq / idle, Adreno 840, Hexagon ADSP / CDSP (NPU), SoCCP, Iris, CAMSS, DPU / DSI / DP,
   PCIe + ath12k, USB (dwc3, QMP combo PHY, eUSB2 PHY + repeater), UFS, RPMh / AOSS / AOP, PMICs, TSENS, interconnects,
   LLCC / BWMON, crypto (QCE), IMEM / SRAM, watchdog. Per block: driver, source (mainline / infiniti base / our queue
   patch numbers), status, run reference.
3. Board: panel + backlight, touch + pen, pen charger, pogo keyboard, speakers / codec / mics, cameras + focus +
   EEPROMs + flash, sensors via the ADSP sensor hub, battery / charger via pmic_glink, hall / lid, buttons, LEDs.
4. Power: PMIC list, the rails our docs prove (audit results), BCL, thermal design (zones, trips, cooling maps,
   skin policy), per-rail telemetry.
5. Memory and storage: RAM size / type, UFS device, LUNs, block size 4096.
6. Partitions: the layout by LUN in generic form, A/B pairs, which ones Linux reads (firmware) and which ones the
   plan writes; `efisp` explained.
7. Firmware: what the kernel loads, where it comes from on the owner's device, why it is never distributed.
8. Hardware inventory summary (wf/hwinv: 112 rows) and the "no mainline driver" list.

### 03-BOOT-AND-PARTITIONS
1. Stock chain PBL -> XBL -> (TZ, hyp, AOP ...) -> UEFI -> ABL -> boot / vendor_boot / init_boot / dtbo; A/B slots,
   retry counters, AVB and the unlocked "orange" state; EDL is not a recovery path.
2. Our RAM boot: an Android boot image (header v4) with our U-Boot or kernel + initramfs, `fastboot boot`, nothing
   written; the kit's shim, USB network, rootfs over HTTP, auto reboot back to Android.
3. The planned install: ABL -> U-Boot (in `boot_b`) -> EFI boot manager -> shim -> GRUB -> kernel-iceland + DT from
   the ESP -> initramfs with the loop-over-userdata module -> Fedora root; why `userdata` holds a whole GPT disk with
   4 KiB sectors; `efisp` vs the image's own ESP.
4. The rehearsal chain (rehearsal U-Boot without UFS, network disk over USB) and what it can and cannot prove.
5. Unbrickable / restorable / permanent (INSTALL-PLAN section 11): write surface, rescue levels L0-L5.

### 04-BUILD-YOUR-OWN
0. Read first: what you need (unlocked bootloader, backup, a Linux PC), what can go wrong, what is proven.
1. Prerequisites (packages, clang / lld, python, android tools, mkbootimg).
2. Get the trees (iceland-linux, iceland-mainline, iceland-u-boot) - private today; how access works.
3. `prepare.sh` + `kernel.pin`: what is verified (upstream commit, tree hashes after each series).
4. Configure + build (`scripts/build.sh`): config fragments, what `required.config` checks; outputs.
5. Firmware: the list, extraction from your own tablet (read-only adb / the on-device extractor), placement.
6. A RAM-boot image: the kit tools (`tools/linux-ram`), what `fastboot boot` does and does not do.
7. First boot, logs (USB network, kmsg streams), tests (how our test parts work), how to return to Android.
8. The device package and the sensor packages (build on Fedora).
9. What needs an unlocked bootloader and the risks; what we have not proven.

### 05-PORTING-TO-OTHER-DISTROS
1. What is distro-neutral (kernel queue + distro-neutral.config, firmware, UCM, udev rules, U-Boot) vs Fedora-specific.
2. Kernel packaging: our rpm (`kernel-install` + 90-iceland-dtb plug-in) vs a Debian `linux-image` (make bindeb-pkg,
   `/etc/kernel/postinst.d` hook for the DT on the ESP, flash-kernel not used).
3. Firmware placement and compression (FW_LOADER_COMPRESS XZ / ZSTD; Debian ships uncompressed or zstd).
4. Initramfs: dracut module (what it does) vs initramfs-tools hooks; the read-only storage rule from the first second.
5. The device package piece by piece -> Debian packages / files (udev, hwdb, UCM, systemd units, the battery guard,
   thermal daemon, logind drop-in, WirePlumber rule, DMA-heap rule, dnf rules that have no Debian analogue / apt pinning).
6. Sensors: hexagonrpc, libssc, iio-sensor-proxy (patched) - build and service units.
7. Cameras: libcamera with the GPU soft ISP, the EGL leak fix, the WirePlumber >= 0.5.18 need, the private sensor module.
8. Desktop choices (GNOME tested; Phosh / KDE untested), the boot chain (GRUB vs systemd-boot under U-Boot EFI).
9. Arch Linux ARM and postmarketOS-style notes (brief).

### 06-PROCESS-HISTORY
1. Timeline: phases (discovery / backup, U-Boot, first Linux, display, GPU / GNOME, critical items, areas,
   campaign 2, workflows round 1-5, install tooling) with dates and run ranges.
2. The method: RAM kits, run pipeline, workflows (agents prepare, main session tests), queueing with tree checks,
   matrix + WORKLOG + privacy-guarded commits.
3. Key findings and decisions (dated): freeze root cause, DMABUF_DEBUG, Wi-Fi SBS, audio TDM, camera bus level
   shifters, CMA heap, f_ncm flush, CX collapse path, Fedora choice, install design.
4. Lessons learned (the hard-won rules) and why each exists.
5. Evidence map: where logs, results, kernels, kits, workflow reports live.

### 07-INSTALL-REVIEW
1. Scope and sources read (plan, guide, wf/install REPORT / NEXT / tooling, runs 63-93, R1).
2. Findings by severity (blocking / high / medium / low), each with evidence and a concrete suggestion.
3. Consistency matrix: plan vs guide vs scripts (partition names, sizes, decisions, gate lists, file names).
4. Missing recovery instructions and unclear steps.
5. Suggested additions to the guide (text ready to paste).

## Sources (read for these documents)

Project folder `C:\Users\lucne\OnePlusPad4-Mainline`: HANDOVER.md, STATE.md, CLAUDE.md, WORKLOG.md (entries 1-44+),
docs/INSTALL-PLAN.md, docs/INSTALL-GUIDE.md, docs/WORKFLOW-BRIEF*.md, docs/memory/*.
iceland-linux: README, kernel.pin, scripts/prepare.sh + build.sh, configs/, patches/ (0001-infiniti 138,
0002-iceland 0001-0166), packaging/fedora, docs/PORT-LOG.md.
iceland-mainline: README / PROJECT.md, docs/FEATURES.md, docs/features/features-data.py, docs/KNOWLEDGE.md,
docs/reference/pad4-hardware-boot-partitions.md, docs/device-facts/, packaging/iceland-device, packaging/sensors,
tools/linux-ram, tools/dualboot, phase4/, firmware/manifest.tsv (names only), audio/ucm.
iceland-u-boot: README, patches, build scripts.
Workflow folders `~/mainline/build/wf/*/REPORT.md`, `NEXT.md` (install, hwinv, audit, deepsleep, gpuisp, camera, ...).
Build scripts: build-q2.sh, build-q56.sh, an/genwf.py, linux-ram kit pipeline, queue-*.sh.
Excluded by rule (read at most to learn, never copied): wf/*/priv, wf/*/work, wf/thermal, AUDIT-TABLE-full.md,
build/fwsuper, camdrv / camtrace, the owner's backup contents.

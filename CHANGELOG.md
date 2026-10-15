# Changelog

Work on mainline Linux for the OnePlus Pad 4 (`iceland`). Newest first. The repositories and references are listed in
[PROJECT.md](PROJECT.md). The entries from 29 Sep to 14 Oct 2026 are summaries; the detailed test logs and the working
records are not published.
Commit hashes cited in entries before 14 Oct may not exist any more: the history of the public repositories was
rewritten on 13 and 14 Oct to remove test material. Use the dates and the tags.

Repos: [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) ·
[iceland-linux](https://github.com/mzakamin-hub/iceland-linux) ·
[iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) (all public).

## 2026-10-14 - slot marking fixed in 0.28-8; U-Boot v4; matrix page v62

- Fedora 44 GNOME boots from `boot_b` on its own ([docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md)).
- The Fedora-side slot marking of `iceland-device` 0.28-7 did not run on the installed layout: its guard refused the
  loop-mounted root, so ABL's retry count for the slot went down at every power-on.
- `iceland-device` 0.28-8: the slot-mark guard accepts the installed layout and sets the boot LUN writable for one
  `qbootctl -m` call only; stock's screen-off thermal table; stock's input boost ceiling.
- U-Boot install build v4: a power-on boot menu on the keys (Fedora, or the boot loader's fastboot).
- Power diagnostic on the installed system: average 2.08 W with the screen on at 120 Hz, Wi-Fi power save on and one
  Electron app open.
- DisplayPort over USB-C: HPD and EDID work and GNOME enables a 4K output, but no picture. The power contract is 5 V x 2 A;
  a possible over-current cut-off of the monitor is unverified.
- Feature matrix page v62: 104 rows, 83 working, 13 partly, 5 to do, 3 out of scope.
- The public repositories were cleaned of test material with their history (13-14 Oct): test tools, rehearsal logs and
  the kit scripts are no longer in them. All six repositories of the project are public, the LineageOS device and vendor trees
  included (a full scan of the vendor tree found no unit-specific data).

## 2026-10-13 - final golden B149; the first install

- Kernel q89e (Linux v7.3-rc7 rebase, 11-12 Oct) plus the 13 Oct fixes = q89f and q89g: the panel's brightness limit
  through the kernel (the backlight driver's cooling device, one state per stock gear); the UFS scheduler change
  no longer fails on the busy tag set (Fedora's own rule sets bfq on the UFS disks); the rear lens held at stock's start
  position while the camera streams; the USB controller and the Wi-Fi root port no longer wake the tablet; the GPU
  frequency floor and the Wi-Fi address helper removed (no longer needed). The idle refresh is compiled in and off.
- `iceland-device` 0.28-5 (microphone chain: the echo canceller, then a +14 dB limiter at -1 dBFS; the decimators at
  stock's 84), 0.28-6 (brightness through the kernel; helpers removed), 0.28-7 (the speaker default waits for WirePlumber's
  default metadata and reads its write back).
- Golden B147 (06:02, q89e + 0.28-5 + firmware 11.A.38-3) passed rehearsal r156 with one known failure: the libcamera
  stop race (F54, 1 of 40 cycles). B148 (0.28-6, r157) showed two failures (the lens at 434, the
  configured default output cleared) and was not used as the image.
- Golden B149 (committed 15:45): kernel q89g, `iceland-device` 0.28-7, `iceland-firmware` 11.A.38-3, Fedora's libcamera
  0.7.1-2. Final rehearsal r158 with 0 failures in the regression set (no regression against r141).
- The install image was rebuilt from B149 and checked offline (128 PASS, 0 FAIL). Fedora 44 GNOME was installed with
  the two writes of the install guide (`userdata`, then the footered U-Boot v3 in `boot_b`) and started from `boot_b`
  on its own.
- The install is Fedora only (no dual boot); the way back is the stock 11.A.38 image.
- The public repositories: the testing documents and the rehearsals were removed from GitHub, history included; the
  rewrites of 13 and 14 Oct changed several commit hashes. Older hash references in this file may no longer resolve.

## 2026-10-12 - golden B145 accepted; speakers at +9 dB; firmware repository public

- The firmware repository `iceland-firmware` was created and made public: release 11.A.38-2 (278 generic files, sha256 per
  file, notices kept). Release 11.A.38-3 (12-13 Oct) adds the decoded stock thermal model that the thermal service reads.
- `iceland-device` 0.28-2 (the Bluetooth address helper v2: the address is set after a real power cycle of the controller;
  the Bluetooth fault of bluez 5.87 is gone), 0.28-3 (speaker make-up +9 dB; the speakers listed as
  protected; the sensors restart after a resume), 0.28-4 (minimal Fedora holds; `iceland-firmware-fetch` with sha256
  pins; the brightness cap taken out of the service until it could come back through the kernel).
- Kernel q89d9 (rc6): the Bluetooth firmware baud change no longer drops received bytes (no more "Frame reassembly
  failed" at each Bluetooth power-on).
- Golden B143 (12 Oct morning) and B145: the first clean final rehearsal (r139c, 36 rows, 0 failures) and the accepted
  rehearsal r141 (48 PASS, one failure that was a test expectation, fixed). The update and rollback paths were proven as
  rehearsal rows (r142, r146, r141u, r141ub).
- The stock skin-temperature policy (60 / 61 / 70 C) was proven in an emulation (r150b).
- libcamera 0.7.1-2 from Fedora was proven (r152): 40 of 40 camera start and stop cycles.
- The rc7 rebase started (q89e).

## 2026-10-11 - audio work; minimal holds; Bluetooth address helper

- The speaker chain was brought to stock's levels in the PipeWire protection filter (150 Hz high-pass, compressor,
  limiter), and the sound card's gain and default outputs were checked against stock (0.27r6; rehearsals r138a-c).
- Rehearsal r139 (golden B141) failed four rows: the Bluetooth race of the address helper (fixed in 0.28-2 by the v2
  helper) and test expectations. The SoundWire IRQ and hci_qca sleep candidates were tested and dropped.
- Minimal holds: Fedora updates GRUB, shim, libcamera and the firmware packages; the sensor programs and `alsa-ucm` stay
  held; `kernel-iceland*` and `iceland-*` are never offered by Fedora.
- The SuperTurtleDev items entered the kernel series (q89d).

## 2026-10-10 - rc6 rebase; tb323fu patches; U-Boot install build v3

- Kernel rc6 rebase (q89 -> q89b); the F55 microphone replay passes on it; golden B130 confirmed.
- The tb323fu patches were added as q89c-tb.
- The U-Boot install build was tested from `boot_b` (each test write undone the same day). Patches 0008-0010 were
  added: no self power-off or reset (an earlier build reset itself and used up the slot's tries); USB up without the
  boot loader; `fastboot reboot-bootloader` reaches the boot loader without a key press.
- The AVB footer of the install U-Boot was proven on the tablet's own pulled images.
- The device package went from 0.23 to 0.26 on this day.
- The upstream scan by hardware block was done.

## 2026-10-08 to 09 - loop 5 starts; microphone stall found

- The fresh-boot rehearsal r2m (golden B123) showed a microphone stall (3 of 10 fresh opens empty) and one timeout of the
  audio processor. The image was held; the fix was queued as q87 (queue 0190).
- Loop 5 started on 9 Oct with that item first.

## 2026-10-03 - the team round; release candidate 1

- The team round started at 03:00. The first consolidated kernel (q84, rc4 base) and then q85 with the golden B112 and the
  rehearsal r2i (46 PASS, 0 FAIL): release candidate 1.
- q86 switched the Wi-Fi firmware's 802.11d scan off by default, the fix for the connection drops after a reconnect.
- The install guide was revised for release candidate 1 (the first-boot setup step).

## 2026-10-01 to 02 - campaign 2: battery, cameras, sleep, the install's first B run

- 1 Oct: the NPU, the microphone, the Wi-Fi 5 GHz fixes (0066-0068), and the first camera frames from both sensors.
- 2 Oct: the battery estimate (0071-0072); libcamera on both cameras (0073); the sensor programs as RPM packages; the
  charging behaviour as stock (0078-0080); the camera focus motor (0087-0089); the pogo keyboard and the pen charger
  (0090-0097).
- 2 Oct: deep sleep measured at 98 % of a sleep in the cluster collapse; the install B run passed (run 93); the AVB footer
  of the install U-Boot was proven on the PC (21:00).
- 2-3 Oct night: the first full rehearsal boot to the GNOME desktop from RAM (R1d) and the R2 rehearsals.

## 2026-09-29 to 30 - suspend, display, video, freeze

- Suspend fixed (PCIe WAKE# polarity, queue 0040). The ADSP starts after the root hand-over. The audio root cause: the
  stock ADSP has no audio-interface module, so the speakers go through TDM.
- 144 Hz black screen fixed (0058); the pink UBWC glitch fixed (0060); CPU thermal trips and cooling maps at stock
  (0022-0023); dEQP and WebGL runs.
- The roughly 60-second freeze under fast USB traffic fixed in the kernel (0063, 30 Sep).
- Hardware video decode bit-exact against the reference vectors (30 Sep). The green picture traced to the DMA-buf debug
  option (config fix 92047dc).

## 2026-09-28 (afternoon/evening) — Phase 3 hardware, PC relay kits pc-001..011

All built and run unattended by the PC session (results kept in the PC session's records, not published).

| Kit | Result | iceland-linux |
|---|---|---|
| Test 7b | both images white: rails and bandwidth ruled out; INT2 GDSC off | fe964f7 |
| pc-001 | **white screen fixed**: the framebuffer holds the MDSS INT2 GDSC (dispcc genpd sync_state ignores `pd_ignore_unused`) | 05031dc (0022) |
| pc-002/003 | CPU passive trips + cooling maps, stock 105/112/114 °C, held at 105 °C under load | f0162e1, d7c9f52 (0023) |
| pc-004 | modules in the debug initramfs; ADC5 Gen4 config fix | cc85322 |
| pc-005..007 | **native display at 120 Hz** (KTZ8869 stock values, video-mode splash kept, both MDSS GDSCs, GPIO shared proxy) | f9bc5e2 (0024–0027) |
| pc-008 | touch firmware runs (stock container converted, SRAM download) | – |
| pc-009 | Wi-Fi up (`qdss.cfg` required; BDF/regdb from odm) | – |
| pc-010 | Bluetooth, Wi-Fi scan, SoCCP attach, ADSP boot | – |
| pc-011 | battery data (pmic-glink channel race fixed), GPU powers up, audio groundwork | e0b025a (0028) |

Mainline: Tab S6 evaluation (keep U-Boot), the Nura OnePlus 15 page mapped to the Pad 4, the knowledge base (not published) updated with
all PC results, and relays 002/003 (sync; one shared knowledge file).

## 2026-09-28 — Linux on the tablet (Phase 2)

### Display: keeping the ABL framebuffer alive
The framebuffer console shows kernel text, then the panel goes black or white. Each test removed one cause:

| Test | Symptom | Cause found | Fix |
|---|---|---|---|
| 2 | black after the text | unused regulators and the backlight turned off | `regulator_ignore_unused`; both KTZ8869 backlight nodes disabled in the debug DT (iceland-u-boot 35cb950, iceland-mainline 7a39818) |
| 3 | white, no USB | display pipeline released (the DT had no framebuffer with votes) | Pad 4 DT describes ABL's splash framebuffer: clocks, MDSS GDSC, MMCX vote, `cont_splash_mem` no-map (iceland-linux c17f732) |
| 5 | white | simpledrm voted MMCX **SVS**, but ABL runs the MDP at 650 MHz = **TURBO**; orphan DSI byte/pixel clocks | MMCX TURBO, DSI clocks dropped (iceland-linux 27326fe) |
| 6 | white at 20–30 s | at the deferred-probe timeout (~22 s) rpmhpd sync_state switches off rails nobody votes for: **MXC went off** (on kaanapali, MMCX has no MXC parent). The `qnm_mdp` interconnect vote is also 0. | MXC TURBO vote (iceland-linux 2728bb9, test 7). Stock data from the PC then showed dispcc needs **MX**, so test 7 was replaced by **test 7b**: A = MMCX+MX+MXC votes (fe964f7), B = A + sync_state disabled (debug patch). The MDP bandwidth vote comes next if needed. |

### Linux debug image and tablet script (RAM-boot kits; the tools are not published)
- The RAM-boot kit tool (not published) can now boot several Linux images in one session, going back to Android in between, with results in one folder per image. `package.sh` builds a kit from U-Boot diag L plus labelled images. Dry-run against the mock tablet: A and B both completed using only allowlisted commands.
- The PC relay is in use (request 001, Linux test 7b).
- 359c8f7: first Linux RAM boot through U-Boot fastboot:
  - header v2 image with the kernel, a debug DTB and a busybox initramfs;
  - USB NCM network (the tablet's USB network address; the PC gets the next address);
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
- Linux test 6 survey: run log, not published.

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
- 68d8b5b: plan v3 (not published):
  - built on the results verified on the tablet;
  - faster order of work: RAM-boot Linux through U-Boot, pmOS only until the hardware works, upstream as we go;
  - realistic distro scope: one kernel source and config packaged per distro; Tier 1 pmOS / Fedora / Arch ARM; Tier 2 Debian testing / Kali / latest Ubuntu; Debian stable and Ubuntu LTS not supported (Mesa too old for Adreno 840);
  - Mu-Silicium fallback dropped.

## 2026-09-27 — Device facts, firmware manifest
- 00afc4a, a718977: plan v2 and read-only capture tools for Android with DSU root (capture tools, not published).
- 0bafbbb, a4192c1, a6bd734: captures 1–3 in `docs/device-facts/`:
  - ABL memory map (20 segments, 11.5 GiB), 68 reserved regions;
  - display framebuffer, I2C/SPI map, remoteprocs, firmware locations;
  - live and stock DTs, iceland-O-IN fixups.
  - Capture scripts fixed along the way: devicetree path, endianness, Windows-safe names, tar transfer, adb lookup, serial and MAC redaction.
- 106d125: firmware manifest. 21 files, with the stock 11.A.38 source and sha256 for each. No blobs are committed.

## 2026-09-27 — Discovery and repositories
- Studied the reference projects listed in [PROJECT.md](PROJECT.md): map220v, infiniti-mainline, pmOS/Nura OnePlus 15, troikoss, aaronsb, Mu-Silicium, PrestarLin, Y700, SM8750. The notes are not published.
- Created the three private repos.
- b94d38b (iceland-linux): first patch queue, v7.2 + map220v `iceland-7.2` (40 commits). It was superseded by the 7.3-rc4 rebase.

## Next (as of 28 Sep 2026; done or superseded)
1. Run Linux test 7b (PC relay request 001): A = MX vote, B = A + sync_state disabled. If the panel still turns white, add the MDP interconnect vote.
2. Load modules in the debug initramfs (touch SPI, ADC, TFA9865…).
3. Add CPU passive thermal trips and cooling maps before any load.
4. Firmware extractor, run once by the user.
5. Phase 3 hardware bring-up, in the order of the plan.

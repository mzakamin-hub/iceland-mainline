# OnePlus Pad 4 ("iceland") mainline Linux - project state

Saved 2026-10-01 from the Claude Code session that owns the project (the PC session). Read this first, then the last
block of `docs/memory/iceland-resume-point.md`. Everything here is a copy; the live work is in WSL (`~/mainline`) and
in the two private GitHub repos below.

## Goal

Mainline Linux (7.3-rc4 + the Pad 4 patch queue) with Fedora 44 GNOME on the OnePlus Pad 4 (Snapdragon SM8850
"Kaanapali", board "iceland"), tested by RAM boot only. Installing on the tablet happens only with the user's
go-ahead (phase 4 target: Fedora with GNOME - never pmOS / Debian / Ubuntu again).

## Hard rules (the user's, verbatim or near-verbatim)

- "don't install anything, or flash any partition only ram boot" - never flash, unlock, wipe or switch slots.
- "make the test fully automated without needing my check, if an items needs myself to check deferr it for now".
  Runs about 10 minutes ("60 mins is too long make it only for 10 mins").
- Rule 13: every hardware value comes from Pad 4 stock sources (stock DT, firmware logs, LineageOS logcat).
- Private - never commit or upload: proprietary firmware and stock ACDB / XML / TFA files; the partition backup
  `C:\OnePlusPad4\backups\20260927-1933-unknown`; every carve in `build/fwsuper` (dtbo, stockdtb, x-vendor, x-odm,
  x-system_ext, x-my_product, x-persist, x-dsp, sensors-root, *.img, vendor_dlkm_a.img, x-vendor_dlkm); the camera
  trace, timeline and register tables (`build/camtrace`, `C:\OnePlusPad4\camtrace`, `build/camdrv/*-regs.h`);
  `fw25/qcom/kaanapali/iceland/vpu40_2v.mbn`; the test media (`build/vclips`, `vclips.tar`, webcam frames).
- Mask MAC / BD addresses, the tablet serial (`build/.serial`, `build/.bdaddr` hold the values) and SSIDs /
  connection names in anything committed. The commit scripts have guards for all of these.
- Never commit `~/.ssh/iceland`. Repos stay private; nothing is published or sent upstream without the user's OK.
- Commits: author `mzak <mzak.amin@gmail.com>`; trailers `Signed-off-by: mzak <mzak.amin@gmail.com>` and
  `Co-Authored-By: Claude <model> <noreply@anthropic.com>` (Fable 5.1 since 2026-10-01); `git pull --rebase` before
  every push; never rewrite pushed history.
- Never `wsl --shutdown`. "hold the tablet" = stop every tablet action at once.
- Webcam ("USB2.0 HD UVC WebCam" on the PC) only during kit runs; frames stay in the session scratchpad, are never
  committed and are deleted after the verdict is written (`docs/memory/iceland-webcam-rule.md`).
- Kill old runners / probes before a new run. Charging safety first.

## Where things live

| What | Where |
|---|---|
| Kernel tree, kits, logs, results, tablet scripts | WSL Ubuntu-24.04 `~/mainline/build` (`src/` = kernel git, `an/` = tablet + probe scripts, `results-*.md`, `area-*/` log sets, `bin<tag>/` kernels, `modfull-<tag>.tar.gz`) |
| Patch queue + kernel configs (private GitHub) | `~/mainline/gh/iceland-linux` (`patches/0001..0063`, `configs/`, `kernel.pin`, `scripts/`) - copy in `kernel/queue/` |
| Docs, feature matrix, relay results, kit tools, test log sets (private GitHub) | `~/mainline/gh/iceland-mainline` (`docs/features/features-data.py` + `build.py`, `docs/NEXT-ACTIONS.md`, `relay/results/`, `tools/linux-ram/`, `docs/tests/`) |
| U-Boot | `~/mainline/gh/iceland-u-boot` (a3c7ca5) |
| Matrix update scripts | `~/mainline/research/matrix-*.py` - copies in `scripts/research/` |
| Kit staging, adb, runner, kmsg streams | `C:\platform-tools` (`relay-run-kit-early.ps1`, `usb-proxy.py`, `rootfs-serve\`, `relay-side-<stamp>\stream-*.txt`) |
| Backups and camera trace (private) | `C:\OnePlusPad4` |
| LineageOS source tree (+ `out/`, test media sources) | `~/android/lineage` |
| Feature matrix page | https://claude.ai/artifact/GtN6zLRTeabVcyg3LirNBm (republish `scratchpad/feature-matrix.html`, copied from `docs/features/feature-matrix.html` after `build.py`) |
| Claude memory notes (originals) | `C:\Users\lucne\.claude\projects\<scratch-workspace>\memory\` - copies in `docs/memory/` (serial masked) |

## How a test run works (the kit pipeline)

1. `prep-area-X.sh` builds the kit with `make-kit26.sh` (`BIN_TAG` kernel, `USB_QOS`, `KIT_LABEL`, `KIT_DESC` -
   no single quote in the description).
2. The chain script (`scripts/pc-chains/area-X-chain.sh`, Git Bash) stops old runners, waits for Android over adb,
   builds and stages the kit to `C:\platform-tools`, verifies `SHA256SUMS`, starts `cam.ps1` (webcam, if used),
   starts `relay-run-kit-early.ps1 -Wait N` (RAM boot + live kmsg streams) and launches `an/area-X-probe.sh` in WSL.
3. The probe waits for ssh (`an/fedora-ssh.sh`, tablet at 172.16.42.1), asserts `uname -r` = `bin<tag>/kernel.release`,
   turns off GNOME's suspend / lock, copies the scripts, the module tree and the test clips, runs each part on the
   tablet with nohup, follows `/tmp/area/timeline.txt`, fetches `/tmp/area-X.tgz`, reboots the tablet to Android.
4. Watch with `run-watch.sh <probe log> <kit img>` (`KEXTRA` / `PEXTRA` add patterns). A repeating heartbeat line
   means the tablet froze.
5. PC servers that must run: `python -m http.server 8000 --bind 0.0.0.0 --directory C:\platform-tools\rootfs-serve`
   and `python C:\platform-tools\usb-proxy.py 0.0.0.0 3128` (they stopped with the old session - restart first).

Kernels: `build-q2.sh BRANCH TAG` -> `bin<TAG>` + `modstage<TAG>`; `mk-modfull.sh TAG` -> `modfull-TAG.tar.gz`.
Queueing a patch: `queue-00NN.sh` (fast-forward `iceland`, format-patch into iceland-linux, `kernel.pin`,
`scripts/prepare.sh` verify).

## Status update 2 Oct 2026 21:00 (read `HANDOVER.md` first; details in WORKLOG.md from entry 44 on)

- Feature matrix: 61 working / 12 in progress / 5 not started / 2 not planned (of 80); page v41. Docs repo
  iceland-mainline: commit u (`docs/guide/` = the documentation set: overview, hardware, boot and partitions,
  build-your-own, porting to Debian and others, process history, install review, glossary, index).
- Kernel queue: iceland-linux `f84d0d2` = 0001-0166: 0117-0124 NPU / CDSP cooling (QMI TMD), 0125-0138 quick wins
  (bwmon, camera EEPROMs, DP + DP audio, WSA off, ...), 0139-0161 23 upstream fixes, 0162 the f_ncm NTB flush retry
  (the USB link no longer collapses with traffic both ways), 0163-0166 the PMIC power telemetry (lazy start).
  Test kernel of the queue head: `build/binq77`.
- Proven today: CX collapse 95 % in a 90 s sleep with everything an installed boot loads (run 92); the charge-limit
  settings confirmed by the owner (run 95); the install rehearsal's B run builds the whole image on the tablet in
  about 4 minutes (runs 93 / 94, device package 0.18 with the camera and deep-sleep changes).
- Open: R1 (first rehearsal boot) after the U-Boot fix's verification; install round 6 (ADSP firmware timing on the
  installed initramfs, the AVB footer for write 2, the guide); hwfix (PCIe L2 timeout, device-tree gaps, bypass
  charging); the boot-log plan `docs/BOOT-LOG-PLAN.md`; owner tests and decisions (HANDOVER section 3).
- Owner decisions: Fedora-only install for now (a dual-boot plan is prepared, not executed); the write-2 probe
  comes first, after the AVB proof, and the owner runs it; ask the owner to connect the tablet before every test.

## Status update 2 Oct 2026 10:00 - HAND-OVER POINT (superseded by the block above)

- Feature matrix: 55 working / 9 in progress / 10 not started / 2 not planned (of 76); page v32. Docs repo
  iceland-mainline `81cca68` (+ a small follow-up).
- Kernel queue: iceland-linux `c52d6ee` = 0001-0089 (0074 charge limit; 0075 / 0076 low-battery limiting; 0077
  step-wise governor fix; 0078-0080 charging as stock; 0081 PMIC temp-alarm fix; 0082 / 0083 shell-temperature
  inputs and PMIC cooling maps; 0084-0086 the camera bus level shifters; 0087-0089 the focus motor). Test kernel of
  the queue head: `build/binq55`. iceland-device 0.16 in the repo; 0.17 in preparation (`build/wf/pkg017/`).
- Green on the queue head (run 45): charging (PC port), charge limit (80 / 85 %), low-battery limiting, GPU cooling
  (20 of 20), thermal kernel parts, no stuck CPU limits.
- Cameras: bus fix and focus motor queued; 30 fps in all modes with the reworked private driver; fixed-focus helper,
  picture quality and a browser pass (run 46); GNOME's Camera app still shows no preview (open, camera workflow).
- Round-4 workflows (not-started items): pen charging (driver idles correctly on a test kernel, two checks open),
  pogo keyboard (delivered, not built), deep-sleep proof (delivered, not run), wake sources, GNOME app set,
  stock-values audit, device package 0.17, install tooling (paused mid-work). `HANDOVER.md` section 3 has each
  one's next action; nothing is running.
- Guides: `docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md` (the two writes are locked until the RAM rehearsal
  tools exist and pass).
- The tablet is in Android (LineageOS, slot b) between runs; nothing has ever been written to it.

## Status (feature matrix: 43 working / 17 in progress / 13 not started / 2 not planned, of 75)

The user's order: 1 refresh rates OK, 2 pink glitches OK, 3 sensors OK, 4 GPU correctness OK, **5 hardware video OK
(finished 30 Sep)**, **6 NPU = next**. Parallel tracks: cameras, USB host / OTG / PD, USB accessories, DisplayPort
over USB-C (enumerates), Wi-Fi 5 GHz, microphone.

Results from the last two days (full text in `docs/results/` and `docs/repo-docs/`):

- **The ~60 s freeze** (`results-freeze.md`): fast PC-to-tablet USB traffic (>= ~15 MB/s) while the CPUs may power
  collapse hangs the SoC (hard reset, no log). Fixed in the kernel: queue **0063** `dwc3-qcom` holds a 2 us
  `cpu_latency_qos` request while active (stock `qcom,pm-qos-latency = <2>`); the kits can also hold `USB_QOS`.
  Four runs with the kit QoS off and only the kernel fix: no freeze.
- **Video, item 5** (`results-video-2.md`): Iris (VPU 4.0) with the stock `vpu40_2v` firmware, queue **0062**.
  Decoding is bit-exact against the AOSP VTS reference MD5s (H.264 High 240/240, HEVC 300/300, VP9 300/300,
  AV1 167/167); 4K H.264 450 fps and 4K VP9 308 fps with about a tenth of the CPU time; `playbin3` and GNOME's
  Showtime pick the hardware decoder by themselves (1080p H.264 at 3 % CPU vs 47 % in software). Firefox decodes
  in software (Fedora's FFmpeg lacks V4L2-M2M). 10-bit VP9 is not negotiated by GStreamer yet.
- **The green picture** (same file): every hardware-decoded frame was drawn solid green because
  `CONFIG_DMABUF_DEBUG` (default on with `DEBUG_KERNEL`) strips the pages from importers' sg tables and the Adreno
  driver builds its GPU page tables from them. Proven with a debug kernel (q37d, `kernel/session/`), fixed by
  `CONFIG_DMABUF_DEBUG=n` in `configs/distro-neutral.config` (iceland-linux 92047dc), verified on the webcam (q38).
- **Encoder streams**: Iris encodes H.264 / HEVC fine; GStreamer's V4L2 decoder rejects the colour description it
  writes (colorimetry `2:4:5:4` from VUI 6/1/6); relabelled `bt709` all frames decode. GStreamer issue, upstream
  only with the user's OK.
- **GPU correctness, item 4** (`results-graphics-3.md`): dEQP Vulkan 34,650 cases / 2 fail, GLES 34,950 / 53 fail
  (Mesa gaps for the Adreno 8xx), WebGL 196 pages / 3 failing; the kernel side is clean.
- **USB-C** (`results-usb-1.md`): DP alt mode enumerates without errors; accessory drivers load on demand (UAS
  missing); host mode deferred to the user (needs devices plugged in).
- **Wi-Fi 5 GHz** (`results-wifi-23.md`): the firmware offers hw modes 0 and 5 (prefers 5), ath12k forces DBS;
  regulatory load fails every time and `regulatory.db` is missing in the kit. Not concluded.

## Kernel state

- iceland-linux: queue 0001-0063 (`0062` Iris DT enable, `0063` dwc3-qcom CPU-latency QoS); config fix 92047dc
  (`CONFIG_DMABUF_DEBUG=n`). Rejected candidates kept as local branches only: rpmh-rsc clamp (q34), arch timer
  always-on (q35).
- `build/src` branches: `iceland` = 320c54661 (queue head, clean); `gpudbg` 8ba95f149 (debug prints, never queue);
  `usbqos`, `video` (merged into the queue); `rscfix`, `rscfix2`; `wififix` 0eff456e1 (unbuilt); `dp` (q31);
  `wifidbg2` (q30).
- Built kernels: `binq36` = queue 0063 (DMABUF_DEBUG still on); `binq37d` = debug; **`binq38` = queue 0063 with
  DMABUF_DEBUG off - use this one** (`out/.config` carries the setting; `build-q2.sh` keeps it through olddefconfig).
- iceland-mainline: 105fa26 ("relay 019 item 5 done"), log sets in `docs/tests/area-video-2..5`.
- Tablet: in LineageOS. No runner, probe or monitor active.

## Pending (in order)

1. Nothing left from item 5: the results commit (iceland-mainline 105fa26), the config fix (iceland-linux 92047dc)
   and the matrix page (version 22, 2026-10-01) are all in.
2. **Item 6, the NPU** (Hexagon on the CDSP): the kits disable the CDSP in the DTB (`linux-ram/build.sh` `dis`
   list drops `/soc@0/remoteproc@26300000`; use `ENABLE=`); the board DT names `qcom/kaanapali/iceland/cdsp.mbn` +
   `cdsp_dtb.mbn` (`kaanapali-oneplus-iceland.dts:1488`) but the stock images are split `.mdt` + `.bNN` like the
   ADSP ones (`fw17/B/late`, handled with `ADSP_MDT=1`) - do the same for the CDSP; FastRPC compute contexts 1..12
   on the CDSP; `fastrpc_shell_3` / `fastrpc_shell_unsigned_3` live in `fwsuper/x-dsp/cdsp` (private); then an
   unsigned-PD test program. Fix the `iceland-npu-off` unit path. Stock values per rule 13.
3. Video leftovers (low priority): 10-bit VP9 negotiation; Firefox hardware decoding (needs an FFmpeg with
   V4L2-M2M); the GStreamer colorimetry match; a camera / screen-recorder test of the encoder once cameras work.
4. Parallel: camera C3 first light (`build/camdrv` private, `dt-camera.py`, `CONFIG_VIDEO_DW9719=m`);
   `area-wifi-4` (`regulatory.db` in the kit, country, regulatory state per pass, boot-time A/B of hw modes);
   a host-mode USB kit when the user can plug accessories in; the dwc3 QoS idle-power cost with a data cable
   plugged in (busy-only vote like stock if it costs too much).
5. Older deferred-user items: auto-rotate turn, PD charger test, skin trip 48 vs 50 / 60 C, the 5 GHz password,
   the microphone comparison.
6. Phase 4 install - only with the user's go-ahead.

## Gotchas

- `KIT_DESC` must not contain a single quote. The Fedora rootfs has a stale `/lib/modules/...00175` tree: use the
  shim's root via `/proc/<pid>/root` (`/etc/modload.list`) or the full module tree + `depmod`.
- GStreamer lists the `v4l2*` elements only once `/dev/video*` exists: load `qcom_iris` before `gst-inspect`.
- The rpmh-rsc parameter lives under `/sys/module/qcom_rpmh/`, not `rpmh_rsc`.
- Freeze signature: heartbeat repeats in the watcher, USB gone 11-23 s later, LineageOS `bootloader_log` says
  PSHOLD / Hard Reset (needs `adb root`); pstore is wiped by the cold boot.
- A log tarball fetched by scp can be truncated when the session ends; fetch mid-run and verify with `tar -tzf`.
- Git from Windows on `//wsl.localhost` paths fails with "dubious ownership": run git inside WSL.
- `openh264dec` is not a reference for High-profile H.264 (106 / 240 vs the VTS MD5s); use the VTS vectors.
- `cut` buffers in a Monitor pipe: use `sed -u`. Python cannot open a `\\wsl.localhost` backslash path: `cd` there
  and use relative paths. `mkdir` on `//wsl.localhost` from Git Bash fails: do it inside WSL.
- The commit-script privacy guards had false positives (sed patterns inside scripts, `.sum` files): keep the SSID
  check scoped to `docs/tests`, keep `.sum` allowed.

## Folder map

- `STATE.md` - this file.
- `docs/results/` - `results-graphics-3.md`, `results-wifi-23.md`, `results-usb-1.md`, `results-video-1.md`,
  `results-video-2.md` (runs 1-5), `results-freeze.md`.
- `docs/repo-docs/` - `NEXT-ACTIONS.md`, `FEATURES.md`, `README.md`, `relay/results/*.md` from iceland-mainline.
- `docs/memory/` - the Claude memory notes (project rules, resume points, lessons), serial masked.
- `docs/feature-matrix.html` - the published matrix page.
- `scripts/pc-chains/` - chain scripts, `run-watch.sh`, `cam.ps1`, `glitch.ps1`.
- `scripts/tablet/` - `an/` tablet scripts and probes (video 1-5, freeze 1-7, display-1 helpers, wifi, usb),
  `nal.py`, `vtsvec.py`, `fedora-ssh.sh`.
- `scripts/kit/` - `make-kit26.sh`, `linux-ram/init`, `build.sh`, `cgi-*`, `relay-run-kit-early.ps1`.
- `scripts/build/` - `build-q2.sh`, `build-q33..q38*.sh`, `mk-modfull.sh`, `mk-vclips.sh`, `queue-00NN.sh`,
  the `prep-area-*.sh` kit builds.
- `scripts/commit/` - the commit scripts with their privacy guards, `save-project*.sh`.
- `scripts/research/` - the matrix update scripts.
- `kernel/queue/` - iceland-linux patches 0001-0063, `configs/`, `kernel.pin`, `scripts/`, `README.md`.
- `kernel/session/` - the DMABUF_DEBUG config fix (92047dc), the debug-print patch (q37d, never queue), git log heads.

# Work log - OnePlus Pad 4 mainline

Newest entry last. Every entry: what was done, the result, what comes next. Read `STATE.md` for the rules and
locations, this file for the running history, so no step is repeated. A copy goes to
`iceland-mainline/docs/WORKLOG.md` with each commit.

## Campaign 2 (started 2026-10-01): one combined step, run until green

The user's order (2026-10-01): combine the NPU, the video leftovers and the parallel tracks into one step, add the
microphone input meter (still not fixed), and test + debug until all of them are green; keep the feature matrix and
this log current.

| ID | Item | Green means | State |
|---|---|---|---|
| N | NPU (Hexagon CDSP) | CDSP boots from the tablet's own firmware and stays up; FastRPC on the CDSP; a user PD (unsigned) runs a real remote call; "CDSP off on battery" unit works | open |
| V1 | 10-bit VP9 hardware decode | GStreamer plays VP9 profile 2 through Iris, frames exact vs software | open |
| V2 | Hardware decode in a browser | a web video decoded by Iris (Firefox, or GNOME Web if Firefox cannot on Fedora's FFmpeg), cause documented | open |
| V3 | Hardware encoder round trip | Iris-encoded H.264 + HEVC decode on Iris and in software | open |
| C | Camera first light | chip IDs read, raw frames from the rear and the front sensor, a picture through libcamera | open |
| W | Wi-Fi 5 GHz | regulatory database + country set, 5 GHz networks found at boot every time (connecting needs the user's password) | open |
| U | USB fix idle power | cost of the always-on CPU-latency request measured with a data cable; busy-only vote like stock if it is costly, freeze test still clean | open |
| M | Microphone input meter | capture level matched to stock for the same sound, GNOME's input meter visibly moves (webcam + measured peaks) | open |

Known before starting (from `docs/repo-docs/`):
- N: the kits disable the CDSP node; the board DT names `cdsp.mbn`, stock ships split `.mdt` in the modem partition
  (backup has `modem_a.img`, `dsp_a.img`); `fastrpc_shell_3` and `fastrpc_shell_unsigned_3` are in the dsp partition;
  hexagonrpcd already serves the ADSP for the sensors (area-sensors-4..7).
- M: capture works; noise floor fixed by queue 0059 (-63 dBFS). Speech arrives at -29..-43 dBFS vs stock's
  -17..-35 dBFS (peaks -3), so GNOME's linear meter barely moves. Suspect: gain (analog ADC 14 = stock's recorder
  value, but the digital / DSP gain of stock's recorder path is not applied here).
- C: sensors SC1320CS (rear, 0x36) and SC820CS (front, 0x10) on i2c@884000, CSIPHY 4 / 5, driver + DT drafted and
  compile-tested (`build/camdrv`, private tables), CAMSS has Kaanapali resources in the tree.
- W: firmware offers hw modes 0 and 5, ath12k forces DBS; `regulatory.db` missing, country request rejected.
- V: Iris decode exact (H.264, HEVC, VP9 8-bit, AV1); 10-bit VP9 not negotiated; Firefox: "No appropriate v4l2
  codec found"; encoder streams rejected by GStreamer's caps check on colorimetry 2:4:5:4 (bt601 input).

## Log

### 2026-10-01 - entry 1: setup
- Saved the project (STATE.md, this log), committed the video results (iceland-mainline 105fa26), matrix page v22.
- PC servers restarted (rootfs :8000, proxy :3128). Tablet in LineageOS, adb present.
- Next: offline prep (CDSP firmware from the backup's modem image, PC audio output for the mic tone, hexagonrpc
  tooling from the sensor runs), then kit area-combo-1 on kernel q38: mic levels + meter, CDSP late start + FastRPC,
  video leftover diagnostics.

### 2026-10-01 - entry 2: offline prep + the stock microphone reference
- CDSP firmware found in the backup's modem image (`image/cdsp.mdt`, `.b00-.b16`, `cdsp_dtb.*`, `cdspr.jsn`); read with a
  new read-only FAT reader (`an/fatx.py`, verified: its `adsp.mdt` is identical to the kit's copy). Private:
  `build/fwcdsp`, `cdsp-fw.tar`, `cdsp-root.tar` (dsp partition's `cdsp` tree + the unsigned NPU runtime
  `libQnnHtpV81Skel.so` from odm).
- NPU test client: Qualcomm's open `fastrpc` library (github.com/qualcomm/fastrpc, cloned to `~/mainline/ext/fastrpc`)
  with its `fastrpc_test` (calculator / HAP / multithreading skels, v75) + `an/htp-open.c` (opens the NPU runtime in an
  unsigned PD: `file:///libQnnHtpV81Skel.so?qnn_skel_handle_invoke&_modver=1.0&_dom=cdsp`).
- Kit builder: `CDSP_MDT=1` (firmware-name = cdsp.mdt / cdsp_dtb.mdt), node enabled with `SOC_EXTRA`.
- Stock mic reference (LineageOS recorder, UI driven over adb; `scripts/mic/stock-rec.sh`):
  - PC volume was 6 %: nothing audible. The user allowed raising it for the tests (restored each time).
  - Steady sounds are a bad reference: stock's recorder path suppresses them (1 kHz tone -42 dBFS on one channel,
    gone on the other) = noise suppression in the DSP.
  - Speech reference (Windows voice, `scripts/mic/mic-speech-gen.py`, 21.55 s) at PC volume 0.60: stock speech rms
    -49.7 / -47.7 dBFS, loud frames (95th percentile of 50 ms) -42.9 / -41.0, peaks -29.7 / -28.0. The PC speaker is
    quiet at the tablet; the comparison is relative, same sound for both systems.
  - Stock mixer file: TX_DEC volumes 84 (0 dB) and mic paths in ADC_HIFI; the loudness difference is in the DSP.
  - Left on the tablet: 4 test recordings in Recordings/Sound records (05_26, 05_43, 05_45, 05_46 on 2026-10-01);
    copies in `C:\OnePlusPad4\mic` (private).
- `gnome-screenshot` cannot capture on GNOME 50 (shell interface refused) -> the webcam is used for the meter.
- Next: run area-combo-1 (kernel q38): mic take at TX_DEC 84, gain to match stock's loud frames, GNOME meter with the
  webcam; video leftovers (FFmpeg V4L2-M2M, 10-bit VP9, encoder with BT.709); idle sample; CDSP start; FastRPC tests.

### 2026-10-01 - entry 3: runs area-combo-1 (19:54, kernel q38) and area-combo-2 (20:15, kernel q39)

**N - NPU: working.** (run 1 + 2)
- CDSP boots from the tablet's own firmware (`cdsp.mdt` from the modem partition, copied into RAM, `echo start`):
  state running, `/dev/fastrpc-cdsp` + `-cdsp-secure`, no kernel errors. Kit knob `CDSP_MDT=1` + node enabled.
- `qualcomm/fastrpc` builds on the tablet in 27 s (saved: `build/frpc-built.tgz`); its `cdsprpcd` attaches and serves
  the DSP's file requests from the dsp partition tree.
- Run 1 failed with `0x8000054f`: the client looks for `fastrpc_shell_unsigned_3` only in `/usr/lib/dsp`,
  `/usr/lib/rfsa/adsp`, `/vendor/dsp` (not in `DSP_LIBRARY_PATH`). Run 2 with links there:
  `fastrpc_test -d 3 -U 1` (unsigned PD): calculator PASSED, multithreading PASS, HAP example passes except
  `HAP_mmap` with a DMA handle (0x4e).
- **The tablet's NPU runtime (`libQnnHtpV81Skel.so`, unsigned build from odm) opens and closes in an unsigned PD**
  (`an/htp-open.c`, rc 0). Running a neural network needs Qualcomm's QNN SDK for Linux (licence: the user's call).
- Left: the HAP DMA-handle call; "CDSP off on battery" unit path; packaging (firmware extractor: cdsp files,
  fastrpc RPM, DSP file tree at install like the sensors').

**M - microphone: cause found.** (run 1 + 2)
- The RAM test image (`rootfs-gnome.tar.gz`) carries an OLD UCM without `ADC1/ADC2 Volume 14`: analog gain 0 =
  21 dB too quiet -> GNOME's meter flat. Every RAM session since the image was made had this. The repo and the
  iceland-device package have the right file. Fix: the kits now unpack the repo's UCM over the rootfs at the
  hand-over (`init` + `make-kit26.sh`: rootfs-overlay.tar). Run 2: "overlay applied: 3 files", ADC1/2 = 14.
- Level vs stock for the same sound (marker tone, PC volume 0.60): stock -37.5 dBFS; mainline with the repo UCM
  -51.6 (TX_DEC 84) = 14 dB quieter; with TX_DEC 98 (+14 dB) -35.9. Speech loud frames: stock -42.9 / -41.0,
  mainline -53.5 at 84, -37.1 / -33.2 at 98. Stock adds the gain in its DSP; choice: TX_DEC 96 (+12 dB).
- GNOME Settings needs `XDG_CURRENT_DESKTOP=GNOME` when started from a script. The webcam cannot resolve the small
  level bar; the meter is judged from the same data it shows (40 ms peaks): at TX_DEC 98 the quiet PC sound gives
  4-8 % typical, up to 23 %; a voice at the tablet is ~25 dB louder than this test sound.
- Run 1's first takes were contaminated (room noise, someone at the tablet); the marker tone via a 1 kHz filter is
  the robust measure.

**W - Wi-Fi 5 GHz: regulatory database in, not solved.** (run 2)
- `regulatory.db` (+ .p7s, upstream wireless-regdb) now in the kit firmware tree: cfg80211 loads it. Country from
  the PC's time zone (Egypt -> EG) set with `iw reg set`.
- Boot-time scans: 5 GHz 0 / 0 / 0 BSS; after the country: 0 / 0 / 1; NetworkManager lists 1. ath12k still logs
  "Failed to set the requested Country regulatory setting" three times at load. So the regulatory database alone
  does not fix it; next: the hw-mode candidate (firmware's preferred DBS-or-SBS) at boot.

**V - video leftovers.** (run 1)
- Encoder round trip with BT.709 input: H.264 60/60 on Iris and in software, HEVC 60 on Iris (VUI 1/1/1). OK.
- 10-bit VP9 and the BT.601 encoder stream fail for one reason, read in GStreamer's source: the Iris decoder echoes
  the colorspace in TRY_FMT on the bitstream queue, so GStreamer builds a list of "supported" colorimetries for the
  coded format; streams with `bt2020-10` or `2:4:5:4` are not in it -> not-negotiated. Fix belongs in GStreamer
  (do not probe colorimetry for coded formats); plan: build the patched v4l2 plugin on the tablet and test.
- Firefox: Fedora's `ffmpeg-free` has V4L2-M2M decoders only for h263 / mpeg1 / mpeg2 / mpeg4 / vp8 / vp9 - no
  `h264_v4l2m2m` (distribution policy). Plan: GNOME Web (GStreamer) for a browser on the hardware decoder.

**U - USB fix idle cost.** (run 1) With a data cable and the kernel's 2 us request: CPUs 100 % in WFI, 0 entries
into cpu-sleep-0 / cpu-sleep-1 in 45 s. A/B against a kernel without the request still to do.

**C - camera: two blockers.** (run 2, kernel q39 = queue + camera DT v1)
- I2C bus `884000.i2c` times out (GPI -110) when the focus motor probes alone: its pull-ups hang on the sensors'
  1.8 V rail, which is off until a sensor powers up. First light without the focus motor driver.
- `qcom_camss` crashed in probe (NULL strcmp in `msm_csiphy_subdev_init_legacy`): this tree's Kaanapali CAMSS wants
  the sensors wired through separate CSI-2 PHY nodes (`csiphy4/5`, `qcom,kaanapali-csi2-phy`), not straight into the
  CAMSS ports. DT v2 written (`camdrv/dt-camera2.py`), PHY supplies from stock: csiphy4 0.9 V pmh0110_d_l3, csiphy5
  0.9 V pmh0110_i_l3, 1.2 V pmh0110_d_l1.
- The sensor module loaded but printed nothing (no bind): to diagnose with the sensor loaded first.

Next: kernel q40 = queue + wififix candidate + camera DT v2 (building). Run 3: Wi-Fi at boot with the candidate,
mic with TX_DEC 96 in the UCM, camera first light, GStreamer patch test, GNOME Web. Then the idle A/B.

### 2026-10-01 - entry 4: commit, run 3 results, run 4 crash and relaunch
- Committed iceland-mainline 29f7c21 (mic fix: UCM TX_DEC 96 + kit overlay, iceland-device 0.13; NPU results; logs of
  runs 1-3; matrix 46 working / 15 in progress / 12 not started / 2 not planned; page v23).
- Run 3 (20:33, q40 = queue + ath12k hw-mode candidate + camera DT v2):
  - Mic with TX_DEC 96 in the UCM: marker -40.3 (stock -37.5), speech loud frames -41.4 (stock -41.95). Capture keeps
    running with Settings > Sound open. Tablet speakers as the source: peaks -5.8 dBFS, meter 32 % typical, 51 % max.
  - Wi-Fi with the hw-mode candidate at first load: 5 GHz 0/0/0 at boot, 0/0/0 with the country -> the candidate is
    not the fix; the earlier good passes were after driver reloads.
  - Camera: CAMSS probes with DT v2 (44 entities, 2 PHYs). Sensors not bound: `pin_config_group_set op failed for
    group 12 / 13` (PMH0110 "G" = SPMI 6, GPIO 13 / 14, reset pins). Stock sets power-source 2, output-high,
    drive-strength 2 there (all 10 overlays). Mainline accepts source 2 only on pads with 3+ sources.
- Run 4 first attempt (20:48) **crashed the tablet in my own diagnostic**: the pad readout grepped every
  `/sys/kernel/debug/regmap/*/registers`; an MMIO regmap of an unclocked block gives a synchronous external abort
  (three Oopses in `regmap_mmio_read32le`), the session died, the watchdog rebooted to Android. **Rule: read only the
  SPMI PMIC's regmap, and only the needed lines (`dd bs=9 skip=<register>`); never loop over all regmaps.**
- Stock's USB latency vote read from the OnePlus SM8850 kernel source (`dwc3-msm-core.c`): sample the controller's
  interrupt count every 100 ms, vote 2 us at >= 200 interrupts per sample, then every 2 s keep it at >= 400.
  Candidate patch on top of 0063 does the same (branch `usbqos2`, kernel q41 built, 0 warnings).
- Run 4 relaunched 21:02 (same kernel q40): Wi-Fi first load vs two reloads, GStreamer patched plugin, GNOME Web,
  then the safe pad readout last.
- Next: run 5 = kernel q41, kit QoS off: idle residency + the freeze regression (4 fast downloads + bursts).

### 2026-10-01 - entry 5: runs 4b and 5, USB busy-only vote queued as 0064
- Run 4b (21:02, kernel q40) results:
  - GStreamer: the patched v4l2 plugin (no colorimetry probing for coded formats) built on the tablet; with it the
    BT.601 encoder stream decodes on Iris 60/60 frames identical to software, and 10-bit VP9 negotiates (P010).
    The saved `.patch` file is empty (0 bytes) - regenerate the diff from `~/mainline/ext/gst/gstv4l2object.c`.
  - Wi-Fi: first load vs two driver reloads: no 5 GHz result either way -> the reload is not the variable.
  - GNOME Web: `bwrap: No permissions to create a new namespace` - the kit ran Fedora in a plain chroot.
    Fix in the kit's init: `ROOTFS_MODE=pid1m` (mount --move the root file system over /, then chroot).
  - Pad readout (safe version): PMH0110 "G" GPIO 13 / 14 are LV_VIN2 pads (subtype 0x12, two sources), so stock's
    power-source 2 can never apply; the pads stay on source 0 as booted. DT v3 = v2 with source 0.
- Run 5 (21:15-21:22, kernel q42 = queue + usbqos2 + camera DT v3, kit QoS off, pid1m):
  - **USB busy-only vote passes**: idle with the cable in: cpu-sleep-0 74 %, cpu-sleep-1 25 %, WFI 1 % (was WFI
    100 %); 4 x 696 MB at 36.1 MB/s + 8 bursts with the request at 2 us during traffic and default between; 0 PMIC /
    stall lines, no freeze.
  - pid1m works ("user namespaces ok"); GNOME Web starts, but no process holds /dev/video* while it plays ->
    WebKit does not use the hardware decoder yet.
  - Camera: both sensors answer on I2C with DT v3 (`sc820cs found (chip id 0xd154)`, `sc1320cs found (chip id
    0xc658)`), CAMSS 46 entities. The sensors have 0 media links: the rear sensor's `lens-focus = <&vcm>` makes a
    sub-notifier that waits for the (unloaded) focus-motor driver, so CAMSS's notifier `.complete` never runs.
    My capture script also built a two-line entity name (both entities start with "sc1320cs"): use
    "sc1320cs 0-0036" (rear) and "sc1320cs 0-0010" (front).
  - Wi-Fi sub-band scans: 36-48 and 36-64 alone find the 2 BSS at 5180; any scan that mixes 5 GHz low band
    (<= 5320) with mid / high (>= 5500) finds 0 at 5 GHz; 2412 + 5180 finds both. LineageOS sees the same 2 BSS.
    -> the firmware loses 5 GHz results when one scan request spans its two 5 GHz sub-bands (SBS split).
  - 10-bit VP9 on Iris with the patched plugin: 72/72 frames, P010, but 0 checksums identical to libvpx; 27.7 % of
    the samples differ, max difference 1 (hw 0..701, sw 0..700) -> rounding somewhere, to find.
- **Queued**: iceland-linux 5369887 = patch 0064 "usb: dwc3: qcom: request the CPU wakeup latency only while USB
  is busy" (queue 0001-0064, kernel.pin updated, prepare.sh verified the tree f99042b3).
- Next (kernel q43 = queue 0064 + two candidates): ath12k splits a scan request at the firmware's sub-band border
  into two sequential scans; camera DT v4 without `lens-focus` (focus motor disabled) for first light. Run 6:
  full Wi-Fi scans at boot, raw frames from both sensors (media-ctl links by the exact entity names), 10-bit VP9
  difference analysis (which plane, which side rounds).

### 2026-10-01 - entry 6: run 6 (kernel q43 = queue 0064 + ath12k scan split candidate + camera DT v4)
- Built: `an/ath12k-scan-split.py` (branch `wifisplit`; module parameter `scan_split` 0 / 1 / MHz), `camdrv/dt-camera4.py`
  (no `lens-focus`, focus motor disabled), sensor entity named after the model; q43 0 warnings. Run 21:41-21:50.
- **10-bit VP9: exact.** With `videoconvert dither=none` Iris and libvpx give 72/72 identical frames, 0 differing
  samples in Y / U / V. The "max difference 1" of run 5 was my test: videoconvert dithers by default when it goes
  from P010 (16-bit container) to 10 bit. Nothing to fix in the decoder. V1 closed (needs only the GStreamer patch).
- **GNOME Web uses the Iris decoder** when the web process can see it: without WebKit's sandbox the web process
  creates `v4l2h264dec` and holds /dev/video0. With the sandbox nothing was decoded at all in my test (the clip was a
  file:// path the sandbox hides) -> next: serve the clip over http://127.0.0.1 and compare again.
- **Camera DT v4 works**: both sensors are linked (`sc1320cs 0-0036 -> msm_csiphy4`, `sc820cs 0-0010 ->
  msm_csiphy5`), sub-device nodes exist. No frames yet: my script looked for the link line 6 lines after the entity
  line, it is the 8th (format lines in between) -> skipped the capture. Fixed for run 7 (-A12). The TPG entities are
  not to be touched (no Kaanapali resources -> possible NULL dereference).
- **Wi-Fi 5 GHz, new picture.** Unsplit full scans: 0 BSS at 5 GHz while the station is NOT associated (4 of 4), 3 BSS
  once NetworkManager had connected on 2.4 GHz (2 of 2). MGMT trace of a failing scan: the firmware delivers 6 frames
  in the first second (2.4 GHz) and nothing after it - no host-side drop. Run 5's sub-band result (not associated):
  low-only fine, low + mid/high loses everything. The split ran only after the connect (3 of 3, proves nothing), and
  "auto" never split: the driver's `sbs_lower_band_end_freq` is 5 (not a frequency) - the firmware's capability
  TLV looks misparsed (the struct has no TLV header; 5 = hw mode id DBS_OR_SBS).
  Also seen: "Timeout while waiting for regulatory update" x3, "Failed to set the requested Country" x2; NetworkManager
  did not try to connect for the first 5 minutes after boot (first activation at 345 s).
- Next: kernel q44 = q43 + raw print of that TLV. Run 7: split A/B with the station held disconnected
  (`nmcli device set autoconnect no` + disconnect; off / 5330 alternating x4, traced pair, auto), camera frames,
  GNOME Web over http with / without sandbox.

### 2026-10-01 - entry 7: runs 7-9, Wi-Fi root cause direction, camera first light, USB vote reverted (0065)
- Run 7 (q44 = q43 + raw print of the firmware's DBS/SBS TLV), 21:56-22:07. Setup (dnf) took 490 s, the probe went on
  after 300 s -> camera and 10-bit parts ran without their tools (no result). Results that count:
  - **GNOME Web decodes H.264 on Iris inside its normal sandbox** (clip served over http://127.0.0.1): the web process
    creates `v4l2h264dec` and holds /dev/video0, with and without the sandbox. Browser item closed (Firefox stays
    impossible on Fedora's ffmpeg-free).
  - The firmware TLV: `len 16 words 0400000c 00000005 00000000 00000000` -> every array element carries its own TLV
    header; ath12k's `struct ath12k_wmi_dbs_or_sbs_cap_params` has none, so it reads hw_mode_id (5) as
    `sbs_lower_band_end_freq`. The firmware's real value is 0. Upstream bug, fix = add `tlv_header` (to verify).
  - The scan split: its second part fails to start while not associated (-110, 8 of 8) -> not the way.
- Run 8 (same kernel; setup wait 900 s), 22:09-22:18:
  - **Wi-Fi, firmware scan events while not associated**: `5180 5200` -> visits 5180, 5200, finds 2 BSS. `5180 5745`
    -> visits 5745 then 5180, finds nothing. Full scan: 5 GHz mid/high interleaved with 2.4 GHz (two MACs), and the
    low 5 GHz channels come on the 2.4 GHz MAC after its own channels - and hear nothing. 2.4 + low only: low 5 GHz on
    the main MAC, works. So: when a request has both 5 GHz sub-bands the firmware scans them on the two MACs at once
    (SBS) and the second MAC is deaf in 5 GHz low on this board.
  - **Stock: `enable_sbs=0`** in the tablet's WCNSS_qcom_cfg.ini (odm), comment "hardware ... not support sbs mode".
    The stock host sends the dual-MAC configuration (WMI_PDEV_SET_MAC_CONFIG_CMDID: the firmware's default bits, the
    ASYNC_SBS bit only if SBS is enabled - qcacld policy_mgr_init_dbs_config / policy_mgr_init_sbs_fw_config).
    ath12k never sends it. Reference sources fetched to `~/mainline/ref/fwapi/` (public Qualcomm code, read only).
  - **Camera first light**: both sensors stream 5 frames through CSIPHY -> CSID -> VFE RDI (rear 4160x3120, front
    3264x2448, packed RAW10, stream rc 0). The front preview shows the room (curtains, ceiling edge), dark at the
    default exposure / gain; the rear looks at the desk. Previews in `C:\OnePlusPad4\camshots` (private).
- Kernel q45 = queue 0064 + `an/ath12k-mac-config.py` (module parameter `sbs` -1 / 0 / 1, sent before the next scan)
  + camera DT v4. Run 9 first attempt 22:35: **the tablet froze during dnf at ~101-123 s uptime** (heartbeat gaps,
  then silence, hard reset 30 s later, "Reset by PSHOLD") - the 30 Sep freeze signature, with the busy-only USB vote
  (0064) and the kit's own request off. 4 sessions passed before it. Decision: **0064 reverted as queue patch 0065**
  (iceland-linux dd7ca1c, tree = tree after 0063); kits hold the request again (USB_QOS=2) until kernels are rebuilt
  on 0065. Run 9 relaunched 23:01 with the kit request on.
- The user asked (22:40) for parallel workflows on: auto-rotate, battery time estimate, s2idle, long sleep, CPU
  scaling + GNOME power modes, GNOME About page. Five background workflows started (analysis + test + fix candidates
  as files in `~/mainline/build/wf/<name>/`, brief in `docs/WORKFLOW-BRIEF.md`); they do not touch the tablet, the
  kernel tree or the kit builds. Their tests go into one combined run when they report.

### 2026-10-01 - entry 8: Wi-Fi 5 GHz fixed and queued (0066-0068), camera exposure, the five workflows reported
- Run 9 (q45, kit request on), second attempt 23:01: dnf hung 9 min on a stalled mirror connection -> killed, setup
  rerun through a resume probe; the runner's 900 s limit then ended the session before the log set was fetched (the
  results are in the live kernel stream, saved as `area-combo-9/timeline.txt`).
  **A/B/A, not associated, one boot**: firmware default: full scan no 5 GHz, `5180 5745` nothing; `sbs=0` (fw mode
  b8000000 = default bc000000 without bit 26 ASYNC_SBS): 5180 x2 in every full scan and in `5180 5745` (3 of 3);
  `sbs=1`: lost again (2 of 2); `sbs=0`: found again (2 of 2). Channel order without SBS: the whole 5 GHz band on
  the first MAC, 2.4 GHz interleaved on the second.
- Final form (`an/ath12k-no-sbs.py`): DT property `qcom,no-sbs` on the wifi node, ath12k sends
  WMI_PDEV_SET_MAC_CONFIG (default bits without ASYNC_SBS) in `ath12k_mac_start()`. Kernel q46 = queue 0065 + these 3
  commits + candidates (socinfo 661, cpuinfo model name, camera DT v4). **Run 10 (23:28)**: NetworkManager sees 2 BSS
  at 5 GHz at boot; 4 of 4 full scans and 5 of 5 `5180 5745` scans find them while not associated.
  **Queued: iceland-linux efd75d0 = 0066-0068** (queue 0001-0068, prepare.sh verified tree d414aade).
  Open (separate): NetworkManager did not connect by itself within 60 s of `autoconnect yes` (in run 6 it connected
  after ~5 min and waited 22 s for secrets); ath12k misparses the DBS/SBS capability TLV (upstream bug, not queued).
- dnf now runs with its own limits (`--setopt=timeout=20 --setopt=minrate=30000`, 240 s per try, 3 tries): setup 11 s.
- Camera (run 10): both sensors stream again; exposure max (3999 / 2999 lines) changes nothing in the picture, the
  raw gain values 0x1f / 0x3f raise the rear sensor's noise (std 1.4 -> 4.8) but not the front's -> the exposure
  write does not take effect (or the room is simply dark at 23:30). To do in daylight / with a lit target:
  exposure + gain registers, then libcamera. Previews private in `C:\OnePlusPad4\camshots` (run 10's are named
  combo9-*: fetched by the stale probe, see next line).
- **My mistake**: the run-9 resume probe (`an/area-combo-9-resume.sh`) was still looping when run 10 booted; it
  attached to run 10's session, fetched its logs into `area-combo-9/` and rebooted the tablet at 23:33:37, before
  run 10's About part. Logs moved (`fix-logs-9-10.sh`); the chains now also stop `*-resume.sh` probes. Not a crash.
- The five workflows reported (deliverables in `~/mainline/build/wf/<name>/`: REPORT.md, NEXT.md, tablet.sh, cand/):
  - about: model row = `/etc/machine-info` (OnePlus / Pad 4 / tablet); Processor row needs a `model name` line in
    arm64 /proc/cpuinfo (GNOME reads only that; local kernel carry = the user's call); SoC id 661 = SM8850P missing
    in socinfo (upstreamable).
  - battery: UPower divides charge by an instantaneous current and trusts a status that is always "Charging";
    candidate `battmgr-estimate.py` (CHARGE_NOW = SoC x full capacity, CURRENT_NOW = 1-minute mean, STATUS from it)
    + optional design voltages; DEBUG probe of the firmware's charge counter. The +-20 mA band and "Full at 100 %"
    are our choices, not stock values.
  - sleep: the "unexplained reboot after a long sleep" was the kit's own auto-reboot timer (uptime counts time
    asleep); the watchdog does not bite in s2idle; the two "stalls after audio" were not audio (no stream reached
    the hardware) and ran on kernels before 0063; no s2idle cycle has ever run on a kernel with the USB request.
    Test = 20 cycles + one 240 s sleep. Lid wake is already in the DT (needs a hand test).
  - cpupower: the DT candidates are already queued (0054 / 0055); GNOME's modes were never really switched in a
    test (polkit "Unauthorized" from a `su` session); Balanced uses the floors of the wrong SoC revision; the big
    cores' turbo steps (4.5 / 4.6 GHz, stock's maximum) are off in mainline until the boost switch is on;
    `iceland-npu-off.service` points at a path that is not installed. Candidates = iceland-device 0.14 profiles.
  - rotate: the mount matrix is right as far as data without a turn can show (Y sign inferred); run 7 did NOT show
    GNOME receiving the orientation (the "normal" came from the test's own monitor-sensor); iio-sensor-proxy takes
    its bus name before it finds the SSC sensors -> mutter can miss it; two candidate patches + packaging files;
    the test injects the four orientations through a uinput accelerometer and reads mutter's transform.
- Kernel q47 = queue 0068 + candidates (battery estimate, design voltages, DEBUG probe, socinfo, cpuinfo name,
  camera DT v4), 0 warnings. Run 11 (23:43): cpupower, about, battery. Run 12 next: sleep, rotate.

### 2026-10-02 - entry 9: runs 11-12, queue 0069-0070, iceland-device 0.14, commit B; the tablet went silent in run 12
- Run 11 (q47, 23:43-23:55), the workflows' tests:
  - cpupower: 25 PASS / 1 FAIL / 4 WARN. GNOME's three modes switch as the GNOME user (polkit OK from the user's
    systemd manager) to the iceland profiles; limits per mode as designed; 1-thread load 3.56 / 3.14 / 3.10 s (power
    saver / balanced / performance); capacities 799 / 1024; EAS runs; schedutil rate limit 45 us; refresh unit logic
    60 / 120 Hz OK; npu-off path OK. The FAIL is the "restore" check reading thermally capped limits (skin loop
    active after the 8-thread loads), not the profiles. Turbo steps (4512000 / 4608000) not reached while the cooling
    was active -> open (run 13 tests them first, cool).
  - about: all PASS. hostnamed OnePlus / Pad 4 / tablet with the machine-info candidate; soc0 machine SM8850P;
    8 model name lines; the real Settings page read through AT-SPI: "OnePlus Pad 4", "Qualcomm Oryon x 8",
    Memory 11.1 GiB.
  - battery: C3-C6 PASS (status follows the current's sign in 76 of 76 samples; load step -550 -> -1096 -> -509 mA;
    UPower time spread 11 % and 1 %), C1 / C2 FAIL: CHARGE_NOW missing or 17000 in many samples - the gauge's
    "remaining" word reads 0 / 17 / garbage (gauge words: 300 552 4364 9204 0 5 13786 0 100 ...). The probe:
    BATT_CHG_COUNTER (property 14) = 12688634 = state of charge x full capacity exactly; stock's property 69 answers
    too (12054202). Candidate changed: always state of charge x full capacity. Kernel q48 built for the re-test.
- **Queued: iceland-linux 54a64c8 = 0069 (socinfo SM8850P) + 0070 (arm64 cpuinfo model name, local carry)**; queue
  0001-0070. **iceland-device 0.14** (`pkg-014.sh`): machine-info, tuned profiles (revision 2.0 floors, turbo steps
  in Performance), npu-off unit path, tests (0 failures); the kits' overlay carries machine-info.
- **Commit B: iceland-mainline 06f9f8e** (logs of runs 4-11, tools, workflows' reports under
  `relay/results/pc-016-020/wf/`, matrix 48 working / 13 in progress / 12 not started / 2 not planned, page v24).
- Run 12 (q47, 23:57): the sleep workflow's test. **13 of 13 s2idle cycles clean** (6 s RTC alarm each, wake irq
  pm8xxx_rtc_alarm, no stuck CPU), including one right after a tone (C06) and one during a tone (C10). Cycle 14 is
  the one with a microphone recording before it: it never started. From uptime 227 s one CPU was busy and available
  memory fell by ~30-40 MB/s (6.8 GB -> 1.3 GB at 398 s); at 00:04:47 the USB device disappeared and the tablet has
  not come back in any mode (no Android, no fastboot, no USB device). No log set (RAM). The PC-side stream extract is
  `area-combo-12/timeline.txt`. Unknown: what ate the memory (pw-record / PipeWire / the kernel's capture path after
  13 suspend cycles) and whether the tablet is asleep without an alarm or hung.
  **The tablet needs the user's power key** (a press; if nothing happens, hold it about 10 s to restart into
  Android). Nothing was written to it.
- Prepared and waiting for the tablet: run 13 (kernel q48: turbo steps cool, battery re-test, Wi-Fi link band;
  `gen-combo-13.py`), then the rotate test, then the sleep test again with the microphone step isolated and memory
  watched (first find the memory eater: run the recording step alone, without suspends, with `ps` / slabinfo samples).

### 2026-10-02 - entry 10: runs 13-15: battery queued (0071-0072), sleep proven, auto-rotate by injection, turbo not granted
- 00:27 the user pressed the power key: the RAM session of run 12 resumed (ping, ssh port) and the kit's planned
  reboot (uptime 1800 s) took it to Android before the sleep logs could be copied. So in run 12 the tablet was
  asleep from 00:04:47 without a wake alarm (who suspended it is unknown; touch interrupts rose from 13 to 1214 in
  the last 30 s before) and a 22-minute sleep woke by the power key.
- Run 13 (q48 = queue 0070 + battery v2 + design voltages + camera DT v4), 00:30-00:40:
  - turbo: boost 1 -> policy6 max 4608000, 5 s busy loop on cpu7: schedutil stayed at <= 4396800 (cooling 0).
  - **battery v2: C1 C2 C3 C5 C6 PASS** (CHARGE_NOW 76 of 76 samples within 1 %; status vs sign 0 off; load step
    -510 / -1499 / -493 mA; UPower 23:50-24:50 h in idle2). C4 FAIL only in idle1: the session was still settling
    (current moved 56 %). Judged proven -> **queued: iceland-linux 1b8aaf3 = 0071-0072**, queue 0001-0072.
  - Wi-Fi link: not connected, and the image has NO saved Wi-Fi profile (run 15: one ethernet + loopback profile
    only) -> the connect in run 6 was made by hand. A 5 GHz connect needs the user's password.
  - The battery drains on the PC port during sessions: 92 % at 23:50 -> 86 % at 00:40.
- Run 14 (q48), 00:41-00:50:
  - turbo2 (governor performance): boost 1 requests 4608000 and time_in_state counts 1.03 s there, but the fixed
    load takes 0.713 s vs 0.705 s at 4396800 -> the firmware does not grant the turbo steps.
  - **rotate (workflow test)**: injection through a uinput accelerometer with the real mount matrix: names 5/5,
    mutter transforms 0/1/2/3/0 5/5, picture back to normal; real sensor (0 -7 -6) 'normal'. FAIL (first): udev
    started hexagonrpcd, but iio-sensor-proxy only came up on a manual start (60 s) - it looks for the sensors once
    and exits; `iceland-ssc-wait` returned at once because QMI service 400 is on QRTR before hexagonrpcd serves the
    registry. GNOME's claim per variant: v2 F, v2 F, cur W, v3 W(?), v2 W(?) -> the instrumentation for v2 / v3 is
    not trustworthy; the current tree works after a restart. Next for rotate: a retry policy in the unit
    (Restart=always, RestartSec=5) or a real readiness wait; then RPMs of the three programs.
  - **micdiag**: the step before cycle 14 of the sleep workflow test (4 s pw-record while a 3 s tone plays) is clean
    fresh, after 3 and after 13 more s2idle cycles (recordings 530-800 kB, memory flat, 13 / 0 suspend_stats).
    The run-12 runaway is not this step; cause not found (not reproduced).
- Run 15 (q49 = queue 0072 + camera DT v4), 00:54-01:04, plain sleep test `sleep2`: **10 of 10 cycles + one
  242.87 s sleep**, all woken by irq 23 pm8xxx_rtc_alarm, suspend_stats 11 / 0, tones 5 of 5, recordings 2 of 3
  (53 kB after C5), lowest available memory 6832 MB, one `dpu_crtc_disable: frame done wait timed out` entering the
  long sleep. Verdict line says FAIL only for the one short recording.
  Totals on kernels with the USB request: 37 cycles in 3 sessions, 0 failed.
- A lesson for test scripts: a bare `wait` in a function also waits for a background sampler loop -> always
  `wait $pid`.
- Matrix (matrix-c2c.py): Battery time estimate -> ok; Suspend (s2idle) -> ok; Long sleep -> ok; Auto-rotate part
  (new evidence); CPU modes note (turbo not granted); Wi-Fi note (connect needs the password).

### 2026-10-02 - entry 11: runs 16-19: device package RPM, auto-rotate start and the boot-order bug (mutter)
- Run 16 (q49): pkg FAIL at `alsatplg: command not found` (Fedora: package alsa-topology-utils; spec BuildRequires
  fixed). rotate with `Restart=always`: the daemon stayed up with ONLY the compass (accelerometer not there yet) ->
  a retry policy is not enough.
- Run 17 (q49): **pkg PASS**: iceland-device-0.14-1.fc44.noarch.rpm built on the tablet, 41 files, install rc 0,
  `rpm -V` clean; RPM + SRPM in `C:\platform-tools\rpms`. **rotate PASS** with a real readiness wait
  (`iceland-ssc-wait 30 /usr/bin/ssccli`: polls an accelerometer sample): bring-up 2.53 s by udev alone, first
  contact W, injection 5/5. Its gdm step: the NEW gnome-shell made 0 ClaimAccelerometer calls in 12 s.
- Run 18 (q49): `rotate3` = boot order as a functional test (test accelerometer + daemon up, then `systemctl
  restart gdm` = new autologin session, then four orientations): 0 claims in 30 s, turns 1 of 4.
- mutter 50.5 source read (`~/mainline/ref/mutter/`, reference only): `sync_accelerometer_claimed()` claims only
  when `inhibited_count == 0`; `update_panel_orientation_managed()` (monitor manager) calls uninhibit when the panel
  becomes managed (touch mode + accelerometer + built-in panel) - on the very first has-accelerometer notification
  nothing had inhibited yet, so the count goes to -1 and no claim is ever made. Works by accident when
  HasAccelerometer is false at proxy-ready (daemon started under a running session: blind claim first).
- Run 19 (q49): A/B in one session: current daemon 1 of 4 turns, 0 claims; daemon with
  `wf/rotate/cand/iio-accel-after-claim.py` (HasAccelerometer only for claimers + told at the claim): **4 of 4
  turns**, 1 claim, 60 readings. In this run the REAL sensors never appeared (stack started 246 s after boot; in
  the good runs at ~120 s): the sensor hub seems to stop asking for its files after a while -> hexagonrpcd has to
  start early (it will when packaged; for tests: start it right after the hand-over).
- Next for auto-rotate: RPMs (hexagonrpc + local patch, libssc, iio-sensor-proxy + 3fc1142 + accel-after-claim),
  iceland-device: udev rule + drop-ins + iceland-ssc-wait; report the mutter bug (user's OK); the user's turn.

### 2026-10-02 - entry 12: run 20: the rear camera's exposure and gain work (torch as the light)
- Correction to entry 8 / the matrix: "exposure does not act" was wrong. The driver's default exposure IS the
  longest one (3999 / 2999 lines), so "exposure max" changed nothing, and the room was dark at night.
- Run 20 (q49, 01:47): the flash LEDs as a torch (`/sys/class/leds/white:flash-1`, `yellow:flash-0`, brightness
  1/6 of 255). Rear SC1320CS, mean of the 8 MSBs (black level 16): dark G 17; lit at exposure 3999: G 187 (max
  255); 999: G 110 (parts saturated); 249: G 40 -> 249 vs 999 = 24 : 94 above black = 1 : 3.9: **exposure is
  linear**. At 249: analogue gain 0x1f: G 65 (x2.0), 0x3f: G 110 (x3.9), **0x7f: black picture (not a valid
  code)**, digital gain 0xff: G 64 (x2.0). So 0x3e09 = 0x0f / 0x1f / 0x3f is 1x / 2x / 4x and 0x3e07 0x80..0xff
  is 1x..2x. The preview shows the fabric behind the tablet in focus-less but clear detail.
  Front SC820CS (no light): exposure / 4 lowers the picture's maximum (35 -> 22), digital gain 0xff raises it
  (54); analogue gain 0x3f / 0x7f change nothing -> its gain register coding is still unknown.
- Next: libcamera (run 21: `cam -l`, a capture per camera, a JPEG through `libcamerasrc`).

### 2026-10-02 - entry 13: runs 21-22: libcamera works on both cameras; queue 0073 (camera DT)
- Run 21 (q49): Fedora's libcamera 0.7.1: `cam -l` = "Internal back camera" (camera@36), "Internal front camera"
  (camera@10); capture 10 of 10 frames each, 1280x960 ABGR8888 from 4160x3120 BGGR10 through the software ISP,
  23.98 fps. Warnings only: no sensor helper / properties / tuning file for sc1320cs and sc820cs. My `libcamerasrc`
  line used `num-buffers`, which that element does not have.
- Run 22 (q49): processed previews (`an/abgr2png.py`): rear under the torch = a clear picture of the fabric behind
  the tablet, mean R 173 G 167 B 168, overexposed in the middle (no auto-exposure without a sensor helper); front
  mean 40 (dark room). `libcamerasrc ! identity eos-after=13 ! jpegenc` gives JPEGs. WirePlumber: two
  `Video/Source` nodes (`libcamera_input...camera_36` and `...camera_10`, "Built-in Front Camera").
  Previews private in `C:\OnePlusPad4\camshots\run20` / `run22`.
- **Queued: iceland-linux 82e192d = 0073** the cameras' device tree (= the tree tested as q49). Queue 0001-0073.
- Camera open points: libcamera sensor helper + tuning (AE), front gain coding, focus motor, GNOME Snapshot on
  screen (webcam / user), shipping the private sensor module.

### 2026-10-02 - entry 14: run 23: the sensor programs as RPMs, auto-rotate with the packaged stack, camera gain codes
- New in the repo (not committed yet at this point): `packaging/sensors/` = `hexagonrpc.spec` (upstream 598b591 +
  our patch, units moved to the unit directory, user `fastrpc`, udev rule for the nodes), `libssc.spec` (54dd13e,
  `-devel` split, `ssccli` in the main package), `iio-sensor-proxy.spec` (3.9 with `-Dssc-support=enabled` + two
  patches, release `10.iceland1` above Fedora's 3.8-2), `build-rpm.sh`, README. `build/mk-sensor-pkg.sh` makes the
  source tarballs from the pinned upstream commits and `sensors-pkg.tgz`. Fedora 44 has no hexagonrpc and no libssc
  (checked on mdapi), and its iio-sensor-proxy is 3.8 without SSC.
- iceland-device 0.15 (`build/pkg-015.py`): `81-iceland-ssc.rules`, the two unit drop-ins, `iceland-ssc-wait`,
  `iceland-ssc-resume.service` (hexagonrpcd again after a suspend), Requires on the three packages.
- Run 23 (q49, 05:00-05:05, the whole run took 5 minutes):
  - **pkg2 PASS**: build deps 30 s; the three sensor RPMs built in 9.7 s, the device RPM in 8.6 s, all on the
    first try, no unpackaged-file warnings; `rpm -Uvh` rc 0 with dependencies checked (iio-sensor-proxy 3.8-2 ->
    3.9-10.iceland1), `rpm -V` clean, user `fastrpc` created, the daemon links libssc; the device package's only
    unresolved requires are `kernel-iceland` and `grubby` (not in a RAM session); with the RPMs in the local
    repository `dnf check-upgrade iio-sensor-proxy` offers nothing. RPMs + SRPMs: `C:\platform-tools\rpms\sensors`.
  - **rotpkg start PASS**: the packaged units alone (`modprobe fastrpc` = node added after the rules, as at boot,
    at uptime 131 s; ADSP up at 48.6 s): accelerometer sample after 2.7 s, the daemon found accelerometer, light,
    compass and proximity; GNOME (session already up): 1 claim, 'normal', managed=true.
  - **rotpkg real PASS** (the boot order with the REAL sensor: new GNOME session after the daemon): 1 claim, 504
    readings in 20 s, 'normal', transform 0, vector (0, -7, -6).
  - **rotpkg inject PASS**: packaged daemon + test accelerometer + new session: 4 of 4 turns.
  - **FAIL found**: after the daemon was restarted under that session (the test's clean-up): 0 claims, orientation
    'undefined', managed=false. Cause read from mutter's source: a mutter that has been through its first claim
    sits at inhibit count 1 when the daemon vanishes and waits for HasAccelerometer = true before it claims; patch
    v4 hid it for ever. (After a boot the count is 0 and mutter must NOT see it before the claim.)
    Fix = v5 `wf/rotate/cand/iio-accel-hold-back.py`: held back until the claim, or until 2 s after the client
    first read the property. Logic self-tested on the PC against glib (`an/cc-hold-back.sh`); replaces the commit
    in the local clone; patch `0002-main-hold-back-HasAccelerometer-until-a-client-has-c.patch`.
  - **gainmap** (sensor module q49b: analogue gain register per model = 0x3e09 rear, 0x3e08 front, as in stock's
    trace; slope of two exposures per code, black level drops out):
    rear SC1320CS (flash LEDs): 0x00 1.00, 0x01 1.96, 0x03 3.92, 0x07 7.82, 0x08 1.96, 0x09 3.91, 0x0b 7.80,
    0x0f 15.6, 0x1f 31.4, 0x27 15.5, 0x2f 31.2, 0x3f 63.4; front SC820CS (the screen at full white as the light):
    1.00, 2.03, 3.94, 7.87, 2.00, 3.96, 7.92, 16.0, 31.7, (0x23 48.4), 15.8, 31.7, 62.4, 0x7f 61.9.
    So every set bit of the low six doubles the gain; stock's own codes (0x0f rear; 0x09, 0x0b front) are on the
    ladder 0x00 0x08 0x09 0x0b 0x0f 0x1f 0x3f = 1 2 4 8 16 32 64. Fine digital gain 0x3e07: 0xc0 = 1.51x,
    0xff = 2.01x on both. Correction to entry 12: 0x0f / 0x1f / 0x3f are 16x / 32x / 64x, not 1x / 2x / 4x (the
    driver's old default 0x0f was already 16x, which is why libcamera's pictures were overexposed).
  - Sensor module q49c (`camdrv/gain-table.py`): V4L2_CID_ANALOGUE_GAIN = total gain x 128 (128..8192, linear):
    ladder step + fine digital gain, as stock does. libcamera's software AGC without a sensor helper takes the
    control as linear, so no libcamera patch is needed for auto-exposure.
- Lesson: `prep` checks of the kind "binqNN = queue head + 1 candidate" break when the candidate is queued; compare
  trees instead.
- Next: run 24 = RPMs again with v5, boot order / injection / two daemon restarts, libcamera auto-exposure (rear
  lit, rear dark, front), then systemd's suspend path with the packaged stack (logs fetched before it).

### 2026-10-02 - entry 15: run 24: packaged auto-rotate after a boot order, suspend path; two failures understood
- Run 24 (q49, 05:11-05:19): RPMs rebuilt with the daemon change v5 (rc 0, same checks as run 23).
  - rotpkg start / real / inject: PASS again (1 claim, 503 readings, 'normal'; 4 of 4 turns).
  - **rotpkg restart FAIL** (v5): two daemon restarts under the running session: 0 claims, and the daemon's
    "told after the wait" line never appeared. Cause read from the daemon's source: it takes its bus name BEFORE it
    opens its sensors (`name_acquired_handler` -> `find_sensors`), so mutter's property read can come while there is
    no accelerometer yet; v5 armed its 2 s timer only when the accelerometer existed. Fix v6
    (`wf/rotate/cand/iio-accel-hold-back.py`): the timer is always armed; a client whose delay ended before the
    accelerometer was found is told from `send_dbus_event()` when it appears. Self-test on the PC covers the three
    cases. Local clone commit 6e7aa4f, patch 0002 regenerated.
  - **rotsusp PASS for the path itself**: systemd's own suspend (`systemctl suspend -i` with an RTC alarm, 25 s)
    twice: suspend_stats 0 -> 1 -> 2, no failure, woke by irq 23 pm8xxx_rtc_alarm, ssh back both times. Without
    `iceland-ssc-resume.service` hexagonrpcd is inactive after the resume (its unit conflicts with suspend.target);
    with the unit enabled it is active again. The accelerometer answered `ssccli` in both cases. (GNOME's readings
    could not be judged here: it had no claim because of the restart failure above.)
  - **ae FAIL, not the auto-exposure**: the sensor module was loaded 5.5 minutes after boot and BOTH sensors gave
    no ACK on the chip-id read (`geni_i2c 884000.i2c: DMA txn failed:3`, chip id 0x0000). In run 23 the same
    read worked at 2.3 minutes, while GNOME was reading the accelerometer; in run 24 nobody was (restart failure).
    Hypotheses: (a) a supply the camera bus needs is held up by the ADSP's sensor hub only while its sensors run;
    (b) something time-dependent. Not the gain change (the probe code is unchanged).
- Next: run 25 = v6, `camdiag` (same boot: module loaded with an accelerometer client / with the sensor daemon
  stopped, at ~150 s and at ~350 s), auto-exposure with an accelerometer client held, suspend again.

### 2026-10-02 - entry 16: run 25: daemon v6 proven; the cameras need a rail the sensor hub switches; auto-exposure works
- Run 25 (q49, 05:26-05:37; sensor module q49c with the linear gain control):
  - **rotpkg restart PASS** (daemon v6): after the injection test's clean-up and after two more daemon restarts
    under the running session GNOME claims again 3 s after the daemon is up (130 / 145 readings, 'normal',
    managed=true). The journal shows the mechanism: three clients "look for the accelerometer before claiming it
    (not found yet)" at the daemon's start and are told 2 s later. start / real / inject: PASS as before.
  - **camdiag (root cause of run 24's camera failure)**: the sensor module loaded again and again in one boot:
    early (168-195 s): accelerometer in use 2 of 2 sensors answer, sensor daemon stopped for 12 s 0 of 2, in use
    again 2 of 2; late (324-362 s): stopped 0, in use 2, stopped 0, in use 2. Not time-dependent: the camera
    sensors only answer on their I2C bus while a sensor of the ADSP's sensor hub runs. Stock's sensor configs
    (`odm/sensor/config/*.json`, private) name the hub's rails: `vddio_rail` L1B_E0 for every sensor (1.8 V),
    L18B_E0 (accelerometer core), L2B_E0 (light / proximity). Our DT has `vreg_l1b_1p8` with no consumer and not
    always-on, so only the hub votes for it. Stock's camera nodes do not list L1B either (vio L2F, vana L14B,
    vdig L1F, vaf L16B): on stock the hub always has a sensor running while the screen is on.
    Runs 20-22 worked because the hub was never configured there (no hexagonrpcd), so its boot-time vote stayed.
  - **ae PASS in substance** (an accelerometer client held during the test): libcamera's software AGC takes the
    control as "Exposure 1-3999, gain 128-8192"; rear with the torch: frame 3 mean 47 -> last frame mean 118
    (mid grey; the preview shows the scene well exposed, a hand close to the lens blown out); rear dark 39 -> 46
    and front (dark room) 1 -> 39 at the top of the gain range. The AGC's own step lines were not captured (the
    log level list needs the category after `*:INFO`).
  - **rotsusp PASS**: two suspends through systemd, woke by the RTC alarm; GNOME reads the accelerometer again
    after the resume in both cases (124 readings in 5 s, 'normal'); hexagonrpcd is only running again with
    `iceland-ssc-resume.service`.
- Kernel q50 built (05:30): queue 0073 + candidate `an/dt-l1b-on.py` = `regulator-always-on` on `vreg_l1b_1p8`.
- Next: run 26 (q50): camdiag must give 2 of 2 with the sensor daemon stopped; the RPMs built in run 25 are
  installed from the PC through dnf (no build on the tablet); rotate tests again (the rail now stays on under the
  hub); auto-exposure with the sensor daemon stopped and the AGC steps logged; suspend.

### 2026-10-02 - entry 17: runs 26-31: the camera bus and the sensor hub (cause not found); new request: 5 workflows + install plan
- Run 26 (q50 = queue 0073 + `regulator-always-on` on `vreg_l1b_1p8`, sensor RPMs of run 25 installed from the PC
  through dnf, 05:40): prebuilt RPMs install and start (stack up at uptime 85 s); rotate start / real / inject /
  restart PASS again; **camdiag unchanged: 0 of 2 with the sensor daemon stopped** -> L1B is not it. Suspend PASS.
- Run 27 (q50): `camrail` = one hub sensor at a time through `ssccli`, PMIC B registers read singly: cameras
  answer with ANY hub sensor (magnetometer, light, proximity, accelerometer: 2 of 2; none: 0 of 2, five times).
  PMIC B: L1B on in all states, L2B only with light, L18B only with the accelerometer -> with the magnetometer
  nothing on PMIC B differs from "none". `ae` with an accelerometer client held: AGC steps logged (level list must
  be `*:INFO,IPASoftExposure:DEBUG`): gain 140.8 -> 691.9 in 18 steps / 70 frames, mean 60 -> 106-135.
- Run 28 (q50): `camdiff` = status + enable of every clock / GPIO / SMPS / LDO peripheral of all 8 PMICs, hub idle
  vs magnetometer, twice: no register follows the hub (SMPS status bit 3 flickers at random). `/sys/kernel/debug/
  gpio`: only TLMM gpio4 / gpio5 (the camera I2C lines) differ: HIGH with the hub idle, LOW with it active (camera
  rails off in both).
- Run 29 (q50, sensor module with `hold_ms`: keeps the sensor powered 4 s and reads again): while powered, idle vs
  magnetometer: 0 PMIC registers differ (status, voltage, mode, enable of all SMPS / LDO; reset pads; clocks);
  lines high in both; first and second read fail when idle, succeed with the magnetometer.
- gpio4 / gpio5 are eGPIO pads (`PINGROUP(4, qup2_se1, ibi_i3c, ..., egpio)`): owner bit 12 of the pad's CFG.
  Run 30 read every pad's CFG through /dev/mem and **the tablet reset at once** (reserved pads belong to the
  secure world; it came back to Android by itself, nothing written). Lesson: /dev/mem only for pads Linux uses.
  Run 31 (pads 4 / 5 only): CFG 0x01807 = owned by the application processor in every state; binding the I2C
  controller again does not bring the sensors back. -> not the owner bit.
- State of the camera question: three hypotheses tested and rejected (L1B, any PMIC rail / clock enable, eGPIO
  owner). Facts: works before the hub is ever configured (runs 20-22), fails with the hub configured and idle,
  works with any hub sensor streaming; the SoC-side lines are high at rest when it fails and low when it works
  (low = connected to the unpowered camera side). Suspect: a bus switch or level shifter between the SoC pads and
  the camera connector that the hub enables through a pin Linux cannot read (PMIC peripherals owned by another
  master read as errors: 928 of 1664 in run 28). In daily use GNOME holds the accelerometer whenever the screen
  is on, so the cameras work then. Candidate q50 (L1B always on) is dropped, not queued.
- 06:10 the user's new request: separate workflows for (1) low-battery current limiting (BCL), (2) charging,
  (3) charge limits, (4) GPU cooling, (5) improved thermals; and a full plan for the install (planning only:
  no bricking, restore to stock OxygenOS at any time, which partitions must never be flashed, default GNOME apps,
  upgrades that cannot brick and only take what fits our setup).
  -> `docs/WORKFLOW-BRIEF-2.md`; five background workflows started 06:14 (folders `build/wf/{bcl,charging,
  chargelimit,gpucool,thermal}`; PC work only, their tests are run by the main session afterwards).
  -> `docs/INSTALL-PLAN.md` written (gates, the two partitions that may be written, the never list, rehearsal
  from RAM with the exact image, the two writes, updates, rescue, return to stock, open decisions).

### 2026-10-02 - entry 18: runs 32-34: the camera bus is cut outside the SoC when the hub idles; first workflow results
- Commit G: iceland-mainline 241bbb2 (runs 23-31, packaging/sensors, iceland-device 0.15, docs/INSTALL-PLAN.md);
  matrix 52 / 9 / 12 / 2, page v28.
- Stock's device tree has 8 mA drive strength for the camera I2C lines (overlay) and a sleep pin state that hands the
  two pads to the sensor island (`qcom,remote`); ours has 2 mA and no sleep state.
  Run 32 (q51 = queue 0073 + `an/dt-i2c9-drive.py`, 8 mA): camdiag unchanged (0 of 2 with the hub idle) -> not it.
- Run 33 (`campull`, pads 4 / 5 only, register restored): the pad's level with its own pull set to down / none /
  up: hub active 0 / 0 / 0 (the unpowered camera side pulls the lines low: connected); **hub idle 0 / 0 / 1 (the
  pad follows its own pull: alive, and nothing hangs on it)**. So with the hub idle the camera side is disconnected
  from the SoC pads, outside the SoC.
- Stock has four "bidirectional level shifter" pin states on PMIC B (GPIO pairs 11/12 .. 17/18). Run 34 (`camls`):
  registers 0x00-0x5f of those GPIOs (and of 0x51 / 0x5e): identical with the hub active and idle (mode 00, enable
  00 in all states) -> not them.
- Rejected so far: L1B, every readable PMIC rail / clock / GPIO register, the eGPIO owner bit, rebinding the I2C
  controller, 8 mA, PMIC B's level-shifter GPIOs. What is left is a switch driven from the hub's side through a pin
  that is reserved for it (Linux can neither read nor set reserved pads). Stock has the same dependency in
  principle; there the hub always has a sensor running while the screen is on.
  Practical answer: `iceland-ssc-hold.service` (holds the accelerometer through `monitor-sensor --accel`, bound to
  the sensor daemon) so that the cameras do not depend on GNOME's own claim (orientation lock, no session).
  Test in run 35 (`hubhold`), then auto-exposure over 160 frames with only that unit holding the hub.
- Workflow "chargelimit" delivered (06:42): GNOME's switch needs `charge_control_*_threshold` on the battery (UPower's
  udev rule); stock's limit is a kernel loop through `OPLUS_CHG_EN`, the knob our guard uses; candidate
  `wf/chargelimit/cand/battmgr-charge-limit.py` (14 edits, compiles, 29-case self-test), hwdb 80 / 85, guard
  follows the kernel's thresholds; test `wf_chargelimit`. Its REPORT / NEXT saved by the main session.
- Workflow "bcl" delivered (06:47): stock = two PMIC BCL blocks (alarms cap only the GPU: 1100 / 1000 / 826 MHz)
  + "socd" at 5 % (CPUs 2227200 / 2438400 kHz, GPU 826 MHz); mainline has no driver. Candidates: kernel driver
  `qcom-spmi-bcl` + device tree (syntax-checked), user-space `iceland-bcl-guard` (31 simulated cases); test `wf_bcl`
  (read-only except the three maximum-frequency files, lowered and restored). REPORT / NEXT saved.
- Run 35 (q51 kit; its only difference from the queue head is the 8 mA candidate): bcl run A, chargelimit run A,
  hubhold, ae.

### 2026-10-02 - entry 19: runs 35-36: auto-exposure settles, the hub holder unit, first workflow tests
- Run 35 (q51 kit, 06:55):
  - **bcl run A PASS**: both PMIC BCL blocks answer (PMIH0108 rev 05.01, PMH0101 rev 05.02), enable 0x80, alarms as
    the firmware left them 2790 / 2600 / 2300 mV + 13437 / 15000 mA and 2850 / 2700 / 2300 mV (stock's table for
    this temperature: 2800 / 2800 / 2600 and 2850 / 2700 / 2500), voltage reading 4211 mV against the battery's
    4214 mV; 0 BCL interrupts / zones in today's kernel; the guard's 31 simulated cases pass; live with a simulated
    4 % battery: maxima [3628800 4396800 1200000000] -> [2227200 2438400 826000000] -> restored.
  - chargelimit run A: as expected (no threshold attributes, UPower "not supported", GNOME group hidden).
  - **hubhold PASS**: no desktop session and no holder: 0 of 2 camera sensors; `iceland-ssc-hold.service` started:
    2 of 2; after a restart of the sensor daemon: 2 of 2; daemon stopped: 0 of 2 (the holder goes with it). After the
    daemon was started again the holder stayed off (the test unit was not enabled) -> the packaged version gets
    `Wants=iceland-ssc-hold.service` in the daemon's drop-in.
  - **ae PASS with only the holder keeping the hub awake** (no desktop session): rear with the torch, 160 frames:
    gain 140.8 -> 2161 in 30 steps, exposureMSV 1.0 -> 2.35 (target 2.5 +- 0.2), **settled** (last 10 steps equal),
    frame mean 34 -> 135. Rear dark: gain to the maximum 8192. Front (dark room): still rising after 70 frames.
- Run 36 (q51 kit, 07:03): **charging run A PASS** (workflow "charging"): SDP, VBUS 4975 mV, input 497 of 500 mA,
  charge limit 600 mA = stock; inhibit: 0 uA "Not charging" while inhibited, +136 mA "Charging" after; the
  charge-current knob could not be judged (only 136 mA of charge current on the PC port with the screen off; the
  test needs 180 mA). The session draws 660 mA from the battery with the screen on.
- Workflow "charging" delivered (07:00): on the PC port everything is right and the 6 % per hour drain is the port's
  2.5 W against the session's 4.5 W (stock would do the same). Gaps on wall chargers (from the code): the
  charge-current limit goes through the generic property (stock: 0x300 / 66), a suspend on a charger leaves charging
  to the firmware alone, the type is read once per attach, no stepped input current, C / ACA / Apple as 500 mA,
  rejected requests count as success. Five kernel candidates + a debug probe, a guard candidate (blocks sleep
  while a charger is in), a logger for one sitting with wall chargers. REPORT / NEXT saved.
- Workflow "thermal" delivered (07:08): stock's kernel does NOTHING on the skin thermistor; its policy is a fitted
  shell temperature (five models over skin, WLAN, board, charge pump, battery) with 20 gears from 27 C in 2 C
  steps (CPU / GPU / brightness / charging per gear), read from the tablet's own horae files (decoded on the PC
  with the key in the tablet's own binary). Candidates: two missing sensors in the device tree, a policy daemon
  `iceland-thermal`, the skin loop moved to stock's 60 / 61 C trips as a backstop, stock's PMIC cooling maps.
  **PRIVATE: `wf/thermal/priv/` and `wf/thermal/tablet-in/thermal-model.json` (stock's fitting coefficients and the
  decoded files): RAM only on the tablet, never in a log set, never committed.**
- Kernel q52 built (07:06): queue 0073 + the charge-limit candidate + the BCL driver and its zones
  (`build-q52.sh`). The charging candidates touch the same lines as the charge limit and get their own kernel.
- Run 37 (q52): chargelimit run B (with the hwdb entry), bcl run B (thermal emulation).

### 2026-10-02 - entry 20: run 37, queue 0074-0076, all five workflows delivered; SAVE POINT (user: "save everything and stop for compacting")
- Run 37 (q52 = queue 0073 + charge limit + BCL driver, 07:10):
  - **chargelimit run B**: attributes present; values PASS (end 83 / start 80 read back, 101 refused); hold: status
    "Not charging" after 5 s (28 -> 0 mA: the charge current on the PC port was too small to judge the step);
    release: +114 mA "Charging" after 5 s; UPower PASS (supported, EnableChargeThreshold as the desktop user ->
    sysfs 75 / 80, off -> 0 / 100); GNOME "Battery Charging" group shown, radio follows; everything left as found.
    Open: the candidate hwdb entry (80 / 85) did not take effect (udev still 75,80; `hwdb-update.txt` is empty).
  - **bcl run B PASS**: driver probes on both PMICs (revision 5), alarms programmed to stock's table for 32 C
    (2800 / 2800 / 2600 mV and 2850 / 2700 / 2500 mV), six interrupts with count 0, emulation 7 of 7 zones
    limited to stock's values and released; the user-space guard steps aside.
- **Queued: iceland-linux 70f9604 = 0074 (charge limit), 0075 (qcom-spmi-bcl driver), 0076 (BCL nodes + zones)**,
  `CONFIG_QCOM_SPMI_BCL=y`; queue 0001-0076; the tree equals q52 (`queue-0074.sh`, verified by prepare.sh).
- Workflows "gpucool" and "thermal" delivered; all five have REPORT.md / NEXT.md / tablet.sh / cand/ in
  `build/wf/<name>/`. gpucool: keep the 125 C critical trip (stock powers off there through its thermal service);
  one gap = the PMH0110 F map (GPU from state 5 at 95 C), which the thermal workflow's `dt-pmic-maps.py` also adds.
- Kernel q53 built (07:17): queue 0073 + charging candidates 1, 2, 4, 5 + probe + thermal device tree candidates
  (inputs, skin 60 / 61 C, PMIC maps). `build-q53.sh`; sensor module `camdrv/sc1320cs-q53.ko`.
- Prepared, NOT run: run 38 (`gen-combo-38.py`, kit q51: thermal "before" + gpucool on the queue kernel) and run 39
  (`gen-combo-39.py`, kit q53: charging B, thermal "after" with the private model in RAM, gpucool). The chain of
  run 38 was stopped before it booted the tablet (the user asked to stop). Chains: scratchpad
  `area-combo-38-chain.sh`; for 39 derive it from 38 with sed as before. The prep checks of 38 / 39 accept a kernel
  "built on the queue" (the queue head moved to 0076).
- Next after the break, in this order:
  1. run 38, then run 39; judge with each workflow's NEXT.md.
  2. If run 39 passes: queue the thermal device tree candidates and the charging candidates 4 and 1 (2 if the ladder
     ends at 500 mA on the PC port); the charging candidates must be rebased onto 0074 (same lines of
     qcom_battmgr.c: `an/cand-apply-check.sh` shows which asserts fail).
  3. iceland-device 0.16: `iceland-ssc-hold.service` + `Wants=` in the daemon's drop-in (proven in run 35), the
     hwdb entry (find out why it did not take effect), then - after the user's decisions - the guard changes of
     chargelimit / charging / thermal merged into ONE guard (three candidates touch the same file), the thermal
     daemon, the BCL guard is no longer needed (kernel driver queued).
  4. Commit H is done at this save point (logs of runs 32-37, tools, the four non-thermal workflow folders).
     `wf/thermal` is NOT committed: its report carries stock's fitted weights; `wf/thermal/priv/`,
     `wf/thermal/tablet-in/thermal-model.json` and `cand/mk-thermal-model.py` stay private until the user decides.
  5. The private sensor driver: retry the chip-id read later instead of failing the probe (hub idle at probe time).
- Decisions waiting for the user (collected from the workflows and the plan):
  install: Fedora only or dual boot; boot path `boot_b` or `recovery_b`; open gates block or "charge attended";
  camera module in the image. Charge limit: on by default; hold or charge to the limit when switched on between
  the thresholds; watched during sleep (keep awake on a charger = also the charging guard's KEEP_AWAKE).
  Thermal: skin loop at 60 / 61 C with the policy daemon (recommended) or 50 / 60 or 48 C; Balanced = stock's normal
  table (first cap at 33 C shell temperature) or shifted like Performance; may stock's fitting coefficients be
  committed to the private repo. GPU: an optional 30-minute soak. Earlier ones: one turn of the tablet, Wi-Fi
  password for a 5 GHz connect, reporting the mutter bug, wall-charger sitting, microphone meter look.

### 2026-10-02 - entry 21: resumed; run 38 (thermal baseline, gpucool); stuck CPU limits found; camera workflow started

- User: "resume", then mid-turn "finalize camera as well in seperate workflow". Brief written
  (`docs/WORKFLOW-BRIEF-3-camera.md`: driver robustness, focus motor, picture quality with the software ISP, the
  apps, flash, shipping the private driver, the bus switch) and the workflow started as a background agent; its
  folder is `build/wf/camera/` (`priv/` for anything that quotes the private driver or stock tuning data).
- **Run 38** (kit q51 = queue 0073 + 8 mA; first try stopped at the kit build: a quote character in the kit
  description, fixed in `gen-combo-38.py` / `gen-combo-39.py`):
  - `thermal` run A ("before", kernel zones only): 3 PASS / 0 FAIL / 1 WARN. 70 zones; walk PASS at 48 / 51 C
    (gear 998400 / 883200 kHz + 342 MHz at once, released in 0.75 s); no PMIC maps, no daemon (expected).
    60 s all-core load: skin 39.5 -> 52.0 C in 5 s (2.5 C/s), peak 52.7 C, hottest CPU sensor 106 C; from 30 s
    on the caps are 1.35 / 1.29 GHz and GPU 472 MHz; work 202032 chunks (6711 /s in the first 5 s, 3131 /s in the
    last 30 s) = the baseline for run B. WARN: 90 s after the load the CPU cooling states are still 14 / 14.
  - `gpucool`: 7 PASS, 2 FAIL, 2 SKIP. The read-only checks pass (18 levels, 11 GPU zones with 105 C loop and
    125 C shutdown, skin + XO maps, governors, no faults). SKIP emul + FAIL restore: the CPU cooling states were
    still 14 / 14 three minutes after the thermal load (skin 39 C). FAIL limits: the test's own stop limit (GPU
    sensor 100 C) was reached 7 s into the first free run (43 -> 103.8 C at 1200 MHz); nothing was judged.
- **Finding: CPU limits stay stuck at state 14 after a heavy load** (1.9 / 2.67 GHz instead of 3.6 / 4.4 GHz, until
  a CPU sensor interrupt happens to come). Cause as read from the source (to be proven in run 39):
  `gov_step_wise.c` gives an instance whose trip is NOT exceeded its `lower` state when its zone sees a falling
  temperature while the cooling device's current state is above `lower` - the state of the shared cooling device,
  which another zone (the skin loop at 18-22) holds up. The CPU zones' 112 C maps (queue 0023) have lower = 14;
  a tsens zone is not polled once it has left its passive state, so the stale 14 stays. GPU maps have no such
  lower bound: the GPU is released (0), as seen.
- Changes for run 39 (`an/edit-gen39.py`): order charging -> gpucool -> thermal -> new part `stuck`
  (`an/combo39-parts.sh`: reads the states after the load, releases them with a falling emulated temperature on
  the CPU / LLC zones, then reproduces the fault with emulation only: skin above its gear trip, one CPU zone per
  cluster 90 -> 80 C, skin off; expects 14 / 14 on this kernel). gpucool test: free runs 5 s instead of 10 s, GPU
  stop limit 104 C instead of 100 C (still below stock's first GPU threshold, 105 C).
- Charge-limit hwdb entry (run 37: "did not take effect"): cause found in the logs: `systemd-hwdb query` already
  answered 80,85, but udev kept the old database for the re-trigger. `udevadm control --reload` added to the test
  and to the package's %posttrans.
- iceland-device 0.16 prepared in the repo, not yet built or tested (`build/pkg-016.py`): `iceland-ssc-hold.service`
  + `Wants=` in iio-sensor-proxy's drop-in, `61-iceland-battery.hwdb` (80 / 85 %). Unit test: 12 PASS.
- Charging candidates rebased onto queue 0076 (`an/rebase-charging.py` -> `wf/charging/cand/rebased/`; 0074 had
  moved the anchors of candidates 1 and 2); all five and the three thermal device tree candidates apply on the
  queue head (`an/cand-apply-check3.sh`). Without the skin change the inputs + PMIC maps also apply alone
  (`an/cand-apply-check4.sh`): the skin loop's move to 60 / 61 C waits for the user's decision.
- Run 39 started (kit q53: charging B, gpucool, thermal "after" with the private model in RAM, stuck).

### 2026-10-02 - entry 22: run 39 (kernel q53): charging B and thermal B pass; two kernel faults found and fixed in q54

- **Run 39** (kit q53 = queue 0073 + charging candidates 1 2 4 5 + probe + thermal DT candidates), order charging,
  gpucool, thermal, stuck:
  - `charging` run B: **PASS**. Kernel line as the workflow's criterion: "charger: type 1, input limit 500000 uA,
    charge limit 600000 uA, ... AICL 500000 of 500000 uA, VBUS 4959 mV"; no "charger type changed", no "rejected
    by the charger firmware"; every OnePlus SET answers result 0 (12, 5, 70). Input 497 of 500 mA, inhibit ok
    (0 uA "Not charging", then +91 mA "Charging"). Probe: float voltage 4480000 uV; the firmware's own charge
    limit reads back 2500000 uA while the driver's limit for a PC port is 600000 uA; "charge-current knob: not
    decidable" again (only 91 mA of charge current on the PC port) -> stays with the wall-charger sitting.
  - `thermal` run B ("after": policy daemon + private model in RAM): **7 PASS / 0 FAIL / 0 WARN**. 72 zones;
    wlan-thermal 34.2 C and chg-cp-thermal 33.9 C read plausibly (board 32.6 C); stock's shell estimate at idle
    34.4 C (gear 3); walk PASS at 60 / 61 C; policy 20 of 20 steps as stock's table, handed back on SIGTERM;
    load with the daemon: skin 39.2 -> 56.0 C (1.3 C/s at first, peak 56.0 C, limit 65 C), hottest CPU sensor
    89 C, caps from 30 s on 2.00 / 1.63 GHz, GPU not limited, gear 7, shell 40.8 C; work 281872 chunks (run A:
    202032, +40 %), last 30 s 4446 chunks/s (run A: 3131, +42 %); restore PASS. "pmic no maps" although the
    candidate was in the device tree -> fault 2 below.
  - `gpucool`: 13 PASS, 3 FAIL, 1 SKIP. New passes: walkup (105.0 .. 106.6 C: states 1 .. 17), walkdown, hot,
    release, skin, XO, restore. FAIL maps = this kernel has the skin trips at 60 / 61 C (the test looks for 48 /
    51). FAIL pmic = fault 2. FAIL limits: the third load run stopped at the skin stop limit (51.4 C; the three
    runs follow each other without a pause). Numbers so far: 393 fps free, 174 fps at 342 MHz. Test changed:
    it now waits until the skin sensor is back at 45 C (at most 45 s) before the last free run
    (`an/edit-gpucool2.py`).
  - `stuck`: **reproduced with emulation only**: skin emulated above its gear trip -> states 22 / 27; one CPU zone
    per cluster emulated 90 -> 80 C; skin emulation off -> states 14 / 14 (1900800 / 2668800 kHz) and they stay;
    a falling emulated temperature on every CPU / LLC zone releases them (0 / 0).
- **Fault 1, generic kernel (gov_step_wise)**: confirmed as described in entry 21. Upstream changed the governor
  in 2024 to "go straight to instance->lower when mitigation is over" (lkml 2406.2/09576); it still decides from
  the cooling DEVICE's current state, which another zone can hold up. Fix `an/stepwise-release.py`: a trip that
  needs no mitigation drops its request at once (THERMAL_NO_TARGET).
- **Fault 2, generic kernel (qcom-spmi-temp-alarm)**: for the "gen2 rev2" and "lite" alarm variants the driver
  stores its own stage index in `trip->priv`; thermal_of keeps the trip's device tree node there and matches every
  cooling map against it, so no cooling map of such a PMIC zone can bind (DTB of q53 has the maps, sysfs has no
  binding). Fix `an/tempalarm-trip-priv.py`: the driver remembers `trip->priv` per stage and looks the stage up.
- Kernel **q54** (`build-q54.sh`) = queue 0076 + the two fixes + charging 4, 1, 2 (rebased) + thermal DT inputs +
  PMIC maps; no test-only code; the skin loop stays at 48 / 51 C (the move to 60 / 61 C needs the user's decision
  and the policy daemon). This is the tree meant for the queue.
- Next: run 40 on q54 (`gen-combo-40.py`: charging, chargelimit with the hwdb entry, gpucool, thermal kernel-only,
  stuck = must not reproduce, bcl); then queue; run 41 (`gen-combo-41.py`, part `pkg16` in
  `an/combo41-parts.sh`): iceland-device 0.16 built and installed, holder unit and hwdb from the package.

### 2026-10-02 - entry 23: run 40 (kernel q54) passes -> queue 0077-0083; camera workflow delivered; run 41 started

- **Run 40** (kit q54 = queue 0076 + governor fix + temp-alarm fix + charging 4 1 2 + thermal DT inputs + PMIC
  maps; the tree meant for the queue):
  - `charging`: PASS (497 of 500 mA, "AICL 500000 of 500000 uA, VBUS 4968 mV", inhibit ok; no "rejected", no
    "type changed" line).
  - `chargelimit` with the hwdb entry and `udevadm control --reload`: udev CHARGE_LIMIT 80,85; UPower thresholds
    80 / 85; enabling as the desktop user -> sysfs start 80 end 85, disabling -> 0 / 100; hold PASS (end 82 at
    83 %: "Not charging", 120833 -> 0 uA in 5 s), release PASS (+106 mA after 5 s); GNOME group shown.
    Seen again: right after the boot UPower says "not supported" until it is restarted - it started within a
    second of the system manager, before udev had processed the battery, and reads the property only once.
  - `gpucool`: 19 PASS, 1 FAIL. pmic PASS (PMH0110 F at 95.5 C -> GPU state 5 = 826 MHz, released), limits PASS
    (GPU 98.4 C, skin 49.8 C), cap PASS (never above 342 MHz, 175 fps), effect PASS (392 -> 175 fps), recover
    PASS (388 fps). FAIL ramp = the test's own check (asked for 4 samples, the shortened free run gives 3: "at
    the limit in 3 of 3 samples"); check corrected (`an/edit-gpucool3.py`), repeated in run 41.
  - `thermal` (kernel zones only): 6 PASS / 1 FAIL. pmic PASS (96 C emulated: f 0/0/5, g 27/0/0, i 0/28/0,
    released) = the temp-alarm fix works; restore PASS: cooling states 0 / 0 / 0 after 4.25 s (before the governor
    fix: 14 / 14 for minutes); load: caps 1.26 / 1.18 GHz from 30 s on, work 188221 chunks. FAIL zones = the
    test's expected count (70 + inputs): this kernel has 79 = 72 + the 7 BCL zones; not a fault.
  - `stuck`: NOT reproduced (gear 22 / 27, released to 0 / 0).
  - `bcl`: PASS (alarms as stock's table, 6 interrupts, 7 of 7 zones limited and released).
  - no WARNING / BUG line in the kernel log.
- **Queue 0077-0083** (`queue-0077.sh`, dry run first: the seven commits give exactly the tree of q54; src branch
  `iceland` is at 0083): 0077 gov_step_wise release, 0078 rejected OnePlus request is an error, 0079 limits
  follow the charger type, 0080 input current in stock's steps, 0081 temp-alarm keeps trip->priv, 0082 WLAN and
  charge-pump thermistors, 0083 PMH0110 F / G / I cooling maps. The verification's kernel clone from GitHub
  stalled (124K in ten minutes) and was stopped; `queue-0077-finish.sh` repeats verify + commit + push.
- **Camera workflow delivered** (`build/wf/camera/`: REPORT.md, NEXT.md saved by the main session, tablet.sh,
  candidates per work package, private parts under `priv/`). Main finding: the camera I2C lines run through two
  level shifters inside the PMH0101 whose enable is an RPMh resource (LS1B_E0 / LS2B_E0); the vendor tree keeps
  both always on, mainline has no entry, so they are on only while the sensor hub votes. Candidate: regulators
  ls1-ls4 in the RPMh regulator driver + ls1 / ls2 always-on. Also: the driver patcher (silent bus at probe is a
  warning, re-init at every stream start, frame timing corrected to stock's 30 fps, a binned rear mode), the
  focus motor = mainline dw9719 (DW9800K protocol, 0x0c, needs the L2F supply; libcamera 0.7.1's simple
  pipeline has no lens control, so focus stays manual), black level tuning files, private colour matrices,
  tests for GNOME Camera and a browser, a kmod spec for the private module.
- Patched private sensor module built for q54 (`an/cam-build-r.sh` -> `camdrv/sc1320cs-q54r.ko`; the old driver
  is kept as `camdrv/sc1320cs.c.q54`).
- iceland-device 0.16 gained a UPower drop-in (`pkg-016b.py`: UPower after systemd-udev-settle; cannot be proven
  in a RAM session, where UPower starts before the package is installed - to check at the install rehearsal).
- Prepared: run 41 (`gen-combo-41.py`: gpucool again, pkg2 = RPMs incl. iceland-device 0.16, rotpkg start, pkg16 =
  holder + hwdb + UPower drop-in, chargelimit from the package's thresholds) - started 08:28; run 42
  (`gen-combo-42.py`: camera run A + C with the patched module); `build-q55.sh` (queue head + level shifters +
  focus) for camera run B - to be RUN only after run 42 has shown LS1B_E0 / LS2B_E0 in the command DB.

### 2026-10-02 - entry 24: run 41 (package 0.16) passes; commit I; run 42 (camera A + C); six round-4 workflows started

- **Run 41** (kit q54): gpucool **20 PASS / 0 FAIL** (392 fps free, 175 fps at 342 MHz, 388 fps after; GPU 98.4 C
  max). pkg2: sensor RPMs build in 9.8 s, iceland-device 0.16 in 9.3 s, install rc 0 / 0, `rpm -V` clean.
  rotpkg start: accelerometer after 1.9 s. **pkg16: holder PASS** (holder active after the packaged start; camera
  sensors 2 of 2 with no desktop session, after a daemon restart, after stop / start: the holder stops with the
  daemon and comes back by itself), **hwdb PASS** (udev CHARGE_LIMIT 80,85 from the installed package), UPower
  ordered after systemd-udev-settle. chargelimit with the package's thresholds: PASS (hold 93916 -> 0 uA at end
  81 %, release +101 mA, UPower on -> 80 / 85, off -> 0 / 100, GNOME group shown).
- Queue verification finished from the local base (`queue-0077-finish.sh`): "prepared tree = expected",
  iceland-linux **6c44bdc** pushed (0077-0083).
- **Commit I**: iceland-mainline **0663d62** (467 files: log sets of runs 38-41, results part H, work log,
  packaging 0.16, tools, the camera workflow's public deliverables + brief; no private names). Matrix
  (`research/matrix-c2h.py`): **55 working / 8 in progress / 11 not started / 2 not planned (76)**; new row "Skin
  temperature policy (stock gears)" (in progress, waits for the user's choices); GPU cooling -> working; device
  package -> 0.16. Page **v30**.
- **Run 42** (kit q54 + patched sensor module `sc1320cs-q54r.ko`; camera workflow run A + C):
  - bus: the RPMh command DB lists **LS1B_E0 .. LS4B_E0** (0x46c00 .. 0x46f00) = the gate for kernel q55 is
    passed. "2 of 2 with the hub idle" in this run proves nothing: the sensor stack was never started in this
    boot, so the hub was never configured and the level shifters were still in their boot state.
  - driver: patched driver loads, both sensors in the media graph, libcamera lists 2, streams rc 0; the "bus cut
    during a stream" case did not happen for the same reason (808 frames, no cut).
  - timing: **4 of 4 modes at 30.00 fps** (rear 4160x3120 and the new 2104x1560, front 3264x2448 and 1632x1224;
    line 5520 / 3520 pixel clocks as the workflow derived).
  - quality: 6 of 6 captures, 30 fps, the rear preview uses the binned 2104x1560 mode, the tuning files are
    loaded (`sc1320cs.yaml`, `sc820cs.yaml`), first AGC gain 563.2 (the 4x start), the private matrices raise the
    colourfulness (34 -> 69 rear, 22 -> 45 front). "settled no": 100 frames are too few in a dim room with the
    torch at 1/6 (gain 563 -> 5508 and still rising, mean 133-148) - a test length matter, to send back.
- Runs prepared: 43 (`gen-combo-43.py`: q54, pkg2 + rotpkg start so that the hub IS configured, then cam-a = the
  real baseline and the driver's silent-bus test; started 08:5x), 44 (`gen-combo-44.py`: q55 with the level
  shifters + focus: pkg2, rotpkg start, cam-b "bus focus flash", cam-d "app").
- **User (mid-turn): "Start workflows to address below not started items , test run and fix till resolution and
  use autonomous agents till they are working(Display&input,Power&charging, Sleep&powersaving,
  Software&packaging)".** Brief `docs/WORKFLOW-BRIEF-4.md`; six background agents started, one per not-started
  row of those sections, folders `build/wf/<name>/`:
  pogo (Pogo keyboard), pencharge (Pen charging), wake (Wake by lid / keyboard / charger), deepsleep (Deep-sleep
  proof), apps (Full GNOME app set), audit (Stock-values audit). Loop: an agent delivers -> the main session
  runs its test on the tablet -> results go back to the agent (SendMessage) -> fix -> again, until the item works
  or is proven to need the user's hands (keyboard, pen, lid, a night unplugged).
- Lesson: a shell loop variable inside `wsl.exe bash -c '...'` is expanded by the outer layer (it created
  wf/work, wf/cand, wf/priv; removed): loops go into script files.

### 2026-10-02 - entry 25: runs 43-44: the camera bus fix and the focus motor work -> queue 0084-0089

- **Run 43** (kit q54 = queue 0083, patched sensor module, the hub configured through pkg2 + rotpkg start):
  bus: hub idle (sensor daemon stopped, the packaged holder goes with it) **0 of 2**, with the holder 2 of 2 = the
  true baseline. Driver, now really tested: probe with the hub idle 0 answered / **2 registered without an
  answer / 0 probe failures**; libcamera lists 2 cameras; first stream after the bus is back rc 0, 20 frames; bus
  cut during a stream: **1** "stopped answering" line (5 camera / I2C lines in all, no flood); stream after the
  cut rc 0, 20 frames. timing 4 of 4 at 30 fps.
- **Run 44** (kit q55 = queue 0083 + PMH0101 level shifters ls1-ls4 with ls1 / ls2 always on + dw9719 "vio" supply
  + focus node, hub configured):
  - **bus PASS**: `vreg_ls1b` / `vreg_ls2b` on with use count 1; hub idle **2 of 2 sensors answer**. The cause of
    runs 24-34 is confirmed: the camera I2C lines run through two level shifters of the PMH0101 that only the
    sensor hub voted for.
  - **focus PASS**: `dw9719 0-000c` bound and linked to the rear sensor (`focus_absolute` 0..1023); sweep on the
    binned mode: sharpness 7624 at 0, 3876 at 100, 83036 at 800, 15821 at 1000 = ratio 21.4 with a clear maximum
    at 800; module EEPROM at 0x58 answers (calibration words 352, 734, 736, 398).
  - flash: `yellow:flash-0` alone lights the rear camera's scene (mean 64 -> 231), `white:flash-1` alone does not.
  - **app: not passed**: Snapshot 50.0 starts but shows only its "Camera" page with a Close button, no preview, no
    running source; its log stops at the camera portal request; the session journal has "xdg-document-portal:
    fuse init failed" and "Document portal fuse mount point unknown"; only xdg-desktop-portal-gtk is on the
    accessibility bus. Sent back to the camera workflow with the other findings (bus / driver steps must detect
    an unconfigured hub; quality must run until it settles; fixed focus position; package changes without the
    holder).
- **Queue 0084-0089** (`queue-0084.sh`, dry run = tree of q55): rpmh binding + driver for the PMH0101 level
  shifters, board file keeps ls1 / ls2 on, dw9719 binding + driver "vio" supply, focus motor node enabled.
  Verification from the local base as in entry 23.
- The private driver in `camdrv/sc1320cs.c` is the patched one (30 fps, binned rear mode, silent-bus handling).
- Next for the cameras: iceland-device 0.17 without the holder unit once the camera workflow confirms; the Camera
  app / browser steps after the workflow's next delivery; matrix + commit.

### 2026-10-02 - entry 26: queue 0084-0089 pushed, commit J; "till all green"; the flashing guide; two more workflows

- Queue 0084-0089 verified and pushed: iceland-linux **c52d6ee** (queue head = the tree of test kernel q55).
  Commit J: iceland-mainline **cbecbd0** (runs 42-44, results part I, brief 4). Matrix page v31 (counts unchanged:
  55 / 8 / 11 / 2; the camera row now says what is solved and what is open).
- User: "continue till all workflows are completed and green", then "once all working flows are green , update
  accordingly the project knowledge and make sure the repos are updated, Meanwhile write a complete guide for
  flashing this on my tablet and make sure it follows the safety measures set before".
- **Flashing guide written: `docs/INSTALL-GUIDE.md`** (project folder + docs repo, sent to the user). Built on
  `docs/INSTALL-PLAN.md`: readiness table, the safety rules, Part A (read-only preparation: backup and stock image
  verification, return-to-stock dry run, second copy, read-only copies of `/data/vendor` and today's `boot_b`,
  slot flags), Part B (the RAM rehearsal that must produce the two files and their checksums), Part C (write 1:
  `fastboot flash userdata`), Part D (write 2: `fastboot flash boot_b`, the retry-count check, the undo, the
  `recovery_b` alternative), after the install, back to stock, a "what if" table, the record to fill in. Sizes
  taken from the backup's own partition table: userdata 463202424 sectors = 237159641088 bytes (0x3737D0F000),
  boot_b 100663296 bytes (0x6000000). Parts C and D are locked until Part B has run: its tools do not exist yet.
- Two more background agents started:
  - **pkg017**: merges the three battery-guard candidates (chargelimit, charging, thermal cap) and packages the
    thermal policy daemon = iceland-device 0.17 as a generator + tests (`build/wf/pkg017/`). Defaults taken where
    the user has not answered, each a one-line setting: KEEP_AWAKE=1 as stock, the guard follows the kernel's
    charge thresholds, the policy daemon on, the kernel's skin loop stays at 48 / 51 C (the move to 60 / 61 C
    remains the user's choice), stock's model file stays private and outside the package.
  - **install**: the PC-side tooling of the install plan's work list 1-4 (kernel rpm with the device-tree hook,
    read-only rule / snapshot / trial-boot units, on-device firmware extractor, image builder, the RAM rehearsal
    harness with the acceptance list, update and rollback rehearsal) in `build/wf/install/`. No script of it may
    contain a write to the tablet; rehearsals are `fastboot boot` only.
- **Run 45** (kit q55 = queue head 0089; regression of the finished workflows on the final tree) started 09:15:
  so far charging PASS, chargelimit PASS, gpucool 20 PASS / 0 FAIL, thermal 7 PASS / 0 FAIL / 0 WARN (79 zones,
  PMIC maps, restore) - the rest (stuck, bcl) follows.
- **Run 45 finished, all six parts green on the queue head (kernel q55 = 0001-0089):** charging PASS (497 of
  500 mA, inhibit ok), chargelimit PASS (80 / 85 through the hwdb entry, hold 128833 -> 0 uA, release, GNOME group),
  gpucool 20 PASS / 0 FAIL, thermal 7 PASS / 0 FAIL / 0 WARN (79 zones, PMIC maps f 0/0/5 g 27/0/0 i 0/28/0,
  restore), stuck NOT reproduced, bcl PASS (7 of 7 zones). No WARNING / BUG / Oops in the kernel log. Battery 80 %
  at the end (it drains during test runs on the PC port: pause the runs below 40 %).

### 2026-10-02 - entry 27: SAVE POINT (usage limit reached): run 47 pencharge result, pogo delivered, what is running

- **Run 47** (kit q56 = queue head 0089 + pen charging candidates; `build-q56.sh`, `gen-combo-47.py` through the new
  generator `an/genwf.py`): the pen charger driver comes up without a reset: IC 0x5806 firmware 0x20022, hBoost
  7000 mV asked and confirmed by the charger firmware, lines as stock's idle state, state idle, inhibit works,
  rebind works. Two checks FAIL (after the unbind the test reads no state for the power / tx-off lines) and one
  note (the IC reads 5017 mV where 7000 mV was confirmed). Sent back to the pencharge agent (id
  a410fb5800fadd638) with three questions; log set `build/area-combo-47/combo/pencharge/`.
- **Run 46** (kit q55, camera round 2: pkg2, rotpkg start, cam-d app, cam-f "focus fixfocus", cam-c quality,
  cam-e browser; `gen-combo-46.py`) was started right after run 47 by `scratchpad/run-chain.sh 47 46 ...`; it
  finishes on its own and reboots the tablet to Android. NOT judged yet: read `area-combo-46-probe.log`
  (lines "camera (") and `build/area-combo-46/combo/camera/*/result.txt`, criteria in `wf/camera/NEXT.md`.
- **Camera agent, round 2 delivered** (id a3b3533c41c6d6b08): the Camera app was waiting on the portal's
  permission dialog; test now sets the permission for the run; `cand/wp4-apps/pkg-017-camera.py` = device package
  changes (holder unit out, tuning files, WirePlumber rule, fixed-focus helper at stock's position 450).
- **Pogo agent delivered** (id a53da1519c5319e23): `wf/pogo/` (serdev driver for the keyboard dock at 921600 baud,
  binding, UART node, board nodes; `cand/kernel/pogo-kernel.py`; config `KEYBOARD_ONEPLUS_POGO=y`). NOT built or
  run yet. Next: add a `pogo)` case to `build-q56.sh` (see wf/pogo/NEXT.md run A), build q57 = queue head +
  pencharge + pogo, run `wf_pogo` (before any suspend part), send `$X/pogo/` back.
- Agents that were still working when the limit hit (they may have been stopped; resume each with SendMessage to
  its id and "continue and deliver"): wake a6be96dffe3eab71a, deepsleep a78a7b8bcac860a75, apps
  a15f21638a769c7c1, audit a9cfcdbd7afd6ab6e, pkg017 a93f7eb7566f701cc, install a68073ae3baaf9f4b, pencharge
  a410fb5800fadd638 (second round). Their folders: `build/wf/<name>/` (work in `work/`).
- Not committed yet: docs/INSTALL-GUIDE.md, WORKLOG entries 26-27, run 45-47 log sets, wf/pencharge, wf/pogo
  (next commit: make `mk-commit-k.py` from `mk-commit-j.py`, add the new wf folders and INSTALL-GUIDE.md).
- The user's standing order for the end: when ALL workflows are green, update the project knowledge (WORKLOG,
  STATE.md, CLAUDE.md, memory, snapshot) and make sure the repositories are pushed.
- **Run 46 finished** (kit q55, camera round 2; read after the save point): focus PASS and **fixfocus PASS**
  (motor and EEPROM with the hub idle, the fixed-focus helper); **quality PASS** (6 of 6 settled or at the gain
  limit, 30 fps, binned mode); **browser PASS** (Firefox got camera frames through the portal; both cameras
  listed). **app still CHECK**: previews / photos 0 of 2 also with the camera permission set (fuse now loaded, all
  portal names owned, camera portal present) - details in `build/area-combo-46/combo/camera/app/`; to send back
  to the camera agent (a3b3533c41c6d6b08). Tablet back in Android.

### 2026-10-02 - entry 28: HAND-OVER POINT (user: "save everything because im changing models")

- Nothing is running: no kit run, no build; the seven agents that were still working were stopped at the usage
  limit (partial work kept in their folders). Tablet in Android.
- Written for the next model: **`HANDOVER.md`** (orders in force, exact state, every workflow with its next
  action and agent id, the method, the prompt template, lessons, the first ten minutes), **`docs/WORKFLOW-BRIEF-5.md`**
  (the task texts of the pkg017 and install agents), CLAUDE.md (pointer + new rules), STATE.md status block,
  memory resume block.
- State of the workflow folders at the hand-over (`bash build/an/wf-status.sh`): camera, pencharge, pogo,
  deepsleep have REPORT + NEXT + tablet.sh; wake has tablet.sh + kernel candidate, no documents yet; apps has
  tablet.sh + package lists; audit has its table, tool and fix candidates 01-10+; pkg017 has its generator and
  merged files, tests unfinished; install has only scratch work.
- Open results to act on first: run 46's Camera app CHECK (to the camera agent), run 47's two pencharge checks,
  pogo run A (needs kernel q57), deepsleep (read NEXT.md, run).
- Next WORKLOG entry: 29.
- Hand-over commit: iceland-mainline **81cca68** (403 files: runs 45-47, results part J, HANDOVER.md, INSTALL-GUIDE.md,
  briefs 4 / 5, pencharge / pogo / deepsleep deliverables, tools; no private names). Matrix (`matrix-c2j.py`):
  **55 working / 9 in progress / 10 not started / 2 not planned** (pen charging moved to "in progress"); page v32.
  All three repositories level with their remotes. Snapshot refreshed (`save-project*.sh`, new
  `save-project-wf.sh`: `workflows/` = public parts of every workflow, 270 files; privacy scan clean).

### 2026-10-02 - entry 29: resumed after the model change (Opus 5.5); all seven agents running again; runs 48 + q57

- Idle check at 10:10: no pipeline process, src clean on `iceland`, queue c52d6ee, docs fe9a448, 1 device (Android,
  battery 86 %). Stale wait of run 30 (old background shell) stopped.
- The old agent ids still resume with SendMessage: camera (run 46 app result + three questions: why Snapshot's
  stream stays suspended while Firefox's runs, a package-side format fix, fuse at the start + GStreamer debug),
  pencharge (run 47 resent + three questions: the empty pin reader / safe line state after unbind, "the IC reads
  5017 mV", over-voltage 12000 mV vs stock DT 9000), wake, apps, audit (continue, REPORT / NEXT), pkg017 (finish,
  no collision with the camera fragment, fuse modules-load in one place), install (continue; self-check script for
  the forbidden fastboot words).
- **Run 48** (kit q55 = queue head; deepsleep run 1, steps base bind force quiet long, `gen-combo-48.py`): setup
  without `qcom_iris` (baseline = the session without extra drivers), the agent's debug module
  `qcom_lpm_dbg.ko` (vermagic q55; only stock's own AOP debug requests, reads the rpmh-stats and stock's vx log
  region), AUTOREBOOT_AT 2800, runner -Wait 2500. Writes reviewed: RTC alarms, /sys/power/state freeze,
  pm_debug_messages, an ftrace instance, modprobe of missing drivers, state_synced (RAM boot only), sensor
  service stop / start, Bluetooth rfkill (restored). No charger write. Started 10:2x in the background.
- **Kernel q57** = queue head + pencharge (3 patchers, unchanged) + pogo (`pogo-kernel.py`): dry-applied together
  on a throw-away worktree (`an/try-q57.sh`: all four ok); `build-q56.sh` has a `pogo)` case now
  (`--enable KEYBOARD_ONEPLUS_POGO`). Build started: `TAG=q57 WF="pencharge pogo" bash build-q56.sh`.
- Next: run 49 on q57 = pogo run A (no keyboard) + pencharge (rerun once the agent delivers round 2; rebuild as
  q58 if the driver changes).

### 2026-10-02 - entry 30: run 48 (deepsleep: NOT-DEEP), q57 + q58 built, audit and camera deliveries, run 49 started

- **Run 48** (q55, deepsleep run 1): **NOT-DEEP**, levels base 0 / bind 0 / force - / quiet 0 / long 0; every
  suspend worked (4 of 4, woken by the RTC alarm, display and USB back, 0 hard kernel lines). bind loaded 4 drivers,
  14 of 14 RPMh providers synced, boot-floor votes 45 -> 0. After bind only `xo.lvl=3` and the clock buffer
  `rfclka1` stay voted by Linux while asleep; the AOP monitor names SOCCP as the blocker; rough draw asleep 0.6 W
  on the PC port. 534 interrupts of `qcom_geni_serial_uart1` while frozen. The kit boots with
  `clk_ignore_unused pd_ignore_unused regulator_ignore_unused`. Sent to the deepsleep agent with four questions
  (who holds xo / rfclka1, are the kit flags the reason and is booting without them safe, SOCCP = the PC port?,
  the UART interrupts). Log set `build/area-combo-48/combo/deepsleep/`.
- **Kernel q57** built (queue head + pencharge + pogo): 7.3.0-rc4-iceland-00228-g1ea3e1b70e50, 0 warnings,
  `KEYBOARD_ONEPLUS_POGO=y`, `CHARGER_MT5806_PEN=m`.
- **Audit agent delivered** (`wf/audit/`): 1,249 values compared (934 device-tree rows, 268 amplifier settings, 47 by
  hand); battery / charger, thermal trips, clocks / OPP: nothing above stock. 13 fixes: 01 UFS PHY L4G 0.912 V,
  02 panel I/O L12B 1.896 V, 03 BOB1 3.296 V (mic bias), 04 L1D / L3D always on (held for deepsleep), 05 second
  backlight IC registers as stock's driver writes, 06 144 Hz front porch 64, 07 two amplifier registers, 08 all of
  stock's secure pins reserved, 09 four pin drives / pulls, 10 GPIO 162 not driven, 11 / 12 USB 2 repeater tuning
  (kit B), 13 panel reset pulse. `check-all.sh` PASS on the queue head (any order, DT compiles).
- **Kernel q58** built = queue head + audit kit A (01 02 03 05 06 07 08 09 10 13): 0 warnings.
- **Camera agent delivered round 3**: the Camera app's stream failed because libcamera's software ISP put four
  1920x1080 RGBA buffers (8.3 MB each) into the 32 MiB CMA heap; the 4th failed ("cma: reserved: alloc failed,
  req-size: 2025 pages") and PipeWire reported it as "Format negotiation failed". Fix in the package:
  `71-iceland-dma-heap.rules` (CMA heaps root-only, libcamera falls back to the system heap); in
  `cand/wp4-apps/pkg-017-camera.py`. The app step now proves the failure (H-A) and the fix (B) in one boot.
- **Run 49** (q57) started: audit baseline (no fix expected), pogo run A, pencharge (round-1 test), pkg2, rotpkg
  start, cam-d (camera run C). Run 50 (q58: audit kit A, pkg2 + rotpkg + cam-c, wifi, micdiag) is generated and
  follows.

### 2026-10-02 - entry 31: run 49 (pogo PASS, pencharge PASS, Camera app works), pen charger queued 0090-0093

- **Run 49** (q57 = queue head + pencharge + pogo): **pogo run A PASS** (UART 921600, empty connector, supply off,
  5 of 5 frames echoed through the transmit gate); **pencharge v2 PASS** (unbind leaves the transmitter off:
  power line low, tx-off high, in gpio state and PMIC pads; hBoost switched on by the 7 V request, IC VIN 5005 mV,
  the set-point register is in no stock source: only the owner's pen run says whether the boost follows);
  **Camera app works** (previews alive on both cameras, 2 of 2 photos, 6.4 s video) with the DMA-heap rule;
  run 49's journal shows the cause (without the rule WirePlumber uses /dev/dma_heap/reserved, with it
  "Permission denied" then /dev/dma_heap/system); the no-rule part did not open the camera (Snapshot waits in the
  overview), the camera agent made the step decisive in one boot (N then R). Audit baseline (read only): the
  backlight / amplifier readers found nothing (I2C bus numbers change per boot) - fixed by the agent (find by
  compatible); L4G / L12B already at stock's voltage through the boot vote, BOB1 3032 mV (stock 3296).
- **Queue 0090-0093 pushed** (iceland-linux **db4c7cb**): pmic_glink hBoost client, MT5806 binding + vendor prefix,
  driver, board nodes; `CONFIG_CHARGER_MT5806_PEN=m` (distro-neutral + required). Tree = q56 (verified from the
  local base, `queue-0090.sh` with `PEN_ONLY=1 TAG=q56`). The first attempt with pogo stopped at the tree check:
  the pogo agent changed its driver at 10:35 between the dry run and the real run (nothing was queued). Pogo goes in
  after a retest. `build-q56.sh` now expects the head "add the pen charger"; pogo, wake and audit kit A still apply
  on it (`an/try-head.sh`).
- **Wake agent delivered** (charger plug / unplug wakes as stock: `battmgr-plug-wake.py`; logind drop-in + guard
  "sleep only" for the package; volume keys and lid-on-charger are owner decisions). Kernel **q59** = old head +
  pencharge + pogo + wake built (0 warnings); **run 51** (pkg2, rotpkg start, wake last; AUTOREBOOT_AT 2800) running.
  Wake's package pieces were handed to the pkg017 agent.
- Next: run 51 result -> wake agent; run 50 (q58, audit kit A, with the fixed reader); then one combined kernel on
  the new head (pogo as changed + wake + audit kit A) for the final run of those three + the camera's decisive app
  step, and queue what passes.

### 2026-10-02 - entry 32: run 50 (audit kit A: 8 of 10 in effect), wake run A green, deepsleep round 2, run 53

- **Run 51** (q59, wake run A): **PASS** (warning lid-candidate-setting = a test mistake: the RAM user has no
  password, so GNOME blanks the screen instead of marking the session locked; test fixed). Every sleep ended by the
  RTC alarm (191 s asleep in total); the charger channel answered inside the sleep without waking it; pogo-detect
  armed and never the wake source. The wake kernel candidate is ready to queue (plug / unplug wake itself = the
  owner's windows).
- **Run 50** (q58 = queue head 0089 + audit kit A): audit **FAIL** on two items only: in effect 01 02 05 06 07 08 09
  13, partial 03 (BOB1 not at 3296 mV) and 10 (GPIO 162). Both backlight ICs now b3/eb/77/76/f8 as stock; amplifier
  boost f0 / d7 (none above stock: `07 --dcvos` not needed); panel and UFS 0 error lines; camera quality PASS with
  fix 09's bus drive; Wi-Fi scans as before (the regulatory warnings are in runs 41-49 too); micdiag 13 of 13
  suspends (one recording 1.7 s instead of 4 s: that step started 1.4 s late after a resume, no error). Sent to the
  audit agent.
- **Deepsleep round 2 delivered**: run 48's blocker is the Wi-Fi chip's PCIe link that stays up in s2idle (the root
  port is wake-enabled through its WAKE# GPIO) and keeps a DDR bandwidth vote; the kit flags hold none of the
  remaining votes and must stay (the boot screen runs on simpledrm until the display driver binds). Round 2 steps
  bind dispoff ref rpwake nowifi nobt long (rpwake = root port wakeup disabled at run time); kernel candidate
  `cand/pcie/pci-host-common-port-wake.py`. **Run 53** (q55, `gen-combo-53.py`) started.
- Apps workflow delivered (7 slices, 1.3 GB); asked to split into runs of at most 10 minutes and to apply after
  pkg017 and the camera fragment without a version bump.
- Next: run 52 = kernel q60 (head 0093 + pogo fixed driver + wake + final audit kit A; `gen-combo-52.py`) once the
  audit agent has finished 03 / 10; then queue pogo, wake and audit kit A.

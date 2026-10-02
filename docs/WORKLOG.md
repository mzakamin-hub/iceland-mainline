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

### 2026-10-02 - entry 33: commit L, run 53 (deepsleep round 2: still level 0), q60, runs 52 / 54-56 started

- **Commit L** pushed: iceland-mainline **e8f6ee3** (runs 48-51, results part K, entries 29-32, matrix
  55 / 13 / 6 / 2 with `matrix-c2k.py`, wake / audit / apps deliverables; the audit's full device-tree table and
  generated `.xml` files stay local: the blob guard refuses every `.xml`). Matrix page v33.
- **Audit 03 / 10 revised**: BOB1's regulator table has only 3.000 V + n x 32 mV, so 3.296 V became 3.320 V in run 50;
  the floor is now 3288000 (8 mV below stock, never above). GPIO 162 gets stock's run-time state (input,
  pull-down, 2 mA). New judged finding: BOB2 runs at 3.000 V (stock 2.720 V; mainline's table has no lower step;
  inside stock's range).
- **Run 53** (q55, deepsleep round 2): still level 0 in every step; the Wi-Fi chip's PCIe link stays up even with
  the root port's wakeup off AND the endpoint unbound; xo held by disp_cc_mdss_ahb_clk and the three gcc_pcie_0
  clocks; the AOP monitor now names AUDIO in every line. FAIL only on the clean-up: the Wi-Fi interface was gone
  at the end (RAM only). Sent back with four questions (pcie-qcom suspend path and its ICC vote, the audio blocker,
  the display AHB clock, the clean-up).
- **Kernel q60** = head 0093 + pogo (fixed driver, md5 d2f4e4ed) + wake (battmgr-plug-wake, md5 9a148004) + audit
  kit A (revised 03 / 10), audit applied last: 0 warnings. The three agents froze their `cand/`.
- `queue-0094.sh` written and dry-run: 15 commits (pogo 0094-0097, wake 0098, audit 0099-0108), tree = q60.
- **Runs 52, 54, 55, 56** started as one chain (`run-chain.sh 52 54 55 56`): 52 = the combined confirmation (audit
  kit A, pogo run A with the replay check, pkg2 + rotpkg start + the camera's decisive app step, wake last;
  AUTOREBOOT_AT 2800); 54 / 55 / 56 = apps runs A (core help), B (store media browser), C (print office + guard),
  each one call of at most 570 s (`gen-combo-54.py`).

### 2026-10-02 - entry 34: run 52 all green -> queue 0094-0108 (pogo, plug wake, audit kit A); pkg017 delivered

- **Run 52** (q60 = head 0093 + pogo + wake + audit kit A): **audit PASS** (all ten in effect, partial none,
  panel / UFS 0 errors, 0 warnings; BOB1 3288 mV, GPIO 162 input pull-down); **pogo PASS**
  `[ok:...,selftest,replay-stale,stable]` (5 detect interrupts, 5 judged stale); **camera app decisive**: without
  the DMA-heap rule the stream fails on CMA (1 allocation failure, kernel "req-size: 2025 pages", "Could not start
  camerabin"), with it previews / 2 photos / video; **wake PASS, no warnings** (every sleep by the RTC alarm, lid
  with "GNOME locked: yes (shield up, screen off)", pkey).
- **Queue 0094-0108 pushed** (iceland-linux **acdecb4**, `queue-0094.sh`, tree = q60, verified from the local base):
  pogo 0094-0097, the plug wake 0098, audit kit A 0099-0108 (`commit-all.py`), `CONFIG_KEYBOARD_ONEPLUS_POGO=y`.
  Queue head bfb2d3731; `build-q56.sh` expects "stock's reset sequence" now.
- **pkg017 delivered** iceland-device 0.17 (one guard with chargelimit + charging + thermal cap + wake's
  sleep-only lid block, the thermal daemon without the private model, the logind drop-in; `check.sh` 62 checks,
  0 FAIL). Reviewed: every safety constant and the FCC / VBATDET tables byte-identical to 0.16; the cap is
  min(stock table, cool-down 1200 mA, thermal cap) - only lowers. Order of the three patchers: camera, pkg-017,
  apps. **Run 57** generated (`gen-combo-57.py`: package from a patched copy `build/pkg017-tree`, fuse in setup,
  0.17 globs; pkg2, rotpkg start, pkg017) - runs after the apps chain.

### 2026-10-02 - entry 35: apps runs 54-56, audit kit B (q61), deepsleep round 3 (q62), runs 57-59 started

- **Apps runs** (q55, one call each, all ALL DONE well inside 10 minutes): **54 = A** core + help (57 packages,
  +171 MiB, 211 s): 25 of 26 apps showed a window, `gnome-connections` FAIL; on-screen keyboard comes up on a tap;
  gnome-shell never restarted; 0 core dumps. **55 = B** store + media + browser (143 s): 3 of 3 windows. **56 = C**
  print + office (90 s): guard PASS (dnf reads the excludes, 9 of 9 forbidden installs refused, simulated full
  upgrade 84 packages with nothing forbidden, release 45 refused). Sent to the apps agent (Connections, the
  details of B / C).
- **Audit kit B** (11 12, USB 2 repeater tuning) checked on the new head; the ten queued patchers moved to
  `cand/queued/`, waivers cleaned (966 rows, 0 open). Kernel **q61** = head 0108 + kit B (0 warnings); **run 58**
  generated (`gen-combo-58.py`, setup + audit only: if the link breaks, the kit's auto reboot brings Android back).
- **Deepsleep round 3** delivered: the Wi-Fi port never reaches D3 because pcie-qcom leaves the slot's Hot-Plug
  Capable bit set while CONFIG_HOTPLUG_PCI_PCIE is off (pci_bridge_d3_possible refuses), so the link and its DDR vote
  stay; candidate 5 `pcie-qcom-slot-hpc.py` clears the bit only without the hotplug driver; candidate 6
  `dsi-phy-iface-runtime.py` stops the two DSI PHYs keeping the display AHB clock (and so the crystal vote)
  prepared; round-2 candidate 4 withdrawn; the AUDIO blocker gets a new record + a `noaudio` step. Kernel **q62** =
  head 0108 + 5 + 6 (0 warnings, `deepsleep)` case in `build-q56.sh`), debug module rebuilt for q62; **run 59**
  generated.
- Camera: the WirePlumber rule hiding the 16 raw CAMSS nodes never matched (property only after open); now matched
  by the udev bus path; run 57's package copy regenerated with it.
- **Runs 57 (0.17 package), 58 (audit kit B), 59 (deepsleep round 3)** started as one chain at about 11:40.

### 2026-10-02 - entry 36: runs 57-59, queue 0109-0112 (audit complete), INSTALL-PLAN updated

- **Run 57** (q60, iceland-device 0.17 from a patched copy of the repo tree): 23 of 25 checks; FAIL on two
  test-side points (logind's 4th cover field read empty, so the guard took the careful side and blocked the lid
  switch too; the backlight changed by GNOME's automatic brightness during the part). Everything that protects the
  battery passed: limit 80 / 85, the guard's sleep block on the cable, the thermal cap lowering the current (400 mA
  live), suspend. Sent back to pkg017.
- **Run 58** (q61, audit kit B): **PASS**, repeater 0e/07/04/02/03 as stock, link high-speed, the whole run over USB.
  **Queued 0109-0112** (iceland-linux **0f9a117**, `queue-0109.sh`, tree = q61). Fix 04 dropped (stock votes L1D /
  L3D off in suspend, mainline cannot express "on awake, off asleep"; always-on would hold more than stock). The
  audit's kernel work is complete. `build-q56.sh` expects the head "USB 2 repeater slew rate from stock".
- **Run 59** (q62, deepsleep round 3 = candidates 5 + 6): **the PCIe link goes down and the SoC reaches CX
  collapse** for the first time (cxsd +1); the long sleep was ended after 0.4 s by the Lid interrupt (irq 238).
  Sent to the deepsleep agent and the wake agent (hall sensor supply L1B in CX collapse).
- **Apps run D** generated as run 60 (Connections through gapplication, fwupd plug-ins after a restart, the pin's
  opt-out).
- **Install workflow delivered** the PC-side tooling (pieces a-f all checked on the PC; findings: 4 KiB storage, the
  official image would not boot, root growth needs a GPT, the install U-Boot is a separate build, SELinux off and
  no compressed firmware in kernel-iceland, EFI programs could write every LUN, GRUB's save_env, boot_b AVB-chained,
  the Bluetooth address not in persist). No rehearsal boot before the written proof that the rehearsal cannot touch
  the storage (asked; gate G13).
- User: "update docs/INSTALL-PLAN.md with new findings and suggestions for an unbrickable restorable permanent
  install" -> done: gates G7 / G8 closed, new gates G12-G14, the new findings in sections 2, 3, 5, 6, the run order
  in section 4, decisions 5-10, the work list with states, new section 11 (unbrickable / restorable L0-L5 with a
  day-0 snapshot and home copies / permanent). The next commit script must copy `docs/INSTALL-PLAN.md` from the
  project folder (commit L did not).
- User: "update feature matrix" -> `matrix-c2l.py` (runs 52-59): **56 working / 13 in progress / 5 not started /
  2 not planned**; Stock-values audit -> working (0099-0112 queued); Full GNOME app set -> in progress; Pogo, Wake,
  Deep sleep, Cameras, Firmware extractor, Fedora installed: texts updated. **Commit M** pushed (iceland-mainline
  **424f289**: runs 52-59, results part L, the updated INSTALL-PLAN.md, pkg017 / install public parts). Page v34.

### 2026-10-02 - entry 37: apps run D, iceland-device 0.17 committed, install G13, deepsleep round 4 (CX 98 %)

- **Run 60** (apps run D): GNOME Connections opens (the earlier failure was the test's launcher; 33 of 33 apps over
  runs A-D); fwupd: the 17 plug-ins off after a restart, 0 of 13 devices left (the UFS storage was listed as
  updatable before); the release pin holds and an empty file in /etc/dnf/repos.override.d lifts it. Apps workflow:
  automated part done; the owner's 30-minute look remains.
- **Run 61** (q61 = queue head 0112, iceland-device 0.17 rerun after the test fixes): **pkg017 PASS, 28 checks**
  (guard + thermal daemon active, limit 80 / 85, sleep block on the cable, thermal cap lowers the current, cover
  drop-in in effect, suspend). The 600 mA cap is the kernel's SDP limit (stock's). Guard tables re-checked
  byte-identical to 0.16. **Committed** iceland-mainline **4bd8e0e** "iceland-device 0.17 ..." (`commit-pkg017.sh`:
  check.sh ALL PASS first, the three patchers on the real tree, tree = the tested copy, privacy guards).
- **Install G13 answered**: a real gap found - the rehearsal would have booted the install U-Boot, which maps
  userdata first (read only on today's tablet, nothing would have been written, but not acceptable). Now every
  rehearsal boots `u-boot-iceland-rehearsal.img`: no SCSI / UFS in the build, env without the userdata lines,
  bootcmd `fastboot usb 0`; the EFI write guard stays; the initramfs sets every UFS device read-only before
  anything opens it and accepts only /dev/nbd* as carrier; self-check rules A-C, P. The relay accepts only
  172.16.42.1 (test_relay 8 / 8; rehearse.ps1 starts / stops it). INSTALL-PC-CHECKS 9 PASS.
- **Run 62** (q63 = head 0112 + deepsleep 5 + 6 v2 + wake's L1B always-on): **CX collapse 98 % of a 150 s sleep**
  (cxsd +41), PCIe link down in every sleep, Wi-Fi back, display AHB clock released, rough draw asleep ~0.1 W; aosd
  still +0. The Lid interrupt STILL fired once per sleep with L1B held: the supply is not the cause. Sent to the
  deepsleep and wake agents (GPIO 98 / PDC in CX collapse).
- User asked: "after final install will the kernel be upgradable?" -> yes: kernel-iceland from our repository,
  RAM-tested first, installed by dnf / GNOME Software, trial boot, three kept, never touches boot_b; caveats:
  Fedora's kernels stay blocked, each new Linux release means a rebase of the queue, the private camera module per
  kernel version.
- **Run 63** (q61, install R0 facts, without the network disk) started.

### 2026-10-02 - entry 38: queue 0113-0116 (deep sleep), run 64, K1 kernel q65 + run 65; readiness estimate

- **Run 64** (q64 = head 0112 + deepsleep 5 + 6 v2 + L1B always-on + the wake workflow's gpio-keys lid patch):
  PARTIAL cxsd - CX collapse 98 % of a 150 s sleep, every sleep ended by the RTC alarm with the cover open and the lid
  wake on, PCIe link down, Wi-Fi / display back, 0 hard kernel lines. The Lid edge latched by the PDC at the first CX
  exit (GPIO 98 idles high with the cover open, only the rising edge is armed) is the cause; L1B was not.
  **Queued 0113-0116** (iceland-linux **bdab8af**, `queue-0113.sh`, tree = q64): PCI qcom hot-plug slot, DSI PHY iface
  clock, hall sensor supply, gpio-keys. Head 685ce87b2; `build-q56.sh` expects "do not arm a switch that is already
  released". AOSS sleep: the AOP names APPS / SP / AOP / COMPUTE (the secure processor and the CDSP are never started).
- Wake workflow: done until the owner's windows (NEXT.md section I, ~15 minutes, kit = queue head + 0.17).
- Install: K1 is safe for the kits (their RAM roots carry no SELinux policy: "SELinux: Initializing" only, every check
  allowed, permissive by DEVELOP). `pkg-install.py` fixed for the committed 0.17 (%preun of the trial units), 16 PASS.
  Kernel **q65** = queue head 0116 + install.config (`build-q65.sh`, merge_config): 0 warnings, CONFIG_LSM with
  selinux, FW_LOADER_COMPRESS XZ / ZSTD. **Run 65** (= run 45's regression on the head + the K1 check) started.
- User: "does the new update regarding the full install means i will need to use the laptop as network relay and
  there's no way to install it on tablet?" -> no: the relay / network disk is only the rehearsal before the install;
  after the two writes Fedora runs from the tablet's own storage and Wi-Fi; the PC is needed for the writes, for new
  kernel versions (until a published repository) and for rescue.
- User: "update feature matrix with everything being commited and update the status, and basis everything calculate
  the percentage of having this running successfully on the tablet fully instaled with dual boot android (use
  everything since the start of the project)" -> `matrix-c2n.py` (deep sleep, wake, lid switch, kernel package and
  dual-boot rows; the page subtitle and the FEATURES.md status line rewritten). **The estimate and its model:**
  - Project so far (since 28 Sep): 138 SM8850 base patches + 116 Pad 4 patches, 113 kit runs, 76 test kernels,
    201 docs commits; matrix 57 working / 12 in progress / 5 not started / 2 not planned of 76.
  - Progress = 50 % features + 30 % single install path + 20 % dual-boot specifics:
    - features: 74 rows in scope, working 1, in progress 0.5, not started 0 -> (57 + 6) / 74 = 85 % -> 42.6 points;
    - single install path: running from RAM proven 100 % (w .25), packaging 80 % (kernel rpm 12 / 12, 0.17
      committed, 0.18 checked on the PC; w .20), rehearsal tooling 70 % (built, PC-checked, G13 closed; w .20),
      tablet rehearsal 5 % (R0 only; w .20), the writes 0 % (w .15) -> 56 % -> 16.8 points;
    - dual boot: U-Boot "fedora" partition support + the recovery helper exist; the partition change of LUN 0, its
      rehearsal and the OTA handling are not planned in detail -> 20 % -> 4 points;
    - total about 63 %.
  - Chance that it works as planned (the risks, each from what is proven so far): the install chain on the tablet
    (U-Boot from userdata on 4 KiB storage, shim fallback, GRUB, SELinux denials; all software, the rehearsal shows
    each) 0.90; ABL starting an unsigned boot / recovery image in the unlocked state 0.88; the partition change for
    the dual boot (never done here; fastboot stays reachable, backups exist) 0.85; Android after its data reset and
    smaller userdata 0.95 -> Fedora only about 0.90 x 0.88 = 0.79 (four in five); with dual boot about 0.64 (two in
    three). Not counted as failure: a higher sleep drain than stock (CX collapse reached, AOSS open), autofocus, the
    owner's hand tests still to do.

### 2026-10-02 - entry 39: run 65 (K1 regression PASS, committed), run 66 (CDSP stop loses CX collapse), hwinv workflow, battery estimate

- **Run 65** (q65 = queue head 0116 + install.config): charging, chargelimit, gpucool 20 / 20, stuck, bcl PASS; thermal
  6 / 7 (the restore check saw only the screen brightness changed by GNOME's idle dim; CPU / GPU limits equal). K1
  check: "SELinux: Initializing" 1, policy lines 0, avc 0, lsm list has selinux. **Committed** iceland-linux
  **15ff5a8** "configs: SELinux as the default LSM, compressed firmware (install plan K1)" (`commit-k1.sh`).
  The gsd-power "dim kbd backlight" / "max > min" journal lines are NOT from the pogo driver (they are in every run
  since run 15; the pogo agent checked) - known user-space noise.
- **Run 66** (q64 tree, deepsleep round 6 with the CDSP started from cdsp-fw.tar): with the CDSP running CX collapse
  stays (97 %); after a clean CDSP stop CX collapse is LOST for the rest of the session (cdspoff / long at level 0).
  Sent to the deepsleep agent (what the stop leaves voted; matters for the NPU). AOSS sleep: out of reach on mainline
  (the secure processor has no mainline driver; AOP names it) - the row's proof becomes CX collapse + the night.
- User: "add another workflow to list all hardware that has no drivers or not working on the tablet ... run dmsg or any
  tools ... also let me know an estimate of the battery life on fedora" -> new agent **hwinv** (wf/hwinv/: INVENTORY.md
  from stock vs mainline, a read-only tablet test of unbound / deferred / failed / undescribed devices, REPORT, NEXT);
  the deepsleep agent gets a `wf_powerprofile` test (draw per state: screen on at 30 / 50 / 100 % and 60 / 120 Hz,
  video, CPU load, screen off, s2idle). **First estimate** from the data in hand: battery 13786 mAh full (design
  13380, 5 cycles, 4.5 V cell) = about 52 Wh; measured on the PC port (input 2.47 W x 0.9 + battery power): screen on
  at 50 % brightness with the GNOME session and tests about 6.5 W (run 65), screen off awake about 2.3 W (run 65
  chargelimit baseline), heavy (package build) about 8.9 W (run 61), asleep at CX collapse 0.1-0.5 W (+- 0.3 W, runs
  62 / 64). Battery life: light use 8-10 h, heavy 5-6 h, screen off awake about 22 h, standby roughly 4-20 days (the
  night unplugged decides).

### 2026-10-02 - entry 40: install PC builds, run 67 (power profile noisy, candidate 7 fails), run 68 (install B1 / B2)

- Deepsleep round 6 answer: after a CDSP stop the CDSP's own voter (12) keeps CX level 3 / DDR; AOSS sleep is out of
  reach on mainline (COMPUTE never left the AOP list in any state). Important: iceland-device's iceland-npu-off.service
  stops the CDSP a few seconds into every boot = exactly that start-then-stop -> an installed system would lose CX
  collapse. Candidate 7 (DDR vote around the stop) and a package fallback (keep the CDSP running idle).
- User: "will candidate 7 give better battery life then package fallback for cx collapse" -> if it works, slightly
  (the idle CDSP sits in its own sleep 117 % of the time; retention leakage only, milliwatts), below what the PC-port
  gauge can resolve; the night decides; recommendation: test 7, else the fallback.
- **Install PC builds** (`wf/install/next-k2p1u1.sh`): 5 PASS - K2 kernel-iceland rpm of q65 (22 MB, 13 checks), K3 the
  same tree with release ...g685ce87b2aa2.1 (update rehearsal), P1 iceland-pkg-0.18.tgz (16 checks; the rpm is built on
  the tablet), U1 install + rehearsal U-Boot (29 checks), tablet-in (14 files). `rehearsal-pc.sh prepare`: stage0 =
  the official image re-laid for 4 KiB (13.7 GB body, 4.4 GB on disk, virtual size = userdata), 419 ESP files and
  /boot / root identical.
- **Kernel q66** = head 0116 + candidate 7 (`build-q56.sh` deepsleep case now = candidate 7). **Run 67** (setup with
  qcom_iris): power profile DONE but inconsistent (sd up to 1.8 W; screen off 4.9 W > video 2.9 W; 120 Hz 7.3 W vs
  144 Hz 3.8 W; GNOME's idle dim changed the brightness inside states). Steady states only: idle 30 % 60 Hz 2.34 W,
  idle 50 % 144 Hz 3.85 W, video 2.89 W; battery energy 53.8-56.9 Wh. Deepsleep round 7: candidate 7 does NOT keep CX
  collapse after the stop (cdspoff L0), a restart brings it back (cdspre L1, long 98 %). Both sent back to the
  deepsleep agent (fix the profile method; drop 7 if no other stock step is found -> the package fallback).
- **Run 68** (q65, install: devrpm 0.18 + build1 + build2 on the network disk) started; PC side: `rehearsal-pc.sh serve
  stage0 build` (WSL 127.0.0.1:10810) + `tcp-relay.py --listen=auto --allow=172.16.42.1` (Windows :10809). After the
  run: stop the relay, look for REFUSED in C:\platform-tools\tcp-relay.log, `rehearsal-pc.sh stop`.

### 2026-10-02 - entry 41: hardware inventory delivered, install B1 failed on an NBD timeout, quick-wins workflow

- **hwinv** delivered (wf/hwinv/: INVENTORY.md 109 blocks: 52 working, 13 bound not proven, 4 described not bound,
  2 disabled in our DT, 12 not described, 12 no mainline driver, 13 not on this tablet; read-only tablet test,
  `cand/gen-combo-hwinv.py`). Run 70 (setup, hwinv, cam-a, hwinv2) generated. Top finding: boot votes held by
  fw_devlink because the GPU's GMU node never gets a driver -> install agent: `CONFIG_FW_DEVLINK_SYNC_STATE_TIMEOUT=y`
  (kit test first); the late drivers (QCE, Iris, CAMSS, qcom_stats) should load by udev coldplug on an installed
  system; new `syncstate` check in accept.sh (F17).
- **Run 68** (install): devrpm PASS (iceland-device 0.18 built on the tablet, 87 files); build1 FAIL - the tablet's
  nbd client timed out ~10.5 min in ("Connection timed out ... Dead connection"), writes failed, btrfs on the network
  disk went read-only; build2 refused correctly ("build1 is not complete"). nbd read 31.5 MB/s (F4 ok). Relay: 0
  REFUSED. The tablet's storage untouched. Sent to the install agent (server write path, client timeout /
  connections, slow-request log). Server and relay stopped.
- **Run 69** (q65, power profile v2: 60 s settle + 20 s counted, charge counter, idle dim off) started.
- User: "start combined workflows for items from 1 till 9, keep iterating without asking for my confirmation or
  testing for items 8,9 since i will test them later" -> new agent **quickwins** (wf/quickwins/): 1 fw_devlink
  sync_state timeout, 2 bwmon5, 3 PMIH0108 temp alarm lite, 4 autoload of QCE / CAMSS / qcom_stats (udev coldplug),
  5 camera EEPROMs read-only, 6 charger ulog, 7 IMEM (CONFIG_SRAM), 8 DisplayPort (bind only; the owner tests later),
  9 USB audio offload + DP audio (bind only; owner later). Iterate without asking the owner.
- **Run 69** (q65, power profile v2): consistent (sd <= 0.07 W except the CPU heat-up; repeat of the first state
  within 1 %; the charge counter agrees within 5 %): idle screen on 50 % 60 Hz **3.37 W** (16.0-16.8 h), 120 Hz
  **4.08 W** (13.2-13.9 h), 1080p H.264 hardware video **3.58 W** (15.0-15.8 h), all cores busy **8.14 W**
  (6.6-7.0 h), screen off awake **0.64 W** (84-88 h); light use mix 3.85 W = 14.0-14.7 h; battery 53.8-56.7 Wh.
  Standby asleep not measured on the PC port (below 0.64 W; the night decides). The only FAIL: the brightness
  put-back (1256 instead of 2047 after the last state) - sent back. **Run 70** (hwinv) started.

### 2026-10-02 - entry 42: feature matrix with the battery life and the recomputed completion estimate

- User: "update feature matrix with the battery life numbers and our current percentage of completion" ->
  `matrix-c2o.py`: rows Battery time estimate (the measured table of run 69), 60 Hz on battery / CDSP off (120 Hz
  +0.7 W; never stop the CDSP), NPU (idle CDSP sleeps by itself; the stop bug), Deep-sleep proof (CX collapse 98 %,
  AOSS out of reach on mainline, screen off awake 0.64 W); page subtitle and FEATURES.md status line with the
  battery life and the estimate. Counts since 28 Sep: 118 kit runs, 77 test kernels.
- **Completion estimate recomputed: about 65 %** (entry 38's model, same weights):
  - features 50 %: unchanged 57 / 12 / 5 / 2 -> (57 + 6) / 74 = 85 % -> 42.6 points;
  - single install path 30 %: running from RAM 100 % (w .25); packaging 90 % (kernel-iceland rpm 13 / 13 + the K3
    version, iceland-device 0.18 built on the tablet, K1 config queued; w .20); rehearsal tooling 85 % (both U-Boot
    builds, stage0 prepared, the tablet-only relay, the network disk reads 31.5 MB/s; the write path timed out once;
    w .20); tablet rehearsal 10 % (R0 + devrpm; B1 failed; w .20); writes 0 % (w .15) -> 62 % -> 18.6 points;
  - dual boot 20 %: unchanged 20 % -> 4 points;
  - total 65.2 % -> about 65 %. Chances unchanged: Fedora only about 0.79, with dual boot about 0.64 (the network-disk
    timeout is a tooling fault of the rehearsal, not a risk of the install itself).
- **Run 70** (q65, hwinv): both passes complete - 464 bus devices, 82 unbound; modules built but not loaded 8 (dw9719,
  fastrpc, mt5806_pen_charger, phy_qcom_mipi_csi2, qce_core, qcom_camss, qcom_stats, rpmsg_ctrl); sync_state held by 5
  unbound consumers (crypto, GMU, ISP, two PHYs); the second pass after cam-a showed the same numbers (cam-a to be
  checked). Sent to the hwinv agent.
- User: "also make another agent to add 11 pmic power telemetry" -> new agent **telemetry** (wf/telemetry/): a
  read-only mainline driver for the PMK8850 per-rail power telemetry (hwmon or IIO), binding, DT node, a tablet test
  comparing its total with the battery-side figure; writes only to the telemetry block with stock's values (charging
  safety first). Iterate without asking the owner.
- User: "also start agent for item 10 npu cooling" -> new agent **npucool** (wf/npucool/): the QMI cooling series from
  the lists rebased on the queue head (credit kept), the CDSP's cooling devices + stock's trips / maps, optional QMI TS
  sensors; tablet test starts the CDSP from cdsp-fw.tar (never stops it), steps the cooling states, emulated
  temperatures; cooling only ever limits. Iterate without asking the owner.
- User asked which unmerged patches could help -> searched the lists: our tree already has the A840 with IFPC /
  preemption, Kaanapali CAMSS / Iris / QCE / LLCC / TSENS / FastRPC; worth taking: the remoteproc QMI TMD cooling
  series v8 (9 Aug 2026; passed to npucool as its base), "hwmon: Add Qualcomm SPMI BCL driver" v2 (Jul 2026; PMH0101 /
  PMIH0108; passed to telemetry), accel/qda v2 (Aug 2026; after the NPU decision), libcamera 0.7's GPU soft ISP,
  newer versions of the Kaanapali series (USB, qcrypto, SoCCP, Iris, CAMSS, device-tree batches).
- User: "start both workflows, gpu isp check and upstream sync" -> new agents **gpuisp** (wf/gpuisp/: is the GPU ISP in
  Fedora's libcamera 0.7.1, how to switch it on, a CPU-vs-GPU capture / power test, Snapshot with it) and **upsync**
  (wf/upsync/: SYNC.md of our queue vs the newest postings / mainline, "take" candidates as patches with an apply
  script, a regression plan). Iterate without asking the owner.
- hwinv analysed run 70: 112 rows (52 working, 11 bound not proven, 1 bound not needed, 6 described not bound, 2
  disabled, 12 not described, 14 no mainline driver, 13 not on this tablet); 47 as predicted, 23 new, 5 open (camera:
  cam-a never ran - its generator did not copy wf/camera/tablet.sh, fixed; CDSP cooling). Every unbound device is
  explained (UFS W-LUNs, ADSP glink edges without client, the battery data node, ...). New part `hwload` (loads only
  allowlisted modules that earlier runs loaded). Seven more actions handed to quickwins as items 10-16: WSA / WSA2
  macros off (hold LPASS clocks; maybe the AUDIO voter), autoload of fastrpc / dw9719 / mt5806 / rpmsg_ctrl, EDAC_QCOM,
  WATCHDOG_SYSFS, the PMIH0108 pinconf double bias, no wireless supply in qcom_battmgr, the ulog channel is SOCCP.
- Install B1 failure explained: Windows' WSL localhost forwarder (wslrelay) stalled for good after ~333 MB of writes
  (reproduced on the PC without the tablet); not the tablet, the USB link or the server. Fix: the server also listens
  on WSL's own address (peers 127.0.0.1 and the Windows host only), the relay goes there (`--target=wsl:10810`),
  multi-connection server, TCP_NODELAY / keepalive, slow-request log, nbd-client -t 120 -C 2. PC load check through
  the new path: PASS (2 x 1 GiB written + read, 0 errors, 0 slow). dnf5's "superuser" line was a consequence of the
  read-only btrfs. **Run 71** (q65, install dev + B1 + B2 retry) started; server on 127.0.0.1 + 172.22.46.255:10810,
  relay -> wsl:10810, peers 172.16.42.1 only. Battery 75 %.
- **Run 71** (q65, install retry): devrpm PASS; build1 / build2 FAIL "network disk" at once - the tablet's nbd_up()
  never reached the relay (relay alive the whole run, no connection logged; nbd-client.txt empty; no nbd line in the
  tablet's dmesg; the overlay untouched). Likely the new client options (-t 120 -C 2) or a step before the client.
  Sent back to the install agent (log every step of nbd_up, fall back to one connection). Server and relay stopped.

### 2026-10-02 - entry 43: install B1 runs 71 / 72, quick wins / telemetry / NPU cooling built (runs 73-75)

- Install: run 71 failed at once (Fedora 44's nbd-client 3.27.1 segfaults on the short option `-C 2`; fixed with
  `-connections 2` + a one-connection fallback + full logging). **Run 72**: two connections worked, but build1 took
  1002 s and its own time limit disconnected the disk with writes pending (I/O errors only at the teardown; server
  slow requests 88, errors 0; one relay leg "semaphore timeout"). Cause very likely mine: kernels q68 / q69 were
  compiled in WSL during build1. **Rule: no WSL builds while a network-disk run is active.** Sent back: split build1
  (B1a / B1b with records), never disconnect with writes pending. Overlay deleted, server + relay stopped.
- Agents delivered: **quickwins** (16 items; USB audio offload not possible on mainline for this chip; check.sh 40 / 40),
  **telemetry** (PMK8850 telemetry = per-rail power / energy of 21 bucks from three SDAMs; hwmon driver
  qcom-qpt-hwmon, writes only stock's start / ack bytes in its own SDAMs; `start=0` keeps it read-only),
  **npucool** (upstream QMI TMD series v8, patches 1-4 in rproc-next / linux-next since 25 Sep, backported unchanged;
  + Kaanapali CDSP entry with stock's instance 0x43 and four endpoints, stock's three maps; no trip changed).
  Kernels: **q67** = head + quickwins (0 warnings), **q68** = head + telemetry (inherits the quickwins config lines
  from out/.config; harmless for its test), **q69** = head + npucool (on the restored queue config, 0 warnings).
  Runs 73 (quickwins), 74 (telemetry), 75 (npucool) started as one chain.
- **Run 73** (q67 quickwins): 11 PASS / 4 FAIL - PASS: bwmon (128 updates), PMIH0108 lite alarm, autoload (QCE, Iris,
  CAMSS, CSI PHY + fastrpc, dw9719, mt5806, rpmsg_ctrl by the coldplug trigger), charger ulog on the SoCCP channel
  (462 lines), IMEM, DisplayPort bound (DP-1 disconnected), DP audio, EDAC, watchdog sysfs, no wireless supply. FAIL:
  1 (providers synced 14 / 14 incl. gcc / gpucc / gxclkctl; a criterion?), 5 (rear EEPROM 0x58 reads nothing), 10 (WSA
  macros gone; something else), 14 (the pin reader read nothing). Sent back.
- **Run 74** (q68 telemetry): 7 rails (cpu-m cpu-l gpu nsp mxc cx mmcx); counters consistent (ratio 1.02), CPU rails
  0.3 -> 11.9 W under load, backlight not on a measured buck, stop path ok; FAIL scale: rails +11.68 W vs battery side
  +8.12 W under load (1.44). Sent back.
- **Run 75** (q69 npucool): 13 / 14 PASS - TMD service 24 inst 0x43, four cooling devices stepped through every level,
  the three stock maps set and release under emulated temperatures; QMI TS instance 67 exists on the CDSP; FAIL cdevs
  (to be checked). Sent back.
- install agent: run 72's I/O errors came from its own build2 fallback disconnecting build1's disk; the slowness was
  the tablet -> PC write direction (0.2-0.7 MB/s) from the first minute, NOT my WSL builds (correction); suspect: the
  kits ran without the USB CPU-latency hold (USB_QOS empty in the run-44 template). Build split into build1a / 1b / 2a /
  2b (480 s each, records, safe release), relay per-minute lines. **Run 76** (q65, install dev + b1a b1b b2a b2b,
  USB_QOS=2, AUTOREBOOT_AT 4300, runner -Wait 4000) started; server + relay running.
- **gpuisp** delivered: Fedora 44's libcamera 0.7.1 already has the GPU soft ISP and uses it by default (every camera
  run so far was GPU; the 3.2 ms debayer is the GPU path); select with LIBCAMERA_SOFTISP_MODE or
  /etc/libcamera/configuration.yaml. 0.7.1 issues: GPU framing anchored top-left with garbage columns, no CPU fallback,
  an EGL context leak per camera start; 0.7.2 (in Fedora 44 updates) fixes framing and fallback. Run 77 generated
  (pkg2, rotpkg start, gpuisp-a cam GPU vs CPU + power, gpuisp-b Snapshot + leak, gpuisp-c 0.7.2 side by side).
- **upsync** delivered: base v7.3-rc4 is 705 commits behind mainline (rc5); our infiniti base is current (22 of its
  138 already accepted upstream); 23 "take" fixes in wf/upsync/cand/patches (ath12k regulatory x5, A8xx GPU votes x6,
  GPU shrinker, DPU gamma LUT, Type-C mux in suspend, eUSB2 repeater off at exit, QMP combo usage count, remoteproc stop
  error, TSENS trips above 120 C, Iris x4 incl. 10-bit formats + IOMMU low range, GENI I2C clock selection); risks: I2C
  probe, GPU votes. Plan: build qNN = head + upsync after run 76 (no WSL builds during network-disk runs), run its
  regression (wifi, gpucool, upsync, video / display / speakers, short sleeps).

### 2026-10-02 - entry 44: NPU cooling queued 0117-0124, run 76, quick wins round 2, the matrix

- **Queued 0117-0124** (iceland-linux **66d3736**, `queue-0117.sh`, tree = q69): the upstream remoteproc QMI TMD series
  (4 cherry picks, original authors Gaurav Kohli / Casey Connolly kept) + our Kaanapali CDSP ids / entry / node / stock's
  three maps. Head 6d67bc241; `build-q56.sh` expects "throttle the CDSP as stock".
- **Run 76** (install, split parts, USB_QOS=2): devrpm PASS; build1a: reads 31.1 MB/s, **writes under 0.3 MB/s**,
  package removal hit the budget (rc 124); 1b / 2a / 2b refused correctly; every part released the disk. The latency
  hold did not help: the tablet -> PC direction is the blocker. Sent to the install agent (gadget TX / NCM / TCP / MTU,
  a raw link test both ways). Server and relay stopped, overlay deleted.
- quickwins round 2 delivered: items 1 / 10 / 14 were test bugs (1 = no avdec_h264 in the rootfs; video now checked by
  the reference MD5s), item 5 real (the rear EEPROM loses L16B when the focus driver switches it: at24 gets a vio supply,
  stock's rails), new item 17 (the DSI PHY deferral logged without an error). FW_DEVLINK_SYNC_STATE_TIMEOUT judged safe.
- **Run 77** (q65, GPU ISP) started.
- User: "update feature matrix with everything commited" -> `matrix-c2p.py`: new rows NPU / CDSP cooling (ok),
  per-rail power telemetry (part), hardware inventory (ok); DisplayPort, headset (USB offload not possible), NPU,
  cameras (the ISP already on the GPU), Fedora installed (the write direction) updated; queue 0001-0124 in the status.
- **telemetry round 2 delivered**: the 1.44x was the test's comparison (the load stopped after 5 s at the skin limit,
  right after the 100 % brightness state; the battery figure was mostly that state's tail; the gauge stalled at the
  load start). The tablet's per-phase counts ("frac", two slots per rail) sum to 2.00x the main count = stock's
  6400 uW per count. Real fix: the report clock is 32.768 kHz (1021.7 / 1024 per s), energy 62.5 uJ per count (2.4 %).
  Test v2: load right after idle at the same brightness, skin under 46 C first, 30 s, energy over load + 75 s recovery.
  Next: build `TAG=q72 WF="telemetry"`, `gen-combo-telemetry.py N q72`.
- Commit q pushed as iceland-mainline **5c5187e** (its message says 60 working; the page's count is right: 59 / 13 / 5 / 2).
- try-head on 6d67bc241 (0124): quickwins, upsync (all 23) and telemetry v2 apply. upsync 18 (tsens v2 trip clamp
  -40..120 C -> the hardware's -204..204 C) only stops the driver clamping stock's 125 C trips to 120 C (interrupt
  storm); no trip and no limit changes -> within the charging / thermal safety rule.
- CONFIG_QCOM_QMI_TMD is selected by QCOM_Q6V5_PAS (`if NET`): the queue configs need no line for 0117-0124.
- Building q70 (quickwins r2), q71 (upsync), q72 (telemetry v2) with `build-q70-72.sh` (out/.config restored between).
- Builds done: **q70** 7e081fd8d44f (quickwins r2), **q71** bfc56ce5f7ae (upsync), **q72** a3ac45bc8c43 (telemetry
  v2; the make "clock skew" notice is harmless: the module is newer than the v2 source and has v2's window code), 0 warnings.
- **install agent: the slow tablet -> PC direction is an f_ncm bug**: ncm_tx_timeout()'s flush is dropped with
  NETDEV_TX_BUSY while all 10 IN requests are queued; the partial NTB waits until full; TCP runs into RTO backoff
  (cwnd 1, backoff 9, 137 / 149 retransmissions D-SACKed). Patch (re-arm the timer while busy), a 30 s `link` test part
  and linktest-server.py (Windows, --allow=172.16.42.1). Review note for upstream: hrtimer_forward_now() WARNs if
  another CPU re-armed the timer between the is_queued check and the forward (tiny window). build-q56.sh got case
  `ncm`; building **q73** = head + f_ncm.
- **User: "the tablet isn't charging?"** Read live (run 77, RAM kernel, read-only): battery 66 %, Discharging -0.75 A
  at 4.03 V (3.0 W); USB online as SDP (the PC port), input limit 500 mA, 0.49 A at 4.97 V (2.45 W); charge thresholds
  100 / 0, charge_behaviour auto, battery guard not running. Charging is NOT off: the PC's USB port gives at most
  2.5 W and the run (GNOME, screen, camera, GPU) draws about 5.5 W. A 10 min run costs about 1 %; between runs Android
  charges slowly from the PC port. Nothing raised (the 500 mA SDP limit is the USB standard and stock's).
- **q73** 9e83aef14 = head 0124 + f_ncm only (0 warnings). Kits generated and checked: **78** quickwins r2 (q70),
  **79** upsync regression (q71: wifi, gpucool, upsync, qwvideo, usleep, upsync2; -Wait 2500), **80** telemetry v2
  (q72), **81** link baseline (q69, no fix), **82** link with the f_ncm fix (q73); 81 / 82 AUTOREBOOT_AT 4300 -> 900
  (a 30 s test). linktest-server.py on Windows (0.0.0.0:10811, --allow=172.16.42.1).
- run-chain.sh got a **battery gate** (dumpsys battery in Android, read-only): below MINBAT (40 %) it waits until
  45 % before the next run.
- **Run 77** (q65, gpuisp): **b [app] PASS**: Snapshot on the GPU ISP, CPU 4.05 ms/f + GPU 1.48 ms/f, 5.20 W vs the
  CPU path 24.32 ms/f, 5.38 W; EGL leak per camera start: GPU memory +19.8 MB, RSS +6.1 MB. **a [cam] not compared**:
  the kit's rpm install used the `iceland-device-0.16*` / `hexagonrpc-0*` globs (the packaging is 0.17) -> rc 1, no
  iceland-device, hexagonrpcd inactive, no accelerometer -> no camera frames (generator bug, as fixed in gen-combo-61).
  **c [v072] not run**: no libcamera > 0.7.1-1.fc44 in the repositories. Sent to the gpuisp agent (round 2: generator
  fix, optional self-built libcamera with the EGL patch, leak with / without).
- LESSON: never edit a script a running bash is still reading (`run-chain.sh` got the battery gate while run 77's
  runner was in it: "syntax error" after PROBE DONE, harmless that time). Make a copy, edit the copy, swap between runs.
- Chain 78-82 started (battery before run 78: 71 %).
- **Run 78** (q70, quickwins round 2): **all PASS** - items 1-15 and 17 (16 = 6) in 49 s: 14 / 14 RPMh providers
  synced (11 forced by the sync-state timeout at 45 s, GMU trio released), no interconnect node at the boot floor;
  bwmon 132 updates / 132 interrupts; both EEPROMs read 4096 B before and after the focus driver's rail switch; DP
  binds with its jack; sram, ulog, edac, wdt, audio, speakers, video, display unchanged. **quickwins GREEN.**
- **Queued 0125-0138** (iceland-linux **0391661**, `queue-0125.sh`, tree = q70 e9e82859, QUEUE-VERIFIED): 14 commits
  (one per .msg section) + the config lines (distro-neutral: 6; required: FW_DEVLINK_SYNC_STATE_TIMEOUT, SRAM,
  EEPROM_AT24). build-q56.sh HEAD_SUBJECT -> "do not log a deferred PHY lookup as an error". New base config for
  builds on 0138: `out-config-base-0138` (= the queue config + the 6 lines).
- Note: q71 (upsync) and q72 (telemetry) were built on 0124; to queue them a kernel on 0138 is needed (tree rule):
  after runs 79 / 80, build q74 = 0138 + what passed and run one combined regression.
- **User: "can we replace the usb host / otg with dynamic role switching?"** Answer: it already is dynamic - dwc3
  DUAL_ROLE=y, `usb-role-switch` on the controller, the usb-c-connector power-role / data-role "dual" under pmic_glink,
  UCSI (UCSI_PMIC_GLINK=y) sets the role; live (area-combo-70): port0 data_role host [device], power_role source
  [sink] at the PC. Nothing to replace; host mode is only untested with an accessory (kits need the PC link = device).
  Proposed: CONFIG_USB_UAS=m in the next combined kernel; an accessory kit step (owner unplugs the PC, plugs a hub /
  stick, re-plugs; the tablet logs role, VBUS source, lsusb) as a deferred owner item - asked the user.
- **User: "proceed with 1 and 3"** (1 = CONFIG_USB_UAS, 3 = the USB-C fixes in test; not 2, the accessory kit).
  1: usb-storage is =y, so USB_UAS=m (auto-load by alias, as Fedora); build-q56.sh case `uas`; kit part
  `an/uas_part.py` (aliases, load, unload; no drive). Goes into the combined kernel q74 (0138 + what passes in 79 / 80
  + uas) and run 83; then the config line into the queue configs. 3: upsync 14 (pmic_glink altmode worker on the
  freezable queue) and 16 (qmp-combo init_count on a forced init failure) are judged in run 79 (usbc, usleep, upsync2).
- **Run 79** (q71, upsync regression): **upsync PASS on every group** (wifi, gpu 0 GMU/RPMh errors, gamma LUT 1024,
  thermal 110 trips >= 120 C / 1448 tsens irqs, i2c 9/9, usbc, rproc, video, logs 0); after 2 s2idle cycles usbc PASS
  (altmode bound, gadget configured 1 s after resume, no "Transfer while suspended") = the user's item 3 (upsync 14 /
  16) holds. Non-passes, none a kernel finding: upsync2 logs and quickwins display/GPU "fault" = the kit's own sayk
  summary line in kmsg matched their regexes (false positives); usleep long skipped (WF_SLEEP_LONG=20 < the test's
  60 s minimum); gpucool limits / load SKIP: skin 51.2 C at start (warm from runs 77 / 78), stock's skin stop after
  4 s -> the GPU-vote patches 06-11 still need a cool-start load. Sent to the upsync agent (round 2: fixes, apply on
  0138, parts for a combined run 83). quickwins tablet.sh: the fault count now skips `iceland-combo` lines (fixed here).
- LESSON for every kit: never count kmsg patterns without `grep -v iceland-combo` (sayk writes summaries there).
- **gpuisp round 2 delivered**: Fedora 44 stays on libcamera 0.7.1 (0.7.2 pulled from F44 on 20 Aug for a flicker
  regression, moved to F45) -> `req072` withdrawn. Run 77 part a failed on memory: without iceland-device the DMA-heap
  rule was missing, cam took the 32 MiB CMA heap ("allocation failure for frame-3"); rotpkg looked in /tmp/area-in/rpms
  instead of $R/rpms. Generator fixed (version from the spec). New: a local libcamera 0.7.1 build on the tablet (Fedora's
  SRPM + 3 upstream fixes: border scaling, EGL probe with CPU fallback, the EGL context leak), unpacked to /tmp, not
  installed; part c compares the leak per start (Fedora's >= 1 MiB vs local < 1 MiB). Kit **84** generated (q65; pkg2,
  rotpkg, gpuisp-a 600 s, -b 660 s, -c 480 s; AUTOREBOOT 3600; chain -Wait 4000); starts after the chain 78-82.
- **Run 80** (q72, telemetry v2): FAIL only on load, the rest PASS (7 rails; average 1.555 vs 1.496 W; stop 0x00;
  backlight +8.09 W battery / +0.16 W rails; frac 1.9985x; clock 1022.89 / s = 32.768 kHz); scale CHECK 0.46 (rails
  +48 J vs battery +105 J over 105 s). The load: CPU 50 -> 105 C within 1 s, skin 42.5 -> 53.3 C in 4 s -> the test's
  stock 51 C skin stop at 5 s (the cool-start gate worked; the skin zone sits near the SoC). Sent to the telemetry
  agent (round 3: a load under stock's thresholds, e.g. fewer cores / capped scaling_max_freq; judge 0.46; parts module).
- **upsync round 2 delivered**: log checks skip `iceland-` lines and count from a mark (kmark); usleep LONG 90 /
  BUDGET 240; new `ucool` part (read-only: skin < 46 C and gpuss < 60 C, max 360 s) before gpucool; qwvideo / usleep
  in their own folders; summary wording without the regex words; all 23 apply and compile (W=1) on 0138; 17 still
  valid on the TMD series (0117-0120 = upstream for-next, drop at the 7.4 rebase). Parts module cand/upsync_parts.py.
- try-head "upsync telemetry" on 0138: both apply. q74 = 0138 + upsync + telemetry v2 + uas: `build-q74.sh`, started
  by `after82-build-q74.sh` only once run 82's kit is staged (prep takes the kit lock with flock -n and refuses if busy).
- **q74** 73138ff6c345 (0138 + upsync + telemetry v2 + uas): 0 compiler warnings; 367 make "Clock skew" notices =
  only include/config/auto.conf(.cmd) 1.5 s in the future (Windows / WSL clocks agree to 0.2 s): a future-dated
  prerequisite only causes extra rebuilds later, never a missed target in this build; uas.ko and qcom-qpt-hwmon.ko built.
- **Run 81** (q69, link baseline WITHOUT the f_ncm fix): up 42.92 MB/s, down 36.97 MB/s (linktest.log). The single
  continuous upload does not reproduce run 76's < 0.3 MB/s: a steady stream keeps filling NTBs; the stall needs a burst
  that ends and waits for a reply (NBD writes: request, data, wait for the reply). The link test needs a request /
  reply upload mode to tell the kernels apart -> to the install agent with run 82's result.
- **Run 82** (q73, link WITH the f_ncm fix): up 42.93 MB/s, down 36.55 MB/s = the same as run 81. The continuous
  test cannot separate the kernels. Battery through runs 78-82: 71 -> 69 % (Android charges between runs). Sent to the
  install agent (round 3: a request / reply upload mode = NBD's write pattern, sizes 4 KiB - 512 KiB, predictions for
  q69 vs q73, the next suspects if q69 is fast too). linktest-server.py keeps running on Windows.
- **Run 84** (q65, gpuisp round 2) started (chain MAXN 400).
- **telemetry round 3 delivered** (driver v2 unchanged = the one in q74): the load is a controller: each cluster's
  scaling_max_freq capped to its highest step <= half max (1785.6 / 2227.2 MHz; written back and read back), pinned
  busy threads added one at a time towards +2.5 W on the CPU rails; adds only while skin < 46.5 C, drops one at 48 C or
  above +3.25 W, stops all at 49.5 C (stricter than stock; stock's stops stay armed); 60 s load + 80 s recovery.
  Scale: run 80's 0.46 was no valid measurement (5 s burst vs a gauge that samples every ~5 s and averages 60 s);
  expected 0.7-0.9, PASS 0.6-1.05, CHECK 0.45-0.6 / 1.05-1.2, no verdict below 45 s of load or 80 J battery side.
  Part 7.2 min (8.2 max). Module cand/telemetry_parts.py.
- **Run 83 generated** (`gen-combo-83.py`, q74): setup, telemetry, ucool, gpucool, wifi, upsync, qwvideo, usleep,
  upsync2, uas, close (budgets 3300 s, AUTOREBOOT_AT 4300, chain -Wait 4000); queued to start after run 84.
- **Run 84** (q65, gpuisp round 2): pkg2 / rotpkg fixed (iceland-device 0.17 installed, accelerometer after 2.4 s).
  a [cam] CHECK: rear GPU vs CPU picture DIFFERENT r=0.58 (R/G 0.93 B/G 0.89), front ok 0.99; rear CPU 2.32 vs 21.42
  ms/f at 30 / 30 fps, GPU 0.61 ms/f, 4.71 vs 4.64 W; edges gpu/cpu 3.73 / 0.51 (the border bug?); brightness put-back
  FAIL (1161 != 1256, test bug). b [librpm] FAIL at 16.6 s: meson `Dependency "libdw" not found` (trimmed spec /
  builddep). c [leak] CHECK: preview never came up (err 4). Sent to the gpuisp agent (round 3).
- **install round 3 delivered**: run 81's continuous upload had 0 retransmits (cwnd 200); runs 72 / 76: 134 slow writes,
  each the server waiting for the rest of a write after its header (<= 16 KiB mean 6.1 s, > 256 KiB mean 11.9 s).
  Refined: only bursts that fill all 10 IN requests (> ~140 KiB) or concurrent requests hit the lost flush. New parts
  `rr` (request / reply 4 K-512 K, 2 x 4 in flight, with a download, via the relay to WSL) and `nbdw` (the real NBD
  client, dd oflag=direct to /dev/nbd0 at 100 GiB - checked: only /dev/nbd0, never the tablet's storage).
  Prediction: q69 512 K one at a time < 2 MB/s, q73 25-40 MB/s; "with a download" faster than alone on q69.
  Kits **85** (q69) and **86** (q73) "link rr nbdw", AUTOREBOOT 1200; they need the NBD server + relay, the Windows
  linktest server (new version copied) and the relay leg (WSL linktest 10811 + Windows relay 10812): started after run 83.
- **Run 83** (q74 combined): **telemetry round 3 PASS** (7 rails; average 0.500 vs 0.499 W; cap restored; CPU rails
  +2.19 W for 59 s with up to 3 threads; scale 0.74 over 140 s; frac 1.9954; clock 1023.16) = **telemetry GREEN**.
  ucool PASS (cool at once), **gpucool 20 / 20 PASS** incl. ramp / cap / effect / recover (= upsync 06-11 under load),
  **upsync PASS** on every group, **upsync2 PASS** (21 lines since the mark, 0 warnings), **uas PASS** (27 aliases,
  loads, unloads). Sleep: 3 s2idle + 90.6 s long sleep, cxsd +26. **But no sound card** (sink "Dummy Output", 0
  amplifiers, audio 0 / 2). Cause: 21 modules that run 78 had were never loaded, among them snd_soc_hdmi_codec = the
  DP audio codec the card waits for since quick-wins item 9; run 78's card came exactly when the quick-wins autoload
  step (udevadm trigger of driverless devices) loaded it; run 79 had no DP audio. A kit artifact: kits unpack the module
  tree after boot and nothing loads modules for existing driverless devices; an installed boot does (udev coldplug).
  Fix: genwf.gen(..., coldplug=True) = trigger only driverless devices with a modalias (as quick-wins item 11; guarded
  against an empty list = never "trigger everything"), settle 60 s. Confirmation run **87** (q74: coldplug, qwvideo,
  usleep). Also seen in 83's sleep part: dpu "frame done wait timed out" and PCIe "Timeout waiting for L2 entry" at a
  suspend - compare with earlier sleep runs before queueing.
- **gpuisp round 3 delivered**: libdw (Fedora's %meson = --auto-features=enabled; BuildRequires pkgconfig(libdw));
  part c: iceland-device 0.17's 51-iceland-camera.conf + WirePlumber 0.5.17 stalls WirePlumber's event dispatcher ->
  0 camera sources (fixed upstream 65519a1, in WirePlumber 0.5.18, F44 stable since 1 Oct) -> for 0.18:
  `Requires: wireplumber >= 0.5.18` (or drop the rule); rear DIFFERENT = exposure / clipping / metering area, not
  geometry (the compare now ignores clipped cells); brightness = GNOME's auto level, now restored while owned. Kit **88**.
- Servers for 85 / 86 started: NBD `rehearsal-pc.sh serve stage0 build` (WSL 10810), relay 10809 -> wsl:10810,
  linktest 10811 (Windows), linktest 10811 (WSL, gateway only) + relay 10812; all --allow=172.16.42.1.
  Chain 85 86 87 88 started.
- Suspend-time lines checked across runs: PCIe "Timeout waiting for L2 entry" on every suspend since run 67 (67: 8 / 8,
  79: 2 / 2, 83: 3 / 3) and one dpu "frame done wait timed out" / "enc timeout pending" in run 67 already (before any
  upsync patch) -> pre-existing, not from q74; no block for queueing. (A follow-up for the deep-sleep notes.)
- **Run 85** (q69, NO f_ncm fix; link rr nbdw): link up 42.95 / down 36.42 MB/s. rr one at a time: 4 K 6.75, 64 K
  35.7, 128 K 39.5, **512 K 41.4 MB/s** (max 14 ms) -> the agent's "512 K alone collapses" is wrong. 2 x 4 in flight:
  ~40 MB/s total but stalls 0.7 / 1.1 s. **512 K with a download running: 0.12 MB/s, max 8.4 s, and the download
  itself 0.24 MB/s** = two-way traffic collapses both (NBD reads + writes at once = run 76). **512 K through the relay to
  WSL: 0.03 MB/s, max 19.3 s** (ran right after the collapse: a stuck partial NTB survives into the next flow?).
  nbdw did not run: `wf-install.sh: line 238: r: unbound variable` (agent's bug). Waiting for run 86 (q73, with fix).
- **Run 86** (q73 = 0124 + f_ncm only): **the f_ncm patch fixes the two-way collapse**. q69 -> q73: 512 K + download
  0.12 MB/s (max 8.4 s), download 0.24 -> **8.35 MB/s (max 104 ms), download 31.0 MB/s**; 512 K via the relay to WSL
  0.03 (max 19.3 s) -> **39.7 MB/s (max 14 ms)**; 2 x 4 in flight 64 K 40.7 (676 ms) -> 43.0 (20 ms), 512 K 39.6
  (1141 ms) -> 43.1 (114 ms); one-at-a-time and link unchanged (~41 / 43 / 36 MB/s). Trigger = traffic in both
  directions (the download's ACKs + the upload keep all 10 IN requests busy). nbdw still `r: unbound variable`.
  Sent to the install agent (round 4: nbdw fix, commit message to the data, the hrtimer re-arm race, rehearsal plan).
  To queue: needs a kernel on the head (after q74's queueing) + a short rr confirmation.
- **Run 87** (q74 + coldplug: 36 driverless devices triggered, 16 modules loaded): **sound back** - 6 / 6 amplifiers,
  sink "Built-in Audio Speakers", audio 2 / 2 across s2idle; video 240 / 240, display, GPU ok; sleep PASS (2 cycles +
  89.7 s long). = run 83's missing card was the kit (no autoload of snd_soc_hdmi_codec). **But cxsd +0** (83: +26) and
  **s2idle entries +19** (83: +3): coldplug also autoloaded **qcom_qpt_hwmon, which starts the telemetry at probe**
  ("report every 1000 ms, telemetry started") and keeps it running -> an installed system would run it forever and it
  likely breaks CX collapse (the sound card is a second difference: 79 and 87 with sound had cxsd +0; 79's long sleep
  was skipped). -> telemetry NOT queueable as is; sent to the telemetry agent (round 4: lazy start / idle stop / off in
  suspend, an IRQ-count + s2idle A/B part). Plan: q75 = 0138 + upsync + uas + f_ncm (no telemetry), run 89 regression
  with coldplug (upsync, qwvideo, usleep = cxsd with sound and without telemetry, uas) + run 90 rr link -> queue those.
- **q75** 3c1486eb1f5f = 0138 + upsync + uas + f_ncm (no telemetry), 0 compiler warnings. Kits **89** (q75 regression
  with coldplug: wifi, upsync, qwvideo, usleep, upsync2, uas; AUTOREBOOT 2800) and **90** (q75 "link rr", 900 s)
  generated; queued after run 88; link servers (Windows 10811, WSL 10811 + relay 10812, --allow) running for 90.
  If both pass: queue upsync (23) + the uas config + f_ncm from q75's tree.
- **install round 4 delivered**: nbdw fixed (`local r=""`; dry-run 11 PASS). **f_ncm patch v2**: the race was real
  (ncm_wrap_ntb starts the timer under u_ether's dev->lock, the callback's BUSY return happens before that lock), so
  the callback now calls hrtimer_start() itself and returns NORESTART (allowed; __run_hrtimer leaves an enqueued timer
  alone); no re-arm while the port is suspended; at most 333 re-arms (~100 ms) per NTB; commit message rewritten to
  the q69 / q73 data. qmult workaround removed from iceland-rehearsal. Reviewed here: OK to test.
  -> q75 carries v1, so: chain 89 / 90 stopped before it started, **q76** = 0138 + upsync + uas + f_ncm v2 building;
  kits 89 / 90 to be regenerated for q76. B-run plan after queueing: gate `rr` (+down >= 5 MB/s, slowest < 1 s), then
  "rr dev b1a b1b b2a b2b", AUTOREBOOT 4300, ~20-30 min at 30-40 MB/s; then commit golden, serve golden r1, R1.
- **q76** 825c23ce595c = 0138 + upsync + uas + f_ncm **v2** (TX_TIMEOUT_MAX_REARM in the tree), 0 compiler warnings; kits 89 / 90 regenerated for q76 and re-queued after run 88.
- **Run 88** (q65, gpuisp round 3): **a [cam] PASS** (GPU ISP works: rear r=0.82, front 0.98 after the clipping-aware
  compare; 30 fps; CPU 2.34 vs 21.40 ms/f; 4.86 vs 4.61 W). b [librpm] FAIL at 6.4 s: spec parse error - a comment in
  mk-spec.py's spec mentions `%meson`, RPM expands macros in comments ("Macro expanded in comment on line 30", "Unknown
  tag: CFLAGS=..."). c [leak] CHECK: Fedora's library +19773 KiB GPU / +6148 KiB RSS per start (run 77 exactly);
  "rule as installed: 0 camera sources" = the WirePlumber 0.5.17 stall confirmed. Sent to gpuisp (round 4: %% in
  comments, rpmspec -P check, err 4). Battery before 88: 67 %.
- **telemetry round 4 delivered** (driver **v3**, queue v3 not v2): run 87's counters show the **ADSP awake through
  the whole 90 s sleep** (qcom_stats adsp: last exit after last entry; 83: asleep +93 s) - the long sleep began right
  after wf/sleep's 3 s tone with the stream open -> that alone explains cxsd +0; 87's "s2idle +19" is a running total
  (+1 in the long sleep in both runs); the report IRQ was never requested. Stock: the driver never starts at probe (a
  powercap "enabled" write does; stock's thermal daemon stops it); in suspend stock masks the report IRQ, keeps the
  overflow IRQ as a wake source. v3: no start at probe (a boot-firmware-started one stops after idle), first read of
  energy / power starts it, stops idle_ms (10 s) after the last read, at every suspend and at removal; overflow IRQ
  only while running, not a wake source. New part **tlazy** (PT 420): idle = no reports / IRQs, 90 s s2idle A/B
  (driver loaded vs removed) on CX / AOSS / s2idle entries / ADSP. Next: after q76 is queued, q77 = head + telemetry v3,
  parts setup, tlazy, telemetry.
- Open question for the deep-sleep notes: does PipeWire leave the ADSP awake when audio is idle on the installed
  system? (wf/sleep plays a tone right before its long sleep - worst case.) tlazy's A/B runs with an idle sound card.
- **Run 89** (q76 regression with coldplug: 35 driverless devices, 15 modules): **all PASS** - upsync every group,
  upsync2 (18 lines since the mark, 0 warnings), qwvideo (video 240 / 240, display, 6 / 6 amplifiers), sleep PASS
  (3 s2idle + 90.6 s long, audio 2 / 2), uas PASS. **cxsd +0 again without any telemetry driver** (s2idle entries +3)
  -> confirms the telemetry agent: the ADSP stays awake after wf/sleep's tone (stream open); not the telemetry.
- **gpuisp round 4 delivered**: spec comment without %, mk-spec refuses an unescaped % in added comments, part b runs
  rpmspec -P first; on the PC a real rpm 4.18.2 + Fedora 44 macros parse the spec (0 errors, negative control
  reproduces run 88), rpmbuild -bp with Fedora's lookaside tarball applies all patches at fuzz 0; "err 4" = the stopped
  WirePlumber's IPA workers (harmless), now attributed. Kit **91** queued after run 90.
- `queue-0139.sh` (0139-0161 upsync via git am, authors kept + our trailers; 0162 f_ncm v2; configs USB_UAS=m): DRY
  -> tree equals q76. Waiting for run 90 (link rr on q76) before queueing.
- **Run 90** (q76, f_ncm v2, "link rr"): link 42.91 / 36.37 MB/s; rr 4K 6.57, 64K 35.4, 128K 39.3, 512K 41.5 MB/s;
  2 x 4 in flight 42.9 / 43.0 MB/s (max 17 / 154 ms); **512K + download: rr 4.54 MB/s, max 185 ms, download 33.6 MB/s**
  (q69: 0.12 MB/s max 8.4 s, download 0.24); relay 39.6 MB/s (max 15 ms). = v2 fixes the collapse as v1 did (rr / down
  split 4.5 / 33.6 vs v1's 8.4 / 31.0, same total; no stall > 185 ms). The agent's B-run gate "+down >= 5 MB/s" is too
  strict for TCP's split: gate on "slowest round trip < 1 s and rr + down > 20 MB/s" instead. 0 REFUSED. Link servers
  stopped. Queueing 0139-0162 once run 91 is staged (biz4b3wwq).
- **Queued 0139-0162** (iceland-linux **b591ccd**, `queue-0139.sh`, tree = q76 31260bdc, QUEUE-VERIFIED): 0139-0161
  the 23 upsync fixes (authors kept), 0162 f_ncm v2, configs CONFIG_USB_UAS=m. **upsync GREEN, uas GREEN**, the
  install link blocker fixed in the queue. Head: "usb: gadget: f_ncm: retry the NTB flush while every IN request is
  busy"; base config out-config-base-0162. Next: q77 = head + telemetry v3 -> run 92 (tlazy, telemetry, coldplug).
- **q77** 853e87db03c2 = 0162 + telemetry v3 (idle_ms in the tree), 0 compiler warnings; kit **92** (coldplug,
  tlazy, telemetry) generated. **q78** = the plain queue head 0162 (first head with the f_ncm fix) on base-0162: the
  install B-run kernel; building with the kit lock; then `next-k2p1u1.sh TAG=q78` (DRY first; k3 holds the lock
  10-15 min, so run 92's chain starts only after it).
- **q78** 0b261bcba556 = the plain queue head 0162, 0 compiler warnings. next-k2p1u1.sh DRY TAG=q78: 5 PASS; real run started (k2, k3, p1 -> iceland-device 0.18 source, u1, tin) -> wf/install/work/next-k2p1u1-q78.log.
- **next-k2p1u1 TAG=q78: 5 PASS** - K2 kernel-iceland-7.3.0~rc4.iceland.00300.g0b261bcba556 (22 MB, check 13 PASS),
  K3 (.1, marker in the DT, check 13 PASS, 0 warnings), P1 iceland-pkg-0.18.tgz (0.17 @ 5c5187e + the install
  fragment, check-device 16 PASS), U1 both U-Boot images (29 PASS), TIN tablet-in 14 files 45 MB.
- **B-run kit 93** (q78, "rr dev b1a b1b b2a b2b", AUTOREBOOT 4300, chain -Wait 4000). Safety read: every storage
  write goes to /dev/nbd0 / its loop; ufs_ro sets the UFS devices read-only first; the 15 "flash/format" matches in the
  kit are LEDs / video formats / an rpm queryformat. ov-build was empty (cow.idx 0 B). Servers: NBD serve stage0 build
  (WSL 10810), relay 0.0.0.0:10809 -> wsl:10810 and linktest 10811 (Windows), all --allow=172.16.42.1. Gate judged by
  me: rr "+down" slowest < 1 s (the agent's 5 MB/s is too strict, q76 gave 4.54 with no stall). Chain 92 93 queued.
- **Run 91** (q65, gpuisp round 4): **a PASS** (rear r=1.00, front 0.99; CPU 2.30 vs 21.25 ms/f; 4.81 vs 4.87 W).
  **b**: rpmbuild rc 0 in 104 s, 5 rpms libcamera*-0.7.1-1.fc44.iceland1, SoftISP GPU YES, cam lists 2 cameras;
  "FAIL" only because its patch check read a BUILD dir rpmbuild had removed (build.log lines 15 / 17 / 19: all three
  patches applied in %prep). **c PASS: the local build stops the leak** (system +19773 KiB GPU / +5437 KiB RSS per
  start, local 0 / 0; err 0); border fix: right-edge ratio 10.89 -> 2.16 (CPU 0.40). **gpuisp green in substance**;
  sent: fix b's check, the 0.18 patcher (wp0518 + hold) on the install's 0.18 tree, how the local rpms reach the install.
- NOTE for the next docs commit: run 91's log set holds the 5 built rpms (librpm/rpms/*.rpm) and the blob guard has
  no `rpm`: exclude '*.rpm' in the log-set copy and add rpm to the guard (mk-commit-r).
- **Run 92** (q77 = 0162 + telemetry v3, coldplug): **tlazy PASS** (lazy, start, readings, idle-stop, quiet, suspend,
  s2idle, kernel): s2idle A (driver loaded) cxsd +28 = 95 %, aosd +0, system s2idle +1, apss 98 %, ADSP asleep; B
  (driver removed) cxsd +26 = 95 %, same -> **the v3 driver costs deep sleep nothing, and CX collapses with the sound
  card present and idle** (the cxsd +0 of runs 79 / 87 / 89 = wf/sleep's tone right before its long sleep).
  **telemetry PASS** (round 4): lazy at load, average 0.455 vs 0.458 W, cap restored, stop 0x00, backlight +8.20 /
  +0.01 W, CPU rails +2.15 W for 59 s, **scale 0.86**, frac 1.9948, clock 1023.04. **telemetry GREEN** -> queue from
  q77's tree (+ CONFIG_SENSORS_QCOM_SPMI_QPT=m).
- Run 93 (B run) did not start: prep "sensor module / regulatory.db missing" - build-q78.sh (build-q2.sh directly) did
  not make camdrv/sc1320cs-q78.ko as build-q56.sh does. Built it (an/camdrv-q78.sh, vermagic = q78), run 93 restarted.
- **Queued 0163-0166** (iceland-linux **f84d0d2**, `queue-0163.sh`, tree = q77 da065d30, QUEUE-VERIFIED): binding,
  hwmon driver v3, pmk8850 node, board node + CONFIG_SENSORS_QCOM_SPMI_QPT=m. **telemetry GREEN.** Head "enable the
  power telemetry"; base config out-config-base-0166.
- Workflow state: quickwins, npucool, upsync (+uas, f_ncm), telemetry, hwinv GREEN and queued / done; gpuisp green in
  substance (b's check, the 0.18 patcher, the local rpms pending with the agent); install: B run 93 on q78 running;
  deepsleep: the night test is the owner's, its package fallback goes into 0.18.
- **Commit r** pushed: iceland-mainline **b48a179** (runs 77-92, results part Q, matrix c2q: 61 working / 12 in
  progress / 5 / 2; new row "Upstream fixes for this chip's drivers", telemetry ok, cameras / deep sleep / USB host /
  DP / install updated); 0 rpm and 0 private paths in the commit (the new '*.rpm' exclusions + guard). Matrix page v39.
- **Run 93 = the install rehearsal's B run on q78: ALL PASS.** rr gate: +down 7.57 MB/s up / 31.8 down, max 127 ms;
  devrpm iceland-device-0.18 built on the tablet (87 files, storage rule, dracut module, 2 trial units); build1a nbd
  read 31.3 / **write 38.6 MB/s**, 10 packages removed, firmware 23 ok / 0 failed (= stock 11.A.38), bdaddr placed,
  84 s; build1b Fedora additions 33 s; build2a device package 0.18 + our rpms + grub.cfg 73 s; build2b SELinux labels,
  initramfs with iceland-carrier / nbd.ko / storage rule / zap, kernel 7.3.0-rc4-iceland-00300-g0b261bcba556
  confirmed, 29 s; every part released the disk. (Run 76 before the fix: writes < 0.3 MB/s, nothing finished.)
  Next per the plan: rehearsal-pc.sh stop, commit (golden), serve golden r1, head "enforcing=0", R1 (rehearse.ps1,
  fastboot boot only) + rehearsal-probe.sh accept.
- **gpuisp workflow FINISHED (green)**: part b's check fixed (build.log apply lines + markers in the built library;
  run 91 replays PASS); 0.18 patcher `pkg-gpuisp.py TREE hold wp0518` (wireplumber >= 0.5.18, libcamera* in the hold;
  10 / 10 package tests); local rpms: only libcamera + libcamera-ipa, kept in C:\platform-tools\rpms\libcamera
  (stash-rpms.sh, SHA256SUMS), tin / make-repo / the apps package list take them; hold and rpms go together; rebuild
  only for a newer libcamera / a soname change / F45. To do: fold into the final 0.18 (with the deepsleep fallback).
- G13 was closed in entry 37 (rehearsal U-Boot without SCSI/UFS, initramfs UFS read-only, nbd-only carrier); work-list
  item 6 done today -> **R1** (work-list item 7, RAM only): rehearsal-pc.sh stop / commit (golden = stage0 + 152941
  overlay blocks) / serve golden r1 / head "enforcing=0" (470 MB, rehearsal_max 540 s); rehearse.ps1 -Yes (fastboot
  only devices / getvar / boot / reboot / oem console) + `ACCEPT_SUSPEND=0 rehearsal-probe.sh area-r1 accept`.
- **R1 stopped in the rehearsal U-Boot** (19:38): after "head sent in 19 s" the screen shows U-Boot's blkmap usage
  text (webcam frames at the owner's request, local only: "...mem <addr> [preserve|reserve] - memory mapping",
  "...linear <interface> <dev> <blk#> - device mapping", "...create device (block size of memory maps, default 512)")
  = a blkmap call in the head-unpack path got arguments our patched blkmap does not accept; U-Boot then stays at the
  error: no fastboot, no adb (19:44). Nothing written (this U-Boot has no SCSI / UFS). Needs the owner to hold the
  power button to restart into Android. Sent to the install agent (round 5: the failing command, every failure path
  back to `fastboot usb 0` or `reset` so no failure needs hands, rehearse.ps1 detects it, the rerun steps).
- Owner restarted the tablet (power button): Android back, battery 50 % (charging). R1 left nothing: ov-r1 empty
  (cow 0 B); probe, NBD server, relay and leftover PowerShell processes stopped. Webcam frames cam/r1, cam/r1b kept
  locally until the install agent's round 5 has used them, then deleted (webcam rule).
- Sent to the install agent: fold gpuisp (`pkg-gpuisp.py hold wp0518` + the local libcamera rpms in tin / make-repo /
  the package list) and deepsleep (`npu-keep-running.py`) into P1's 0.18, so the R1 rerun runs the real package; then
  next-k2p1u1 (p1 + tin), B again (~4 min), R1.
- User: "update feature matrix with everything commited" -> matrix-c2r.py (install row: B run passed in ~4 min, R1 stopped in the rehearsal U-Boot, nothing written; camera row: the GPU ISP workflow finished; 143 test runs), results part R; commit s pushed as iceland-mainline **cc21f47** (0 rpm / private / frame files); page v40.
- User: "spin a fable agent to help debug and assist the install agent" -> a Fable-model helper ("r1debug") started:
  PC only, writes only in wf/r1debug/, wf/install read-only, may build its own U-Boot sandbox copy to reproduce the
  blkmap failure; tasks: the exact failing command and why, recovery without hands (back to fastboot or reset) + a
  test, REPORT.md + fix patches in its folder, findings sent to the install agent (who was told) and to me.
- **R1 root cause (install agent)**: cmd/blkmap.c's subcommand table kept `U_BOOT_SUBCMD_MKENT(create, 2, 1, ...)`
  (maxargs 2), so "blkmap create rehearsal 4096" (3 args) was refused with the usage text before do_blkmap_create ran
  (patch 0004 changed the parser and help, not the table entry); fastboot_head's && chain stopped, fastboot_bootcmd
  returned inside the USB completion, the fastboot loop ended, bootcmd (`fastboot usb 0`) was done -> U-Boot at its
  prompt, no fastboot. Fix in progress: maxargs 3; every failure path prints "FAILED: <step> - back to fastboot";
  bootcmd = run fastboot_loop (10 fastboot sessions, then reset) in both builds; a U-Boot sandbox check of the same
  tree. Forwarded to the r1debug helper to verify (the remaining steps, the fix, the recovery paths) instead of
  duplicating.
- User: spin an Opus documentation expert / SME -> "docs" agent started (Opus): read-only everywhere, writes only in
  wf/docs/, no tablet actions / builds / commits, privacy + copyright rules. Deliverables: PLAN.md (outline sent to me
  first), 01-OVERVIEW, 02-HARDWARE (SM8850 / Pad 4 blocks, RAM, UFS, partitions generic, firmware, efisp),
  03-BOOT-AND-PARTITIONS, 04-BUILD-YOUR-OWN (general-user guide), 05-PORTING-TO-OTHER-DISTROS (Debian first),
  06-PROCESS-HISTORY, 07-INSTALL-REVIEW (findings sent to me, not to the busy install agent), GLOSSARY, INDEX.
  The main session reviews and commits the docs (iceland-mainline docs/guide/ planned); the agent stays as SME.
- docs agent: PLAN.md written (wf/docs/); writing INDEX, 01-07, GLOSSARY; facts marked proven (run) / PC-checked / planned / untested; no device-unique values; commands only inside warning blocks.
- **install round 5 delivered**: R1 cause = patch 0004 left `U_BOOT_SUBCMD_MKENT(create, 2, 1, ...)` (fixed: 3),
  reproduced in a U-Boot sandbox of the same tree (cand/u-boot/sandbox-check.sh); the sandbox also found "Stack
  smashing detected in part_test_mac" (the Mac partition parser on 4096-byte blocks) -> no Mac / Amiga parser, checked.
  Every fastboot_head failure prints "=== ... FAILED: <step> - back to fastboot ===", both builds end in `run
  fastboot_loop` (10 sessions, then reset). mk-uboot.sh 37 PASS (sandbox 6 PASS incl. not-gzip, not-a-boot-image,
  the loop -> RESET). rehearse.ps1: U-Boot back -> uboot-console-2.txt, FAILED line, fastboot reboot, exit 2; no device
  at all -> asks the owner for the power button. New U-Boot images 19:57 (rehearsal 9d76918a..., install ae1f533d...).
  P1 now 0.17 + install fragment + gpuisp (hold, wp0518) + deepsleep (npu-keep-running); tin + our libcamera rpms;
  accept.sh `camstack`. User asked what rehearse.ps1 whitelists: fastboot devices / getvar / boot / reboot /
  `oem console` (exact); adb devices / get-state / reboot bootloader / shell getprop <[A-Za-z0-9._]+>; else abort.
- R1 rerun, PC steps: rpms stashed (C:\platform-tools\rpms\libcamera + SHA256SUMS); next-k2p1u1 STEPS="p1 tin": 2 PASS
  (iceland-pkg-0.18.tgz 5d00a340... = 0.17 @ cc21f47 + fragment + gpuisp + npu; check-device 16 PASS; README tests 10;
  tablet-in 16 files incl. libcamera + -ipa). ov-build (run 93's data, merged into golden) and ov-r1 (empty) deleted;
  serve stage0 build; relay + linktest (tablet only); **run 94 = B rerun** started (battery 51 %). R1 waits for the
  r1debug helper's verification of the U-Boot fix.
- User: "seems like audio isn't working again" (run 94 = B rerun kit, no coldplug): read live: no sound card,
  devices_deferred "sound snd-sc8280xp: DisplayPort0 Playback: codec dai not found", hdmi-audio-codec device present,
  snd_soc_hdmi_codec not loaded, PipeWire only "Dummy Output" = run 83's kit artifact. `modprobe snd_soc_hdmi_codec` in
  the running session -> card OnePlus-Pad4 back, sink "Built-in Audio Speakers". Permanent kit fix: snd-soc-hdmi-codec
  added to the kits' early module list mods25/all before snd-soc-sc8280xp (backup all.before-hdmi): every kit type
  now loads it at boot as udev does on an installed system.
- User: "check all errors in kmsg during booting and put a plan to resolve" -> an/kmsg-errors.py on runs 92 (q77 =
  queue 0166, coldplug) + 93 (q78): 77 groups, 0 WARNING / BUG / Oops. Plan in docs/BOOT-LOG-PLAN.md: P1-a ADSP/CDSP
  firmware -2 at 19 s (pas probes in the initramfs; installed system has nothing that starts it later), P1-b the build
  chroot loads SELinux policy into the kit kernel, P1-c ath12k country setting fails (world domain), P1-d PCIe L2
  timeout at suspend; P2 DT gaps vs stock (PCIe / WCN / backlight supplies, VA macro DMIC rate, SoundWire ports,
  FastRPC memory, UFS MCQ, smem DDR info, SCMI FC); P3 cosmetic / harmless.
- User: "isn't it better to move most of the hardware to kernel?" -> answer in BOOT-LOG-PLAN.md: built in only what
  must work before root (clocks, power domains, RPMh, interconnects, pinctrl, regulators, SMMU, UFS, watchdog; USB
  gadget + NBD for the rehearsal); firmware-dependent drivers stay modules (built in they fail like P1-a).
- User: "no setting for charge limit in power setting; can we add a bypass charger mode with a setting in power?" ->
  run 94's session has no device package (install kit): UPower 1.91.4 CHARGE_LIMIT=75,80 but no threshold support
  shown -> GNOME hides the switch (proven with the package in runs 40 / 41). New **bypass** workflow agent (stock's
  bypass, charge_behaviour inhibit-charge as the mechanism, one state machine with the limit / guard / BCL, a Quick
  Settings toggle vs a patched Power panel, a kit test, the charge-limit acceptance check).
- docs agent's install review (8 findings + a gotcha): HIGH no AVB footer on u-boot-iceland.img for a chained boot
  partition (ABL would not continue, slot switch); HIGH the plan's undo uses the pre-LineageOS backup; HIGH plan/guide
  still say the install U-Boot is RAM-booted in rehearsals; MEDIUM U-Boot waits forever installed; MEDIUM EFI boot
  order tries every UFS LUN first (efisp never inspected); MEDIUM dual boot not planned (write 1 erases Android's
  data); guide stale. Forwarded with the boot-log P1-a / P1-b / charge-limit acceptance to the install agent (round 6).
  Owner decisions to ask: write order (probe write 2 first) and dual boot.
- **Run 94 = B rerun with the full 0.18 (fragment + gpuisp + deepsleep, our libcamera rpms in tin): ALL PASS** - rr
  +down 8.26 MB/s / 31.7, max 110 ms; devrpm 0.18 (87 files) 20 s; build1a 82 s (nbd write 36.1 MB/s, firmware 23 ok);
  build1b 40 s; build2a 75 s (0.18 + our rpms + grub.cfg); build2b 29 s (labels, initramfs, kernel confirmed). Relay +
  linktest stopped; NBD server (stage0 build) still up for the golden commit. R1 on this golden waits for the r1debug
  verification; it also answers B1 (ADSP on the installed initramfs) with evidence.
- **Owner decisions**: "no dual boot for now but prepare a plan for it with the best safety precautions" -> install
  stays Fedora-only; the install agent writes wf/install/DUALBOOT-PLAN.md (plan only: options incl. Fedora as an image
  file in Android's userdata, userdata shrink, another LUN, boot selection; FBE / metadata encryption; undo per step;
  L0-L5 levels; RAM rehearsals first); the docs agent reviews it. Write order (R3) still open.
  "also fix pcie timeout and device tree gaps using our debugger" -> the Fable debug helper takes it after its R1
  verification: new folder wf/bootfix/ (PCIe L2 timeout + the 14 probe deferrals + supplies, WCN / backlight
  supplies, VA macro DMIC rate, SoundWire ports, FastRPC memory, UFS MCQ, smem DDR info, SCMI FC, the NVT touch
  message); stock values from wf/audit (read only, private); candidates + tablet test parts + parts module.
- **Owner decision R3: "yes lets test"** = the write-2 probe first (U-Boot in boot_b while Android's data is intact;
  undo = boot_b-before-install.img). Preconditions sent to the install agent: the AVB hash footer + the PC proof with
  today's vbmeta_b (PUBLIC_KEY_REJECTED, not INVALID_METADATA), today's images pulled read-only by a reads-only script,
  a new guide part C0 (the single owner command, what he sees, retry counter, undo), the plan / guide order updated.
  Nothing is written until all is green; the owner runs the write themselves.
- User: "perhaps you can boot it and i can test charging?" -> kit **95** = the owner's charging sitting (wf/charging):
  q77 (= queue 0166), coldplug, pkg2 (device package 0.17: guard + the charge-limit switch), the 20-minute logger
  with notifications and stock's safety stops, the result lines (gen-combo-95.py; AUTOREBOOT 2700). Started, then
  STOPPED before the reboot when the user said: "remember that tablet will be disconnected while it recharges so make
  sure to tell me to connect it before testing anything" -> new rule (memory iceland-ask-before-tablet-runs): ask the
  owner to connect and wait for their go before any tablet action; no chain left waiting on adb.
- bypass agent handed over (REPORT.md DRAFT - HANDOVER): run 94's missing switch = UPower read the battery's udev
  properties at 44.94 s, before udev's coldplug set CHARGE_LIMIT (0.17's start-order drop-in prevents it); accept.sh's
  charge-limit check reads /sys/class/power_supply/battery (wrong name; qcom-battmgr-bat). Stock bypass =
  oplus_chg_plc (`oplus,plc_charge`): charging off with the input kept (= our inhibit-charge), holds the level within
  ~1 %, ends after 5 min unless refreshed and at unplug; threshold picker from 20 %, a Quick Settings tile. Design:
  bypass as one more "charging off" reason inside the battery guard (the only writer of charge_behaviour), a GNOME
  Quick Settings toggle + a polkit-checked helper. Not started: NEXT, tablet.sh, patcher, toggle, tests.
- User: "spin a different agent specifically for pcie timeout, device tree gaps and bypass charging" -> the Fable
  debugger's queued bootfix task cancelled (it only finishes the R1 verification); the first bypass agent handed over
  and stopped; a NEW dedicated agent owns all three: wf/bootfix (A: PCIe L2 timeout + 14 probe deferrals + supplies;
  B: DT gaps vs stock + the NVT touch message) and wf/bypass (C: bypass in the battery guard + a Quick Settings toggle
  + polkit helper, the corrected accept.sh charge-limit check). Order: B quick items, A, C; it reports per topic with
  the build line (WF="bootfix") and a parts module.
- Run 95 (the owner's charging sitting) is generated and waits for the owner to connect the tablet and say go.
- Owner: "tablet connected" (battery 52 %, 25.2 C) -> run 95 (charging sitting) started.
- **Owner: "battery charge settings working fine (preserve, maximize charge) please commit"** (run 95, device package
  0.17 on q77 = queue 0166) -> charge-limit row confirmed by the owner; matrix-c2s (also: the headset row's sentence
  repeated 5x by matrix-c2p - c2p made idempotent -, the EFI row's queue range 0089 -> 0166, 145 test runs);
  BOOT-LOG-PLAN P1-a corrected (battery data via the SoCCP's pmic_glink, works without the ADSP - docs review); commit t.
- docs agent finished the drafts (wf/docs: PLAN, 01-07, GLOSSARY, INDEX; privacy check clean) + inconsistencies list
  (plan vs guide, firmware path OnePlus/iceland vs iceland, 90-iceland-dtb.install vs the GRUB devicetree line,
  iceland-u-boot README / uboot.pin, FEATURES stale bits, volume key mapping, stale HANDOVER / STATE / PROJECT
  blocks). Drafts to be reviewed, then committed under docs/guide/.
- User: "what else can be committed?" -> listed; "yes do 1-3 and skip this charge testing" -> run 95 stopped (log set
  fetched, tablet rebooted to Android, runner killed); (1) the docs drafts reviewed (privacy scan clean: no serial /
  BD / MAC / GUID; write commands only inside warning blocks) -> docs/guide/; (2) project knowledge: HANDOVER.md
  rewritten (21:00), STATE.md new status block, CLAUDE.md new rules, memory resume block; (3) the kits' module list
  -> tools/linux-ram/modlist-all.txt. Commit u + the project-folder snapshot.
- Commit u pushed: iceland-mainline **1c417e9** (docs/guide 10 files, HANDOVER, PROJECT-STATE, PROJECT-CLAUDE, modlist-all; 0 rpm / private / frames). Snapshot refreshed (save-project + fix + wf): privacy scan clean, 1080 files; workflows 521 files in 28 folders, 0 serial / address hits.
- **r1debug (Fable) finished**: the root cause confirmed independently (the env extracted from the failed image:
  `blkmap create rehearsal 4096`, bootcmd `fastboot usb 0`; the dispatcher returns CMD_RET_USAGE for 3 > maxargs 2;
  fastboot_bootcmd returns inside the USB completion -> do_exit_on_complete detaches the gadget -> prompt); reproduced
  exactly in a U-Boot sandbox; the rest of the path checked with the real head's values (644357 blocks, < 1 GiB, end
  0x95D505000 inside the 0x8C0000000 bank, LMB, the EFI boot manager on a 4 KiB GPT/FAT16 ESP). **The install
  agent's fix is correct: 15 / 15 in its sandbox.** Proposals: rehearse.ps1 busy detect (Fb-Count -eq 1 can be a
  busy U-Boot -> getvar product with 5 s), sandbox-check `< /dev/null` + a real GPT/ESP; first tablet step: the
  8 KiB notgzip head (proves fastboot_loop's USB re-registration in seconds). The dotted rectangle = unredrawn panel.
  Sent to the install agent: apply both patches first; then (owner connected) notgzip test, then R1.
- User: "change install tooling workflow to opus and rebase its knowledge from our document expert and r1 debugger"
  -> the running install agent asked to finish its current edit, write wf/install/HANDOVER-ROUND6.md and stop; then a
  new Opus install agent starts from that handover + the docs set (07-INSTALL-REVIEW, 03-BOOT-AND-PARTITIONS,
  02-HARDWARE) + wf/r1debug/REPORT.md and its patches + BOOT-LOG-PLAN, and may ask the docs SME and the r1debug
  agent directly.
- **hwfix topic B test-ready** (wf/bootfix, 7 items, BF_ITEMS="wcn bl dmic fastrpc mcq smem nvt"): wcn = WCN7860 PMU
  inputs as stock cnss-peach (vddaon L2G 1.8 V, vddcx S1J; L2G had no Linux vote; vddant stays dummy as stock),
  bl = ktz8869 vddio optional (stock has none), dmic = qcom,dmic-sample-rate 4800000 (the driver's fallback), fastrpc
  = stock's 12 MiB adsp_heap CMA region + vmids, mcq = UFS MCQ block 0x1da0000 + msi-parent (stock / upstream SM8650
  / SM8750), smem = backport of Konrad Dybcio's Glymur DRAM info (872 bytes) + the 1000UL fix, nvt = dev_err_probe.
  Left on purpose: SoundWire ports (same in every upstream dtsi since SM8550), SCMI FC (firmware refuses), PCIe
  supplies (stock has none; the 14 deferrals = pwrctrl waiting for pci-pwrctrl-pwrseq). Test part bfdt (4 min, reads
  only: UFS via dd of=/dev/null). Building **q79** = 0166 + bootfix; kit **96** (gen-combo-96.py: pkg2 + rotpkg start
  + bfdt, coldplug) for the FastRPC sensor-hub check.
- **q79** f183257aafb7 = 0166 + bootfix topic B, 0 compiler warnings, camdrv/sc1320cs-q79.ko; kit **96** generated (setup + coldplug, pkg2 0.17, rotpkg start, bfdt; AUTOREBOOT 2400) and checked. Waiting for the owner to connect the tablet.
- **Old install agent handed over** (wf/install/HANDOVER-ROUND6.md): rehearse.ps1 ready (8453bb0c..., r1debug's busy
  probe + 300 s wait), sandbox 13 PASS + 1 known gap (truncated gzip crashes unzip; hardening after R1); B1 / B2 / B3
  done in source -> P1 + TIN + the B run again (must show "policy loads 0"); R-1 confirmed on the PC against
  Qualcomm's public ABL source: a plain U-Boot on boot_b = INVALID_METADATA -> ABL stops (slot b unbootable); the
  footered one = PUBLIC_KEY_REJECTED (= LineageOS today) -> continues; AVB-PROOF PASS 12 cases (on the LineageOS build's
  images; rerun on today's after parta-read); R-2 confirmed; R-4 / R-5 / R-6 / R-9 misc check in the tooling;
  parta-read.ps1 (reads only, whitelist) + parta-check.sh (PARTA: READY FOR C0) ready, not run. Not started: guide
  C0 text, DUALBOOT-PLAN.md, R8 / R9 text.
- **New install agent on Opus** started from that handover + the docs set (07, 03, 02, 06) + r1debug's report and
  patches + BOOT-LOG-PLAN; may ask the docs SME and r1debug; tasks: re-verify (selfcheck, check-all), the command
  list for me (P1 + TIN, B run, notgzip test, R1, parta-read / -check), C0 + guide / plan fixes, DUALBOOT-PLAN.md,
  then the unzip hardening.
- Owner: "tablet is connected proceed" (battery 52 %, 24.1 C) -> run 96 (bootfix topic B on q79) started.
- **Run 96** (q79 = 0166 + bootfix B; coldplug, pkg2, rotpkg start, bfdt): **wcn, bl, dmic, fastrpc, mcq, audio PASS**
  (L2G 1.8 V now voted by vddaon; Wi-Fi 5 BSS on 2.4 / 5 GHz, BT up; MCQ 9 queues, 256 MiB O_DIRECT read 2.3 GB/s;
  FastRPC CMA 12 MiB + sensor hub fine; 6 / 6 amps, mics hear the tone); **smem FAIL** (DRAM info parsed - 3 DDR
  frequencies, line gone - but "hbb none" vs the table's 16: semantics asked) and **nvt "absent"** (the panel-wait
  line IS gone, touch + pen ok: the test's detection misses a built-in driver). kmsg vs run 92: the 8 targeted lines
  gone; new only the FastRPC reserved-memory info and pkg2's SELinux policy load into the kit; 0 WARNING / Oops.
  Sent to the hwfix agent; if smem is the test only, queue all 7 from q79's tree.
- **bootfix topic B GREEN (9 / 9 on run 96 after two test fixes)**: smem "hbb none" = the HBB field is 0 -> -ENODATA ->
  qcom_ubwc_config_get_data() keeps the table value 16 by design (no "Couldn't get HBB" line); the 872-byte layout
  proven by the parsed frequency plan (and 4780.8 MHz proves the 1000UL fix); nvt: the module is nt36536_ts.ko and
  carries the new string. q79 = exactly the 7 items (no l2diag). `queue-0167.sh` + .msg written (0167-0174: 8
  commits incl. the smem backport with its original author); waiting for the agent to fill in the backport's Author /
  Signed-off-by from its source, then DRY + queue.
- **Queued 0167-0174** (iceland-linux **a88cf03**, `queue-0167.sh`, tree = q79 fb8aadfc, QUEUE-VERIFIED; 8 commits;
  0172 = the smem backport with author Konrad Dybcio <konradybcio@kernel.org> from the mirror's From header; its
  Signed-off-by left out rather than guessed - the mirror redacts it, lore and patchwork sit behind an Anubis bot
  check that is not passed in an automated browser; the note says so). **bootfix topic B GREEN.**
- **hwfix topic A ready (diagnosis)**: not the controller - without WoW ath12k's suspend_late power-down does the WLAN
  SoC global reset; the reset WCN7860 never answers PME_Turn_Off, dw_pcie_suspend_noirq warns after 10 ms (upstream
  made it a warning for ath12k on SM8650-HDK) and continues (PERST#, pwrctrl powers WLAN off); on resume ath12k
  reloads its firmware (the QRTR lines). Stock keeps the WLAN firmware alive (CESTA DRV). The 14 supply pairs = the
  pwrctrl probe deferrals until pci-pwrctrl-pwrseq binds (installed-system fix: dracut add_drivers pwrseq_qcom_wcn
  pci_pwrctrl_pwrseq; for the install workflow). Test-only switch l2diag (ath12k suspend_soc_reset, never queued);
  part bfpcie: base / noreset / wow / nodrv s2idle variants. Building **q80** = 0174 + l2diag.
- **q80** 58e99054f8ce = 0174 + l2diag (ath12k pci.c only), 0 warnings; kit **97** (setup + coldplug, bfpcie; AUTOREBOOT 1800) generated + checked; waiting for the owner's go.
- Owner: "proceed" -> run 97 (PCIe L2 diagnosis on q80) started.
- **Opus install agent, task 1 done** (verified: selfcheck clean, check-all 14 PASS; B1 / B2 / B3 complete; NEW:
  touch accept check fixed, **B4 the run-94 golden had no GPU firmware trio (gen80200 sqe / gmu / aqe) in its
  initramfs** -> fw-list.tsv + 3 vendor items + accept `gpu`; the pwrseq add_drivers drop-in + accept `pcieprobe`;
  check-b-run.sh). Its full command list is saved in **docs/INSTALL-RERUN-COMMANDS.md** (copy rehearse.ps1 +
  parta-read.ps1, P1 + TIN, the notgzip test, the B run, R1, Part A read). **Owner decision open:** GPU firmware in
  the image = stock (GMU v5.3.39, default) or linux-firmware (v5.3.23, the kits' since pc-024).
- **User: "save state with our documentation expert since will need to compact"** -> HANDOVER.md state table and
  workflows updated (22:30: queue 0174, q79 / q80, the Opus install agent, r1debug finished, run 97 running),
  INSTALL-RERUN-COMMANDS.md, this entry, the memory resume block; the docs agent updates 01 / 03 / 06 / 07 / INDEX and
  writes RESUME-2026-10-02.md; then a commit + the snapshot. **Run 97 (PCIe diagnosis) is RUNNING at this point:**
  judge it from area-combo-97 and send it to the hwfix agent (ab01e21f3f346b12e).
- User asked the difference stock vs linux-firmware GPU firmware -> answered: same features; v5.3.23 (linux-firmware)
  carries every GPU / battery-life / deep-sleep result since pc-024, Fedora updates; v5.3.39 (stock) only proven to
  load and power up (pc-010 / pc-011), never rendered. **Owner decision: "go with linux firmware"** -> sent to the
  install agent (take them from Fedora's firmware package if it has v5.3.23+, else carry linux-firmware's files in
  the device package; the zap shader stays the tablet's; accept `gpu` expects v5.3.23).
- docs agent: the set brought to 22:30 (01 / 02 / 03 / 06 / 07 status per finding / INDEX / GLOSSARY / 04) + RESUME-2026-10-02.md; HANDOVER base config fixed to out-config-base-0174 everywhere; matrix-c2t (row Internal storage (UFS 4): MCQ, 2.3 GB/s; queue 0174; 147 runs / 88 kernels); commit v.
- Commit v pushed: iceland-mainline **26f71db** (docs/guide at 22:30 + RESUME-2026-10-02.md, INSTALL-RERUN-COMMANDS.md,
  HANDOVER / PROJECT-STATE / PROJECT-CLAUDE, run 96, queue-0167; 0 private files); matrix **v42** (62 / 12 / 5 / 2 of
  81, new row Internal storage (UFS 4)); snapshot refreshed (privacy clean).
- **hwfix topic C (bypass) test-ready**: run `bash ~/mainline/build/wf/bypass/apply-pkg.sh` once (refreshes
  wf/bypass/tablet-in), then `python3 ~/mainline/build/wf/bypass/cand/gen-combo-bypass.py N qNN` (setup, bypass,
  close) or bypass_parts.LINE["bypass"] (PT 600) after pkg2; any current kernel. Design: the battery guard (the only
  writer of charge_behaviour) gets bypass as one more STOP reason checked after the stock stops and the charge limit;
  holds the level with inhibit-charge (= stock oplus_chg_plc output_suspend), 1 % top-up, threshold from 20 %, ends
  at unplug / a 5-min lease not renewed / BYPASS=0 / a bad file, never restored after reboot; iceland-bypassd
  (D-Bus org.iceland.Bypass, polkit org.iceland.bypass.set for the active session); a GNOME Shell 50 QuickMenuToggle
  "Bypass Charging" (hold from 20-90 %), enabled by a gschema override; packaged as 0.19 on a copy of 0.18
  (cand/bypass-pkg.py, work/p19); PC tests: spec 147, units 22, guard 115 + 27 + 29, new guard-bypass 38, bypassd 25.
  Part `bypass` (~6 min): install, unit tests on the tablet, base, enable (screen-off PASS: battery <= +30 mA, input
  >= 100 mA), refresh, lease (20 s drop-in), limit (kernel end threshold lowered to SOC-2 for ~20 s, then restored -
  lowering only), disable, shell (gdm restart, extension ACTIVE, renews itself), restore. Owner tests with a wall
  charger: hold 30 min while gaming, unplug ends it, reboot does not restore, threshold above SOC charges then holds,
  screen lock ends it after 5 min, the toggle's look.

### 2 Oct 2026, about 23:30 - run 97 reset the tablet; bypass safety review; install steps 1-2

- **Run 97 (q80 = 0174 + test-only l2diag, part bfpcie): the tablet reset about 150 s into the PCIe s2idle
  cycles; no evidence reached the PC.** Setup was fine (kernel check ok, tools rc 0, coldplug 34 / 15). bfpcie
  started 21:13:34; the follow loop printed nothing after "== bfpcie" (the part writes its timeline line only at its
  end); SSH timed out; the tablet came back in LineageOS by itself (Android kernel start 21:16:26, boot reason only
  "bootloader"; battery 52 %, 23.4 C). So the reset was about 21:16:00-21:16:15 = roughly cycle 6-9 (base probably done,
  noreset or early wow running) - not proven. The same s2idle method (echo freeze + RTC alarm, qcom_stats,
  pm_debug_messages) passed in run 92 on 0166-level kernels; new in 97: the q80 kernel, a Wi-Fi scan between cycles,
  and the noreset / wow / nodrv variants. Chain stopped (TaskStop + the WSL probe killed by PID; TaskStop alone left
  the WSL probe running).
  **Lesson:** a diagnosis part that suspends or resets must write one timeline line per step and stay awake long enough
  for the probe to pull it, and risky variants go into separate parts with a log fetch in between - otherwise a reset
  loses everything. Also: the follow loop's timeout counts only its sleeps, so with SSH down PT=600 lasts about 40 min.
- Sent to hwfix (resumed): split bfpcie into one part per variant with a fetch between, a timeline line per cycle +
  about 15 s awake, check the stock DT for a ramoops / pstore region usable in a TEST-ONLY kit DT, and from the code
  which variant can plausibly reset the SoC. l2diag stays test-only.
- hwfix's final report (topics A / B / C): B queued (0167-0174); A = the diagnosis above; C bypass ready. Its notes: the
  14 vdda / vddpe-3v3 pairs need pwrseq_qcom_wcn + pci_pwrctrl_pwrseq in the initramfs (the install agent's 91 dracut
  drop-in already does this); the smem SoB address stays unverified (left out, as logged).
- **Owner: "spin another opus agent to verify battery bypassing making sure its safe for power and heat on the tablet
  before testing it on the device"** -> a new Opus safety reviewer (wf/bypasssafe, REVIEW.md): 7 items (only limits /
  the battmgr inhibit path / persistence after a crash or reboot / heat vs normal charging / drain at the 500 mA port /
  the test's floors, ceilings and restore traps / lease and polkit), a GO / NO-GO for the first PC-port test. **The
  bypass kit waits for its GO.** No tablet actions, no builds, no commits; it does not edit wf/bypass.
- Install agent: B4 now uses Fedora's own qcom-firmware trio (20260309-1.fc44 / 20260916-1.fc44 carry
  gen80200_{sqe.fw,gmu.bin,aqe.fw}.xz, byte-identical to build/fw-gpu = linux-firmware, GMU v5.3.23); the 90 dracut conf's
  install_items point at /usr/lib/firmware/qcom/*.xz (the updates/ paths never existed = run 94's dracut-install
  ERROR); fw-list.tsv back to 23; zap + touch stay the tablet's own. **C0 safety fix:** ABL gives the TEE the
  footer's os_version AND security_patch (else the boot header's) - the round-6 footer had only os_version, so the TEE
  would have seen U-Boot's 16.0.0 / 2026-08; mk-footer.sh now copies both from today's boot_b, avb-proof.sh checks
  `rot-equal`. INSTALL-RERUN-COMMANDS.md corrected (hashes, 23 items, gpu PASS text, rot-equal).
- **Install steps 1-2 done (PC only):** rehearse.ps1 8453BB0C + parta-read.ps1 836EBA64 copied to C:\platform-tools
  after a scan (only whitelisted reads: getprop, bootctl get / is-*, blockdev, pull / dd if=, getvar, reboot);
  old rehearse.ps1 kept as rehearse.ps1.old-1be32e60. Step 2: NEXT-K2P1U1 2 PASS 0 FAIL, 91 conf 2, 90 conf gmu.xz 1,
  accept.sh 7b828177...3881.
- **Install agent finding (ABL source): the A/B retry counter.** Flashing boot_b resets slot b (successful 0, retry
  MAX); every normal boot of a not-successful slot counts down (not recovery / fastboot / charger boots); at 0 ABL
  marks b unbootable and goes to slot a (case B) or fastboot (case A); only Android marks a slot successful. So a
  permanent U-Boot in boot_b would run out after MAX power-ons unless OnePlus's ABL differs. C0 measures it (hard stop
  at retry <= 2, then the undo; LineageOS marks b successful again). Fallback (OWNER DECISION later): U-Boot in
  recovery_b (never counts down), optionally misc BCB "boot-recovery" to make Fedora the default; a GPT attribute
  write on LUN 4 is rejected (no EDL loader). Routed to the docs SME (03-BOOT-AND-PARTITIONS, R-9).
- **Install step 3 PASS (owner: "yes"), 21:35-21:36:** notgzip U-Boot test via rehearse.ps1 8453BB0C, NBD stage0
  read-only. ABL (canoe, unlocked, slot b, 3922 mV) -> U-Boot 2026.10-rc5-00021 fastboot in 3 s -> head 7e73dd63
  sent -> "=== rehearsal head FAILED: the head is not gzip - back to f[astboot]" (the console line is cut at the
  64-byte fastboot INFO limit) -> fastboot reboot -> Android back after 20 s; relay refused 0; exit code 2; nothing
  written. Results in wf/install/work/t/rehearsal-*-213537 (sent to the install agent). NBD server stopped.
- **Install step 4 = run 98 started about 21:40 (owner: "yes")**: `genwf-install-b.py 98 q78 "rr dev b1a b1b b2a b2b"
  4300 qos=2`, NBD `serve stage0 build` (ov-build removed first), tcp-relay + linktest-server on Windows (auto ->
  0.0.0.0), chain area-combo-98-chain.sh (= 94's, -Wait 4000), run-chain MAXN=480. Agents asked to keep WSL light.
  Afterwards: check-b-run.sh area-combo-98, REFUSED in tcp-relay.log, stop the relay, rehearsal-pc.sh stop.
- **hwfix: bfpcie re-run ready** (wf/bootfix only): parts bfpcie-base / -noreset / -nodrv / -wow (markers
  BFPCIE-<V>-DONE, PT 600, a log fetch after each part), one sayk timeline line per cycle, then awake until the USB
  gadget is configured again (max 45 s; Windows needs about 27 s per resume) + 15 s; 3 cycles (wow 2); the generator
  raises AUTOREBOOT_AT to 3600 for several parts. Kernel q80 reused. Its code reading: l2diag at default 1 = 0174
  exactly; suspects in order wow (MHI M3 with MSI live while PERST# / PHY / GDSC go off: an MSI into an unclocked DBI =
  bus hang -> watchdog), then the topic B items exercised in s2idle for the first time (UFS MCQ ESI vectors re-enabled
  before the UFS clocks on resume; L2G / S1J switched by pwrseq), then noreset, then nodrv. Test-only bisect items in
  reserve (only if base resets): nomcq (t1-nomcq.py), wcnold (t2-wcnold.py). Run 99 after run 98, with the owner's go.
- **pstore lesson:** the kits already stream kmsg into pmsg (ramoops@affe00000, PMSG_ANDROID=1); after a WARM reset
  LineageOS shows it as /sys/fs/pstore/pmsg-ramoops-0 (adb root = Rooted debugging) - read it with
  /proc/bootloader_log BEFORE anything reboots the tablet. Run 97's zone was lost when the step-3 test rebooted at
  21:35. Limits: the copier is frozen during suspend; a watchdog / TZ hard reset cold-boots DDR (empty). Test-only
  idea kept in reserve: one console zone (printk writes it), no_console_suspend, panic=5 panic_on_oops=1.
- **DUALBOOT-PLAN.md (plan only; owner: no dual boot for now) reviewed by the docs SME, closed:** recommends a
  `fedora` partition carved from userdata + U-Boot in recovery_<slot>, probe DB-P1 first. The install agent took in
  the 4 review points (sha 76e4fcbd...): only `boot*` flashes / erases reset a slot's flags (open ABL FastbootCmds.c),
  so a recovery_b flash leaves slot b alone; Power + Volume Up -> recovery unverified until DB-P1 (certain: adb reboot
  recovery, LineageOS "Restart to recovery", fastboot reboot recovery); a size check in ABL between the GPT write and
  the wipe; an owner box with the "decide before write 1" deadline. To adopt into docs/ at the next save:
  wf/install/proposed/INSTALL-GUIDE.md + INSTALL-PLAN.md, DUALBOOT-PLAN.md, wf/docs -> docs/guide.
- **Install agent round 7 texts ready (to adopt into docs/ at the next save):** proposed/INSTALL-GUIDE.md (98a0760e...:
  0.5 the slot counter; Part C0 = C0.0 optional read-only RAM probe of the install U-Boot, C0.1-C0.8 with the flags read
  after the flash and each boot, hard stop at `slot-retry-count:b` <= 3 or slot a / unbootable / a verified-boot error,
  undo, parta-read again; Part D only if C0 showed no countdown), proposed/INSTALL-PLAN.md (384f33bd...: 23 edits -
  R-1..R-4, 5.0 C0, 5.2 the counter + recovery_b fallback as the owner's choice, G13 closed, G15 / G16 new),
  DUALBOOT-PLAN.md (76e4fcbd...). New read-only tool cand/rehearsal/uboot-ram-probe.ps1 (6196f472..., whitelist test 23
  PASS; `-WaitPowerOff` needs the owner present). iceland-mainline's 90-iceland-dracut.conf needs the .xz trio paths
  when 0.18 is committed. Waits for: run 98's check-b-run.sh, then R1, then "WSL free" for the unzip hardening.
- **Run 98 (install step 4, B run) = B-RUN: 18 PASS, 1 FAIL** (21:42-21:48; the probe then rebooted the tablet to
  Android as planned - the owner saw that reboot; it was not a crash). PASS: rr gate (+down slowest 156 ms), devrpm
  (0.18 rpm built in 19 s), 91 conf omits the root-firmware drivers, build1a / 1b / 2a / 2b each "policy loads 0" +
  "disk released", firmware 23 ok / 0 differ, bdaddr yes, NBD 31 / 38 MB/s, no dracut-install error, initramfs with
  Fedora's GPU trio + zap + touch + PCIe power control and no root-firmware driver. **FAIL: 16 SELinux policy lines in
  the kit's kernel log at 18:42:44 tablet time = inside the dev / devrpm part** (after rr 18:42:27, before devrpm's line
  18:42:49): the B2 fix covers the build parts' chroot but not devrpm's tools install. Sent to the install agent: fix
  devrpm, say whether run 98's golden is usable for R1 or the B run must be repeated. Servers stopped (NBD, tcp-relay,
  linktest; REFUSED 0).
- After the run: `adb root` works (Rooted debugging is ON); /sys/fs/pstore empty; /proc/bootloader_log "Reset by
  PSHOLD / Hard Reset / ddr_init cold boot" - the same as any reboot from Linux, so it cannot tell a panic from a
  planned reboot.
- **Owner: "do the read only backups then run99".** Part A (install step 6, parta-read.ps1 836EBA64, 21:51-21:55,
  Rooted debugging ON): **PARTA: NOT READY (1 STOP)**, nothing written. STOP = check-header.py: the install U-Boot's
  boot header still carries the old uboot.pin values while today's boot_b header is 17.0.0 / 2026-09 -> rebuild with
  the stock values (folded into task 4, the unzip hardening, one hash change). PASS: AVB-PROOF all cases + rot-equal
  (footer 17.0.0 / 2026-09-01), candidate for today's boot_b (rollback index 1788220800), ABL unlocked, slot b current /
  successful / not unbootable, boot_b 100663296 bytes, misc 'bootonce-bootloader', vbmeta_b chains boot (location 4),
  rehearsal build refused for boot_b. **New slot facts:** slot b retry count 6 (docs said 5); **slot a successful yes,
  UNBOOTABLE yes**, retry 6 -> if slot b ever runs out, ABL finds slot a unbootable and stops in fastboot (case A),
  not a switch to slot a (case B). Sent to the install agent (+ the run 98 questions, + the owner's boot_a question).
- Owner asked what is in boot_a / what if U-Boot went there. Read on the tablet (root, reads only): boot_a and boot_b
  carry the identical LineageOS GKI kernel 6.12.81-android16-6 (kernel sha 4d3ec9fd736d), header v4 17 / 2026-09; they
  differ only in the AVB footer (boot_a security_patch 2026-08-01 = the 28 Sep install build; boot_b 2026-09-01 = the
  29 Sep OTA); all of slot a's boot set differs from slot b's. From the open ABL source: a boot_a flash resets only slot
  a's flags (name-derived suffix), stays dormant without set_active a (which also switches the UFS boot LUN), counts
  down on slot a, falls back to slot b's LineageOS at 0; LineageOS OTAs would overwrite it.
- **Run 99 started about 21:57** (q80, parts setup, bfpcie-base, -noreset, -nodrv, -wow, close; AUTOREBOOT_AT 3600,
  runner -Wait 3300, run-chain MAXN=420).
- **Install agent: devrpm SELinux leak fixed (PC-proven); repeat the B run before R1.** Cause (run 98's devrpm/dnf.txt):
  devrpm installs rpm-build into the kit's OWN root; the transaction pulled policycoreutils + rpm-plugin-selinux +
  selinux-policy-targeted 44.10, whose scriptlet loaded the policy at 18:42:44. Fix in tablet.sh (4dce3b15...): nosel()
  = own mount namespace with an empty read-only tmpfs over /sys/fs/selinux (fails closed rc 125 without unshare); devrpm's
  dnf, its rpm build and the kit-root nbd install go through it; devrpm now reports "policy loads N". test_nosel.sh 9
  PASS (in check-all, 15 PASS); check-b-run.sh c5819fd4... also requires devrpm policy loads 0. Run 98's golden is
  probably fine functionally but failed the clean-build criterion -> B re-run (~7 min, parts "dev b1a b1b b2a b2b").
- Header pin: mk-uboot.sh now takes the header OS version / patch level from today's boot_b pull (same source as the
  footer), falls back to uboot.pin; folded with the unzip headmax bound into work/r7/stage-unzip-headmax.py.
  **TODO at the next commit: update iceland-u-boot's uboot.pin (17.0.0 / 2026-09 + comment).**
- Order after run 99 (WSL free): PC: stage-unzip-headmax + mk-patches + `STEPS="u1 tin" next-k2p1u1.sh` (2 PASS, header
  "17.0.0 / 2026-09"), parta-check.sh on the 21:51 pull (READY FOR C0), selfcheck + check-all. Tablet (owner's go each):
  B re-run, R1 (new rehearsal U-Boot), Part A again on the C0 day, C0.0 (optional), C0 (owner's write).
- Slot facts in the proposed guide / plan (guide 7fb75056..., plan be042a98..., DUALBOOT-PLAN 9a383a09...): slot a
  successful + unbootable -> exhaustion of slot b ends in ABL fastboot (case A); case B cannot happen today; C0 stop
  rule (retry <= 3) kept as margin. boot_a added to DUALBOOT-PLAN 2.2 as row (d3'), rejected (Fedora expires after a
  few power-ons; set_active from the PC each time), not decided.
- **Run 99 (q80, split bfpcie): base 3 / 3 fine, noreset RESET the tablet in cycle 2; nodrv / wow did not run.** Base
  (switch Y): L2 timeout every cycle (LTSSM 0x12), cx collapsed 2 / 3, Wi-Fi back 3 / 3 (5 / 3 / 3 networks), qrtr 2,
  hard 0, noirq suspend ~46 ms / resume ~318 ms, fw-reload 3 per cycle; boot: 13 probe attempts, link up 45.08 s =
  pwrseq / pwrctrl insmod. -> **the q80 = 0174 kernel incl. the topic B items (MCQ, WCN supplies) survives s2idle**.
  noreset-1: no L2 timeout but wall 26.6 s (irq 272), noirq resume 1077 ms, Wi-Fi scan 0, **9 hard lines**; then the
  reset (Android kernel 22:02:42; bootloader_log "Reset by PSHOLD / Hard Reset / PON by RTC + SYSOK", cold boot; pstore
  empty although read first). noreset is no fix candidate. Base log set fetched (area-combo-99/combo/bootfix/pcie);
  chain + WSL probe stopped. Sent to hwfix: are nodrv / wow worth a run (no reset without a clear question), else the
  write-up for keeping upstream's 10 ms warning.
- **hwfix topic A verdict (from run 99): keep upstream's behaviour - green, no kernel change; nodrv / wow not run.**
  noreset proved the root cause: without the WLAN SoC reset the WCN7860 DOES acknowledge PME_Turn_Off (0 timeouts),
  with it (base) it never does (3 / 3, LTSSM 0x12) -> the warning comes from ath12k's own power-down in suspend_late
  (upstream design for suspend without WoW, same as SM8650-HDK). Dropping the reset breaks the next resume (noreset-1:
  noirq resume 1077 ms = the whole dw_pcie link-wait budget + power-up, i.e. no link; wake by the root port's WAKE#
  GPIO, irq 272 = msmgpio 104) and then hung the bus (PSHOLD reset; likely the AON rail kept up by Bluetooth so the
  un-reset chip does not link-train) - not proven, the 9 lines are lost. Costs of the kept path: 10 ms L2 poll in a
  45.5 ms noirq suspend; noirq resume ~318 ms (D3cold spec waits); early resume ~609 ms (one firmware reload - the
  counter's "3" were three lines of ONE reload); "suspend exit" ~2.2 s after the wake; Wi-Fi back every cycle. l2diag
  stays test-only (or dropped). wow only if the owner wants Wi-Fi kept connected in sleep (needs credentials + the
  ramoops evidence kit). Matrix: "PCIe L2 warning at suspend: expected, upstream behaviour".
- New observation for the pencharge / sleep topic (not bootfix): base-1's s2idle was aborted by "PM: Triggering wakeup
  from IRQ 316" (cx +0, wall 4.5 s) and that first suspend's "suspend of devices" took 2250 ms ending with the mt5806
  pen charger's "transmitter looking for a pen" -> identify IRQ 316, check mt5806's suspend on the first suspend after
  boot. Cosmetic upstream nits left: QRTR "failed to announce" in 2 / 3 resumes; "hwmon: parent phy0 should not be
  sleeping" after each resume. The 13 probe deferrals = initramfs order (install workflow's 91 drop-in).
- **Install round 7b PC steps (after run 99, WSL free): NEXT-K2P1U1 1 PASS 1 FAIL (U1).** Both U-Boot builds compiled
  (headmax 0xc0000000, header values from today's boot_b), but the u-boot check failed 1: the sandbox's new
  truncated-gzip case (inflate() -3, then "Address not mapped: 0x11401000 / 0x13400000" instead of the FAILED line and
  fastboot); the other 12 sandbox cases PASS. TIN PASS; parta-check on parta-20261002-2154 still STOP on check-header
  (no new install image), rot-equal + AVB proof PASS; selfcheck clean (117), check-all 15 PASS. Sent to the install
  agent: sandbox setup or a real bug in the bounded-unzip path?

### 2 Oct 2026, late - Windows on ARM: plan written (planning only, a separate session)

- **Owner: "create a proper plan for porting windows on arm to the pad 4, you can use similar devices as a
  reference".** Result: `docs/WINDOWS-PLAN.md`. PC reading and web research only; no tablet action, no build, no
  commit, nothing sent upstream.
- Facts found (web, 2 Oct): Mu-Silicium has `KaanapaliPkg` + `infinitiPkg` (OnePlus 15) since v3.3 (March 2026): UEFI
  display / UFS / buttons / USB device ok, USB host and PD no, Linux boot yes, **Windows boot no**; its ACPI line is
  commented out and Silicium-ACPI has no tables for Kaanapali, Pakala (SM8750) or Lanai (SM8650). No 8 Elite /
  8 Elite Gen 5 device boots Windows; 8 Gen 3 phones reach Windows PE only. The only relative with Windows drivers
  is the X2 Elite (Glymur, SC8480XP; Windows 11 26H1 build 28000). No Windows driver set for SM8850 is public.
- The plan: W0 facts on the PC (UEFI driver set from the backup, memory map, a write-path audit of the UEFI build,
  the X2 Elite driver / ACPI mapping), W1 UEFI from RAM (`icelandPkg`, no mass storage, UFS read-only, variables in
  RAM, a session watchdog), W2 Windows PE to a prompt (ACPI from our device tree, kernel debugger over USB as the log
  stream), W3 Windows' generic drivers, W4 X2 Elite driver experiments with stop rules, W5 install not planned.
  Estimates: UEFI 85 %, Windows PE prompt 50 %, storage 35 %, touch 15 %, a usable Windows under 5 %.
- Open owner decisions (plan section 11): start W0 now or after the install work; OK to ask the Mu-Silicium
  maintainers; a private repository; Wine + FEX on Fedora as its own workflow. Next step if "go": three PC-only
  workflows `winuefi`, `winacpi`, `winkit`. The file is in the project folder only: copy it to WSL / the docs repo
  at the next save.
- Install agent: the U1 failure was its sandbox bound (headmax 0x8000000 let the runaway inflate overwrite the
  sandbox's own U-Boot data at ~0x9bb9c90), not the tablet path (bound [0x8C0000000, fbaddr 0x980000000), U-Boot's data
  at ~0xAEF000000+). Fixed: sandbox headmax 0x4000000 + a guard test (sandbox-check.sh 1967ed2f...).
- **Round 7c PC steps green (22:10-22:16):** U1 PASS (u-boot check 41 PASS; header "17.0.0 / 2026-09 (uboot.pin is
  overridden)"; sandbox 0 failures incl. the truncated-gzip case); parta-check on parta-20261002-2154 **PARTA: READY FOR
  C0** (check-header PASS, rot-equal PASS, new footered sha); selfcheck clean; INSTALL-PC-CHECKS 15 PASS.
- **Owner: "yes run the build run after the rebuild"** -> run 100 started about 22:18: `genwf-install-b.py 100 q78
  "dev b1a b1b b2a b2b" 4300 qos=2`, fresh ov-build, tcp-relay; tablet-in tablet.sh 4dce3b15 (nosel).
- **Run 100 (B re-run, 22:18-22:25) = B-RUN: 20 PASS, 0 FAIL** - the clean golden. devrpm "policy loads 0 (its tools
  went in through nosel)", every build part policy loads 0 + disk released, firmware / bdaddr / uuids, no dracut-install
  error, initramfs with Fedora's GPU trio + zap + touch + PCIe power control and no root-firmware driver, **no SELinux
  policy load in the whole session**. The probe rebooted the tablet to Android as planned. NBD + relay stopped,
  REFUSED 0. Next: R1 on this golden (owner's go).
- **Bypass safety review (Opus, wf/bypasssafe/REVIEW.md): feature SAFE; NO-GO for wf/bypass/tablet.sh, GO with
  cand/tablet.sh.** The original test could RAISE the charge limit (at 90 % with 80 / 85 it wrote end 88 / start 83),
  had no battery floor / temperature ceiling / restore on interrupt, a GetState that could hang to the kit's
  auto-reboot, could leave charging inhibited (sim: 18 of 62 FAIL; fixed 62 / 62 x3). Fixed test G1-G6: start at >= 30 %,
  battery 5.0-44.9 C, USB-C < 54 C, charger online; abort + restore < 20 %, 45 C, USB-C 54 C, input over limit +15 % +50 mA
  x3; traps + watchdog + timeouts; limit step lowers the end threshold only, never writes start; charge_behaviour back
  as found. Guard gaps (S1-S3, guard_safety_patch.py, test 12 / 12): release a bypass-only hold when the guard stops;
  bypass faults contained; request read as bytes, finite lease only. inhibit-charge = the stock bypass firmware command;
  any reboot clears it. Main session read the corrected test's writes (lower-only end threshold, restore to found).
- **Owner decision: "leave bypass out for now as a feature mark it as to be added later".** Bypass charging is
  DEFERRED: no kit run, no 0.19 package, not in the installed image (the install workflow stays on 0.18). Kept for
  later, unchanged: wf/bypass (the feature, 0.19 patcher, tests) and wf/bypasssafe (REVIEW.md, the corrected
  cand/tablet.sh, guard_safety_patch.py + its test, the simulation). When it is picked up again: adopt the review's
  section 5 (corrected test + S1-S3 guard fix) first, then the PC-port test with the owner's go, then the wall-charger
  checks W1-W8. Matrix: bypass = to be added later.
- Owner: "but would we need to fix the guard even if we didn't add bypass?" -> the review's S1-S3 are bypass-only (the
  0.18 guard has no bypass code); one PRE-EXISTING gap applies to normal charging: at a USB-C connector-temperature or
  input over-limit stop the guard can only inhibit charging, the system load still flows through the hot connector,
  while stock opens CC / suspends the input / discharges VBUS (oplus_mms_wired.c:2701-2741). **Owner: "yes spin a
  fable agent to tackle both follow ups"** -> new Fable agent "chgsafe" (wf/chgsafe): (1) a desktop notification at
  guard USB-C / input stops, (2) a stock-exact input-suspend lever in qcom_battmgr used by the guard (limit-only,
  USB-data impact, low battery, reboot / unplug / guard-death fail-safes), kernel + package candidates, a RAM kit test.
- Docs adopted into the project folder (for commit w): docs/INSTALL-GUIDE.md (7fb75056), docs/INSTALL-PLAN.md
  (be042a98), docs/DUALBOOT-PLAN.md (9a383a09) from the install agent (old ones in the scratchpad's docs-before-w);
  wf/docs/03: hard stop "3 or less" (was 2), the slot facts of Part A (b retry 6; a successful + unbootable -> case A),
  Power + Volume Up "open ABL, not yet seen on this tablet".
- **Owner: "yes go ahead and r1"** -> R1b started about 22:33: run 100's build overlay committed into the golden
  (156844 blocks), `serve golden r1` (fresh overlay), head "enforcing=0" (head-20261002-223228); run 100's leftover kit
  runner stopped; rehearse.ps1 -Yes (log C:\platform-tools\r1b-rehearse.log) + rehearsal-probe.sh accept
  (area-install-r1b, ACCEPT_SUSPEND=0) side by side. Battery 52 %.
- **R1b: booted, then HUNG - the USB link dropped 5 s after the NBD root connected; nothing written.** rehearse.ps1:
  22:34:13 U-Boot fastboot, 22:34:32 head (470 MB) sent in 19 s, 22:34:49 "the rehearsal system answers on
  172.16.42.1 after 36 s". relay.log: 22:36:42 NBD connect from 172.16.42.1, 22:36:47 closed after 5 s
  (ConnectionAbortedError "aborted by the local system" = the Windows NCM interface went away), no reconnect. Then
  Windows' UsbNcm adapter Up again with only 169.254.15.70 (APIPA) and reset counters = the gadget re-enumerated without
  the tablet's IP. Owner saw Fedora's boot splash spinning, then frozen. The tablet rebooted itself (Android kernel
  22:39:29; "Reset by PSHOLD / Hard Reset / SYSOK", cold boot = hung_task_panic + panic=10), pstore empty. Probe + NBD
  stopped. Sent to the install agent: find what resets the USB gadget ~5 s after nbd-client connects (role-switch /
  typec / ucsi / pmic_glink modules in the golden's initramfs?) and the 2-min gap before the connect; next R1 with
  evidence (netconsole to the PC from the initramfs and/or a head without plymouth / quiet + the webcam). Lesson: on
  this tablet every Linux-initiated reboot is a PS_HOLD hard reset (cold DDR) - pstore is no tool for kit crashes.
- **Owner: "take the help of a fable agent as well to review the install agent and work on fixes basis on logs"** ->
  r1debug (Fable, resumed) reviews the rehearsal design (carrier, dracut confs, nbd resilience, the golden's initramfs
  modules vs the kit's mods25 order) and the R1b logs, proposes fixes + the evidence kit as candidates in wf/r1debug;
  the install agent stays the owner of wf/install and also reports independently (two views).

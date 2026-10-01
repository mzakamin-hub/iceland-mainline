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

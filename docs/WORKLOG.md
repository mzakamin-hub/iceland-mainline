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

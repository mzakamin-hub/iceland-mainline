# Feature matrix audit, 13 Oct 2026 (PC only, read-only)

Scope: every `part` / `todo` row and every `Fixing:` / `Add:` / `Tune:` item of
`~/mainline/gh/iceland-mainline/docs/features/features-data.py` at 488c469 (pulled 13 Oct; 104 rows: 79 ok, 16 part,
6 todo, 3 out). Owner checks of ok rows are listed only where they duplicate another row or became stale.
Nothing was run on the tablet; no repo file was changed.

Evidence (newest wins):
- Loop 5 `R138-TRACKER.md` (to 13 Oct ~01:10) and `WORKLOG.md` tail (to 13 Oct ~02:40, the owner's merge of N1-N4
  into B146), `STATE-2026-10-12-1400.md`;
- run logs r141 / r141u / r141ub, r142 / r142b, r144-r147, r148c, r150 / r150b, r151, r152, r153;
- main `WORKLOG.md` tail, `docs/TIMETABLE-B146-2026-10-12.md` (incl. the 02:10 and 02:40 adjustments),
  `MATRIX-AUDIT-2026-10-12.md`, `SOUND-PLAN-2026-10-12.md`, `QUALCOMM-LINUX-KERNEL-2026-10-12.md`,
  `AUTOMATE-FINAL-2026-10-12.md`;
- `~/mainline/gh/iceland-linux` (origin has `iceland-7.3-rc6-q89d8` and `iceland-7.3-rc6-q89d9`, tags `q89d8` and `q89d9`;
  no q89e yet), `~/mainline/gh/iceland-firmware` (tags 11.A.38-2 and 11.A.38-3, 70ea8f1), `wf/rc7`, `wf/b146`
  (0.28-4 tgz built; check-b146.sh covers fetch, BRIGHTNESS=0, no random seed, N4), `wf/n2mic`, `wf/n3rng`, `wf/n4gst`.

Classes: DONE, IN PROGRESS, STALE, DUPLICATE, REGRESSION-RISK, OPEN-VALID (priority high / med / low; owner = needs
the owner's hands, eyes or OK).

**Scope change to note.** The brief lists N1-N4 as "after B146". The newest evidence (Loop 5 WORKLOG ~02:40 and the
TIMETABLE's "Owner change ~02:40") says the owner merged N1-N4 INTO B146 and its single confirmation run r155. Each
has its own switch and is dropped from B146 if its agent reports a blocker. Only the ktz8869 clamp, R2 and the
libcamera 0.7.1-2 adoption stay after B146. The table names both rounds where this matters.

## 1. Items

| # | Row / item | Class | Evidence | Suggested wording |
|---|---|---|---|---|
| B0 | U-Boot (ok) - Owner check: decision 3, the permanent boot path | DUPLICATE of B10 | same decision as the Fedora-installed row | "Owner check: decision 3 (see Fedora installed on the tablet)" |
| B1 | Linux 7.3-rc6 - Add: the rebase onto v7.3-rc7 / v7.3 "when tagged" | STALE (now IN PROGRESS, B146) | v7.3-rc7 is tagged (24a19b953e2a; QUALCOMM-LINUX-KERNEL doc); q89e rebase running in wf/rc7 (build / check / manifest scripts dated 12 Oct 23:43); owner 13 Oct ~01:45 "both in same step" means B146 is built on q89e | "Fixing: q89e = q89d9 rebased onto v7.3-rc7, merged patches dropped, the r2t breakers kept out (B146, confirmation r155 vs r141)" |
| B2 | Linux 7.3-rc6 - Add: push the q89d9 branch and tag | STALE (done) | origin/iceland-7.3-rc6-q89d9 a2c12cb + tag q89d9 50726cc pushed 12 Oct 13:1x (Loop 5 WORKLOG S6; `git branch -a` / `git tag` in iceland-linux) | drop; notes: "q89d8 and q89d9 branches + tags pushed" |
| B3 | Hardware watchdog - Tune: suspend_late stall | OPEN-VALID low, no owner | only the installed system suspends; rehearsals never do | keep |
| B4 | Memory bus DVFS - Tune: measure the power saving | OPEN-VALID low, no owner | nothing since kit 135 | keep; run it with N1's rail-telemetry idle measurement |
| B5 | Hardware RNG - Add: a rate-independent RNG row | DONE | RN row PASS in r142 and r141u: smccc_trng 131,072 bytes, 52 FIPS 140-2 blocks, 0 failed, chi2 261.8 (255 dof), crng ready. N3 now only moves the row into the full set (r155) | next "Nothing (RN in the regression set from r155)"; notes: replace the kit 119 numbers with r141u's |
| B6 | SCMI CPUCP cold soak (part) - Owner check: cold-soak start + load | OPEN-VALID med, owner | no cold-soak test logged | keep |
| B7 | Firmware package (part) - Add: fetch from the repo's releases with an sha256 pin | STALE (proven; ships in B146) | r153: fwfetch 12 rows 0 FAIL (FF1, FF3-FF7 PASS; FF2 CHECK = slow GitHub link only); helper in iceland-device 0.28-4 (wf/b146/pkg) | "Fixing: 0.28-4 ships the fetch helper (proven r153) and B146 carries 11.A.38-3 (r155)" |
| B7b | Firmware package - row status part | DONE (status ok) | package in golden B145, r143 / r145 / r141 FP1-FP4 PASS, public repo with releases 11.A.38-2 and 11.A.38-3 (11.A.38-3 = the decoded generic thermal model; r153 FF6 PASS: owned, sha = MANIFEST, iceland-thermal reads it) | status ok; notes add 11.A.38-3 + r153 |
| B8 | Fedora installed (todo) - Owner check: accept or drop the random-seed FAIL | IN PROGRESS (B146) | owner chose "drop" (Loop 5 WORKLOG ~22:45 item 5); B146 = "no random-seed", checked by check-b146.sh; image rebuilt from B146 (TIMETABLE step 8) | drop the item once the B146 image's offline check passes it |
| B9 | Fedora installed - notes / next wording | STALE | candidate is still "golden B145"; next repeats "then the two writes (docs/INSTALL-GUIDE.md)" twice. The held B145 image also carries 0.28-3's brightness fight (r151 case A FAIL), so it must not be the image the owner writes | notes: "Candidate: golden B146 (q89e + 0.28-4 + iceland-firmware 11.A.38-3, no random-seed) after r155; the install image is rebuilt from B146 and held (the B145 image is superseded)"; next: "Owner check: decision 3 (boot path), backups G4 / G5, then the two writes (docs/INSTALL-GUIDE.md)" |
| B10 | Fedora installed - Owner check: decision 3, backups, the two writes | OPEN-VALID high, owner | unchanged; writes are the owner's only | keep (master item for decision 3) |
| B11 | Boot slot marked good (part) - Owner check: first real run | OPEN-VALID med, owner (after install) | I1 PASS r139b, r139c, r141 | keep |
| B12 | Dual boot (todo) - Owner check: decision 1 | OPEN-VALID low, owner | unchanged | keep |
| B13 | Gunyah (todo) - Add: SuperTurtleDev's import later | OPEN-VALID low, no owner | not carried | keep |
| B14 | Native display - Fixing: (watch) DPU vblank timeout / commit done -110 during the idle dim | OPEN-VALID low, no owner | 0 lines in r139c and r141 (GP3 PASS), but since r141 every rehearsal holds an idle inhibit for the whole run (PV), so the idle dim that triggered it (r139b) is no longer exercised | "Fixing: (watch) the DPU lines during the idle dim - 0 in r139c / r141, but rehearsals now inhibit idle; needs one deliberate idle-dim row" |
| B15 | Refresh - Tune: seamless switching; tb323fu 0110 later | IN PROGRESS (N1, merged into B146 / r155 if licence + seamless checks pass, else after B146) | TIMETABLE "Owner change ~02:40": rc7 agent += N1 (0110 on top of the rebase, licence first, seamless only, separable); 0110 not in up3-qd7-bt84 | "Fixing: N1 lower idle refresh (tb323fu 0110, seamless only, rail-telemetry gain) in B146 / r155 or the next round" |
| B16 | Backlight - Tune: the brightness curve against stock | OPEN-VALID low, no owner | no work logged | keep; do it in the ktz8869 clamp round (same driver) |
| B17 | Smooth window moves (part) - Tune: "together with the thermal policy choice" | STALE wording (item OPEN-VALID low) | the policy choice is made: stock 60 / 61 C + 20 gears (r150 / r150b) | "Tune: frame timing of window drags idle and under an all-core load on the stock thermal policy" |
| B18 | Pogo keyboard (part) - Owner check | OPEN-VALID med, owner | unchanged | keep |
| B19 | Auto-rotate - Add: report the GNOME bug upstream | OPEN-VALID low, owner's OK | unchanged; owner 12 Oct "don't patch it upstream" covers patches, a bug report still needs the OK | keep |
| B20 | GPU correctness - Tune: single-worker dEQP / WebGL rerun on Mesa 26.2.4; Mesa report | OPEN-VALID low (report = owner's OK) | dEQP last on older Mesa | keep |
| B21 | Video decoding - Fixing: GStreamer V4L2 colour patch for SD BT.601 | IN PROGRESS (N4, merged into B146) | r147 / r141u VE-601 CHECK (not negotiated by stock 1.28.8); wf/n4gst holds the patch + a Fedora gstreamer1-plugins-good rebuild; check-b146.sh checks GST_REL | "Fixing: N4 - a Fedora-superseded gstreamer1-plugins-good with the colorimetry patch (B146 / r155, VE-601 bit-exact)" |
| B22 | Video decoding - Add: the same fix upstream (owner's OK) | OPEN-VALID low, owner (on hold) | owner 12 Oct ~22:45: "fix open items but don't patch it upstream" | "Add: upstream only with the owner's OK (on hold, 12 Oct)" |
| B23 | Video decoding - "Firefox stays software (Fedora's FFmpeg has no V4L2 path)" | STALE (format) | an item without a prefix, so it renders as a next step | move to notes |
| B24 | Video encoding - Add: a camera or screen-recorder encode test | OPEN-VALID low, no owner | VE rows use raw test video only (r147, r141u) | keep |
| B24b | Video encoding - notes "BT.601 needs the GStreamer colour patch" | DUPLICATE of B21 (N4) | same patch | "BT.601: see Hardware video decoding (N4)" |
| B25 | NPU - Owner check: QNN SDK licence | OPEN-VALID low, owner | unchanged | keep |
| B26 | DSP audio - Tune: the SoundWire clash / parity lines | OPEN-VALID low, no owner | r141 N1 INFO; sound unaffected (SA / AE PASS) | keep; never the old SoundWire "N1" patch; R2 (SoundWire 2.2 series) is the next source |
| B27 | Echo cancellation (part) - Tune: raw-capture clipping upright | IN PROGRESS (N2, 0.28-4 in B146) | r141 LP CHECK (raw capture still clips upright); TIMETABLE 02:40: 0.28-4 = fetch + BACKLIGHT_CAP=0 + N2 mic gain; wf/n2mic | "Fixing: N2 capture gain so the raw upright capture does not clip, never above stock (ADC 14 / TX_DEC 98); r155 LP / ERLE / F55" |
| B28 | Speaker level (part) - Owner check: listening after the install | OPEN-VALID high, owner | r141 LS INFO, OWN DEFERRED | keep |
| B29 | TFA DSP protection (todo) - Add: TFA2 RFC later | OPEN-VALID low, no owner | not a breaker (skipped as ordered) | keep |
| B30 | Headset (todo) - Owner check + Add: WCD939x accessory mode | OPEN-VALID low (test = owner) | unchanged | keep |
| B31 | Wi-Fi 5 / 6 GHz (part) - Owner check | OPEN-VALID med, owner | rehearsals keep no saved network | keep |
| B32 | Fast USB transfers - Tune: (research only) the lighter hold | REGRESSION-RISK (guarded) | 0064 froze (known breaker); the wording already forbids re-shipping it | keep the wording as is; never as a kernel change |
| B33 | USB host / OTG (todo) - Owner check | OPEN-VALID med, owner | the port carries the PC link in every test | keep |
| B34 | DisplayPort (part) - Owner check | OPEN-VALID med, owner | no monitor tried | keep |
| B35 | Charging (part) - Owner check: 20 min with wall chargers | OPEN-VALID med, owner | PC port only | keep (master charger session) |
| B36 | Pen charging (part) - Owner check | OPEN-VALID low, owner | unchanged | keep |
| B37 | Skin temperature policy (part) - Fixing: the brightness cap vs gsd-power | IN PROGRESS (B146: BACKLIGHT_CAP=0 interim; after B146: the ktz8869 kernel clamp) | r151: probe valid; 0.28-3 fights GNOME with automatic brightness on (case A FAIL: above the cap, swings, dims to 1308, no hand-back); the 0.28-4 user-space candidate also FAILS case A; cause = gnome-shell / mutter adopting the sysfs write and writing back through logind, not gsd-power | notes: "r151: the user-space cap fights GNOME's automatic brightness (case A)"; next: "Fixing: B146 ships the daemon's backlight cap off (BACKLIGHT_CAP=0); then a clamp in the ktz8869 driver (stock-like, invisible to GNOME), own rehearsal" |
| B38 | Wi-Fi across sleep - Add: wake-on-WLAN later | OPEN-VALID low, no owner | unchanged | keep |
| B39 | Wake by lid / keyboard / charger (part) - Owner check | OPEN-VALID med, owner | cover wake still CHECK (kit 132) | keep |
| B40 | Deep-sleep proof (part) - Owner check: one night unplugged; Tune: allow_cluster_off=0 only on a reset | OPEN-VALID med, owner | unchanged; the switch is carried | keep |
| B41 | Camera focus (part) - Add: autofocus once upstream libcamera has it | OPEN-VALID low (external) | simple pipeline has no AF | keep |
| B42 | Camera app - Add (upstream, watch): F54 stop race "candidate patch 0006 in wf/camfix" | REGRESSION-RISK (wording) | 0006 means a patched libcamera (dropped by the owner 11 Oct) or an upstream post (owner 12 Oct: no upstream) | "Add (watch): upstream libcamera issues #320 / #335 (F54); no patched libcamera; 0006 upstream only with the owner's OK" |
| B43 | Camera app - libcamera 0.7.1-2 adoption (in the notes, no next item) | IN PROGRESS (queued: when F44 stable) | r152 lc0712 7/7 PASS: G4 40/40 close-fatal 0, IPA in-process; FORCE_ISOLATION 40/40 | "Add: Fedora libcamera 0.7.1-2 as a normal update when it reaches F44 stable (r152 PASS); one G4 row after it lands" |
| B44 | Camera app - Tune: the simple-IPA yaml values | OPEN-VALID low, no owner | r139c uses /usr/share/libcamera/ipa/simple/sc1320cs.yaml | keep; through a config override only, never a rebuilt libcamera |
| B45 | Camera app - Owner check: sharpness and colours | OPEN-VALID low, owner | unchanged | keep |
| B46 | Cameras - Add: SuperTurtleDev's GPL SmartSens driver as a comparison | OPEN-VALID low, no owner | in-tree driver loaded (r148c CAMDRV PASS) | keep |
| B47 | Kernel package - Add: reproducible builds | OPEN-VALID low, no owner | unchanged | keep |
| B48 | Update policy - Owner check: versionlock firmware / the sensor stack | OPEN-VALID med, owner (decision) | unchanged | keep |
| B49 | Full GNOME app set (part) - Owner check: 30-minute look | OPEN-VALID low, owner | unchanged | keep |
| B50 | Stock-values audit - Tune: re-run after every kernel / package change | IN PROGRESS (r155 on q89e: AK / ST rows) | routine; AK PASS r141 on q89d9 | keep |
| B51 | About page - Tune: memory 11.1 GiB | OPEN-VALID low, no owner | unchanged | keep |
| B52 | Upstream fixes - Add: drop the 7.4-merged patches at the next rebase | IN PROGRESS (q89e, B146) | TIMETABLE step 2p "drop merged patches; r2t breakers out" | "Fixing: q89e drops the merged patches (B146)"; re-check every rebase |

## 2. ok rows whose notes are contradicted by newer evidence

| Row | Contradiction | Evidence | Change |
|---|---|---|---|
| Linux 7.3-rc6 through EFI | "no v7.3-rc7 tag yet"; "push the q89d9 branch and tag" | rc7 tagged (24a19b953e2a); q89d9 pushed 12 Oct | B1 / B2; after r155 rename the row to "Linux 7.3-rc7 through EFI" with q89e |
| Hardware random number generator | numbers from kit 119 only; Add still open | r142 / r141u RN PASS | B5 |
| Hardware video decoding | an unprefixed "Firefox stays software" next item | - | B23 |
| Upstream fixes for this chip's drivers / DSP audio | "N1 (SoundWire) and N2 (hci_qca)" and "the upstream N1 patch": the same names as the new round's N1 (idle refresh) and N2 (mic clipping) | TIMETABLE N-round | call the old ones "the SoundWire IRQ patch (old N1)" and "the hci_qca patch (old N2)" |
| Automated rehearsals | "runs alone" holds, but PV is CHECK in every run r141-r153 (camera pre-grant "cam: CHECK" at the start, PASS at the end) | r141, r150b, r151, r152, r153 | notes: "PV CHECK (camera grant read at start) is known, not an owner step"; or fix the PV start check |
| Device package (iceland-device 0.28-3) | B146 replaces it with 0.28-4 (fetch helper, BACKLIGHT_CAP=0, N2 mic gain) | wf/b146/pkg/iceland-pkg-0.28-4.tgz | rename after r155 |
| Camera app on the installed image | next item cites "candidate patch 0006" | owner: no patched libcamera, no upstream | B42 |

Not contradicted: Skin and XO zones (60 / 61 C, r150b), Cameras (in-tree module, r148c), Speaker protection, Bluetooth
rows, Gyroscope (r142 / r141u GY PASS).

## 3. Counts

Items: 55. DONE 2 (B5, B7b); IN PROGRESS 8 (B8, B15, B21, B27, B37, B43, B50, B52); STALE 6 (B1, B2, B7, B9, B17, B23);
DUPLICATE 2 (B0, B24b); REGRESSION-RISK 2 (B32 guarded, B42); OPEN-VALID 35 (owner-gated 21, PC-only 14).

Matrix status counts:
- now 79 ok / 16 part / 6 todo / 3 out;
- after these corrections 80 / 15 / 6 / 3 (Firmware package -> ok);
- after a passing r155:
  - Echo cancellation -> ok if N2 leaves LP clipping at 0: 81 / 14 / 6 / 3;
  - Skin temperature policy stays part until the ktz8869 clamp is proven.

## 4. Matrix changes (for a research/matrix-*.py after B146 / r155)

Apply 1-12 now (evidence exists); apply 13-19 only with r155's result.

1. Linux row next: replace both items with B1's wording; notes: drop "no v7.3-rc7 tag yet", add "q89d8 and q89d9 pushed (branches + tags)".
2. Hardware RNG: notes = r141u's RN numbers; next "Nothing (RN row in the regression set)".
3. Firmware package: status ok; notes add "11.A.38-3 (decoded generic thermal model) released; r153: pinned fetch, tamper refusal, offline keep, upgrade -2 -> -3 PASS"; next per B7.
4. Fedora installed: notes / next per B9 (remove the duplicated clause; the random-seed item goes once B146's image passes).
5. U-Boot: next "Owner check: decision 3 (see Fedora installed on the tablet)".
6. Native display: next per B14.
7. Smooth window moves: next per B17.
8. Hardware video decoding: Fixing per B21; Add per B22; move "Firefox stays software" into notes.
9. Hardware video encoding: notes "BT.601: see Hardware video decoding (N4)".
10. Skin temperature policy: notes / next per B37 (cause = GNOME's write-back, r151; gsd-power wording out).
11. Camera app: Add per B42; add B43's adoption item.
12. Upstream fixes + DSP audio: rename the old N1 / N2 patches (section 2).
13. Linux row (after r155 PASS): title "Linux 7.3-rc7 through EFI", notes = q89e version string, build warnings, r155.
14. Refresh: N1 result (in B146 or moved to the next round), per B15.
15. Echo cancellation: N2 result; status ok if LP clipping is 0 upright with ERLE / F55 unchanged and gains <= stock.
16. Hardware video decoding: N4 result (VE-601 PASS -> drop the Fixing).
17. Device package: rename to 0.28-4, list fetch helper + BACKLIGHT_CAP=0 + N2.
18. Fedora installed + header (DATE, STATUS_MD, STATUS_HTML): golden B146, r155, image rebuilt from B146 (HELD).
19. Upstream fixes: "merged patches dropped at the rc7 rebase (q89e)".

Then build.py, privacy guards, commit, republish the matrix page (Loop 5 owns the step).
